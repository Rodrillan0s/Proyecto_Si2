import inspect
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from app.repos import crm_repos, incidencia_repos, notificaciones_repos, unidad_repos
from app.routes import crm_routes, unidad_routes
from app.services import crm_services, unidad_services


class FakeDatabase:
    def __init__(self, rows=None, row=None, columns=None):
        self.rows = rows or []
        self.row = row
        self.columns = columns or []
        self.queries = []
        self.closed = False

    def create_connection(self):
        pass

    def execute_query(self, query, params, fetchall=False, fetchone=False, commit=False):
        self.queries.append((query, params))
        if "information_schema.columns" in query:
            return self.columns
        return self.rows if fetchall else self.row

    def close_connection(self):
        self.closed = True


class ClienteHU115HU117Tests(unittest.TestCase):
    def setUp(self):
        self.token = {
            "nro_usuario": 12,
            "id_empresa": 4,
            "nombre_rol": "CLIENTE",
        }

    @staticmethod
    def _route(path):
        return next(route for route in crm_routes.router.routes if route.path == path)

    @staticmethod
    def _route_unidades(path):
        return next(route for route in unidad_routes.router_unidades.routes if route.path == path)

    def _mock_cliente(self, id_cliente=7, unidades=None):
        return (
            patch.object(
                crm_services.crm_repos,
                "obtener_id_cliente_por_usuario_empresa",
                return_value=id_cliente,
            ),
            patch.object(
                crm_services.crm_repos,
                "listar_unidades_cliente_cu30",
                return_value=unidades or [],
            ),
        )

    def test_cliente_autorizado_obtiene_fotografias_de_su_unidad(self):
        fotografia = {
            "id_fotografia": 51,
            "id_evidencia": 51,
            "id_unidad": 31,
            "nombre_archivo": "avance.jpg",
            "tipo_mime": "image/jpeg",
            "tamano_bytes": 100,
            "es_principal": False,
            "orden": 1,
            "fecha": "2026-11-20T12:00:00+00:00",
            "created_at": "2026-11-20T12:00:00+00:00",
        }
        identidad, unidades = self._mock_cliente(unidades=[{"id_unidad": 31, "id_obra": 9}])
        with identidad, unidades, patch.object(
            crm_repos,
            "listar_fotografias_cliente_cu30",
            return_value=[fotografia.copy()],
        ) as listar_fotografias:
            actual = crm_services.listar_fotografias_cliente_autenticado(31, self.token)

        self.assertEqual(actual["data"][0]["id_fotografia"], 51)
        self.assertEqual(actual["data"][0]["id_evidencia"], 51)
        self.assertEqual(
            actual["data"][0]["url_archivo"],
            "/api/crm/cliente/unidades/31/fotografias/51/archivo",
        )
        listar_fotografias.assert_called_once_with(
            id_cliente=7,
            id_unidad=31,
            id_empresa=4,
        )

    def test_cliente_no_consulta_fotografias_de_otra_unidad(self):
        identidad, unidades = self._mock_cliente(unidades=[{"id_unidad": 32, "id_obra": 9}])
        with identidad, unidades, patch.object(
            crm_repos, "listar_fotografias_cliente_cu30"
        ) as listar_fotografias:
            with self.assertRaises(crm_services.CrmError) as error:
                crm_services.listar_fotografias_cliente_autenticado(31, self.token)

        self.assertEqual(error.exception.status_code, 404)
        listar_fotografias.assert_not_called()

    def test_hu115_otro_cliente_rechazado_para_unidad_ajena(self):
        # El cliente 7 intenta acceder a la unidad 99 asignada a otro cliente
        identidad, unidades = self._mock_cliente(id_cliente=7, unidades=[{"id_unidad": 31, "id_obra": 9}])
        with identidad, unidades, patch.object(
            crm_repos, "listar_fotografias_cliente_cu30"
        ) as listar_fotografias:
            with self.assertRaises(crm_services.CrmError) as error:
                crm_services.listar_fotografias_cliente_autenticado(99, self.token)

        self.assertEqual(error.exception.status_code, 404)
        listar_fotografias.assert_not_called()

    def test_hu115_rechaza_unidad_que_no_pertenece_al_tenant_del_token(self):
        token = {**self.token, "id_empresa": 8}
        identidad, unidades = self._mock_cliente(unidades=[])
        with identidad, unidades, patch.object(
            crm_repos, "listar_fotografias_cliente_cu30"
        ) as listar_fotografias:
            with self.assertRaises(crm_services.CrmError) as error:
                crm_services.listar_fotografias_cliente_autenticado(31, token)

        self.assertEqual(error.exception.status_code, 404)
        listar_fotografias.assert_not_called()

    def test_cliente_sin_fotografias_recibe_lista_vacia(self):
        identidad, unidades = self._mock_cliente(unidades=[{"id_unidad": 31, "id_obra": 9}])
        with identidad, unidades, patch.object(
            crm_repos,
            "listar_fotografias_cliente_cu30",
            return_value=[],
        ):
            actual = crm_services.listar_fotografias_cliente_autenticado(31, self.token)

        self.assertEqual(actual, {"success": True, "data": []})

    def test_repositorio_fotografias_filtra_cliente_unidad_tenant_y_tipo(self):
        fecha = datetime(2026, 11, 20, tzinfo=timezone.utc)
        db = FakeDatabase(rows=[(51, 31, "avance.jpg", "image/jpeg", 100, False, 1, fecha)])
        with patch.object(crm_repos, "PostgreSQL", return_value=db):
            fotografias = crm_repos.listar_fotografias_cliente_cu30(7, 31, 4)

        self.assertEqual(fotografias[0]["id_fotografia"], 51)
        self.assertEqual(fotografias[0]["fecha"], fecha.isoformat())
        self.assertEqual(fotografias[0]["created_at"], fecha.isoformat())
        query, params = db.queries[0]
        self.assertIn("t_unidad_fotografia", query)
        self.assertIn("c.id_cliente = %s", query)
        self.assertIn("c.id_empresa = %s", query)
        self.assertIn("uf.id_unidad = %s", query)
        self.assertIn("o.id_empresa = %s", query)
        self.assertIn("cu.id_cliente = c.id_cliente", query)
        self.assertIn("uf.tipo_mime IN ('image/jpeg', 'image/png', 'image/webp', 'image/gif')", query)
        self.assertIn("ORDER BY uf.orden ASC, uf.created_at DESC, uf.id_fotografia DESC", query)
        self.assertEqual(params, (7, 4, 31, 4))
        self.assertTrue(db.closed)

    def test_repositorio_obtener_fotografia_filtra_id_fotografia_unidad_tenant(self):
        db = FakeDatabase(row=(51, 31, "uploads/unidades/31/abc.jpg", "avance.jpg", "image/jpeg", 100))
        with patch.object(crm_repos, "PostgreSQL", return_value=db):
            foto = crm_repos.obtener_fotografia_cliente_cu30(7, 31, 51, 4)

        self.assertEqual(foto["id_fotografia"], 51)
        self.assertEqual(foto["ruta_archivo"], "uploads/unidades/31/abc.jpg")
        query, params = db.queries[0]
        self.assertIn("t_unidad_fotografia", query)
        self.assertIn("uf.id_fotografia = %s", query)
        self.assertIn("uf.id_unidad = %s", query)
        self.assertIn("c.id_cliente = %s", query)
        self.assertIn("o.id_empresa = %s", query)
        self.assertEqual(params, (7, 4, 51, 31, 4))
        self.assertTrue(db.closed)

    def test_descargar_archivo_fotografia_valida_contencion_y_existencia(self):
        backend_dir = Path(crm_services.__file__).resolve().parents[2]
        unidades_dir = backend_dir / "uploads" / "unidades" / "31"
        unidades_dir.mkdir(parents=True, exist_ok=True)
        archivo_prueba = unidades_dir / "test_hu115.jpg"
        archivo_prueba.write_bytes(b"\xff\xd8\xff\xe0testimage")

        try:
            identidad, unidades = self._mock_cliente(unidades=[{"id_unidad": 31, "id_obra": 9}])
            foto_meta = {
                "id_fotografia": 51,
                "id_unidad": 31,
                "ruta_archivo": "uploads/unidades/31/test_hu115.jpg",
                "nombre_archivo": "avance.jpg",
                "tipo_mime": "image/jpeg",
                "tamano_bytes": 14,
            }
            with identidad, unidades, patch.object(
                crm_repos,
                "obtener_fotografia_cliente_cu30",
                return_value=foto_meta,
            ):
                ruta, nombre, mime = crm_services.obtener_archivo_fotografia_cliente_autenticado(31, 51, self.token)

            self.assertEqual(nombre, "avance.jpg")
            self.assertEqual(mime, "image/jpeg")
            self.assertTrue(Path(ruta).is_file())
        finally:
            if archivo_prueba.exists():
                archivo_prueba.unlink()

    def test_descargar_archivo_fotografia_rechaza_unidad_ajena(self):
        identidad, unidades = self._mock_cliente(unidades=[{"id_unidad": 32, "id_obra": 9}])
        with identidad, unidades, patch.object(crm_repos, "obtener_fotografia_cliente_cu30"):
            with self.assertRaises(crm_services.CrmError) as error:
                crm_services.obtener_archivo_fotografia_cliente_autenticado(31, 51, self.token)
        self.assertEqual(error.exception.status_code, 404)

    def test_descargar_archivo_fotografia_inexistente_retorna_404(self):
        identidad, unidades = self._mock_cliente(unidades=[{"id_unidad": 31, "id_obra": 9}])
        with identidad, unidades, patch.object(
            crm_repos, "obtener_fotografia_cliente_cu30", return_value=None
        ):
            with self.assertRaises(crm_services.CrmError) as error:
                crm_services.obtener_archivo_fotografia_cliente_autenticado(31, 999, self.token)
        self.assertEqual(error.exception.status_code, 404)

    def test_descargar_archivo_fotografia_rechaza_path_traversal(self):
        identidad, unidades = self._mock_cliente(unidades=[{"id_unidad": 31, "id_obra": 9}])
        foto_maliciosa = {
            "id_fotografia": 51,
            "id_unidad": 31,
            "ruta_archivo": "uploads/../etc/passwd",
            "nombre_archivo": "malicioso.jpg",
            "tipo_mime": "image/jpeg",
        }
        with identidad, unidades, patch.object(
            crm_repos, "obtener_fotografia_cliente_cu30", return_value=foto_maliciosa
        ):
            with self.assertRaises(crm_services.CrmError) as error:
                crm_services.obtener_archivo_fotografia_cliente_autenticado(31, 51, self.token)
        self.assertEqual(error.exception.status_code, 404)

    def test_carga_fotografia_unidad_autorizada_jefe_obra(self):
        token_jefe = {"nro_usuario": 5, "id_empresa": 4, "nombre_rol": "JEFE DE OBRA"}
        info_unidad = {"id_unidad": 31, "codigo": "UNI-031", "id_obra": 9, "id_empresa": 4}
        with patch.object(unidad_repos, "obtener_empresa_de_unidad", return_value=info_unidad), \
             patch.object(unidad_repos, "insertar_fotografia_unidad", return_value={
                 "id_fotografia": 101,
                 "id_unidad": 31,
                 "ruta_archivo": "uploads/unidades/31/foto.jpg",
                 "nombre_archivo": "fachada.jpg",
                 "tipo_mime": "image/jpeg",
                 "tamano_bytes": 100,
                 "es_principal": True,
                 "orden": 1,
                 "id_usuario": 5,
                 "created_at": "2026-11-22T12:00:00Z"
             }), \
             patch.object(unidad_services.bitacora_repos, "registrar_bitacora"):
            res = unidad_services.cargar_fotografia_unidad(
                id_unidad=31,
                token_data=token_jefe,
                filename="fachada.jpg",
                content_type="image/jpeg",
                contenido=b"\xff\xd8\xff\xe0testimagebytes",
                es_principal=True,
                orden=1,
            )

        self.assertTrue(res["success"])
        self.assertEqual(res["id_fotografia"], 101)

    def test_carga_fotografia_unidad_rechaza_otra_empresa(self):
        token_jefe = {"nro_usuario": 5, "id_empresa": 99, "nombre_rol": "JEFE DE OBRA"}
        info_unidad = {"id_unidad": 31, "codigo": "UNI-031", "id_obra": 9, "id_empresa": 4}
        with patch.object(unidad_repos, "obtener_empresa_de_unidad", return_value=info_unidad):
            with self.assertRaises(ValueError) as err:
                unidad_services.cargar_fotografia_unidad(
                    id_unidad=31,
                    token_data=token_jefe,
                    filename="fachada.jpg",
                    content_type="image/jpeg",
                    contenido=b"\xff\xd8\xff\xe0testimagebytes",
                )
        self.assertIn("No tiene autorización", str(err.exception))

    def test_carga_fotografia_unidad_rechaza_mime_invalido(self):
        token_admin = {"nro_usuario": 1, "id_empresa": 1, "nombre_rol": "ADMINISTRADOR"}
        with self.assertRaises(ValueError) as err:
            unidad_services.cargar_fotografia_unidad(
                id_unidad=31,
                token_data=token_admin,
                filename="archivo.pdf",
                content_type="application/pdf",
                contenido=b"%PDF-1.4...",
            )
        self.assertIn("Solo se permiten fotografías", str(err.exception))

    def test_carga_fotografia_unidad_rechaza_rol_cliente(self):
        route = self._route_unidades("/api/unidades/{id_unidad}/fotografias")
        dependency = route.dependant.dependencies[0].call
        with patch("app.routes.unidad_routes.obtener_permisos_rol", return_value=set()):
            with self.assertRaises(HTTPException) as error:
                dependency({"nombre_rol": "CLIENTE", "id_empresa": 1})
            self.assertEqual(error.exception.status_code, 403)

    def test_cliente_recibe_sus_comunicaciones_con_estado_de_lectura(self):
        comunicaciones = [
            {"id_notificacion": 8, "leido": False},
            {"id_notificacion": 7, "leido": True},
        ]
        identidad, _ = self._mock_cliente()
        with identidad, patch.object(
            notificaciones_repos,
            "listar_notificaciones_cliente_cu30",
            return_value=comunicaciones,
        ) as listar_comunicaciones:
            actual = crm_services.listar_comunicaciones_cliente_autenticado(self.token)

        self.assertEqual(actual["data"], comunicaciones)
        self.assertEqual(actual["no_leidas"], 1)
        listar_comunicaciones.assert_called_once_with(
            id_cliente=7,
            nro_usuario=12,
            id_empresa=4,
        )

    def test_hu116_rechaza_usuario_sin_cliente_en_empresa_del_token(self):
        identidad, _ = self._mock_cliente(id_cliente=None)
        with identidad, patch.object(
            notificaciones_repos, "listar_notificaciones_cliente_cu30"
        ) as listar_comunicaciones:
            with self.assertRaises(crm_services.CrmError) as error:
                crm_services.listar_comunicaciones_cliente_autenticado(self.token)

        self.assertEqual(error.exception.status_code, 404)
        listar_comunicaciones.assert_not_called()

    def test_hu116_otro_tenant_rechazado(self):
        token = {**self.token, "id_empresa": 8}
        identidad, _ = self._mock_cliente(id_cliente=None)
        with identidad, patch.object(
            notificaciones_repos, "listar_notificaciones_cliente_cu30"
        ) as listar_comunicaciones:
            with self.assertRaises(crm_services.CrmError) as error:
                crm_services.listar_comunicaciones_cliente_autenticado(token)

        self.assertEqual(error.exception.status_code, 404)
        listar_comunicaciones.assert_not_called()

    def test_hu116_otro_cliente_rechazado_y_no_se_mezclan_comunicaciones(self):
        identidad, _ = self._mock_cliente(id_cliente=7)
        with identidad, patch.object(
            notificaciones_repos,
            "listar_notificaciones_cliente_cu30",
            return_value=[{"id_notificacion": 1, "leido": False}],
        ) as listar_comunicaciones:
            actual = crm_services.listar_comunicaciones_cliente_autenticado(self.token)

        self.assertEqual(actual["data"][0]["id_notificacion"], 1)
        listar_comunicaciones.assert_called_once_with(
            id_cliente=7,
            nro_usuario=12,
            id_empresa=4,
        )

    def test_cliente_sin_comunicaciones_recibe_lista_vacia(self):
        identidad, _ = self._mock_cliente()
        with identidad, patch.object(
            notificaciones_repos,
            "listar_notificaciones_cliente_cu30",
            return_value=[],
        ):
            actual = crm_services.listar_comunicaciones_cliente_autenticado(self.token)

        self.assertEqual(actual, {"success": True, "no_leidas": 0, "data": []})

    def test_repositorio_comunicaciones_aisla_usuario_y_tenant(self):
        db = FakeDatabase(
            rows=[(8, "Aviso", "Mensaje", "OBRA", False, datetime(2026, 11, 20, tzinfo=timezone.utc), None)]
        )
        with patch.object(notificaciones_repos, "PostgreSQL", return_value=db):
            comunicaciones = notificaciones_repos.listar_notificaciones_cliente_cu30(7, 12, 4)

        self.assertEqual(comunicaciones[0]["id_notificacion"], 8)
        query, params = db.queries[1]
        self.assertIn("n.nro_usuario = %s", query)
        self.assertIn("u.id_empresa = %s", query)
        self.assertEqual(params, (12, 4, 200))
        self.assertTrue(db.closed)

    def test_repositorio_comunicaciones_filtra_empresa_y_obra_si_cu22_esta_aplicada(self):
        db = FakeDatabase(
            rows=[],
            columns=[("id_empresa",), ("id_obra",)],
        )
        with patch.object(notificaciones_repos, "PostgreSQL", return_value=db):
            comunicaciones = notificaciones_repos.listar_notificaciones_cliente_cu30(7, 12, 4)

        self.assertEqual(comunicaciones, [])
        query, params = db.queries[1]
        self.assertIn("n.id_empresa = %s", query)
        self.assertIn("n.id_obra IS NULL", query)
        self.assertIn("c.id_cliente = %s", query)
        self.assertEqual(params, (12, 4, 4, 4, 7, 4, 200))

    def test_cliente_obtiene_solo_sus_solicitudes(self):
        solicitudes = [{
            "id_solicitud": 41,
            "titulo": "Consulta de fase de construcción",
            "asunto": "Consulta de fase de construcción",
            "codigo_unidad": "UNI-000009",
            "nombre_obra": "Green Tower",
            "estado": "EN_PROCESO",
            "respuesta": None,
            "fecha_creacion": "2026-11-22T10:00:00Z"
        }]
        identidad, _ = self._mock_cliente()
        with identidad, patch.object(
            crm_repos,
            "listar_solicitudes_cliente_cu30",
            return_value=solicitudes,
        ) as listar_solicitudes:
            actual = crm_services.listar_solicitudes_cliente_autenticado(self.token)

        self.assertEqual(actual["data"], solicitudes)
        listar_solicitudes.assert_called_once_with(
            id_cliente=7,
            id_usuario=12,
            id_empresa=4,
        )

    def test_hu117_otro_cliente_rechazado_y_no_se_mezclan_solicitudes(self):
        identidad, _ = self._mock_cliente(id_cliente=7)
        with identidad, patch.object(
            crm_repos,
            "listar_solicitudes_cliente_cu30",
            return_value=[{"id_solicitud": 10, "estado": "PENDIENTE"}],
        ) as listar_solicitudes:
            actual = crm_services.listar_solicitudes_cliente_autenticado(self.token)

        self.assertEqual(actual["data"][0]["id_solicitud"], 10)
        listar_solicitudes.assert_called_once_with(
            id_cliente=7,
            id_usuario=12,
            id_empresa=4,
        )

    def test_hu117_rechaza_cliente_de_otro_tenant(self):
        token = {**self.token, "id_empresa": 8}
        identidad, _ = self._mock_cliente(id_cliente=None)
        with identidad, patch.object(
            crm_repos, "listar_solicitudes_cliente_cu30"
        ) as listar_solicitudes:
            with self.assertRaises(crm_services.CrmError) as error:
                crm_services.listar_solicitudes_cliente_autenticado(token)

        self.assertEqual(error.exception.status_code, 404)
        listar_solicitudes.assert_not_called()

    def test_cliente_sin_solicitudes_recibe_lista_vacia(self):
        identidad, _ = self._mock_cliente()
        with identidad, patch.object(
            crm_repos,
            "listar_solicitudes_cliente_cu30",
            return_value=[],
        ):
            actual = crm_services.listar_solicitudes_cliente_autenticado(self.token)

        self.assertEqual(actual, {"success": True, "data": []})

    def test_cliente_puede_consultar_detalle_solicitud(self):
        detalle = {
            "id_solicitud": 41,
            "titulo": "Consulta de fase",
            "asunto": "Consulta de fase",
            "descripcion": "Quiero conocer fase actual.",
            "codigo_unidad": "UNI-000009",
            "nombre_obra": "Green Tower",
            "estado": "ATENDIDA",
            "respuesta": "La unidad se encuentra en fase de instalaciones eléctricas.",
            "fecha_respuesta": "2026-11-22T14:00:00Z",
            "evidencia": None
        }
        identidad, _ = self._mock_cliente()
        with identidad, patch.object(
            crm_repos,
            "obtener_solicitud_cliente_cu30",
            return_value=detalle,
        ) as obtener_solicitud:
            res = crm_services.obtener_detalle_solicitud_cliente_autenticado(41, self.token)

        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["id_solicitud"], 41)
        self.assertEqual(res["data"]["estado"], "ATENDIDA")
        self.assertEqual(res["data"]["respuesta"], "La unidad se encuentra en fase de instalaciones eléctricas.")
        obtener_solicitud.assert_called_once_with(
            id_cliente=7,
            id_usuario=12,
            id_solicitud=41,
            id_empresa=4,
        )

    def test_cliente_no_puede_consultar_solicitud_de_otro_cliente_o_inexistente(self):
        identidad, _ = self._mock_cliente(id_cliente=7)
        with identidad, patch.object(
            crm_repos,
            "obtener_solicitud_cliente_cu30",
            return_value=None,
        ):
            with self.assertRaises(crm_services.CrmError) as error:
                crm_services.obtener_detalle_solicitud_cliente_autenticado(999, self.token)

        self.assertEqual(error.exception.status_code, 404)
        self.assertIn("no pertenece al cliente", str(error.exception))

    def test_cliente_puede_crear_solicitud_para_su_unidad(self):
        identidad, _ = self._mock_cliente(id_cliente=7)
        payload = {
            "id_unidad": 31,
            "titulo": "Consulta de instalaciones",
            "descripcion": "Deseo consultar sobre el avance de cableado."
        }
        registro_creado = {
            "id_solicitud": 55,
            "id_cliente": 7,
            "id_usuario": 12,
            "id_empresa": 4,
            "id_obra": 9,
            "id_unidad": 31,
            "titulo": payload["titulo"],
            "asunto": payload["titulo"],
            "descripcion": payload["descripcion"],
            "estado": "PENDIENTE",
            "fecha_creacion": "2026-11-22T10:00:00Z"
        }
        with identidad, \
             patch.object(crm_repos, "validar_unidad_asociada_cliente", return_value=True), \
             patch.object(crm_repos, "obtener_empresa_unidad", return_value={"id_unidad": 31, "id_obra": 9, "id_empresa": 4}), \
             patch.object(crm_repos, "crear_solicitud_cliente_db", return_value=registro_creado) as crear_mock, \
             patch.object(crm_services.bitacora_repos, "registrar_bitacora"):
            res = crm_services.registrar_solicitud_cliente_autenticado(payload, self.token)

        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["id_solicitud"], 55)
        self.assertEqual(res["data"]["estado"], "PENDIENTE")
        crear_mock.assert_called_once_with(
            id_cliente=7,
            id_usuario=12,
            id_empresa=4,
            id_obra=9,
            id_unidad=31,
            titulo=payload["titulo"],
            descripcion=payload["descripcion"],
        )

    def test_cliente_no_puede_crear_solicitud_para_unidad_ajena(self):
        identidad, _ = self._mock_cliente(id_cliente=7)
        payload = {
            "id_unidad": 999,
            "titulo": "Consulta",
            "descripcion": "Descripción válida"
        }
        with identidad, \
             patch.object(crm_repos, "validar_unidad_asociada_cliente", return_value=False):
            with self.assertRaises(crm_services.CrmError) as error:
                crm_services.registrar_solicitud_cliente_autenticado(payload, self.token)

        self.assertEqual(error.exception.status_code, 400)
        self.assertIn("no está asociada", str(error.exception))

    def test_constructora_puede_gestionar_estado_y_responder(self):
        token_admin = {"nro_usuario": 1, "id_empresa": 4, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
        solicitud_existente = {
            "id_solicitud": 55,
            "id_cliente": 7,
            "id_empresa": 4,
            "id_obra": 9,
            "estado": "PENDIENTE"
        }
        actualizado_mock = {
            "id_solicitud": 55,
            "estado": "ATENDIDA",
            "respuesta": "La unidad se encuentra actualmente en fase de instalaciones eléctricas.",
            "fecha_respuesta": "2026-11-22T14:30:00Z",
            "fecha_actualizacion": "2026-11-22T14:30:00Z",
            "id_obra": 9,
            "id_cliente": 7,
        }
        payload = {
            "estado": "ATENDIDA",
            "respuesta": "La unidad se encuentra actualmente en fase de instalaciones eléctricas."
        }
        with patch.object(crm_repos, "obtener_solicitud_por_id", return_value=solicitud_existente), \
             patch.object(crm_repos, "responder_solicitud_constructora_db", return_value=actualizado_mock) as responder_mock, \
             patch.object(crm_services.bitacora_repos, "registrar_bitacora"):
            res = crm_services.responder_solicitud_constructora(55, payload, token_admin)

        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["estado"], "ATENDIDA")
        responder_mock.assert_called_once_with(
            id_solicitud=55,
            id_empresa=4,
            estado="ATENDIDA",
            respuesta=payload["respuesta"],
            id_usuario_respuesta=1,
            id_fotografia_evidencia=None,
        )

    def test_constructora_atendida_exige_respuesta(self):
        token_admin = {"nro_usuario": 1, "id_empresa": 4, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
        payload = {"estado": "ATENDIDA", "respuesta": ""}
        with self.assertRaises(crm_services.CrmError) as error:
            crm_services.responder_solicitud_constructora(55, payload, token_admin)

        self.assertEqual(error.exception.status_code, 400)
        self.assertIn("Debe registrar la respuesta", str(error.exception))

    def test_constructora_rechaza_solicitud_de_otra_empresa(self):
        token_admin = {"nro_usuario": 1, "id_empresa": 4, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
        payload = {"estado": "EN_PROCESO"}
        with patch.object(crm_repos, "obtener_solicitud_por_id", return_value=None):
            with self.assertRaises(crm_services.CrmError) as error:
                crm_services.responder_solicitud_constructora(55, payload, token_admin)

        self.assertEqual(error.exception.status_code, 404)

    def test_constructora_valida_estados_permitidos(self):
        token_admin = {"nro_usuario": 1, "id_empresa": 4, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
        payload = {"estado": "ESTADO_INEXISTENTE"}
        with self.assertRaises(crm_services.CrmError) as error:
            crm_services.responder_solicitud_constructora(55, payload, token_admin)

        self.assertEqual(error.exception.status_code, 400)
        self.assertIn("Estado inválido", str(error.exception))

    def test_repositorio_solicitudes_filtra_propietario_y_empresa(self):
        fecha = datetime(2026, 11, 20, tzinfo=timezone.utc)
        db = FakeDatabase(rows=[(41, 7, 12, 4, 9, "Obra 1", "OB1", 31, "UNI-01", "DEPTO", "Consulta", "Detalle", "EN_PROCESO", None, None, None, fecha, fecha, None)])
        with patch.object(crm_repos, "PostgreSQL", return_value=db):
            solicitudes = crm_repos.listar_solicitudes_cliente_cu30(7, 12, 4)

        self.assertEqual(solicitudes[0]["titulo"], "Consulta")
        self.assertEqual(solicitudes[0]["codigo_unidad"], "UNI-01")
        query, params = db.queries[0]
        self.assertIn("t_cliente_solicitud s", query)
        self.assertIn("s.id_cliente = %s", query)
        self.assertIn("s.id_usuario = %s", query)
        self.assertIn("s.id_empresa = %s", query)
        self.assertIn("ORDER BY s.fecha_creacion DESC", query)
        self.assertEqual(params, (7, 12, 4))
        self.assertTrue(db.closed)

    def test_roles_no_cliente_son_rechazados_en_endpoints_hu115_hu117(self):
        paths = (
            "/cliente/unidades/{id_unidad}/fotografias",
            "/cliente/unidades/{id_unidad}/fotografias/{id_fotografia}/archivo",
            "/cliente/comunicaciones",
            "/cliente/solicitudes",
            "/cliente/solicitudes/{id_solicitud}",
        )
        for path in paths:
            with self.subTest(path=path):
                route = self._route(path)
                dependency = route.dependant.dependencies[0].call
                with self.assertRaises(HTTPException) as error:
                    dependency({"nombre_rol": "ADMINISTRADOR_EMPRESA"})
                self.assertEqual(error.exception.status_code, 403)

    def test_endpoints_no_reciben_id_cliente_ni_id_empresa(self):
        for path in (
            "/cliente/unidades/{id_unidad}/fotografias",
            "/cliente/unidades/{id_unidad}/fotografias/{id_fotografia}/archivo",
            "/cliente/comunicaciones",
            "/cliente/solicitudes",
            "/cliente/solicitudes/{id_solicitud}",
        ):
            with self.subTest(path=path):
                parametros = inspect.signature(self._route(path).endpoint).parameters
                self.assertNotIn("id_cliente", parametros)
                self.assertNotIn("id_empresa", parametros)

    # ─────────────────────────────────────────────────────────────────────────
    # HU116: EMISIÓN DE COMUNICACIONES DIRECTAS
    # ─────────────────────────────────────────────────────────────────────────
    def test_hu116_usuario_autorizado_puede_crear_comunicacion(self):
        token_admin = {"nro_usuario": 1, "id_empresa": 1, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
        payload = {
            "id_cliente": 54,
            "id_obra": 8,
            "id_unidad": 9,
            "titulo": "Avance de su unidad",
            "cuerpo": "Se informa que su unidad UNI-000009 presenta avances.",
            "tipo_referencia": "COMUNICACION",
        }
        cliente_mock = {"id_cliente": 54, "id_empresa": 1, "nombre_completo": "Fabricio"}
        unidad_mock = {"id_unidad": 9, "id_obra": 8, "id_empresa": 1}
        registro_mock = {
            "id_notificacion": 99,
            "titulo": payload["titulo"],
            "cuerpo": payload["cuerpo"],
            "tipo_referencia": "COMUNICACION",
            "nro_usuario": 20,
            "id_empresa": 1,
            "id_obra": 8,
            "leido": False,
            "fecha_creacion": "2026-11-22 17:00:00",
        }

        with patch.object(crm_services.crm_repos, "obtener_cliente_por_id", return_value=cliente_mock), \
             patch.object(crm_services.crm_repos, "obtener_id_usuario_por_cliente", return_value=20), \
             patch.object(crm_services.notificaciones_repos, "validar_obra_empresa", return_value={"id_obra": 8, "id_empresa": 1}), \
             patch.object(crm_services.crm_repos, "obtener_empresa_unidad", return_value=unidad_mock), \
             patch.object(crm_services.crm_repos, "validar_unidad_asociada_cliente", return_value=True), \
             patch.object(crm_services.notificaciones_repos, "crear_comunicacion_cliente_db", return_value=registro_mock) as crear_mock, \
             patch.object(crm_services.bitacora_repos, "registrar_bitacora"):
            res = crm_services.crear_comunicacion_cliente(payload, token_admin)

        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["id_notificacion"], 99)
        self.assertFalse(res["data"]["leido"])
        crear_mock.assert_called_once_with(
            titulo=payload["titulo"],
            cuerpo=payload["cuerpo"],
            tipo_referencia="COMUNICACION",
            nro_usuario=20,
            id_empresa=1,
            id_obra=8,
        )

    def test_hu116_usuario_no_autorizado_recibe_403(self):
        route = self._route("/comunicaciones")
        dependency = route.dependant.dependencies[0].call

        with patch("app.routes.crm_routes.obtener_permisos_rol", return_value=set()):
            with self.assertRaises(HTTPException) as err_cliente:
                dependency({"nombre_rol": "CLIENTE", "id_empresa": 1})
            self.assertEqual(err_cliente.exception.status_code, 403)

            with self.assertRaises(HTTPException) as err_albanil:
                dependency({"nombre_rol": "ALBAÑIL", "id_empresa": 1})
            self.assertEqual(err_albanil.exception.status_code, 403)

            # Roles autorizados pasan exitosamente
            for rol in ("ADMINISTRADOR", "ADMINISTRADOR_EMPRESA", "JEFE DE OBRA", "RESPONSABLE"):
                token_valido = {"nombre_rol": rol, "id_empresa": 1}
                self.assertEqual(dependency(token_valido), token_valido)

    def test_hu116_cliente_de_otro_tenant_no_puede_ser_destinatario(self):
        token_admin = {"nro_usuario": 1, "id_empresa": 1, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
        payload = {"id_cliente": 999, "titulo": "Aviso", "cuerpo": "Contenido"}

        with patch.object(crm_services.crm_repos, "obtener_cliente_por_id", return_value=None):
            with self.assertRaises(crm_services.CrmError) as err:
                crm_services.crear_comunicacion_cliente(payload, token_admin)
            self.assertEqual(err.exception.status_code, 404)

    def test_hu116_obra_de_otro_tenant_es_rechazada(self):
        token_admin = {"nro_usuario": 1, "id_empresa": 1, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
        payload = {"id_cliente": 54, "id_obra": 99, "titulo": "Aviso", "cuerpo": "Contenido"}
        cliente_mock = {"id_cliente": 54, "id_empresa": 1}

        with patch.object(crm_services.crm_repos, "obtener_cliente_por_id", return_value=cliente_mock), \
             patch.object(crm_services.crm_repos, "obtener_id_usuario_por_cliente", return_value=20), \
             patch.object(crm_services.notificaciones_repos, "validar_obra_empresa", return_value={"id_obra": 99, "id_empresa": 2}):
            with self.assertRaises(crm_services.CrmError) as err:
                crm_services.crear_comunicacion_cliente(payload, token_admin)
            self.assertEqual(err.exception.status_code, 403)

    def test_hu116_unidad_de_otro_tenant_es_rechazada(self):
        token_admin = {"nro_usuario": 1, "id_empresa": 1, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
        payload = {"id_cliente": 54, "id_unidad": 50, "titulo": "Aviso", "cuerpo": "Contenido"}
        cliente_mock = {"id_cliente": 54, "id_empresa": 1}

        with patch.object(crm_services.crm_repos, "obtener_cliente_por_id", return_value=cliente_mock), \
             patch.object(crm_services.crm_repos, "obtener_id_usuario_por_cliente", return_value=20), \
             patch.object(crm_services.crm_repos, "obtener_empresa_unidad", return_value={"id_unidad": 50, "id_empresa": 3, "id_obra": 4}):
            with self.assertRaises(crm_services.CrmError) as err:
                crm_services.crear_comunicacion_cliente(payload, token_admin)
            self.assertEqual(err.exception.status_code, 403)

    def test_hu116_unidad_que_no_pertenece_al_cliente_es_rechazada(self):
        token_admin = {"nro_usuario": 1, "id_empresa": 1, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
        payload = {"id_cliente": 54, "id_unidad": 9, "titulo": "Aviso", "cuerpo": "Contenido"}
        cliente_mock = {"id_cliente": 54, "id_empresa": 1}

        with patch.object(crm_services.crm_repos, "obtener_cliente_por_id", return_value=cliente_mock), \
             patch.object(crm_services.crm_repos, "obtener_id_usuario_por_cliente", return_value=20), \
             patch.object(crm_services.crm_repos, "obtener_empresa_unidad", return_value={"id_unidad": 9, "id_empresa": 1, "id_obra": 8}), \
             patch.object(crm_services.crm_repos, "validar_unidad_asociada_cliente", return_value=False):
            with self.assertRaises(crm_services.CrmError) as err:
                crm_services.crear_comunicacion_cliente(payload, token_admin)
            self.assertEqual(err.exception.status_code, 400)
            self.assertIn("no está asociada al cliente", str(err.exception))

    def test_hu116_comunicacion_queda_asociada_al_usuario_correcto(self):
        token_admin = {"nro_usuario": 1, "id_empresa": 1, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
        payload = {"id_cliente": 54, "titulo": "Aviso", "cuerpo": "Contenido"}
        cliente_mock = {"id_cliente": 54, "id_empresa": 1}

        with patch.object(crm_services.crm_repos, "obtener_cliente_por_id", return_value=cliente_mock), \
             patch.object(crm_services.crm_repos, "obtener_id_usuario_por_cliente", return_value=20) as resolver_usuario, \
             patch.object(crm_services.notificaciones_repos, "crear_comunicacion_cliente_db", return_value={"id_notificacion": 1, "leido": False, "fecha_creacion": "2026-11-22"}), \
             patch.object(crm_services.bitacora_repos, "registrar_bitacora"):
            crm_services.crear_comunicacion_cliente(payload, token_admin)

        resolver_usuario.assert_called_once_with(54, 1)

    def test_hu116_fabricio_recibe_la_comunicacion_mediante_get_existente(self):
        token_fabricio = {"nro_usuario": 20, "id_empresa": 1, "nombre_rol": "CLIENTE"}
        comunicacion_fabricio = {
            "id_notificacion": 105,
            "titulo": "Avance de su unidad",
            "cuerpo": "Se informa avance en UNI-000009.",
            "tipo_referencia": "COMUNICACION",
            "leido": False,
            "fecha_creacion": "2026-11-22 17:15:00",
        }

        with patch.object(crm_services.crm_repos, "obtener_id_cliente_por_usuario_empresa", return_value=54), \
             patch.object(crm_services.notificaciones_repos, "listar_notificaciones_cliente_cu30", return_value=[comunicacion_fabricio]):
            resultado = crm_services.listar_comunicaciones_cliente_autenticado(token_fabricio)

        self.assertTrue(resultado["success"])
        self.assertEqual(resultado["no_leidas"], 1)
        self.assertEqual(len(resultado["data"]), 1)
        self.assertEqual(resultado["data"][0]["titulo"], "Avance de su unidad")
        self.assertFalse(resultado["data"][0]["leido"])

    def test_hu116_comunicacion_creada_para_fabricio_no_aparece_para_otro_cliente(self):
        token_otro_cliente = {"nro_usuario": 99, "id_empresa": 1, "nombre_rol": "CLIENTE"}

        with patch.object(crm_services.crm_repos, "obtener_id_cliente_por_usuario_empresa", return_value=77), \
             patch.object(crm_services.notificaciones_repos, "listar_notificaciones_cliente_cu30", return_value=[]):
            resultado_otro = crm_services.listar_comunicaciones_cliente_autenticado(token_otro_cliente)

        self.assertTrue(resultado_otro["success"])
        self.assertEqual(resultado_otro["no_leidas"], 0)
        self.assertEqual(resultado_otro["data"], [])

    def test_hu116_leido_inicia_en_false(self):
        token_admin = {"nro_usuario": 1, "id_empresa": 1, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
        payload = {"id_cliente": 54, "titulo": "Aviso", "cuerpo": "Contenido"}
        cliente_mock = {"id_cliente": 54, "id_empresa": 1}
        retorno_db = {
            "id_notificacion": 101,
            "titulo": "Aviso",
            "cuerpo": "Contenido",
            "tipo_referencia": "COMUNICACION",
            "nro_usuario": 20,
            "id_empresa": 1,
            "id_obra": None,
            "leido": False,
            "fecha_creacion": "2026-11-22 17:00:00",
        }

        with patch.object(crm_services.crm_repos, "obtener_cliente_por_id", return_value=cliente_mock), \
             patch.object(crm_services.crm_repos, "obtener_id_usuario_por_cliente", return_value=20), \
             patch.object(crm_services.notificaciones_repos, "crear_comunicacion_cliente_db", return_value=retorno_db), \
             patch.object(crm_services.bitacora_repos, "registrar_bitacora"):
            res = crm_services.crear_comunicacion_cliente(payload, token_admin)

        self.assertIn("data", res)
        self.assertIs(res["data"]["leido"], False)

    def test_hu117_constructora_listar_solicitudes(self):
        token_jefe_obra = {"nro_usuario": 5, "id_empresa": 1, "nombre_rol": "JEFE DE OBRA"}
        solicitudes_db = [{
            "id_solicitud": 3,
            "id_cliente": 54,
            "id_usuario": 20,
            "id_empresa": 1,
            "id_obra": 8,
            "id_unidad": 9,
            "titulo": "revision de proyecto",
            "asunto": "revision de proyecto",
            "descripcion": "agregas mas unidades",
            "estado": "PENDIENTE",
            "respuesta": None,
            "nombre_obra": "Green Tower",
            "codigo_unidad": "UNI-000009",
            "nombre_cliente": "Fabricio"
        }]

        with patch.object(crm_services.crm_repos, "listar_solicitudes_constructora", return_value=solicitudes_db):
            res = crm_services.listar_solicitudes_constructora(token_jefe_obra)

        self.assertTrue(res["success"])
        self.assertEqual(len(res["data"]), 1)
        self.assertEqual(res["data"][0]["codigo_unidad"], "UNI-000009")
        self.assertEqual(res["data"][0]["nombre_cliente"], "Fabricio")
        self.assertEqual(res["data"][0]["estado"], "PENDIENTE")

    def test_hu117_constructora_responder_solicitud_transiciones(self):
        token_jefe_obra = {"nro_usuario": 5, "id_empresa": 1, "nombre_rol": "JEFE DE OBRA"}
        solicitud_actual = {
            "id_solicitud": 3,
            "id_empresa": 1,
            "id_obra": 8,
            "id_cliente": 54,
            "estado": "EN_PROCESO"
        }
        retorno_atendida = {
            "id_solicitud": 3,
            "estado": "ATENDIDA",
            "respuesta": "La unidad se encuentra actualmente en fase de instalaciones eléctricas.",
            "fecha_respuesta": "2026-11-22T20:34:04Z",
            "fecha_actualizacion": "2026-11-22T20:34:04Z",
            "id_obra": 8,
            "id_cliente": 54
        }

        with patch.object(crm_services.crm_repos, "obtener_solicitud_por_id", return_value=solicitud_actual), \
             patch.object(crm_services.crm_repos, "responder_solicitud_constructora_db", return_value=retorno_atendida), \
             patch.object(crm_services.bitacora_repos, "registrar_bitacora"):
            res = crm_services.responder_solicitud_constructora(
                3,
                {"estado": "ATENDIDA", "respuesta": "La unidad se encuentra actualmente en fase de instalaciones eléctricas."},
                token_jefe_obra
            )

        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["estado"], "ATENDIDA")
        self.assertEqual(res["data"]["respuesta"], "La unidad se encuentra actualmente en fase de instalaciones eléctricas.")


if __name__ == "__main__":
    unittest.main()
