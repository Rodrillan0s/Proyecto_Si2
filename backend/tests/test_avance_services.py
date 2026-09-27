import unittest
from datetime import date
from unittest.mock import patch

from app.services import avance_services


class AvanceValidationTests(unittest.TestCase):
    def test_valida_porcentaje_correcto(self):
        self.assertEqual(avance_services._validar_porcentaje(0), 0.0)
        self.assertEqual(avance_services._validar_porcentaje(50.5), 50.5)
        self.assertEqual(avance_services._validar_porcentaje(100), 100.0)
        self.assertEqual(avance_services._validar_porcentaje("75.25"), 75.25)

    def test_rechaza_porcentaje_invalido(self):
        with self.assertRaisesRegex(ValueError, "obligatorio"):
            avance_services._validar_porcentaje(None)

        with self.assertRaisesRegex(ValueError, "número válido"):
            avance_services._validar_porcentaje("abc")

        with self.assertRaisesRegex(ValueError, "entre 0 y 100"):
            avance_services._validar_porcentaje(-5)

        with self.assertRaisesRegex(ValueError, "entre 0 y 100"):
            avance_services._validar_porcentaje(105)

    def test_valida_fecha_registro(self):
        # Si es None, retorna fecha actual
        hoy = date.today()
        self.assertEqual(avance_services._validar_fecha(None), hoy)
        self.assertEqual(avance_services._validar_fecha(""), hoy)

        # Si viene en formato YYYY-MM-DD
        d = avance_services._validar_fecha("2026-05-15")
        self.assertEqual(d, date(2026, 5, 15))

        # Si ya es date
        self.assertEqual(avance_services._validar_fecha(hoy), hoy)

        # Formato inválido
        with self.assertRaisesRegex(ValueError, "Formato de fecha incorrecto"):
            avance_services._validar_fecha("15-05-2026")

    def test_id_empresa_segun_rol(self):
        admin_token = {"nombre_rol": "ADMINISTRADOR", "id_empresa": 99}
        self.assertIsNone(avance_services._id_empresa(admin_token))

        supervisor_token = {"nombre_rol": "ADMINISTRADOR_EMPRESA", "id_empresa": 5}
        self.assertEqual(avance_services._id_empresa(supervisor_token), 5)

        jefe_token = {"nombre_rol": "JEFE DE OBRA", "id_empresa": 5}
        self.assertEqual(avance_services._id_empresa(jefe_token), 5)

    def test_registrar_avance_requiere_unidad(self):
        token = {"nro_usuario": 1, "nombre_rol": "ADMINISTRADOR"}
        with self.assertRaisesRegex(ValueError, "unidad de construcción es obligatoria"):
            avance_services.registrar_avance(1, {}, token)

        with self.assertRaisesRegex(ValueError, "identificador de la unidad.*inválido"):
            avance_services.registrar_avance(1, {"id_unidad": -1, "porcentaje_avance": 50}, token)

    @patch("app.repos.bitacora_repos.registrar_bitacora")
    @patch("app.repos.avance_repos.registrar_avance_fn")
    def test_registrar_avance_exitoso(self, mock_repo, mock_bitacora):
        mock_repo.return_value = {"success": True, "id_avance": 10}
        token = {"nro_usuario": 2, "nombre_rol": "JEFE DE OBRA", "id_empresa": 1}
        payload = {
            "id_unidad": 3,
            "porcentaje_avance": 45.0,
            "fecha_registro": "2026-06-01",
            "observacion": "Cimentación concluida",
        }

        res = avance_services.registrar_avance(1, payload, token, "127.0.0.1")
        self.assertTrue(res["success"])
        self.assertEqual(res["id_avance"], 10)
        mock_repo.assert_called_once_with(
            id_obra=1,
            id_unidad=3,
            id_empresa=1,
            porcentaje=45.0,
            fecha_registro=date(2026, 6, 1),
            observacion="Cimentación concluida",
            id_usuario=2,
        )
        mock_bitacora.assert_called_once()


if __name__ == "__main__":
    unittest.main()
