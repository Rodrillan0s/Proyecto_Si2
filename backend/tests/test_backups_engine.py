import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4
from app.services.backups import engine, crypto, packages, restoration
from app.services.backups.settings import BackupError


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.release=self.root/'release';self.backup=self.root/'backup'
        for sub in ('work','archives'): (self.backup/sub).mkdir(parents=True)
        file=self.release/'backend/app/config.py';file.parent.mkdir(parents=True);file.write_text('# source')
        (self.release/'backend/.env').write_text('do not capture secret')
        file=self.release/'frontend/src/main.ts';file.parent.mkdir(parents=True);file.write_text('// source')
        self.settings=SimpleNamespace(directory=self.backup,release_target=self.release,key_id='key',keys={'key':os.urandom(32)},
            max_bytes=10*1024**2,max_files=100,environment='test',s3_bucket='')
        self.job={'id':str(uuid4()),'solicitud':{'alcance':'sistema_completo'},'protegido':False,'id_usuario':1}
        self.inventory={'tablas':{'obras.t_empresa':2},'evidencias':[],'base':{}}
        self.versions={'servidor_major':17,'dump_major':17}
        self.registered=[]
        def register(job,name,digest,size,manifest,remote):
            self.registered.append({'nombre':name,'sha256':digest,'bytes':size,'manifiesto':manifest,'id':'archive','eliminado_en':None,'remoto':None})
            return 'archive'
        def dump(settings,destination,beat):destination.write_bytes(b'PGDMP'+b'fixture');return self.inventory
        self.patches=[patch.object(engine.postgres,'versions',return_value=self.versions),patch.object(engine.postgres,'dump',side_effect=dump),
            patch.object(engine,'drain'),patch.object(engine.repo,'update'),patch.object(engine.repo,'barrier'),
            patch.object(engine.repo,'register_archive',side_effect=register)]
        for item in self.patches:item.start()
    def tearDown(self):
        for item in reversed(self.patches):item.stop()
        self.temp.cleanup()
    def test_complete_archive_is_published_encrypted_with_real_release_hash(self):
        result=engine.create(self.settings,self.job)
        self.assertEqual(result,'archive');self.assertEqual(len(self.registered),1)
        archive=self.registered[0]; path=self.backup/'archives'/archive['nombre']
        self.assertEqual(crypto.sha256(path),archive['sha256'])
        crypto.decrypt(path,self.root/'decrypted.zip',self.settings.keys,self.settings.max_bytes)
        manifest=packages.unpack(self.root/'decrypted.zip',self.root/'unpacked',self.settings)
        self.assertEqual(manifest,archive['manifiesto']);self.assertEqual(manifest['inventario_bd']['tablas']['obras.t_empresa'],2)
        self.assertTrue(manifest['release_sha256']);self.assertFalse((self.root/'unpacked/release/backend/.env').exists())
        self.assertEqual(list((self.backup/'work').iterdir()),[])
    def test_missing_evidence_never_produces_ready_archive(self):
        self.inventory['evidencias']=['uploads/missing.jpg']
        with self.assertRaises(BackupError) as error: engine.create(self.settings,self.job)
        self.assertEqual(error.exception.code,'BACKUP_EVIDENCE_UNAVAILABLE')
        self.assertEqual(self.registered,[]);self.assertEqual(list((self.backup/'archives').iterdir()),[])
    def test_windows_evidence_reference_is_captured_without_changing_database_inventory(self):
        evidence=self.release/'backend/uploads/incidencias/image.jpg'
        evidence.parent.mkdir(parents=True);evidence.write_bytes(b'evidence content')
        self.inventory['evidencias']=[r'uploads\incidencias\image.jpg']
        engine.create(self.settings,self.job)
        archive=self.registered[0]
        crypto.decrypt(self.backup/'archives'/archive['nombre'],self.root/'package.zip',self.settings.keys,self.settings.max_bytes)
        manifest=packages.unpack(self.root/'package.zip',self.root/'unpacked',self.settings)
        self.assertEqual(manifest['evidencias_sha256'],{'uploads/incidencias/image.jpg':crypto.sha256(evidence)})
        self.assertEqual(manifest['inventario_bd']['evidencias'],[r'uploads\incidencias\image.jpg'])
        self.assertEqual((self.root/'unpacked/uploads/incidencias/image.jpg').read_bytes(),b'evidence content')
        restoration.check_evidence(self.settings,self.root/'unpacked',manifest)
    def test_database_backup_records_missing_evidence_and_can_be_verified_as_database_only(self):
        self.job['solicitud']['alcance']='base_datos'
        self.inventory['evidencias']=[r'uploads\incidencias\missing.jpg']
        engine.create(self.settings,self.job)
        archive=self.registered[0]
        crypto.decrypt(self.backup/'archives'/archive['nombre'],self.root/'package.zip',self.settings.keys,self.settings.max_bytes)
        manifest=packages.unpack(self.root/'package.zip',self.root/'unpacked',self.settings)
        self.assertEqual([entry['ruta'] for entry in manifest['archivos']],['database.dump'])
        self.assertEqual(manifest['evidencias_no_disponibles'],['uploads/incidencias/missing.jpg'])
        self.assertEqual(manifest['evidencias_sha256'],{})
        self.assertEqual(manifest['inventario_bd']['evidencias'],[r'uploads\incidencias\missing.jpg'])
        from app.services.backup_services import public_archive
        warning=public_archive(dict(archive,alcance='base_datos',verificado_en=None))['advertencias']
        self.assertEqual(len(warning),1)
        self.assertIn('1 evidencias externas',warning[0])
        with self.assertRaises(BackupError) as error:
            restoration.check_evidence(self.settings,self.root/'unpacked',manifest)
        self.assertEqual(error.exception.code,'BACKUP_EVIDENCE_UNAVAILABLE')
    def test_database_backup_still_rejects_unsafe_evidence_paths(self):
        self.job['solicitud']['alcance']='base_datos'
        self.inventory['evidencias']=[r'uploads\..\secret']
        with self.assertRaises(BackupError): engine.create(self.settings,self.job)
        self.assertEqual(self.registered,[])
    def test_evidence_normalization_rejects_absolute_and_traversal_paths(self):
        for reference in [r'C:\uploads\image.jpg',r'\\server\uploads\image.jpg',
                          r'uploads\..\secret',r'uploads/..\secret',
                          '/uploads/image.jpg','outside/image.jpg',None]:
            with self.subTest(reference=reference),self.assertRaises(BackupError):
                engine.evidence_inventory(self.release,{'evidencias':[reference]})
    def test_capture_failure_restores_barrier_but_never_publishes(self):
        with patch.object(engine.postgres,'dump',side_effect=BackupError('dump failed')):
            with self.assertRaises(BackupError): engine.create(self.settings,self.job)
        engine.repo.barrier.assert_called_with(self.job['id'],False)
        self.assertEqual(self.registered,[])
    def test_preventive_backup_does_not_release_restoration_maintenance(self):
        engine.create(self.settings,self.job,barrier_owner='restore-id')
        engine.repo.barrier.assert_not_called()
    def test_changed_ciphertext_is_not_registered(self):
        with patch.object(engine.crypto,'decrypt',side_effect=BackupError('tampered')):
            with self.assertRaises(BackupError): engine.create(self.settings,self.job)
        self.assertEqual(self.registered,[])
    def test_staged_database_mismatch_does_not_mark_backup_restore_tested(self):
        engine.create(self.settings,self.job); archive=self.registered[0]
        row={'id':str(uuid4()),'archivo':'archive','id_usuario':1}
        with (patch.object(restoration.repo,'get',return_value=archive),patch.object(restoration.postgres,'create_stage'),
             patch.object(restoration.postgres,'restore_stage',return_value={'tablas':{'obras.t_empresa':1}}),patch.object(restoration.repo,'event')):
            with self.assertRaises(BackupError): restoration.validate(self.settings,row,lambda:None)
        self.assertFalse(any(call.args[0]=='archivo' for call in engine.repo.update.call_args_list))
    def test_full_rehearsal_marks_ready_only_after_catalog_and_counts_match(self):
        engine.create(self.settings,self.job); archive=self.registered[0]
        row={'id':str(uuid4()),'archivo':'archive','id_usuario':1}
        with (patch.object(restoration.repo,'get',return_value=archive),patch.object(restoration.postgres,'create_stage'),
             patch.object(restoration.postgres,'restore_stage',return_value=self.inventory),patch.object(restoration.repo,'event')):
            restoration.validate(self.settings,row,lambda:None)
        self.assertTrue(any(call.args[0]=='archivo' and 'verificado_en' in call.kwargs for call in engine.repo.update.call_args_list))
        self.assertTrue(any(call.kwargs.get('estado')=='VALIDADA' for call in engine.repo.update.call_args_list))


if __name__=='__main__':unittest.main()
