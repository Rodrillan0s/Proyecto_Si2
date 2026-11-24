import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from app.repos import avance_repos
from app.services import avance_services


class FakeDatabase:
    def __init__(self, rows):
        self.rows = rows
        self.query = None
        self.params = None
        self.closed = False

    def create_connection(self):
        pass

    def execute_query(self, query, params, fetchall=False):
        self.query = query
        self.params = params
        if not fetchall:
            raise AssertionError("Expected a row list query.")
        return self.rows

    def close_connection(self):
        self.closed = True


class AvanceFisicoUnidadClienteTests(unittest.TestCase):
    def setUp(self):
        self.token = {
            "nro_usuario": 12,
            "id_empresa": 4,
            "nombre_rol": "CLIENTE",
        }

    def test_service_returns_avance_for_authorized_unit_and_tenant(self):
        result = {"success": True, "data": [{"id_unidad": 31}]}
        with (
            patch.object(
                avance_services.crm_repos,
                "obtener_id_cliente_por_usuario_empresa",
                return_value=7,
            ) as obtener_cliente,
            patch.object(
                avance_services.crm_repos,
                "listar_unidades_cliente_cu30",
                return_value=[{"id_unidad": 31, "id_obra": 9}],
            ) as listar_unidades,
            patch.object(
                avance_services.avance_repos,
                "listar_avance_fisico_unidad_cliente",
                return_value=result,
            ) as listar_avance,
        ):
            actual = avance_services.consultar_avance_fisico_unidad_cliente(
                9, 31, self.token
            )

        self.assertEqual(actual, result)
        obtener_cliente.assert_called_once_with(12, 4)
        listar_unidades.assert_called_once_with(7, 4)
        listar_avance.assert_called_once_with(
            id_cliente=7,
            id_unidad=31,
            id_obra=9,
            id_empresa=4,
        )

    def test_service_denies_unit_associated_to_another_client(self):
        with (
            patch.object(
                avance_services.crm_repos,
                "obtener_id_cliente_por_usuario_empresa",
                return_value=7,
            ),
            patch.object(
                avance_services.crm_repos,
                "listar_unidades_cliente_cu30",
                return_value=[{"id_unidad": 32, "id_obra": 9}],
            ),
            patch.object(
                avance_services.avance_repos,
                "listar_avance_fisico_unidad_cliente",
            ) as listar_avance,
        ):
            with self.assertRaises(PermissionError):
                avance_services.consultar_avance_fisico_unidad_cliente(
                    9, 31, self.token
                )

        listar_avance.assert_not_called()

    def test_service_denies_unit_from_another_tenant(self):
        with (
            patch.object(
                avance_services.crm_repos,
                "obtener_id_cliente_por_usuario_empresa",
                return_value=7,
            ),
            patch.object(
                avance_services.crm_repos,
                "listar_unidades_cliente_cu30",
                return_value=[],
            ),
            patch.object(
                avance_services.avance_repos,
                "listar_avance_fisico_unidad_cliente",
            ) as listar_avance,
        ):
            with self.assertRaises(PermissionError):
                avance_services.consultar_avance_fisico_unidad_cliente(
                    9, 31, self.token
                )

        listar_avance.assert_not_called()

    def test_service_denies_unverified_project_id(self):
        with (
            patch.object(
                avance_services.crm_repos,
                "obtener_id_cliente_por_usuario_empresa",
                return_value=7,
            ),
            patch.object(
                avance_services.crm_repos,
                "listar_unidades_cliente_cu30",
                return_value=[{"id_unidad": 31, "id_obra": 8}],
            ),
            patch.object(
                avance_services.avance_repos,
                "listar_avance_fisico_unidad_cliente",
            ) as listar_avance,
        ):
            with self.assertRaises(PermissionError):
                avance_services.consultar_avance_fisico_unidad_cliente(
                    9, 31, self.token
                )

        listar_avance.assert_not_called()

    def test_service_requires_client_role(self):
        token = {**self.token, "nombre_rol": "ADMINISTRADOR_EMPRESA"}
        with patch.object(
            avance_services.crm_repos,
            "obtener_id_cliente_por_usuario_empresa",
        ) as obtener_cliente:
            with self.assertRaises(PermissionError):
                avance_services.consultar_avance_fisico_unidad_cliente(9, 31, token)

        obtener_cliente.assert_not_called()

    def test_repository_filters_tenant_and_maps_physical_history(self):
        db = FakeDatabase(
            [
                (
                    15,
                    9,
                    31,
                    Decimal("65.50"),
                    "EN_CONSTRUCCION",
                    date(2026, 11, 20),
                    "Estructura concluida",
                )
            ]
        )
        with patch.object(avance_repos, "PostgreSQL", return_value=db):
            result = avance_repos.listar_avance_fisico_unidad_cliente(7, 31, 9, 4)

        self.assertEqual(
            result,
            {
                "success": True,
                "data": [
                    {
                        "id_avance": 15,
                        "id_obra": 9,
                        "id_unidad": 31,
                        "porcentaje_avance": 65.5,
                        "estado_unidad": "EN_CONSTRUCCION",
                        "fecha_registro": "2026-11-20",
                        "observacion": "Estructura concluida",
                    }
                ],
            },
        )
        self.assertEqual(db.params, (7, 4, 31, 9, 4))
        self.assertIn("o.id_obra = e.id_obra", db.query)
        self.assertIn("o.id_obra = a.id_obra", db.query)
        self.assertIn("o.id_empresa = %s", db.query)
        self.assertIn("cu.id_cliente = c.id_cliente", db.query)
        self.assertNotIn("estado_asociacion", db.query)
        self.assertTrue(db.closed)


if __name__ == "__main__":
    unittest.main()
