import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
load_dotenv(str(BASE_DIR / ".env"))

from app.classes.postgres import PostgreSQL
from app.services import crm_services, avance_services


def ejecutar_migracion_hu117():
    print("--- 1. APLICANDO MIGRACIÓN MIGRATION_CU30_HU117_SOLICITUDES.SQL ---")
    sql_path = BASE_DIR / "database" / "migration_cu30_hu117_solicitudes.sql"
    sql_content = sql_path.read_text(encoding="utf-8")

    db = PostgreSQL()
    db.create_connection()
    try:
        # Ejecutar sentencias DDL
        cur = db.conn.cursor()
        cur.execute(sql_content)
        db.conn.commit()
        print("✓ Migración ejecutada correctamente.")

        # Verificar tabla creada
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'obras' AND table_name = 't_cliente_solicitud'
            ORDER BY ordinal_position;
        """)
        cols = cur.fetchall()
        print(f"✓ Columnas en obras.t_cliente_solicitud ({len(cols)} columnas):")
        for c, t in cols:
            print(f"   - {c}: {t}")
    finally:
        db.close_connection()


def probar_flujo_completo_fabricio():
    print("\n--- 2. PROBANDO FLUJO COMPLETO CLIENTE (FABRICIO) -> CONSTRUCTORA -> CLIENTE ---")
    token_fabricio = {
        "nro_usuario": 20,
        "id_empresa": 1,
        "nombre_rol": "CLIENTE",
    }
    token_constructora = {
        "nro_usuario": 1,
        "id_empresa": 1,
        "nombre_rol": "ADMINISTRADOR_EMPRESA",
    }

    # PASO 1: Fabricio crea la solicitud
    print("\n[Paso 1: Fabricio registra solicitud]")
    payload_creacion = {
        "id_unidad": 9,  # UNI-000009
        "titulo": "Consulta de fase de construcción",
        "descripcion": "Quiero conocer en qué fase exacta se encuentra actualmente mi unidad.",
    }
    res_crear = crm_services.registrar_solicitud_cliente_autenticado(payload_creacion, token_fabricio)
    solicitud_creada = res_crear["data"]
    id_solicitud = solicitud_creada["id_solicitud"]
    print(f"✓ Solicitud #{id_solicitud} creada exitosamente.")
    print(f"   - Título: {solicitud_creada['titulo']}")
    print(f"   - Estado inicial: {solicitud_creada['estado']}")
    print(f"   - Unidad ID: {solicitud_creada['id_unidad']}")
    assert solicitud_creada["estado"] == "PENDIENTE", "El estado inicial debe ser PENDIENTE"

    # PASO 2: Constructora gestiona la solicitud
    print("\n[Paso 2: Constructora pasa a EN_PROCESO]")
    res_en_proceso = crm_services.responder_solicitud_constructora(
        id_solicitud=id_solicitud,
        data={"estado": "EN_PROCESO"},
        token=token_constructora,
    )
    print(f"✓ Estado actualizado: {res_en_proceso['data']['estado']}")
    assert res_en_proceso["data"]["estado"] == "EN_PROCESO"

    print("\n[Paso 2b: Constructora responde y pasa a ATENDIDA]")
    respuesta_oficial = "La unidad se encuentra actualmente en fase de instalaciones eléctricas."
    res_atendida = crm_services.responder_solicitud_constructora(
        id_solicitud=id_solicitud,
        data={
            "estado": "ATENDIDA",
            "respuesta": respuesta_oficial,
        },
        token=token_constructora,
    )
    print(f"✓ Solicitud #{id_solicitud} atendida:")
    print(f"   - Estado: {res_atendida['data']['estado']}")
    print(f"   - Respuesta: {res_atendida['data']['respuesta']}")
    print(f"   - Fecha respuesta: {res_atendida['data']['fecha_respuesta']}")
    assert res_atendida["data"]["estado"] == "ATENDIDA"
    assert res_atendida["data"]["respuesta"] == respuesta_oficial

    # PASO 3: Fabricio entra a "Mis solicitudes" y consulta lista
    print("\n[Paso 3: Fabricio lista sus solicitudes]")
    lista_res = crm_services.listar_solicitudes_cliente_autenticado(token_fabricio)
    solicitudes = lista_res["data"]
    sol_fabricio = next((s for s in solicitudes if s["id_solicitud"] == id_solicitud), None)
    assert sol_fabricio is not None, "La solicitud debe aparecer en la lista de Fabricio"
    print(f"✓ Solicitud #{id_solicitud} encontrada en Mis solicitudes:")
    print(f"   - Título: {sol_fabricio['titulo']}")
    print(f"   - Unidad: {sol_fabricio['codigo_unidad']} ({sol_fabricio['nombre_obra']})")
    print(f"   - Estado: {sol_fabricio['estado']}")
    print(f"   - Fecha: {sol_fabricio['fecha_creacion']}")

    # PASO 4: Fabricio selecciona "Ver detalle"
    print("\n[Paso 4: Fabricio consulta detalle de la solicitud]")
    detalle_res = crm_services.obtener_detalle_solicitud_cliente_autenticado(id_solicitud, token_fabricio)
    detalle = detalle_res["data"]
    print("✓ Detalle completo obtenido:")
    print(f"   - Título: {detalle['titulo']}")
    print(f"   - Unidad: {detalle['codigo_unidad']} - {detalle['nombre_obra']}")
    print(f"   - Descripción: {detalle['descripcion']}")
    print(f"   - Estado: {detalle['estado']}")
    print(f"   - Respuesta constructora: {detalle['respuesta']}")
    print(f"   - Fecha de atención: {detalle['fecha_respuesta']}")
    assert detalle["estado"] == "ATENDIDA"
    assert detalle["respuesta"] == respuesta_oficial

    # PASO 5: Seguridad y Aislamiento Multi-Tenant
    print("\n[Paso 5: Pruebas de Aislamiento y Seguridad]")
    token_otro_cliente = {
        "nro_usuario": 12,  # usuario cliente de otra empresa o sin acceso
        "id_empresa": 4,
        "nombre_rol": "CLIENTE",
    }
    try:
        crm_services.obtener_detalle_solicitud_cliente_autenticado(id_solicitud, token_otro_cliente)
        print("❌ ERROR: Otro cliente pudo consultar la solicitud ajena!")
        sys.exit(1)
    except crm_services.CrmError as err:
        print(f"✓ Cliente de otro tenant rechazado correctamente con HTTP {err.status_code}: {err}")
        assert err.status_code == 404

    # Fabricio intenta crear solicitud para unidad que no le pertenece
    try:
        crm_services.registrar_solicitud_cliente_autenticado({
            "id_unidad": 9999,
            "titulo": "Unidad ajena",
            "descripcion": "Intento no autorizado",
        }, token_fabricio)
        print("❌ ERROR: Fabricio pudo crear solicitud para unidad ajena!")
        sys.exit(1)
    except crm_services.CrmError as err:
        print(f"✓ Creación con unidad no asociada rechazada correctamente con HTTP {err.status_code}: {err}")
        assert err.status_code == 400

    print("\n[Paso 6: Verificación de No Regresión HU114, HU115, HU116]")
    # HU114
    res_hu114 = avance_services.consultar_avance_fisico_unidad_cliente(8, 9, token_fabricio)
    assert res_hu114.get("success") is True, "HU114 debe seguir funcionando"
    print(f"✓ HU114 (Avance físico unidad): {len(res_hu114.get('data', []))} registros obtenidos.")

    # HU115
    res_hu115 = crm_services.listar_fotografias_cliente_autenticado(9, token_fabricio)
    assert res_hu115.get("success") is True, "HU115 debe seguir funcionando"
    print(f"✓ HU115 (Fotografías unidad): {len(res_hu115.get('data', []))} fotos obtenidas.")

    # HU116
    res_hu116 = crm_services.listar_comunicaciones_cliente_autenticado(token_fabricio)
    assert res_hu116.get("success") is True, "HU116 debe seguir funcionando"
    print(f"✓ HU116 (Comunicaciones directas): {len(res_hu116.get('data', []))} comunicaciones obtenidas.")

    # HU117
    res_hu117 = crm_services.listar_solicitudes_cliente_autenticado(token_fabricio)
    assert res_hu117.get("success") is True, "HU117 debe seguir funcionando"
    print(f"✓ HU117 (Solicitudes enviadas): {len(res_hu117.get('data', []))} solicitudes obtenidas.")

    print("\n=======================================================")
    print("🎉 FLUJO COMPLETO HU117 Y NO-REGRESIÓN VERIFICADOS AL 100%")
    print("=======================================================")


if __name__ == "__main__":
    ejecutar_migracion_hu117()
    probar_flujo_completo_fabricio()
