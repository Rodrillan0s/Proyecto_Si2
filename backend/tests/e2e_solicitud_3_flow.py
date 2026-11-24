import sys
import json
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
load_dotenv(str(BASE_DIR / ".env"))

from app.services import crm_services


def run_e2e_solicitud_3():
    token_jefe_obra = {
        "nro_usuario": 5,
        "id_empresa": 1,
        "nombre_rol": "JEFE DE OBRA",
    }

    token_fabricio = {
        "nro_usuario": 20,
        "id_empresa": 1,
        "nombre_rol": "CLIENTE",
    }

    print("=== 1. VERIFICAR SOLICITUD 3 COMO JEFE DE OBRA ===")
    res_solicitudes = crm_services.listar_solicitudes_constructora(token_jefe_obra)
    solicitudes = res_solicitudes.get("data", []) if isinstance(res_solicitudes, dict) else res_solicitudes
    sol3 = next((s for s in solicitudes if s["id_solicitud"] == 3), None)
    assert sol3 is not None, "Solicitud 3 no encontrada en constructora"
    print(f"Solicitud encontrada: ID={sol3['id_solicitud']}, Cliente={sol3['nombre_cliente']}, Unidad={sol3['codigo_unidad']}, Obra={sol3['nombre_obra']}, Estado={sol3['estado']}")

    print("\n=== 2. TRANSICIÓN 1: PENDIENTE -> EN_PROCESO ===")
    res1 = crm_services.responder_solicitud_constructora(3, {"estado": "EN_PROCESO"}, token_jefe_obra)
    print("Respuesta transición 1:", res1)
    assert res1["success"] is True
    res_sol_2 = crm_services.listar_solicitudes_constructora(token_jefe_obra)
    sols_2 = res_sol_2.get("data", []) if isinstance(res_sol_2, dict) else res_sol_2
    sol3_en_proceso = next((s for s in sols_2 if s["id_solicitud"] == 3), None)
    print(f"Nuevo estado verificado en constructora: {sol3_en_proceso['estado']}")
    assert sol3_en_proceso["estado"] == "EN_PROCESO"

    print("\n=== 3. TRANSICIÓN 2: EN_PROCESO -> ATENDIDA CON RESPUESTA OFICIAL ===")
    respuesta_texto = "La unidad se encuentra actualmente en fase de instalaciones eléctricas."
    res2 = crm_services.responder_solicitud_constructora(3, {"estado": "ATENDIDA", "respuesta": respuesta_texto}, token_jefe_obra)
    print("Respuesta transición 2:", res2)
    assert res2["success"] is True
    res_sol_3 = crm_services.listar_solicitudes_constructora(token_jefe_obra)
    sols_3 = res_sol_3.get("data", []) if isinstance(res_sol_3, dict) else res_sol_3
    sol3_atendida = next((s for s in sols_3 if s["id_solicitud"] == 3), None)
    print(f"Estado final en constructora: {sol3_atendida['estado']}, Respuesta: {sol3_atendida['respuesta']}")
    assert sol3_atendida["estado"] == "ATENDIDA"
    assert sol3_atendida["respuesta"] == respuesta_texto

    print("\n=== 4. VERIFICAR COMO CLIENTE FABRICIO (Panel -> Mis solicitudes -> Ver detalle) ===")
    detalle_fabricio = crm_services.obtener_detalle_solicitud_cliente_autenticado(3, token_fabricio)
    print("Detalle recuperado por Fabricio:")
    print(json.dumps(detalle_fabricio, indent=2, default=str))
    assert detalle_fabricio["success"] is True
    data_fab = detalle_fabricio["data"]
    assert data_fab["id_solicitud"] == 3
    assert data_fab["estado"] == "ATENDIDA"
    assert data_fab["respuesta"] == respuesta_texto
    assert data_fab["fecha_respuesta"] is not None
    print("\n>>> FLUJO MANUAL E2E VALIDADO CON ÉXITO AL 100% <<<")


if __name__ == "__main__":
    run_e2e_solicitud_3()
