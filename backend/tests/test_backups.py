"""Pruebas aisladas: no conectan a PostgreSQL ni envían correos."""
import asyncio
import base64
import json
import os
import stat
import tempfile
import unittest
import zipfile
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app import create_app
from app.services import backup_services as service
from app.services.backups import crypto, packages, restoration, engine, postgres
from app.services.backups.contracts import BackupRequest, Schedule, next_run, ApplyRequest
from app.services.backups.settings import Settings, BackupError
from app.services.backups.coordination import MaintenanceMiddleware, drain
from app.utils import security


@contextmanager
def business_tx(*args, **kwargs):
    yield MagicMock()


class CryptoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.key = os.urandom(32)
        self.source = self.root/'source'
        self.source.write_bytes(b'PGDMP'+os.urandom(2*1024*1024))
        self.encrypted = self.root/'archive'
        crypto.encrypt(self.source, self.encrypted, 'k1', self.key, 'backup-id', 4*1024*1024)
    def tearDown(self):
        self.temp.cleanup()
    def test_streaming_roundtrip_and_header(self):
        header = crypto.decrypt(self.encrypted, self.root/'out', {'k1': self.key}, 4*1024*1024)
        self.assertEqual(header['id'], 'backup-id')
        self.assertEqual(crypto.sha256(self.source), crypto.sha256(self.root/'out'))
    def test_ciphertext_tamper_never_returns_plaintext(self):
        content = bytearray(self.encrypted.read_bytes()); content[-30] ^= 1
        self.encrypted.write_bytes(content)
        with self.assertRaises(BackupError): crypto.decrypt(self.encrypted, self.root/'out', {'k1': self.key}, 4*1024*1024)
        self.assertFalse((self.root/'out').exists())
    def test_tag_tamper_and_wrong_key_fail_closed(self):
        with self.assertRaises(BackupError): crypto.decrypt(self.encrypted, self.root/'out', {'k1': os.urandom(32)}, 4*1024*1024)
        self.assertFalse((self.root/'out').exists())
    def test_authenticated_metadata_cannot_be_relabelled(self):
        content = self.encrypted.read_bytes().replace(b'backup-id', b'changed-id')
        self.encrypted.write_bytes(content)
        with self.assertRaises(BackupError): crypto.decrypt(self.encrypted, self.root/'out', {'k1': self.key}, 4*1024*1024)
    def test_missing_key_identifies_recovery_requirement(self):
        with self.assertRaises(BackupError) as exc: crypto.decrypt(self.encrypted, self.root/'out', {}, 4*1024*1024)
        self.assertEqual(exc.exception.code, 'BACKUP_KEY_MISSING')
    def test_wrong_format_and_size_do_not_extract(self):
        self.encrypted.write_bytes(b'SELECT dangerous_sql();')
        with self.assertRaises(BackupError): crypto.decrypt(self.encrypted, self.root/'out', {'k1': self.key}, 20)
    def test_fresh_nonces_for_identical_content(self):
        crypto.encrypt(self.source, self.root/'other', 'k1', self.key, 'backup-id', 4*1024*1024)
        self.assertNotEqual(self.encrypted.read_bytes(), (self.root/'other').read_bytes())


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.config = SimpleNamespace(max_files=100, max_bytes=1024*1024)
    def tearDown(self): self.temp.cleanup()
    def archive(self, entries, override=None):
        infos = []
        path = self.root/'archive.zip'
        with zipfile.ZipFile(path, 'w') as out:
            for name, content in entries:
                temp = self.root/'digest'; temp.write_bytes(content)
                infos.append(dict(ruta=name, bytes=len(content), sha256=crypto.sha256(temp)))
                out.writestr(name, content)
            manifest = dict(formato=1, alcance='sistema_completo', archivos=infos)
            if override: manifest.update(override)
            out.writestr('manifest.json', json.dumps(manifest))
        return path
    def test_database_and_uploads_extract_with_verified_digest(self):
        path = self.archive([('database.dump', b'PGDMP-data'), ('uploads/incidencias/1/a.jpg', b'image')])
        packages.unpack(path, self.root/'stage', self.config)
        self.assertEqual((self.root/'stage/uploads/incidencias/1/a.jpg').read_bytes(), b'image')
    def test_path_traversal_windows_and_absolute_names_rejected(self):
        for index, name in enumerate(['../outside', '/absolute', 'C:/key', 'uploads\\..\\secret']):
            path = self.archive([('database.dump', b'PGDMP'), (name, b'x')])
            with self.subTest(name=name), self.assertRaises(BackupError): packages.unpack(path, self.root/str(index), self.config)
        self.assertFalse((self.root.parent/'outside').exists())
    def test_environment_and_unlisted_software_cannot_be_restored(self):
        for index, name in enumerate(['release/backend/.env', 'release/.git/config', 'release/frontend/node_modules/key', 'secret.sql']):
            path = self.archive([('database.dump', b'PGDMP'), (name, b'x')])
            with self.assertRaises(BackupError): packages.unpack(path, self.root/str(index), self.config)
    def test_declared_size_and_digest_must_match(self):
        entries = [dict(ruta='database.dump', bytes=6, sha256='0'*64)]
        path = self.archive([('database.dump', b'PGDMPx')], {'archivos': entries})
        with self.assertRaises(BackupError): packages.unpack(path, self.root/'stage', self.config)
    def test_expansion_and_file_count_bounded(self):
        path = self.archive([('database.dump', b'PGDMP'), ('uploads/a', b'x'*5000)])
        with self.assertRaises(BackupError): packages.unpack(path, self.root/'stage', SimpleNamespace(max_files=1,max_bytes=100))
    def test_symbolic_link_rejected(self):
        path = self.root/'archive.zip'
        with zipfile.ZipFile(path, 'w') as out:
            out.writestr('database.dump', b'PGDMP')
            info = zipfile.ZipInfo('uploads/link'); info.create_system=3; info.external_attr=(stat.S_IFLNK|0o777)<<16
            out.writestr(info, b'../secret')
            out.writestr('manifest.json', json.dumps(dict(formato=1,alcance='sistema_completo',archivos=[
                dict(ruta='database.dump',bytes=5,sha256='0'*64),dict(ruta='uploads/link',bytes=9,sha256='0'*64)])))
        with self.assertRaises(BackupError): packages.unpack(path, self.root/'stage', self.config)
    def test_source_capture_excludes_secrets_and_dependencies(self):
        for name in ['backend/app/a.py', 'backend/app/.env', 'backend/app/__pycache__/a.pyc', 'backend/uploads/1.jpg', 'frontend/src/main.ts']:
            file=self.root/name; file.parent.mkdir(parents=True,exist_ok=True); file.write_text('data')
        names=[name for name, _ in packages.sources(True, self.root)]
        self.assertIn('release/backend/app/a.py', names)
        self.assertIn('uploads/1.jpg', names)
        self.assertFalse(any('.env' in name or '__pycache__' in name for name in names))


