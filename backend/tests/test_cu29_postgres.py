"""Integración CU29 contra PostgreSQL local desechable, con servicios/repos reales.

Ejecutar con tests/cu29_postgres_check.py. Sin destino explícito, se omite.
El esquema se copia sin datos desde PostgreSQL; todos los actores son sintéticos.
"""
import json
import os
from datetime import date
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from psycopg2 import sql
from psycopg2.extras import Json

from cu29_postgres_check import connect_test
from app.classes.postgres import PostgreSQL
from app.config import Config
from app.repos import reportes_repos as repo
from app.services import material_services
from app.services.ai import assistant_operations as operations, assistant_service as assistant
from app.services.ai.assistant_analysis import analizar_salud_operativa
from app.services.ai import assistant_analysis
from app.routes.ai_routes import router
from app.utils.security import create_access_token
from app.services.planes_catalog import MODULOS
from app.services.reportes.authorization import context
from app.services.reportes.contracts import AssistantRequest


PERMISSIONS = ['Visualizar_reportes', 'Visualizar_obras', 'Visualizar_incidencias',
               'Visualizar_ordenes_trabajo', 'Visualizar_inventario', 'Visualizar_materiales',
               'Visualizar_consultas_tecnicas', 'Visualizar_proveedores', 'Visualizar_control_costos',
               'Visualizar_clientes', 'Visualizar_usuarios', 'Registrar_incidencias',
               'Registrar_ordenes_trabajo', 'Registrar_materiales', 'Visualizar_ordenes_compra',
               'Aprobar_ordenes_compra', 'Registrar_usuarios']
TOKEN = dict(nro_usuario=99, id_empresa=5, nombre_rol='ADMINISTRADOR_EMPRESA')


