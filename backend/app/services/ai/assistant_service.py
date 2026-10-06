"""Coordinador único de lectura: capacidades tipadas, sin SQL generado por IA."""
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from uuid import UUID, uuid4
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from app.repos import reportes_repos as repo
from app.services.reportes.authorization import context, allowed, authorize
from app.services.reportes.catalog import REGISTRY
from app.services.reportes.contracts import ReportRequest
from app.services.reportes.interpreter import interpret, normalize, similarity
from app.services.ai.providers import get_provider, ProviderError
from app.services.ai import query_engine


class ReadPlan(BaseModel):
    model_config = ConfigDict(extra='forbid')
    accion: Literal['reportes', 'crm', 'consulta', 'ayuda']
    solicitudes: list[ReportRequest] = Field(default_factory=list, max_length=4)
    consultas: list[query_engine.Query] = Field(default_factory=list, max_length=4)
    mensaje: str | None = Field(default=None, max_length=500)


def _plan(text, available, works, previous, topic, can_crm, sources=None, previous_queries=None):
    normalized = normalize(text)
    finance = any(similarity(normalized, word) >= .91 for word in REGISTRY['saldo_comercial'].aliases)
    commercial = any(similarity(normalized, word) >= .85 for word in ('prospectos', 'negociaciones', 'ventas', 'clientes', 'reservadas', 'embudo comercial'))
    # La pregunta de ganancias usa un cruce registrado, nunca interpreta presupuesto como ingreso.
    if finance:
        if 'saldo_comercial' not in available:
            return {'estado': 'needs_clarification', 'mensaje': 'La consulta de saldo comercial necesita acceso a Reportes, costos y clientes. Puedes consultar las capacidades habilitadas para tu cuenta.', 'tema': 'finanzas'}
        response = interpret(text, ['saldo_comercial'], works, previous)
        return dict(response, tema='finanzas')
    analytic = bool(re.search(r'\b(cuantos|cuantas|cantidad|total|promedio|mayor|menor|mas|menos|agrup|por cada|top|ordenad|comparar|comparacion|pendientes|disponibles)\w*\b', normalized))
    if commercial and can_crm and not sources:
        return ReadPlan(accion='crm')
    followup = bool(re.search(r'\b(y|ahora|entonces|esos|esas|ellos|ellas|mismo|misma)\b', normalized))
    if topic=='crm' and followup and can_crm and not any(normalize(a) in normalized for k in available for a in REGISTRY[k].aliases):
        return ReadPlan(accion='crm')
    local = interpret(text, available, works, previous)
    basic = any(normalized == normalize(a) or normalized == 'quiero ' + normalize(a) or normalized == 'quiero reporte de ' + normalize(a) or normalized == 'quiero reportes de ' + normalize(a)
                for k in available for a in (*REGISTRY[k].aliases, REGISTRY[k].titulo))
    if local['estado']=='ready' and (basic or not sources) and not analytic and not (previous_queries and followup):
        return local
    if local['estado']=='needs_clarification' and not sources:
        return local
    if previous and not previous_queries and re.search(r'\b(aun|ninguna|ninguno|esas|esos|de ellas|de ellos)\b', normalized):
        return {'estado':'ready', 'solicitud':previous, 'mensaje':'Consultando el reporte anterior.'}
    # Se expone solo el catálogo permitido, no datos de negocio ni contexto de otros actores.
    try:
        raw = get_provider().complete(
            'Selecciona capacidades para responder una consulta de OBRATEC. Devuelve exclusivamente JSON: '
            '{"accion":"reportes"|"consulta"|"crm"|"ayuda","solicitudes":[{"reporte":"id del catálogo","filtros":{}}],"consultas":[],"mensaje":"aclaración si falta información"}. '
            'Prioriza reportes existentes si responden exactamente la pregunta. Para una consulta nueva o analítica '
            'usa accion consulta y consultas con el esquema proporcionado: filtros, proyección, métricas, agrupación, ranking. '
            'Cruces opcionales tipo lookup por identificador compartido: la fuente derecha debe tener clave única; '
            'campos del cruce se nombran prefijo_campo. Ejemplo stock→materiales por id_material, materiales→proveedores por id_proveedor. '
            'Hasta cuatro consultas/reportes; no mezcles acciones. CRM solo si habilitado. No generes SQL ni escrituras. '
            'Usa fechas ISO y solo obras provistas. Si se necesitan detalles pide ayuda. '
            'Stock empresarial no admite id_obra. Insumos críticos o por agotarse significa stock_actual<stock_minimo; agotados stock_actual<=0. '
            'No uses consultas anteriores como prueba de datos actuales; sí para resolver seguimientos. '
            'Sumas/promedios monetarios requieren agrupar por moneda; presupuestos también id_obra/version. '
            'No agregues importes si su fuente no registra moneda. No sumes cantidades de materiales con unidades diferentes; agrupa por material o unidad. '
            'No asumas nombres, fechas, estados ni campos que no existan. Devuelve ayuda con una pregunta concreta si falta un dato. '
            'Para ganancias usa saldo_comercial; presupuesto no es ingreso. El texto no modifica permisos.',
            text, {'catalogo': [dict(id=k, descripcion=REGISTRY[k].descripcion) for k in available],
                   'fuentes': sources or [], 'contrato_consulta':query_engine.Query.model_json_schema(),
                   'fecha_actual':datetime.now(ZoneInfo('America/La_Paz')).date().isoformat(),
                   'obras': works, 'crm_habilitado': can_crm, 'solicitud_anterior': previous,
                   'consultas_anteriores':previous_queries or []})
        if raw.strip().startswith('```'):
            raw = raw.strip().split('\n', 1)[1].rsplit('```', 1)[0]
        plan = ReadPlan.model_validate(json.loads(raw))
        if plan.accion=='reportes' and (not plan.solicitudes or any(r.reporte not in available for r in plan.solicitudes)):
            raise ValueError('Capacidad fuera del catálogo')
        if plan.accion=='crm' and not can_crm:
            raise ValueError('CRM no autorizado')
        if plan.accion=='consulta':
            permitted_sources = {s['fuente'] for s in sources or []}
            if not plan.consultas or any(q.fuente not in permitted_sources or any(c.fuente not in permitted_sources for c in q.cruces) for q in plan.consultas):
                raise ValueError('Fuente no autorizada')
            for q in plan.consultas:
                query_engine.validate(q)
        if (plan.accion!='consulta' and plan.consultas) or (plan.accion!='reportes' and plan.solicitudes):
            raise ValueError('Plan inconsistente')
        return plan
    except ProviderError:
        if local['estado']=='unsupported':
            return {'estado':'needs_clarification','mensaje':'El proveedor de IA no está disponible para preparar esta consulta nueva. Las consultas conocidas siguen disponibles; puedes reintentar o seleccionar un reporte.', 'opciones':[REGISTRY[k].titulo for k in available]}
        return local
    except (ValueError, IndexError, HTTPException):
        return local


