"""Inspección puntual, exclusivamente de lectura, de los planes configurados."""
from inspect_subscription_db import connect

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--verificar',action='store_true')
    args=parser.parse_args()
    conn=connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), to_regclass('obras.t_plan_suscripcion'), to_regclass('obras.t_plan_suscripcion_historial')")
            print('Objetos:',cur.fetchall())
            cur.execute("SELECT column_name,data_type FROM information_schema.columns WHERE table_schema='obras' AND table_name='t_plan_suscripcion' ORDER BY ordinal_position")
            print('Columnas:',cur.fetchall())
            cur.execute('SELECT codigo,nombre,limite_usuarios,limite_obras,consultas_ia_mes,nivel_reportes,exportar_reportes,automatizar_reportes FROM obras.t_plan_suscripcion ORDER BY orden')
            print('Planes:',cur.fetchall())
            cur.execute('SELECT codigo_plan,count(*) FROM obras.t_suscripcion_empresa GROUP BY codigo_plan')
            print('Empresas por plan:',cur.fetchall())
            if args.verificar:
                cur.execute('SELECT codigo,modulos,version FROM obras.t_plan_suscripcion ORDER BY orden')
                planes=cur.fetchall()
                assert all(version==1 for _,_,version in planes)
                assert all(('ia' in modulos)==(codigo=='EMPRESARIAL') for codigo,modulos,_ in planes)
                cur.execute('SELECT count(*) FROM obras.t_plan_suscripcion_historial')
                assert cur.fetchone()[0]==0
                print('Módulos y versiones iniciales conservados; historial sin cambios administrativos reales.')
        if args.verificar:
            from contextlib import contextmanager
            from psycopg2.extras import RealDictCursor
            from app.repos import planes_repos
            from app.services import planes_services
            @contextmanager
            def lectura():
                with conn.cursor(cursor_factory=RealDictCursor) as cur: yield cur
            planes_repos.transaccion=lectura
            with lectura() as cur: plan=planes_repos.obtener(cur,'BASICO')
            campos=('version','nombre','descripcion','modulos','limite_usuarios','limite_obras','consultas_ia_mes','nivel_reportes','exportar_reportes','automatizar_reportes')
            vista=planes_services.configurar({'nombre_rol':'ADMINISTRADOR'},'BASICO',{k:plan[k] for k in campos})
            assert vista['total_empresas']==1
            print('Previsualización real verificada en solo lectura:', vista['total_empresas'],'empresa(s),',len(vista['empresas_sobre_cupo']),'sobre cupo.')
    finally:
        conn.rollback();conn.close()
