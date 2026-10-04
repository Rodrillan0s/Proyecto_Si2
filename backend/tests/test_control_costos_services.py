from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
import unittest

from app.services import control_costos_services as service


TOKEN = {
    "id_empresa": 7,
    "nro_usuario": 21,
    "nombre_rol": "RESPONSABLE DEL PROYECTO",
}

LINEA = {
    "id_control_costo": 3,
    "id_empresa": 7,
    "id_obra": 9,
    "id_estimacion_base": 15,
    "estado": "ACTIVO",
}

PARTIDA = {
    "id_partida_presupuestaria": 31,
    "id_estimacion": 15,
    "id_analisis_precio_unitario": 44,
    "item_codigo": "01.01",
    "cantidad": Decimal("10.000"),
    "costo_directo_unitario": Decimal("25.00"),
    "descripcion_partida": "Muro de ladrillo",
    "unidad": "m2",
}


class ControlCostosServicesTests(unittest.TestCase):
    def test_selecciona_presupuesto_aprobado_como_linea_base(self):
        created = {**LINEA, "version_presupuesto": 2, "moneda": "BOB"}
        with patch.object(service.control_costos_repos, "crear_linea_base", return_value=created), patch.object(
            service.bitacora_repos, "registrar_bitacora"
        ):
            response = service.crear_linea_base(
                {"id_obra": 9, "id_estimacion_base": 15}, TOKEN
            )
        self.assertTrue(response["success"])
        self.assertEqual(response["data"]["id_estimacion_base"], 15)

    def test_rechaza_token_sin_empresa(self):
        with self.assertRaises(service.ControlCostosError) as ctx:
            service._empresa({"nro_usuario": 1})
        self.assertEqual(ctx.exception.status_code, 403)

    def test_registra_costo_en_partida_de_linea_base(self):
        payload = {
            "id_control_costo": 3,
            "id_partida_presupuestaria": 31,
            "fecha": date(2026, 9, 30),
            "concepto": "Compra de ladrillos",
            "categoria": "MATERIAL",
            "cantidad": Decimal("2.0000"),
            "costo_unitario": Decimal("15.00"),
            "monto": Decimal("30.00"),
            "documento": "FAC-10",
            "observacion": None,
        }
        saved = {**payload, "id_costo_ejecutado": 80, "estado": "REGISTRADO"}
        with patch.object(
            service.control_costos_repos, "obtener_linea_base_por_id", return_value=LINEA
        ), patch.object(
            service.control_costos_repos, "obtener_partida_base", return_value=PARTIDA
        ), patch.object(
            service.control_costos_repos, "crear_costo", return_value=saved
        ) as create_cost, patch.object(
            service.bitacora_repos, "registrar_bitacora"
        ):
            response = service.registrar_costo(payload, TOKEN)
        self.assertEqual(response["data"]["monto"], Decimal("30.00"))
        self.assertEqual(create_cost.call_args.args[1:], (7, 21))

    def test_rechaza_monto_que_no_coincide_con_cantidad_por_unitario(self):
        payload = {
            "id_control_costo": 3,
            "id_partida_presupuestaria": 31,
            "fecha": date(2026, 9, 30),
            "concepto": "Costo inconsistente",
            "categoria": "OTRO",
            "cantidad": Decimal("2"),
            "costo_unitario": Decimal("15"),
            "monto": Decimal("31"),
        }
        with self.assertRaisesRegex(service.ControlCostosError, "cantidad por costo_unitario"):
            service.registrar_costo(payload, TOKEN)

    def test_rechaza_partida_de_otra_estimacion(self):
        payload = {
            "id_control_costo": 3,
            "id_partida_presupuestaria": 999,
            "fecha": date(2026, 9, 30),
            "concepto": "Costo",
            "categoria": "OTRO",
            "cantidad": Decimal("1"),
            "costo_unitario": Decimal("5"),
            "monto": Decimal("5"),
        }
        with patch.object(
            service.control_costos_repos, "obtener_linea_base_por_id", return_value=LINEA
        ), patch.object(
            service.control_costos_repos, "obtener_partida_base", return_value=None
        ):
            with self.assertRaisesRegex(service.ControlCostosError, "exactamente"):
                service.registrar_costo(payload, TOKEN)

    def test_anula_costo_sin_eliminarlo(self):
        annulled = {
            "id_costo_ejecutado": 80,
            "estado": "ANULADO",
            "motivo_anulacion": "Documento duplicado",
            "anulado_por": 21,
        }
        with patch.object(
            service.control_costos_repos, "anular_costo", return_value=annulled
        ) as annul, patch.object(service.bitacora_repos, "registrar_bitacora"):
            response = service.anular_costo(
                80, "Documento duplicado", TOKEN
            )
        self.assertEqual(response["data"]["estado"], "ANULADO")
        annul.assert_called_once_with(80, "Documento duplicado", 7, 21)

    def test_compara_costo_original_revisado_y_ejecutado(self):
        rows = [
            {
                "costo_presupuestado": Decimal("250.00"),
                "impacto_ordenes_aprobadas": Decimal("50.00"),
                "presupuesto_revisado": Decimal("300.00"),
                "costo_ejecutado": Decimal("330.00"),
            }
        ]
        with patch.object(
            service.control_costos_repos, "obtener_linea_base", return_value=LINEA
        ), patch.object(
            service.control_costos_repos, "comparacion_por_obra", return_value=rows
        ):
            response = service.obtener_comparacion(9, TOKEN)
        totals = response["data"]["totales"]
        self.assertEqual(totals["variacion_original"], Decimal("80.00"))
        self.assertEqual(totals["variacion_original_porcentaje"], Decimal("32.00"))
        self.assertEqual(totals["variacion_revisada"], Decimal("30.00"))
        self.assertEqual(totals["variacion_revisada_porcentaje"], Decimal("10.00"))

    def test_porcentaje_es_nulo_si_presupuesto_es_cero(self):
        self.assertIsNone(service._porcentaje(Decimal("10"), Decimal("0")))

    def test_prepara_aumento_de_cantidad_con_snapshot_cu16(self):
        raw = [
            {
                "id_partida_presupuestaria": 31,
                "tipo_cambio": "AUMENTO_CANTIDAD",
                "cantidad_delta": Decimal("2.000"),
                "costo_nuevo": None,
                "observacion": "Mayor metrado",
            }
        ]
        with patch.object(
            service.control_costos_repos, "obtener_partida_base", return_value=PARTIDA
        ):
            details = service._preparar_detalles(raw, LINEA, 7)
        self.assertEqual(details[0]["cantidad_revisada"], Decimal("12.000"))
        self.assertEqual(details[0]["impacto_costo"], Decimal("50.00"))
        self.assertEqual(details[0]["costo_anterior"], Decimal("25.00"))

    def test_nueva_orden_parte_del_estado_revisado_por_ordenes_aprobadas(self):
        revised_part = {
            **PARTIDA,
            "cantidad_revisada_actual": Decimal("12.000"),
            "costo_revisado_actual": Decimal("30.00"),
        }
        raw = [
            {
                "id_partida_presupuestaria": 31,
                "tipo_cambio": "AUMENTO_CANTIDAD",
                "cantidad_delta": Decimal("1.000"),
            }
        ]
        with patch.object(
            service.control_costos_repos,
            "obtener_partida_base",
            return_value=revised_part,
        ):
            details = service._preparar_detalles(raw, LINEA, 7)
        self.assertEqual(details[0]["cantidad_anterior"], Decimal("12.000"))
        self.assertEqual(details[0]["cantidad_revisada"], Decimal("13.000"))
        self.assertEqual(details[0]["impacto_costo"], Decimal("30.00"))

    def test_crea_orden_pendiente_con_historial_por_repository(self):
        payload = {
            "id_control_costo": 3,
            "codigo": "OC-001",
            "titulo": "Mayor metrado",
            "descripcion": None,
            "justificacion": "Cambio solicitado por supervision",
            "fecha": date(2026, 9, 30),
            "impacto_plazo_dias": 2,
            "detalles": [
                {
                    "id_partida_presupuestaria": 31,
                    "id_analisis_precio_unitario": None,
                    "tipo_cambio": "AUMENTO_CANTIDAD",
                    "item_codigo_snapshot": None,
                    "descripcion_snapshot": None,
                    "unidad_snapshot": None,
                    "cantidad_delta": Decimal("2.000"),
                    "costo_nuevo": None,
                    "observacion": None,
                }
            ],
        }
        created = {"id_orden_cambio": 5, "estado": "PENDIENTE"}
        full = {**created, "detalles": [{"impacto_costo": Decimal("50.00")}]}
        with patch.object(
            service.control_costos_repos, "obtener_linea_base_por_id", return_value=LINEA
        ), patch.object(
            service.control_costos_repos, "obtener_partida_base", return_value=PARTIDA
        ), patch.object(
            service.control_costos_repos, "crear_orden", return_value=created
        ) as create_order, patch.object(
            service.control_costos_repos, "obtener_orden", return_value=full
        ), patch.object(service.bitacora_repos, "registrar_bitacora"):
            response = service.crear_orden(payload, TOKEN)
        self.assertEqual(response["data"]["estado"], "PENDIENTE")
        self.assertEqual(create_order.call_args.args[2], Decimal("50.00"))

    def test_rechaza_disminucion_que_deja_cantidad_negativa(self):
        raw = [
            {
                "id_partida_presupuestaria": 31,
                "tipo_cambio": "DISMINUCION_CANTIDAD",
                "cantidad_delta": Decimal("-11.000"),
            }
        ]
        with patch.object(
            service.control_costos_repos, "obtener_partida_base", return_value=PARTIDA
        ):
            with self.assertRaisesRegex(service.ControlCostosError, "revisada"):
                service._preparar_detalles(raw, LINEA, 7)

    def test_aprueba_solo_orden_pendiente_con_detalles(self):
        order = {
            "id_orden_cambio": 5,
            "estado": "PENDIENTE",
            "detalles": [{"id_orden_cambio_detalle": 1}],
        }
        approved = {**order, "estado": "APROBADA", "decidido_por": 21}
        with patch.object(
            service.control_costos_repos, "obtener_orden", return_value=order
        ), patch.object(
            service.control_costos_repos, "decidir_orden", return_value=approved
        ) as decide, patch.object(
            service.bitacora_repos, "registrar_bitacora"
        ):
            response = service.aprobar_orden(5, "Conforme", TOKEN)
        self.assertEqual(response["data"]["estado"], "APROBADA")
        self.assertEqual(decide.call_args.args[1], "APROBADA")

    def test_rechazo_requiere_motivo(self):
        with self.assertRaisesRegex(service.ControlCostosError, "motivo"):
            service.rechazar_orden(5, "   ", TOKEN)

    def test_rechaza_orden_pendiente_y_conserva_motivo(self):
        order = {
            "id_orden_cambio": 5,
            "estado": "PENDIENTE",
            "detalles": [{"id_orden_cambio_detalle": 1}],
        }
        rejected = {
            **order,
            "estado": "RECHAZADA",
            "motivo_decision": "Sin respaldo tecnico",
        }
        with patch.object(
            service.control_costos_repos, "obtener_orden", return_value=order
        ), patch.object(
            service.control_costos_repos, "decidir_orden", return_value=rejected
        ) as decide, patch.object(service.bitacora_repos, "registrar_bitacora"):
            response = service.rechazar_orden(
                5, "Sin respaldo tecnico", TOKEN
            )
        self.assertEqual(response["data"]["estado"], "RECHAZADA")
        self.assertEqual(decide.call_args.args[1:3], ("RECHAZADA", "Sin respaldo tecnico"))

    def test_consulta_historial_solo_de_orden_de_la_empresa(self):
        order = {"id_orden_cambio": 5, "estado": "APROBADA", "detalles": []}
        history = [{"accion": "CREACION"}, {"accion": "APROBACION"}]
        with patch.object(
            service.control_costos_repos, "obtener_orden", return_value=order
        ), patch.object(
            service.control_costos_repos, "listar_historial", return_value=history
        ) as list_history:
            response = service.listar_historial(5, TOKEN)
        self.assertEqual(len(response["data"]), 2)
        list_history.assert_called_once_with(5, 7)

    def test_repository_no_escribe_tablas_cu16(self):
        repository = Path(service.control_costos_repos.__file__).read_text(encoding="utf-8")
        forbidden = (
            "UPDATE obras.t_estimacion ",
            "UPDATE obras.t_estimacion_analisis_precio_unitario ",
            "UPDATE obras.t_analisis_precio_unitario ",
            "DELETE FROM obras.t_estimacion",
            "DELETE FROM obras.t_analisis_precio_unitario",
        )
        for statement in forbidden:
            self.assertNotIn(statement, repository)


if __name__ == "__main__":
    unittest.main()
