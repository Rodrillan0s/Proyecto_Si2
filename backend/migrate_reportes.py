"""Revisión por defecto; aplicación solo con --apply. No se ejecuta desde la API."""
import argparse
import hashlib
from pathlib import Path
import psycopg2
from app.config import Config

TABLES = ('t_reporte_programacion','t_reporte_programacion_destinatario','t_reporte_ejecucion',
          't_reporte_archivo','t_reporte_envio','t_asistente_conversacion','t_asistente_mensaje')
PRECONDITIONS = {'t_usuario':{'id_usuario','id_empresa','id_persona','estado'},
    't_empresa':{'id_empresa'},'t_rol':{'id_rol','nombre_rol'},'t_permiso':{'id_permiso','nombre_permiso','id_modulo'},
    't_modulo':{'id_modulo','nombre_modulo'},'t_rol_permiso':{'id_rol','id_permiso'},
    't_estimacion':{'id_estimacion','id_empresa','id_obra'},'t_control_costo_obra':{'id_control_costo','id_empresa','id_obra'},
    't_costo_ejecutado':{'id_partida_presupuestaria','id_control_costo','monto'},
    't_detalle_obra':{'id_cliente','id_obra'},'t_orden_compra_detalle':{'cantidad_recibida','cantidad_solicitada'}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true',help='Aplicar la migración al entorno configurado.')
    args = parser.parse_args()
    path = Path(__file__).parent/'database'/'20261004_reportes.sql'
    sql = path.read_text(encoding='utf-8')
    connection = psycopg2.connect(host=Config.DB_HOST,port=Config.DB_PORT,dbname=Config.DB_NAME,
        user=Config.DB_USER,password=Config.DB_PASSWORD,connect_timeout=10,
        options='-c statement_timeout=60000'+('' if args.apply else ' -c default_transaction_read_only=on'))
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT table_name,column_name FROM information_schema.columns WHERE table_schema='obras'")
            columns = {}
            for table,column in cursor.fetchall(): columns.setdefault(table,set()).add(column)
            for table,required in PRECONDITIONS.items():
                if not required.issubset(columns.get(table,set())):
                    raise RuntimeError('El esquema no cumple la precondición: '+table)
            missing = [table for table in TABLES if table not in columns]
            print('Base configurada:',Config.DB_NAME)
            print('SHA256 migración:',hashlib.sha256(sql.encode()).hexdigest())
            print('Tablas de Reportes pendientes:', ', '.join(missing) or 'ninguna')
            if args.apply:
                connection.rollback()
                connection.autocommit=True
                cursor.execute(sql)
                print('Migración aplicada. Revisar permisos y luego activar el worker.')
            else:
                print('Revisión de solo lectura. No se aplicaron cambios.')
    finally:
        connection.rollback()
        connection.close()


if __name__=='__main__':
    main()
