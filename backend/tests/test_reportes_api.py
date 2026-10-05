import unittest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routes.reportes_routes import router
from app.utils.security import verificar_token
from app.utils.reportes_errors import ReportesSchemaMissing
from psycopg2.errors import UndefinedTable


class ReportesApiTests(unittest.TestCase):
    def test_missing_report_schema_returns_actionable_503(self):
        from app import create_app
        app = create_app()
        app.dependency_overrides[verificar_token] = lambda: {'nro_usuario': 1}
        with patch('app.routes.reportes_routes.service.history', side_effect=ReportesSchemaMissing()):
            response = TestClient(app).get('/api/reportes/ejecuciones?id_empresa=1')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['code'], 'REPORTES_SCHEMA_MISSING')
        self.assertIn('migrate_reportes.py', response.json()['detail'])
        self.assertNotIn('SELECT', response.text)

    def test_missing_report_table_closes_connection_without_committing(self):
        from app.repos.reportes_repos import transaction
        db = MagicMock()
        with patch('app.repos.reportes_repos.PostgreSQL', return_value=db):
            with self.assertRaises(ReportesSchemaMissing):
                with transaction() as connection:
                    raise UndefinedTable('relation "obras.t_reporte_ejecucion" does not exist')
        db.conn.commit.assert_not_called()
        db.close_connection.assert_called_once()

    def test_other_missing_tables_are_not_mislabeled_as_report_installation(self):
        from app.repos.reportes_repos import transaction
        with patch('app.repos.reportes_repos.PostgreSQL'):
            with self.assertRaises(UndefinedTable):
                with transaction():
                    raise UndefinedTable('relation "obras.t_obra" does not exist')

    def test_application_factory_registers_reports_and_preserves_tenant(self):
        from app import create_app
        app = create_app()
        app.dependency_overrides[verificar_token] = lambda: {'nro_usuario': 1}
        with patch('app.routes.reportes_routes.service.catalog', return_value={'reportes': []}) as catalog:
            response = TestClient(app).get('/api/reportes/catalogo?id_empresa=3')
            self.assertEqual(response.status_code, 200)
            catalog.assert_called_once_with({'nro_usuario': 1}, 3)
        self.assertIn('/api/voz/transcribir', app.openapi()['paths'])

    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.app.dependency_overrides[verificar_token] = lambda: {'nro_usuario':1,'id_empresa':7}
        self.client = TestClient(self.app)

    def test_rejects_untyped_sql_and_filters_before_services(self):
        with patch('app.routes.reportes_routes.service.create') as create:
            response = self.client.post('/api/reportes/ejecuciones',json={'reporte':'stock','sql':'SELECT *','filtros':{}})
            self.assertEqual(response.status_code,422)
            response = self.client.post('/api/reportes/ejecuciones',json={'reporte':'incidencias','filtros':{'desde':'2026-10-04','hasta':'2026-01-01'}})
            self.assertEqual(response.status_code,422)
            create.assert_not_called()

    def test_requires_delivery_identity_and_actor_ids(self):
        with patch('app.routes.reportes_routes.service.send') as send:
            url='/api/reportes/ejecuciones/00000000-0000-4000-8000-000000000001/envios'
            response=self.client.post(url,json={'destinatarios':[2],'formatos':['pdf']})
            self.assertEqual(response.status_code,422)
            response=self.client.post(url,json={'destinatarios':['correo@example.test'],'formatos':['pdf']},headers={'Idempotency-Key':'00000000-0000-4000-8000-000000000002'})
            self.assertEqual(response.status_code,422)
            send.assert_not_called()

    def test_authenticated_download_sets_no_store(self):
        with patch('app.routes.reportes_routes.service.download',return_value=(b'%PDF','stock.pdf','pdf')):
            response=self.client.get('/api/reportes/archivos/00000000-0000-4000-8000-000000000001')
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.content,b'%PDF')
            self.assertEqual(response.headers['cache-control'],'private, no-store')


if __name__=='__main__':
    unittest.main()
