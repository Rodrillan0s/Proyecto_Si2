"""Pruebas unitarias aisladas para el Motor Semántico Compartido, Orquestador IA,
ContextManager (6 compartimentos), Bandeja Proactiva y VisionExtractor honesto.
"""
import json
import struct
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException

from app.services.reportes import authorization as auth
from app.services.reportes.authorization import Context
from app.services.semantic import catalog, compiler, executor
from app.services.semantic.contracts import (
    CrossModuleSpec,
    ReportSpecPatch,
    SemanticFilter,
    SemanticMetric,
    SemanticQuerySpec,
    TimeConfig,
)
from app.services.ai import context_manager, orchestrator, vision_extractor
from app.services.ai.proactive_inbox_service import consultar_pendientes


def _ctx(rol='ADMINISTRADOR_EMPRESA', empresa=10, usuario=5, persona=50, permisos=()):
    return Context(
        usuario=usuario,
        empresa=empresa,
        rol=rol,
        persona=persona,
        permisos=frozenset(permisos),
        correo='test@obratec.bo',
    )


class TestCentralizedAuthorization:
    def test_cliente_only_sees_allowed_entities_and_tools(self):
        ctx = _ctx(rol='CLIENTE', permisos=('Visualizar_avances',))
        ents = auth.authorized_entities(ctx)
        assert 'unidades' in ents
        assert 'garantias' in ents
        assert 'posventa' in ents
        assert 'costos_ejecutados' not in ents
        assert 'compras' not in ents
        assert auth.authorize_tool(ctx, 'recomendar_inmuebles') is True
        assert auth.authorize_tool(ctx, 'consultar_pendientes') is True
        assert auth.authorize_tool(ctx, 'analizar_cruce_obras') is False
        assert auth.authorize_tool(ctx, 'ejecutar_diagnostico_operativo') is False

    def test_worker_cannot_access_financial_entities(self):
        ctx = _ctx(rol='ALBAÑIL', permisos=('Visualizar_incidencias', 'Visualizar_obras'))
        ents = auth.authorized_entities(ctx)
        assert 'incidencias' in ents
        assert 'ordenes_trabajo' in ents
        assert 'costos_ejecutados' not in ents
        assert 'estimaciones' not in ents
        assert auth.authorize_tool(ctx, 'analizar_cruce_obras') is False


