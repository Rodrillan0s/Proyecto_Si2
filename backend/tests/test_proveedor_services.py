"""
Pruebas unitarias para CU15 – Gestión de Proveedores.
Validan la lógica de negocio en proveedor_services sin requerir conexión a BD.
Ejecutar: python -m pytest tests/test_proveedor_services.py -v
"""

import unittest
from app.services import proveedor_services


class ProveedorValidacionTests(unittest.TestCase):

    # ── HU-70 Registrar: validaciones de campos obligatorios ──────────────
    def test_rechaza_nombre_vacio(self):
        """HU-70: El nombre es obligatorio."""
        with self.assertRaisesRegex(proveedor_services.ProveedorError, "nombre"):
            proveedor_services._validar({"nombre": "", "nit": "123-4"}, creando=True)

    def test_rechaza_nit_vacio(self):
        """HU-70: El NIT es obligatorio."""
        with self.assertRaisesRegex(proveedor_services.ProveedorError, "NIT"):
            proveedor_services._validar({"nombre": "Proveedor S.A.", "nit": "   "}, creando=True)

    def test_rechaza_email_con_formato_invalido(self):
        """HU-70: El correo debe tener formato válido cuando se proporciona."""
        with self.assertRaisesRegex(proveedor_services.ProveedorError, "correo electrónico"):
            proveedor_services._validar({
                "nombre": "Proveedor S.A.", "nit": "123-4", "email": "no-es-un-email"
            }, creando=True)

    def test_acepta_email_valido(self):
        """HU-70: Un email con formato correcto debe ser aceptado."""
        result = proveedor_services._validar({
            "nombre": "Proveedor S.A.", "nit": "123-4", "email": "info@proveedor.com"
        }, creando=True)
        self.assertEqual(result["email"], "info@proveedor.com")

    def test_acepta_email_nulo(self):
        """HU-70: El email es opcional; None debe ser aceptado."""
        result = proveedor_services._validar({
            "nombre": "Proveedor S.A.", "nit": "123-4", "email": None
        }, creando=True)
        self.assertIsNone(result["email"])

    # ── HU-71 Modificar: campos inmutables ────────────────────────────────
    def test_rechaza_modificar_id_proveedor(self):
        """HU-71: No se permite modificar el id_proveedor."""
        with self.assertRaisesRegex(proveedor_services.ProveedorError, "id_proveedor"):
            proveedor_services._validar({
                "id_proveedor": 99, "nombre": "X", "nit": "1"
            }, creando=False)

    def test_rechaza_modificar_id_empresa(self):
        """HU-71: No se permite modificar el id_empresa."""
        with self.assertRaisesRegex(proveedor_services.ProveedorError, "id_empresa"):
            proveedor_services._validar({
                "id_empresa": 5, "nombre": "X", "nit": "1"
            }, creando=False)

    # ── HU-72 Consultar: validación de estado ─────────────────────────────
    def test_rechaza_estado_invalido(self):
        """HU-72: El estado debe ser ACTIVO o INACTIVO."""
        token = {"id_empresa": 1, "nro_usuario": 1}
        with self.assertRaisesRegex(proveedor_services.ProveedorError, "Estado inválido"):
            proveedor_services.listar(token, estado="BORRADO")

    def test_rechaza_paginacion_invalida(self):
        """HU-72: El limit no puede superar 100."""
        token = {"id_empresa": 1, "nro_usuario": 1}
        with self.assertRaisesRegex(proveedor_services.ProveedorError, "Paginación"):
            proveedor_services.listar(token, limit=200)

    # ── HU-73 Asociar materiales ──────────────────────────────────────────
    def test_rechaza_lista_materiales_vacia(self):
        """HU-73: Debe proporcionarse al menos un id_material."""
        token = {"id_empresa": 1, "nro_usuario": 1}
        with self.assertRaisesRegex(proveedor_services.ProveedorError, "al menos un id_material"):
            proveedor_services.asociar_materiales(1, [], token)

    def test_rechaza_id_material_no_numerico(self):
        """HU-73: Los IDs de material deben ser enteros."""
        token = {"id_empresa": 1, "nro_usuario": 1}
        with self.assertRaisesRegex(proveedor_services.ProveedorError, "ID de material inválido"):
            # Simulamos que el proveedor existe pasando un mock básico
            import unittest.mock as mock
            with mock.patch("app.repos.proveedor_repos.obtener", return_value={"id_proveedor": 1}):
                proveedor_services.asociar_materiales(1, ["abc"], token)

    # ── Normalización de campos ───────────────────────────────────────────
    def test_normaliza_campos_de_texto(self):
        """Los campos de texto deben ser limpiados con strip()."""
        result = proveedor_services._validar({
            "nombre": "  Constructora Norte  ", "nit": "  456-7  "
        }, creando=True)
        self.assertEqual(result["nombre"], "Constructora Norte")
        self.assertEqual(result["nit"], "456-7")

    def test_token_sin_empresa_lanza_error(self):
        """Un token sin id_empresa debe lanzar ProveedorError 403."""
        token = {"nro_usuario": 1}
        with self.assertRaises(proveedor_services.ProveedorError) as ctx:
            proveedor_services._empresa(token)
        self.assertEqual(ctx.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
