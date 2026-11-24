"""
Pruebas unitarias CU41 – Idempotencia transaccional y marcas temporales offline
sobre los flujos existentes de CU18 (avances) y CU19 (incidencias).
Aisladas sin conexión a base de datos productiva.
"""
import os
import sys
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.routes import avance_routes, incidencia_routes
from app.services import avance_services, incidencia_services, sync_offline_services
from app.utils.security import verificar_token

TOKEN_EMPRESA_3 = {
    "nro_usuario": 14,
    "nombre_rol": "JEFE DE OBRA",
    "id_empresa": 3,
}

TOKEN_EMPRESA_4 = {
    "nro_usuario": 22,
    "nombre_rol": "JEFE DE OBRA",
    "id_empresa": 4,
}


class FakeSyncStore:
    """Simula obras.t_sync_operacion_offline con unicidad por (empresa, usuario, tipo, clave)."""

    def __init__(self):
        self.rows = {}
        self.seq = 0
        self.marcas = []

    def reservar(self, id_empresa, id_usuario, tipo_operacion, id_obra, client_operation_id, fecha_ocurrencia_local):
        key = (id_empresa, id_usuario, tipo_operacion, client_operation_id)
        if key in self.rows:
            r = self.rows[key]
            return {
                "estado": "EXISTENTE",
                "id_sync": r["id_sync"],
                "estado_op": r["estado"],
                "id_recurso_creado": r["id_recurso_creado"],
                "respuesta_json": r["respuesta_json"],
                "fecha_ocurrencia_local": (
                    r["fecha_ocurrencia_local"].isoformat()
                    if hasattr(r["fecha_ocurrencia_local"], "isoformat")
                    else str(r["fecha_ocurrencia_local"])
                ),
                "fecha_sincronizacion": r["fecha_sincronizacion"],
            }
        self.seq += 1
        self.rows[key] = {
            "id_sync": self.seq,
            "estado": "EN_PROCESO",
            "id_recurso_creado": None,
            "respuesta_json": None,
            "fecha_ocurrencia_local": fecha_ocurrencia_local,
            "fecha_sincronizacion": "2026-11-24T12:00:00+00:00",
        }
        return {"estado": "NUEVA", "id_sync": self.seq}

    def completar(self, id_sync, id_recurso_creado, respuesta_json):
        for r in self.rows.values():
            if r["id_sync"] == id_sync:
                r["estado"] = "PROCESADO"
                r["id_recurso_creado"] = id_recurso_creado
                r["respuesta_json"] = dict(respuesta_json)
                return {"fecha_sincronizacion": r["fecha_sincronizacion"]}
        return {"fecha_sincronizacion": None}

    def liberar(self, id_sync):
        for key, r in list(self.rows.items()):
            if r["id_sync"] == id_sync and r["estado"] == "EN_PROCESO":
                del self.rows[key]

    def marcar(self, tabla, columna_pk, id_recurso, fecha_ocurrencia_local):
        self.marcas.append((tabla, columna_pk, id_recurso, fecha_ocurrencia_local))


def _patch_store(monkeypatch, store: FakeSyncStore):
    monkeypatch.setattr(sync_offline_services.sync_offline_repos, "reservar_operacion", store.reservar)
    monkeypatch.setattr(sync_offline_services.sync_offline_repos, "completar_operacion", store.completar)
    monkeypatch.setattr(sync_offline_services.sync_offline_repos, "liberar_operacion_fallida", store.liberar)
    monkeypatch.setattr(sync_offline_services.sync_offline_repos, "registrar_marcas_temporales_recurso", store.marcar)


def test_avance_online_sin_idempotency_conserva_contrato_exacto(monkeypatch):
    llamadas = []
    monkeypatch.setattr(
        avance_services.avance_repos,
        "registrar_avance_fn",
        lambda **kw: llamadas.append(kw) or {"success": True, "id_avance": 91},
    )
    monkeypatch.setattr(avance_services.bitacora_repos, "registrar_bitacora", lambda *a, **kw: None)
    reservar = Mock()
    monkeypatch.setattr(sync_offline_services.sync_offline_repos, "reservar_operacion", reservar)

    res = avance_services.registrar_avance(
        10,
        {"id_unidad": 5, "porcentaje_avance": 45, "observacion": "Online normal"},
        TOKEN_EMPRESA_3,
    )
    assert res == {"success": True, "id_avance": 91}
    assert len(llamadas) == 1
    reservar.assert_not_called()