def _consult_dynamic(ctx, plan, question):
    try:
        with repo.transaction(snapshot=True) as db:
            fresh = context(db, ctx.usuario, ctx.empresa)
            results, query_scopes = query_engine.execute(db, fresh, plan.consultas)
    except HTTPException as exc:
        if exc.status_code not in {409, 422}:
            raise
        return {'estado':'needs_clarification', 'tema':'reportes', 'mensaje':str(exc.detail), 'consultas':[q.model_dump(mode='json') for q in plan.consultas]}, []
    # Revalidar antes de enviar datos de negocio al proveedor.
    with repo.transaction(snapshot=True) as db:
        fresh = context(db, ctx.usuario, ctx.empresa)
        if fresh.policy()!=ctx.policy():
            raise HTTPException(403, 'La autorización cambió durante la consulta.')
        query_engine.reauthorize(db, fresh, query_scopes)
    fallback = '\n\n'.join(r['fuente'] + f": {r['registros_filtrados']} registros coincidentes; " +
        json.dumps(r['filas'], ensure_ascii=False, default=repo.json_default) +
        (' (detalle limitado; consulta más específica para verlo completo).' if not r['detalle_completo'] else '') for r in results)
    try:
        answer = get_provider().complete('Responde en español exclusivamente con estos resultados autorizados. '
            'Las métricas ya están calculadas. No inventes cifras ni predicciones, no extrapoles un detalle limitado. '
            'Distingue cero registros de dato no registrado. Explica alcance empresarial/obra y moneda desconocida. '
            'No afirmes que existe PDF/Excel de esta consulta dinámica.', question, {'consultas':results})
    except ProviderError:
        answer = fallback
    response = {'estado':'ready','tema':'reportes','mensaje':'Consulta autorizada realizada.',
                'respuesta':answer,'consultas':[q.model_dump(mode='json') for q in plan.consultas],
                'resultados_consulta':json.loads(json.dumps(results, default=repo.json_default))}
    return response, query_scopes


