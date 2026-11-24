"""Orquestador IA Multi-Perfil con DeepSeek Function Calling.

Combina herramientas semánticas (SemanticQueryEngine) y herramientas especializadas
(Pendientes proactivos, Recomendaciones inmobiliarias, Reportes estándar, Diagnóstico,
Ayuda y Operaciones asistidas de 2 pasos) bajo la autoridad única de authorization.py.
"""
import json
import re
from datetime import datetime
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from pydantic import ValidationError

from app.repos import reportes_repos as repo
from app.services.ai import assistant_analysis, assistant_operations, context_manager, knowledge_base
from app.services.ai.proactive_inbox_service import consultar_pendientes
from app.services.ai.providers import ProviderError, get_provider
from app.services.reportes import authorization as auth
from app.services.reportes.catalog import REGISTRY
from app.services.reportes.contracts import ReportRequest
from app.services.reportes.interpreter import normalize
from app.services.semantic import catalog as sem_catalog
from app.services.semantic import compiler as sem_compiler
from app.services.semantic import executor as sem_executor
from app.services.semantic.contracts import CrossModuleSpec, ReportSpecPatch, SemanticQuerySpec

MAX_TOOL_ROUNDS = 3


def _build_tool_definitions(ctx, available_reports: list[str], plan_caps: dict | None) -> list[dict]:
    """Construye el listado de tools para DeepSeek filtrando estrictamente por authorization.py."""
    entities = auth.authorized_entities(ctx)
    tools: list[dict] = []

    if auth.authorize_tool(ctx, 'consultar_datos', plan_caps) and entities:
        tools.append({
            'type': 'function',
            'function': {
                'name': 'consultar_datos',
                'description': (
                    'Consulta dinámica de solo lectura sobre entidades autorizadas de OBRATEC '
                    '(filtros, dimensiones, métricas, series temporales, comparativa de períodos). '
                    'Entidades disponibles: ' + ', '.join(entities)
                ),
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'entidad': {'type': 'string', 'enum': entities},
                        'filtros': {'type': 'array', 'items': {'type': 'object'}},
                        'tiempo': {'type': 'object'},
                        'dimensiones': {'type': 'array', 'items': {'type': 'string'}},
                        'metricas': {'type': 'array', 'items': {'type': 'object'}},
                        'campos': {'type': 'array', 'items': {'type': 'string'}},
                        'ordenar_por': {'type': 'string'},
                        'orden': {'type': 'string', 'enum': ['asc', 'desc']},
                        'limite': {'type': 'integer', 'minimum': 1, 'maximum': 500},
                        'id_obra': {'type': 'integer'},
                        'titulo': {'type': 'string'},
                        'tipo_grafico': {'type': 'string', 'enum': ['auto', 'none', 'kpi', 'bar', 'stacked_bar', 'line', 'pie']},
                        'guardar_como_reporte': {'type': 'boolean'},
                    },
                    'required': ['entidad'],
                },
            },
        })

    if auth.authorize_tool(ctx, 'analizar_cruce_obras', plan_caps):
        tools.append({
            'type': 'function',
            'function': {
                'name': 'analizar_cruce_obras',
                'description': (
                    'Cruza métricas agregadas por obra entre múltiples módulos sin duplicar filas '
                    '(retrasos de cronograma, incidencias críticas, costos ejecutados, OTs vencidas, posventa).'
                ),
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'modulos': {
                            'type': 'array',
                            'items': {'type': 'string', 'enum': ['retrasos', 'incidencias_criticas', 'costos', 'ordenes_trabajo', 'posventa']},
                            'minItems': 2,
                        },
                        'id_obra': {'type': 'integer'},
                        'ordenar_por': {'type': 'string'},
                        'orden': {'type': 'string', 'enum': ['asc', 'desc']},
                        'limite': {'type': 'integer', 'minimum': 1, 'maximum': 100},
                    },
                    'required': ['modulos'],
                },
            },
        })

    if auth.authorize_tool(ctx, 'ejecutar_reporte_estandar', plan_caps) and available_reports:
        tools.append({
            'type': 'function',
            'function': {
                'name': 'ejecutar_reporte_estandar',
                'description': 'Ejecuta y persiste uno de los reportes estándar oficiales exportables: ' + ', '.join(available_reports),
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'reporte': {'type': 'string', 'enum': available_reports},
                        'filtros': {'type': 'object'},
                    },
                    'required': ['reporte'],
                },
            },
        })

    if auth.authorize_tool(ctx, 'modificar_reporte_activo', plan_caps):
        tools.append({
            'type': 'function',
            'function': {
                'name': 'modificar_reporte_activo',
                'description': (
                    'Modifica incrementalmente el reporte dinámico activo en la conversación '
                    '(agregar/quitar dimensión, filtro, rango temporal, comparativa de períodos, orden o gráfico) y lo re-ejecuta.'
                ),
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'operacion': {
                            'type': 'string',
                            'enum': ['add_dimension', 'remove_dimension', 'add_filter', 'remove_filter', 'set_time', 'compare_periods', 'set_sort', 'set_chart', 'set_limit', 'set_title'],
                        },
                        'campo': {'type': 'string'},
                        'filtro': {'type': 'object'},
                        'tiempo': {'type': 'object'},
                        'orden': {'type': 'string', 'enum': ['asc', 'desc']},
                        'tipo_grafico': {'type': 'string', 'enum': ['auto', 'none', 'kpi', 'bar', 'stacked_bar', 'line', 'pie']},
                        'limite': {'type': 'integer'},
                        'titulo': {'type': 'string'},
                    },
                    'required': ['operacion'],
                },
            },
        })

    if auth.authorize_tool(ctx, 'exportar_reporte_activo', plan_caps):
        tools.append({
            'type': 'function',
            'function': {
                'name': 'exportar_reporte_activo',
                'description': 'Exporta a PDF o XLSX la última ejecución de reporte de esta conversación.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'formato': {'type': 'string', 'enum': ['pdf', 'xlsx']},
                    },
                    'required': ['formato'],
                },
            },
        })

    if auth.authorize_tool(ctx, 'consultar_pendientes', plan_caps):
        tools.append({
            'type': 'function',
            'function': {
                'name': 'consultar_pendientes',
                'description': (
                    'Consolida y prioriza los pendientes del usuario según su rol y permisos '
                    '(OTs, incidencias, aprobaciones, compras, cronogramas, seguimientos CRM, posventa).'
                ),
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'horizonte_dias': {'type': 'integer', 'minimum': 1, 'maximum': 60},
                        'id_obra': {'type': 'integer'},
                    },
                },
            },
        })

    if auth.authorize_tool(ctx, 'ejecutar_diagnostico_operativo', plan_caps):
        tools.append({
            'type': 'function',
            'function': {
                'name': 'ejecutar_diagnostico_operativo',
                'description': 'Genera diagnóstico integral de salud operativa, nivel de riesgo y recomendaciones.',
                'parameters': {
                    'type': 'object',
                    'properties': {'id_obra': {'type': 'integer'}},
                },
            },
        })

    if auth.authorize_tool(ctx, 'recomendar_inmuebles', plan_caps):
        tools.append({
            'type': 'function',
            'function': {
                'name': 'recomendar_inmuebles',
                'description': 'Busca y recomienda unidades inmobiliarias disponibles de la empresa según presupuesto, superficie, dormitorios, zona y estilo.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'tipo_unidad': {'type': 'string'},
                        'presupuesto_max': {'type': 'number'},
                        'moneda': {'type': 'string', 'enum': ['BOB', 'USD']},
                        'superficie_min_m2': {'type': 'number'},
                        'superficie_max_m2': {'type': 'number'},
                        'min_dormitorios': {'type': 'integer'},
                        'min_banos': {'type': 'integer'},
                        'zona': {'type': 'string'},
                        'estilo_acabado': {'type': 'string'},
                    },
                },
            },
        })

    if auth.authorize_tool(ctx, 'comparar_inmuebles', plan_caps):
        tools.append({
            'type': 'function',
            'function': {
                'name': 'comparar_inmuebles',
                'description': 'Compara lado a lado 2 a 4 unidades inmobiliarias disponibles por precio, superficie, costo/m2 y características.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'codigos': {'type': 'array', 'items': {'type': 'string'}},
                        'ids_unidades': {'type': 'array', 'items': {'type': 'integer'}},
                    },
                },
            },
        })

    if auth.authorize_tool(ctx, 'consultar_ayuda_plataforma', plan_caps):
        tools.append({
            'type': 'function',
            'function': {
                'name': 'consultar_ayuda_plataforma',
                'description': 'Explica módulos, rutas y procedimientos oficiales de OBRATEC habilitados para el usuario.',
                'parameters': {
                    'type': 'object',
                    'properties': {'tema': {'type': 'string'}},
                    'required': ['tema'],
                },
            },
        })

    if auth.authorize_tool(ctx, 'proponer_operacion', plan_caps):
        tools.append({
            'type': 'function',
            'function': {
                'name': 'proponer_operacion',
                'description': 'Prepara una propuesta de creación de bajo riesgo (crear_incidencia, crear_orden_trabajo o crear_material) que requerirá confirmación explícita del usuario.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'tipo_operacion': {'type': 'string', 'enum': ['crear_incidencia', 'crear_orden_trabajo', 'crear_material']},
                        'parametros': {'type': 'object'},
                    },
                    'required': ['tipo_operacion', 'parametros'],
                },
            },
        })

    return tools


