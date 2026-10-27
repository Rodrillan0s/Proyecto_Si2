"""
Pruebas unitarias para CU23 – Gestionar consultas técnicas de obra (RFI)
HU138, HU139, HU140
Validación de datos, reglas de negocio, aislamiento multitenant y transiciones de estado.
"""
import unittest
from unittest.mock import patch, MagicMock

from app.services import consulta_tecnica_services as service
from app.services.planes_catalog import modulo_ruta
from app.services.suscripcion_policy import proteger_http


class ConsultaTecnicaValidationTests(unittest.TestCase):

    def test_token_empresa_segun_rol(self):
        admin_global = {"nombre_rol": "ADMINISTRADOR", "id_empresa": 1, "nro_usuario": 1}
        self.assertIsNone(service._empresa_id(admin_global))

        admin_empresa = {"nombre_rol": "ADMINISTRADOR_EMPRESA", "id_empresa": 3, "nro_usuario": 4}
        self.assertEqual(service._empresa_id(admin_empresa), 3)

        jefe_obra = {"nombre_rol": "JEFE DE OBRA", "id_empresa": 4, "nro_usuario": 5}
        self.assertEqual(service._empresa_id(jefe_obra), 4)

    def test_token_sin_empresa_falla_si_no_es_admin(self):
        token_invalido = {"nombre_rol": "JEFE DE OBRA", "id_empresa": None, "nro_usuario": 5}
        with self.assertRaises(service.ConsultaTecnicaError) as ctx:
            service._empresa_id(token_invalido)
        self.assertEqual(ctx.exception.status_code, 403)

    @patch("app.repos.consulta_tecnica_repos.obtener_obra")
    def test_obra_no_encontrada_o_ajena_al_tenant(self, mock_obtener_obra):
        mock_obtener_obra.return_value = None
        token = {"nombre_rol": "ADMINISTRADOR_EMPRESA", "id_empresa": 3, "nro_usuario": 4}

        with self.assertRaises(service.ConsultaTecnicaError) as ctx:
            service.autorizar_acceso_obra(999, token)
        self.assertEqual(ctx.exception.status_code, 404)

    @patch("app.repos.consulta_tecnica_repos.obtener_obra")
    def test_validacion_campos_asunto_y_descripcion(self, mock_obtener_obra):
        mock_obtener_obra.return_value = {"id_obra": 1, "id_empresa": 1, "codigo": "SCZ-01"}
        token = {"nombre_rol": "ADMINISTRADOR", "id_empresa": 1, "nro_usuario": 1}

        # Asunto vacío o muy corto
        with self.assertRaises(service.ConsultaTecnicaError) as ctx:
            service.registrar_consulta(1, {"asunto": "a", "descripcion": "Descripción válida con más de cinco caracteres"}, token)
        self.assertEqual(ctx.exception.status_code, 422)

        # Descripción vacía o muy corta
        with self.assertRaises(service.ConsultaTecnicaError) as ctx:
            service.registrar_consulta(1, {"asunto": "Asunto válido", "descripcion": "abc"}, token)
        self.assertEqual(ctx.exception.status_code, 422)

    @patch("app.repos.consulta_tecnica_repos.obtener_obra")
    @patch("app.repos.consulta_tecnica_repos.generar_siguiente_codigo")
    @patch("app.repos.consulta_tecnica_repos.crear_consulta")
    def test_registro_exitoso_consulta(self, mock_crear, mock_codigo, mock_obra):
        mock_obra.return_value = {"id_obra": 8, "id_empresa": 1, "codigo": "GT-01"}
        mock_codigo.return_value = "CT-GT-01-001"
        mock_crear.return_value = 101

        token = {"nombre_rol": "JEFE DE OBRA", "id_empresa": 1, "nro_usuario": 6}
        datos = {
            "asunto": "Discrepancia en diámetro de armadura viga V-12",
            "descripcion": "El plano estructural indica 4 varillas de 16mm, pero la memoria de cálculo refiere 4 varillas de 20mm.",
            "referencia_tecnica": "Plano Estructural E-04",
            "asignado_a": 11
        }
        resp = service.registrar_consulta(8, datos, token)
        self.assertTrue(resp["success"])
        self.assertEqual(resp["id_consulta_tecnica"], 101)
        self.assertEqual(resp["codigo"], "CT-GT-01-001")


