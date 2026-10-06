"""
Pruebas unitarias para CU19 - Gestión de incidencias (HU69-HU74).
Validan la lógica de negocio en incidencia_services sin requerir conexión a BD
(se mockea app.services.incidencia_services.incidencia_repos).
Ejecutar: python -m pytest tests/test_incidencia_services.py -v
"""

import unittest
from unittest import mock

from app.services import incidencia_services as svc


TOKEN_A = {"id_empresa": 1, "nro_usuario": 10, "nombre_rol": "JEFE DE OBRA"}
TOKEN_B = {"id_empresa": 2, "nro_usuario": 20, "nombre_rol": "JEFE DE OBRA"}


# ─────────────────────────────────────────────────────────────────────────────
# HU69 - Registrar incidencia
# ─────────────────────────────────────────────────────────────────────────────
class RegistrarIncidenciaTests(unittest.TestCase):

    # 1. Registrar incidencia válida
    @mock.patch("app.services.incidencia_services.bitacora_repos")
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_registrar_incidencia_valida(self, mock_repo, mock_bitacora):
        mock_repo.obtener_empresa_obra.return_value = 1
        mock_repo.crear.return_value = 99
        data = {"id_obra": 5, "titulo": "Grieta en muro", "descripcion": "Grieta visible", "prioridad": "ALTA"}

        result = svc.registrar(data, TOKEN_A, "127.0.0.1")

        self.assertTrue(result["success"])
        self.assertEqual(result["id_incidencia"], 99)
        mock_repo.crear.assert_called_once_with(5, None, 10, "Grieta en muro", "Grieta visible", "ALTA", None)
        mock_repo.crear_seguimiento.assert_called_once_with(99, 10, None, "ABIERTA", "Incidencia registrada.")
        mock_bitacora.registrar_bitacora.assert_called_once()

    # 2. Título vacío
    def test_rechaza_titulo_vacio(self):
        data = {"id_obra": 5, "titulo": "   ", "descripcion": "Descripción", "prioridad": "ALTA"}
        with mock.patch("app.services.incidencia_services.incidencia_repos.obtener_empresa_obra", return_value=1):
            with self.assertRaisesRegex(svc.IncidenciaError, "título"):
                svc.registrar(data, TOKEN_A)

    # 3. Prioridad inválida
    def test_rechaza_prioridad_invalida(self):
        data = {"id_obra": 5, "titulo": "Fuga de agua", "descripcion": "Descripción", "prioridad": "URGENTE"}
        with mock.patch("app.services.incidencia_services.incidencia_repos.obtener_empresa_obra", return_value=1):
            with self.assertRaisesRegex(svc.IncidenciaError, "prioridad"):
                svc.registrar(data, TOKEN_A)

    # 4. Proyecto inexistente
    def test_rechaza_proyecto_inexistente(self):
        data = {"id_obra": 999, "titulo": "T", "descripcion": "D", "prioridad": "ALTA"}
        with mock.patch("app.services.incidencia_services.incidencia_repos.obtener_empresa_obra", return_value=None):
            with self.assertRaises(svc.IncidenciaError) as ctx:
                svc.registrar(data, TOKEN_A)
            self.assertEqual(ctx.exception.status_code, 404)

    # 5. Proyecto de otro tenant (el repo ya filtra por la empresa del token y no lo encuentra)
    def test_rechaza_proyecto_de_otro_tenant(self):
        data = {"id_obra": 7, "titulo": "T", "descripcion": "D", "prioridad": "ALTA"}
        with mock.patch("app.services.incidencia_services.incidencia_repos.obtener_empresa_obra") as mock_fn:
            mock_fn.return_value = None
            with self.assertRaises(svc.IncidenciaError):
                svc.registrar(data, TOKEN_A)
            # Se valida que siempre se use la empresa del TOKEN, nunca una enviada por el cliente.
            mock_fn.assert_called_once_with(7, 1)

    # 6. Unidad válida
    @mock.patch("app.services.incidencia_services.bitacora_repos")
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_acepta_unidad_valida(self, mock_repo, mock_bitacora):
        mock_repo.obtener_empresa_obra.return_value = 1
        mock_repo.unidad_pertenece_a_obra.return_value = True
        mock_repo.crear.return_value = 100
        data = {"id_obra": 5, "id_unidad": 3, "titulo": "T", "descripcion": "D", "prioridad": "MEDIA"}

        result = svc.registrar(data, TOKEN_A)

        self.assertTrue(result["success"])
        mock_repo.crear.assert_called_once_with(5, 3, 10, "T", "D", "MEDIA", None)

    # 7. Unidad de otra obra
    def test_rechaza_unidad_de_otra_obra(self):
        data = {"id_obra": 5, "id_unidad": 3, "titulo": "T", "descripcion": "D", "prioridad": "MEDIA"}
        with mock.patch("app.services.incidencia_services.incidencia_repos.obtener_empresa_obra", return_value=1), \
             mock.patch("app.services.incidencia_services.incidencia_repos.unidad_pertenece_a_obra", return_value=False):
            with self.assertRaisesRegex(svc.IncidenciaError, "unidad"):
                svc.registrar(data, TOKEN_A)

    def test_rechaza_sin_id_obra(self):
        data = {"titulo": "T", "descripcion": "D", "prioridad": "MEDIA"}
        with self.assertRaisesRegex(svc.IncidenciaError, "proyecto"):
            svc.registrar(data, TOKEN_A)

    # El cliente no puede fijar el estado inicial: se ignora cualquier 'estado' recibido.
    @mock.patch("app.services.incidencia_services.bitacora_repos")
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_ignora_estado_inicial_enviado_por_cliente(self, mock_repo, mock_bitacora):
        mock_repo.obtener_empresa_obra.return_value = 1
        mock_repo.crear.return_value = 1
        data = {
            "id_obra": 5, "titulo": "T", "descripcion": "D", "prioridad": "MEDIA",
            "estado": "CERRADA",
        }
        svc.registrar(data, TOKEN_A)
        # crear() nunca recibe el estado del payload; siempre nace ABIERTA en el repo/BD.
        args, _ = mock_repo.crear.call_args
        self.assertNotIn("CERRADA", args)
        mock_repo.crear_seguimiento.assert_called_once_with(1, 10, None, "ABIERTA", "Incidencia registrada.")


