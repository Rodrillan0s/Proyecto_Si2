"""
Pruebas unitarias CU42 – Garantías Inmobiliarias y Servicio Posventa (HU161–HU168).
Aisladas sin conexión a base de datos productiva.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services import garantia_posventa_services as service

ADMIN_EMP_3 = {"nro_usuario": 10, "nombre_rol": "ADMINISTRADOR_EMPRESA", "id_empresa": 3}
ADMIN_EMP_4 = {"nro_usuario": 20, "nombre_rol": "ADMINISTRADOR_EMPRESA", "id_empresa": 4}
CLIENTE_E3 = {"nro_usuario": 30, "nombre_rol": "CLIENTE", "id_empresa": 3}
TECNICO_E3 = {"nro_usuario": 40, "nombre_rol": "ELECTRICO", "id_empresa": 3}
TECNICO_E4 = {"nro_usuario": 50, "nombre_rol": "ELECTRICO", "id_empresa": 4}


class FakePosventaRepo:
    def __init__(self):
        self.unidades = {
            101: {"id_unidad": 101, "unidad_codigo": "U-101", "unidad_nombre": "Dpto 101", "id_obra": 10, "obra_nombre": "Torre A", "id_empresa": 3},
            202: {"id_unidad": 202, "unidad_codigo": "U-202", "unidad_nombre": "Dpto 202", "id_obra": 20, "obra_nombre": "Torre B", "id_empresa": 4},
        }
        self.usuarios = {
            (40, 3): {"id_usuario": 40, "id_empresa": 3, "nombre_rol": "ELECTRICO", "nombre_completo": "Carlos Técnico"},
            (30, 3): {"id_usuario": 30, "id_empresa": 3, "nombre_rol": "CLIENTE", "nombre_completo": "Ana Cliente"},
            (50, 4): {"id_usuario": 50, "id_empresa": 4, "nombre_rol": "ELECTRICO", "nombre_completo": "Luis Otra Empresa"},
        }
        self.garantias = {}
        self.solicitudes = {}
        self.seguimientos = []
        self.g_seq = 0
        self.s_seq = 0

    def obtener_unidad_con_empresa(self, id_unidad):
        return self.unidades.get(id_unidad)

    def obtener_usuario_activo_empresa(self, id_usuario, id_empresa):
        return self.usuarios.get((id_usuario, id_empresa))

    def crear_garantia(self, id_empresa, id_unidad, codigo, tipo_garantia, descripcion, fecha_inicio, fecha_fin, observaciones, id_usuario_registro):
        self.g_seq += 1
        g = {
            "id_garantia": self.g_seq,
            "id_empresa": id_empresa,
            "id_unidad": id_unidad,
            "codigo": codigo,
            "tipo_garantia": tipo_garantia,
            "descripcion": descripcion,
            "fecha_inicio": fecha_inicio.isoformat(),
            "fecha_fin": fecha_fin.isoformat() if fecha_fin else None,
            "observaciones": observaciones,
            "id_usuario_registro": id_usuario_registro,
            "creado_en": "2026-11-24T00:00:00Z",
        }
        self.garantias[self.g_seq] = g
        return g

    def obtener_garantia_por_id(self, id_garantia, id_empresa=None):
        g = self.garantias.get(id_garantia)
        if not g:
            return None
        if id_empresa is not None and g["id_empresa"] != id_empresa:
            return None
        return dict(g)

    def listar_garantias(self, id_empresa=None, id_unidad=None, id_cliente=None):
        out = []
        for g in self.garantias.values():
            if id_empresa is not None and g["id_empresa"] != id_empresa:
                continue
            if id_unidad is not None and g["id_unidad"] != id_unidad:
                continue
            out.append(dict(g))
        return out

    def crear_solicitud_posventa(self, id_empresa, id_unidad, id_cliente, id_garantia, titulo, descripcion, id_usuario_creacion):
        self.s_seq += 1
        self.solicitudes[self.s_seq] = {
            "id_solicitud_posventa": self.s_seq,
            "id_empresa": id_empresa,
            "id_unidad": id_unidad,
            "id_cliente": id_cliente,
            "id_garantia": id_garantia,
            "titulo": titulo,
            "descripcion": descripcion,
            "categoria": None,
            "estado": "REGISTRADA",
            "id_responsable": None,
            "id_usuario_creacion": id_usuario_creacion,
            "creado_en": "2026-11-24T01:00:00Z",
        }
        return self.s_seq

    def registrar_seguimiento(self, id_solicitud_posventa, id_usuario, accion, estado_anterior, estado_nuevo, observacion):
        ev = {
            "id_seguimiento": len(self.seguimientos) + 1,
            "id_solicitud_posventa": id_solicitud_posventa,
            "id_usuario": id_usuario,
            "accion": accion,
            "estado_anterior": estado_anterior,
            "estado_nuevo": estado_nuevo,
            "observacion": observacion,
        }
        self.seguimientos.append(ev)
        return ev

    def actualizar_clasificacion(self, id_solicitud, categoria, nuevo_estado):
        self.solicitudes[id_solicitud]["categoria"] = categoria
        self.solicitudes[id_solicitud]["estado"] = nuevo_estado

    def actualizar_asignacion(self, id_solicitud, id_responsable, nuevo_estado):
        self.solicitudes[id_solicitud]["id_responsable"] = id_responsable
        self.solicitudes[id_solicitud]["estado"] = nuevo_estado

    def actualizar_estado(self, id_solicitud, nuevo_estado):
        self.solicitudes[id_solicitud]["estado"] = nuevo_estado

    def obtener_solicitud_por_id(self, id_solicitud, id_empresa=None):
        s = self.solicitudes.get(id_solicitud)
        if not s:
            return None
        if id_empresa is not None and s["id_empresa"] != id_empresa:
            return None
        return dict(s)

    def listar_solicitudes(self, id_empresa=None, id_cliente=None, id_unidad=None, estado=None, categoria=None, id_responsable=None):
        out = []
        for s in self.solicitudes.values():
            if id_empresa is not None and s["id_empresa"] != id_empresa:
                continue
            if id_cliente is not None and s["id_cliente"] != id_cliente:
                continue
            if id_unidad is not None and s["id_unidad"] != id_unidad:
                continue
            if estado is not None and s["estado"] != estado:
                continue
            if categoria is not None and s["categoria"] != categoria:
                continue
            if id_responsable is not None and s["id_responsable"] != id_responsable:
                continue
            out.append(dict(s))
        return out

    def listar_seguimiento_solicitud(self, id_solicitud):
        return [dict(e) for e in self.seguimientos if e["id_solicitud_posventa"] == id_solicitud]


@pytest.fixture
def fake_env(monkeypatch):
    fake = FakePosventaRepo()
    monkeypatch.setattr(service, "repo", fake)
    monkeypatch.setattr(service.bitacora_repos, "registrar_bitacora", lambda *a, **kw: None)
    monkeypatch.setattr(
        service.crm_repos,
        "obtener_id_cliente_por_usuario_empresa",
        lambda u, e: 700 if (u, e) == (30, 3) else None,
    )
    monkeypatch.setattr(
        service.crm_repos,
        "validar_unidad_asociada_cliente",
        lambda c, u: (c, u) == (700, 101),
    )
    return fake


def test_hu161_hu162_registrar_y_consultar_garantia_aislada_por_empresa(fake_env):
    res = service.registrar_garantia(
        {
            "id_unidad": 101,
            "codigo": "GAR-101",
            "tipo_garantia": "Instalaciones",
            "descripcion": "Cobertura registrada sin fecha de vencimiento asumida",
            "fecha_inicio": "2026-11-01",
        },
        ADMIN_EMP_3,
    )
    assert res["success"] is True
    assert res["data"]["fecha_fin"] is None

    # Otra empresa no puede registrar sobre unidad 101 ni ver la garantía
    with pytest.raises(service.PosventaError) as exc:
        service.registrar_garantia(
            {"id_unidad": 101, "tipo_garantia": "X", "descripcion": "Y", "fecha_inicio": "2026-11-01"},
            ADMIN_EMP_4,
        )
    assert exc.value.status_code == 403
    assert service.listar_garantias(ADMIN_EMP_4)["data"] == []
    assert len(service.listar_garantias(CLIENTE_E3)["data"]) == 1


def test_hu163_a_hu168_flujo_completo_sin_garantia_y_trazabilidad(fake_env):
    # HU163: Cliente registra solicitud SIN garantía asociada (id_garantia opcional)
    creada = service.registrar_solicitud_posventa(
        {
            "id_unidad": 101,
            "titulo": "Tomacorriente flojo",
            "descripcion": "En dormitorio principal no hace buen contacto.",
        },
        CLIENTE_E3,
    )
    id_sol = creada["id_solicitud_posventa"]
    assert creada["data"]["estado"] == "REGISTRADA"
    assert creada["data"]["id_garantia"] is None

    # Cliente no puede registrar sobre unidad de otra empresa
    with pytest.raises(service.PosventaError) as exc:
        service.registrar_solicitud_posventa(
            {"id_unidad": 202, "titulo": "Ajena", "descripcion": "No autorizada"},
            CLIENTE_E3,
        )
    assert exc.value.status_code == 403

    # HU164: Clasificar NO altera la descripción original del cliente
    clasif = service.clasificar_solicitud(
        id_sol,
        {"categoria": "INSTALACION_ELECTRICA", "observacion": "Derivado a área eléctrica"},
        ADMIN_EMP_3,
    )
    assert clasif["data"]["categoria"] == "INSTALACION_ELECTRICA"
    assert clasif["data"]["estado"] == "CLASIFICADA"
    assert clasif["data"]["descripcion"] == "En dormitorio principal no hace buen contacto."

    # HU165: No se puede asignar usuario de otra empresa ni usuario CLIENTE
    with pytest.raises(service.PosventaError) as exc_cross:
        service.asignar_responsable(id_sol, {"id_responsable": 50}, ADMIN_EMP_3)
    assert exc_cross.value.status_code == 403

    with pytest.raises(service.PosventaError) as exc_cli:
        service.asignar_responsable(id_sol, {"id_responsable": 30}, ADMIN_EMP_3)
    assert exc_cli.value.status_code == 400

    asig = service.asignar_responsable(id_sol, {"id_responsable": 40}, ADMIN_EMP_3)
    assert asig["data"]["estado"] == "ASIGNADA"
    assert asig["data"]["id_responsable"] == 40

    # HU166: Transiciones válidas y rechazo de estado no aprobado (RECHAZADA) o salto ilegal
    with pytest.raises(service.PosventaError):
        service.gestionar_atencion(id_sol, {"estado": "RECHAZADA", "observacion": "No permitido"}, ADMIN_EMP_3)

    with pytest.raises(service.PosventaError) as exc_salto:
        service.gestionar_atencion(id_sol, {"estado": "CERRADA", "observacion": "Salto ilegal"}, ADMIN_EMP_3)
    assert exc_salto.value.status_code == 409

    # El técnico asignado puede gestionar atención
    en_atencion = service.gestionar_atencion(
        id_sol, {"estado": "EN_ATENCION", "observacion": "Visita iniciada en unidad"}, TECNICO_E3
    )
    assert en_atencion["data"]["estado"] == "EN_ATENCION"

    resuelta = service.gestionar_atencion(
        id_sol, {"estado": "RESUELTA", "observacion": "Tomacorriente reemplazado y probado"}, TECNICO_E3
    )
    assert resuelta["data"]["estado"] == "RESUELTA"

    cerrada = service.gestionar_atencion(
        id_sol, {"estado": "CERRADA", "observacion": "Conformidad del propietario"}, ADMIN_EMP_3
    )
    assert cerrada["data"]["estado"] == "CERRADA"

    # HU167 & HU168: Seguimiento e historial consolidado por unidad
    seg = service.obtener_seguimiento_solicitud(id_sol, CLIENTE_E3)["data"]["seguimiento"]
    assert len(seg) == 6  # REGISTRO, CLASIFICACION, ASIGNACION, EN_ATENCION, RESUELTA, CERRADA

    hist = service.consultar_historial_unidad(101, CLIENTE_E3)["data"]
    assert hist["unidad"]["id_unidad"] == 101
    assert len(hist["solicitudes"]) == 1
    assert len(hist["solicitudes"][0]["seguimiento"]) == 6

    # Otra empresa no puede ver el historial de la unidad 101
    with pytest.raises(service.PosventaError) as exc_hist:
        service.consultar_historial_unidad(101, ADMIN_EMP_4)
    assert exc_hist.value.status_code == 403