class ScheduleTests(unittest.TestCase):
    def test_local_daily_to_utc(self):
        now=datetime(2026,10,4,6,0,tzinfo=timezone.utc)
        self.assertEqual(next_run(Schedule(),now), datetime(2026,10,5,6,0,tzinfo=timezone.utc))
    def test_weekly_and_monthly_days(self):
        now=datetime(2026,10,4,12,tzinfo=timezone.utc)
        self.assertEqual(next_run(Schedule(frecuencia='semanal',dia_semana=0),now).day,5)
        self.assertEqual(next_run(Schedule(frecuencia='mensual',dia_mes=28),now).day,28)
    def test_ambiguous_hour_executed_once_and_nonexistent_hour_normalized(self):
        config=Schedule(zona_horaria='America/New_York',hora='01:30')
        self.assertEqual(next_run(config,datetime(2026,11,1,5,40,tzinfo=timezone.utc)).day,2)
        config=Schedule(zona_horaria='America/New_York',hora='02:30')
        self.assertEqual(next_run(config,datetime(2026,3,8,6,tzinfo=timezone.utc)).hour,7)
    def test_invalid_configuration_and_arbitrary_sql_rejected(self):
        for data in [{'hora':'25:00'},{'zona_horaria':'not-a-zone'},{'dia_mes':31},{'retencion_dias':365},{'sql':'SELECT *'}]:
            with self.assertRaises(ValueError): Schedule.model_validate(data)
        with self.assertRaises(ValueError): BackupRequest.model_validate({'alcance':'tenant','id_empresa':7})


