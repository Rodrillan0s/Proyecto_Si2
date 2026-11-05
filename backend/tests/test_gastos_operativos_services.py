"""CU32: calculos de CU17, autorizacion HTTP y atomicidad sin acceder a produccion."""
from contextlib import ExitStack
from copy import deepcopy
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.repos import obra_repos
from app.routes import control_costos_routes, obra_routes
from app.services import gastos_operativos_services as svc, obra_services
from app.utils import security


TOKEN = {"id_empresa": 7, "nro_usuario": 21, "nombre_rol": "JEFE DE OBRA"}
OBRA = {"id_obra": 9, "id_empresa": 7, "codigo": "O-9", "nombre": "Obra",
        "estado_obra": "FINALIZADO", "moneda": "BOB"}
LINEA = {"id_control_costo": 3, "id_estimacion_base": 15,
         "presupuesto_estado": "APROBADA", "estado": "ACTIVO"}
ROWS = [{"costo_presupuestado": Decimal("250.00"),
         "impacto_ordenes_aprobadas": Decimal("50.00"),
         "presupuesto_revisado": Decimal("300.00"),
         "costo_ejecutado": Decimal("330.00")}]
COSTS = [{"categoria": "MATERIAL", "monto": Decimal("100.10"), "estado": "REGISTRADO"},
         {"categoria": "MANO_OBRA", "monto": Decimal("229.90"), "estado": "REGISTRADO"},
         {"categoria": "EQUIPO", "monto": Decimal("999.00"), "estado": "ANULADO"}]


class GastosOperativosTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.db = MagicMock()
        self.stack.enter_context(patch.object(svc, "PostgreSQL", return_value=self.db))
        self.repo = svc.control_costos_repos
        self.obra = self.stack.enter_context(patch.object(self.repo, "obtener_obra", return_value=dict(OBRA)))
        self.linea = self.stack.enter_context(patch.object(self.repo, "obtener_linea_base", return_value=dict(LINEA)))
        self.rows = self.stack.enter_context(patch.object(self.repo, "comparacion_por_obra", return_value=deepcopy(ROWS)))
        self.costs = self.stack.enter_context(patch.object(self.repo, "listar_costos", return_value=deepcopy(COSTS)))
        self.payroll = self.stack.enter_context(patch.object(
            svc.trabajadores_costos_repos, "listar_cierre_mano_obra", return_value=[]
        ))
        self.close_payroll = self.stack.enter_context(patch.object(
            svc.trabajadores_costos_repos, "cerrar_mano_obra"
        ))
        self.orders = self.stack.enter_context(patch.object(self.repo, "listar_ordenes", return_value=[
            {"estado": "APROBADA"}, {"estado": "PENDIENTE"}, {"estado": "RECHAZADA"}]))
        self.update = self.stack.enter_context(patch.object(obra_repos, "actualizar_estado_obra_sp", return_value={"success": True}))
        self.insert = self.stack.enter_context(patch.object(self.repo, "crear_costo"))

    def test_reutiliza_comparacion_y_excluye_anulados_del_desglose(self):
        data = svc.obtener_resumen_final(9, TOKEN)["data"]
        totals = data["resumen"]
        self.assertEqual(totals["costo_final_registrado"], Decimal("330.00"))
        self.assertEqual(totals["variacion_original"], Decimal("80.00"))
        self.assertEqual(totals["variacion_revisada"], Decimal("30.00"))
        self.assertEqual(totals["variacion_original_porcentaje"], Decimal("32.00"))
        self.assertEqual(totals["variacion_revisada_porcentaje"], Decimal("10.00"))
        self.assertEqual(totals["total_costos_anulados"], 1)
        self.assertEqual(totals["ordenes_pendientes"], 1)
        self.assertEqual(data["desglose_por_categoria"]["EQUIPO"], Decimal("0.00"))
        self.assertEqual(set(data["desglose_por_categoria"]), svc.costos.CATEGORIAS_COSTO)
        self.costs.assert_any_call(7, id_obra=9, id_control_costo=3, estado="REGISTRADO", db=self.db)
        self.rows.assert_called_once_with(7, 9, db=self.db)
        self.insert.assert_not_called()
        self.update.assert_not_called()
        self.db.conn.commit.assert_not_called()

    def test_todas_las_categorias_se_consolidan_con_decimales(self):
        self.costs.return_value = [dict(categoria=key, monto=Decimal("66.00"), estado="REGISTRADO")
                                   for key in svc.costos.CATEGORIAS_COSTO]
        data = svc.obtener_resumen_final(9, TOKEN)["data"]
        self.assertEqual(sum(data["desglose_por_categoria"].values()), Decimal("330.00"))
        self.assertTrue(all(value == Decimal("66.00") for value in data["desglose_por_categoria"].values()))

    def test_sin_costos_y_presupuesto_cero_no_divide_por_cero(self):
        self.rows.return_value = []
        self.costs.return_value = []
        data = svc.obtener_resumen_final(9, TOKEN)["data"]
        self.assertEqual(data["resumen"]["costo_final_registrado"], Decimal("0.00"))
        self.assertIsNone(data["resumen"]["variacion_original_porcentaje"])
        self.assertIsNone(data["resumen"]["variacion_revisada_porcentaje"])

    def test_obra_no_finalizada_rechazada_antes_de_calcular(self):
        self.obra.return_value = {**OBRA, "estado_obra": "ACTIVO"}
        with self.assertRaises(svc.costos.ControlCostosError) as ctx:
            svc.obtener_resumen_final(9, TOKEN)
        self.assertEqual(ctx.exception.status_code, 409)
        self.rows.assert_not_called()

    def test_obra_inexistente_o_ajena_no_expone_costos(self):
        self.obra.return_value = None
        with self.assertRaises(svc.costos.ControlCostosError) as ctx:
            svc.obtener_resumen_final(9, TOKEN)
        self.assertEqual(ctx.exception.status_code, 404)
        self.obra.assert_called_once_with(7, 9, db=self.db, bloquear=False)
        self.rows.assert_not_called()

    def test_token_sin_empresa_no_abre_transaccion(self):
        with self.assertRaises(svc.costos.ControlCostosError) as ctx:
            svc.obtener_resumen_final(9, {"nro_usuario": 21})
        self.assertEqual(ctx.exception.status_code, 403)
        self.db.create_connection.assert_not_called()

    def test_finalizar_confirma_estado_y_calculo_sin_insertar_costos(self):
        self.obra.side_effect = [{**OBRA, "estado_obra": "ACTIVO"}, dict(OBRA)]
        result = svc.finalizar_obra(9, TOKEN)
        self.assertEqual(result["resumen_economico_final"]["obra"]["estado_obra"], "FINALIZADO")
        self.close_payroll.assert_called_once_with(7, 9, self.db)
        self.update.assert_called_once_with(9, 7, "FINALIZADO", db=self.db)
        self.db.conn.commit.assert_called_once()
        self.obra.assert_any_call(7, 9, db=self.db, bloquear=True)
        self.insert.assert_not_called()
        self.db.execute_query.assert_called_once_with("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")

    def test_sin_linea_base_revierte_finalizacion(self):
        self.linea.return_value = None
        with self.assertRaises(svc.costos.ControlCostosError):
            svc.finalizar_obra(9, TOKEN)
        self.update.assert_called_once()
        self.db.conn.commit.assert_not_called()
        self.assertEqual(self.db.conn.rollback.call_count, 2)
        self.db.close_connection.assert_called_once()

    def test_presupuesto_no_aprobado_revierte_finalizacion(self):
        self.linea.return_value = {**LINEA, "presupuesto_estado": "BORRADOR"}
        with self.assertRaises(svc.costos.ControlCostosError) as ctx:
            svc.finalizar_obra(9, TOKEN)
        self.assertEqual(ctx.exception.status_code, 409)
        self.db.conn.commit.assert_not_called()

    def test_fallo_del_sp_no_calcula_ni_confirma(self):
        self.update.return_value = {"success": False, "error": "Transicion invalida"}
        with self.assertRaisesRegex(svc.costos.ControlCostosError, "Transicion invalida"):
            svc.finalizar_obra(9, TOKEN)
        self.rows.assert_not_called()
        self.db.conn.commit.assert_not_called()

    def test_verifica_estado_real_devuelto_por_bd(self):
        self.obra.return_value = {**OBRA, "estado_obra": "ACTIVO"}
        with self.assertRaises(svc.costos.ControlCostosError):
            svc.finalizar_obra(9, TOKEN)
        self.db.conn.commit.assert_not_called()

    def test_error_sql_revierte_y_se_propaga(self):
        self.rows.side_effect = RuntimeError("fallo SQL")
        with self.assertRaisesRegex(RuntimeError, "fallo SQL"):
            svc.finalizar_obra(9, TOKEN)
        self.db.conn.commit.assert_not_called()
        self.db.close_connection.assert_called_once()

    def test_desglose_inconsistente_no_se_publica(self):
        self.costs.return_value = []
        with self.assertRaisesRegex(svc.costos.ControlCostosError, "no coincide"):
            svc.obtener_resumen_final(9, TOKEN)

    def test_integra_varios_trabajadores_en_hu135_y_recalcula_hu136(self):
        self.rows.return_value = [{**ROWS[0], "costo_ejecutado": Decimal("100.10")}]
        self.costs.return_value = [
            {"categoria": "MATERIAL", "monto": Decimal("100.10"), "estado": "REGISTRADO"}
        ]
        self.payroll.return_value = [
            {
                "id_usuario": 31, "nombre_completo": "Trabajador A",
                "nombre_rol": "ALBAÑIL", "fecha": date(2026, 10, day + 1),
                "dias_trabajados": Decimal("1.00"),
                "salario_diario": Decimal("200.00"),
                "costo_calculado": Decimal("200.00"),
            }
            for day in range(10)
        ] + [
            {
                "id_usuario": 32, "nombre_completo": "Trabajador B",
                "nombre_rol": "ELECTRICO", "fecha": date(2026, 10, day + 1),
                "dias_trabajados": Decimal("1.00"),
                "salario_diario": Decimal("150.00"),
                "costo_calculado": Decimal("150.00"),
            }
            for day in range(8)
        ]
        data = svc.obtener_resumen_final(9, TOKEN)["data"]
        totals = data["resumen"]
        self.assertEqual(totals["costo_mano_obra_calculado"], Decimal("3200.00"))
        self.assertEqual(totals["costo_final_registrado"], Decimal("3300.10"))
        self.assertEqual(totals["costo_ejecutado"], Decimal("3300.10"))
        self.assertEqual(totals["variacion_original"], Decimal("3050.10"))
        self.assertEqual(totals["variacion_revisada"], Decimal("3000.10"))
        self.assertEqual(totals["variacion_original_porcentaje"], Decimal("1220.04"))
        self.assertEqual(totals["variacion_revisada_porcentaje"], Decimal("1000.03"))
        self.assertEqual(data["desglose_por_categoria"]["MANO_OBRA"], Decimal("3200.00"))
        self.assertEqual(len(data["mano_obra_trabajadores"]), 18)
        self.assertEqual(totals["total_trabajadores_con_costo"], 2)

    def test_conflicto_de_origen_manual_impide_cerrar_y_no_duplica(self):
        self.close_payroll.side_effect = svc.trabajadores_costos_repos.TrabajadoresCostosConflictError(
            "Hay costos MANO_OBRA manuales y jornadas de trabajadores"
        )
        with self.assertRaises(svc.costos.ControlCostosError) as ctx:
            svc.finalizar_obra(9, TOKEN)
        self.assertEqual(ctx.exception.status_code, 409)
        self.db.conn.commit.assert_not_called()

    def test_resumen_sin_jornadas_conserva_calculo_actual_de_cu17(self):
        data = svc.obtener_resumen_final(9, TOKEN)["data"]
        self.assertEqual(data["resumen"]["costo_final_registrado"], Decimal("330.00"))
        self.assertEqual(data["resumen"]["variacion_original"], Decimal("80.00"))
        self.assertEqual(data["desglose_por_categoria"]["MANO_OBRA"], Decimal("229.90"))

    def test_repositorio_no_confirma_ni_cierra_conexion_compartida(self):
        # Ejecutar la funcion real, no el doble usado para la orquestacion.
        with patch.object(obra_repos, "actualizar_estado_obra_sp", wraps=REAL_UPDATE) as update:
            self.db.execute_query.return_value = ({"success": True},)
            result = update(9, 7, "FINALIZADO", db=self.db)
        self.assertTrue(result["success"])
        self.assertFalse(self.db.execute_query.call_args.kwargs["commit"])
        self.db.close_connection.assert_not_called()


