"""
Suite de 3 pruebas integrativas principales para CU31:
Gestionar comercialización de unidades inmobiliarias (HU143, HU144, HU145, HU146).

Valida el flujo completo routes -> services -> repos -> PostgreSQL (doble transaccional en memoria):
1. Reserva exitosa + cambio a RESERVADA + historial.
2. Doble reserva o acceso de otro tenant rechazado (con rollback transaccional).
3. Cancelación/venta + sincronización correcta con CRM e historial.
"""
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException

os.environ["BACKUP_ENABLED"] = "false"

from app.routes import comercializacion_routes as routes
from app.services import comercializacion_services as services


TOKEN_EMPRESA_A = {
    "nro_usuario": 10,
    "id_usuario": 10,
    "username": "jefe.empresa.a",
    "nombre_rol": "ADMINISTRADOR_EMPRESA",
    "id_empresa": 100,
}

TOKEN_EMPRESA_B = {
    "nro_usuario": 20,
    "id_usuario": 20,
    "username": "jefe.empresa.b",
    "nombre_rol": "JEFE DE OBRA",
    "id_empresa": 200,
}


class FakeTransactionalConn:
    def __init__(self, store):
        self.store = store
        self.closed = 0

    def commit(self):
        self.store.commits += 1
        self.store._snapshot = self.store._clone_state()

    def rollback(self):
        self.store.rollbacks += 1
        self.store._restore_snapshot()