# ─────────────────────────────────────────────────────────────────────────────
# HU71 - Asignar responsable
# ─────────────────────────────────────────────────────────────────────────────
class AsignarResponsableTests(unittest.TestCase):

    # 8. Asignar responsable válido / 10. ABIERTA -> ASIGNADA
    @mock.patch("app.services.incidencia_services.bitacora_repos")
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_asignar_responsable_valido_mueve_a_asignada(self, mock_repo, mock_bitacora):
        mock_repo.obtener_estado_actual.return_value = ("ABIERTA", None)
        mock_repo.obtener_empresa_incidencia.return_value = 1
        mock_repo.usuario_pertenece_a_empresa.return_value = True
        mock_repo.obtener_detalle.return_value = {"id_obra": 8}
        mock_repo.obtener_usuarios_asignables.return_value = [{"nro_usuario": 55}]
        mock_repo.asignar_responsable.return_value = True

        result = svc.asignar_responsable(1, {"id_responsable": 55}, TOKEN_A)

        self.assertTrue(result["success"])
        self.assertEqual(result["estado"], "ASIGNADA")
        mock_repo.asignar_responsable.assert_called_once_with(1, 1, 55, "ASIGNADA")
        mock_repo.crear_seguimiento.assert_called_once_with(1, 10, "ABIERTA", "ASIGNADA", "Responsable 55 asignado.")

    # 9. Responsable de otro tenant
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_rechaza_responsable_de_otro_tenant(self, mock_repo):
        mock_repo.obtener_estado_actual.return_value = ("ABIERTA", None)
        mock_repo.obtener_empresa_incidencia.return_value = 1
        mock_repo.usuario_pertenece_a_empresa.return_value = False

        with self.assertRaises(svc.IncidenciaError) as ctx:
            svc.asignar_responsable(1, {"id_responsable": 999}, TOKEN_A)
        self.assertEqual(ctx.exception.status_code, 404)
        mock_repo.asignar_responsable.assert_not_called()

    @mock.patch("app.services.incidencia_services.bitacora_repos")
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_reasignar_no_retrocede_el_estado(self, mock_repo, mock_bitacora):
        mock_repo.obtener_estado_actual.return_value = ("EN_PROCESO", 55)
        mock_repo.obtener_empresa_incidencia.return_value = 1
        mock_repo.usuario_pertenece_a_empresa.return_value = True
        mock_repo.obtener_detalle.return_value = {"id_obra": 8}
        mock_repo.obtener_usuarios_asignables.return_value = [{"nro_usuario": 77}]
        mock_repo.asignar_responsable.return_value = True

        result = svc.asignar_responsable(1, {"id_responsable": 77}, TOKEN_A)

        self.assertEqual(result["estado"], "EN_PROCESO")
        mock_repo.asignar_responsable.assert_called_once_with(1, 1, 77, "EN_PROCESO")

    def test_rechaza_asignar_sin_id_responsable(self):
        with self.assertRaisesRegex(svc.IncidenciaError, "id_responsable"):
            svc.asignar_responsable(1, {}, TOKEN_A)

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_rechaza_asignar_incidencia_cerrada(self, mock_repo):
        mock_repo.obtener_estado_actual.return_value = ("CERRADA", 55)
        with self.assertRaisesRegex(svc.IncidenciaError, "cerrada"):
            svc.asignar_responsable(1, {"id_responsable": 55}, TOKEN_A)