REAL_UPDATE = obra_repos.actualizar_estado_obra_sp


class GastosOperativosHTTPTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(control_costos_routes.router)
        app.include_router(obra_routes.router, prefix="/api/proyectos")
        app.dependency_overrides[security.verificar_token] = lambda: TOKEN
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_resumen_existente_mantiene_contrato(self):
        with patch.object(security, "obtener_permisos_rol", return_value={"Visualizar_control_costos"}), \
             patch.object(svc.costos, "obtener_resumen", return_value={"success": True, "data": {"resumen": {}}}) as resumen, \
             patch.object(svc, "obtener_resumen_final") as final:
            result = self.client.get("/api/control-costos/obras/9/resumen")
        self.assertEqual(result.status_code, 200)
        resumen.assert_called_once_with(9, TOKEN)
        final.assert_not_called()

    def test_consulta_final_reutiliza_permiso_y_serializa_decimales(self):
        with patch.object(security, "obtener_permisos_rol", return_value={"Visualizar_control_costos"}), \
             patch.object(svc, "obtener_resumen_final", return_value={"success": True, "data": {"costo": Decimal("330.10")}}) as final:
            result = self.client.get("/api/control-costos/obras/9/resumen?final=true")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(Decimal(str(result.json()["data"]["costo"])), Decimal("330.10"))
        final.assert_called_once_with(9, TOKEN)

    def test_sin_permiso_no_consulta_cu32(self):
        with patch.object(security, "obtener_permisos_rol", return_value=set()), \
             patch.object(svc, "obtener_resumen_final") as final:
            result = self.client.get("/api/control-costos/obras/9/resumen?final=true")
        self.assertEqual(result.status_code, 403)
        final.assert_not_called()

    def test_error_de_estado_se_expone_como_409(self):
        with patch.object(security, "obtener_permisos_rol", return_value={"Visualizar_control_costos"}), \
             patch.object(svc, "obtener_resumen_final", side_effect=svc.costos.ControlCostosError("Obra no finalizada", 409)):
            result = self.client.get("/api/control-costos/obras/9/resumen?final=true")
        self.assertEqual(result.status_code, 409)

    def test_patch_invoca_cu32_y_conserva_bitacora(self):
        with patch.object(security, "obtener_permisos_rol", return_value={"Modificar_obras"}), \
             patch.object(svc, "finalizar_obra", return_value={"success": True, "resumen_economico_final": {}}) as final, \
             patch.object(obra_services.bitacora_repos, "registrar_bitacora") as log:
            result = self.client.patch("/api/proyectos/9/estado", json={"estado_obra": "FINALIZADO"})
        self.assertEqual(result.status_code, 200)
        self.assertNotIn("resumen_economico_final", result.json())
        final.assert_called_once_with(9, TOKEN)
        log.assert_called_once()

    def test_patch_propaga_error_cu32_sin_bitacora_exitosa(self):
        with patch.object(security, "obtener_permisos_rol", return_value={"Modificar_obras"}), \
             patch.object(svc, "finalizar_obra", side_effect=svc.costos.ControlCostosError("Sin linea base", 404)), \
             patch.object(obra_services.bitacora_repos, "registrar_bitacora") as log:
            result = self.client.patch("/api/proyectos/9/estado", json={"estado_obra": "FINALIZADO"})
        self.assertEqual(result.status_code, 404)
        log.assert_not_called()

    def test_consulta_mano_obra_reutiliza_permiso_y_servicio(self):
        with patch.object(
            security, "obtener_permisos_rol", return_value={"Visualizar_control_costos"}
        ), patch.object(
            control_costos_routes.trabajadores_costos_services,
            "listar_mano_obra",
            return_value={"success": True, "data": {"trabajadores": [], "jornadas": []}},
        ) as listing:
            result = self.client.get("/api/control-costos/obras/9/mano-obra")
        self.assertEqual(result.status_code, 200)
        listing.assert_called_once_with(9, TOKEN)

    def test_salario_diario_y_jornada_exigen_modificar_obras(self):
        with patch.object(security, "obtener_permisos_rol", return_value=set()), patch.object(
            control_costos_routes.trabajadores_costos_services, "registrar_salario"
        ) as salary, patch.object(
            control_costos_routes.trabajadores_costos_services, "registrar_jornada"
        ) as jornada:
            denied_salary = self.client.post(
                "/api/control-costos/obras/9/trabajadores/31/salarios",
                json={"salario_diario": 200, "fecha_vigencia": "2026-10-25"},
            )
            denied_jornada = self.client.post(
                "/api/control-costos/obras/9/jornadas",
                json={"id_usuario": 31, "fecha": "2026-10-25", "dias_trabajados": 1},
            )
        self.assertEqual(denied_salary.status_code, 403)
        self.assertEqual(denied_jornada.status_code, 403)
        salary.assert_not_called()
        jornada.assert_not_called()

    def test_otro_estado_no_invoca_cu32(self):
        with patch.object(svc, "finalizar_obra") as final, \
             patch.object(obra_repos, "actualizar_estado_obra_sp", return_value={"success": True}) as update, \
             patch.object(obra_services.bitacora_repos, "registrar_bitacora"):
            obra_services.actualizar_estado_obra(9, "ACTIVO", TOKEN)
        final.assert_not_called()
        update.assert_called_once_with(9, 7, "ACTIVO")

    def test_administrador_global_resuelve_empresa_de_la_obra(self):
        actor = {"nombre_rol": "ADMINISTRADOR", "nro_usuario": 1}
        with patch.object(obra_repos, "obtener_obra_detalle_sp", return_value={"success": True, "data": OBRA}), \
             patch.object(svc, "finalizar_obra", return_value={"success": True}) as final, \
             patch.object(obra_services.bitacora_repos, "registrar_bitacora"):
            obra_services.actualizar_estado_obra(9, "FINALIZADO", actor)
        final.assert_called_once_with(9, {**actor, "id_empresa": 7})


if __name__ == "__main__":
    unittest.main()