class InMemoryComercializacionDB:
    """
    Motor transaccional en memoria que simula fielmente las tablas de PostgreSQL:
    t_unidad_construccion, t_estructura_obra, t_obra, t_crm_cliente,
    t_crm_cliente_unidad y t_unidad_historial_comercial, soportando commit y rollback.
    """
    def __init__(self):
        self.unidades = {
            101: {
                "id_unidad": 101,
                "codigo": "DPTO-101",
                "tipo_unidad": "DEPARTAMENTO",
                "superficie": 95.5,
                "estado_constructivo": "EN_CONSTRUCCION",
                "estado_comercial": "DISPONIBLE",
                "publicado_comercial": False,
                "precio_venta": 85000.0,
                "moneda_comercial": "USD",
                "descripcion_comercial": "Departamento de 2 dormitorios",
                "id_estructura": 10,
                "nombre_estructura": "Torre Norte",
                "id_obra": 1,
                "nombre_obra": "Condominio Las Palmas",
                "codigo_obra": "OB-001",
                "id_empresa": 100,
            }
        }
        self.clientes = {
            501: {
                "id_cliente": 501,
                "id_empresa": 100,
                "nombre_completo": "Carlos Mendoza",
                "telefono": "70012345",
                "email": "carlos.mendoza@test.bo",
                "estado": "INTERESADO",
            },
            502: {
                "id_cliente": 502,
                "id_empresa": 100,
                "nombre_completo": "Ana Suárez",
                "telefono": "70099887",
                "email": "ana.suarez@test.bo",
                "estado": "NUEVO",
            },
            999: {
                "id_cliente": 999,
                "id_empresa": 200,  # Pertenece a otra empresa (Empresa B)
                "nombre_completo": "Cliente Otra Empresa",
                "telefono": "71100000",
                "email": "externo@otraempresa.bo",
                "estado": "NUEVO",
            },
        }
        self.usuarios = {
            10: "jefe.empresa.a",
            20: "jefe.empresa.b",
        }
        self.cliente_unidades = []
        self.historial = []
        self.fotografias = []
        self.commits = 0
        self.rollbacks = 0
        self._snapshot = self._clone_state()
        self.conn = FakeTransactionalConn(self)

    def _clone_state(self):
        import copy
        return copy.deepcopy((self.unidades, self.cliente_unidades, self.historial, self.fotografias))

    def _restore_snapshot(self):
        import copy
        u, cu, h, f = copy.deepcopy(self._snapshot)
        self.unidades = u
        self.cliente_unidades = cu
        self.historial = h
        self.fotografias = f

    def create_connection(self):
        self.conn = FakeTransactionalConn(self)

    def close_connection(self, commit=False):
        if commit:
            self.conn.commit()

    def execute_query(self, query, params=None, fetchall=False, fetchone=False, commit=False):
        q = " ".join(query.split())
        params = params or ()

        # 1. Verificación de pertenencia unidad-empresa
        if q.startswith("SELECT 1 FROM") and "t_unidad_construccion u" in q:
            id_unidad, id_empresa = int(params[0]), int(params[1])
            u = self.unidades.get(id_unidad)
            res = (1,) if (u and u["id_empresa"] == id_empresa) else None
            if commit:
                self.conn.commit()
            return res

        # 2. Bloqueo FOR UPDATE de unidad en transacciones
        if "FROM" in q and "t_unidad_construccion u" in q and "FOR UPDATE" in q:
            id_unidad, id_empresa = int(params[0]), int(params[1])
            u = self.unidades.get(id_unidad)
            if not u or u["id_empresa"] != id_empresa:
                return None
            if "moneda_comercial" in q:
                return (
                    u["id_unidad"],
                    u["codigo"],
                    u["estado_comercial"],
                    u["precio_venta"],
                    u["moneda_comercial"],
                )
            return (
                u["id_unidad"],
                u["codigo"],
                u["estado_comercial"],
                u["precio_venta"],
            )

        # 3. Ficha comercial base de unidad (obtener_unidad_comercial)
        if "u.estado AS estado_constructivo" in q and "WHERE u.id_unidad = %s AND o.id_empresa = %s" in q:
            id_unidad, id_empresa = int(params[0]), int(params[1])
            u = self.unidades.get(id_unidad)
            if not u or u["id_empresa"] != id_empresa:
                return None
            bloqueada = any(
                cu["id_unidad"] == id_unidad and cu["estado_asociacion"] in ("RESERVADO", "VENDIDO", "ENTREGADO")
                for cu in self.cliente_unidades
            )
            disp_efectiva = (u["estado_comercial"] == "DISPONIBLE") and not bloqueada
            return (
                u["id_unidad"],
                u["codigo"],
                u["tipo_unidad"],
                u["superficie"],
                u["estado_constructivo"],
                u["estado_comercial"],
                u["publicado_comercial"],
                u["precio_venta"],
                u["moneda_comercial"],
                u["descripcion_comercial"],
                u["id_estructura"],
                u["nombre_estructura"],
                u["id_obra"],
                u["nombre_obra"],
                u["codigo_obra"],
                u["id_empresa"],
                disp_efectiva,
            )

        # 4. Verificación de cliente por empresa
        if "FROM" in q and "t_crm_cliente c" in q and "WHERE c.id_cliente = %s AND c.id_empresa = %s" in q:
            id_cliente, id_empresa = int(params[0]), int(params[1])
            c = self.clientes.get(id_cliente)
            if not c or c["id_empresa"] != id_empresa:
                return None
            if "c.tipo_cliente" in q:
                return (c["id_cliente"], c["id_empresa"], c["nombre_completo"], c["email"], c["telefono"], "PROSPECTO", c["estado"])
            return (c["id_cliente"], c["nombre_completo"], c["estado"])

        # 5. Consulta de asociación CRM activa en obtener_unidad_comercial
        if "FROM" in q and "t_crm_cliente_unidad cu" in q and "c.id_empresa = %s" in q:
            id_unidad, id_empresa = int(params[0]), int(params[1])
            activas = [
                cu for cu in self.cliente_unidades
                if cu["id_unidad"] == id_unidad
                and self.clientes.get(cu["id_cliente"], {}).get("id_empresa") == id_empresa
                and cu["estado_asociacion"] in ("RESERVADO", "VENDIDO", "ENTREGADO", "INTERESADO")
            ]
            if not activas:
                return None
            cu = activas[-1]
            c = self.clientes[cu["id_cliente"]]
            return (
                cu["id_cliente_unidad"],
                cu["id_cliente"],
                cu["estado_asociacion"],
                cu["monto_pactado"],
                cu["monto_reserva"],
                cu["fecha_vencimiento_reserva"],
                cu["fecha_asociacion"],
                cu["observaciones"],
                c["nombre_completo"],
                c["telefono"],
                c["email"],
                cu["id_usuario_registro"],
            )

        # 6. Consulta de asociación activa FOR UPDATE (RESERVADO, VENDIDO, ENTREGADO)
        if "FROM" in q and "t_crm_cliente_unidad" in q and "IN ('RESERVADO', 'VENDIDO', 'ENTREGADO')" in q and "FOR UPDATE" in q:
            id_unidad = int(params[0])
            for cu in self.cliente_unidades:
                if cu["id_unidad"] == id_unidad and cu["estado_asociacion"] in ("RESERVADO", "VENDIDO", "ENTREGADO"):
                    if "monto_pactado" in q and q.index("monto_pactado") < q.index("FROM"):
                        if q.startswith("SELECT id_cliente_unidad, id_cliente, monto_pactado, estado_asociacion"):
                            return (cu["id_cliente_unidad"], cu["id_cliente"], cu["monto_pactado"], cu["estado_asociacion"])
                        return (cu["id_cliente_unidad"], cu["id_cliente"], cu["estado_asociacion"], cu["monto_pactado"])
                    return (cu["id_cliente_unidad"], cu["estado_asociacion"], cu["id_cliente"])
            return None

        # 7. Consulta de asociación INTERESADO previa del mismo cliente
        if "FROM" in q and "t_crm_cliente_unidad" in q and "estado_asociacion = 'INTERESADO'" in q:
            id_unidad, id_cliente = int(params[0]), int(params[1])
            for cu in self.cliente_unidades:
                if cu["id_unidad"] == id_unidad and cu["id_cliente"] == id_cliente and cu["estado_asociacion"] == "INTERESADO":
                    return (cu["id_cliente_unidad"],)
            return None

        # 8. INSERT en t_crm_cliente_unidad
        if q.startswith("INSERT INTO") and "t_crm_cliente_unidad" in q:
            nuevo_id = len(self.cliente_unidades) + 1
            if "'RESERVADO'" in q:
                id_cliente, id_unidad, monto_pactado, monto_reserva, fecha_venc, id_usuario, obs = params
                estado_asoc = "RESERVADO"
            else:
                id_cliente, id_unidad, monto_pactado, id_usuario, obs = params
                monto_reserva, fecha_venc = None, None
                estado_asoc = "VENDIDO"
            registro = {
                "id_cliente_unidad": nuevo_id,
                "id_cliente": int(id_cliente),
                "id_unidad": int(id_unidad),
                "estado_asociacion": estado_asoc,
                "monto_pactado": monto_pactado,
                "monto_reserva": monto_reserva,
                "fecha_vencimiento_reserva": fecha_venc,
                "id_usuario_registro": id_usuario,
                "observaciones": obs,
                "fecha_asociacion": datetime.now(timezone.utc).isoformat(),
            }
            self.cliente_unidades.append(registro)
            if commit:
                self.conn.commit()
            return (nuevo_id,)

        # 9. UPDATE en t_crm_cliente_unidad
        if q.startswith("UPDATE") and "t_crm_cliente_unidad" in q:
            if "SET estado_asociacion = 'CANCELADO'" in q:
                obs, id_cu = params
                for cu in self.cliente_unidades:
                    if cu["id_cliente_unidad"] == int(id_cu):
                        cu["estado_asociacion"] = "CANCELADO"
                        cu["observaciones"] = obs
            elif "SET estado_asociacion = 'VENDIDO'" in q:
                monto_pactado, obs, id_cu = params[0], params[-2], params[-1]
                for cu in self.cliente_unidades:
                    if cu["id_cliente_unidad"] == int(id_cu):
                        cu["estado_asociacion"] = "VENDIDO"
                        cu["monto_pactado"] = monto_pactado
                        if obs:
                            cu["observaciones"] = obs
            if commit:
                self.conn.commit()
            return 1

        # 10. UPDATE en t_unidad_construccion
        if q.startswith("UPDATE") and "t_unidad_construccion" in q:
            if "SET estado_comercial = 'RESERVADA'" in q:
                id_unidad = int(params[0])
                self.unidades[id_unidad]["estado_comercial"] = "RESERVADA"
            elif "SET estado_comercial = 'DISPONIBLE'" in q:
                id_unidad = int(params[0])
                self.unidades[id_unidad]["estado_comercial"] = "DISPONIBLE"
            elif "SET estado_comercial = 'VENDIDA'" in q:
                id_unidad = int(params[0])
                self.unidades[id_unidad]["estado_comercial"] = "VENDIDA"
            else:
                id_unidad, id_empresa = int(params[-2]), int(params[-1])
                u = self.unidades.get(id_unidad)
                if u and u["id_empresa"] == id_empresa:
                    idx = 0
                    for col in ("publicado_comercial", "precio_venta", "moneda_comercial", "descripcion_comercial", "estado_comercial"):
                        if f"{col} = %s" in q:
                            u[col] = params[idx]
                            idx += 1
            if commit:
                self.conn.commit()
            return 1

        # 11. INSERT en t_unidad_historial_comercial
        if q.startswith("INSERT INTO") and "t_unidad_historial_comercial" in q:
            nuevo_id = len(self.historial) + 1
            if "'RESERVA'" in q:
                id_u, id_c, id_cu, est_ant, precio_v, monto_p, obs, id_usr = params
                tipo_ev, est_nuevo = "RESERVA", "RESERVADA"
            elif "'CANCELACION'" in q:
                id_u, id_c, id_cu, est_ant, precio_v, monto_p, obs, id_usr = params
                tipo_ev, est_nuevo = "CANCELACION", "DISPONIBLE"
            elif "'VENTA'" in q:
                id_u, id_c, id_cu, est_ant, precio_v, monto_p, obs, id_usr = params
                tipo_ev, est_nuevo = "VENTA", "VENDIDA"
            else:
                id_u, tipo_ev, est_ant, est_nuevo, precio_v, monto_p, obs, id_usr, id_c, id_cu = params

            self.historial.append({
                "id_historial": nuevo_id,
                "id_unidad": int(id_u),
                "id_cliente": int(id_c) if id_c is not None else None,
                "id_cliente_unidad": int(id_cu) if id_cu is not None else None,
                "tipo_evento": tipo_ev,
                "estado_anterior": est_ant,
                "estado_nuevo": est_nuevo,
                "precio_venta": precio_v,
                "monto_pactado": monto_p,
                "observacion": obs,
                "id_usuario": id_usr,
                "fecha": datetime.now(timezone.utc).isoformat(),
            })
            if commit:
                self.conn.commit()
            return (nuevo_id,)

        # 12. SELECT de fotografías
        if "FROM" in q and "t_unidad_fotografia" in q:
            return []

        # 13. SELECT de historial comercial (HU146 y obtener_unidad_comercial)
        if "FROM" in q and "t_unidad_historial_comercial h" in q:
            id_unidad = int(params[0])
            eventos = [h for h in reversed(self.historial) if h["id_unidad"] == id_unidad]
            incluye_id_unidad = "h.id_unidad," in q
            filas = []
            for h in eventos:
                usr_name = self.usuarios.get(h["id_usuario"], "sistema")
                cli_name = self.clientes.get(h["id_cliente"], {}).get("nombre_completo") if h["id_cliente"] else None
                cu_match = next((cu for cu in self.cliente_unidades if cu["id_cliente_unidad"] == h["id_cliente_unidad"]), None)
                if incluye_id_unidad:
                    filas.append((
                        h["id_historial"],
                        h["id_unidad"],
                        h["tipo_evento"],
                        h["estado_anterior"],
                        h["estado_nuevo"],
                        h["precio_venta"],
                        h["monto_pactado"],
                        h["observacion"],
                        h["fecha"],
                        usr_name,
                        cli_name,
                        h["id_cliente"],
                        h["id_cliente_unidad"],
                        h["id_usuario"],
                        cu_match["monto_reserva"] if cu_match else None,
                        cu_match["fecha_vencimiento_reserva"] if cu_match else None,
                        cu_match["estado_asociacion"] if cu_match else None,
                    ))
                else:
                    filas.append((
                        h["id_historial"],
                        h["tipo_evento"],
                        h["estado_anterior"],
                        h["estado_nuevo"],
                        h["precio_venta"],
                        h["monto_pactado"],
                        h["observacion"],
                        h["fecha"],
                        usr_name,
                        cli_name,
                        h["id_cliente"],
                        h["id_cliente_unidad"],
                        h["id_usuario"],
                    ))
            return filas

        return [] if fetchall else None


