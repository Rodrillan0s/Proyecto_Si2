"""Inspección/instalación explícita CU39. Nunca inicia la aplicación ni workers.

python manage_cronogramas.py --check
python manage_cronogramas.py --apply --database obras
"""
import argparse
import json
import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parent
TABLES=('t_cronograma','t_cronograma_actividad','t_cronograma_dependencia')


def inspect(cur):
    cur.execute('SELECT current_database(),current_user,current_setting(\'transaction_read_only\')')
    target=cur.fetchone()
    cur.execute('''SELECT table_name,column_name,data_type,is_nullable FROM information_schema.columns
        WHERE table_schema='obras' AND table_name=ANY(%s) ORDER BY table_name,ordinal_position''',(list(TABLES),))
    columns=cur.fetchall()
    cur.execute('''SELECT c.relname,co.conname,pg_get_constraintdef(co.oid) FROM pg_constraint co
        JOIN pg_class c ON c.oid=co.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='obras' AND c.relname=ANY(%s) ORDER BY 1,2''',(list(TABLES),))
    constraints=cur.fetchall()
    cur.execute('''SELECT r.nombre_rol,p.nombre_permiso FROM obras.t_rol r
        JOIN obras.t_rol_permiso rp USING(id_rol) JOIN obras.t_permiso p USING(id_permiso)
        WHERE p.nombre_permiso LIKE '%%cronograma' ORDER BY 1,2''')
    permissions=cur.fetchall()
    cur.execute('''SELECT c.relname,has_table_privilege(c.oid,'SELECT')
        AND has_table_privilege(c.oid,'INSERT') AND has_table_privilege(c.oid,'UPDATE')
        AND has_table_privilege(c.oid,'DELETE')
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='obras' AND c.relname=ANY(%s)''',(list(TABLES),))
    privileges=cur.fetchall()
    return dict(database=target[0],actor=target[1],read_only=target[2],columns=columns,
                constraints=constraints,permissions=permissions,privileges=privileges)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check',action='store_true');mode.add_argument('--apply',action='store_true')
    parser.add_argument('--database',help='Destino requerido al aplicar; debe coincidir con DB_NAME')
    args=parser.parse_args()
    for path in (ROOT.parent/'.env',ROOT/'.env'):
        if path.exists(): load_dotenv(path,override=True)
    if args.apply and (not args.database or args.database != os.getenv('DB_NAME')):
        parser.error('--database debe identificar explícitamente la base configurada.')
    conn=psycopg2.connect(host=os.getenv('DB_HOST'),port=os.getenv('DB_PORT'),dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),password=os.getenv('DB_PASSWORD'),connect_timeout=10,
        options='-c statement_timeout=30000 -c lock_timeout=5000')
    try:
        conn.set_session(readonly=not args.apply)
        with conn.cursor() as cur:
            cur.execute('SELECT current_database()')
            if args.apply and cur.fetchone()[0] != args.database:
                raise RuntimeError('La base conectada no coincide con el destino explícito.')
            if args.apply:
                cur.execute("SELECT pg_advisory_xact_lock(hashtext('obratec-cu39-install'))")
                cur.execute((ROOT/'database/20261025_cu39_cronogramas.sql').read_text(encoding='utf-8'))
            result=inspect(cur)
            if args.apply:
                found={r[0] for r in result['columns']}
                if found != set(TABLES): raise RuntimeError('Instalación incompleta: se revierte la transacción.')
                if not all(r[1] for r in result['privileges']): raise RuntimeError('Privilegios incompletos: se revierte la transacción.')
                conn.commit()
            print(json.dumps(dict(applied=args.apply,**result),ensure_ascii=False,indent=2))
    finally:
        conn.rollback();conn.close()


if __name__=='__main__': main()