# ─────────────────────────────────────────────────────────────────────────────
# HU71 - Candidatos a responsable (selector del modal "Asignar responsable")
# ─────────────────────────────────────────────────────────────────────────────
class ObtenerResponsablesTests(unittest.TestCase):

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_lista_candidatos_de_la_empresa_real_de_la_incidencia(self, mock_repo):
        mock_repo.obtener_detalle.return_value = {"id_incidencia": 1, "id_obra": 8}
        mock_repo.obtener_empresa_incidencia.return_value = 1
        mock_repo.obtener_usuarios_asignables.return_value = [
            {"nro_usuario": 55, "nombre_usuario": "jperez", "nombre_completo": "Juan Perez", "nombre_rol": "JEFE DE OBRA"}
        ]

        result = svc.obtener_responsables(1, TOKEN_A)

        self.assertTrue(result["success"])
        self.assertEqual(len(result["data"]), 1)
        # Nunca se usa el id_empresa del token para el catálogo de candidatos:
        # siempre la empresa real derivada de incidencia -> obra -> empresa.
        mock_repo.obtener_usuarios_asignables.assert_called_once_with(1, 8)

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_incidencia_inexistente_o_de_otro_tenant_da_404(self, mock_repo):
        mock_repo.obtener_detalle.return_value = None
        with self.assertRaises(svc.IncidenciaError) as ctx:
            svc.obtener_responsables(1, TOKEN_A)
        self.assertEqual(ctx.exception.status_code, 404)
        mock_repo.obtener_usuarios_asignables.assert_not_called()

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_sin_candidatos_devuelve_lista_vacia_no_error(self, mock_repo):
        mock_repo.obtener_detalle.return_value = {"id_incidencia": 1, "id_obra": 8}
        mock_repo.obtener_empresa_incidencia.return_value = 1
        mock_repo.obtener_usuarios_asignables.return_value = []

        result = svc.obtener_responsables(1, TOKEN_A)

        self.assertTrue(result["success"])
        self.assertEqual(result["data"], [])

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_administrador_global_consulta_empresa_real_no_su_token(self, mock_repo):
        # El ADMINISTRADOR global no tiene id_empresa en el token (None), pero
        # el catálogo de candidatos igual se acota a la empresa real dueña de
        # la incidencia (nunca se devuelven usuarios de otros tenants).
        mock_repo.obtener_detalle.return_value = {"id_incidencia": 1, "id_obra": 8}
        mock_repo.obtener_empresa_incidencia.return_value = 3
        mock_repo.obtener_usuarios_asignables.return_value = []
        token_admin = {"nro_usuario": 1, "nombre_rol": "ADMINISTRADOR"}

        svc.obtener_responsables(1, token_admin)

        mock_repo.obtener_detalle.assert_called_once_with(1, None)
        mock_repo.obtener_usuarios_asignables.assert_called_once_with(3, 8)


