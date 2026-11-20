"""Contrato de descargas OCI sin escribir en PostgreSQL ni contactar OCI."""
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app import create_app
from app.routes.backup_routes import global_admin
from app.services import backup_services as service
from app.services.backups.oracle_settings import Settings, BackupError
from app.repos import backup_jobs_repos as jobs
from tests.test_backup_vm import job, transaction

CONFIG = Settings(True, 'postgresql://example/control', 'designado', False, 120)
PAR = 'https://objectstorage.sa-saopaulo-1.oraclecloud.com/p/test-token/n/grdnljcz1opp/b/obratec_backups/o/obras/backup_1.dump'


def request(state='COMPLETADO', **changes):
    return dict(dict(id=9223372036854775807, job_id=1, estado=state, par_url=PAR,
                     expira_en=datetime.now(timezone.utc)+timedelta(minutes=10), solicitado_por=7, error=None), **changes)


class ResultTests(unittest.TestCase):
    def test_ready_request_releases_only_scoped_url_and_string_ids(self):
        result = service.download_result(request(), job(), CONFIG)
        self.assertEqual(result['url'], PAR)
        self.assertEqual(result['id'], '9223372036854775807')
        self.assertEqual(result['job_id'], '1')
        self.assertEqual(result['nombre'], 'backup_1.dump')
        self.assertNotIn('par_url', result)
        self.assertNotIn('solicitado_por', result)

    def test_pending_processing_failed_and_expired_never_disclose_url(self):
        for state in ['PENDIENTE', 'PROCESANDO', 'FALLIDO']:
            with self.subTest(state=state):
                result = service.download_result(request(state, error='https://example/p/private-token'), job(), CONFIG)
                self.assertIsNone(result['url'])
                self.assertNotIn('private-token', str(result))
        row = request(expira_en=datetime.now(timezone.utc)-timedelta(seconds=1))
        result = service.download_result(row, job(), CONFIG)
        self.assertEqual(result['estado'], 'EXPIRADO')
        self.assertIsNone(result['url'])
        self.assertEqual(row['estado'], 'COMPLETADO')  # Estado derivado, sin UPDATE.

    def test_rejects_untrusted_or_different_object_urls(self):
        invalid = [PAR.replace('https:', 'http:'), PAR.replace('oraclecloud.com', 'oraclecloud.com.evil.test'),
                   PAR.replace('/obras/backup_1.dump', '/obras/another.dump'),
                   PAR.replace('/b/obratec_backups/', '/b/other/'), PAR.replace('/n/grdnljcz1opp/', '/n/other/'),
                   PAR.replace('https://', 'https://user:secret@'), PAR.replace('https://', 'https://@'), PAR+'?next=https://evil.test',
                   PAR+'#fragment', PAR.replace('/p/test-token/', '/p//'), PAR+'\n',
                   PAR.replace('oraclecloud.com/', 'oraclecloud.com:8443/'), PAR.replace('test-token', 'test%0Atoken'), None]
        for url in invalid:
            with self.subTest(url=url), self.assertRaises(BackupError) as exc:
                service.download_result(request(par_url=url), job(), CONFIG)
            self.assertEqual(exc.exception.code, 'BACKUP_DOWNLOAD_INVALID')
            self.assertNotIn('test-token', str(exc.exception))

    def test_percent_encoded_object_is_compared_to_known_source(self):
        result = service.download_result(request(par_url=PAR.replace('/obras/backup_1.dump', '/obras%2Fbackup_1.dump')), job(), CONFIG)
        self.assertIsNotNone(result['url'])

    def test_missing_or_naive_expiry_is_not_released(self):
        for expiry in [None, datetime.now()]:
            with self.subTest(expiry=expiry), self.assertRaises(BackupError):
                service.download_result(request(expira_en=expiry), job(), CONFIG)

    def test_unavailable_source_never_queues_request(self):
        with patch.object(jobs, 'get', return_value=job(state='PROCESANDO')), patch.object(jobs, 'request_download') as queue:
            with self.assertRaises(BackupError): service.download('1', 7)
        queue.assert_not_called()

    def test_service_passes_only_known_id_and_authenticated_actor(self):
        with patch.object(Settings, 'load', return_value=CONFIG), patch.object(jobs, 'get', return_value=job()), \
             patch.object(jobs, 'download_installation'), patch.object(jobs, 'request_download', return_value=(request('PENDIENTE'), job())) as queue:
            self.assertEqual(service.download('1', 7)['estado'], 'PENDIENTE')
        queue.assert_called_once_with(1, 7, service.checked_source)

    def test_status_lookup_is_restricted_to_authenticated_owner(self):
        with patch.object(Settings, 'load', return_value=CONFIG), \
             patch.object(jobs, 'download_request', return_value=(None, None)) as lookup:
            with self.assertRaises(HTTPException) as exc: service.download_status('2', 7)
        self.assertEqual(exc.exception.status_code, 404)
        lookup.assert_called_once_with(2, 7)

    def test_download_setup_failure_does_not_disable_manual_backups(self):
        with patch.object(Settings, 'load', return_value=CONFIG), patch.object(service.control_repo, 'control', return_value={'mantenimiento':False}), \
             patch.object(jobs, 'installation'), patch.object(jobs, 'download_installation', side_effect=BackupError('Revisar permisos.')):
            result = service.status()
        self.assertTrue(result['configurado'])
        self.assertFalse(result['descarga_habilitada'])
        self.assertEqual(result['requisitos_descarga'], ['Revisar permisos.'])


