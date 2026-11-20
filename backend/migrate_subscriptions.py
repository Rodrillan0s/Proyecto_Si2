"""Aplica exclusivamente suscripciones a una base explícitamente designada."""
import argparse
from pathlib import Path
from inspect_subscription_db import connect


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', required=True)
    parser.add_argument('--seed', action='store_true', help='Asignar planes a La Roca y El Gran Piraí si no tienen plan.')
    parser.add_argument('--restricciones', action='store_true', help='Aplicar cupos y capacidades de los tres planes.')
    parser.add_argument('--configuracion', action='store_true', help='Aplicar solo la edición de planes, sin reponer límites existentes.')
    args = parser.parse_args()
    if args.configuracion and (args.restricciones or args.seed):
        parser.error('--configuracion se ejecuta por separado para conservar capacidades actuales.')
    conn = connect(readonly=False)
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT current_database()')
            if cur.fetchone()[0] != args.database:
                raise RuntimeError('La base conectada no coincide con la designada.')
            cur.execute("SELECT pg_advisory_xact_lock(hashtext('obratec_suscripciones_20261024'))")
            if args.configuracion:
                cur.execute((Path(__file__).parent / 'database/20261024_configuracion_planes.sql').read_text(encoding='utf-8'))
            else:
                cur.execute((Path(__file__).parent / 'database/20261024_suscripciones_empresa.sql').read_text(encoding='utf-8'))
            if args.seed:
                for empresa, plan in [('CONSTRUCTORA LA ROCA', 'PROFESIONAL'), ('CONSTRUCTORA EL GRAN PIRAI', 'EMPRESARIAL')]:
                    cur.execute('''
                        INSERT INTO obras.t_suscripcion_empresa (id_empresa,codigo_plan,estado,fecha_inicio)
                        SELECT id_empresa,%s,'ACTIVA',(CURRENT_TIMESTAMP AT TIME ZONE 'America/La_Paz')::date
                        FROM obras.t_empresa WHERE nombre_empresa=%s
                        ON CONFLICT (id_empresa) DO NOTHING RETURNING id_empresa,codigo_plan,estado,fecha_inicio
                    ''', (plan, empresa))
                    for row in cur.fetchall():
                        cur.execute('''INSERT INTO obras.t_suscripcion_historial
                            (id_empresa,codigo_plan,estado,fecha_inicio,origen)
                            VALUES (%s,%s,%s,%s,'ASIGNACION_INICIAL')''', row)
            if args.restricciones:
                cur.execute((Path(__file__).parent / 'database/20261024_restricciones_suscripciones.sql').read_text(encoding='utf-8'))
            cur.execute('''SELECT e.nombre_empresa,p.nombre,s.estado,s.fecha_inicio,count(u.id_usuario)
                FROM obras.t_suscripcion_empresa s JOIN obras.t_empresa e USING(id_empresa)
                JOIN obras.t_plan_suscripcion p ON p.codigo=s.codigo_plan
                LEFT JOIN obras.t_usuario u ON u.id_empresa=e.id_empresa
                GROUP BY e.id_empresa,e.nombre_empresa,p.nombre,s.estado,s.fecha_inicio ORDER BY e.id_empresa''')
            resultado = cur.fetchall()
        conn.commit()
        print('Migración aplicada. Suscripciones:', resultado)
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