# ─────────────────────────────────────────────────────────────────────────────
# HU72 / HU74 - Transiciones de estado
# ─────────────────────────────────────────────────────────────────────────────
class TransicionesEstadoTests(unittest.TestCase):

    # 11. Rechazar ABIERTA -> CERRADA
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_rechaza_salto_abierta_a_cerrada(self, mock_repo):
        mock_repo.obtener_estado_actual.return_value = ("ABIERTA", None)
        with self.assertRaisesRegex(svc.IncidenciaError, "no permitida"):
            svc.cambiar_estado(1, {"estado": "CERRADA"}, TOKEN_A)
        mock_repo.cambiar_estado.assert_not_called()

    # 12. ASIGNADA -> EN_PROCESO (por el responsable asignado: TOKEN_A es el usuario 10)
    @mock.patch("app.services.incidencia_services.bitacora_repos")
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_asignada_a_en_proceso(self, mock_repo, mock_bitacora):
        mock_repo.obtener_estado_actual.return_value = ("ASIGNADA", 10)
        mock_repo.cambiar_estado.return_value = True
        result = svc.cambiar_estado(1, {"estado": "EN_PROCESO"}, TOKEN_A)
        self.assertEqual(result["estado_nuevo"], "EN_PROCESO")

    # 13. EN_PROCESO -> RESUELTA (por el responsable asignado)
    @mock.patch("app.services.incidencia_services.bitacora_repos")
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_en_proceso_a_resuelta(self, mock_repo, mock_bitacora):
        mock_repo.obtener_estado_actual.return_value = ("EN_PROCESO", 10)
        mock_repo.cambiar_estado.return_value = True
        result = svc.cambiar_estado(1, {"estado": "PENDIENTE_VALIDACION"}, TOKEN_A)
        self.assertEqual(result["estado_nuevo"], "PENDIENTE_VALIDACION")

    # 14. RESUELTA -> CERRADA (requiere permiso Cerrar_incidencias)
    @mock.patch("app.services.incidencia_services.bitacora_repos")
    @mock.patch("app.services.incidencia_services._tiene_permiso", return_value=True)
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_resuelta_a_cerrada(self, mock_repo, mock_permiso, mock_bitacora):
        mock_repo.obtener_estado_actual.return_value = ("RESUELTA", 55)
        mock_repo.cambiar_estado.return_value = True
        result = svc.cambiar_estado(1, {"estado": "CERRADA"}, TOKEN_A)
        self.assertEqual(result["estado_nuevo"], "CERRADA")

    def test_rechaza_asignada_sin_responsable(self):
        with mock.patch("app.services.incidencia_services.incidencia_repos") as mock_repo:
            mock_repo.obtener_estado_actual.return_value = ("ABIERTA", None)
            with self.assertRaisesRegex(svc.IncidenciaError, "responsable"):
                svc.cambiar_estado(1, {"estado": "ASIGNADA"}, TOKEN_A)

    # 17. Usuario sin permiso (verificado a nivel de negocio para el cierre)
    @mock.patch("app.services.incidencia_services._tiene_permiso", return_value=False)
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_rechaza_cerrar_sin_permiso_dedicado(self, mock_repo, mock_permiso):
        mock_repo.obtener_estado_actual.return_value = ("RESUELTA", 55)
        with self.assertRaises(svc.IncidenciaError) as ctx:
            svc.cambiar_estado(1, {"estado": "CERRADA"}, TOKEN_A)
        self.assertEqual(ctx.exception.status_code, 403)
        mock_repo.cambiar_estado.assert_not_called()

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_rechaza_estado_invalido(self, mock_repo):
        with self.assertRaisesRegex(svc.IncidenciaError, "Estado inválido"):
            svc.cambiar_estado(1, {"estado": "NO_EXISTE"}, TOKEN_A)
        mock_repo.obtener_estado_actual.assert_not_called()

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_incidencia_inexistente_en_cambio_estado(self, mock_repo):
        mock_repo.obtener_estado_actual.return_value = (None, None)
        with self.assertRaises(svc.IncidenciaError) as ctx:
            svc.cambiar_estado(1, {"estado": "ASIGNADA"}, TOKEN_A)
        self.assertEqual(ctx.exception.status_code, 404)


    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_rechaza_todos_los_saltos_de_estado(self, mock_repo):
        saltos = [
            ("ABIERTA", "RESUELTA"), ("ABIERTA", "CERRADA"), ("ABIERTA", "EN_PROCESO"),
            ("ASIGNADA", "RESUELTA"), ("ASIGNADA", "CERRADA"),
            ("EN_PROCESO", "CERRADA"), ("EN_PROCESO", "ASIGNADA"),
            ("RESUELTA", "EN_PROCESO"), ("CERRADA", "ABIERTA"),
        ]
        for actual, nuevo in saltos:
            with self.subTest(f"{actual} -> {nuevo}"):
                mock_repo.obtener_estado_actual.return_value = (actual, 10)
                with self.assertRaisesRegex(svc.IncidenciaError, "no permitida"):
                    svc.cambiar_estado(1, {"estado": nuevo}, TOKEN_A)
        mock_repo.cambiar_estado.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# Responsable: solo él inicia / finaliza la atención. Fechas en servidor.