def _persist_dynamic_execution(token: dict, ctx, result_dict: dict, scope: list[int]) -> dict:
    """Persiste un UnifiedResultSet dinámico en t_reporte_ejecucion para exportación PDF/XLSX."""
    ident = str(uuid4())
    with repo.transaction() as db:
        fresh = auth.context(db, ctx.usuario, ctx.empresa)
        if fresh.policy() != ctx.policy():
            raise HTTPException(403, 'La autorización cambió durante la consulta.')
        repo.insert_ready_execution(
            db,
            (
                ident,
                ctx.empresa,
                ctx.usuario,
                repo.j({'reporte': result_dict['reporte'], 'filtros': {}, 'consulta_dinamica': result_dict['solicitud']}),
                repo.j(ctx.policy()),
                scope,
                repo.j(result_dict),
            ),
        )
    return {'id': ident, 'estado': 'LISTO', 'resultado': json.loads(json.dumps(result_dict, default=repo.json_default))}


def _dispatch_tool(
    tool_name: str,
    args: dict[str, Any],
    *,
    token: dict,
    ctx,
    state: context_manager.ConversationState,
    plan_caps: dict | None,
    modules: list[str] | None,
    question: str,
    navigation_work: int | None,
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    """Ejecuta una tool validando autorización en vivo a través de authorization.py."""
    from app.services import reportes_services as reports

    if not auth.authorize_tool(ctx, tool_name, plan_caps):
        return {'error': f"Herramienta '{tool_name}' no autorizada para su cuenta."}

    try:
        if tool_name == 'consultar_datos':
            guardar = bool(args.pop('guardar_como_reporte', False))
            if navigation_work and not args.get('id_obra'):
                ent = sem_catalog.get_entity(args.get('entidad', ''))
                if ent and ent.work_column and not re.search(r'\b(todas|todos|por obra|por proyecto)\b', normalize(question)):
                    args['id_obra'] = navigation_work
            spec = SemanticQuerySpec.model_validate(args)
            with repo.transaction(snapshot=True) as db:
                fresh = auth.context(db, ctx.usuario, ctx.empresa)
                result, scope = sem_executor.execute_semantic_query(db, fresh, spec)
            res_dict = json.loads(json.dumps(result.model_dump(mode='json'), default=repo.json_default))
            state.report_spec_activo = {'tipo': 'dinamico', 'spec': spec.model_dump(mode='json')}
            if spec.id_obra:
                state.entidades_resueltas['obra_actual'] = {'id_obra': spec.id_obra}
            if guardar or auth.authorize_tool(ctx, 'exportar_reporte_activo', plan_caps):
                exec_obj = _persist_dynamic_execution(token, ctx, res_dict, scope)
                state.ultima_ejecucion = {'id_ejecucion': exec_obj['id'], 'origen': 'dinamico', 'corte': res_dict['corte']}
                artifacts['ejecucion'] = exec_obj
                artifacts.setdefault('ejecuciones', []).append(exec_obj)
            artifacts['chart_spec'] = res_dict.get('chart_spec')
            artifacts['tema'] = 'reportes'
            context_manager.record_tool_summary(state, tool_name, {'entidad': spec.entidad, 'registros': len(res_dict['filas'])})
            return {
                'titulo': res_dict['titulo'],
                'tipo_resultado': res_dict['tipo_resultado'],
                'resumen': res_dict['resumen'],
                'comparativa_periodo': res_dict.get('comparativa_periodo'),
                'chart_spec': res_dict.get('chart_spec'),
                'advertencias': res_dict['advertencias'],
                'filas_muestra': res_dict['filas'][:60],
                'id_ejecucion': state.ultima_ejecucion['id_ejecucion'] if state.ultima_ejecucion else None,
            }

        if tool_name == 'analizar_cruce_obras':
            spec = CrossModuleSpec.model_validate(args)
            with repo.transaction(snapshot=True) as db:
                fresh = auth.context(db, ctx.usuario, ctx.empresa)
                result, scope = sem_executor.execute_cross_module(db, fresh, spec)
            res_dict = json.loads(json.dumps(result.model_dump(mode='json'), default=repo.json_default))
            exec_obj = _persist_dynamic_execution(token, ctx, res_dict, scope)
            state.ultima_ejecucion = {'id_ejecucion': exec_obj['id'], 'origen': 'multidimensional', 'corte': res_dict['corte']}
            artifacts['ejecucion'] = exec_obj
            artifacts.setdefault('ejecuciones', []).append(exec_obj)
            artifacts['chart_spec'] = res_dict.get('chart_spec')
            artifacts['tema'] = 'analisis'
            context_manager.record_tool_summary(state, tool_name, {'modulos': spec.modulos, 'obras': len(res_dict['filas'])})
            return {
                'titulo': res_dict['titulo'],
                'resumen': res_dict['resumen'],
                'advertencias': res_dict['advertencias'],
                'fuentes_consultadas': res_dict['fuentes_consultadas'],
                'fuentes_omitidas': res_dict['fuentes_omitidas'],
                'filas': res_dict['filas'][:50],
                'id_ejecucion': exec_obj['id'],
            }

        if tool_name == 'modificar_reporte_activo':
            active = state.report_spec_activo
            if not active or active.get('tipo') != 'dinamico' or not active.get('spec'):
                return {'error': 'No existe un reporte dinámico activo en la conversación para modificar. Genera uno primero.'}
            patch = ReportSpecPatch.model_validate(args)
            current_spec = SemanticQuerySpec.model_validate(active['spec'])
            updated_spec = sem_compiler.apply_patch(current_spec, patch)
            with repo.transaction(snapshot=True) as db:
                fresh = auth.context(db, ctx.usuario, ctx.empresa)
                result, scope = sem_executor.execute_semantic_query(db, fresh, updated_spec)
            res_dict = json.loads(json.dumps(result.model_dump(mode='json'), default=repo.json_default))
            state.report_spec_activo = {'tipo': 'dinamico', 'spec': updated_spec.model_dump(mode='json')}
            exec_obj = _persist_dynamic_execution(token, ctx, res_dict, scope)
            state.ultima_ejecucion = {'id_ejecucion': exec_obj['id'], 'origen': 'dinamico', 'corte': res_dict['corte']}
            artifacts['ejecucion'] = exec_obj
            artifacts.setdefault('ejecuciones', []).append(exec_obj)
            artifacts['chart_spec'] = res_dict.get('chart_spec')
            artifacts['tema'] = 'reportes'
            context_manager.record_tool_summary(state, tool_name, {'operacion': patch.operacion, 'registros': len(res_dict['filas'])})
            return {
                'titulo': res_dict['titulo'],
                'tipo_resultado': res_dict['tipo_resultado'],
                'resumen': res_dict['resumen'],
                'comparativa_periodo': res_dict.get('comparativa_periodo'),
                'advertencias': res_dict['advertencias'],
                'filas_muestra': res_dict['filas'][:60],
                'id_ejecucion': exec_obj['id'],
            }

        if tool_name == 'ejecutar_reporte_estandar':
            req = ReportRequest.model_validate(args)
            execution = reports.create(token, req, ctx.empresa)
            state.report_spec_activo = {'tipo': 'estandar', 'solicitud': req.model_dump(mode='json')}
            state.ultima_ejecucion = {'id_ejecucion': execution['id'], 'origen': 'estandar', 'corte': execution['resultado']['corte']}
            artifacts['ejecucion'] = execution
            artifacts.setdefault('ejecuciones', []).append(execution)
            artifacts['solicitud'] = execution['resultado']['solicitud']
            artifacts['tema'] = 'finanzas' if req.reporte == 'saldo_comercial' else 'reportes'
            context_manager.record_tool_summary(state, tool_name, {'reporte': req.reporte, 'registros': len(execution['resultado']['filas'])})
            return {
                'id_ejecucion': execution['id'],
                'titulo': execution['resultado']['titulo'],
                'resumen': execution['resultado']['resumen'],
                'advertencias': execution['resultado']['advertencias'],
                'recomendaciones': execution['resultado']['recomendaciones'],
                'filas_muestra': execution['resultado']['filas'][:60],
            }

        if tool_name == 'exportar_reporte_activo':
            last = state.ultima_ejecucion
            if not last or not last.get('id_ejecucion'):
                return {'error': 'No hay ningún reporte generado en esta conversación para exportar.'}
            formato = args.get('formato', 'xlsx')
            exported = reports.export_execution(token, last['id_ejecucion'], formato)
            export_info = {
                'id_archivo': str(exported['id']),
                'nombre': exported['nombre'],
                'formato': formato,
                'url_descarga': f"/api/reportes/archivos/{exported['id']}",
            }
            artifacts['exportacion'] = export_info
            context_manager.record_tool_summary(state, tool_name, {'formato': formato, 'id_archivo': export_info['id_archivo']})
            return export_info

        if tool_name == 'consultar_pendientes':
            with repo.transaction(snapshot=True) as db:
                fresh = auth.context(db, ctx.usuario, ctx.empresa)
                inbox = consultar_pendientes(
                    db, fresh,
                    horizonte_dias=int(args.get('horizonte_dias') or 7),
                    id_obra=args.get('id_obra') or navigation_work,
                )
            artifacts['pendientes'] = inbox
            artifacts['tema'] = 'analisis'
            context_manager.record_tool_summary(state, tool_name, {'total_pendientes': inbox['total_pendientes']})
            return inbox

        if tool_name == 'ejecutar_diagnostico_operativo':
            with repo.transaction(snapshot=True) as db:
                fresh = auth.context(db, ctx.usuario, ctx.empresa)
                analisis, scope_diag = assistant_analysis.analizar_con_alcance(
                    db, fresh, id_obra=args.get('id_obra') or navigation_work
                )
            artifacts['resultado_analisis'] = analisis
            artifacts['analysis_scope'] = scope_diag
            artifacts['tema'] = 'analisis'
            context_manager.record_tool_summary(state, tool_name, {'nivel_riesgo': analisis['nivel_riesgo']})
            return analisis

        if tool_name in {'recomendar_inmuebles', 'comparar_inmuebles'}:
            from app.repos import commercial_repos
            from app.services.commercial import commercial_query_engine as cqe
            from app.services.commercial.contracts import CommercialSearchCriteria

            datos_param = commercial_repos.obtener_parametros_estimacion_empresa(ctx.empresa)
            unidades_raw = commercial_repos.listar_unidades_comerciales(ctx.empresa)
            prefs = state.preferencias_usuario.get('comercial') or {}
            merged_args = {**prefs, **{k: v for k, v in args.items() if v is not None}}

            if tool_name == 'recomendar_inmuebles':
                from app.services.commercial import project_proposal_engine as ppe
                crit = CommercialSearchCriteria(
                    intencion='recomendar_presupuesto',
                    tipo_unidad=merged_args.get('tipo_unidad'),
                    presupuesto_max=merged_args.get('presupuesto_max'),
                    moneda=merged_args.get('moneda') or 'BOB',
                    superficie_min_m2=merged_args.get('superficie_min_m2'),
                    superficie_max_m2=merged_args.get('superficie_max_m2'),
                    min_dormitorios=merged_args.get('min_dormitorios'),
                    min_banos=merged_args.get('min_banos'),
                    zona=merged_args.get('zona'),
                    estilo_acabado=merged_args.get('estilo_acabado'),
                    amoblamiento_preferido=merged_args.get('amoblamiento_preferido'),
                    amoblamiento_indispensable=bool(merged_args.get('amoblamiento_indispensable', False)),
                    acepta_cotizar_mobiliario=bool(merged_args.get('acepta_cotizar_mobiliario', False)),
                    tiene_terreno=merged_args.get('tiene_terreno'),
                )
                res = cqe.filtrar_y_recomendar_unidades(unidades_raw, datos_param, crit, top_k=5)
                state.preferencias_usuario['comercial'] = {
                    k: v for k, v in merged_args.items()
                    if k in {
                        'tipo_unidad', 'presupuesto_max', 'moneda', 'zona',
                        'min_dormitorios', 'min_banos', 'amoblamiento_preferido',
                        'amoblamiento_indispensable', 'acepta_cotizar_mobiliario', 'tiene_terreno',
                    }
                }
                unidades_out = [
                    {
                        'id_unidad': u['id_unidad'], 'codigo': u['codigo_unidad'], 'nombre': u['nombre_unidad'],
                        'obra': u['nombre_obra'], 'tipo': u['tipo_unidad'], 'superficie_m2': u['superficie_m2'],
                        'precio_bob': u['precio_bob'], 'precio_usd': u['precio_usd'],
                        'fuente_precio': u['fuente_precio'], 'tipo_precio': u.get('tipo_precio', u['fuente_precio']),
                        'estado_amoblamiento': u.get('estado_amoblamiento', 'DESCONOCIDO'),
                        'cotizacion_mobiliario_separada': u.get('cotizacion_mobiliario_separada'),
                        'disponibilidad': u['disponibilidad_comercial'], 'afinidad_score': u['afinidad_score'],
                        'razones': u['razones_recomendacion'], 'advertencias': u.get('observaciones_criterio') or [],
                    }
                    for u in res['unidades_recomendadas']
                ]
                propuesta_proj = None
                if not unidades_out or crit.tiene_terreno is not None:
                    lotes_disp = [
                        u for u in res['todas_enriquecidas']
                        if u.get('disponibilidad_comercial') == 'DISPONIBLE' and u.get('tipo_unidad') == 'LOTE'
                    ]
                    propuesta_proj = ppe.generar_propuesta_proyecto(ctx.empresa, crit, datos_param, lotes_disponibles=lotes_disp)
                    artifacts['propuesta_proyecto'] = propuesta_proj
                state.entidades_resueltas['ultimas_unidades'] = [u['id_unidad'] for u in unidades_out]
                artifacts['unidades_recomendadas'] = unidades_out
                artifacts['tema'] = 'crm'
                context_manager.record_tool_summary(state, tool_name, {'encontradas': len(unidades_out)})
                return {
                    'coincidencias_exactas': res['coincidencias_exactas'],
                    'motivos_exclusion': res.get('motivos_exclusion'),
                    'nota_precios': 'Cada unidad diferencia PRECIO_PUBLICADO de ESTIMACION_PARAMETRICA. Nunca corresponde a monto pactado de terceros.',
                    'unidades': unidades_out,
                    'propuesta_proyecto': propuesta_proj,
                }
            else:
                res = cqe.filtrar_y_recomendar_unidades(unidades_raw, datos_param, CommercialSearchCriteria(solo_disponibles=False), top_k=6)
                ids = args.get('ids_unidades') or state.entidades_resueltas.get('ultimas_unidades') or []
                comp = cqe.comparar_alternativas_inmobiliarias(
                    res['todas_enriquecidas'], ids_solicitud=ids, codigos_solicitud=args.get('codigos') or [],
                    candidatas_fallback=res['unidades_recomendadas'],
                )
                artifacts['comparativa'] = comp
                artifacts['tema'] = 'crm'
                context_manager.record_tool_summary(state, tool_name, {'comparadas': comp['total_comparadas']})
                return comp

        if tool_name == 'consultar_ayuda_plataforma':
            know = knowledge_base.buscar_conocimiento(args.get('tema') or question, ctx.rol, permisos=ctx.permisos, modulos=modules)
            artifacts['tema'] = 'conocimiento'
            context_manager.record_tool_summary(state, tool_name, {'encontrado': bool(know)})
            return know or {'mensaje': 'No hay módulos o procedimientos adicionales para su rol actual.'}

        if tool_name == 'proponer_operacion':
            norm_q = normalize(question)
            is_neg = bool(re.search(r'\b(no\s+(crear|crea|registrar|registres|emitir|emitas|agregar|agregues))\b', norm_q))
            has_intent = bool(re.search(r'\b(crea|crear|registra|registrar|nueva|nuevo|emite|emitir|agrega|agregar)\b', norm_q) and not is_neg)
            if not has_intent:
                return {'error': 'La consulta es de solo lectura; no se generó ninguna operación de escritura.'}
            ticket = assistant_operations.proponer_operacion(
                ctx, args['tipo_operacion'], args.get('parametros') or {}, id_obra_contexto=navigation_work
            )
            artifacts['operacion_propuesta'] = ticket
            artifacts['tema'] = 'operacion'
            context_manager.record_tool_summary(state, tool_name, {'tipo_operacion': args['tipo_operacion']})
            return ticket

        return {'error': f"Herramienta desconocida: '{tool_name}'."}
    except (ValidationError, HTTPException, ValueError) as exc:
        detail = getattr(exc, 'detail', None) or str(exc)
        return {'error': str(detail)}


def run_orchestrator(
    *,
    token: dict,
    ctx,
    question: str,
    state: context_manager.ConversationState,
    recent_rows: list[dict],
    available_reports: list[str],
    works: list[dict],
    plan_caps: dict | None,
    modules: list[str] | None,
    navigation_work: int | None,
    provider=None,
) -> dict[str, Any]:
    """Ejecuta el ciclo de DeepSeek Function Calling (máx. MAX_TOOL_ROUNDS) y retorna respuesta unificada."""
    ai_provider = provider or get_provider()
    if not hasattr(ai_provider, 'chat_with_tools'):
        raise ProviderError('El proveedor configurado no soporta Function Calling.')

    tools = _build_tool_definitions(ctx, available_reports, plan_caps)
    entities_meta = sem_catalog.list_entity_summaries(auth.authorized_entities(ctx))
    today = datetime.now(ZoneInfo('America/La_Paz')).date().isoformat()

    system_prompt = (
        f"Eres el Asistente Inteligente de OBRATEC para el rol {ctx.rol}. Fecha actual: {today}. "
        "Usa las herramientas disponibles para responder con datos reales y verificados. "
        "NUNCA generes SQL libre ni inventes cifras, monedas o rutas inexistentes. "
        "Si una herramienta devuelve un error de validación (por ejemplo, falta agrupar por moneda), corrige los parámetros y reintenta. "
        "Si el usuario pide modificar un reporte anterior (agregar columna, filtrar, comparar períodos o exportar), usa modificar_reporte_activo o exportar_reporte_activo. "
        "Si el usuario pregunta por sus tareas o pendientes, usa consultar_pendientes. "
        "Responde siempre en español claro, ejecutivo y conciso.\n"
        f"Contexto de sesión (solo lectura): {json.dumps({'obras_autorizadas': works[:40], 'entidades': entities_meta, 'report_spec_activo': state.report_spec_activo, 'entidades_resueltas': state.entidades_resueltas}, ensure_ascii=False, default=str)}"
    )

    messages = context_manager.build_chat_history(recent_rows, max_turns=6)
    messages.append({'role': 'user', 'content': question})

    artifacts: dict[str, Any] = {'tema': 'reportes'}
    final_answer = ''

    for _round in range(MAX_TOOL_ROUNDS):
        res = ai_provider.chat_with_tools(messages=messages, tools=tools, system=system_prompt)
        tool_calls = res.get('tool_calls') or []
        if not tool_calls:
            final_answer = res.get('content') or ''
            break

        messages.append({
            'role': 'assistant',
            'content': res.get('content') or '',
            'tool_calls': tool_calls,
        })

        for tc in tool_calls[:4]:
            fn = tc.get('function') or {}
            tname = fn.get('name') or ''
            try:
                targs = json.loads(fn.get('arguments') or '{}')
                if not isinstance(targs, dict):
                    targs = {}
            except ValueError:
                targs = {}
            tresult = _dispatch_tool(
                tname, targs, token=token, ctx=ctx, state=state, plan_caps=plan_caps,
                modules=modules, question=question, navigation_work=navigation_work, artifacts=artifacts,
            )
            messages.append({
                'role': 'tool',
                'tool_call_id': tc.get('id') or f'call_{uuid4().hex[:8]}',
                'name': tname,
                'content': json.dumps(tresult, ensure_ascii=False, default=repo.json_default)[:16000],
            })
    else:
        # Si agotó las rondas con tool calls, solicitar síntesis final sin tools
        res = ai_provider.chat_with_tools(messages=messages, tools=[], system=system_prompt)
        final_answer = res.get('content') or ''

    if not final_answer:
        final_answer = 'Consulta procesada con los datos autorizados.'

    response: dict[str, Any] = {
        'estado': 'ready',
        'tema': artifacts.get('tema', 'reportes'),
        'mensaje': 'Consulta procesada.',
        'respuesta': final_answer,
    }
    for key in ('ejecucion', 'ejecuciones', 'solicitud', 'operacion_propuesta', 'resultado_analisis',
                'pendientes', 'chart_spec', 'exportacion', 'unidades_recomendadas', 'comparativa', 'analysis_scope'):
        if key in artifacts:
            response[key] = artifacts[key]
    return response