class AuthorizationTests(unittest.TestCase):
    def test_reloads_role_not_claim_or_company_selection(self):
        row=dict(id_usuario=1,estado='ACTIVO',nombre_rol='ADMINISTRADOR_EMPRESA')
        with patch.object(service.business,'transaction',business_tx),patch.object(service.business,'actor',return_value=row):
            with self.assertRaises(HTTPException): service.administrator({'nro_usuario':1,'nombre_rol':'ADMINISTRADOR','id_empresa':7})
            row['nombre_rol']='ADMINISTRADOR'
            self.assertEqual(service.administrator({'nro_usuario':1,'id_empresa':999}),1)
            row['estado']='INACTIVO'
            with self.assertRaises(HTTPException): service.administrator({'nro_usuario':1})
    def test_session_epoch_revokes_tokens_after_restore(self):
        with patch('app.repos.backup_repos.epoch',return_value=4):
            token=security.create_access_token(1,'admin','ADMINISTRADOR',1,'A','Admin',None)
            self.assertTrue(security.decode_access_token(token)['success'])
        with patch('app.repos.backup_repos.epoch',return_value=5):
            self.assertFalse(security.decode_access_token(token)['success'])
    def test_control_failure_does_not_accept_token(self):
        with patch('app.repos.backup_repos.epoch',return_value=0):
            token=security.create_access_token(1,'admin','ADMINISTRADOR',1,'A','Admin',None)
        with patch('app.repos.backup_repos.epoch',side_effect=BackupError('control fuera de servicio',status=503)):
            with self.assertRaises(BackupError): security.decode_access_token(token)
    def test_idempotency_key_required_and_no_untyped_creation(self):
        with patch.object(service,'preflight'),patch.object(service.repo,'queue') as queue:
            with self.assertRaises(HTTPException): service.create(1,BackupRequest(),'')
            queue.assert_not_called()


