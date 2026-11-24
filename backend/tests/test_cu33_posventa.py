"""
Suite de pruebas unitarias e integrativas para CU33:
Gestión de Garantías y Servicio Posventa (HU161 a HU168).
Valida las reglas de negocio, transiciones de estado y aislamiento multi-tenant estricto.
"""
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException

from app.routes import posventa_routes as routes
from app.services import posventa_services as services
from app.repos import posventa_repos as repos


TOKEN_ADMIN_EMP_A = {
    "nro_usuario": 1,
    "id_usuario": 1,
    "username": "admin.empresa.a",
    "nombre_rol": "ADMINISTRADOR_EMPRESA",
    "id_empresa": 10,
}

TOKEN_JEFE_OBRA_A = {
    "nro_usuario": 2,
    "id_usuario": 2,
    "username": "jefe.obra.a",
    "nombre_rol": "JEFE DE OBRA",
    "id_empresa": 10,
}

TOKEN_SUPERVISOR_A = {
    "nro_usuario": 3,
    "id_usuario": 3,
    "username": "sup.obra.a",
    "nombre_rol": "SUPERVISOR",
    "id_empresa": 10,
}

TOKEN_CLIENTE_A = {
    "nro_usuario": 4,
    "id_usuario": 4,
    "username": "cliente.juan",
    "nombre_rol": "CLIENTE",
    "id_empresa": 10,
}

TOKEN_EMPRESA_B = {
    "nro_usuario": 99,
    "id_usuario": 99,
    "username": "admin.empresa.b",
    "nombre_rol": "ADMINISTRADOR_EMPRESA",
    "id_empresa": 99,
}


class MockDBStore:
    def __init__(self):
        self.garantias = {}
        self.solicitudes = {}
        self.evidencias = {}
        self.bitacoras = {}
        self.next_garantia_id = 1
        self.next_solicitud_id = 1
        self.next_evidencia_id = 1
        self.next_bitacora_id = 1


@pytest.fixture
def store():
    return MockDBStore()


# ─────────────────────────────────────────────────────────────────────────────
# 1. PRUEBAS HU161: REGISTRO DE GARANTÍAS INMOBILIARIAS
# ─────────────────────────────────────────────────────────────────────────────

def test_hu161_registro_garantia_exitoso():
    """HU161: El Administrador_empresa registra una garantía válida para una unidad comercializada."""
    with patch("app.repos.posventa_repos.verificar_unidad_pertenece_empresa") as mock_u, \
         patch("app.repos.posventa_repos.verificar_cliente_propietario_unidad") as mock_c, \
         patch("app.repos.posventa_repos.registrar_garantia") as mock_reg, \
         patch("app.repos.posventa_repos.obtener_garantia_por_id") as mock_get:

        mock_u.return_value = {"id_unidad": 101, "nombre": "Dpto 4B", "id_obra": 1, "id_empresa": 10}
        mock_c.return_value = True
        mock_reg.return_value = 1
        mock_get.return_value = {
            "id_garantia": 1,
            "id_empresa": 10,
            "id_unidad": 101,
            "nombre_unidad": "Dpto 4B",
            "tipo_garantia": "ESTRUCTURAL",
            "descripcion_cobertura": "Cubre fallas estructurales y losas por 5 años",
            "fecha_inicio": "2026-01-01",
            "fecha_fin": "2031-01-01",
            "estado": "VIGENTE"
        }

        dto = routes.RegistrarGarantiaDTO(
            id_unidad=101,
            id_cliente=5,
            tipo_garantia="ESTRUCTURAL",
            descripcion_cobertura="Cubre fallas estructurales y losas por 5 años",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2031, 1, 1),
            condiciones="Sujeto a mantenimiento preventivo anual"
        )

        res = routes.registrar_garantia(dto, token_data=TOKEN_ADMIN_EMP_A)
        assert res["success"] is True
        assert res["garantia"]["id_garantia"] == 1
        assert res["garantia"]["tipo_garantia"] == "ESTRUCTURAL"


def test_hu161_rechazo_fechas_invalidas():
    """HU161: Se debe rechazar si la fecha_fin es anterior a fecha_inicio."""
    dto = routes.RegistrarGarantiaDTO(
        id_unidad=101,
        id_cliente=5,
        tipo_garantia="ACABADOS",
        descripcion_cobertura="Pintura y zócalos",
        fecha_inicio=date(2026, 12, 1),
        fecha_fin=date(2026, 1, 1),  # Fecha fin anterior
    )
    with pytest.raises(HTTPException) as exc:
        routes.registrar_garantia(dto, token_data=TOKEN_ADMIN_EMP_A)
    assert exc.value.status_code == 422
    assert "fecha de fin no puede ser anterior" in exc.value.detail


