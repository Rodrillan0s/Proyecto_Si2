from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
import unittest

from app.repos import trabajadores_costos_repos as repo
from app.services import control_costos_services as costos
from app.services import trabajadores_costos_services as service


TOKEN = {"id_empresa": 7, "nro_usuario": 21, "nombre_rol": "ADMINISTRADOR_EMPRESA"}


class TrabajadoresCostosServiceTests(unittest.TestCase):
    def test_salario_diario_valido_conserva_vigencia_y_usuario_registrador(self):
        vigencia = date.today()
        saved = {
            "id_salario": 11, "id_usuario": 31,
            "salario_diario": Decimal("200.00"), "fecha_vigencia": vigencia,
        }
        with patch.object(repo, "registrar_salario", return_value=saved) as create:
            response = service.registrar_salario(
                9, 31, {"salario_diario": Decimal("200"), "fecha_vigencia": vigencia}, TOKEN
            )
        self.assertEqual(response["data"]["salario_diario"], Decimal("200.00"))
        create.assert_called_once_with(
            7, 9, 31, Decimal("200.00"), vigencia, 21
        )

    def test_rechaza_salario_retroactivo_o_cero(self):
        with patch.object(repo, "registrar_salario") as create:
            with self.assertRaises(costos.ControlCostosError):
                service.registrar_salario(
                    9, 31,
                    {"salario_diario": 200, "fecha_vigencia": date.today() - timedelta(days=1)},
                    TOKEN,
                )
            with self.assertRaises(costos.ControlCostosError):
                service.registrar_salario(
                    9, 31,
                    {"salario_diario": 0, "fecha_vigencia": date.today()},
                    TOKEN,
                )
            create.assert_not_called()

    def test_jornada_vigente_valida_incluye_cero_dias(self):
        work_date = date.today()
        saved = {
            "id_jornada": 5, "id_usuario": 31, "fecha": work_date,
            "dias_trabajados": Decimal("0.00"), "id_salario": 11,
        }
        with patch.object(repo, "registrar_jornada", return_value=saved) as create:
            response = service.registrar_jornada(
                9,
                {"id_usuario": 31, "fecha": work_date, "dias_trabajados": Decimal("0")},
                TOKEN,
            )
        self.assertEqual(response["data"]["dias_trabajados"], Decimal("0.00"))
        create.assert_called_once_with(7, 9, 31, work_date, Decimal("0.00"))

    def test_rechaza_jornada_futura_o_mayor_a_un_dia(self):
        with patch.object(repo, "registrar_jornada") as create:
            with self.assertRaises(costos.ControlCostosError):
                service.registrar_jornada(
                    9,
                    {"id_usuario": 31, "fecha": date.today() + timedelta(days=1),
                     "dias_trabajados": 1},
                    TOKEN,
                )
            with self.assertRaises(costos.ControlCostosError):
                service.registrar_jornada(
                    9,
                    {"id_usuario": 31, "fecha": date.today(), "dias_trabajados": "1.01"},
                    TOKEN,
                )
            create.assert_not_called()

    def test_trabajador_ajeno_o_sin_salario_no_puede_generar_jornada(self):
        with patch.object(
            repo, "registrar_jornada",
            side_effect=repo.TrabajadoresCostosConflictError(
                "El trabajador no está asignado o no tiene salario."
            ),
        ):
            with self.assertRaises(costos.ControlCostosError) as ctx:
                service.registrar_jornada(
                    9,
                    {"id_usuario": 99, "fecha": date.today(), "dias_trabajados": 1},
                    TOKEN,
                )
        self.assertEqual(ctx.exception.status_code, 409)

    def test_aislamiento_exige_empresa_activa(self):
        with patch.object(repo, "listar_trabajadores_obra") as listing, patch.object(
            service.control_costos_repos, "obtener_obra", return_value=None
        ):
            with self.assertRaises(costos.ControlCostosError) as ctx:
                service.listar_mano_obra(9, {"nro_usuario": 21})
        self.assertEqual(ctx.exception.status_code, 403)
        listing.assert_not_called()

    def test_captura_jornada_usa_salario_vigente_de_la_fecha_y_no_otra_obra(self):
        db = MagicMock()
        db.cur.description = None
        db.execute_query.side_effect = [
            (31, "ACTIVO"),
            (44,),
            None,
            (Decimal("0.25"),),
            (8, 31, date.today(), Decimal("0.75"), 44),
        ]
        with patch.object(repo, "PostgreSQL", return_value=db):
            repo.registrar_jornada(7, 9, 31, date.today(), Decimal("0.75"))
        salary_query = db.execute_query.call_args_list[1]
        self.assertIn("fecha_vigencia <= %s", salary_query.args[0])
        self.assertEqual(salary_query.args[1], (7, 31, date.today()))
        db.conn.commit.assert_called_once()

    def test_limita_un_dia_sumando_jornadas_de_otras_obras(self):
        db = MagicMock()
        db.execute_query.side_effect = [
            (31, "ACTIVO"),
            (44,),
            None,
            (Decimal("0.50"),),
        ]
        with patch.object(repo, "PostgreSQL", return_value=db):
            with self.assertRaisesRegex(
                repo.TrabajadoresCostosConflictError, "no pueden superar un día"
            ):
                repo.registrar_jornada(7, 9, 31, date.today(), Decimal("0.75"))
        db.conn.commit.assert_not_called()
        db.conn.rollback.assert_called_once()

    def test_cierre_snapshot_calcula_desde_salario_referenciado_y_no_manual(self):
        db = MagicMock()
        db.execute_query.side_effect = [(2,), (False,), None]
        repo.cerrar_mano_obra(7, 9, db)
        insert_sql = db.execute_query.call_args_list[2].args[0]
        self.assertIn("ROUND(j.dias_trabajados * s.salario_diario, 2)", insert_sql)
        self.assertIn("ON CONFLICT (id_jornada) DO NOTHING", insert_sql)

    def test_cierre_rechaza_costos_manual_y_calculado_simultaneos(self):
        db = MagicMock()
        db.execute_query.side_effect = [(1,), (True,)]
        with self.assertRaisesRegex(repo.TrabajadoresCostosConflictError, "manuales"):
            repo.cerrar_mano_obra(7, 9, db)
        self.assertEqual(db.execute_query.call_count, 2)


if __name__ == "__main__":
    unittest.main()