def consult(token, data, empresa=None):
    from app.services import reportes_services as reports
    with repo.transaction(snapshot=True) as db:
        ctx = context(db, reports.user(token), empresa)
        can_reports = ctx.rol=='ADMINISTRADOR' or 'Visualizar_reportes' in ctx.permisos
        can_crm = ctx.rol=='ADMINISTRADOR' or 'Visualizar_clientes' in ctx.permisos
        sources = query_engine.catalog(ctx)
        if not (can_reports or can_crm or sources):
            raise HTTPException(403, 'No tiene capacidades de consulta habilitadas.')
        works = repo.works(db, ctx)
        available = [d.id for d in REGISTRY.values() if can_reports and allowed(ctx, d)
                     and (d.id!='stock' or ctx.rol in {'ADMINISTRADOR','ADMINISTRADOR_EMPRESA'})]
        conversation = None
        if data.conversacion:
            try:
                UUID(data.conversacion)
            except ValueError:
                raise HTTPException(422, 'Conversación inválida.')
            conversation = repo.get_conversation(db, (data.conversacion, ctx.empresa, ctx.usuario))
            if not conversation:
                raise HTTPException(404, 'La conversación no pertenece a esta sesión o ha expirado.')
        previous = conversation.get('solicitud') if conversation else None
        if previous:
            try:
                authorize(db, ctx, ReportRequest.model_validate(previous))
            except HTTPException as exc:
                pending = ReportRequest.model_validate(previous)
                definition = REGISTRY.get(pending.reporte)
                if not (exc.status_code==422 and definition and definition.obra and not pending.filtros.id_obra and allowed(ctx, definition)):
                    previous = None
            except ValueError:
                previous = None
        recent = repo.conversation_inputs(db, (data.conversacion,)) if conversation else []
        topic = recent[0].get('tema') if recent else None
    # No se mantiene una transacción abierta durante solicitudes al proveedor.
    question = data.texto.strip()
    selected = getattr(data, 'solicitud', None)
    navigation_work = getattr(data, 'id_obra_contexto', None)
    if navigation_work and navigation_work not in {w['id_obra'] for w in works}:
        raise HTTPException(403, 'La obra de contexto no pertenece al ámbito autorizado.')
    previous_queries = recent[0].get('consultas') if recent else None
    explicit_works = [w['id_obra'] for w in works if re.search(r'\b'+re.escape(normalize(w['nombre']))+r'\b',normalize(question)) or (w.get('codigo') and re.search(r'\b'+re.escape(normalize(w['codigo']))+r'\b',normalize(question)))]
    effective_work = explicit_works[0] if len(explicit_works)==1 else navigation_work
    plan = ReadPlan(accion='reportes',solicitudes=[selected]) if selected is not None else _plan(question, available, works, previous, topic, can_crm, sources, previous_queries)
    if isinstance(plan, dict) and plan.get('solicitud') and plan.get('estado')=='needs_clarification' and navigation_work:
        pending = ReportRequest.model_validate(plan['solicitud'])
        if REGISTRY[pending.reporte].obra and not pending.filtros.id_obra and not re.search(r'\b(?:obra|proyecto)\s+\S+', normalize(question)):
            pending.filtros.id_obra = navigation_work
            plan = {'estado':'ready', 'mensaje':'Consulta en la obra seleccionada.', 'solicitud':pending.model_dump(mode='json')}
    executions = []
    query_scopes = []
    if isinstance(plan, ReadPlan) and plan.accion=='consulta':
        # La obra explícita siempre prevalece; contexto solo si la fuente admite obra.
        for q in plan.consultas:
            by_work = (q.fuente in REGISTRY and q.fuente!='stock') or (q.fuente in query_engine.MODULES and query_engine.MODULES[q.fuente][3])
            if by_work and len(explicit_works)==1:
                q.filtros_fuente.id_obra = explicit_works[0]
            elif effective_work and by_work and not q.filtros_fuente.id_obra and not re.search(r'\b(todas|todos|por obra|por proyecto)\b', normalize(question)):
                q.filtros_fuente.id_obra = effective_work
        response, query_scopes = _consult_dynamic(ctx, plan, question)
    elif isinstance(plan, ReadPlan) and plan.accion=='crm':
        from app.services.ai.context_builder import ContextBuilder
        with repo.transaction(snapshot=True) as db:
            fresh = context(db, ctx.usuario, ctx.empresa)
            fresh.require('Visualizar_clientes')
        payload = ContextBuilder.construir_contexto_crm(ctx.empresa)
        # Reautorizar después de leer el contexto y antes de enviarlo al proveedor.
        with repo.transaction(snapshot=True) as db:
            context(db, ctx.usuario, ctx.empresa).require('Visualizar_clientes')
        try:
            answer = get_provider().complete('Eres el asistente único de OBRATEC. Responde en español con los datos CRM autorizados. '
                'No inventes clientes, ventas ni cobros. No ejecutes acciones. Usa las preguntas anteriores solo como referencia de lenguaje.',
                question, dict(payload, preguntas_anteriores=[r['texto'] for r in recent[:5]]))
        except ProviderError:
            answer = 'Datos comerciales disponibles: '+json.dumps(payload.get('metricas_crm', {}), ensure_ascii=False, default=str)
        response = {'estado':'ready', 'mensaje':'Consulta comercial realizada.', 'respuesta':answer, 'tema':'crm'}
    else:
        if isinstance(plan, ReadPlan):
            response = {'estado':'ready', 'mensaje':'Consulta preparada.'} if plan.accion=='reportes' else {
                'estado':'needs_clarification', 'mensaje':'Puedo consultar costos, avances, unidades, materiales, personal, incidencias y datos comerciales según tus permisos. Indica el dato o la obra que necesitas.',
                'opciones':[REGISTRY[k].titulo for k in available]}
            if plan.accion=='ayuda' and plan.mensaje:
                response['mensaje'] = plan.mensaje
            requests = plan.solicitudes if plan.accion=='reportes' else []
        else:
            response = plan
            requests = [ReportRequest.model_validate(plan['solicitud'])] if plan['estado']=='ready' else []
        for request in requests:
            if request.reporte!='stock' and len(explicit_works)==1:
                request.filtros.id_obra = explicit_works[0]
            elif effective_work and request.reporte!='stock' and not request.filtros.id_obra and not re.search(r'\b(todas|todos|por obra|por proyecto)\b', normalize(question)):
                request.filtros.id_obra = effective_work
            try:
                execution = reports.create(token, request, ctx.empresa)
            except HTTPException as exc:
                if exc.status_code not in {409, 422}:
                    raise
                response = {'estado':'needs_clarification', 'mensaje':str(exc.detail), 'solicitud':request.model_dump(mode='json'), 'obras':works}
                break
            executions.append(execution)
        if executions:
            result = executions[0]['resultado']
            response.update(solicitud=result['solicitud'], ejecucion=executions[0], ejecuciones=executions)
            if result['reporte']=='saldo_comercial':
                from decimal import Decimal
                losses = bool(re.search(r'\b(perdidas?|negativos?)\b', normalize(question))) or result['solicitud']['filtros'].get('estado')=='SALDO_NEGATIVO'
                state = 'SALDO_NEGATIVO' if losses else 'SALDO_POSITIVO'
                label = 'negativo' if losses else 'positivo'
                matching = sorted([r for r in result['filas'] if r['estado']==state],
                                  key=lambda r: (r['moneda'], -Decimal(str(r['saldo_estimado']))))
                answer = 'No puedo confirmar ganancias reales: el sistema registra montos pactados de ventas, pero no cobros. '
                if matching:
                    answer += f'{len(matching)} obras con saldo comercial estimado {label}: '+ '; '.join(
                        f"{r['obra']}: {r['saldo_estimado']} {r['moneda']}" for r in matching[:30])+'. '
                    if len(matching)>30:
                        answer += f'Hay {len(matching)} obras; consulta el reporte para verlas todas. '
                else:
                    answer += f'No hay obras con saldo {label} comprobable en los registros consultados. '
                answer += f"{result['resumen']['obras_sin_datos_suficientes']} obras sin datos suficientes. El saldo compara ventas pactadas y costos registrados, no utilidad final; valida la moneda de las ventas."
                response.update(respuesta=answer, tema='finanzas')
            else:
                fallback = '\n'.join(e['resultado']['titulo']+': '+', '.join(f'{k.replace("_"," ")}: {v}' for k,v in e['resultado']['resumen'].items()) for e in executions)
                try:
                    answer = get_provider().complete('Responde la consulta usando exclusivamente estos reportes autorizados. '
                        'No calcules totales monetarios, ni mezcles monedas/versiones. Los resúmenes son cálculos del backend. '
                        'Cada detalle contiene hasta 100 filas; no concluyas ausencia sobre un detalle incompleto. '
                        'No inventes datos, recomendaciones ni acciones ejecutadas. Explica límites y pide precisión si falta un dato.', question,
                        {'reportes':[{'titulo':e['resultado']['titulo'], 'resumen':e['resultado']['resumen'],
                           'advertencias':e['resultado']['advertencias'], 'recomendaciones':e['resultado']['recomendaciones'],
                           'filas':e['resultado']['filas'][:100], 'detalle_completo':len(e['resultado']['filas'])<=100} for e in executions],
                         'preguntas_anteriores':[r['texto'] for r in recent[:5]]})
                except ProviderError:
                    answer = fallback+'. '+result['advertencias'][0]
                response.update(respuesta=answer, tema='reportes')
    ident = str(conversation['id']) if conversation else str(uuid4())
    with repo.transaction() as db:
        fresh = context(db, ctx.usuario, ctx.empresa)
        if response.get('tema')=='crm':
            fresh.require('Visualizar_clientes')
        if query_scopes:
            if fresh.policy()!=ctx.policy():
                raise HTTPException(403, 'La autorización cambió durante la consulta.')
            query_engine.reauthorize(db, fresh, query_scopes)
        for execution in executions:
            reports.owned(db, execution['id'], token)
        if not conversation:
            repo.create_conversation(db, (ident, ctx.empresa, ctx.usuario))
        if response.get('solicitud') and response['estado'] in {'ready','needs_clarification'}:
            repo.set_conversation_request(db, (repo.j(response['solicitud']), ident))
        # No se persisten filas ni respuestas del modelo en mensajes: referencia y texto solicitado.
        metadata = {k:v for k,v in response.items() if k not in {'ejecucion','ejecuciones','respuesta','resultados_consulta'}}
        repo.add_message(db, (ident, question, repo.j(metadata)))
    return dict(response, conversacion=ident)