# ─────────────────────────────────────────────────────────────────────────────
class ResponsableYTiemposTests(unittest.TestCase):

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_no_responsable_no_puede_iniciar(self, mock_repo):
        mock_repo.obtener_estado_actual.return_value = ("ASIGNADA", 55)
        with self.assertRaises(svc.IncidenciaError) as ctx:
            svc.cambiar_estado(1, {"estado": "EN_PROCESO"}, TOKEN_A)
        self.assertEqual(ctx.exception.status_code, 403)
        mock_repo.cambiar_estado.assert_not_called()
        mock_repo.crear_seguimiento.assert_not_called()

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_no_responsable_no_puede_resolver(self, mock_repo):
        mock_repo.obtener_estado_actual.return_value = ("EN_PROCESO", 55)
        with self.assertRaises(svc.IncidenciaError) as ctx:
            svc.cambiar_estado(1, {"estado": "PENDIENTE_VALIDACION"}, TOKEN_A)
        self.assertEqual(ctx.exception.status_code, 403)
        mock_repo.cambiar_estado.assert_not_called()

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_ni_el_admin_de_plataforma_inicia_si_no_es_responsable(self, mock_repo):
        mock_repo.obtener_estado_actual.return_value = ("ASIGNADA", 55)
        token_admin = {"nro_usuario": 1, "nombre_rol": "ADMINISTRADOR"}
        with self.assertRaises(svc.IncidenciaError) as ctx:
            svc.cambiar_estado(1, {"estado": "EN_PROCESO"}, token_admin)
        self.assertEqual(ctx.exception.status_code, 403)

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_mismo_tenant_otro_usuario_no_puede_resolver(self, mock_repo):
        # Mismo id de usuario pero en formato string en el token: se compara por valor.
        mock_repo.obtener_estado_actual.return_value = ("EN_PROCESO", 10)
        mock_repo.cambiar_estado.return_value = True
        with mock.patch("app.services.incidencia_services.bitacora_repos"):
            svc.cambiar_estado(1, {"estado": "PENDIENTE_VALIDACION"}, {**TOKEN_A, "nro_usuario": "10"})
        token_otro = {**TOKEN_A, "nro_usuario": 11}
        with self.assertRaises(svc.IncidenciaError) as ctx:
            svc.cambiar_estado(1, {"estado": "PENDIENTE_VALIDACION"}, token_otro)
        self.assertEqual(ctx.exception.status_code, 403)

    @mock.patch("app.services.incidencia_services.bitacora_repos")
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_inicio_pasa_responsable_y_estado_esperado_al_repo(self, mock_repo, mock_bitacora):
        mock_repo.obtener_estado_actual.return_value = ("ASIGNADA", 10)
        mock_repo.cambiar_estado.return_value = True
        # Una fecha enviada por el cliente se ignora: el repo no la recibe.
        svc.cambiar_estado(1, {"estado": "EN_PROCESO", "fecha_inicio_atencion": "2000-01-01"}, TOKEN_A)
        mock_repo.cambiar_estado.assert_called_once_with(1, 1, "ASIGNADA", "EN_PROCESO", 10)
        mock_repo.crear_seguimiento.assert_called_once_with(
            1, 10, "ASIGNADA", "EN_PROCESO", "Inicio de atención de la incidencia."
        )

    @mock.patch("app.services.incidencia_services.bitacora_repos")
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_fin_genera_seguimiento_con_observacion_del_responsable(self, mock_repo, mock_bitacora):
        mock_repo.obtener_estado_actual.return_value = ("EN_PROCESO", 10)
        mock_repo.cambiar_estado.return_value = True
        svc.cambiar_estado(1, {"estado": "PENDIENTE_VALIDACION", "observacion": "Se selló la tubería"}, TOKEN_A)
        mock_repo.cambiar_estado.assert_called_once_with(1, 1, "EN_PROCESO", "PENDIENTE_VALIDACION", 10)
        mock_repo.crear_seguimiento.assert_called_once_with(
            1, 10, "EN_PROCESO", "PENDIENTE_VALIDACION", "Se selló la tubería"
        )

    @mock.patch("app.services.incidencia_services.bitacora_repos")
    @mock.patch("app.services.incidencia_services._tiene_permiso", return_value=True)
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_cierre_no_exige_ser_responsable(self, mock_repo, mock_permiso, mock_bitacora):
        mock_repo.obtener_estado_actual.return_value = ("RESUELTA", 55)
        mock_repo.cambiar_estado.return_value = True
        svc.cambiar_estado(1, {"estado": "CERRADA"}, TOKEN_A)
        mock_repo.cambiar_estado.assert_called_once_with(1, 1, "RESUELTA", "CERRADA", None)

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_iniciar_dos_veces_concurrente_da_409(self, mock_repo):
        # Ambas peticiones leen ASIGNADA, pero el UPDATE condicional solo
        # prospera una vez; la segunda recibe False del repo -> 409.
        mock_repo.obtener_estado_actual.return_value = ("ASIGNADA", 10)
        mock_repo.cambiar_estado.return_value = False
        with self.assertRaises(svc.IncidenciaError) as ctx:
            svc.cambiar_estado(1, {"estado": "EN_PROCESO"}, TOKEN_A)
        self.assertEqual(ctx.exception.status_code, 409)
        mock_repo.crear_seguimiento.assert_not_called()

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_iniciar_ya_en_proceso_es_rechazado(self, mock_repo):
        mock_repo.obtener_estado_actual.return_value = ("EN_PROCESO", 10)
        with self.assertRaisesRegex(svc.IncidenciaError, "ya se encuentra"):
            svc.cambiar_estado(1, {"estado": "EN_PROCESO"}, TOKEN_A)

    def test_sql_de_cambio_de_estado_genera_fechas_en_servidor_y_condiciona(self):
        from app.repos import incidencia_repos
        captured = {}

        class FakeConn:
            def commit(self): pass
            def rollback(self): pass

        class FakePostgreSQL:
            conn = FakeConn()
            def create_connection(self): pass
            def close_connection(self): pass
            def execute_query(self, query, params=None, fetchall=False, fetchone=False, commit=False):
                captured["query"] = query
                captured["params"] = params
                return (1,)

        with mock.patch("app.repos.incidencia_repos.PostgreSQL", FakePostgreSQL):
            self.assertTrue(incidencia_repos.cambiar_estado(1, 2, "ASIGNADA", "EN_PROCESO", 10))

        q = captured["query"]
        self.assertIn("CURRENT_TIMESTAMP", q)
        self.assertIn("i.estado = %s", q)
        self.assertIn("i.id_responsable = %s", q)
        self.assertIn("o.id_empresa", q)
        self.assertIn("fecha_inicio_atencion IS NULL", q)
        self.assertIn("ASIGNADA", captured["params"])
        self.assertIn(10, captured["params"])


