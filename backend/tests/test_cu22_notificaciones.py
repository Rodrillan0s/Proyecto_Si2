"""Pruebas unitarias aisladas para CU22 (HU141 y HU142).

No abre conexiones reales a PostgreSQL ni servicios externos.
"""
import os
import sys
import unittest
from decimal import Decimal
from unittest.mock import patch, MagicMock

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services import notificaciones_services
from app.repos import notificaciones_repos


def _token(nro_usuario=10, rol="ADMINISTRADOR_EMPRESA", id_empresa=1):
    return {
        "nro_usuario": nro_usuario,
        "nombre_rol": rol,
        "id_empresa": id_empresa,
    }


class TestCU22ConfiguracionAlertasHU141(unittest.TestCase):
    def setUp(self):
        notificaciones_services._limpiar_cache_idempotencia()

    def test_rechaza_roles_no_autorizados(self):
        for rol in ("CLIENTE", "ELECTRICO", "SUPERVISOR_OBRA", "ALBAÑIL"):
            with self.assertRaises(notificaciones_services.NotificacionesError) as ctx:
                notificaciones_services.obtener_configuracion_alertas(_token(rol=rol))
            self.assertEqual(ctx.exception.status_code, 403)

    def test_admin_empresa_no_puede_consultar_otra_empresa(self):
        with self.assertRaises(notificaciones_services.NotificacionesError) as ctx:
            notificaciones_services.obtener_configuracion_alertas(
                _token(rol="ADMINISTRADOR_EMPRESA", id_empresa=1),
                id_empresa_solicitada=2,
            )
        self.assertEqual(ctx.exception.status_code, 403)

    def test_jefe_obra_no_puede_modificar_obra_de_otra_empresa(self):
        with patch.object(
            notificaciones_repos,
            "validar_obra_empresa",
            return_value={"id_obra": 99, "nombre": "Obra Ajena", "id_empresa": 2},
        ):
            with self.assertRaises(notificaciones_services.NotificacionesError) as ctx:
                notificaciones_services.actualizar_configuracion_alertas(
                    _token(rol="JEFE DE OBRA", id_empresa=1),
                    {
                        "id_obra": 99,
                        "configuraciones": [
                            {"tipo_evento": "INCIDENCIA", "activo": False, "roles_destino": ["JEFE DE OBRA"]}
                        ],
                    },
                )
        self.assertEqual(ctx.exception.status_code, 403)

    def test_admin_global_puede_consultar_empresa_especifica(self):
        with patch.object(
            notificaciones_repos,
            "obtener_configuraciones_alertas_db",
            return_value=[
                {
                    "id_configuracion": 1,
                    "id_empresa": 3,
                    "id_obra": None,
                    "tipo_evento": "INCIDENCIA",
                    "activo": False,
                    "roles_destino": ["JEFE DE OBRA"],
                    "actualizado_por": 1,
                    "actualizado_en": "2026-11-21 10:00:00",
                }
            ],
        ):
            res = notificaciones_services.obtener_configuracion_alertas(
                _token(nro_usuario=1, rol="ADMINISTRADOR", id_empresa=1),
                id_empresa_solicitada=3,
            )
        self.assertTrue(res["success"])
        self.assertEqual(res["id_empresa"], 3)
        self.assertFalse(res["migracion_pendiente"])
        inc = next(x for x in res["data"] if x["tipo_evento"] == "INCIDENCIA")
        self.assertFalse(inc["activo"])
        self.assertEqual(inc["origen"], "EMPRESA")
        self.assertEqual(inc["roles_destino"], ["JEFE DE OBRA"])

    def test_prioridad_obra_sobrescribe_empresa(self):
        reglas = [
            {
                "id_empresa": 1,
                "id_obra": None,
                "tipo_evento": "AVANCE_OBRA",
                "activo": False,
                "roles_destino": ["ADMINISTRADOR_EMPRESA"],
            },
            {
                "id_empresa": 1,
                "id_obra": 25,
                "tipo_evento": "AVANCE_OBRA",
                "activo": True,
                "roles_destino": ["JEFE DE OBRA", "SUPERVISOR_OBRA"],
            },
        ]
        with patch.object(notificaciones_repos, "obtener_configuraciones_alertas_db", return_value=reglas):
            pref = notificaciones_services.resolver_configuracion_evento(1, "AVANCE_OBRA", id_obra=25)
        self.assertTrue(pref["activo"])
        self.assertEqual(pref["origen"], "OBRA")
        self.assertEqual(pref["roles_destino"], ["JEFE DE OBRA", "SUPERVISOR_OBRA"])

    def test_degradacion_segura_si_migracion_no_aplicada(self):
        with patch.object(
            notificaciones_repos,
            "obtener_configuraciones_alertas_db",
            side_effect=notificaciones_repos.NotificacionesSchemaMissing("tabla faltante"),
        ):
            res = notificaciones_services.obtener_configuracion_alertas(_token())
        self.assertTrue(res["success"])
        self.assertTrue(res["migracion_pendiente"])
        self.assertEqual(len(res["data"]), len(notificaciones_services.CATALOGO_EVENTOS_ALERTA))

        with patch.object(
            notificaciones_repos,
            "guardar_configuraciones_alertas_db",
            side_effect=notificaciones_repos.NotificacionesSchemaMissing("tabla faltante"),
        ):
            with self.assertRaises(notificaciones_services.NotificacionesError) as ctx:
                notificaciones_services.actualizar_configuracion_alertas(
                    _token(),
                    {"configuraciones": [{"tipo_evento": "INCIDENCIA", "activo": False, "roles_destino": []}]},
                )
        self.assertEqual(ctx.exception.status_code, 503)

    def test_validacion_evento_invalido_y_rol_invalido(self):
        with self.assertRaises(notificaciones_services.NotificacionesError) as ctx1:
            notificaciones_services.actualizar_configuracion_alertas(
                _token(),
                {"configuraciones": [{"tipo_evento": "EVENTO_FICTICIO", "activo": True, "roles_destino": []}]},
            )
        self.assertEqual(ctx1.exception.status_code, 400)

        with self.assertRaises(notificaciones_services.NotificacionesError) as ctx2:
            notificaciones_services.actualizar_configuracion_alertas(
                _token(),
                {"configuraciones": [{"tipo_evento": "INCIDENCIA", "activo": True, "roles_destino": ["ROL_INVENTADO"]}]},
            )
        self.assertEqual(ctx2.exception.status_code, 400)