def test_hu161_rechazo_unidad_otra_empresa():
    """HU161: Intentar registrar garantía en una unidad de otra empresa es rechazado con 404."""
    with patch("app.repos.posventa_repos.verificar_unidad_pertenece_empresa") as mock_u:
        mock_u.return_value = None  # No pertenece a la empresa del token

        dto = routes.RegistrarGarantiaDTO(
            id_unidad=999,
            id_cliente=5,
            tipo_garantia="ACABADOS",
            descripcion_cobertura="Pintura",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2027, 1, 1),
        )
        with pytest.raises(HTTPException) as exc:
            routes.registrar_garantia(dto, token_data=TOKEN_ADMIN_EMP_A)
        assert exc.value.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# 2. PRUEBAS HU162: CONSULTA DE GARANTÍAS POR EL CLIENTE
# ─────────────────────────────────────────────────────────────────────────────

def test_hu162_cliente_solo_ve_sus_propias_garantias():
    """HU162: El Cliente solo consulta las garantías vinculadas a sus unidades adquiridas."""
    with patch("app.repos.posventa_repos.obtener_cliente_por_usuario") as mock_cli, \
         patch("app.repos.posventa_repos.listar_garantias") as mock_list:

        mock_cli.return_value = {"id_cliente": 7, "id_empresa": 10, "nombre_cliente": "Juan Perez"}
        mock_list.return_value = [
            {
                "id_garantia": 1,
                "id_unidad": 101,
                "nombre_unidad": "Dpto 4B",
                "tipo_garantia": "ESTRUCTURAL",
                "estado": "VIGENTE",
                "fecha_fin": "2031-01-01"
            }
        ]

        # Llamar como cliente con argumentos limpios
        res = routes.listar_garantias(
            id_unidad=None,
            id_cliente=None,
            id_obra=None,
            estado=None,
            token_data=TOKEN_CLIENTE_A
        )
        assert len(res) == 1
        assert res[0]["id_garantia"] == 1
        # Verificar que se filtró exactamente con id_cliente=7
        mock_list.assert_called_once_with(
            id_empresa=10,
            id_unidad=None,
            id_cliente=7,
            id_obra=None,
            estado=None
        )


# ─────────────────────────────────────────────────────────────────────────────
# 3. PRUEBAS HU163: REGISTRAR SOLICITUD DE POSVENTA
# ─────────────────────────────────────────────────────────────────────────────

def test_hu163_cliente_registra_solicitud_con_ticket():
    """HU163: El Cliente registra una solicitud, generando ticket y estado inicial PENDIENTE."""
    with patch("app.repos.posventa_repos.obtener_cliente_por_usuario") as mock_cli, \
         patch("app.repos.posventa_repos.verificar_unidad_pertenece_empresa") as mock_u, \
         patch("app.repos.posventa_repos.verificar_cliente_propietario_unidad") as mock_prop, \
         patch("app.repos.posventa_repos.registrar_solicitud") as mock_reg, \
         patch("app.repos.posventa_repos.obtener_solicitud_detalle") as mock_det:

        mock_cli.return_value = {"id_cliente": 7, "id_empresa": 10}
        mock_u.return_value = {"id_unidad": 101, "id_empresa": 10}
        mock_prop.return_value = True
        mock_reg.return_value = (50, "PV-20261123-0001")
        mock_det.return_value = {
            "id_solicitud": 50,
            "codigo_ticket": "PV-20261123-0001",
            "estado": "PENDIENTE",
            "titulo": "Fuga de agua en lavaplatos",
            "descripcion_defecto": "Gotera constante bajo el mueble de cocina"
        }

        dto = routes.RegistrarSolicitudDTO(
            id_unidad=101,
            titulo="Fuga de agua en lavaplatos",
            descripcion_defecto="Gotera constante bajo el mueble de cocina"
        )

        res = routes.registrar_solicitud(dto, token_data=TOKEN_CLIENTE_A)
        assert res["success"] is True
        assert res["codigo_ticket"] == "PV-20261123-0001"
        assert res["solicitud"]["estado"] == "PENDIENTE"


# ─────────────────────────────────────────────────────────────────────────────
# 4. PRUEBAS HU164: CLASIFICAR SOLICITUD DE POSVENTA
# ─────────────────────────────────────────────────────────────────────────────

