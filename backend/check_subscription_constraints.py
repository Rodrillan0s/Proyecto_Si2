"""Pruebas PostgreSQL explícitas en un esquema aislado; no modifica datos de negocio."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from threading import Barrier
from psycopg2.extras import RealDictCursor
from inspect_subscription_db import connect


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', required=True)
    args = parser.parse_args()
    schema = 'codex_suscripciones_prueba_20261024'
    conn = connect(readonly=False)
    creado = False
    pruebas = 0
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT current_database(),to_regnamespace(%s)', (schema,))
            database, existente = cur.fetchone()
            if database != args.database or existente is not None:
                raise RuntimeError('Destino distinto o esquema de prueba ya existente; no se modifica.')
            cur.execute(f'CREATE SCHEMA {schema}')
            cur.execute(f'''CREATE TABLE {schema}.t_empresa(id_empresa serial PRIMARY KEY,nombre_empresa text);
                CREATE TABLE {schema}.t_rol(id_rol integer PRIMARY KEY,nombre_rol text);
                CREATE TABLE {schema}.t_usuario(id_usuario serial PRIMARY KEY,id_empresa integer REFERENCES {schema}.t_empresa,
                    id_rol integer REFERENCES {schema}.t_rol,estado text DEFAULT 'ACTIVO',username text);
                CREATE TABLE {schema}.t_obra(id_obra serial PRIMARY KEY,id_empresa integer REFERENCES {schema}.t_empresa,estado_obra text,nombre text);
                INSERT INTO {schema}.t_rol VALUES(1,'ADMINISTRADOR'),(3,'ADMINISTRADOR_EMPRESA');''')
            for name in ('20261024_suscripciones_empresa.sql','20261024_restricciones_suscripciones.sql','20261024_configuracion_planes.sql'):
                sql = (Path(__file__).parent / 'database' / name).read_text(encoding='utf-8').replace('obras.',schema + '.')
                cur.execute(sql)
        conn.commit()
        creado = True
        with conn.cursor() as cur:
            def run(sql, params=None):
                cur.execute(sql.replace('obras.',schema + '.'),params)

            def denegar(sql, params=None, codigo='SUSCRIPCION_CUPO'):
                nonlocal pruebas
                run('SAVEPOINT caso')
                try:
                    run(sql,params)
                except Exception as exc:
                    if codigo not in str(exc): raise
                    run('ROLLBACK TO SAVEPOINT caso')
                    pruebas += 1
                else:
                    raise AssertionError('La operación debía ser rechazada')
                run('RELEASE SAVEPOINT caso')

            run("INSERT INTO obras.t_empresa(id_empresa,nombre_empresa) VALUES(1,'Prueba'),(2,'Otra'),(9,'Concurrente'),(10,'IA')")
            for i in range(5): run("INSERT INTO obras.t_usuario(id_empresa,id_rol,username) VALUES(1,3,%s)",(str(i),))
            denegar("INSERT INTO obras.t_usuario(id_empresa,id_rol) VALUES(1,3)")
            run("INSERT INTO obras.t_usuario(id_empresa,id_rol,estado,username) VALUES(1,3,'INACTIVO','inactivo')")
            denegar("UPDATE obras.t_usuario SET estado='ACTIVO' WHERE username='inactivo'")
            run("UPDATE obras.t_usuario SET estado='INACTIVO' WHERE username='0'")
            run("UPDATE obras.t_usuario SET estado='ACTIVO' WHERE username='inactivo'")
            pruebas += 1
            run("INSERT INTO obras.t_usuario(id_empresa,id_rol,username) VALUES(1,1,'global')")
            denegar("UPDATE obras.t_usuario SET id_rol=3 WHERE username='global'")
            run("UPDATE obras.t_usuario SET id_empresa=2 WHERE username='1'")
            run('SELECT usuarios FROM obras.t_suscripcion_cupo WHERE id_empresa=1')
            assert cur.fetchone()[0]==4; pruebas += 1
            run("INSERT INTO obras.t_obra(id_empresa,estado_obra,nombre) VALUES(1,'ACTIVO','A'),(1,'PLANIFICACION','B')")
            denegar("INSERT INTO obras.t_obra(id_empresa,estado_obra) VALUES(1,'PAUSADO')")
            run("UPDATE obras.t_obra SET estado_obra='FINALIZADO' WHERE nombre='A'")
            run("INSERT INTO obras.t_obra(id_empresa,estado_obra,nombre) VALUES(1,'ACTIVO','C')")
            denegar("UPDATE obras.t_obra SET estado_obra='ACTIVO' WHERE nombre='A'")
            run("UPDATE obras.t_suscripcion_empresa SET codigo_plan='EMPRESARIAL' WHERE id_empresa=2")
            for i in range(6): run("INSERT INTO obras.t_usuario(id_empresa,id_rol) VALUES(2,3)")
            run("UPDATE obras.t_suscripcion_empresa SET codigo_plan='BASICO' WHERE id_empresa=2")
            run("UPDATE obras.t_usuario SET username='editado' WHERE id_empresa=2")
            denegar("INSERT INTO obras.t_usuario(id_empresa,id_rol) VALUES(2,3)")
            denegar("UPDATE obras.t_usuario SET id_empresa=2 WHERE username='inactivo'")
            run('SELECT usuarios FROM obras.t_suscripcion_cupo WHERE id_empresa=1')
            assert cur.fetchone()[0]==4; pruebas += 1
            run("UPDATE obras.t_suscripcion_empresa SET fecha_inicio=CURRENT_DATE-30,fecha_fin=(CURRENT_TIMESTAMP AT TIME ZONE 'America/La_Paz')::date-7 WHERE id_empresa=1")
            run('SELECT obras.fn_suscripcion_escritura(1)'); assert cur.fetchone()[0]; pruebas += 1
            run("UPDATE obras.t_suscripcion_empresa SET fecha_fin=(CURRENT_TIMESTAMP AT TIME ZONE 'America/La_Paz')::date-8 WHERE id_empresa=1")
            denegar("INSERT INTO obras.t_usuario(id_empresa,id_rol) VALUES(1,3)",codigo='SUSCRIPCION_SOLO_LECTURA')
            # Registro de identidad en la empresa técnica no consume un plan comercial.
            run("INSERT INTO obras.t_empresa(id_empresa,nombre_empresa) VALUES(20,'CLIENTES SIN EMPRESA')")
            for _ in range(6): run('INSERT INTO obras.t_usuario(id_empresa,id_rol) VALUES(20,3)')
            pruebas += 1
            for _ in range(4): run('INSERT INTO obras.t_usuario(id_empresa,id_rol) VALUES(9,3)')
            run("UPDATE obras.t_suscripcion_empresa SET codigo_plan='EMPRESARIAL' WHERE id_empresa=10")
            run("INSERT INTO obras.t_suscripcion_ia_uso VALUES(10,date_trunc('month',CURRENT_TIMESTAMP AT TIME ZONE 'America/La_Paz')::date,499)")
        conn.commit()

        barrier = Barrier(2)
        def alta(_):
            c = connect(readonly=False)
            try:
                barrier.wait(timeout=10)
                with c.cursor() as cur:
                    cur.execute(f'INSERT INTO {schema}.t_usuario(id_empresa,id_rol) VALUES(9,3)')
                c.commit(); return True
            except Exception as exc:
                c.rollback()
                if 'SUSCRIPCION_CUPO' not in str(exc): raise
                return False
            finally: c.close()
        with ThreadPoolExecutor(max_workers=2) as executor:
            assert sorted(executor.map(alta,range(2))) == [False,True]
        pruebas += 1

        # Ejecutar el repositorio real, sustituyendo exclusivamente el esquema/conexión.
        from app.repos import suscripcion_repos as repo
        class CursorAislado:
            def __init__(self, cursor): self.cursor=cursor
            def execute(self, sql, params=None): return self.cursor.execute(sql.replace('obras.',schema+'.'),params)
            def __getattr__(self, name): return getattr(self.cursor,name)
        @contextmanager
        def aislada():
            c=connect(readonly=False)
            try:
                with c.cursor(cursor_factory=RealDictCursor) as cur: yield CursorAislado(cur)
                c.commit()
            finally: c.rollback(); c.close()
        repo.conexion=aislada
        with conn.cursor() as cur:
            cur.execute("SELECT date_trunc('month',CURRENT_TIMESTAMP AT TIME ZONE 'America/La_Paz')::date")
            mes=cur.fetchone()[0]
        barrier = Barrier(2)
        def reservar(_):
            barrier.wait(timeout=10)
            return repo.reservar_ia(10,mes)
        with ThreadPoolExecutor(max_workers=2) as executor:
            assert sorted(executor.map(reservar,range(2))) == [False,True]
        pruebas += 1
        repo.liberar_ia(10,mes)
        assert repo.reservar_ia(10,mes); pruebas += 1
        with conn.cursor() as cur:
            cur.execute(f'SELECT consultas FROM {schema}.t_suscripcion_ia_uso WHERE id_empresa=10')
            assert cur.fetchone()[0]==500
        from app.services import planes_services
        from app.repos import planes_repos
        planes_repos.transaccion=aislada
        token={'nro_usuario':None,'nombre_rol':'ADMINISTRADOR'}
        with aislada() as cur: actual=planes_repos.obtener(cur,'BASICO')
        campos=('version','nombre','descripcion','modulos','limite_usuarios','limite_obras','consultas_ia_mes','nivel_reportes','exportar_reportes','automatizar_reportes')
        cambio={k:actual[k] for k in campos}
        cambio['modulos']=[m for m in cambio['modulos'] if m!='crm']
        cambio['limite_usuarios']=7
        preview=planes_services.configurar(token,'BASICO',cambio)
        nuevo=planes_services.configurar(token,'BASICO',cambio,preview['confirmacion'])
        assert nuevo['version']==2 and 'crm' not in nuevo['modulos']
        with aislada() as cur:
            cur.execute(f"SELECT version,antes,despues,empresas_afectadas FROM {schema}.t_plan_suscripcion_historial WHERE codigo_plan='BASICO'")
            evento=cur.fetchone()
            assert evento['version']==2 and evento['antes']['limite_usuarios']==5 and evento['despues']['limite_usuarios']==7
            assert evento['empresas_afectadas']
        # Reaplicar el SQL antiguo de restricciones no puede reponer límites configurados.
        with aislada() as cur:
            sql=(Path(__file__).parent / 'database/20261024_restricciones_suscripciones.sql').read_text(encoding='utf-8')
            cur.execute(sql)
            assert planes_repos.obtener(cur,'BASICO')['limite_usuarios']==7
            cur.execute((Path(__file__).parent / 'database/20261024_configuracion_planes.sql').read_text(encoding='utf-8'))
            assert 'crm' not in planes_repos.obtener(cur,'BASICO')['modulos']
        pruebas += 3
        cambio['version']=2
        cambio['limite_obras']=9
        preview=planes_services.configurar(token,'BASICO',cambio)
        try:
            planes_services.configurar({**token,'nro_usuario':-999999},'BASICO',cambio,preview['confirmacion'])
        except Exception as exc:
            if 'foreign key' not in str(exc): raise
        else: raise AssertionError('El fallo de auditoría debe revertir la edición')
        with aislada() as cur:
            assert planes_repos.obtener(cur,'BASICO')['version']==2
            assert planes_repos.obtener(cur,'BASICO')['limite_obras']==2
        pruebas += 1
        print(f'{pruebas} comprobaciones PostgreSQL correctas: cupos, reactivación, transferencia, downgrade, gracia, identidad técnica y concurrencia de altas/IA.')
    finally:
        conn.rollback()
        if creado:
            with conn.cursor() as cur: cur.execute(f'DROP SCHEMA {schema} CASCADE')
            conn.commit()
            print('Esquema aislado de prueba eliminado; datos de negocio intactos.')
        conn.close()


if __name__ == '__main__': main()