def _mock_request():
    req = MagicMock()
    req.client.host = "127.0.0.1"
    return req


# =============================================================================
# PRUEBA INTEGRATIVA 1: RESERVA EXITOSA + CAMBIO A RESERVADA + HISTORIAL
# =============================================================================
def test_1_reserva_exitosa_cambio_a_reservada_e_historial():
    """
    Verifica el flujo integrativo completo (routes -> services -> repos -> DB):
    - Publicación y actualización comercial previa (HU143).
    - Registro atómico de reserva para cliente de la misma empresa (HU144).
    - Cambio de estado_comercial a RESERVADA conservando estado constructivo intacto.
    - Persistencia de monto_reserva, fecha_vencimiento_reserva e id_usuario_registro en CRM.
    - Registro y consulta cronológica del historial comercial (HU146).
    """
    fake_db = InMemoryComercializacionDB()
    req = _mock_request()

    with patch("app.repos.comercializacion_repos.PostgreSQL", return_value=fake_db), \
         patch("app.services.comercializacion_services.bitacora_repos.registrar_bitacora"):

        # 1. Publicar y actualizar precio de la unidad (HU143)
        ficha_pub = routes.patch_unidad_comercial(
            id_unidad=101,
            request=req,
            datos={
                "publicado_comercial": True,
                "precio_venta": 88000.0,
                "moneda_comercial": "USD",
                "descripcion_comercial": "Departamento de lujo con vista panorámica",
            },
            token=TOKEN_EMPRESA_A,
        )
        assert ficha_pub["publicado_comercial"] is True
        assert ficha_pub["precio_venta"] == 88000.0
        assert ficha_pub["estado_constructivo"] == "EN_CONSTRUCCION"

        # 2. Registrar reserva para cliente 501 de la misma Empresa A (HU144)
        res_reserva = routes.post_reserva_unidad(
            id_unidad=101,
            request=req,
            datos={
                "id_cliente": 501,
                "monto_reserva": 5000.0,
                "monto_pactado": 87500.0,
                "fecha_vencimiento_reserva": "2026-12-20",
                "observaciones": "Reserva con abono en cuenta bancaria",
            },
            token=TOKEN_EMPRESA_A,
        )

        assert res_reserva["estado_comercial"] == "RESERVADA"
        assert res_reserva["estado_asociacion"] == "RESERVADO"
        assert res_reserva["monto_reserva"] == 5000.0
        assert res_reserva["monto_pactado"] == 87500.0
        assert res_reserva["fecha_vencimiento_reserva"] == "2026-12-20"
        assert res_reserva["id_usuario_registro"] == 10

        # 3. Verificar que la unidad ya no está disponible y conserva su estado constructivo
        disp = routes.get_disponibilidad_unidad(id_unidad=101, token=TOKEN_EMPRESA_A)
        assert disp["estado_comercial"] == "RESERVADA"
        assert disp["estado_constructivo"] == "EN_CONSTRUCCION"
        assert disp["disponible_efectiva"] is False
        assert disp["bloqueada_por_crm"] is True

        # 4. Consultar historial comercial (HU146)
        hist_resp = routes.get_historial_comercial(id_unidad=101, token=TOKEN_EMPRESA_A)
        eventos = hist_resp["historial"]
        tipos = [e["tipo_evento"] for e in eventos]
        assert "RESERVA" in tipos
        assert "PUBLICACION" in tipos
        assert "ACTUALIZACION_PRECIO" in tipos

        evento_reserva = next(e for e in eventos if e["tipo_evento"] == "RESERVA")
        assert evento_reserva["estado_anterior"] == "DISPONIBLE"
        assert evento_reserva["estado_nuevo"] == "RESERVADA"
        assert evento_reserva["cliente_relacionado"] == "Carlos Mendoza"
        assert evento_reserva["monto_reserva"] == 5000.0
        assert evento_reserva["usuario_registro"] == "jefe.empresa.a"


