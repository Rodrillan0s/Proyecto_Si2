"""Herramientas oficiales PostgreSQL; comandos construidos sin shell ni SQL del usuario."""
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import parse_dsn
from app.config import Config
from .settings import BackupError


def tool(name):
    configured = os.getenv('BACKUP_'+name.upper()+'_PATH')
    if configured:
        candidate = Path(configured)
        if candidate.is_file():
            return str(candidate.resolve())
        raise BackupError('No se encontró '+name+' en la ruta configurada.', 'BACKUP_TOOLS_MISSING', 503)
    found = shutil.which(name)
    if found:
        return found
    for directory in (Path('C:/Program Files/PostgreSQL'), Path('C:/Program Files (x86)/PostgreSQL')):
        candidates = list(directory.glob('*/bin/'+name+'.exe')) if directory.exists() else []
        if candidates:
            return str(max(candidates, key=lambda item: int(item.parents[1].name) if item.parents[1].name.isdigit() else 0))
    raise BackupError('Instala las herramientas PostgreSQL pg_dump y pg_restore o configura sus rutas.', 'BACKUP_TOOLS_MISSING', 503)


def connection(settings, database=None, restore=False, autocommit=False):
    try:
        options = parse_dsn(settings.restore_dsn) if restore else dict(host=Config.DB_HOST,
            port=Config.DB_PORT, user=Config.DB_USER, password=Config.DB_PASSWORD, dbname=Config.DB_NAME,
            sslmode=settings.sslmode)
        if database:
            options['dbname'] = database
        options['connect_timeout'] = 10
        conn = psycopg2.connect(**options)
        conn.autocommit = autocommit
        return conn
    except Exception as exc:
        raise BackupError('No se pudo conectar PostgreSQL con la cuenta configurada.', 'BACKUP_DATABASE_UNAVAILABLE', 503) from exc


