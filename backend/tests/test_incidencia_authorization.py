"""
Pruebas de autorización para CU19 - Gestión de incidencias.
Valida que exigir_permiso() (mecanismo ya usado por el resto del backend)
bloquea correctamente a roles sin el permiso requerido para cada operación
del módulo de incidencias, y que ADMINISTRADOR (admin de plataforma) sigue
teniendo bypass total, igual que en el resto del sistema.
Ejecutar: python -m pytest tests/test_incidencia_authorization.py -v
"""

import unittest
from unittest import mock

from fastapi import HTTPException

from app.utils import security


class ExigirPermisoIncidenciasTests(unittest.TestCase):

    # 17. Usuario sin permiso -> 403
    @mock.patch("app.utils.security.obtener_permisos_rol")
    def test_usuario_sin_permiso_es_rechazado(self, mock_permisos):
        mock_permisos.return_value = {"Visualizar_incidencias"}
        token_data = {"nombre_rol": "SUPERVISOR"}
        checker = security.exigir_permiso("Registrar_incidencias")

        with self.assertRaises(HTTPException) as ctx:
            checker(token_data)
        self.assertEqual(ctx.exception.status_code, 403)

    @mock.patch("app.utils.security.obtener_permisos_rol")
    def test_usuario_con_permiso_correcto_pasa(self, mock_permisos):
        mock_permisos.return_value = {"Visualizar_incidencias", "Registrar_incidencias"}
        token_data = {"nombre_rol": "JEFE DE OBRA"}
        checker = security.exigir_permiso("Registrar_incidencias")

        result = checker(token_data)
        self.assertEqual(result, token_data)

    @mock.patch("app.utils.security.obtener_permisos_rol")
    def test_administrador_global_bypassa_permisos(self, mock_permisos):
        mock_permisos.return_value = set()
        token_data = {"nombre_rol": "ADMINISTRADOR"}
        checker = security.exigir_permiso("Cerrar_incidencias")

        result = checker(token_data)
        self.assertEqual(result, token_data)
        # Ni siquiera debería consultar la tabla de permisos para el admin global.
        mock_permisos.assert_not_called()

    @mock.patch("app.utils.security.obtener_permisos_rol")
    def test_jefe_de_obra_sin_permiso_de_cierre_es_rechazado(self, mock_permisos):
        # JEFE DE OBRA tiene Modificar_incidencias pero no Cerrar_incidencias
        # (ver migration_cu19_incidencias.sql): el cierre queda reservado a
        # quien tenga ese permiso dedicado (p.ej. Supervisor).
        mock_permisos.return_value = {
            "Visualizar_incidencias", "Registrar_incidencias",
            "Modificar_incidencias", "Asignar_incidencias",
        }
        token_data = {"nombre_rol": "JEFE DE OBRA"}
        checker = security.exigir_permiso("Cerrar_incidencias")

        with self.assertRaises(HTTPException) as ctx:
            checker(token_data)
        self.assertEqual(ctx.exception.status_code, 403)


# ─────────────────────────────────────────────────────────────────────────────
# 18. Aislamiento multi-tenant a nivel de repositorio (SQL parametrizado)
# ─────────────────────────────────────────────────────────────────────────────
class RepoTenantScopingTests(unittest.TestCase):
    """
    Verifica que las funciones de solo-lectura del repo jamás construyan una
    consulta de detalle únicamente por id_incidencia: siempre deben incluir el
    filtro de empresa (derivado de incidencia -> obra -> empresa) en el SQL.
    """

    def test_obtener_detalle_incluye_filtro_de_empresa_en_el_sql(self):
        from app.repos import incidencia_repos

        captured = {}

        class FakePostgreSQL:
            def create_connection(self):
                pass

            def close_connection(self):
                pass

            def execute_query(self, query, params=None, fetchall=False, fetchone=False, commit=False):
                captured["query"] = query
                captured["params"] = params
                return None

        with mock.patch("app.repos.incidencia_repos.PostgreSQL", FakePostgreSQL):
            incidencia_repos.obtener_detalle(1, id_empresa=2)

        self.assertIn("o.id_empresa", captured["query"])
        self.assertIn(2, captured["params"])

    def test_usuarios_asignables_filtra_por_empresa_obra_y_activo(self):
        from app.repos import incidencia_repos

        captured = {}

        class FakePostgreSQL:
            def create_connection(self):
                pass

            def close_connection(self):
                pass

            def execute_query(self, query, params=None, fetchall=False, fetchone=False, commit=False):
                captured["query"] = query
                captured["params"] = params
                return []

        with mock.patch("app.repos.incidencia_repos.PostgreSQL", FakePostgreSQL):
            incidencia_repos.obtener_usuarios_asignables(3, 8)

        self.assertIn("u.id_empresa = %s", captured["query"])
        self.assertIn("o.id_empresa = u.id_empresa", captured["query"])
        self.assertIn("obras.t_obra_usuario", captured["query"])
        self.assertIn("o.id_obra = %s", captured["query"])
        self.assertIn("u.estado = 'ACTIVO'", captured["query"])
        self.assertNotIn("t_rol_permiso", captured["query"])
        self.assertEqual(captured["params"], (3, 8))


# ─────────────────────────────────────────────────────────────────────────────
# Permiso exigido por cada ruta de OT afectadas / cambio de estado
# ─────────────────────────────────────────────────────────────────────────────
class RutasPermisosTests(unittest.TestCase):

    @staticmethod
    def _permiso_de_ruta(path, method):
        from app.routes import incidencia_routes
        for route in incidencia_routes.router.routes:
            if route.path == path and method in route.methods:
                for dep in route.dependant.dependencies:
                    cells = dep.call.__closure__ or ()
                    for cell in cells:
                        if isinstance(cell.cell_contents, str):
                            return cell.cell_contents
        return None

    def test_permisos_de_rutas_ot_afectadas(self):
        # No se crean permisos nuevos: se reutilizan los existentes de CU19.
        self.assertEqual(self._permiso_de_ruta("/{id_incidencia}/ordenes-trabajo", "GET"), "Visualizar_incidencias")
        self.assertEqual(self._permiso_de_ruta("/{id_incidencia}/ordenes-trabajo/disponibles", "GET"), "Asignar_incidencias")
        self.assertEqual(self._permiso_de_ruta("/{id_incidencia}/ordenes-trabajo", "PUT"), "Asignar_incidencias")

    def test_estado_usa_autorizacion_especifica(self):
        from app.routes import incidencia_routes as routes
        route = next(r for r in routes.router.routes if r.path == "/{id_incidencia}/estado")
        self.assertIn(routes.acceso_estado, [d.call for d in route.dependant.dependencies])

    @mock.patch("app.utils.security.obtener_permisos_rol")
    def test_rol_sin_asignar_no_puede_vincular_ot(self, mock_permisos):
        # Un rol con solo Modificar_incidencias (p.ej. un responsable) no vincula OT.
        mock_permisos.return_value = {"Visualizar_incidencias", "Modificar_incidencias"}
        checker = security.exigir_permiso("Asignar_incidencias")
        with self.assertRaises(HTTPException) as ctx:
            checker({"nombre_rol": "SUPERVISOR"})
        self.assertEqual(ctx.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
