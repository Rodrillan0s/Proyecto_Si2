"""Comprobación explícita EXPLAIN de consultas, sin leer filas de negocio ni aplicar migraciones.

Ejecutar desde backend: python tests/reportes_sql_readonly_check.py
"""
import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import psycopg2
from app.config import Config
from app.repos import reportes_repos as repo
from app.services.reportes.authorization import Context
from app.services.reportes.catalog import REGISTRY
from app.services.reportes.contracts import ReportRequest


def main():
    queries = []
    def capture(db,sql,params=()):
        queries.append((sql,params))
        return []
    db = MagicMock()
    db.execute_query.side_effect=lambda sql,params,**kwargs: capture(db,sql,params)
    db.cur.description=[]
    with patch.object(repo,'rows',capture):
        repo.actor(db,0)
        repo.pending_purchases(db,0)
        repo.list_recipients(db,(0,))
        # Las consultas de instalación deben cubrir el historial y las programaciones.
        empty_id = '00000000-0000-0000-0000-000000000000'
        repo.list_executions(db,(0,0))
        repo.list_schedules(db,(0,False,0))
        repo.list_deliveries(db,(empty_id,))
        repo.get_execution(db,(empty_id,))
        repo.get_conversation(db,(empty_id,0,0))
        repo.conversation_inputs(db,(empty_id,))
        repo.get_file(db,(empty_id,))
    with patch.object(repo,'rows',capture),patch.object(repo,'one',return_value={'moneda':'BOB'}):
        for role in ('ADMINISTRADOR_EMPRESA','JEFE DE OBRA','CLIENTE','ALBAÑIL'):
            ctx = Context(0,0,role,0,frozenset(),None)
            repo.works(db,ctx)
            for kind in REGISTRY:
                if role=='ALBAÑIL' and kind not in {'asignacion_personal','utilizacion_personal','incidencias','incidencias_criticas'}:
                    continue
                request = ReportRequest(reporte=kind,filtros={'id_obra':1} if kind=='comparativo_costos' else {})
                repo.datasets(db,ctx,request,[0])
                if REGISTRY[kind].fecha:
                    dated = request.model_copy(update={'filtros': request.filtros.model_copy(update={
                        'desde': date(2026,1,1), 'hasta': date(2026,10,4)})})
                    repo.datasets(db,ctx,dated,[0])
    connection = psycopg2.connect(host=Config.DB_HOST,port=Config.DB_PORT,dbname=Config.DB_NAME,
        user=Config.DB_USER,password=Config.DB_PASSWORD,connect_timeout=10,
        options='-c default_transaction_read_only=on -c statement_timeout=15000')
    try:
        connection.set_session(readonly=True)
        with connection.cursor() as cursor:
            for sql,params in queries:
                cursor.execute('EXPLAIN '+sql,params)
        print(f'Consultas validadas mediante EXPLAIN de solo lectura: {len(queries)}')
    finally:
        connection.rollback()
        connection.close()


if __name__=='__main__':
    main()
