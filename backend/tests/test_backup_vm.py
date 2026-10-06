"""Contrato VM y seguridad, sin conexión real, daemon, herramientas o OCI."""
import os
import unittest
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app import create_app
from app.repos import backup_jobs_repos as jobs
from app.services import backup_services as service
from app.services.backups.oracle_settings import Settings, BackupError
from app.services.backups.contracts import BackupRequest, Schedule, ApplyRequest
from app.utils import security


def job(identifier=1, state='COMPLETADO', kind='BACKUP', origin='MANUAL'):
    return dict(id=identifier, tipo=kind, origen=origin, estado=state,
                object_name='obras/backup_1.dump', sha256='a'*64, size_bytes=2048,
                solicitado_por=1, error=None, fecha_solicitud=datetime.now(timezone.utc),
                fecha_inicio=None, fecha_fin=None, job_relacionado_id=None)


@contextmanager
def transaction(*args, **kwargs):
    yield MagicMock()


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.config = Settings(True, 'postgresql://example/control', 'designado', False, 120)

    def test_preflight_needs_no_disk_keys_s3_or_local_tools(self):
        with patch.object(service.Settings, 'load', return_value=self.config), \
             patch.object(service.control_repo, 'control', return_value={'mantenimiento': False}), \
             patch.object(jobs, 'installation'), patch('subprocess.run') as physical:
            result = service.preflight()
        self.assertEqual(result['schema'], 'obras')
        self.assertFalse(result['heartbeat_verificado'])
        physical.assert_not_called()

    def test_legacy_invalid_keys_do_not_affect_vm_configuration(self):
        with patch.dict(os.environ, {'BACKUP_ENABLED':'true','BACKUP_CONTROL_DSN':'postgresql://example/control',
                                     'BACKUP_ENVIRONMENT':'test','BACKUP_KEYS_JSON':'bad-json',
                                     'BACKUP_VM_HEARTBEAT_MAX_AGE':'120'}):
            self.assertEqual(Settings.load().requirements(), [])

    def test_unconnected_legacy_heartbeat_does_not_claim_daemon_alive(self):
        state = {'mantenimiento':False,'heartbeat':datetime.now(timezone.utc)}
        with patch.object(service.Settings, 'load', return_value=self.config), \
             patch.object(service.control_repo, 'control', return_value=state), patch.object(jobs, 'installation'), \
             patch.object(jobs, 'download_installation', side_effect=BackupError('Falta tabla de descargas.')):
            status = service.status()
        self.assertTrue(status['configurado'])
        self.assertFalse(status['worker_activo'])
        self.assertIsNone(status['ultimo_latido'])
        self.assertFalse(status['restauracion_habilitada'])
        self.assertFalse(status['descarga_habilitada'])

    def test_connected_stale_heartbeat_fails_closed(self):
        config = replace(self.config, heartbeat_connected=True)
        state = {'mantenimiento':False,'heartbeat':datetime.now(timezone.utc)-timedelta(minutes=10)}
        with patch.object(service.control_repo, 'control', return_value=state), patch.object(jobs, 'installation'):
            with self.assertRaises(BackupError) as exc:
                service.preflight(config)
        self.assertEqual(exc.exception.code, 'BACKUP_SERVICE_UNAVAILABLE')

    def test_future_heartbeat_is_not_available(self):
        self.assertFalse(service.heartbeat({'heartbeat':datetime.now(timezone.utc)+timedelta(minutes=1)},
                                          replace(self.config, heartbeat_connected=True))[1])

    def test_preserves_maintenance_even_when_daemon_disconnected(self):
        with patch.object(service.control_repo, 'control', return_value={'mantenimiento':True}), \
             patch.object(jobs, 'installation'), patch.object(service.control_repo, 'barrier') as barrier:
            with self.assertRaises(BackupError): service.preflight(self.config)
        barrier.assert_not_called()

    def test_legacy_worker_cannot_claim_or_execute_jobs(self):
        from app.services.backups.worker import tick
        with patch.object(service.control_repo,'claim') as claim, self.assertRaises(BackupError) as exc:
            tick()
        self.assertEqual(exc.exception.code,'BACKUP_LEGACY_RETIRED')
        claim.assert_not_called()

    def test_bigint_id_and_metadata_are_not_lost(self):
        source=job(9223372036854775807)
        result=service.public_job(source)
        self.assertEqual(result['id'],'9223372036854775807')
        self.assertEqual(result['estado'],'COMPLETADO')
        self.assertEqual(result['respaldo']['sha256'],source['sha256'])
        self.assertEqual(result['size_bytes'],2048)
        for invalid in ['0','-1','1;DROP TABLE x','9223372036854775808','1.5']:
            with self.subTest(invalid=invalid), self.assertRaises(HTTPException): service.identifier(invalid)

    def test_pre_restore_relation_keeps_existing_meaning(self):
        row=job(6,origin='PRE_RESTORE');row['job_relacionado_id']=5
        self.assertEqual(service.public_job(row)['job_relacionado_id'],'5')
        self.assertIsNone(service.public_restore(job(5,kind='RESTORE'))['respaldo'])

    def test_daemon_errors_do_not_disclose_connection_or_access_urls(self):
        text=service.safe_error('postgresql://user:secret@host/control https://oci.example/p/private-token token=secret')
        self.assertNotIn('private-token',text)
        self.assertNotIn('user:',text)
        self.assertNotIn('secret',text)

    def test_rejects_non_completed_sources_and_arbitrary_scope(self):
        for row in [job(state='PENDIENTE'),job(kind='RESTORE'),dict(job(),sha256='bad'),dict(job(),object_name=None)]:
            with self.subTest(row=row), self.assertRaises(BackupError): service.checked_source(row)
        for body in [{'alcance':'sistema_completo'},{'object_name':'arbitrary'},{'id_empresa':3}]:
            with self.subTest(body=body), self.assertRaises(ValueError): BackupRequest.model_validate(body)

    def test_disabled_restore_survives_old_enabled_flag(self):
        with patch.dict(os.environ, {'BACKUP_RESTORE_ENABLED':'true'}), patch.object(jobs, 'get', return_value=job()), \
             patch.object(jobs, 'queue') as queue:
            from app.services.backups.contracts import ValidateRequest
            with self.assertRaises(BackupError) as exc: service.validate(1,ValidateRequest(archivo='1'))
        self.assertEqual(exc.exception.code,'BACKUP_RESTORE_MIGRATION')
        queue.assert_not_called()

    def test_reauthentication_and_confirmation_remain_mandatory(self):
        request=ApplyRequest(confirmacion='RESTAURAR TODOS LOS TENANTS 1',desafio='x'*32,token_reautenticacion='fresh-'+'x'*30)
        with patch.object(service,'decode_access_token',return_value={'success':True,'payload':{'iat':datetime.now(timezone.utc).timestamp()}}), \
             patch.object(service,'administrator',return_value=1):
            with self.assertRaises(BackupError) as exc: service.apply(1,'1',request,'other-token')
            self.assertEqual(exc.exception.code,'BACKUP_RESTORE_MIGRATION')
            with self.assertRaises(HTTPException): service.apply(1,'1',request,request.token_reautenticacion)
            with self.assertRaises(BackupError): service.apply(1,'1',request.model_copy(update={'confirmacion':'sí'}),'other-token')

    def test_old_or_different_actor_reauthentication_is_rejected(self):
        request=ApplyRequest(confirmacion='RESTAURAR TODOS LOS TENANTS 1',desafio='x'*32,token_reautenticacion='fresh-'+'x'*30)
        for issued, actor in [(0,1),(datetime.now(timezone.utc).timestamp(),2)]:
            with patch.object(service,'decode_access_token',return_value={'success':True,'payload':{'iat':issued}}), \
                 patch.object(service,'administrator',return_value=actor), self.assertRaises(HTTPException):
                service.apply(1,'1',request,'old-token')

    def test_legacy_full_schedule_is_paused_without_database_write(self):
        row={'configuracion':{'habilitada':True,'alcance':'sistema_completo'},'next_run':'old'}
        with patch.object(service.control_repo,'get',return_value=row), patch.object(service.control_repo,'save_schedule') as save:
            result=service.schedule()
        self.assertFalse(result['configuracion']['habilitada'])
        self.assertTrue(row['configuracion']['habilitada'])
        save.assert_not_called()


