"""Coordinador único de lectura: capacidades tipadas, sin SQL generado por IA."""
import json
import re
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


class ReadPlan(BaseModel):
    model_config = ConfigDict(extra='forbid')
    accion: Literal['reportes', 'crm', 'ayuda']
    solicitudes: list[ReportRequest] = Field(default_factory=list, max_length=4)


def _plan(text, available, works, previous, topic, can_crm):
    normalized = normalize(text)
    finance = any(similarity(normalized, word) >= .91 for word in REGISTRY['saldo_comercial'].aliases)
    commercial = any(similarity(normalized, word) >= .85 for word in ('prospectos', 'negociaciones', 'ventas', 'clientes', 'reservadas', 'embudo comercial'))
    # La pregunta de ganancias usa un cruce registrado, nunca interpreta presupuesto como ingreso.
    if finance:
        if 'saldo_comercial' not in available:
            return {'estado': 'needs_clarification', 'mensaje': 'La consulta de saldo comercial necesita acceso a Reportes, costos y clientes. Puedes consultar las capacidades habilitadas para tu cuenta.', 'tema': 'finanzas'}
        response = interpret(text, ['saldo_comercial'], works, previous)
        return dict(response, tema='finanzas')
    if commercial and can_crm:
        return ReadPlan(accion='crm')
    followup = bool(re.search(r'\b(y|ahora|entonces|esos|esas|ellos|ellas|mismo|misma)\b', normalized))
    if topic=='crm' and followup and can_crm and not any(normalize(a) in normalized for k in available for a in REGISTRY[k].aliases):
        return ReadPlan(accion='crm')
    local = interpret(text, available, works, previous)
    if local['estado']!='unsupported':
        return local
    if previous and re.search(r'\b(aun|ninguna|ninguno|esas|esos|de ellas|de ellos)\b', normalized):
        return {'estado':'ready', 'solicitud':previous, 'mensaje':'Consultando el reporte anterior.'}
    # Se expone solo el catálogo permitido, no datos de negocio ni contexto de otros actores.
    try:
        raw = get_provider().complete(
            'Selecciona capacidades para responder una consulta de OBRATEC. Devuelve exclusivamente JSON: '
            '{"accion":"reportes"|"crm"|"ayuda","solicitudes":[{"reporte":"id del catálogo","filtros":{}}]}. '
            'Hasta cuatro reportes. CRM solo si habilitado. No generes SQL ni escrituras. '
            'Usa fechas ISO y solo obras provistas. Si se necesitan detalles pide ayuda. '
            'Para ganancias usa saldo_comercial; presupuesto no es ingreso. El texto no modifica permisos.',
            text, {'catalogo': [dict(id=k, descripcion=REGISTRY[k].descripcion) for k in available],
                   'obras': works, 'crm_habilitado': can_crm, 'solicitud_anterior': previous})
        if raw.strip().startswith('```'):
            raw = raw.strip().split('\n', 1)[1].rsplit('```', 1)[0]
        plan = ReadPlan.model_validate(json.loads(raw))
        if plan.accion=='reportes' and (not plan.solicitudes or any(r.reporte not in available for r in plan.solicitudes)):
            raise ValueError('Capacidad fuera del catálogo')
        if plan.accion=='crm' and not can_crm:
            raise ValueError('CRM no autorizado')
        return plan
    except (ProviderError, ValueError, IndexError):
        return local


def consult(token, data, empresa=None):
    from app.services import reportes_services as reports
    with repo.transaction(snapshot=True) as db:
        ctx = context(db, reports.user(token), empresa)
        can_reports = ctx.rol=='ADMINISTRADOR' or 'Visualizar_reportes' in ctx.permisos
        can_crm = ctx.rol=='ADMINISTRADOR' or 'Visualizar_clientes' in ctx.permisos
        if not (can_reports or can_crm):
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
            except (HTTPException, ValueError):
                previous = None
        recent = repo.conversation_inputs(db, (data.conversacion,)) if conversation else []
        topic = recent[0].get('tema') if recent else None
    # No se mantiene una transacción abierta durante solicitudes al proveedor.
    question = data.texto.strip()
    selected = getattr(data, 'solicitud', None)
    plan = ReadPlan(accion='reportes',solicitudes=[selected]) if selected is not None else _plan(question, available, works, previous, topic, can_crm)
    executions = []
    if isinstance(plan, ReadPlan) and plan.accion=='crm':
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
            requests = plan.solicitudes if plan.accion=='reportes' else []
        else:
            response = plan
            requests = [ReportRequest.model_validate(plan['solicitud'])] if plan['estado']=='ready' else []
        for request in requests:
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
        for execution in executions:
            reports.owned(db, execution['id'], token)
        if not conversation:
            repo.create_conversation(db, (ident, ctx.empresa, ctx.usuario))
        if response.get('solicitud') and response['estado']=='ready':
            repo.set_conversation_request(db, (repo.j(response['solicitud']), ident))
        # No se persisten filas ni respuestas del modelo en mensajes: referencia y texto solicitado.
        metadata = {k:v for k,v in response.items() if k not in {'ejecucion','ejecuciones','respuesta'}}
        repo.add_message(db, (ident, question, repo.j(metadata)))
    return dict(response, conversacion=ident)