# =============================================================================
# PRUEBA INTEGRATIVA 2: DOBLE RESERVA O ACCESO DE OTRO TENANT RECHAZADO
# =============================================================================
def test_2_doble_reserva_o_acceso_otro_tenant_rechazado():
    """
    Verifica seguridad multi-tenant y atomicidad transaccional:
    - Impedir doble reserva activa sobre una unidad ya reservada (409 Conflict + rollback).
    - Impedir asociar un cliente de Empresa B con una unidad de Empresa A (403 Forbidden + rollback).
    - Impedir que un usuario de Empresa B opere sobre unidad de Empresa A, incluso enviando id_empresa=100.
    - Impedir intento de modificar estado constructivo o path traversal en fotografías.
    """
    fake_db = InMemoryComercializacionDB()
    req = _mock_request()

    with patch("app.repos.comercializacion_repos.PostgreSQL", return_value=fake_db), \
         patch("app.services.comercializacion_services.bitacora_repos.registrar_bitacora"):

        # 1. Intentar reservar unidad de Empresa A (100) con cliente 999 que pertenece a Empresa B (200)
        rollbacks_antes = fake_db.rollbacks
        with pytest.raises(HTTPException) as exc_cross_client:
            routes.post_reserva_unidad(
                id_unidad=101,
                request=req,
                datos={"id_cliente": 999, "monto_reserva": 3000.0},
                token=TOKEN_EMPRESA_A,
            )
        assert exc_cross_client.value.status_code == 403
        assert fake_db.rollbacks == rollbacks_antes + 1
        assert fake_db.unidades[101]["estado_comercial"] == "DISPONIBLE"

        # 2. Usuario de Empresa B (200) intenta reservar unidad 101 de Empresa A enviando id_empresa=100
        with pytest.raises(HTTPException) as exc_cross_tenant:
            routes.post_reserva_unidad(
                id_unidad=101,
                request=req,
                datos={"id_cliente": 501, "monto_reserva": 3000.0},
                id_empresa=100,  # Intento de suplantar id_empresa desde frontend
                token=TOKEN_EMPRESA_B,
            )
        assert exc_cross_tenant.value.status_code == 404
        assert fake_db.unidades[101]["estado_comercial"] == "DISPONIBLE"

        # 3. Registrar primera reserva válida con cliente 501 (Empresa A)
        routes.post_reserva_unidad(
            id_unidad=101,
            request=req,
            datos={"id_cliente": 501, "monto_reserva": 4000.0},
            token=TOKEN_EMPRESA_A,
        )
        assert fake_db.unidades[101]["estado_comercial"] == "RESERVADA"

        # 4. Intentar doble reserva sobre la misma unidad 101 con otro cliente (502) de Empresa A
        rollbacks_antes_doble = fake_db.rollbacks
        with pytest.raises(HTTPException) as exc_doble:
            routes.post_reserva_unidad(
                id_unidad=101,
                request=req,
                datos={"id_cliente": 502, "monto_reserva": 6000.0},
                token=TOKEN_EMPRESA_A,
            )
        assert exc_doble.value.status_code == 409
        assert fake_db.rollbacks == rollbacks_antes_doble + 1
        # La reserva original del cliente 501 permanece intacta tras el rollback
        assert len(fake_db.cliente_unidades) == 1
        assert fake_db.cliente_unidades[0]["id_cliente"] == 501

        # 5. Bloquear intento de path traversal en nombre de archivo
        with pytest.raises(services.ComercializacionError) as exc_traversal:
            services._sanitizar_nombre_archivo("../../etc/passwd")
        assert exc_traversal.value.status_code == 400