class TestSemanticCompilerSecurityAndRules:
    def test_injects_tenant_work_scope_and_rls_for_worker(self):
        ctx = _ctx(rol='ALBAÑIL', empresa=7, usuario=99, permisos=('Visualizar_incidencias',))
        ent = catalog.get_entity('incidencias')
        spec = SemanticQuerySpec(
            entidad='incidencias',
            filtros=[SemanticFilter(campo='prioridad', operador='eq', valor='CRITICA')],
        )
        sql, params, cols, _, tipo = compiler.compile_semantic_query(ctx, ent, [11, 12], spec)
        assert 'o.id_empresa = %s' in sql
        assert 'i.id_obra = ANY(%s)' in sql
        assert '(i.id_usuario_registro = %s OR i.id_responsable = %s)' in sql
        assert params[0] == 7
        assert params[1] == [11, 12]
        assert params[2] == 99 and params[3] == 99
        assert params[4] == 'CRITICA'
        assert tipo == 'tabular'

    def test_rejects_sql_injection_in_field_names(self):
        ctx = _ctx(permisos=('Visualizar_incidencias',))
        ent = catalog.get_entity('incidencias')
        spec = SemanticQuerySpec(
            entidad='incidencias',
            campos=['titulo; DROP TABLE obras.t_obra; --'],
        )
        with pytest.raises(HTTPException) as exc:
            compiler.compile_semantic_query(ctx, ent, [1], spec)
        assert exc.value.status_code == 422

    def test_blocks_money_sum_without_currency_grouping(self):
        ctx = _ctx(permisos=('Visualizar_control_costos',))
        ent = catalog.get_entity('costos_ejecutados')
        spec = SemanticQuerySpec(
            entidad='costos_ejecutados',
            dimensiones=['obra'],
            metricas=[SemanticMetric(operacion='sum', campo='monto', alias='total_monto')],
        )
        with pytest.raises(HTTPException) as exc:
            compiler.compile_semantic_query(ctx, ent, [1], spec)
        assert exc.value.status_code == 422
        assert 'moneda' in exc.value.detail.lower()

        # Agrupando por moneda sí compila correctamente
        spec_ok = spec.model_copy(update={'dimensiones': ['obra', 'moneda']})
        sql, _, _, _, tipo = compiler.compile_semantic_query(ctx, ent, [1], spec_ok)
        assert 'GROUP BY' in sql and 'SUM(ce.monto) AS total_monto' in sql
        assert tipo == 'agregacion'

    def test_blocks_estimaciones_sum_across_versions(self):
        ctx = _ctx(permisos=('Visualizar_estimaciones',))
        ent = catalog.get_entity('estimaciones')
        spec = SemanticQuerySpec(
            entidad='estimaciones',
            dimensiones=['moneda'],
            metricas=[SemanticMetric(operacion='sum', campo='monto_total', alias='suma')],
        )
        with pytest.raises(HTTPException) as exc:
            compiler.compile_semantic_query(ctx, ent, [1], spec)
        assert exc.value.status_code == 422
        assert 'version' in exc.value.detail.lower()

    def test_incremental_patch_workflow(self):
        spec = SemanticQuerySpec(
            entidad='incidencias',
            dimensiones=['obra'],
            metricas=[SemanticMetric(operacion='count', alias='total')],
        )
        spec = compiler.apply_patch(spec, ReportSpecPatch(operacion='add_dimension', campo='responsable'))
        assert spec.dimensiones == ['obra', 'responsable']

        spec = compiler.apply_patch(
            spec,
            ReportSpecPatch(
                operacion='add_filter',
                filtro=SemanticFilter(campo='prioridad', operador='eq', valor='CRITICA'),
            ),
        )
        assert len(spec.filtros) == 1 and spec.filtros[0].valor == 'CRITICA'

        spec = compiler.apply_patch(
            spec,
            ReportSpecPatch(
                operacion='compare_periods',
                tiempo=TimeConfig(desde=date(2026, 8, 1), hasta=date(2026, 10, 31), granularidad='month'),
            ),
        )
        assert spec.tiempo.comparar_periodo_anterior is True
        assert spec.tiempo.granularidad == 'month'

    def test_cross_module_compiles_preaggregated_ctes_without_fanout(self):
        ctx = _ctx(permisos=('Visualizar_cronograma', 'Visualizar_incidencias', 'Visualizar_control_costos'))
        spec = CrossModuleSpec(modulos=['retrasos', 'incidencias_criticas', 'costos'])
        sql, params, cols = compiler.compile_cross_module_works(ctx, spec.modulos, [1, 2], spec)
        assert 'WITH' in sql
        assert 'cte_retrasos AS' in sql
        assert 'cte_inc AS' in sql
        assert 'cte_costos AS' in sql
        assert any(c['campo'] == 'actividades_retrasadas' for c in cols)
        assert any(c['campo'] == 'incidencias_criticas' for c in cols)
        assert any(c['campo'] == 'costo_ejecutado' for c in cols)


class TestContextManager6Compartments:
    def test_policy_change_invalidates_report_spec_and_entities_only(self):
        ctx_old = _ctx(rol='ADMINISTRADOR_EMPRESA', empresa=10, usuario=5, persona=50)
        state = context_manager.ConversationState(
            policy_snapshot=ctx_old.policy(),
            id_empresa=10,
            entidades_resueltas={'obra_actual': {'id_obra': 9}},
            preferencias_usuario={'moneda_preferida': 'USD'},
            report_spec_activo={'tipo': 'dinamico', 'spec': {'entidad': 'incidencias'}},
            ultima_ejecucion={'id_ejecucion': 'abc'},
        )
        # Cambio de rol -> invalida report_spec_activo y entidades_resueltas
        ctx_new = _ctx(rol='JEFE DE OBRA', empresa=10, usuario=5, persona=50)
        loaded, invalidated = context_manager.load_state({'solicitud': state.model_dump()}, ctx_new)
        assert invalidated is True
        assert loaded.report_spec_activo is None
        assert loaded.ultima_ejecucion is None
        assert loaded.entidades_resueltas == {}
        assert loaded.preferencias_usuario == {'moneda_preferida': 'USD'}