class RepositoryTests(unittest.TestCase):
    def test_inserts_only_job_and_actor_and_audits_without_url(self):
        with patch.object(jobs, 'transaction', transaction), patch.object(jobs, 'get', return_value=job()), \
             patch.object(jobs, 'one', side_effect=[None, request('PENDIENTE')]) as query, patch.object(jobs, 'event') as audit:
            row, _ = jobs.request_download(1, 7, service.checked_source)
        self.assertEqual(row['estado'], 'PENDIENTE')
        self.assertEqual(query.call_args_list[1].args[2], (1, 7))
        self.assertIn('INSERT INTO public.backup_download_requests(job_id,solicitado_por)', query.call_args_list[1].args[1])
        self.assertNotIn('test-token', str(audit.call_args))

    def test_retry_reuses_own_pending_or_unexpired_request(self):
        for state in ['PENDIENTE', 'COMPLETADO']:
            with patch.object(jobs, 'transaction', transaction), patch.object(jobs, 'get', return_value=job()), \
                 patch.object(jobs, 'one', return_value=request(state)) as query, patch.object(jobs, 'event') as audit:
                jobs.request_download(1, 7, service.checked_source)
            self.assertEqual(query.call_count, 1)
            self.assertIn('solicitado_por=%s', query.call_args.args[1])
            self.assertIn('expira_en > now()', query.call_args.args[1])
            self.assertEqual(query.call_args.args[2], (1, 7))
            audit.assert_not_called()

    def test_other_actor_request_is_not_returned(self):
        with patch.object(jobs, 'transaction', transaction), patch.object(jobs, 'one', return_value=None) as query, patch.object(jobs, 'get') as source:
            self.assertEqual(jobs.download_request(2, 8), (None, None))
        self.assertIn('solicitado_por=%s', query.call_args.args[1])
        self.assertEqual(query.call_args.args[2], (2, 8))
        source.assert_not_called()

    def test_source_is_revalidated_inside_enqueue_transaction(self):
        with patch.object(jobs, 'transaction', transaction), patch.object(jobs, 'get', return_value=job(state='FALLIDO')), \
             patch.object(jobs, 'one') as query:
            with self.assertRaises(BackupError): jobs.request_download(1, 7, service.checked_source)
        query.assert_not_called()

    def test_missing_download_table_or_grants_fails_explicitly(self):
        for rows in [[{'requests':None}], [{'requests':'public.backup_download_requests'}, {'read':True,'write':False}]]:
            with patch.object(jobs, 'transaction', transaction), patch.object(jobs, 'one', side_effect=rows):
                with self.assertRaises(BackupError): jobs.download_installation()


class ApiTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {'BACKUP_ENABLED':'false'})
        env.start(); self.addCleanup(env.stop)
        app = create_app()
        app.dependency_overrides[global_admin] = lambda: 7
        self.client = TestClient(app)

    def test_start_and_compatibility_get_return_202_without_caching(self):
        result = service.download_result(request('PENDIENTE'), job(), CONFIG)
        with patch.object(service, 'download', return_value=result) as start:
            for method in ['post', 'get']:
                response = getattr(self.client, method)('/api/backup/ejecuciones/1/archivo')
                self.assertEqual(response.status_code, 202)
                self.assertEqual(response.headers['cache-control'], 'no-store')
                self.assertIsNone(response.json()['url'])
            start.assert_called_with('1', 7)

    def test_completed_poll_returns_200_and_no_store(self):
        with patch.object(service, 'download_status', return_value=service.download_result(request(), job(), CONFIG)) as poll:
            response = self.client.get('/api/backup/descargas/9223372036854775807')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertEqual(response.json()['url'], PAR)
        poll.assert_called_once_with('9223372036854775807', 7)

    def test_every_download_endpoint_requires_global_admin(self):
        def reject(): raise HTTPException(403, 'Solo administrador global.')
        self.client.app.dependency_overrides[global_admin] = reject
        with patch.object(service, 'download') as start, patch.object(service, 'download_status') as poll:
            self.assertEqual(self.client.post('/api/backup/ejecuciones/1/archivo').status_code, 403)
            self.assertEqual(self.client.get('/api/backup/ejecuciones/1/archivo').status_code, 403)
            self.assertEqual(self.client.get('/api/backup/descargas/2').status_code, 403)
        start.assert_not_called(); poll.assert_not_called()


if __name__ == '__main__': unittest.main()