class RepositoryTests(unittest.TestCase):
    def test_preflight_detects_missing_auxiliary_permissions_before_accepting_work(self):
        with patch.object(jobs,'transaction',transaction),patch.object(jobs,'one',side_effect=[
            {'jobs':'public.backup_jobs','requests':'backup_control.t_backup_vm_request'},
            {'read':True,'write':True,'sequence':True},
            {'request_read':False,'request_write':False,'audit_write':True,'audit_sequence':True}]):
            with self.assertRaises(BackupError) as exc: jobs.installation()
        self.assertEqual(exc.exception.code,'BACKUP_CONTROL_FORBIDDEN')

    def test_missing_idempotent_job_does_not_create_duplicate_work(self):
        with patch.object(jobs,'transaction',transaction), \
             patch.object(jobs,'one',side_effect=[dict(job_id=1,id_usuario=7,origen='MANUAL'),None]) as query:
            with self.assertRaises(BackupError) as exc: jobs.queue(7,'key')
        self.assertEqual(exc.exception.code,'BACKUP_JOB_UNAVAILABLE')
        self.assertFalse(any('INSERT INTO public.backup_jobs' in call.args[1] for call in query.call_args_list))

    def test_retry_returns_same_job_without_duplicate_physical_work(self):
        cur=MagicMock(); row=job(state='PENDIENTE')
        previous=dict(job_id=1,id_usuario=7,origen='MANUAL')
        @contextmanager
        def tx(): yield cur
        with patch.object(jobs,'transaction',tx), \
             patch.object(jobs,'one',side_effect=[None,{'mantenimiento':False},row,previous,row]), \
             patch.object(jobs,'event'):
            self.assertEqual(jobs.queue(7,'key')['id'],jobs.queue(7,'key')['id'])
        # El INSERT real se hace por one(); inspeccionar sus consultas a través del mock.
        # La tabla de solicitudes solo se escribe una vez durante el primer encolado.
        inserts=[c for c in cur.execute.call_args_list if 'INSERT INTO backup_control.t_backup_vm_request' in c.args[0]]
        self.assertEqual(len(inserts),1)

    def test_queue_cannot_cross_active_barrier(self):
        with patch.object(jobs,'transaction',transaction), \
             patch.object(jobs,'one',side_effect=[None,{'mantenimiento':True}]) as read:
            with self.assertRaises(BackupError): jobs.queue(1,'key')
        self.assertEqual(len(read.call_args_list),2)

    def test_queue_uses_actual_vm_fields_without_source_or_relation(self):
        with patch.object(jobs,'transaction',transaction), \
             patch.object(jobs,'one',side_effect=[None,{'mantenimiento':False},job(state='PENDIENTE')]) as query, \
             patch.object(jobs,'event'):
            jobs.queue(7,'manual:7:key')
        sql=query.call_args_list[2].args[1]
        self.assertIn('public.backup_jobs',sql)
        self.assertIn("'BACKUP'",sql)
        self.assertEqual(query.call_args_list[2].args[2],('MANUAL',7))
        self.assertNotIn('job_relacionado_id',sql)

    def test_due_schedule_revalidates_actor_and_uses_same_queue(self):
        row=dict(id_usuario=7,configuracion=Schedule(habilitada=True).model_dump(),
                 next_run=datetime.now(timezone.utc)-timedelta(days=3))
        authorize=MagicMock()
        with patch.object(jobs,'transaction',transaction),patch.object(jobs,'one',return_value=row), \
             patch.object(jobs,'queue',return_value=job()) as queue,patch.object(jobs,'event'):
            self.assertEqual(jobs.dispatch_schedule(authorize)['id'],1)
        authorize.assert_called_once_with({'nro_usuario':7})
        self.assertEqual(queue.call_args.args[2],'AUTOMATICO')
        self.assertTrue(queue.call_args.args[1].startswith('schedule:'))

    def test_not_due_disabled_or_revoked_schedule_never_enqueues(self):
        for enabled, date in [(False,datetime.now(timezone.utc)-timedelta(days=1)),
                              (True,datetime.now(timezone.utc)+timedelta(days=1))]:
            row=dict(id_usuario=7,configuracion=Schedule(habilitada=enabled).model_dump(),next_run=date)
            with patch.object(jobs,'transaction',transaction),patch.object(jobs,'one',return_value=row), \
                 patch.object(jobs,'queue') as queue:
                self.assertIsNone(jobs.dispatch_schedule(MagicMock()))
            queue.assert_not_called()
        row=dict(id_usuario=7,configuracion=Schedule(habilitada=True).model_dump(),next_run=datetime.now(timezone.utc)-timedelta(days=1))
        with patch.object(jobs,'transaction',transaction),patch.object(jobs,'one',return_value=row),patch.object(jobs,'queue') as queue:
            with self.assertRaises(HTTPException): jobs.dispatch_schedule(MagicMock(side_effect=HTTPException(403)))
        queue.assert_not_called()


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(os.environ,{'BACKUP_ENABLED':'false'});self.env.start();self.addCleanup(self.env.stop)
        app=create_app();app.dependency_overrides[security.verificar_token]=lambda:dict(nro_usuario=1)
        self.client=TestClient(app)
        self.tx=patch.object(service.business,'transaction',transaction);self.tx.start();self.addCleanup(self.tx.stop)
        self.actor=patch.object(service.business,'actor',return_value={'estado':'ACTIVO','nombre_rol':'ADMINISTRADOR'})
        self.actor.start();self.addCleanup(self.actor.stop)

    def test_manual_job_is_accepted_and_body_cannot_select_object(self):
        with patch.object(service,'preflight'),patch.object(jobs,'queue',return_value=job(state='PENDIENTE')) as queue:
            response=self.client.post('/api/backup/ejecuciones',json={'alcance':'base_datos'},headers={'Idempotency-Key':'same-key'})
            self.assertEqual(response.status_code,202)
            self.assertEqual(response.json()['id'],'1')
            queue.assert_called_once_with(1,'manual:1:same-key')
            response=self.client.post('/api/backup/ejecuciones',json={'object_name':'dangerous'})
            self.assertEqual(response.status_code,422)

    def test_history_detail_and_real_states(self):
        with patch.object(jobs,'history',return_value={'items':[job()], 'total':1,'pagina':1}),patch.object(jobs,'get',return_value=job()):
            self.assertEqual(self.client.get('/api/backup/ejecuciones?estado=COMPLETADO').json()['items'][0]['estado'],'COMPLETADO')
            self.assertEqual(self.client.get('/api/backup/ejecuciones/1').json()['object_name'],'obras/backup_1.dump')
            self.assertEqual(self.client.get('/api/backup/ejecuciones?estado=LISTO').status_code,422)

    def test_restore_and_import_are_explicitly_unavailable(self):
        with patch.object(jobs,'get',return_value=job()),patch.object(jobs,'queue') as queue:
            response=self.client.post('/api/backup/restauraciones/validar',json={'archivo':'1'})
            self.assertEqual(response.status_code,503)
            self.assertEqual(response.json()['code'],'BACKUP_RESTORE_MIGRATION')
            self.assertEqual(self.client.post('/api/backup/importaciones',content=b'PGDMP',headers={'Content-Type':'application/octet-stream'}).status_code,410)
        queue.assert_not_called()

    def test_company_admin_cannot_dispatch_or_restore(self):
        service.business.actor.return_value['nombre_rol']='ADMINISTRADOR_EMPRESA'
        self.assertEqual(self.client.post('/api/backup/programacion/ejecutar',json={}).status_code,403)
        self.assertEqual(self.client.post('/api/backup/restauraciones/validar',json={'archivo':'1'}).status_code,403)


if __name__=='__main__': unittest.main()