def test_hu164_clasificar_solicitud_valida_cobertura():
    """HU164: Administrador clasifica especialidad, prioridad y valida si aplica garantía vigente."""
    with patch("app.repos.posventa_repos.obtener_solicitud_detalle") as mock_sol, \
         patch("app.repos.posventa_repos.obtener_garantia_por_id") as mock_gar, \
         patch("app.repos.posventa_repos.clasificar_solicitud") as mock_clas:

        mock_sol.return_value = {
            "id_solicitud": 50,
            "id_unidad": 101,
            "estado": "PENDIENTE",
            "id_empresa": 10
        }
        mock_gar.return_value = {
            "id_garantia": 3,
            "id_unidad": 101,
            "estado": "VIGENTE"
        }
        mock_clas.return_value = True

        dto = routes.ClasificarSolicitudDTO(
            categoria="PLOMERIA",
            prioridad="ALTA",
            aplica_garantia=True,
            id_garantia=3,
            observaciones="Aplica cobertura por garantía hidrosanitaria vigente."
        )

        res = routes.clasificar_solicitud(50, dto, token_data=TOKEN_ADMIN_EMP_A)
        assert res["success"] is True
        mock_clas.assert_called_once_with(
            id_solicitud=50,
            id_empresa=10,
            categoria="PLOMERIA",
            prioridad="ALTA",
            aplica_garantia=True,
            id_garantia=3,
            observaciones="Aplica cobertura por garantía hidrosanitaria vigente.",
            id_usuario_clasifica=1
        )


def test_hu164_rechazo_garantia_vencida():
    """HU164: Intentar clasificar con una garantía que ya venció lanza error."""
    with patch("app.repos.posventa_repos.obtener_solicitud_detalle") as mock_sol, \
         patch("app.repos.posventa_repos.obtener_garantia_por_id") as mock_gar:

        mock_sol.return_value = {"id_solicitud": 50, "id_unidad": 101, "estado": "PENDIENTE", "id_empresa": 10}
        mock_gar.return_value = {"id_garantia": 3, "id_unidad": 101, "estado": "VENCIDA"}

        dto = routes.ClasificarSolicitudDTO(
            categoria="PLOMERIA",
            prioridad="ALTA",
            aplica_garantia=True,
            id_garantia=3
        )

        with pytest.raises(HTTPException) as exc:
            routes.clasificar_solicitud(50, dto, token_data=TOKEN_ADMIN_EMP_A)
        assert exc.value.status_code == 400
        assert "ya se encuentra vencida" in exc.value.detail


# ─────────────────────────────────────────────────────────────────────────────
# 5. PRUEBAS HU165: ASIGNAR RESPONSABLE DE ATENCIÓN (JEFE DE OBRA)
# ─────────────────────────────────────────────────────────────────────────────

def test_hu165_jefe_de_obra_asigna_supervisor():
    """HU165: Jefe de Obra asigna supervisor disponible, fecha de visita y pasa a ASIGNADA."""
    with patch("app.repos.posventa_repos.obtener_solicitud_detalle") as mock_sol, \
         patch("app.repos.posventa_repos.listar_supervisores_disponibles") as mock_sup, \
         patch("app.repos.posventa_repos.asignar_supervisor_solicitud") as mock_asig:

        mock_sol.return_value = {"id_solicitud": 50, "estado": "CLASIFICADA", "id_empresa": 10}
        mock_sup.return_value = [{"id_usuario": 3, "nombre_completo": "Ing. Carlos Mendoza"}]
        mock_asig.return_value = True

        dto = routes.AsignarResponsableDTO(
            id_supervisor=3,
            fecha_estimada_visita=date(2026, 11, 25),
            instrucciones_tecnicas="Llevar sellador de silicona y llave inglesa."
        )

        res = routes.asignar_responsable(50, dto, token_data=TOKEN_JEFE_OBRA_A)
        assert res["success"] is True
        mock_asig.assert_called_once_with(
            id_solicitud=50,
            id_empresa=10,
            id_supervisor=3,
            fecha_estimada_visita=date(2026, 11, 25),
            instrucciones_tecnicas="Llevar sellador de silicona y llave inglesa.",
            id_usuario_asigna=2
        )


# ─────────────────────────────────────────────────────────────────────────────
# 6. PRUEBAS HU166: GESTIONAR ATENCIÓN Y CIERRE (SUPERVISOR)
# ─────────────────────────────────────────────────────────────────────────────

