from decimal import Decimal
import unittest

from app.services import material_services


class MaterialValidationTests(unittest.TestCase):
    def test_rechaza_numero_negativo(self):
        with self.assertRaisesRegex(material_services.MaterialError, "no puede ser negativo"):
            material_services._numero(-1, "La cantidad inicial")

    def test_rechaza_cantidad_actual_en_edicion(self):
        with self.assertRaisesRegex(material_services.MaterialError, "cantidad_actual"):
            material_services._validar({"cantidad_actual": 10}, creando=False)

    def test_rechaza_estado_invalido_antes_de_consultar_bd(self):
        with self.assertRaisesRegex(material_services.MaterialError, "Estado inválido"):
            material_services.listar({"id_empresa": 1}, estado="BORRADO")

    def test_normaliza_numero_no_negativo(self):
        self.assertEqual(material_services._numero("10.500", "Stock"), Decimal("10.500"))


if __name__ == "__main__":
    unittest.main()