class TestOrchestratorFunctionCalling:
    def test_multi_round_tool_call_and_synthesis(self):
        ctx = _ctx(rol='ADMINISTRADOR_EMPRESA', permisos=('Visualizar_incidencias', 'Visualizar_reportes', 'Exportar_reportes'))
        state = context_manager.ConversationState(policy_snapshot=ctx.policy(), id_empresa=ctx.empresa)

        fake_provider = MagicMock()
        fake_provider.chat_with_tools.side_effect = [
            {
                'content': '',
                'tool_calls': [{
                    'id': 'call_1',
                    'type': 'function',
                    'function': {
                        'name': 'consultar_datos',
                        'arguments': json.dumps({
                            'entidad': 'incidencias',
                            'dimensiones': ['obra'],
                            'metricas': [{'operacion': 'count', 'alias': 'total'}],
                        }),
                    },
                }],
                'finish_reason': 'tool_calls',
            },
            {
                'content': 'Se encontraron 4 incidencias en la Obra Central.',
                'tool_calls': [],
                'finish_reason': 'stop',
            },
        ]

        fake_db = MagicMock()
        with patch('app.services.ai.orchestrator.repo.transaction') as mock_tx, \
             patch('app.services.ai.orchestrator.auth.context', return_value=ctx), \
             patch('app.services.reportes.authorization.repo.works', return_value=[{'id_obra': 1, 'nombre': 'Obra Central', 'codigo': 'OC-1'}]), \
             patch('app.services.semantic.executor.repo.rows', return_value=[{'obra': 'Obra Central', 'total': 4}]), \
             patch('app.services.semantic.executor.repo.cutoff', return_value={'corte': datetime(2026, 11, 24, tzinfo=timezone.utc)}), \
             patch('app.services.ai.orchestrator.repo.insert_ready_execution'):
            mock_tx.return_value.__enter__.return_value = fake_db
            out = orchestrator.run_orchestrator(
                token={'nro_usuario': 5},
                ctx=ctx,
                question='Genera un reporte de incidencias por obra',
                state=state,
                recent_rows=[],
                available_reports=['incidencias'],
                works=[{'id_obra': 1, 'nombre': 'Obra Central', 'codigo': 'OC-1'}],
                plan_caps={'reportes_habilitado': True, 'exportar_habilitado': True},
                modules=None,
                navigation_work=None,
                provider=fake_provider,
            )

        assert out['estado'] == 'ready'
        assert 'Obra Central' in out['respuesta']
        assert state.report_spec_activo['tipo'] == 'dinamico'
        assert state.ultima_ejecucion is not None
        # Verificar compatibilidad estricta con Angular ReportResult
        res = out['ejecucion']['resultado']
        for required_key in ('titulo', 'corte', 'columnas', 'filas', 'resumen', 'advertencias', 'recomendaciones', 'solicitud'):
            assert required_key in res


class TestVisionExtractorHonesty:
    def test_does_not_fabricate_rooms_without_multimodal_extractor(self):
        # PNG válido de 800x600
        png = b'\x89PNG\r\n\x1a\n' + b'\x00' * 8 + struct.pack('>II', 800, 600) + b'\x00' * 16
        res = vision_extractor.extract_blueprint(png, '¿Cuánto cuesta construir esto?')
        assert res['modo_extraccion'] == 'SIN_EXTRACTOR_MULTIMODAL'
        assert res['nivel_confianza'] == 'PRELIMINAR'
        assert res['superficie_m2'] is None
        assert res['ambientes_detectados'] == []
        assert 'superficie_m2' in res['datos_no_legibles']
        assert any('colegiado' in a for a in res['advertencias'])

    def test_rejects_invalid_file_format(self):
        with pytest.raises(ValueError):
            vision_extractor.extract_blueprint(b'not-an-image-or-pdf-content')


class TestProactiveInbox:
    def test_cliente_only_queries_posventa_and_never_admin_modules(self):
        ctx = _ctx(rol='CLIENTE', empresa=3, usuario=20, persona=200, permisos=())
        fake_db = MagicMock()
        with patch('app.services.ai.proactive_inbox_service.repo.works', return_value=[]), \
             patch('app.services.ai.proactive_inbox_service.repo.rows', return_value=[
                 {'id_solicitud_posventa': 7, 'titulo': 'Fuga en baño', 'estado': 'REGISTRADA', 'unidad': 'A-101', 'obra': 'Torre Sur'}
             ]):
            inbox = consultar_pendientes(fake_db, ctx)
        assert inbox['fuentes_consultadas'] == ['posventa']
        assert inbox['total_pendientes'] == 1
        assert inbox['items'][0]['ruta_angular'] == '/posventa'
        assert inbox['items'][0]['prioridad'] == 'ALTA'