def test_hu166_supervisor_atiende_y_cierra_ticket():
    """HU166: Supervisor registra bitácora, materiales utilizados y cierra el ticket."""
    with patch("app.repos.posventa_repos.obtener_solicitud_detalle") as mock_sol, \
         patch("app.repos.posventa_repos.registrar_atencion_tecnica") as mock_aten:

        mock_sol.return_value = {
            "id_solicitud": 50,
            "estado": "EN_ATENCION",
            "id_supervisor_asignado": 3,
            "id_empresa": 10
        }
        mock_aten.return_value = True

        dto = routes.AtenderSolicitudDTO(
            nuevo_estado="RESUELTA",
            acciones_realizadas="Se reemplazó el sifón y empaquetadura defectuosa.",
            materiales_utilizados="1 sifón PVC 1 1/2 pulg, cinta teflón",
            motivo_cierre="Reparación completada y verificada sin filtraciones."
        )

        res = routes.registrar_atencion(50, dto, token_data=TOKEN_SUPERVISOR_A)
        assert res["success"] is True
        mock_aten.assert_called_once_with(
            id_solicitud=50,
            id_empresa=10,
            id_supervisor=3,
            nuevo_estado="RESUELTA",
            acciones_realizadas="Se reemplazó el sifón y empaquetadura defectuosa.",
            materiales_utilizados="1 sifón PVC 1 1/2 pulg, cinta teflón",
            motivo_cierre="Reparación completada y verificada sin filtraciones."
        )


# ─────────────────────────────────────────────────────────────────────────────
# 7. PRUEBAS HU167: CONSULTAR SEGUIMIENTO Y LÍNEA DE TIEMPO (CLIENTE)
# ─────────────────────────────────────────────────────────────────────────────

def test_hu167_seguimiento_timeline_solicitud():
    """HU167: El cliente consulta el detalle con su línea de tiempo completa."""
    with patch("app.repos.posventa_repos.obtener_solicitud_detalle") as mock_sol, \
         patch("app.repos.posventa_repos.obtener_cliente_por_usuario") as mock_cli:

        mock_cli.return_value = {"id_cliente": 7, "id_empresa": 10}
        mock_sol.return_value = {
            "id_solicitud": 50,
            "codigo_ticket": "PV-20261123-0001",
            "id_cliente": 7,
            "id_empresa": 10,
            "estado": "RESUELTA",
            "linea_tiempo": [
                {"tipo_evento": "REGISTRO_TICKET", "detalle_acciones": "Apertura ticket"},
                {"tipo_evento": "CLASIFICACION", "detalle_acciones": "Clasificado en Plomería"},
                {"tipo_evento": "ASIGNACION_SUPERVISOR", "detalle_acciones": "Asignado a Carlos Mendoza"},
                {"tipo_evento": "CIERRE_TECNICO", "detalle_acciones": "Reparación completada"}
            ],
            "evidencias": []
        }

        res = routes.obtener_detalle_solicitud(50, token_data=TOKEN_CLIENTE_A)
        assert res["id_solicitud"] == 50
        assert len(res["linea_tiempo"]) == 4
        assert res["estado"] == "RESUELTA"


# ─────────────────────────────────────────────────────────────────────────────
# 8. PRUEBAS HU168 Y MULTI-TENANT: AUDITORÍA Y BLOQUEO ENTRE EMPRESAS
# ─────────────────────────────────────────────────────────────────────────────

def test_hu168_metricas_auditoria_posventa():
    """HU168: Métricas de resolución y auditoría por empresa."""
    with patch("app.repos.posventa_repos.obtener_metricas_posventa") as mock_m:
        mock_m.return_value = {
            "total_solicitudes": 15,
            "pendientes": 2,
            "resueltas": 10,
            "cubiertas_por_garantia": 12,
            "promedio_dias_resolucion": 2.5
        }

        res = routes.consultar_metricas(token_data=TOKEN_ADMIN_EMP_A)
        assert res["success"] is True
        assert res["metricas"]["total_solicitudes"] == 15
        mock_m.assert_called_once_with(10)


def test_aislamiento_multitenant_bloquea_otra_empresa():
    """Un usuario de Empresa B no puede ver ni modificar solicitudes de Empresa A."""
    with patch("app.repos.posventa_repos.obtener_solicitud_detalle") as mock_sol:
        mock_sol.return_value = None  # Al buscar con id_empresa=99 no existe

        with pytest.raises(HTTPException) as exc:
            routes.obtener_detalle_solicitud(50, token_data=TOKEN_EMPRESA_B)
        assert exc.value.status_code == 404