@pytest.fixture
def pg(monkeypatch):
    configured = os.environ.get('CU29_TEST_SETTINGS')
    if not configured:
        pytest.skip('Requiere PostgreSQL desechable designado mediante cu29_postgres_check.py')
    settings = json.loads(configured)
    connection = connect_test(settings)
    connection.autocommit = True
    for name, value in dict(DB_HOST=settings['host'], DB_PORT=str(settings['port']),
                            DB_USER=settings['user'], DB_PASSWORD='', DB_NAME=settings['dbname'],
                            TOKEN_KEY='cu29-local-test-signing-key-with-sufficient-length',
                            DEEPSEEK_API_KEY='', GEMINI_API_KEY='', AI_PROVIDER='deepseek').items():
        monkeypatch.setattr(Config, name, value)
    monkeypatch.setenv('BACKUP_ENABLED', 'false')
    if PostgreSQL._pool:
        PostgreSQL._pool.closeall()
    PostgreSQL._pool = None
    with connection.cursor() as cursor:
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='obras'")
        tables = [sql.Identifier('obras', row[0]) for row in cursor.fetchall()]
        cursor.execute(sql.SQL('TRUNCATE {} RESTART IDENTITY CASCADE').format(sql.SQL(',').join(tables)))
        for order, code in enumerate(['BASICO', 'PROFESIONAL', 'EMPRESARIAL'], 1):
            cursor.execute('''INSERT INTO obras.t_plan_suscripcion
                (codigo,nombre,descripcion,prestaciones,orden,limite_usuarios,limite_obras,
                 consultas_ia_mes,nivel_reportes,exportar_reportes,automatizar_reportes,modulos)
                VALUES(%s,%s,'Plan sintético','[]',%s,100,100,500,'TODOS',true,true,%s)''',
                           (code, code, order, Json(list(MODULOS))))
        cursor.execute("INSERT INTO obras.t_empresa(id_empresa,nombre_empresa) VALUES(5,'Empresa de prueba A'),(6,'Empresa de prueba B')")
        cursor.execute("UPDATE obras.t_suscripcion_empresa SET codigo_plan='EMPRESARIAL'")
        cursor.execute("INSERT INTO obras.t_modulo(id_modulo,nombre_modulo) VALUES(1,'Pruebas')")
        cursor.execute("INSERT INTO obras.t_rol(id_rol,nombre_rol) VALUES(1,'ADMINISTRADOR'),(2,'CLIENTE'),(3,'ADMINISTRADOR_EMPRESA'),(4,'JEFE DE OBRA'),(5,'ELECTRICO')")
        for permission in PERMISSIONS:
            cursor.execute('INSERT INTO obras.t_permiso(nombre_permiso,id_modulo) VALUES(%s,1)', (permission,))
        cursor.execute('INSERT INTO obras.t_rol_permiso SELECT 3,id_permiso FROM obras.t_permiso')
        cursor.execute("INSERT INTO obras.t_rol_permiso SELECT 5,id_permiso FROM obras.t_permiso WHERE nombre_permiso IN ('Visualizar_incidencias','Visualizar_ordenes_trabajo','Visualizar_reportes')")
        cursor.execute('INSERT INTO obras.t_rol_permiso SELECT 4,id_permiso FROM obras.t_permiso')
        cursor.execute("INSERT INTO obras.t_rol_permiso SELECT 2,id_permiso FROM obras.t_permiso WHERE nombre_permiso='Visualizar_reportes'")
        for uid, company, role in [(1, 5, 1), (99, 5, 3), (199, 6, 3), (77, 5, 5), (88, 5, 4), (55, 5, 2)]:
            cursor.execute('INSERT INTO obras.t_persona(id_persona,nombre_completo,ci) VALUES(%s,%s,%s)',
                           (uid, f'Actor sintético {uid}', f'TEST-{uid}'))
            cursor.execute('INSERT INTO obras.t_usuario(id_usuario,username,correo,id_empresa,id_persona,id_rol,estado) VALUES(%s,%s,%s,%s,%s,%s,%s)',
                           (uid, f'test_{uid}', f'test{uid}@example.test', company, uid, role, 'ACTIVO'))
        cursor.execute("INSERT INTO obras.t_obra(id_obra,id_empresa,codigo,nombre,estado_obra) VALUES(12,5,'ALFA','Obra Alfa','EN_PROCESO'),(13,5,'BETA','Obra Beta','EN_PROCESO'),(22,6,'OTRA','Obra de otra empresa','EN_PROCESO')")
        cursor.execute('INSERT INTO obras.t_obra_usuario(id_obra,id_usuario) VALUES(12,77),(12,88)')
        cursor.execute("INSERT INTO obras.t_categoria_material(id_categoria,nombre,estado) VALUES(1,'Categoría sintética','ACTIVO')")
        cursor.execute("INSERT INTO obras.t_unidad_medida(id_unidad_medida,nombre,abreviatura,estado) VALUES(1,'Unidad','u','ACTIVO')")
    if hasattr(operations, '_propuestas'):
        operations._propuestas.clear()
    try:
        yield connection
    finally:
        if PostgreSQL._pool:
            PostgreSQL._pool.closeall()
        PostgreSQL._pool = None
        connection.close()


def actor(uid=99, company=5):
    with repo.transaction(snapshot=True) as db:
        return context(db, uid, company)


def scalar(pg, query, params=()):
    with pg.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchone()[0]


def sql_write(pg, query, params=()):
    with pg.cursor() as cursor:
        cursor.execute(query, params)


def client_for(uid=99, company=5, role='ADMINISTRADOR_EMPRESA'):
    app = FastAPI()
    app.include_router(router, prefix='/api/ai')
    token = create_access_token(uid, f'test_{uid}', role, company, 'Pruebas', 'Actor sintético', None)
    return TestClient(app, headers={'Authorization': 'Bearer ' + token}, raise_server_exceptions=False)


@pytest.mark.parametrize('kind,params,key,table', [
    ('crear_incidencia', dict(id_obra=12,titulo='Incidencia de prueba'), 'id_incidencia', 't_incidencia'),
    ('crear_orden_trabajo', dict(id_obra=12,tipo_trab='Trabajo de prueba'), 'orden_nro', 't_orden_trabajo'),
])
def test_stage1_operaciones_context_real(pg, kind, params, key, table):
    ctx = actor()
    assert not hasattr(ctx, 'obras_autorizadas')
    proposal = operations.proponer_operacion(ctx, kind, params)
    response = operations.ejecutar_propuesta(TOKEN, proposal['id_propuesta'])
    assert response['success'] and response['resultado'][key]
    assert scalar(pg, f'SELECT count(*) FROM obras.{table}') == 1