# ─────────────────────────────────────────────────────────────────────────────
# Órdenes de trabajo afectadas (M:N)
# ─────────────────────────────────────────────────────────────────────────────
class OrdenesTrabajoTests(unittest.TestCase):

    DETALLE = {"id_incidencia": 1, "id_obra": 8, "estado": "ABIERTA"}

    @mock.patch("app.services.incidencia_services.bitacora_repos")
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_vincula_varias_ot_de_la_misma_obra(self, mock_repo, mock_bitacora):
        mock_repo.obtener_detalle.return_value = dict(self.DETALLE)
        mock_repo.obtener_empresa_incidencia.return_value = 1
        mock_repo.filtrar_ordenes_de_obra.return_value = {1, 4}
        mock_repo.reemplazar_ordenes_trabajo.return_value = ([1, 4], [])

        result = svc.actualizar_ordenes_trabajo(1, {"ordenes": [1, 4, 4]}, TOKEN_A)

        self.assertTrue(result["success"])
        self.assertEqual(result["agregadas"], [1, 4])
        # Se valida contra la obra de la incidencia y la empresa REAL, sin duplicados.
        mock_repo.filtrar_ordenes_de_obra.assert_called_once_with([1, 4], 8, 1)
        mock_repo.reemplazar_ordenes_trabajo.assert_called_once_with(1, [1, 4], 10)
        args, _ = mock_repo.crear_seguimiento.call_args
        self.assertIn("OT-001", args[4])
        self.assertIn("OT-004", args[4])

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_rechaza_ot_de_otra_obra(self, mock_repo):
        mock_repo.obtener_detalle.return_value = dict(self.DETALLE)
        mock_repo.obtener_empresa_incidencia.return_value = 1
        mock_repo.filtrar_ordenes_de_obra.return_value = {1}  # la 7 es de otra obra

        with self.assertRaisesRegex(svc.IncidenciaError, "OT-007"):
            svc.actualizar_ordenes_trabajo(1, {"ordenes": [1, 7]}, TOKEN_A)
        mock_repo.reemplazar_ordenes_trabajo.assert_not_called()

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_rechaza_ot_de_otro_tenant(self, mock_repo):
        mock_repo.obtener_detalle.return_value = dict(self.DETALLE)
        mock_repo.obtener_empresa_incidencia.return_value = 1
        mock_repo.filtrar_ordenes_de_obra.return_value = set()  # OT de la empresa B

        with self.assertRaises(svc.IncidenciaError) as ctx:
            svc.actualizar_ordenes_trabajo(1, {"ordenes": [5]}, TOKEN_A)
        self.assertEqual(ctx.exception.status_code, 400)
        mock_repo.reemplazar_ordenes_trabajo.assert_not_called()

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_incidencia_de_otro_tenant_da_404(self, mock_repo):
        mock_repo.obtener_detalle.return_value = None
        with self.assertRaises(svc.IncidenciaError) as ctx:
            svc.actualizar_ordenes_trabajo(1, {"ordenes": [1]}, TOKEN_B)
        self.assertEqual(ctx.exception.status_code, 404)
        mock_repo.obtener_detalle.assert_called_once_with(1, 2)
        mock_repo.filtrar_ordenes_de_obra.assert_not_called()

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_ignora_id_empresa_e_id_obra_del_cliente(self, mock_repo):
        mock_repo.obtener_detalle.return_value = dict(self.DETALLE)
        mock_repo.obtener_empresa_incidencia.return_value = 1
        mock_repo.filtrar_ordenes_de_obra.return_value = set()
        with self.assertRaises(svc.IncidenciaError):
            svc.actualizar_ordenes_trabajo(1, {"ordenes": [9], "id_empresa": 2, "id_obra": 99}, TOKEN_A)
        mock_repo.filtrar_ordenes_de_obra.assert_called_once_with([9], 8, 1)

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_rechaza_incidencia_cerrada(self, mock_repo):
        mock_repo.obtener_detalle.return_value = {**self.DETALLE, "estado": "CERRADA"}
        with self.assertRaisesRegex(svc.IncidenciaError, "cerrada"):
            svc.actualizar_ordenes_trabajo(1, {"ordenes": [1]}, TOKEN_A)

    def test_valida_formato_de_ordenes(self):
        for payload in ({}, {"ordenes": "1,2"}, {"ordenes": [0]}, {"ordenes": ["x"]},
                        {"ordenes": [True]}, {"ordenes": list(range(1, 102))}):
            with self.subTest(payload=str(payload)[:40]):
                with self.assertRaises(svc.IncidenciaError):
                    svc.actualizar_ordenes_trabajo(1, payload, TOKEN_A)

    @mock.patch("app.services.incidencia_services.bitacora_repos")
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_lista_vacia_quita_todas_y_sin_cambios_no_genera_seguimiento(self, mock_repo, mock_bitacora):
        mock_repo.obtener_detalle.return_value = dict(self.DETALLE)
        mock_repo.obtener_empresa_incidencia.return_value = 1
        mock_repo.filtrar_ordenes_de_obra.return_value = set()
        mock_repo.reemplazar_ordenes_trabajo.return_value = ([], [])

        svc.actualizar_ordenes_trabajo(1, {"ordenes": []}, TOKEN_A)

        mock_repo.reemplazar_ordenes_trabajo.assert_called_once_with(1, [], 10)
        mock_repo.crear_seguimiento.assert_not_called()

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_disponibles_solo_de_la_obra_y_empresa_real(self, mock_repo):
        mock_repo.obtener_detalle.return_value = dict(self.DETALLE)
        mock_repo.obtener_empresa_incidencia.return_value = 1
        mock_repo.listar_ordenes_trabajo_obra.return_value = []
        svc.listar_ordenes_trabajo_disponibles(1, TOKEN_A)
        mock_repo.listar_ordenes_trabajo_obra.assert_called_once_with(8, 1, 1)

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_detalle_incluye_ordenes_trabajo(self, mock_repo):
        mock_repo.obtener_detalle.return_value = dict(self.DETALLE)
        mock_repo.listar_ordenes_trabajo_incidencia.return_value = [{"orden_nro": 1}, {"orden_nro": 4}]
        result = svc.obtener(1, TOKEN_A)
        self.assertEqual(len(result["data"]["ordenes_trabajo"]), 2)

    def test_sql_filtrar_ordenes_exige_misma_obra_y_empresa(self):
        from app.repos import incidencia_repos
        captured = {}

        class FakePostgreSQL:
            def create_connection(self): pass
            def close_connection(self): pass
            def execute_query(self, query, params=None, fetchall=False, fetchone=False, commit=False):
                captured["query"] = query
                captured["params"] = params
                return [(1,)]

        with mock.patch("app.repos.incidencia_repos.PostgreSQL", FakePostgreSQL):
            self.assertEqual(incidencia_repos.filtrar_ordenes_de_obra([1, 7], 8, 1), {1})
        self.assertIn("ot.id_obra = %s", captured["query"])
        self.assertIn("o.id_empresa = %s", captured["query"])
        self.assertEqual(captured["params"], ([1, 7], 8, 1))


