"""Verifica API/SQL de suscripciones con conexión de solo lectura; no inicia el backend."""
from contextlib import contextmanager
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg2.extras import RealDictCursor
from inspect_subscription_db import connect
from app.repos import suscripcion_repos as repo
from app.routes.suscripcion_routes import router
from app.utils.security import verificar_token


def main():
    conn = connect(readonly=True)
    try:
        @contextmanager
        def lectura():
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                yield cur

        repo.conexion = lectura
        planes = repo.listar_planes()
        assert {p['codigo']:(p['limite_usuarios'],p['limite_obras'],p['consultas_ia_mes']) for p in planes} == {
            'BASICO':(5,2,0),'PROFESIONAL':(15,10,0),'EMPRESARIAL':(50,30,500)}
        with conn.cursor() as cur:
            cur.execute('''SELECT c.id_empresa,c.usuarios,c.obras,
                (SELECT count(*) FROM obras.t_usuario u LEFT JOIN obras.t_rol r USING(id_rol)
                 WHERE u.id_empresa=c.id_empresa AND u.estado='ACTIVO' AND r.nombre_rol IS DISTINCT FROM 'ADMINISTRADOR'),
                (SELECT count(*) FROM obras.t_obra o WHERE o.id_empresa=c.id_empresa
                 AND COALESCE(o.estado_obra,'') NOT IN ('FINALIZADO','CANCELADO','ARCHIVADO'))
                FROM obras.t_suscripcion_cupo c ORDER BY c.id_empresa''')
            for empresa,usuarios,obras,reales_u,reales_o in cur.fetchall():
                assert (usuarios,obras)==(reales_u,reales_o)
            cur.execute('SELECT COALESCE(sum(consultas),0) FROM obras.t_suscripcion_ia_uso')
            uso_inicial=cur.fetchone()[0]
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[verificar_token] = lambda: {'nombre_rol': 'ADMINISTRADOR', 'nro_usuario': 1}
        with TestClient(app) as client:
            res = client.get('/api/suscripciones/planes')
            assert res.status_code == 200 and len(res.json()['data']) == 3
            res = client.get('/api/suscripciones/empresas')
            assert res.status_code == 200
            activas = [s for s in res.json()['data'] if s['estado_efectivo'] == 'ACTIVA']
            assert {s['id_empresa'] for s in activas} >= {3, 4}
            for empresa in (3, 4):
                res = client.get(f'/api/suscripciones/empresas/{empresa}/historial')
                assert res.status_code == 200 and res.json()['data']
            with conn.cursor() as cur:
                cur.execute("SELECT id_usuario,id_empresa FROM obras.t_usuario WHERE id_empresa=3 AND estado='ACTIVO' ORDER BY id_usuario LIMIT 1")
                usuario, empresa = cur.fetchone()
            app.dependency_overrides[verificar_token] = lambda: {
                'nombre_rol': 'ADMINISTRADOR_EMPRESA', 'nro_usuario': usuario, 'id_empresa': empresa,
            }
            res = client.get('/api/suscripciones/mi-empresa')
            assert res.status_code == 200 and res.json()['data']['codigo_plan'] == 'PROFESIONAL'
            assert client.get('/api/suscripciones/mi-empresa?id_empresa=4').status_code == 403
            assert client.get('/api/suscripciones/empresas').status_code == 403
            assert client.put('/api/suscripciones/empresas/3', json={
                'codigo_plan': 'BASICO', 'fecha_inicio': '2026-10-24',
            }).status_code == 403
            from app.services import suscripcion_policy as policy, reportes_services as reports
            from app.services.reportes.contracts import AssistantRequest
            from fastapi import HTTPException
            from types import SimpleNamespace
            for empresa,codigo in ((1,'BASICO'),(3,'PROFESIONAL'),(4,'EMPRESARIAL')):
                plan=repo.obtener_politica(empresa)
                assert plan['codigo_plan']==codigo
                caps=policy.capacidades(plan)
                assert not caps['solo_lectura']
                assert caps['ia_habilitada']==(codigo=='EMPRESARIAL')
                ctx=SimpleNamespace(empresa=empresa,rol='ADMINISTRADOR_EMPRESA')
                if codigo=='BASICO':
                    try: policy.exigir_reporte(ctx,'saldo_comercial')
                    except HTTPException as exc: assert exc.status_code==403
                    else: raise AssertionError('El plan Básico no debe generar reportes financieros')
                print('Plan y consumos verificados:', empresa,codigo,plan['usuarios_activos'],plan['obras_activas'],plan['consultas_ia_usadas'])
            # Profesional se deniega antes de reservar cupo o llamar a proveedores.
            try: reports.assistant({'nro_usuario':usuario,'id_empresa':3,'nombre_rol':'ADMINISTRADOR_EMPRESA'},AssistantRequest(texto='stock'))
            except HTTPException as exc: assert exc.status_code==403
            else: raise AssertionError('Profesional no debe acceder a IA')
            with conn.cursor() as cur:
                cur.execute('SELECT COALESCE(sum(consultas),0) FROM obras.t_suscripcion_ia_uso')
                assert cur.fetchone()[0]==uso_inicial
            print('Capacidades, contadores e IA denegada comprobados en solo lectura; cero consumo de IA.')
            print('API y SQL verificados en solo lectura: tres planes, dos asignaciones, historial, aislamiento y gestión global.')
            print('Usuarios cubiertos:', sum(s['usuarios'] for s in activas if s['id_empresa'] in (3, 4)))
    finally:
        conn.rollback()
        conn.close()


if __name__ == '__main__':
    main()
