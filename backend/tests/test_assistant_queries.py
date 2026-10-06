"""Consultas naturales/modulares aisladas: sin DB, IA, correo ni workers reales."""
import json
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from pydantic import ValidationError
from app.services.ai import query_engine as engine, assistant_service as assistant
from app.services.reportes.interpreter import interpret
from app.services.reportes.catalog import REGISTRY
from app.services.reportes.contracts import AssistantRequest
from app.repos import assistant_repos, reportes_repos as repo
from test_reportes import actor, fake_transaction


WORKS = [{'id_obra':9,'nombre':'Edificio Laguna','codigo':'LAG'},
         {'id_obra':10,'nombre':'Parque Residencial','codigo':'PAR'}]


class NaturalQueryTests(unittest.TestCase):
    def test_critical_supplies_and_typos_use_existing_stock(self):
        for text in ['Quiero reportes de insumos criticos', 'Quiero reporte de insumos que esten por agotarse',
                     'materiales critcos', 'materiales faltantes']:
            with self.subTest(text=text):
                result = interpret(text, list(REGISTRY), WORKS)
                self.assertEqual(result['estado'], 'ready')
                self.assertEqual(result['solicitud']['reporte'], 'stock')
                self.assertEqual(result['solicitud']['filtros'].get('estado'), 'STOCK_BAJO')

    def test_stock_never_inherits_a_work(self):
        for text in ['Stock de materiales Edificio Laguna', 'ahora Edificio Laguna']:
            result = interpret(text, list(REGISTRY), WORKS, {'reporte':'stock','filtros':{'id_obra':10}})
            self.assertEqual(result['estado'], 'ready')
            self.assertNotIn('id_obra', result['solicitud']['filtros'])

    def test_named_followup_overrides_previous_work(self):
        result = interpret('Edificio Laguna', list(REGISTRY), WORKS, {'reporte':'costos_periodo','filtros':{'id_obra':10}})
        self.assertEqual(result['solicitud']['filtros']['id_obra'],9)

    def test_provider_can_create_a_new_query_for_an_existing_domain(self):
        ctx = actor(permissions=['Visualizar_reportes','Visualizar_proveedores'])
        provider = MagicMock()
        provider.complete.return_value = json.dumps({'accion':'consulta','consultas':[{
            'fuente':'proveedores','condiciones':[{'campo':'estado','operador':'eq','valor':'ACTIVO'}],
            'metricas':[{'operacion':'count','nombre':'cantidad'}]}]})
        with patch.object(assistant,'get_provider',return_value=provider):
            result = assistant._plan('Cuantos proveedores activos hay', [], WORKS, None, None, False, engine.catalog(ctx))
        self.assertEqual(result.accion,'consulta')
        self.assertEqual(result.consultas[0].fuente,'proveedores')

    def test_unknown_and_unauthorized_sources_or_sql_are_rejected(self):
        provider = MagicMock()
        for query in [{'fuente':'backup_jobs'}, {'fuente':'proveedores'}, {'fuente':'incidencias','sql':'DELETE FROM usuarios'}]:
            provider.complete.return_value=json.dumps({'accion':'consulta','consultas':[query]})
            with patch.object(assistant,'get_provider',return_value=provider):
                result=assistant._plan('consulta especial',['incidencias'],WORKS,None,None,False,
                    [{'fuente':'incidencias','campos':[]}])
            self.assertEqual(result['estado'],'unsupported')