class ConsultaTecnicaTransicionesTests(unittest.TestCase):

    @patch("app.repos.consulta_tecnica_repos.obtener_por_id")
    def test_impedir_asignacion_a_consulta_cerrada(self, mock_obtener):
        mock_obtener.return_value = {
            "id_consulta_tecnica": 10, "id_empresa": 1, "estado": "CERRADA"
        }
        token = {"nombre_rol": "JEFE DE OBRA", "id_empresa": 1, "nro_usuario": 6}

        with self.assertRaises(service.ConsultaTecnicaError) as ctx:
            service.asignar_responsable(10, {"asignado_a": 4}, token)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("CERRADA", str(ctx.exception))

    @patch("app.repos.consulta_tecnica_repos.obtener_por_id")
    def test_impedir_respuesta_a_consulta_cerrada(self, mock_obtener):
        mock_obtener.return_value = {
            "id_consulta_tecnica": 10, "id_empresa": 1, "estado": "CERRADA"
        }
        token = {"nombre_rol": "SUPERVISOR_OBRA", "id_empresa": 1, "nro_usuario": 6}

        with self.assertRaises(service.ConsultaTecnicaError) as ctx:
            service.registrar_respuesta(10, {"contenido": "Respuesta tardía"}, token)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("CERRADA", str(ctx.exception))

    @patch("app.repos.consulta_tecnica_repos.obtener_por_id")
    @patch("app.repos.consulta_tecnica_repos.cerrar_consulta")
    def test_cierre_exitoso_con_motivo(self, mock_cerrar, mock_obtener):
        mock_obtener.return_value = {
            "id_consulta_tecnica": 15, "id_empresa": 3, "estado": "RESPONDIDA"
        }
        mock_cerrar.return_value = True
        token = {"nombre_rol": "ADMINISTRADOR_EMPRESA", "id_empresa": 3, "nro_usuario": 4}

        res = service.cambiar_estado(15, {"estado": "CERRADA", "motivo": "Aclaración aceptada por el proyectista"}, token)
        self.assertTrue(res["success"])
        self.assertIn("cerrada", res["message"])

    @patch("app.repos.consulta_tecnica_repos.obtener_por_id")
    @patch("app.repos.consulta_tecnica_repos.reabrir_consulta")
    def test_reapertura_exitosa_de_cerrada_a_abierta(self, mock_reabrir, mock_obtener):
        mock_obtener.return_value = {
            "id_consulta_tecnica": 15, "id_empresa": 3, "estado": "CERRADA"
        }
        mock_reabrir.return_value = True
        token = {"nombre_rol": "JEFE DE OBRA", "id_empresa": 3, "nro_usuario": 4}

        res = service.cambiar_estado(15, {"estado": "ABIERTA", "motivo": "Nueva contradicción en plano de detalle complementario"}, token)
        self.assertTrue(res["success"])
        self.assertIn("reabierta", res["message"])


class ConsultaSaaSPolicyTests(unittest.TestCase):

    def test_modulo_ruta_mapea_consultas_tecnicas_a_obras(self):
        # Subruta bajo proyectos
        self.assertEqual(modulo_ruta("/api/proyectos/12/consultas-tecnicas"), "obras")
        # Ruta directa
        self.assertEqual(modulo_ruta("/api/consultas-tecnicas/5/respuestas"), "obras")
        self.assertEqual(modulo_ruta("/api/consultas-tecnicas/5/asignacion"), "obras")


if __name__ == "__main__":
    unittest.main()