class TestCU22EmisionEIdempotencia(unittest.TestCase):
    def setUp(self):
        notificaciones_services._limpiar_cache_idempotencia()

    def test_evento_desactivado_no_persiste_ni_envia_ws(self):
        with patch.object(
            notificaciones_repos,
            "obtener_configuraciones_alertas_db",
            return_value=[
                {
                    "id_empresa": 1,
                    "id_obra": None,
                    "tipo_evento": "INCIDENCIA",
                    "activo": False,
                    "roles_destino": ["ADMINISTRADOR_EMPRESA"],
                }
            ],
        ), patch.object(notificaciones_repos, "guardar_notificacion_db") as mock_guardar, patch.object(
            notificaciones_services, "_despachar_ws_seguro"
        ) as mock_ws:
            enviadas = notificaciones_services.emitir_notificacion_push_empresa(
                titulo="Incidencia",
                cuerpo="Detalle",
                tipo_referencia="INCIDENCIA",
                id_empresa=1,
                id_obra=5,
                clave_evento="INCIDENCIA:CREAR:100",
            )
        self.assertEqual(enviadas, 0)
        mock_guardar.assert_not_called()
        mock_ws.assert_not_called()

    def test_filtra_usuarios_de_otra_empresa_y_evita_duplicados(self):
        with patch.object(
            notificaciones_repos,
            "obtener_configuraciones_alertas_db",
            return_value=[],
        ), patch.object(
            notificaciones_repos,
            "filtrar_usuarios_autorizados_empresa",
            return_value=[11],  # usuario 99 de otra empresa queda fuera
        ), patch.object(
            notificaciones_repos,
            "obtener_usuarios_por_roles",
            return_value=[{"nro_usuario": 11, "nombre_usuario": "jefe", "nombre_rol": "JEFE DE OBRA", "id_empresa": 1}],
        ), patch.object(
            notificaciones_repos,
            "guardar_notificacion_db",
            return_value={"id_notificacion": 501, "fecha_creacion": "2026-11-21 14:00:00", "duplicada": False},
        ) as mock_guardar, patch.object(
            notificaciones_services, "_despachar_ws_seguro"
        ) as mock_ws:
            primera = notificaciones_services.emitir_notificacion_push_empresa(
                titulo="Avance",
                cuerpo="50%",
                tipo_referencia="AVANCE_OBRA",
                id_empresa=1,
                id_obra=7,
                usuarios_especificos=[11, 99],
                clave_evento="AVANCE_OBRA:7:3:50",
            )
            segunda = notificaciones_services.emitir_notificacion_push_empresa(
                titulo="Avance",
                cuerpo="50%",
                tipo_referencia="AVANCE_OBRA",
                id_empresa=1,
                id_obra=7,
                usuarios_especificos=[11, 99],
                clave_evento="AVANCE_OBRA:7:3:50",
            )
        self.assertEqual(primera, 1)
        self.assertEqual(segunda, 0)
        self.assertEqual(mock_guardar.call_count, 1)
        self.assertEqual(mock_ws.call_count, 1)