def test_avance_offline_idempotente_evita_duplicados_y_conserva_fecha_local(monkeypatch):
    store = FakeSyncStore()
    _patch_store(monkeypatch, store)
    contador = {"n": 0}

    def fake_registrar(**kw):
        contador["n"] += 1
        return {"success": True, "id_avance": 200 + contador["n"]}

    monkeypatch.setattr(avance_services.avance_repos, "registrar_avance_fn", fake_registrar)
    monkeypatch.setattr(avance_services.bitacora_repos, "registrar_bitacora", lambda *a, **kw: None)

    payload = {
        "id_unidad": 7,
        "porcentaje_avance": 60,
        "observacion": "Registrado sin señal",
        "fecha_ocurrencia_local": "2026-11-23T15:30:00Z",
    }
    primero = avance_services.registrar_avance(
        10, payload, TOKEN_EMPRESA_3, idempotency_key="op-avance-uuid-1"
    )
    segundo = avance_services.registrar_avance(
        10, payload, TOKEN_EMPRESA_3, idempotency_key="op-avance-uuid-1"
    )

    assert contador["n"] == 1
    assert primero["id_avance"] == 201
    assert primero["duplicado_idempotente"] is False
    assert primero["fecha_ocurrencia_local"] == "2026-11-23T15:30:00+00:00"
    assert segundo["id_avance"] == 201
    assert segundo["duplicado_idempotente"] is True
    assert len(store.marcas) == 1
    assert store.marcas[0][0] == "t_avance_obra"


def test_avance_offline_error_libera_clave_para_reintento(monkeypatch):
    store = FakeSyncStore()
    _patch_store(monkeypatch, store)
    intento = {"n": 0}

    def fake_registrar(**kw):
        intento["n"] += 1
        if intento["n"] == 1:
            raise RuntimeError("Corte temporal de BD")
        return {"success": True, "id_avance": 305}

    monkeypatch.setattr(avance_services.avance_repos, "registrar_avance_fn", fake_registrar)
    monkeypatch.setattr(avance_services.bitacora_repos, "registrar_bitacora", lambda *a, **kw: None)

    with pytest.raises(RuntimeError):
        avance_services.registrar_avance(
            10, {"id_unidad": 7, "porcentaje_avance": 50}, TOKEN_EMPRESA_3, idempotency_key="op-retry-1"
        )

    reintento = avance_services.registrar_avance(
        10, {"id_unidad": 7, "porcentaje_avance": 50}, TOKEN_EMPRESA_3, idempotency_key="op-retry-1"
    )
    assert intento["n"] == 2
    assert reintento["id_avance"] == 305
    assert reintento["duplicado_idempotente"] is False


def test_incidencia_offline_idempotente_y_aislada_por_empresa(monkeypatch):
    store = FakeSyncStore()
    _patch_store(monkeypatch, store)
    creadas = []

    monkeypatch.setattr(
        incidencia_services.incidencia_repos,
        "obtener_empresa_obra",
        lambda id_obra, emp: emp,
    )
    monkeypatch.setattr(
        incidencia_services.incidencia_repos,
        "crear",
        lambda *a: creadas.append(a) or (500 + len(creadas)),
    )
    monkeypatch.setattr(incidencia_services.incidencia_repos, "crear_seguimiento", lambda *a: None)
    monkeypatch.setattr(incidencia_services.bitacora_repos, "registrar_bitacora", lambda *a, **kw: None)

    data = {
        "id_obra": 12,
        "titulo": "Fisura en losa",
        "descripcion": "Detectada en inspección sin señal",
        "prioridad": "ALTA",
        "fecha_ocurrencia_local": "2026-11-23T09:15:00-04:00",
    }

    r1 = incidencia_services.registrar(data, TOKEN_EMPRESA_3, idempotency_key="op-inc-uuid-1")
    r2 = incidencia_services.registrar(data, TOKEN_EMPRESA_3, idempotency_key="op-inc-uuid-1")
    # Misma clave en otra empresa NO colisiona ni expone datos de empresa 3
    r_otra_empresa = incidencia_services.registrar(data, TOKEN_EMPRESA_4, idempotency_key="op-inc-uuid-1")

    assert r1["id_incidencia"] == 501
    assert r2["id_incidencia"] == 501
    assert r2["duplicado_idempotente"] is True
    assert r_otra_empresa["id_incidencia"] == 502
    assert r_otra_empresa["duplicado_idempotente"] is False
    assert len(creadas) == 2


def test_conflicto_concurrente_devuelve_409_en_ruta(monkeypatch):
    store = FakeSyncStore()
    _patch_store(monkeypatch, store)
    # Simular operación ya EN_PROCESO
    store.reservar(3, 14, "INCIDENCIA", 12, "op-en-curso", "2026-11-23T10:00:00Z")

    monkeypatch.setattr(incidencia_services.incidencia_repos, "obtener_empresa_obra", lambda id_obra, emp: 3)
    monkeypatch.setattr(incidencia_services, "_tiene_permiso", lambda token, p: True)

    app = FastAPI()
    app.include_router(incidencia_routes.router, prefix="/api/incidencias")
    app.dependency_overrides[verificar_token] = lambda: TOKEN_EMPRESA_3

    with TestClient(app) as client:
        resp = client.post(
            "/api/incidencias/",
            headers={"Idempotency-Key": "op-en-curso"},
            json={
                "id_obra": 12,
                "titulo": "Corte eléctrico",
                "descripcion": "Sin energía en piso 2",
                "prioridad": "MEDIA",
            },
        )
    assert resp.status_code == 409