# ─────────────────────────────────────────────────────────────────────────────
# Ubicación (nuevo campo opcional)
# ─────────────────────────────────────────────────────────────────────────────
class UbicacionTests(unittest.TestCase):

    @mock.patch("app.services.incidencia_services.bitacora_repos")
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_registrar_con_ubicacion(self, mock_repo, mock_bitacora):
        mock_repo.obtener_empresa_obra.return_value = 1
        mock_repo.crear.return_value = 1
        data = {"id_obra": 5, "titulo": "T", "descripcion": "D", "prioridad": "ALTA",
                "ubicacion": "  Bloque 1, piso 2  "}
        svc.registrar(data, TOKEN_A)
        mock_repo.crear.assert_called_once_with(5, None, 10, "T", "D", "ALTA", "Bloque 1, piso 2")

    @mock.patch("app.services.incidencia_services.bitacora_repos")
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_editar_sin_campo_ubicacion_la_conserva(self, mock_repo, mock_bitacora):
        mock_repo.obtener_estado_actual.return_value = ("ABIERTA", None)
        mock_repo.actualizar.return_value = True
        svc.actualizar(1, {"titulo": "T", "descripcion": "D", "prioridad": "BAJA"}, TOKEN_A)
        mock_repo.actualizar.assert_called_once_with(1, 1, "T", "D", "BAJA", False, None)

    @mock.patch("app.services.incidencia_services.bitacora_repos")
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_editar_con_ubicacion(self, mock_repo, mock_bitacora):
        mock_repo.obtener_estado_actual.return_value = ("ABIERTA", None)
        mock_repo.actualizar.return_value = True
        svc.actualizar(1, {"titulo": "T", "descripcion": "D", "prioridad": "BAJA", "ubicacion": "Eje B"}, TOKEN_A)
        mock_repo.actualizar.assert_called_once_with(1, 1, "T", "D", "BAJA", True, "Eje B")

    def test_rechaza_ubicacion_muy_larga(self):
        data = {"id_obra": 5, "titulo": "T", "descripcion": "D", "prioridad": "ALTA", "ubicacion": "x" * 256}
        with mock.patch("app.services.incidencia_services.incidencia_repos.obtener_empresa_obra", return_value=1):
            with self.assertRaisesRegex(svc.IncidenciaError, "ubicación"):
                svc.registrar(data, TOKEN_A)