def test_stage1_conversacion_valida_continua(pg):
    request = AssistantRequest(texto='¿Qué módulos tengo disponibles?')
    first = assistant.consult(TOKEN, request, 5)
    second = assistant.consult(TOKEN, request.model_copy(update={'conversacion':first['conversacion']}), 5)
    assert second['conversacion'] == first['conversacion']
    assert scalar(pg, 'SELECT count(*) FROM obras.t_asistente_mensaje') == 2


def test_stage1_sql_trabajador_y_filas_reales(pg):
    with pg.cursor() as cursor:
        for uid, title in [(77, 'Incidencia propia'), (99, 'Incidencia ajena')]:
            cursor.execute("INSERT INTO obras.t_incidencia(id_obra,id_usuario_registro,titulo,descripcion,prioridad) VALUES(12,%s,%s,'Prueba','CRITICA')", (uid,title))
    with repo.transaction(snapshot=True) as db:
        result = analizar_salud_operativa(db, context(db,77,5), 12)
    assert result['indicadores'][0]['valor'] == 1
    assert 'Incidencia ajena' not in str(result)


def test_stage1_stock_cero_si_genera_alerta(pg):
    material_services.registrar(dict(codigo='TEST-CERO',nombre_material='Material agotado',
                                    id_categoria=1,id_unidad_medida=1,precio='10'), TOKEN)
    with repo.transaction(snapshot=True) as db:
        result = analizar_salud_operativa(db, context(db,99,5), 12)
    assert any(item['codigo']=='STOCK_AGOTADO' and item['valor']==1 for item in result['indicadores'])


@pytest.mark.parametrize('kind,module,params,table', [
    ('crear_material','materiales',dict(codigo='MAT',nombre_material='Material'),'t_material'),
    ('crear_incidencia','incidencias',dict(id_obra=12,titulo='Prueba incidencia'),'t_incidencia'),
    ('crear_orden_trabajo','ordenes_trabajo',dict(id_obra=12,tipo_trab='Prueba OT'),'t_orden_trabajo'),
])
def test_stage2_modulo_retirado_impide_confirmacion(pg,kind,module,params,table):
    proposal = operations.proponer_operacion(actor(),kind,params)
    sql_write(pg,"UPDATE obras.t_plan_suscripcion SET modulos=modulos-%s WHERE codigo='EMPRESARIAL'",(module,))
    response = client_for().post('/api/ai/operacion/confirmar?id_empresa=5',json={'id_propuesta':proposal['id_propuesta']})
    assert response.status_code == 403, response.text
    assert scalar(pg, f'SELECT count(*) FROM obras.{table}') == 0


def test_stage2_permiso_revocado_y_plan_suspendido(pg):
    proposal = operations.proponer_operacion(actor(),'crear_incidencia',dict(id_obra=12,titulo='Prueba incidencia'))
    sql_write(pg,"DELETE FROM obras.t_rol_permiso WHERE id_rol=3 AND id_permiso IN (SELECT id_permiso FROM obras.t_permiso WHERE nombre_permiso='Registrar_incidencias')")
    response = client_for().post('/api/ai/operacion/confirmar?id_empresa=5',json={'id_propuesta':proposal['id_propuesta']})
    assert response.status_code == 403
    assert scalar(pg,'SELECT count(*) FROM obras.t_incidencia') == 0
    sql_write(pg,"UPDATE obras.t_suscripcion_empresa SET estado='SUSPENDIDA' WHERE id_empresa=5")
    with pytest.raises(HTTPException) as error:
        operations.ejecutar_propuesta(TOKEN,proposal['id_propuesta'])
    assert error.value.status_code == 403


def test_stage2_ticket_empresa_y_obra_no_cambian(pg):
    proposal = operations.proponer_operacion(actor(),'crear_incidencia',dict(id_obra=12,titulo='Prueba'),id_obra_contexto=12)
    client = client_for()
    for action in ['confirmar','cancelar']:
        response = client.post(f'/api/ai/operacion/{action}?id_empresa=6&id_obra_contexto=12',json={'id_propuesta':proposal['id_propuesta']})
        assert response.status_code == 403
        response = client.post(f'/api/ai/operacion/{action}?id_empresa=5&id_obra_contexto=13',json={'id_propuesta':proposal['id_propuesta']})
        assert response.status_code == 409
    sql_write(pg,'UPDATE obras.t_usuario SET id_empresa=6 WHERE id_usuario=99')
    for action in ['confirmar','cancelar']:
        response = client_for(company=6).post(f'/api/ai/operacion/{action}?id_empresa=6&id_obra_contexto=12',json={'id_propuesta':proposal['id_propuesta']})
        assert response.status_code == 403
    assert scalar(pg,'SELECT count(*) FROM obras.t_incidencia') == 0