class QueryEngineTests(unittest.TestCase):
    def test_filters_compares_fields_and_ranks_numeric_stock(self):
        query=engine.Query(fuente='stock', condiciones=[{'campo':'stock_actual','operador':'lt','comparar_campo':'stock_minimo'}],
            campos=['nombre_material','stock_actual'],ordenar_por='stock_actual', limite=1)
        result=engine.evaluate(query,[{'nombre_material':'A','stock_actual':Decimal('10'),'stock_minimo':Decimal('20')},
            {'nombre_material':'B','stock_actual':Decimal('2'),'stock_minimo':Decimal('5')},
            {'nombre_material':'C','stock_actual':Decimal('100'),'stock_minimo':Decimal('20')}])
        self.assertEqual(result['filas'][0]['nombre_material'],'B')
        self.assertEqual(result['registros_filtrados'],2)
        self.assertFalse(result['detalle_completo'])

    def test_exact_decimal_aggregates_group_currency(self):
        query=engine.Query(fuente='costos_periodo',agrupar_por=['moneda'],metricas=[{'operacion':'sum','campo':'monto','nombre':'total'}])
        result=engine.evaluate(query,[{'moneda':'BOB','monto':Decimal('.10')},{'moneda':'BOB','monto':Decimal('.20')},{'moneda':'USD','monto':Decimal('5')}])
        self.assertEqual(result['filas'],[{'moneda':'BOB','total':Decimal('.30')},{'moneda':'USD','total':Decimal('5')}])

    def test_mixed_currencies_and_budget_versions_cannot_be_summed(self):
        for source, column in [('costos_periodo','monto'),('presupuestario','monto_total')]:
            with self.assertRaises(HTTPException):
                engine.validate(engine.Query(fuente=source,metricas=[{'operacion':'sum','campo':column,'nombre':'total'}]))

    def test_unknown_fields_and_aliases_rejected_even_without_rows(self):
        for data in [{'campos':['password']},{'condiciones':[{'campo':'id_empresa','operador':'eq','valor':8}]},
                     {'metricas':[{'operacion':'count','nombre':'estado'}]}]:
            with self.assertRaises(HTTPException):
                engine.evaluate(engine.Query(fuente='proveedores',**data),[])

    def test_count_distinct_empty_count_and_nulls(self):
        result=engine.evaluate(engine.Query(fuente='proveedores',metricas=[{'operacion':'count','nombre':'cantidad'}]),[])
        self.assertEqual(result['filas'],[{'cantidad':0}])
        result=engine.evaluate(engine.Query(fuente='utilizacion_personal',metricas=[{'operacion':'count_distinct','campo':'id_usuario','nombre':'personas'}]),
            [{'id_usuario':1},{'id_usuario':1},{'id_usuario':2},{'id_usuario':None}])
        self.assertEqual(result['filas'][0]['personas'],2)

    def test_limits_nan_and_schema_rejection(self):
        with self.assertRaises(ValidationError): engine.Query(fuente='stock', limite=10000)
        with self.assertRaises(HTTPException): engine.decimal('NaN')
        with self.assertRaises(HTTPException): engine.evaluate(engine.Query(fuente='stock'),[{}]*20001)
        with self.assertRaises(HTTPException),patch.object(repo,'rows',return_value=[]):
            assistant_repos.read_module(None,actor(),engine.Query(fuente='proveedores'))

    def test_access_catalog_respects_domains_and_actor_scope(self):
        self.assertNotIn('proveedores',[s['fuente'] for s in engine.catalog(actor())])
        self.assertNotIn('stock',[s['fuente'] for s in engine.catalog(actor('CLIENTE'))])
        self.assertNotIn('crm_clientes',[s['fuente'] for s in engine.catalog(actor('CLIENTE',['Visualizar_clientes']))])
        self.assertIn('proveedores',[s['fuente'] for s in engine.catalog(actor(permissions=['Visualizar_proveedores']))])
        self.assertNotIn('password',engine.fields('usuarios'))
        self.assertNotIn('correo',engine.fields('usuarios'))
        self.assertNotIn('email',engine.fields('crm_clientes'))

    def test_module_sql_has_bound_tenant_and_authorized_works(self):
        for source in ['proveedores','obras','ordenes_trabajo']:
            columns=engine.MODULES[source][2].split()+['id_empresa']
            with patch.object(repo,'rows',side_effect=[[{'column_name':c} for c in columns],[]]) as read,patch.object(repo,'works',return_value=WORKS):
                assistant_repos.read_module(None,actor(),engine.Query(fuente=source))
                sql,params=read.call_args.args[1:]
                self.assertIn('id_empresa=%s',sql)
                self.assertEqual(params[0],7)
                self.assertNotIn('=7',sql)
                if source!='proveedores': self.assertIn([9,10],params)

    def test_foreign_work_rejected_before_business_query(self):
        with patch.object(repo,'rows',return_value=[{'column_name':c} for c in engine.MODULES['obras'][2].split()+['id_empresa']]) as read,patch.object(repo,'works',return_value=WORKS):
            with self.assertRaises(HTTPException) as error:
                assistant_repos.read_module(None,actor(),engine.Query(fuente='obras',filtros_fuente={'id_obra':999}))
            self.assertEqual(error.exception.status_code,403)
            self.assertEqual(read.call_count,1)

    def test_revoked_permission_blocks_results(self):
        with self.assertRaises(HTTPException):
            engine.reauthorize(None,actor(),[(engine.Query(fuente='proveedores'),[])])

    def test_lookup_reuses_reads_and_never_multiplies_rows(self):
        ctx=actor(permissions=['Visualizar_materiales','Visualizar_proveedores'])
        query=engine.Query(fuente='materiales',cruces=[{'fuente':'proveedores','campo':'id_proveedor','clave':'id_proveedor','prefijo':'proveedor'}],
            campos=['nombre_material','proveedor_nombre'])
        material=[{'id_material':1,'id_proveedor':5,'nombre_material':'Cemento'}]
        supplier=[{'id_proveedor':5,'nombre':'Acme'}]
        with patch.object(assistant_repos,'read_module',side_effect=[(material,[]),(supplier,[])]) as read:
            result, scopes=engine.execute(None,ctx,[query,query])
        self.assertEqual(read.call_count,2)
        self.assertEqual(result[0]['filas'],[{'nombre_material':'Cemento','proveedor_nombre':'Acme'}])
        self.assertEqual(len(scopes),4)
        with patch.object(assistant_repos,'read_module',side_effect=[(material,[]),(supplier+supplier,[])]):
            with self.assertRaises(HTTPException): engine.execute(None,ctx,[query])

    def test_lookup_requires_both_permissions_and_safe_relationship(self):
        query=engine.Query(fuente='materiales',cruces=[{'fuente':'proveedores','campo':'id_proveedor','clave':'id_proveedor','prefijo':'p'}])
        with patch.object(assistant_repos,'read_module',return_value=([],[])):
            with self.assertRaises(HTTPException) as error:
                engine.execute(None,actor(permissions=['Visualizar_materiales']),[query])
        self.assertEqual(error.exception.status_code,403)
        with self.assertRaises(HTTPException):
            engine.validate(engine.Query(fuente='materiales',cruces=[{'fuente':'proveedores','campo':'id_material','clave':'id_proveedor','prefijo':'p'}]))

    def test_quantities_require_material_or_unit_group(self):
        with self.assertRaises(HTTPException):
            engine.validate(engine.Query(fuente='stock',metricas=[{'operacion':'sum','campo':'stock_actual','nombre':'total'}]))

    def test_unknown_currency_and_mixed_currency_ranking_do_not_invent_totals(self):
        with self.assertRaises(HTTPException):
            engine.validate(engine.Query(fuente='compras',metricas=[{'operacion':'sum','campo':'total','nombre':'importe'}]))
        with self.assertRaises(HTTPException):
            engine.evaluate(engine.Query(fuente='costos_periodo',ordenar_por='monto'),
                            [{'moneda':'BOB','monto':Decimal(10)},{'moneda':'USD','monto':Decimal(2)}])

    def test_payload_is_bounded(self):
        with self.assertRaises(HTTPException):
            engine.evaluate(engine.Query(fuente='proveedores'),[{'nombre':'x'*200001}])

    def test_joined_money_has_the_currency_of_its_own_source(self):
        with self.assertRaises(HTTPException):
            engine.validate(engine.Query(fuente='obras',cruces=[{'fuente':'apu','campo':'id_obra','clave':'id_obra','prefijo':'m'}],
                metricas=[{'operacion':'sum','campo':'m_precio_unitario_final','nombre':'importe'}],agrupar_por=['moneda']))

    def test_pending_report_can_receive_an_explicit_work(self):
        result=interpret('Edificio Laguna',list(REGISTRY),WORKS,{'reporte':'comparativo_costos','filtros':{}})
        self.assertEqual(result['estado'],'ready')
        self.assertEqual(result['solicitud']['filtros']['id_obra'],9)