# ─────────────────────────────────────────────────────────────────────────────
# Seguimiento
# ─────────────────────────────────────────────────────────────────────────────
class SeguimientoTests(unittest.TestCase):

    # 15. Registrar seguimiento
    @mock.patch("app.services.incidencia_services.bitacora_repos")
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_registrar_seguimiento(self, mock_repo, mock_bitacora):
        mock_repo.obtener_estado_actual.return_value = ("EN_PROCESO", 55)
        mock_repo.crear_seguimiento.return_value = 7

        result = svc.registrar_seguimiento(1, {"observacion": "Avance del 50%"}, TOKEN_A)

        self.assertTrue(result["success"])
        self.assertEqual(result["id_seguimiento"], 7)
        mock_repo.crear_seguimiento.assert_called_once_with(1, 10, "EN_PROCESO", "EN_PROCESO", "Avance del 50%")

    def test_rechaza_seguimiento_sin_observacion(self):
        with mock.patch("app.services.incidencia_services.incidencia_repos") as mock_repo:
            mock_repo.obtener_estado_actual.return_value = ("EN_PROCESO", 55)
            with self.assertRaisesRegex(svc.IncidenciaError, "observación"):
                svc.registrar_seguimiento(1, {"observacion": "  "}, TOKEN_A)

    # 16. Consultar seguimiento
    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_consultar_seguimiento(self, mock_repo):
        mock_repo.listar_seguimiento.return_value = [{"id_seguimiento": 1, "estado_nuevo": "ABIERTA"}]
        result = svc.listar_seguimiento(1, TOKEN_A)
        self.assertTrue(result["success"])
        self.assertEqual(len(result["data"]), 1)

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_consultar_seguimiento_incidencia_inexistente(self, mock_repo):
        mock_repo.listar_seguimiento.return_value = None
        with self.assertRaises(svc.IncidenciaError) as ctx:
            svc.listar_seguimiento(1, TOKEN_A)
        self.assertEqual(ctx.exception.status_code, 404)


# ─────────────────────────────────────────────────────────────────────────────
# Multi-tenant (18. Tenant A no puede ver incidencias de Tenant B)
# ─────────────────────────────────────────────────────────────────────────────
class TenantIsolationTests(unittest.TestCase):

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_no_puede_ver_incidencia_de_otro_tenant(self, mock_repo):
        # El repo siempre filtra por la empresa real del token; si la incidencia
        # pertenece a otra empresa, la consulta no la encuentra (no existe "para él").
        mock_repo.obtener_detalle.return_value = None
        with self.assertRaises(svc.IncidenciaError) as ctx:
            svc.obtener(1, TOKEN_B)
        self.assertEqual(ctx.exception.status_code, 404)
        mock_repo.obtener_detalle.assert_called_once_with(1, 2)

    def test_token_sin_empresa_lanza_403(self):
        token = {"nro_usuario": 1, "nombre_rol": "JEFE DE OBRA"}
        with self.assertRaises(svc.IncidenciaError) as ctx:
            svc.obtener(1, token)
        self.assertEqual(ctx.exception.status_code, 403)

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_administrador_global_no_filtra_por_empresa(self, mock_repo):
        mock_repo.obtener_detalle.return_value = {"id_incidencia": 1, "id_obra": 8}
        token_admin = {"nro_usuario": 1, "nombre_rol": "ADMINISTRADOR"}
        svc.obtener(1, token_admin)
        mock_repo.obtener_detalle.assert_called_once_with(1, None)


# ─────────────────────────────────────────────────────────────────────────────
# HU73 - Evidencias fotográficas (validaciones que no requieren disco)
# ─────────────────────────────────────────────────────────────────────────────
class EvidenciaTests(unittest.TestCase):

    def test_rechaza_archivo_vacio(self):
        with self.assertRaisesRegex(svc.IncidenciaError, "vacío"):
            svc.adjuntar_evidencia(1, TOKEN_A, "foto.jpg", "image/jpeg", b"")

    def test_rechaza_mime_no_permitido(self):
        with self.assertRaisesRegex(svc.IncidenciaError, "fotografías"):
            svc.adjuntar_evidencia(1, TOKEN_A, "doc.pdf", "application/pdf", b"contenido")

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_rechaza_evidencia_en_incidencia_cerrada(self, mock_repo):
        mock_repo.obtener_estado_actual.return_value = ("CERRADA", 55)
        with self.assertRaisesRegex(svc.IncidenciaError, "cerrada"):
            svc.adjuntar_evidencia(1, TOKEN_A, "foto.jpg", "image/jpeg", b"contenido")

    @mock.patch("app.services.incidencia_services.incidencia_repos")
    def test_rechaza_evidencia_incidencia_inexistente(self, mock_repo):
        mock_repo.obtener_estado_actual.return_value = (None, None)
        with self.assertRaises(svc.IncidenciaError) as ctx:
            svc.adjuntar_evidencia(1, TOKEN_A, "foto.jpg", "image/jpeg", b"contenido")
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