class RecoveryTests(unittest.TestCase):
    def test_expired_writer_does_not_silently_unlock(self):
        with patch('app.services.backups.coordination.repo.barrier') as barrier,patch('app.services.backups.coordination.repo.active_writers',return_value=1):
            with self.assertRaises(BackupError): drain('owner','backup',timeout=0)
            barrier.assert_called_once_with('owner',True,'backup')
    def test_prepared_file_promotion_can_be_compensated(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); release=root/'release'; work=root/'work'; release.mkdir(); work.mkdir()
            current=release/'a'; preserved=work/'a'; preserved.write_text('previous')
            settings=SimpleNamespace(release_target=release,directory=root,stop_hook=('stop',),start_hook=('start',),health_hook=('health',))
            journal=[dict(paso='Preservar archivo',tipo='file',origen=str(current),destino=str(preserved),estado='PREPARADO')]
            with patch.object(restoration,'hook'),patch.object(restoration.repo,'update'),patch.object(restoration.repo,'barrier'):
                restoration.compensate(settings,{'id':'id'},journal,lambda:None)
            self.assertEqual(current.read_text(),'previous'); self.assertEqual(journal[0]['estado'],'REVERTIDO')
    def test_ambiguous_promotion_keeps_resources_and_requires_operator(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); release=root/'release'; work=root/'work'; release.mkdir(); work.mkdir()
            (release/'a').write_text('current'); (work/'a').write_text('old')
            settings=SimpleNamespace(release_target=release,directory=root,stop_hook=('stop',))
            journal=[dict(paso='move',tipo='file',origen=str(release/'a'),destino=str(work/'a'),estado='PREPARADO')]
            with patch.object(restoration,'hook'),self.assertRaises(BackupError): restoration.compensate(settings,{'id':'id'},journal,lambda:None)
            self.assertEqual((release/'a').read_text(),'current'); self.assertEqual((work/'a').read_text(),'old')
    def test_postgres_names_never_accept_user_sql_or_production_drop(self):
        for name in ['obras','postgres','obratec_stage_x;DROP DATABASE obras']:
            with self.assertRaises(BackupError): postgres.checked_name(name)
        with self.assertRaises(BackupError): postgres.drop_stage(None,'obratec_old_'+'a'*24)
    def test_no_reauth_logout_on_wrong_password_and_distinct_login_tokens(self):
        with patch('app.repos.backup_repos.epoch',return_value=0):
            first=security.create_access_token(1,'admin','ADMINISTRADOR',1,'A','Admin',None)
            second=security.create_access_token(1,'admin','ADMINISTRADOR',1,'A','Admin',None)
            self.assertNotEqual(first,second)
    def test_missing_evidence_blocks_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            manifest=dict(alcance='sistema_completo',evidencias_sha256={'uploads/missing.jpg':'0'*64})
            with self.assertRaises(BackupError): restoration.check_evidence(SimpleNamespace(release_target=root),root,manifest)


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.environment=patch.dict(os.environ,{'BACKUP_ENABLED':'false'})
        self.environment.start(); self.addCleanup(self.environment.stop)
        self.app=create_app(); self.app.dependency_overrides[security.verificar_token]=lambda:dict(nro_usuario=1)
        self.client=TestClient(self.app)
        self.tx=patch.object(service.business,'transaction',business_tx);self.tx.start()
        self.actor=patch.object(service.business,'actor',return_value=dict(id_usuario=1,nombre_rol='ADMINISTRADOR',estado='ACTIVO'));self.actor.start()
    def tearDown(self): self.actor.stop();self.tx.stop()
    def test_state_returns_setup_requirements_without_false_success(self):
        with patch.dict(os.environ,{'BACKUP_ENABLED':'false','BACKUP_CONTROL_DSN':''}):
            response=self.client.get('/api/backup/estado?id_empresa=999')
        self.assertEqual(response.status_code,200)
        self.assertFalse(response.json()['configurado']);self.assertFalse(response.json()['worker_activo'])
        self.assertTrue(response.json()['alcance_global'])
    def test_global_only_for_every_action(self):
        service.business.actor.return_value['nombre_rol']='ADMINISTRADOR_EMPRESA'
        for url in ['/estado','/programacion','/ejecuciones','/restauraciones']:
            self.assertEqual(self.client.get('/api/backup'+url).status_code,403)
    def test_strict_creation_and_job_202(self):
        with patch.object(service,'create',return_value=dict(id=str(uuid4()),estado='PENDIENTE')) as create:
            response=self.client.post('/api/backup/ejecuciones',json={'alcance':'base_datos'},headers={'Idempotency-Key':'repeatable'})
            self.assertEqual(response.status_code,202)
            self.assertEqual(create.call_args.args[0],1)
            response=self.client.post('/api/backup/ejecuciones',json={'sql':'SELECT *'})
            self.assertEqual(response.status_code,422)
    def test_safe_configuration_errors_have_machine_code(self):
        with patch.object(service,'create',side_effect=BackupError('Falta instalar control','BACKUP_SETUP_REQUIRED',503)):
            response=self.client.post('/api/backup/ejecuciones',json={})
            self.assertEqual(response.status_code,503);self.assertEqual(response.json()['code'],'BACKUP_SETUP_REQUIRED')
    def test_raw_sql_import_rejected_before_import_service(self):
        with patch.object(service,'import_archive') as importer:
            response=self.client.post('/api/backup/importaciones',content=b'SELECT x',headers={'Content-Type':'application/sql'})
            self.assertEqual(response.status_code,415);importer.assert_not_called()
    def test_download_requires_ready_archive(self):
        with patch.object(service.repo,'get',return_value=dict(tipo='BACKUP',estado='PENDIENTE')):
            response=self.client.get('/api/backup/ejecuciones/1/archivo')
            self.assertEqual(response.status_code,409)
    def test_wrong_reauthentication_uses_dedicated_code(self):
        with patch('app.services.auth_services.loguear_usuario',side_effect=ValueError('Contraseña incorrecta.')):
            response=self.client.post('/api/backup/reautenticacion',json={'identificador':'admin','password':'invalid'})
            self.assertEqual(response.status_code,401)
            self.assertEqual(response.json()['code'],'BACKUP_REAUTH_FAILED')
    def test_maintenance_middleware_blocks_business_and_keeps_control_plane(self):
        from fastapi import FastAPI
        app=FastAPI();app.add_middleware(MaintenanceMiddleware)
        @app.post('/business')
        def business(): return {'unexpected':'mutation'}
        @app.get('/api/backup/estado')
        def state(): return {'mantenimiento':True}
        with patch('app.services.backups.coordination.Settings.load',return_value=SimpleNamespace(enabled=True)),patch('app.services.backups.coordination.repo.control',return_value={'mantenimiento':True,'motivo':'restore'}):
            client=TestClient(app)
            self.assertEqual(client.post('/business').status_code,503)
            self.assertEqual(client.get('/api/backup/estado').status_code,200)


if __name__ == '__main__': unittest.main()
