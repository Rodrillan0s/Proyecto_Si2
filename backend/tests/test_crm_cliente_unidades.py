import inspect
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.routes import crm_routes
from app.services import crm_services


class UnidadesClienteAutenticadoTests(unittest.TestCase):
    def setUp(self):
        self.token = {
            "nro_usuario": 12,
            "id_empresa": 4,
            "nombre_rol": "CLIENTE",
        }

    @staticmethod
    def _route():
        return next(
            route
            for route in crm_routes.router.routes
            if getattr(route, "path", None) == "/cliente/unidades"
        )

    def test_cliente_obtiene_unidades_resueltas_desde_su_token(self):
        unidades = [{"id_unidad": 31, "id_obra": 9}]
        with (
            patch.object(
                crm_services.crm_repos,
                "obtener_id_cliente_por_usuario_empresa",
                return_value=7,
            ) as obtener_cliente,
            patch.object(
                crm_services.crm_repos,
                "listar_unidades_cliente_cu30",
                return_value=unidades,
            ) as listar_unidades,
        ):
            actual = crm_services.listar_unidades_cliente_autenticado(self.token)

        self.assertEqual(actual, {"success": True, "data": unidades})
        obtener_cliente.assert_called_once_with(12, 4)
        listar_unidades.assert_called_once_with(7, 4)

    def test_usuario_con_otro_rol_es_rechazado(self):
        dependency = self._route().dependant.dependencies[0].call
        with self.assertRaises(HTTPException) as error:
            dependency({"nombre_rol": "ADMINISTRADOR_EMPRESA"})
        self.assertEqual(error.exception.status_code, 403)

    def test_usuario_sin_cliente_crm_es_rechazado(self):
        with (
            patch.object(
                crm_services.crm_repos,
                "obtener_id_cliente_por_usuario_empresa",
                return_value=None,
            ) as obtener_cliente,
            patch.object(
                crm_services.crm_repos,
                "listar_unidades_cliente_cu30",
            ) as listar_unidades,
        ):
            with self.assertRaises(crm_services.CrmError) as error:
                crm_services.listar_unidades_cliente_autenticado(self.token)

        self.assertEqual(error.exception.status_code, 404)
        obtener_cliente.assert_called_once_with(12, 4)
        listar_unidades.assert_not_called()

    def test_claims_autenticados_definen_usuario_y_tenant(self):
        token = {**self.token, "nro_usuario": 21, "id_empresa": 8}
        with (
            patch.object(
                crm_services.crm_repos,
                "obtener_id_cliente_por_usuario_empresa",
                return_value=15,
            ) as obtener_cliente,
            patch.object(
                crm_services.crm_repos,
                "listar_unidades_cliente_cu30",
                return_value=[],
            ) as listar_unidades,
        ):
            actual = crm_services.listar_unidades_cliente_autenticado(token)

        self.assertEqual(actual, {"success": True, "data": []})
        obtener_cliente.assert_called_once_with(21, 8)
        listar_unidades.assert_called_once_with(15, 8)

    def test_endpoint_no_acepta_id_cliente_ni_id_empresa_externos(self):
        route = self._route()
        self.assertEqual(set(inspect.signature(route.endpoint).parameters), {"token"})
        self.assertEqual(route.dependant.path_params, [])
        self.assertEqual(route.dependant.query_params, [])

    def test_cliente_no_recibe_unidades_de_otro_tenant(self):
        token = {**self.token, "id_empresa": 4}
        with (
            patch.object(
                crm_services.crm_repos,
                "obtener_id_cliente_por_usuario_empresa",
                return_value=7,
            ) as obtener_cliente,
            patch.object(
                crm_services.crm_repos,
                "listar_unidades_cliente_cu30",
                return_value=[],
            ) as listar_unidades,
        ):
            actual = crm_services.listar_unidades_cliente_autenticado(token)

        self.assertEqual(actual["data"], [])
        obtener_cliente.assert_called_once_with(12, 4)
        listar_unidades.assert_called_once_with(7, 4)

    def test_cliente_sin_unidades_recibe_lista_vacia(self):
        with (
            patch.object(
                crm_services.crm_repos,
                "obtener_id_cliente_por_usuario_empresa",
                return_value=7,
            ),
            patch.object(
                crm_services.crm_repos,
                "listar_unidades_cliente_cu30",
                return_value=[],
            ),
        ):
            actual = crm_services.listar_unidades_cliente_autenticado(self.token)

        self.assertEqual(actual, {"success": True, "data": []})


if __name__ == "__main__":
    unittest.main()
