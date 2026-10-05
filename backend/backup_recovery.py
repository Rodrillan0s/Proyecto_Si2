"""Consola del operador: no requiere login a la base de negocio ni expone secretos."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from app.repos import backup_repos as repo
from app.services.backups import crypto, packages, storage, postgres, restoration
from app.services.backups.settings import Settings, BackupError


def main():
    parser = argparse.ArgumentParser(description='Recuperación independiente OBRATEC')
    parser.add_argument('--environment', required=True)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--status', action='store_true')
    actions.add_argument('--preflight', action='store_true')
    actions.add_argument('--register', type=Path, help='Reconstruir catálogo desde un paquete autenticado')
    actions.add_argument('--validate', help='ID del archivo de control')
    actions.add_argument('--apply', help='ID de restauración ya validada')
    actions.add_argument('--rollback', help='Compensar la promoción del ID indicado')
    actions.add_argument('--clear-writer', help='ID exacto del escritor terminado, comprobado por el operador')
    actions.add_argument('--release-maintenance', help='ID propietario; solo si no se promovieron recursos')
    actions.add_argument('--discard-validation', help='Limpiar un ensayo terminado/vencido, sin promociones')
    parser.add_argument('--confirm', default='')
    parser.add_argument('--disaster', action='store_true', help='Solo si la base original NO existe')
    args = parser.parse_args()
    settings = Settings.load()
    if not settings.environment or args.environment != settings.environment:
        raise BackupError('El entorno no coincide con BACKUP_ENVIRONMENT.')
    if args.status:
        state = repo.control()
        print(json.dumps({'mantenimiento': state['mantenimiento'], 'propietario': str(state['propietario']),
            'motivo': state['motivo'], 'session_epoch': state['session_epoch']}, ensure_ascii=False))
        with repo.transaction() as cur:
            cur.execute('SELECT id,tipo,lease_until FROM backup_control.t_backup_escritor ORDER BY lease_until')
            print(json.dumps([dict(row) for row in cur.fetchall()], default=str, ensure_ascii=False))
        return
    storage.prepare(settings)
    if args.preflight:
        repo.control()
        print(json.dumps({'postgres': postgres.versions(settings, recovery=settings.restore_enabled),
            'requisitos_restauracion': settings.restore_requirements()}, ensure_ascii=False))
        return
    if args.register:
        work = settings.directory/'work'/str(uuid4())
        work.mkdir(mode=0o700)
        try:
            metadata = crypto.decrypt(args.register, work/'package.zip', settings.keys, settings.max_bytes)
            manifest = packages.unpack(work/'package.zip', work/'package', settings)
            if metadata['id'] != manifest['id'] or metadata['key_id'] != manifest['key_id']:
                raise BackupError('La cabecera y el manifiesto del paquete no coinciden.')
            name = 'recovered_'+str(uuid4())+'.obratec'
            import shutil
            shutil.copyfile(args.register, work/'archive.partial')
            digest, size = crypto.sha256(work/'archive.partial'), (work/'archive.partial').stat().st_size
            _, remote = storage.publish(settings, work/'archive.partial', name)
            identifier = repo.register_archive(None, name, digest, size, manifest, remote)
            print('Archivo reconstruido en el catálogo:', identifier)
        finally:
            storage.cleanup_work(settings, work)
        return
    if args.validate:
        row = repo.validate_queue(args.validate, 0)
        restoration.validate(settings, row, lambda: None)
        print('Restauración validada:', row['id'])
        return
    if args.clear_writer:
        if args.confirm != 'ESCRITOR TERMINADO '+args.clear_writer:
            raise BackupError('Confirma ESCRITOR TERMINADO seguido de su ID tras comprobar que no ejecuta ni escribe.')
        repo.leave_writer(args.clear_writer)
        repo.event(None, 0, 'ESCRITOR_LIMPIADO_POR_OPERADOR', {'id': args.clear_writer})
        return
    if args.discard_validation:
        row = repo.get('restauracion', args.discard_validation)
        if args.confirm != 'DESCARTAR ENSAYO '+args.discard_validation or not row or row['diario'] or row['aplicar_en']:
            raise BackupError('Confirma DESCARTAR ENSAYO seguido del ID; no se descartan promociones.')
        if row['lease_until'] and row['lease_until'] > datetime.now(timezone.utc) and row['worker']:
            raise BackupError('El ensayo todavía tiene un worker activo.')
        if row['stage_db']:
            if row['stage_db'] != postgres.stage_name(row['id']):
                raise BackupError('Nombre temporal incompatible con la restauración.')
            postgres.drop_stage(settings, row['stage_db'])
        if row['stage_dir'] and Path(row['stage_dir']).exists():
            expected = settings.directory/'work'/('restore_'+str(row['id']))
            if Path(row['stage_dir']).resolve() != expected.resolve():
                raise BackupError('Directorio temporal incompatible.')
            storage.cleanup_work(settings, expected)
        repo.update('restauracion', row['id'], estado='DESCARTADA', etapa='Ensayo descartado por operador')
        repo.event(row['id'], 0, 'ENSAYO_DESCARTADO')
        return
    identifier = args.apply or args.rollback or args.release_maintenance
    if args.confirm != 'RESTAURAR TODOS LOS TENANTS '+identifier:
        raise BackupError('Se requiere confirmación exacta RESTAURAR TODOS LOS TENANTS seguida del ID.')
    row = repo.get('restauracion', identifier)
    if args.release_maintenance:
        if row and row['diario']:
            raise BackupError('Hay promociones registradas. Revisa/compensa el diario antes de liberar mantenimiento.')
        if repo.active_writers():
            raise BackupError('Todavía hay escritores registrados; comprueba su terminación.')
        repo.barrier(identifier, False)
        repo.event(identifier, 0, 'MANTENIMIENTO_LIBERADO_POR_OPERADOR')
        return
    if not row:
        raise BackupError('Restauración inexistente.')
    if args.rollback:
        if row['estado'] == 'COMPLETADA':
            raise BackupError('Una restauración completada se recupera mediante otra copia validada, con preventiva nueva; no mediante compensación de un diario histórico.')
        repo.barrier(identifier, True, 'Compensación solicitada por operador')
        restoration.compensate(settings, row, row['diario'], lambda: None)
        return
    if row['estado'] != 'VALIDADA':
        raise BackupError('Se requiere un ensayo VALIDADA antes de aplicar.')
    restoration.apply(settings, row, lambda: None, disaster=args.disaster)
    print('Proceso finalizado; consultar estado y diario de control.')


if __name__ == '__main__':
    try:
        main()
    except BackupError as exc:
        raise SystemExit(str(exc))
    except Exception:
        raise SystemExit('Recuperación interrumpida. Mantén los recursos preservados y revisa el plano de control.')