class CoordinatorTests(unittest.TestCase):
    def test_explicit_work_overrides_navigation_and_model_guess(self):
        ctx=actor(permissions=['Visualizar_obras'])
        plan=assistant.ReadPlan(accion='consulta',consultas=[engine.Query(fuente='obras',filtros_fuente={'id_obra':10})])
        with patch.object(repo,'transaction',fake_transaction),patch.object(assistant,'context',return_value=ctx), \
             patch.object(repo,'works',return_value=WORKS),patch.object(assistant,'_plan',return_value=plan), \
             patch.object(assistant,'_consult_dynamic',return_value=({'estado':'ready','mensaje':'Listo'},[])),patch.object(repo,'add_message'):
            assistant.consult({'nro_usuario':1},AssistantRequest(texto='Obras Edificio Laguna',id_obra_contexto=10),7)
        self.assertEqual(plan.consultas[0].filtros_fuente.id_obra,9)

    def test_missing_baseline_or_large_source_asks_to_refine_without_false_results(self):
        with patch.object(repo,'transaction',fake_transaction),patch.object(assistant,'context',return_value=actor()), \
             patch.object(engine,'execute',side_effect=HTTPException(422,'Acota la fuente')),patch.object(assistant,'get_provider') as provider:
            response,scopes=assistant._consult_dynamic(actor(),assistant.ReadPlan(accion='consulta',consultas=[engine.Query(fuente='stock')]),'consulta')
        self.assertEqual(response['estado'],'needs_clarification')
        self.assertNotIn('resultados_consulta',response)
        self.assertEqual(scopes,[])
        provider.assert_not_called()

    def test_dynamic_query_is_executed_and_reauthorized_without_persisting_rows(self):
        ctx=actor(permissions=['Visualizar_proveedores'])
        plan=assistant.ReadPlan(accion='consulta',consultas=[engine.Query(fuente='proveedores')])
        results=[{'fuente':'proveedores','registros_filtrados':1,'filas':[{'nombre':'Acme'}],'detalle_completo':True}]
        provider=MagicMock(); provider.complete.return_value='Acme'
        with patch.object(repo,'transaction',fake_transaction),patch.object(assistant,'context',return_value=ctx), \
             patch.object(repo,'works',return_value=WORKS),patch.object(assistant,'_plan',return_value=plan), \
             patch.object(engine,'execute',return_value=(results,[(plan.consultas[0],[])])), \
             patch.object(engine,'reauthorize') as reauth,patch.object(assistant,'get_provider',return_value=provider), \
             patch.object(repo,'add_message') as save:
            result=assistant.consult({'nro_usuario':1},AssistantRequest(texto='proveedores'),7)
        self.assertEqual(result['respuesta'],'Acme')
        self.assertEqual(reauth.call_count,2)
        self.assertNotIn('Acme',str(save.call_args))


if __name__=='__main__': unittest.main()