# =============================================================================
# PRUEBA INTEGRATIVA 3: CANCELACIÓN / VENTA + SINCRONIZACIÓN CRM E HISTORIAL
# =============================================================================
def test_3_cancelacion_y_venta_sincronizacion_crm_e_historial():
    """
    Verifica el ciclo completo de control de estados comerciales (HU145 y HU146):
    - Reserva activa -> Cancelación/liberación a DISPONIBLE + sincronización CRM (CANCELADO) + historial (CANCELACION).
    - Nueva reserva -> Confirmación de venta a VENDIDA + sincronización CRM (VENDIDO) + historial (VENTA).
    - Bloqueo de transiciones inconsistentes desde el estado terminal VENDIDA.
    """
    fake_db = InMemoryComercializacionDB()
    req = _mock_request()

    with patch("app.repos.comercializacion_repos.PostgreSQL", return_value=fake_db), \
         patch("app.services.comercializacion_services.bitacora_repos.registrar_bitacora"):

        # 1. Reservar inicialmente para cliente 501
        routes.post_reserva_unidad(
            id_unidad=101,
            request=req,
            datos={"id_cliente": 501, "monto_reserva": 3500.0},
            token=TOKEN_EMPRESA_A,
        )
        assert fake_db.unidades[101]["estado_comercial"] == "RESERVADA"

        # 2. Cancelar/liberar la reserva -> vuelve a DISPONIBLE y sincroniza CRM a CANCELADO
        res_cancel = routes.post_cancelar_reserva_unidad(
            id_unidad=101,
            request=req,
            datos={"motivo": "Cliente desistió por financiamiento"},
            token=TOKEN_EMPRESA_A,
        )
        assert res_cancel["estado_comercial"] == "DISPONIBLE"
        assert res_cancel["estado_asociacion"] == "CANCELADO"
        assert fake_db.unidades[101]["estado_comercial"] == "DISPONIBLE"
        assert fake_db.cliente_unidades[0]["estado_asociacion"] == "CANCELADO"

        # Verificar que la unidad volvió a estar efectivamente disponible
        disp = routes.get_disponibilidad_unidad(id_unidad=101, token=TOKEN_EMPRESA_A)
        assert disp["disponible_efectiva"] is True

        # 3. Reservar para cliente 502 y luego confirmar la venta
        routes.post_reserva_unidad(
            id_unidad=101,
            request=req,
            datos={"id_cliente": 502, "monto_reserva": 6000.0, "monto_pactado": 84000.0},
            token=TOKEN_EMPRESA_A,
        )
        res_venta = routes.post_confirmar_venta_unidad(
            id_unidad=101,
            request=req,
            datos={"monto_pactado": 83500.0, "observaciones": "Minuta de compraventa firmada"},
            token=TOKEN_EMPRESA_A,
        )
        assert res_venta["estado_comercial"] == "VENDIDA"
        assert res_venta["estado_asociacion"] == "VENDIDO"
        assert res_venta["id_cliente"] == 502
        assert res_venta["monto_pactado"] == 83500.0
        assert fake_db.unidades[101]["estado_comercial"] == "VENDIDA"
        assert fake_db.cliente_unidades[1]["estado_asociacion"] == "VENDIDO"

        # 4. Bloquear estados inconsistentes: una unidad VENDIDA no puede cancelarse ni revertirse a DISPONIBLE
        with pytest.raises(HTTPException) as exc_inconsistente:
            routes.patch_estado_comercial_unidad(
                id_unidad=101,
                request=req,
                datos={"estado_comercial": "DISPONIBLE"},
                token=TOKEN_EMPRESA_A,
            )
        assert exc_inconsistente.value.status_code == 400

        with pytest.raises(HTTPException) as exc_cancel_vendida:
            routes.post_cancelar_reserva_unidad(
                id_unidad=101,
                request=req,
                datos={"motivo": "Intento inválido sobre unidad vendida"},
                token=TOKEN_EMPRESA_A,
            )
        assert exc_cancel_vendida.value.status_code == 400

        # 5. Verificar trazabilidad completa en historial comercial (HU146)
        hist = routes.get_historial_comercial(id_unidad=101, token=TOKEN_EMPRESA_A)
        secuencia_eventos = [h["tipo_evento"] for h in hist["historial"]]
        # Orden cronológico inverso (más reciente primero): VENTA, RESERVA, CANCELACION, RESERVA
        assert secuencia_eventos == ["VENTA", "RESERVA", "CANCELACION", "RESERVA"]
        assert hist["historial"][0]["estado_nuevo"] == "VENDIDA"
        assert hist["historial"][0]["cliente_relacionado"] == "Ana Suárez"
        assert hist["historial"][0]["monto_pactado"] == 83500.0
