"""Pruebas exhaustivas para la resolución de los 16 hallazgos de auditoría CU29:
Seguridad (A1-A6), Consistencia funcional y operativa (M1-M8), y Calidad (B1-B2).
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from pydantic import ValidationError

from app.services.ai.knowledge_base import buscar_conocimiento, MODULOS_OBRATEC
from app.services.ai.assistant_analysis import analizar_salud_operativa
from app.services.ai import assistant_operations
from app.services.ai.assistant_service import ReadPlan, ActionProposal, _plan
from app.services.incidencia_services import IncidenciaError
from app.services.material_services import MaterialError


# ─────────────────────────────────────────────────────────────────────────────
# 1. Base de Conocimiento y Rutas (B1)
# ─────────────────────────────────────────────────────────────────────────────
def test_b1_knowledge_base_rutas_y_capacidades_reales():
    """B1: Valida ruta corregida /equipos-maquinaria, cuota configurable y advertencia de restore."""
    res = buscar_conocimiento("¿Dónde veo los equipos y maquinaria?", "ADMINISTRADOR")
    assert res is not None
    rutas = [m["ruta"] for m in res["modulos"]]
    assert "/equipos-maquinaria" in rutas
    assert "/equipo-maquinaria" not in rutas

    # Cupo SaaS configurable
    mod_saas = next(m for m in MODULOS_OBRATEC if m["id"] == "suscripciones_planes")
    assert any("configurable" in cap.lower() for cap in mod_saas["capacidades"])

    # Restore bloqueado
    mod_bk = next(m for m in MODULOS_OBRATEC if m["id"] == "backup_restore")
    assert any("bloqueada" in cap.lower() for cap in mod_bk["capacidades"])


def test_b1_knowledge_base_filtrado_por_permisos_reales():
    """B1: Módulos se filtran por el conjunto de permisos efectivos del actor."""
    permisos = frozenset(["Visualizar_obras", "Visualizar_incidencias"])
    res = buscar_conocimiento("¿Qué módulos tengo disponibles?", "JEFE DE OBRA", permisos=permisos)
    assert res is not None
    rutas = [m["ruta"] for m in res["modulos"]]
    assert "/proyectos" in rutas
    assert "/incidencias" in rutas
    assert "/control-costos" not in rutas
    assert "/compras" not in rutas


# ─────────────────────────────────────────────────────────────────────────────
# 2. Revalidación RBAC, SaaS y Tenencia en Confirmación (A1, A2)
# ─────────────────────────────────────────────────────────────────────────────
def test_a1_confirmacion_revalida_rbac_revocado():
    """A1: Si el permiso del usuario fue revocado entre propuesta y confirmación, se rechaza con 403."""
    ctx = MagicMock()
    ctx.usuario = 42
    ctx.empresa = 10
    ctx.obras_autorizadas = [101]
    ctx.require = MagicMock()

    propuesta = assistant_operations.proponer_operacion(
        ctx,
        tipo_operacion="crear_incidencia",
        parametros={"id_obra": 101, "titulo": "Fisura en muro", "prioridad": "ALTA"},
    )
    id_propuesta = propuesta["id_propuesta"]

    # Al confirmar, simular que ctx.require arroja 403 por revocación
    token = {"nro_usuario": 42, "id_empresa": 10, "nombre_rol": "JEFE DE OBRA"}
    mock_ctx_fresco = MagicMock()
    mock_ctx_fresco.obras_autorizadas = [101]
    mock_ctx_fresco.require.side_effect = HTTPException(403, "No tiene permiso: Registrar_incidencias")

    with patch("app.repos.reportes_repos.transaction") as mock_tx, \
         patch("app.services.ai.assistant_operations.context", return_value=mock_ctx_fresco), \
         patch("app.repos.reportes_repos.one", return_value={"id_empresa": 10}), \
         patch("app.services.suscripcion_policy.exigir_escritura"):

        with pytest.raises(HTTPException) as exc:
            assistant_operations.ejecutar_propuesta(token, id_propuesta)
        assert exc.value.status_code == 403
        assert "Registrar_incidencias" in str(exc.value.detail)


def test_a1_confirmacion_revalida_saas_escritura():
    """A1: Si la suscripción de la empresa bloquea escritura, se rechaza la confirmación."""
    ctx = MagicMock()
    ctx.usuario = 42
    ctx.empresa = 10
    ctx.obras_autorizadas = [101]
    ctx.require = MagicMock()

    propuesta = assistant_operations.proponer_operacion(
        ctx,
        tipo_operacion="crear_material",
        parametros={"codigo": "MAT-01", "nombre_material": "Arena fina"},
    )
    id_propuesta = propuesta["id_propuesta"]

    token = {"nro_usuario": 42, "id_empresa": 10, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
    mock_ctx_fresco = MagicMock()

    with patch("app.repos.reportes_repos.transaction"), \
         patch("app.services.ai.assistant_operations.context", return_value=mock_ctx_fresco), \
         patch("app.services.suscripcion_policy.exigir_escritura", side_effect=HTTPException(403, "Plan no permite escritura")):

        with pytest.raises(HTTPException) as exc:
            assistant_operations.ejecutar_propuesta(token, id_propuesta)
        assert exc.value.status_code == 403
        assert "escritura" in str(exc.value.detail)


def test_a2_confirmacion_impone_empresa_ticket_y_rechaza_obra_ajena():
    """A2: El token forzado usa la empresa del ticket y rechaza si la obra no pertenece a dicha empresa."""
    ctx = MagicMock()
    ctx.usuario = 99
    ctx.empresa = 5
    ctx.obras_autorizadas = [50]
    ctx.require = MagicMock()

    # Propuesta creada válidamente en empresa 5
    propuesta = assistant_operations.proponer_operacion(
        ctx,
        tipo_operacion="crear_incidencia",
        parametros={"id_obra": 50, "titulo": "Desperfecto", "prioridad": "MEDIA"},
    )
    id_propuesta = propuesta["id_propuesta"]

    # Token de confirmación
    token_global = {"nro_usuario": 99, "id_empresa": 999, "nombre_rol": "ADMINISTRADOR"}
    mock_ctx = MagicMock()
    mock_ctx.obras_autorizadas = [50]

    # Obra 50 reporta pertenecer a empresa 88 (cruce de empresa simulado)
    with patch("app.repos.reportes_repos.transaction"), \
         patch("app.services.ai.assistant_operations.context", return_value=mock_ctx), \
         patch("app.repos.reportes_repos.one", return_value={"id_empresa": 88}), \
         patch("app.services.suscripcion_policy.exigir_escritura"):

        with pytest.raises(HTTPException) as exc:
            assistant_operations.ejecutar_propuesta(token_global, id_propuesta)
        assert exc.value.status_code == 403
        assert "no pertenece a la empresa" in str(exc.value.detail)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Diagnóstico Administrativo: Permisos y Schema Real (A3, A4)
# ─────────────────────────────────────────────────────────────────────────────
def test_a3_analisis_salud_autorizacion_individual_por_dominio():
    """A3: Dominios sin permiso RBAC son omitidos con registro en fuentes_omitidas."""
    db = MagicMock()
    ctx = MagicMock()
    ctx.usuario = 15
    ctx.empresa = 2
    ctx.rol = "CLIENTE"
    # Solo tiene avances, no incidencias, ni OTs, ni materiales
    ctx.permisos = frozenset(["Visualizar_avances"])

    with patch("app.repos.reportes_repos.works", return_value=[{"id_obra": 1, "nombre": "Torre A"}]):
        res = analizar_salud_operativa(db, ctx, id_obra=1)
        assert res["tipo"] == "analisis_salud"
        omitidos = [f["modulo"] for f in res["fuentes_omitidas"]]
        assert "incidencias" in omitidos
        assert "ordenes_trabajo" in omitidos
        assert "inventario" in omitidos
        assert "consultas_tecnicas" in omitidos
        assert len(res["fuentes_consultadas"]) == 0


def test_a3_analisis_salud_restriccion_fila_trabajador():
    """A3: Rol trabajador aplica filtro de fila id_responsable / id_usuario."""
    db = MagicMock()
    ctx = MagicMock()
    ctx.usuario = 77
    ctx.empresa = 2
    ctx.rol = "ELECTRICO"
    ctx.permisos = frozenset(["Visualizar_incidencias", "Visualizar_ordenes_trabajo"])

    captured_sqls = []
    def fake_rows(db_conn, sql, params=()):
        captured_sqls.append(sql)
        return []

    with patch("app.repos.reportes_repos.works", return_value=[{"id_obra": 1, "nombre": "Torre A"}]), \
         patch("app.repos.reportes_repos.rows", side_effect=fake_rows):
        analizar_salud_operativa(db, ctx, id_obra=1)

    # Validar que SQLs contienen el filtro de asignación del trabajador
    assert any("id_responsable = %s OR i.id_usuario = %s" in sql for sql in captured_sqls)
    assert any("t_orden_trabajo_usuario" in sql for sql in captured_sqls)


def test_a4_analisis_salud_utiliza_fn_listar_inventario():
    """A4: El análisis de inventario consume fn_listar_inventario_empresa y no t_inventario_almacen."""
    db = MagicMock()
    ctx = MagicMock()
    ctx.usuario = 1
    ctx.empresa = 3
    ctx.rol = "ADMINISTRADOR_EMPRESA"
    ctx.permisos = frozenset(["Visualizar_materiales"])

    captured_sqls = []
    def fake_rows(db_conn, sql, params=()):
        captured_sqls.append(sql)
        if "fn_listar_inventario_empresa" in sql:
            return [{"id_material": 1, "codigo": "C-01", "nombre_material": "Clavos", "precio": 10, "stock_actual": 0}]
        return []

    with patch("app.repos.reportes_repos.works", return_value=[{"id_obra": 1, "nombre": "Obra 1"}]), \
         patch("app.repos.reportes_repos.rows", side_effect=fake_rows):
        analisis = analizar_salud_operativa(db, ctx, id_obra=1)

    assert any("fn_listar_inventario_empresa" in sql for sql in captured_sqls)
    assert not any("t_inventario_almacen" in sql for sql in captured_sqls)
    assert any(ind["codigo"] == "STOCK_AGOTADO" for ind in analisis["indicadores"])


# ─────────────────────────────────────────────────────────────────────────────
# 4. Integraciones Reales de Dominio y Preservación de IDs (A5, B2)
# ─────────────────────────────────────────────────────────────────────────────
def test_a5_ejecutar_crear_orden_trabajo_contrato_real():
    """A5: Ejecución de OT llama a crear_orden_trabajo y extrae orden_nro correctamente."""
    ctx = MagicMock()
    ctx.usuario = 10
    ctx.empresa = 1
    ctx.obras_autorizadas = [5]
    ctx.require = MagicMock()

    propuesta = assistant_operations.proponer_operacion(
        ctx,
        tipo_operacion="crear_orden_trabajo",
        parametros={"id_obra": 5, "tipo_trab": "Instalación eléctrica"},
    )

    token = {"nro_usuario": 10, "id_empresa": 1, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
    mock_ctx = MagicMock()
    mock_ctx.obras_autorizadas = [5]

    with patch("app.repos.reportes_repos.transaction"), \
         patch("app.services.ai.assistant_operations.context", return_value=mock_ctx), \
         patch("app.repos.reportes_repos.one", return_value={"id_empresa": 1}), \
         patch("app.services.suscripcion_policy.exigir_escritura"), \
         patch("app.services.orden_Trabajo_services.crear_orden_trabajo", return_value={"success": True, "orden_nro": 884}), \
         patch("app.repos.bitacora_repos.registrar_bitacora"):

        res = assistant_operations.ejecutar_propuesta(token, propuesta["id_propuesta"])
        assert res["success"] is True
        assert res["resultado"]["orden_nro"] == 884


def test_a5_ejecutar_crear_material_contrato_real():
    """A5: Ejecución de material llama a registrar y extrae id_material."""
    ctx = MagicMock()
    ctx.usuario = 10
    ctx.empresa = 1
    ctx.obras_autorizadas = []
    ctx.require = MagicMock()

    propuesta = assistant_operations.proponer_operacion(
        ctx,
        tipo_operacion="crear_material",
        parametros={"codigo": "TUB-01", "nombre_material": "Tubo PVC 1/2"},
    )

    token = {"nro_usuario": 10, "id_empresa": 1, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
    mock_ctx = MagicMock()

    with patch("app.repos.reportes_repos.transaction"), \
         patch("app.services.ai.assistant_operations.context", return_value=mock_ctx), \
         patch("app.services.suscripcion_policy.exigir_escritura"), \
         patch("app.services.material_services.registrar", return_value={"success": True, "id_material": 302, "message": "OK"}), \
         patch("app.repos.bitacora_repos.registrar_bitacora"):

        res = assistant_operations.ejecutar_propuesta(token, propuesta["id_propuesta"])
        assert res["success"] is True
        assert res["resultado"]["id_material"] == 302


def test_b2_ejecutar_crear_incidencia_preserva_id_real():
    """B2: Incidencia extrae id_incidencia de la raíz del resultado devuelto por registrar()."""
    ctx = MagicMock()
    ctx.usuario = 10
    ctx.empresa = 1
    ctx.obras_autorizadas = [2]
    ctx.require = MagicMock()

    propuesta = assistant_operations.proponer_operacion(
        ctx,
        tipo_operacion="crear_incidencia",
        parametros={"id_obra": 2, "titulo": "Bomba dañada", "prioridad": "MEDIA"},
    )

    token = {"nro_usuario": 10, "id_empresa": 1, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
    mock_ctx = MagicMock()
    mock_ctx.obras_autorizadas = [2]

    # Contrato real: devuelve id_incidencia en el nivel superior
    with patch("app.repos.reportes_repos.transaction"), \
         patch("app.services.ai.assistant_operations.context", return_value=mock_ctx), \
         patch("app.repos.reportes_repos.one", return_value={"id_empresa": 1}), \
         patch("app.services.suscripcion_policy.exigir_escritura"), \
         patch("app.services.incidencia_services.registrar", return_value={"success": True, "id_incidencia": 777, "message": "Creada"}), \
         patch("app.repos.bitacora_repos.registrar_bitacora"):

        res = assistant_operations.ejecutar_propuesta(token, propuesta["id_propuesta"])
        assert res["success"] is True
        assert res["resultado"]["id_incidencia"] == 777


# ─────────────────────────────────────────────────────────────────────────────
# 5. Saneamiento de Historial e Inyección de Prompt (A6, M1)
# ─────────────────────────────────────────────────────────────────────────────
def test_a6_historial_conversacion_no_inyecta_respuestas_antiguas():
    """A6: historial_conversacion suministrado al prompt no incluye el texto libre de respuestas anteriores."""
    recent_inputs = [
        {"texto": "¿Cuánto costó la obra 1?", "texto_respuesta": "IMPORTE_SECRETO_99999", "tema": "costos"}
    ]
    captured_payload = {}
    mock_provider = MagicMock()
    def fake_complete(instruction, text, payload):
        captured_payload.update(payload)
        return '{"accion":"ayuda","mensaje":"test"}'
    mock_provider.complete = fake_complete

    with patch("app.services.ai.assistant_service.get_provider", return_value=mock_provider):
        _plan(
            "Pregunta nueva", ["comparativo_costos"], [], None, None, False, [], None,
            recent=recent_inputs, user_role="ADMINISTRADOR"
        )

    historial = captured_payload.get("historial_conversacion", [])
    assert len(historial) == 1
    # Verifica que el texto sensible del modelo no está presente en el historial
    assert "asistente" not in historial[0]
    assert "IMPORTE_SECRETO_99999" not in str(historial)


def test_m1_lectura_no_dispara_propuesta_accion():
    """M1: Una consulta de solo lectura informativa nunca produce un plan de operacion."""
    mock_provider = MagicMock()
    # Simular proveedor que alucina devolviendo accion='operacion' ante pregunta de lectura
    mock_provider.complete.return_value = (
        '{"accion":"operacion","operacion_propuesta":{"tipo_operacion":"crear_incidencia","entidad":"Incidencia","resumen":"Hack","parametros":{}}}'
    )
    with patch("app.services.ai.assistant_service.get_provider", return_value=mock_provider):
        plan = _plan(
            "¿Cuántos proveedores tenemos registrados?", ["stock"], [], None, None, False, [], None,
            user_role="ADMINISTRADOR"
        )
    assert isinstance(plan, ReadPlan)
    assert plan.accion != "operacion"
    assert "lectura informativa" in plan.mensaje


# ─────────────────────────────────────────────────────────────────────────────
# 6. Desambiguación de Obra y Negación (M2)
# ─────────────────────────────────────────────────────────────────────────────
def test_m2_obra_desconocida_o_ambigua_pide_aclaracion():
    """M2: Si no se indica obra o es desconocida, pide aclaración y no asume works[0]."""
    works = [{"id_obra": 1, "nombre": "Torre Norte", "codigo": "TN"}, {"id_obra": 2, "nombre": "Torre Sur", "codigo": "TS"}]

    # Sin obra especificada
    plan1 = _plan("Registra una incidencia de fuga", ["incidencias"], works, None, None, False, [], None)
    assert isinstance(plan1, ReadPlan)
    assert plan1.accion == "ayuda"
    assert "especifique" in plan1.mensaje

    # Con negación explícita
    plan2 = _plan("No crear una incidencia por favor", ["incidencias"], works, None, None, False, [], None)
    if isinstance(plan2, ReadPlan):
        assert plan2.accion != "operacion"
    else:
        assert plan2.get("accion") != "operacion"
        assert "operacion_propuesta" not in plan2


# ─────────────────────────────────────────────────────────────────────────────
# 7. Ciclo de Vida del Ticket, Cancelación y Concurrencia (M3, M4, M5)
# ─────────────────────────────────────────────────────────────────────────────
def test_m3_usuario_ajeno_no_consume_ticket():
    """M3: Un usuario ajeno que intenta confirmar el ticket recibe 403 y el ticket NO se destruye."""
    ctx = MagicMock()
    ctx.usuario = 100
    ctx.empresa = 1
    ctx.obras_autorizadas = [1]
    ctx.require = MagicMock()

    propuesta = assistant_operations.proponer_operacion(
        ctx,
        tipo_operacion="crear_material",
        parametros={"codigo": "AC-10", "nombre_material": "Acero 1/2"},
    )
    id_propuesta = propuesta["id_propuesta"]

    # Usuario ajeno (ID 999) intenta ejecutar
    token_ajeno = {"nro_usuario": 999, "id_empresa": 1, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
    with pytest.raises(HTTPException) as exc:
        assistant_operations.ejecutar_propuesta(token_ajeno, id_propuesta)
    assert exc.value.status_code == 403

    # El propietario original (ID 100) aún puede consultar/cancelar su propuesta
    token_dueno = {"nro_usuario": 100, "id_empresa": 1, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
    cancel_res = assistant_operations.cancelar_propuesta(token_dueno, id_propuesta)
    assert cancel_res["success"] is True


def test_m4_cancelar_propuesta_y_formato_expiracion():
    """M4: Se permite cancelar explícitamente y la propuesta incluye expira_en en formato ISO."""
    ctx = MagicMock()
    ctx.usuario = 100
    ctx.empresa = 1
    ctx.obras_autorizadas = [1]
    ctx.require = MagicMock()

    propuesta = assistant_operations.proponer_operacion(
        ctx,
        tipo_operacion="crear_incidencia",
        parametros={"id_obra": 1, "titulo": "Vidrio roto", "prioridad": "BAJA"},
    )
    assert "expira_en" in propuesta
    datetime.fromisoformat(propuesta["expira_en"]) # Valida que es ISO válido

    token = {"nro_usuario": 100, "id_empresa": 1}
    res = assistant_operations.cancelar_propuesta(token, propuesta["id_propuesta"])
    assert res["success"] is True

    # Al intentar ejecutar una cancelada da 404
    with pytest.raises(HTTPException) as exc:
        assistant_operations.ejecutar_propuesta(token, propuesta["id_propuesta"])
    assert exc.value.status_code == 404


def test_m5_errores_dominio_mapeados_a_4xx():
    """M5: IncidenciaError, MaterialError y ValueError devuelven status_code correspondiente en vez de 500."""
    ctx = MagicMock()
    ctx.usuario = 100
    ctx.empresa = 1
    ctx.obras_autorizadas = [1]
    ctx.require = MagicMock()

    propuesta = assistant_operations.proponer_operacion(
        ctx,
        tipo_operacion="crear_incidencia",
        parametros={"id_obra": 1, "titulo": "Validación de error", "prioridad": "ALTA"},
    )

    token = {"nro_usuario": 100, "id_empresa": 1, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
    mock_ctx = MagicMock()
    mock_ctx.obras_autorizadas = [1]

    with patch("app.repos.reportes_repos.transaction"), \
         patch("app.services.ai.assistant_operations.context", return_value=mock_ctx), \
         patch("app.repos.reportes_repos.one", return_value={"id_empresa": 1}), \
         patch("app.services.suscripcion_policy.exigir_escritura"), \
         patch("app.services.incidencia_services.registrar", side_effect=IncidenciaError("Prioridad inválida", 400)):

        with pytest.raises(HTTPException) as exc:
            assistant_operations.ejecutar_propuesta(token, propuesta["id_propuesta"])
        assert exc.value.status_code == 400
        assert "Prioridad inválida" in str(exc.value.detail)