def command(settings, args, beat=lambda: None, database=None, restore=False):
    options = parse_dsn(settings.restore_dsn) if restore else dict(host=Config.DB_HOST, port=Config.DB_PORT,
        user=Config.DB_USER, password=Config.DB_PASSWORD, dbname=Config.DB_NAME, sslmode=settings.sslmode)
    if database:
        options['dbname'] = database
    env = os.environ.copy()
    # No permitir PGOPTIONS/PGSERVICE heredados que cambien el destino o ejecuten ajustes.
    for key in list(env):
        if key.startswith('PG'):
            env.pop(key)
    mapping = {'host': 'PGHOST', 'port': 'PGPORT', 'user': 'PGUSER', 'password': 'PGPASSWORD',
               'dbname': 'PGDATABASE', 'sslmode': 'PGSSLMODE', 'sslrootcert': 'PGSSLROOTCERT',
               'sslcert': 'PGSSLCERT', 'sslkey': 'PGSSLKEY'}
    env.update({target: str(options[source]) for source, target in mapping.items() if options.get(source) is not None})
    env['PGCONNECT_TIMEOUT'] = '10'
    with tempfile.TemporaryFile() as errors, tempfile.TemporaryFile() as output:
        process = subprocess.Popen(args, env=env, shell=False, stdin=subprocess.DEVNULL,
            stdout=output, stderr=errors, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        deadline = time.monotonic()+settings.timeout
        try:
            while process.poll() is None:
                beat()
                destination = next((value[7:] for value in args if value.startswith('--file=')), None)
                if destination and Path(destination).exists() and Path(destination).stat().st_size > settings.max_bytes:
                    raise BackupError('El volcado superó el límite del paquete.', 'BACKUP_QUOTA_EXCEEDED')
                if time.monotonic() > deadline:
                    raise BackupError('La operación PostgreSQL superó el tiempo permitido.', 'BACKUP_TIMEOUT')
                time.sleep(0.25)
            if process.returncode:
                # El stderr puede incluir datos/credenciales; no exponerlo por HTTP.
                errors.seek(0)
                diagnostic = errors.read(65536).decode('utf-8',errors='replace').lower()
                category = next((label for marker,label in (
                    ('permission denied','permisos insuficientes'),('does not exist','objeto/rol/extensión faltante'),
                    ('authentication failed','autenticación rechazada'),('version mismatch','versión incompatible'),
                    ('no space left','almacenamiento lleno'),('could not connect','conexión no disponible'))
                    if marker in diagnostic),'error de PostgreSQL; revisar logs del servidor')
                logging.getLogger(__name__).error('%s falló (código %s): %s',Path(args[0]).name,process.returncode,category)
                raise BackupError('PostgreSQL rechazó la operación. Revisa permisos, roles/extensiones y compatibilidad de versión.', 'BACKUP_POSTGRES_FAILED')
            output.seek(0)
            return output.read(65536)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def versions(settings, recovery=False):
    dump = command(settings, [tool('pg_dump'), '--version']).decode()
    restore = command(settings, [tool('pg_restore'), '--version']).decode()
    conn = connection(settings, 'postgres' if recovery else None, restore=recovery)
    try:
        with conn.cursor() as cur:
            cur.execute('SHOW server_version_num')
            server = int(cur.fetchone()[0]) // 10000
        dmajor = int(re.search(r'(\d+)(?:\.\d+)', dump).group(1))
        rmajor = int(re.search(r'(\d+)(?:\.\d+)', restore).group(1))
        if dmajor < server or dmajor != rmajor:
            raise BackupError('pg_dump debe soportar el servidor y compartir versión mayor con pg_restore.', 'BACKUP_VERSION_MISMATCH')
        return {'servidor_major': server, 'dump_major': dmajor, 'pg_dump': dump.strip(), 'pg_restore': restore.strip()}
    finally:
        conn.close()


def inventory(conn):
    """Conteos y catálogo bajo el MISMO snapshot que el dump, sin datos de filas."""
    tables, objects, sequences = {}, [], {}
    with conn.cursor() as cur:
        cur.execute('SET LOCAL search_path=pg_catalog')
        cur.execute("""SELECT n.nspname,c.relname,c.relkind FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname NOT IN ('information_schema')
              AND c.relkind IN ('r','p','m') ORDER BY 1,2""")
        relations = cur.fetchall()
        for namespace, name, kind in relations:
            cur.execute(sql.SQL('SELECT count(*) FROM {}.{}').format(sql.Identifier(namespace), sql.Identifier(name)))
            tables[namespace+'.'+name] = cur.fetchone()[0]
        queries = [
            """SELECT n.nspname,c.relname,a.attname,format_type(a.atttypid,a.atttypmod),a.attnotnull,
                COALESCE(pg_get_expr(d.adbin,d.adrelid),''),a.attidentity,a.attgenerated FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
                JOIN pg_namespace n ON n.oid=c.relnamespace LEFT JOIN pg_attrdef d ON d.adrelid=c.oid AND d.adnum=a.attnum
                WHERE a.attnum>0 AND NOT a.attisdropped AND n.nspname NOT LIKE 'pg_%'
                AND n.nspname<>'information_schema' AND c.relkind IN ('r','p','v','m') ORDER BY 1,2,3""",
            """SELECT n.nspname,p.proname,pg_get_function_identity_arguments(p.oid),
                pg_get_functiondef(p.oid) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname<>'information_schema' AND p.prokind IN ('f','p') ORDER BY 1,2,3""",
            """SELECT n.nspname,c.relname,t.tgname,pg_get_triggerdef(t.oid) FROM pg_trigger t
                JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE NOT t.tgisinternal AND n.nspname NOT LIKE 'pg_%' ORDER BY 1,2,3""",
            """SELECT n.nspname,c.relname,k.conname,pg_get_constraintdef(k.oid),k.convalidated
                FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname NOT LIKE 'pg_%' ORDER BY 1,2,3""",
            """SELECT n.nspname,c.relname,pg_get_indexdef(i.indexrelid),i.indisvalid FROM pg_index i
                JOIN pg_class c ON c.oid=i.indexrelid JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname NOT LIKE 'pg_%' ORDER BY 1,2""",
            "SELECT extname,extversion FROM pg_extension ORDER BY 1",
            """SELECT n.nspname,c.relname,pg_get_viewdef(c.oid,TRUE) FROM pg_class c
                JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind IN ('v','m')
                AND n.nspname NOT LIKE 'pg_%' AND n.nspname<>'information_schema' ORDER BY 1,2""",
            """SELECT n.nspname,t.typname,e.enumlabel,e.enumsortorder FROM pg_enum e
                JOIN pg_type t ON t.oid=e.enumtypid JOIN pg_namespace n ON n.oid=t.typnamespace ORDER BY 1,2,4""",
            """SELECT n.nspname,c.relname,c.relrowsecurity,c.relforcerowsecurity FROM pg_class c
                JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname NOT LIKE 'pg_%'
                AND n.nspname<>'information_schema' AND c.relkind IN ('r','p') ORDER BY 1,2""",
            """SELECT n.nspname,c.relname,p.polname,p.polcmd,p.polpermissive,
                pg_get_expr(p.polqual,p.polrelid),pg_get_expr(p.polwithcheck,p.polrelid)
                FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid
                JOIN pg_namespace n ON n.oid=c.relnamespace ORDER BY 1,2,3""",
            """SELECT n.nspname,c.relname,COALESCE(c.relacl::text,''),pg_get_userbyid(c.relowner)
                FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname<>'information_schema' AND c.relkind IN ('r','p','S','v','m') ORDER BY 1,2"""
        ]
        for query in queries:
            cur.execute(query)
            objects.append(cur.fetchall())
        cur.execute("""SELECT n.nspname,c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE c.relkind='S' AND n.nspname NOT LIKE 'pg_%' ORDER BY 1,2""")
        for namespace, name in cur.fetchall():
            cur.execute(sql.SQL('SELECT last_value,is_called FROM {}.{}').format(sql.Identifier(namespace), sql.Identifier(name)))
            sequences[namespace+'.'+name] = list(cur.fetchone())
        cur.execute('SELECT oid,pg_get_userbyid(lomowner),COALESCE(lomacl::text,\'\') FROM pg_largeobject_metadata ORDER BY oid')
        large_objects = {}
        for oid, owner, acl in cur.fetchall():
            digest = hashlib.sha256()
            large = conn.lobject(oid, 'rb')
            try:
                for chunk in iter(lambda: large.read(1024*1024), b''):
                    digest.update(chunk)
            finally:
                large.close()
            large_objects[str(oid)] = {'sha256':digest.hexdigest(),'owner':owner,'acl':acl}
        # Los permisos funcionales son tablas del inventario; comprobar también rol/estado.
        cur.execute("SELECT to_regclass('obras.t_usuario'),to_regclass('obras.t_incidencia_evidencia')")
        user_table, evidence_table = cur.fetchone()
        if not user_table:
            raise BackupError('La base no contiene el modelo OBRATEC esperado.')
        cur.execute("SELECT count(*) FROM obras.t_usuario u JOIN obras.t_rol r USING(id_rol) WHERE r.nombre_rol='ADMINISTRADOR' AND u.estado='ACTIVO'")
        if cur.fetchone()[0] < 1:
            raise BackupError('No existe un administrador global activo para recuperar acceso.')
        evidence = []
        if evidence_table:
            cur.execute('SELECT ruta_archivo FROM obras.t_incidencia_evidencia ORDER BY ruta_archivo')
            evidence = [row[0] for row in cur.fetchall()]
    return {'tablas': tables, 'catalogo_sha256': hashlib.sha256(json.dumps(objects, default=str, ensure_ascii=False).encode()).hexdigest(),
            'secuencias': sequences, 'evidencias': evidence, 'large_objects':large_objects, 'base': database_metadata(conn)}


def database_metadata(conn):
    with conn.cursor() as cur:
        # PostgreSQL 17 es el servidor verificado del proyecto.
        cur.execute("""SELECT pg_encoding_to_char(encoding),datcollate,datctype,datlocprovider,
            datlocale,daticurules,datcollversion,pg_get_userbyid(datdba),datconnlimit,
            (SELECT spcname FROM pg_tablespace WHERE oid=dattablespace)
            FROM pg_database WHERE datname=current_database()""")
        keys = ('encoding','collate','ctype','provider','locale','icu_rules','collversion','owner','connection_limit','tablespace')
        result = dict(zip(keys, cur.fetchone()))
        cur.execute("""SELECT pg_get_userbyid(acl.grantor),CASE WHEN acl.grantee=0 THEN 'PUBLIC'
            ELSE pg_get_userbyid(acl.grantee) END,acl.privilege_type,acl.is_grantable
            FROM pg_database d,aclexplode(COALESCE(d.datacl,acldefault('d',d.datdba))) acl
            WHERE d.datname=current_database() ORDER BY 1,2,3,4""")
        result['grants'] = [list(row) for row in cur.fetchall()]
        cur.execute("""SELECT CASE WHEN s.setrole=0 THEN '' ELSE pg_get_userbyid(s.setrole) END,s.setconfig
            FROM pg_db_role_setting s JOIN pg_database d ON d.oid=s.setdatabase
            WHERE d.datname=current_database() ORDER BY 1""")
        result['role_settings'] = [list(row) for row in cur.fetchall()]
        return result


def dump(settings, destination, beat):
    conn = connection(settings)
    try:
        conn.set_session(isolation_level='REPEATABLE READ', readonly=True)
        with conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout='120s'")
            cur.execute('SELECT pg_export_snapshot()')
            snapshot = cur.fetchone()[0]
        captured = inventory(conn)
        command(settings, [tool('pg_dump'), '--format=custom', '--file='+str(destination), '--snapshot='+snapshot], beat)
        # No -n: se incluyen todos los esquemas, datos, ACL, owners y large objects.
        return captured
    finally:
        conn.rollback()
        conn.close()


def stage_name(identifier):
    return 'obratec_stage_'+str(identifier).replace('-', '')[:24]


def checked_name(name):
    if not re.fullmatch(r'obratec_(?:stage|old)_[a-f0-9]{24}', name):
        raise BackupError('Destino temporal no autorizado.')
    return name


def create_stage(settings, name, metadata):
    checked_name(name)
    conn = connection(settings, 'postgres', restore=True, autocommit=True)
    try:
        with conn.cursor() as cur:
            provider = {'c':'libc','i':'icu','b':'builtin'}.get(metadata['provider'])
            if not provider:
                raise BackupError('Proveedor de collation incompatible.')
            query = sql.SQL('CREATE DATABASE {} TEMPLATE template0 OWNER {} ENCODING {} LC_COLLATE {} LC_CTYPE {} LOCALE_PROVIDER {} TABLESPACE {}').format(
                sql.Identifier(name),sql.Identifier(metadata['owner']),sql.Literal(metadata['encoding']),
                sql.Literal(metadata['collate']),sql.Literal(metadata['ctype']),sql.SQL(provider),sql.Identifier(metadata['tablespace']))
            if provider in {'icu','builtin'}:
                query += sql.SQL(' {} {}').format(sql.SQL('ICU_LOCALE' if provider=='icu' else 'BUILTIN_LOCALE'),sql.Literal(metadata['locale']))
            if provider == 'icu' and metadata.get('icu_rules'):
                query += sql.SQL(' ICU_RULES {}').format(sql.Literal(metadata['icu_rules']))
            cur.execute(query)
            cur.execute(sql.SQL('ALTER DATABASE {} CONNECTION LIMIT {}').format(sql.Identifier(name),sql.Literal(metadata['connection_limit'])))
            cur.execute(sql.SQL('SET ROLE {}').format(sql.Identifier(metadata['owner'])))
            cur.execute(sql.SQL('REVOKE ALL ON DATABASE {} FROM PUBLIC').format(sql.Identifier(name)))
            for grantor, grantee, privilege, grantable in metadata['grants']:
                if privilege not in {'CONNECT','CREATE','TEMPORARY'}:
                    raise BackupError('Privilegio de base incompatible.')
                cur.execute('RESET ROLE')
                cur.execute(sql.SQL('SET ROLE {}').format(sql.Identifier(grantor)))
                cur.execute(sql.SQL('GRANT {} ON DATABASE {} TO {}{}').format(sql.SQL(privilege),sql.Identifier(name),
                    sql.SQL('PUBLIC') if grantee=='PUBLIC' else sql.Identifier(grantee),sql.SQL(' WITH GRANT OPTION' if grantable else '')))
            cur.execute('RESET ROLE')
            for role, options in metadata['role_settings']:
                for setting in options:
                    key,value=setting.split('=',1)
                    cur.execute((sql.SQL('ALTER ROLE {} IN DATABASE {} SET {} TO {}').format(sql.Identifier(role),sql.Identifier(name),sql.Identifier(key),sql.Literal(value))) if role else
                        sql.SQL('ALTER DATABASE {} SET {} TO {}').format(sql.Identifier(name),sql.Identifier(key),sql.Literal(value)))
    finally:
        conn.close()


def restore_stage(settings, name, dump_file, beat):
    checked_name(name)
    command(settings, [tool('pg_restore'), '--exit-on-error', '--single-transaction', '--dbname='+name, str(dump_file)], beat, name, True)
    conn = connection(settings, name, True)
    try:
        conn.set_session(readonly=True)
        return inventory(conn)
    finally:
        conn.close()


def rename(settings, source, target):
    # Solo el nombre de negocio de Config y nombres temporales generados.
    for name in (source, target):
        if name != Config.DB_NAME:
            checked_name(name)
    conn = connection(settings, 'postgres', True, autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s AND pid<>pg_backend_pid()', (source,))
            cur.execute(sql.SQL('ALTER DATABASE {} RENAME TO {}').format(sql.Identifier(source), sql.Identifier(target)))
    finally:
        conn.close()


def exists(settings, name):
    conn = connection(settings, 'postgres', True)
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT 1 FROM pg_database WHERE datname=%s', (name,))
            return bool(cur.fetchone())
    finally:
        conn.close()


def drop_stage(settings, name):
    checked_name(name)
    if not name.startswith('obratec_stage_'):
        raise BackupError('Solo se limpian bases temporales de ensayo.')
    conn = connection(settings, 'postgres', True, autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute(sql.SQL('DROP DATABASE IF EXISTS {} WITH (FORCE)').format(sql.Identifier(name)))
    finally:
        conn.close()


def quarantine_reports(settings):
    conn = connection(settings, Config.DB_NAME, True)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT to_regclass('obras.t_reporte_programacion')")
                if cur.fetchone()[0]:
                    cur.execute("UPDATE obras.t_reporte_programacion SET habilitada=FALSE,estado='PAUSADA',error='Pausada tras restauración; requiere revisión explícita.'")
                    cur.execute("UPDATE obras.t_reporte_ejecucion SET estado='FALLIDO',error='Trabajo en cuarentena tras restauración.',lease_until=NULL WHERE estado IN ('PENDIENTE','GENERANDO')")
                    cur.execute("UPDATE obras.t_reporte_envio SET estado='INCIERTO',error='Cuarentena: Brevo no revierte envíos al restaurar la base.',lease_until=NULL WHERE estado IN ('PENDIENTE','ENVIANDO')")
    finally:
        conn.close()