class TestCU22EstadoNotificacionesHU142(unittest.TestCase):
    def test_listar_y_marcar_lectura_aislado_por_usuario(self):
        with patch.object(
            notificaciones_repos,
            "obtener_notificaciones_por_usuario_db",
            return_value=[
                {"id_notificacion": 1, "titulo": "A", "cuerpo": "x", "tipo_referencia": "INCIDENCIA", "leido": False},
                {"id_notificacion": 2, "titulo": "B", "cuerpo": "y", "tipo_referencia": "AVANCE_OBRA", "leido": True},
            ],
        ):
            res = notificaciones_services.listar_mis_notificaciones(10)
        self.assertTrue(res["success"])
        self.assertEqual(res["no_leidas"], 1)
        self.assertEqual(len(res["data"]), 2)

        with patch.object(notificaciones_repos, "marcar_notificacion_leida_db", return_value=False):
            with self.assertRaises(ValueError):
                notificaciones_services.cambiar_estado_leido(nro_usuario=10, id_notificacion=999)

        with patch.object(notificaciones_repos, "marcar_todas_las_notificaciones_leidas_db", return_value=3):
            res_all = notificaciones_services.cambiar_estado_leido(nro_usuario=10, marcar_todo=True)
        self.assertTrue(res_all["success"])
        self.assertEqual(res_all["actualizadas"], 3)


class TestCU22IntegracionProductoresReales(unittest.TestCase):
    def test_incidencia_registrar_emite_con_firma_valida(self):
        from app.services import incidencia_services

        with patch.object(incidencia_services, "_empresa_id", return_value=1), patch.object(
            incidencia_services, "es_trabajador", return_value=False
        ), patch.object(
            incidencia_services.incidencia_repos, "obtener_empresa_obra", return_value=1
        ), patch.object(
            incidencia_services.incidencia_repos, "crear", return_value=77
        ), patch.object(
            incidencia_services.incidencia_repos, "crear_seguimiento"
        ), patch.object(
            incidencia_services, "_log"
        ), patch.object(
            notificaciones_services, "emitir_notificacion_push_empresa", return_value=1
        ) as mock_emit:
            res = incidencia_services.registrar(
                {"id_obra": 4, "titulo": "Fuga", "descripcion": "Tubería rota", "prioridad": "ALTA"},
                _token(nro_usuario=10, rol="JEFE DE OBRA", id_empresa=1),
            )
        self.assertTrue(res["success"])
        mock_emit.assert_called_once()
        kwargs = mock_emit.call_args.kwargs
        self.assertEqual(kwargs["id_empresa"], 1)
        self.assertEqual(kwargs["tipo_referencia"], "INCIDENCIA")
        self.assertEqual(kwargs["id_obra"], 4)
        self.assertEqual(kwargs["nro_referencia"], 77)
        self.assertNotIn("tipo", kwargs)

    def test_obra_cambio_estado_emite_alerta(self):
        from app.services import obra_services

        with patch.object(
            obra_services.obra_repos, "actualizar_estado_obra_sp", return_value={"success": True}
        ), patch.object(
            obra_services.bitacora_repos, "registrar_bitacora"
        ), patch.object(
            notificaciones_services, "emitir_notificacion_push_empresa", return_value=1
        ) as mock_emit:
            res = obra_services.actualizar_estado_obra(
                id_obra=15,
                nuevo_estado="PAUSADO",
                token_data=_token(nro_usuario=10, rol="ADMINISTRADOR_EMPRESA", id_empresa=1),
            )
        self.assertTrue(res["success"])
        mock_emit.assert_called_once()
        kwargs = mock_emit.call_args.kwargs
        self.assertEqual(kwargs["tipo_referencia"], "OBRA_ESTADO")
        self.assertEqual(kwargs["id_obra"], 15)
        self.assertEqual(kwargs["id_empresa"], 1)

    def test_orden_cambio_creacion_emite_alerta(self):
        from app.services import control_costos_services

        with patch.object(control_costos_services, "_empresa", return_value=1), patch.object(
            control_costos_services, "_usuario", return_value=10
        ), patch.object(
            control_costos_services.control_costos_repos,
            "obtener_linea_base_por_id",
            return_value={"id_control_costo": 2, "id_obra": 18},
        ), patch.object(
            control_costos_services,
            "_preparar_detalles",
            return_value=[{"impacto_costo": Decimal("1500.00")}],
        ), patch.object(
            control_costos_services.control_costos_repos,
            "crear_orden",
            return_value={"id_orden_cambio": 31},
        ), patch.object(
            control_costos_services, "_log"
        ), patch.object(
            control_costos_services, "obtener_orden", return_value={"success": True, "data": {"id_orden_cambio": 31}}
        ), patch.object(
            notificaciones_services, "emitir_notificacion_push_empresa", return_value=1
        ) as mock_emit:
            res = control_costos_services.crear_orden(
                {
                    "id_control_costo": 2,
                    "codigo": "OC-01",
                    "titulo": "Adicional zapatas",
                    "justificacion": "Suelo blando",
                    "detalles": [{}],
                },
                _token(),
            )
        self.assertTrue(res["success"])
        mock_emit.assert_called_once()
        kwargs = mock_emit.call_args.kwargs
        self.assertEqual(kwargs["tipo_referencia"], "ORDEN_CAMBIO")
        self.assertEqual(kwargs["id_obra"], 18)
        self.assertEqual(kwargs["nro_referencia"], 31)


if __name__ == "__main__":
    unittest.main()