def test_stage2_global_debe_seleccionar_empresa_del_ticket(pg):
    proposal = operations.proponer_operacion(actor(1,5),'crear_incidencia',dict(id_obra=12,titulo='Prueba global'))
    client = client_for(1,5,'ADMINISTRADOR')
    for query,status in [('',422),('?id_empresa=6',403),('?id_empresa=5',200)]:
        response = client.post('/api/ai/operacion/confirmar'+query,json={'id_propuesta':proposal['id_propuesta']})
        assert response.status_code == status, response.text
    assert scalar(pg,'SELECT id_obra FROM obras.t_incidencia') == 12


def test_stage2_diagnostico_sin_permiso_y_revocacion_antes_de_devolver(pg,monkeypatch):
    sql_write(pg,"DELETE FROM obras.t_rol_permiso WHERE id_rol=3 AND id_permiso IN (SELECT id_permiso FROM obras.t_permiso WHERE nombre_permiso='Visualizar_inventario')")
    with repo.transaction(snapshot=True) as db:
        result=analizar_salud_operativa(db,context(db,99,5))
    assert 'inventario' not in result['fuentes_consultadas']
    sql_write(pg,"INSERT INTO obras.t_incidencia(id_obra,id_usuario_registro,titulo,descripcion,prioridad) VALUES(12,99,'Dato reservado','Prueba','CRITICA')")
    original=assistant_analysis.analizar_con_alcance
    def revoke_after_read(*args,**kwargs):
        result=original(*args,**kwargs)
        sql_write(pg,"DELETE FROM obras.t_rol_permiso WHERE id_rol=3 AND id_permiso IN (SELECT id_permiso FROM obras.t_permiso WHERE nombre_permiso='Visualizar_incidencias')")
        return result
    # El hook solo provoca una revocación REAL en otra conexión después de leer.
    monkeypatch.setattr(assistant_analysis,'analizar_con_alcance',revoke_after_read)
    response=client_for().post('/api/ai/consulta?id_empresa=5',json={'texto':'Analizar salud operativa'})
    assert response.status_code == 403
    assert 'Dato reservado' not in response.text
    assert scalar(pg,'SELECT count(*) FROM obras.t_asistente_mensaje') == 0


def test_stage2_conocimiento_filtra_procedimientos_y_plan(pg):
    from app.services.ai.knowledge_base import buscar_conocimiento
    sql_write(pg,"DELETE FROM obras.t_rol_permiso WHERE id_rol=3 AND id_permiso IN (SELECT id_permiso FROM obras.t_permiso WHERE nombre_permiso='Aprobar_ordenes_compra')")
    ctx=actor()
    result=buscar_conocimiento('Aprobación de orden de compra',ctx.rol,ctx.permisos,list(MODULOS))
    assert all(p['modulo'] != 'compras' for p in result.get('procedimientos', []))
    result=buscar_conocimiento('Módulos disponibles',ctx.rol,ctx.permisos,['ia'])
    assert '/compras' not in str(result)
    assert '/inventario' not in str(result)


def test_stage2_trabajador_pierde_registro_aunque_conserve_la_obra(pg):
    sql_write(pg,"INSERT INTO obras.t_incidencia(id_obra,id_usuario_registro,id_responsable,titulo,descripcion,prioridad) VALUES(12,99,77,'Asignada','Prueba','CRITICA')")
    with repo.transaction(snapshot=True) as db:
        _, scope=assistant_analysis.analizar_con_alcance(db,context(db,77,5),12)
    sql_write(pg,'UPDATE obras.t_incidencia SET id_responsable=99')
    with repo.transaction(snapshot=True) as db, pytest.raises(HTTPException) as error:
        assistant_analysis.reautorizar(db,context(db,77,5),scope)
    assert error.value.status_code == 403
