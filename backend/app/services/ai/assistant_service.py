import json
import re
from datetime import datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from pydantic import BaseModel, Field
from app.repos import reportes_repos as repo
from app.services.reportes.catalog import REGISTRY
from app.services.reportes.contracts import ReportRequest
from app.services.reportes.authorization import allowed, authorize, context
from app.services.ai.ai_service import get_provider, ProviderError
from app.services.ai import query_engine
from app.services.ai import knowledge_base
from app.services.ai import assistant_analysis
from app.services.ai import assistant_operations
from app.services.reportes.interpreter import normalize
from app.services import suscripcion_policy as subscription


def _knowledge_response(question, ctx, modules):
    know = knowledge_base.buscar_conocimiento(question, ctx.rol, permisos=ctx.permisos, modulos=modules)
    if not know:
        text = 'No hay módulos o procedimientos disponibles para esta consulta con sus permisos actuales.'
    else:
        text = know.get('mensaje', 'Información del sistema según sus permisos actuales.')
        text += '\n' + '\n'.join(f"• **{m['nombre']}** (`{m['ruta']}`): {m['descripcion']}" for m in know['modulos'])
        for procedure in know.get('procedimientos', []):
            text += f"\n\n**{procedure['tema']}**\n" + '\n'.join(f'{i+1}. {step}' for i, step in enumerate(procedure['pasos']))
    return dict(estado='ready', tema='conocimiento', mensaje='Información del sistema consultada.', respuesta=text)


def _company_modules(db, ctx):
    return None if ctx.rol == 'ADMINISTRADOR' else (subscription.obtener(ctx.empresa, db.cur) or {}).get('modulos', [])


class ActionProposal(BaseModel):
    tipo_operacion: str = Field(description="crear_incidencia | crear_orden_trabajo | crear_material")
    resumen: str = Field(description="Descripción clara de lo que se creará")
    entidad: str = Field(description="Incidencia | Orden de Trabajo | Material")
    parametros: dict = Field(default_factory=dict, description="Parámetros validados para la operación")


class ReadPlan(BaseModel):
    accion: str = Field(description="reportes | consulta | crm | ayuda | conocimiento | analisis | operacion")
    solicitudes: list[ReportRequest] = Field(default_factory=list)
    consultas: list[query_engine.Query] = Field(default_factory=list)
    mensaje: str = ""
    tema: str = ""
    operacion_propuesta: ActionProposal | None = None
    referencias: list[str] = Field(default_factory=list)
    sugerencias: list[str] = Field(default_factory=list)


def _plan(text, available, works, previous, topic, can_crm, sources=None, previous_queries=None,
          recent=None, user_role="ADMINISTRADOR", id_obra_contexto=None, permisos=None, modulos=None):
    from app.services.reportes.interpreter import interpret, similarity
    normalized = normalize(text)
    finance = any(similarity(normalized, word) >= .91 for word in REGISTRY['saldo_comercial'].aliases)
    commercial = any(similarity(normalized, word) >= .85 for word in ('prospectos', 'negociaciones', 'ventas', 'clientes', 'reservadas', 'embudo comercial'))
    if finance:
        if 'saldo_comercial' not in available:
            return {'estado': 'needs_clarification', 'mensaje': 'La consulta de saldo comercial necesita acceso a Reportes, costos y clientes. Puedes consultar las capacidades habilitadas para tu cuenta.', 'tema': 'finanzas'}
        response = interpret(text, ['saldo_comercial'], works, previous)
        return dict(response, tema='finanzas')

    # 2. Regla de análisis operativo integral
    if re.search(r'\b(analisis|analizar|salud operativa|diagnostico|desviacion|desviaciones|retrasos|riesgos|recomendaciones|como van los proyectos|alertas operativas|estado general)\b', normalized):
        return ReadPlan(accion='analisis', tema='analisis', mensaje='Iniciando análisis operativo determinista.')

    # 3. Regla de conocimiento y procedimientos del sistema
    know = knowledge_base.buscar_conocimiento(text, user_role, permisos=permisos, modulos=modulos)
    if know and re.search(r'\b(como|donde|donde esta|que modulos|procedimiento|funciona|pasos|que es|ayuda)\b', normalized):
        return ReadPlan(accion='conocimiento', tema='conocimiento', mensaje='Consulta de procedimientos y módulos OBRATEC.')

    # 4. Regla de operaciones de bajo riesgo (propuesta asistida) (M1, M2)
    is_negation = bool(re.search(r'\b(no\s+(crear|crea|registrar|registres|emitir|emitas|agregar|agregues|hacer|hagas|generar|generes))\b', normalized))
    if re.search(r'\b(crea|crear|registra|registrar|nueva|nuevo|emite|emitir|agrega|agregar)\b', normalized) and not is_negation:
        target_work = None
        explicit_matches = [
            w['id_obra'] for w in works
            if re.search(r'\b' + re.escape(normalize(w['nombre'])) + r'\b', normalized)
            or (w.get('codigo') and re.search(r'\b' + re.escape(normalize(w['codigo'])) + r'\b', normalized))
        ]
        if len(explicit_matches) == 1:
            target_work = explicit_matches[0]
        elif len(explicit_matches) > 1:
            return ReadPlan(
                accion='ayuda',
                mensaje='Se encontraron múltiples obras coincidentes con su solicitud. Por favor especifique exactamente el nombre o código de la obra.'
            )
        elif id_obra_contexto and id_obra_contexto in [w['id_obra'] for w in works]:
            target_work = id_obra_contexto

        if re.search(r'\b(incidencia|falla|averia|problema|inconveniente)\b', normalized):
            if not target_work:
                return ReadPlan(
                    accion='ayuda',
                    mensaje='Por favor especifique en qué obra desea registrar la incidencia o selecciónela en el selector de contexto superior.'
                )
            prioridad = "CRITICA" if "critica" in normalized else ("ALTA" if "alta" in normalized else "MEDIA")
            return ReadPlan(
                accion='operacion', tema='operacion',
                operacion_propuesta=ActionProposal(
                    tipo_operacion='crear_incidencia', entidad='Incidencia de Obra',
                    resumen="",
                    parametros={'id_obra': target_work, 'titulo': text[:180], 'prioridad': prioridad, 'descripcion': text[:300]}
                ),
                sugerencias=['Confirmar incidencia', 'Cancelar']
            )
        elif re.search(r'\b(orden de trabajo|ot|tarea)\b', normalized):
            if not target_work:
                return ReadPlan(
                    accion='ayuda',
                    mensaje='Por favor especifique en qué obra desea crear la orden de trabajo o selecciónela en el selector de contexto superior.'
                )
            return ReadPlan(
                accion='operacion', tema='operacion',
                operacion_propuesta=ActionProposal(
                    tipo_operacion='crear_orden_trabajo', entidad='Orden de Trabajo',
                    resumen="",
                    parametros={'id_obra': target_work, 'tipo_trab': text[:100]}
                ),
                sugerencias=['Confirmar orden de trabajo', 'Cancelar']
            )
        elif re.search(r'\b(material|insumo)\b', normalized):
            codigo_gen = f"MAT-{uuid4().hex[:6].upper()}"
            return ReadPlan(
                accion='operacion', tema='operacion',
                operacion_propuesta=ActionProposal(
                    tipo_operacion='crear_material', entidad='Material de Catálogo',
                    resumen="",
                    parametros={'codigo': codigo_gen, 'nombre_material': text[:100], 'precio': 0.0}
                ),
                sugerencias=['Confirmar material', 'Cancelar']
            )

    analytic = bool(re.search(r'\b(cuantos|cuantas|cantidad|total|promedio|mayor|menor|mas|menos|agrup|por cada|top|ordenad|comparar|comparacion|pendientes|disponibles)\w*\b', normalized))
    if commercial and can_crm and not sources:
        return ReadPlan(accion='crm')
    followup = bool(re.search(r'\b(y|ahora|entonces|esos|esas|ellos|ellas|mismo|misma)\b', normalized))
    if topic == 'crm' and followup and can_crm and not any(normalize(a) in normalized for k in available for a in REGISTRY[k].aliases):
        return ReadPlan(accion='crm')
    local = interpret(text, available, works, previous)
    basic = any(normalized == normalize(a) or normalized == 'quiero ' + normalize(a) or normalized == 'quiero reporte de ' + normalize(a) or normalized == 'quiero reportes de ' + normalize(a)
                for k in available for a in (*REGISTRY[k].aliases, REGISTRY[k].titulo))
    if local['estado'] == 'ready' and (basic or not sources) and not analytic and not (previous_queries and followup):
        return local
    if local['estado'] == 'needs_clarification' and not sources:
        return local
    if previous and not previous_queries and re.search(r'\b(aun|ninguna|ninguno|esas|esos|de ellas|de ellos)\b', normalized):
        return {'estado': 'ready', 'solicitud': previous, 'mensaje': 'Consultando el reporte anterior.'}

    # Invocación estructurada al proveedor con historial conversacional saneado (A6)
    try:
        historial_reciente = [
            {
                "usuario": r["texto"],
                "tema": r.get("tema") or ""
            }
            for r in reversed((recent or [])[:4])
        ]
        system_instruction = (
            'Eres el Asistente Administrativo y Operativo de OBRATEC. Selecciona capacidades para responder al usuario. '
            'Devuelve exclusivamente JSON: '
            '{"accion":"reportes"|"consulta"|"crm"|"ayuda"|"conocimiento"|"analisis"|"operacion",'
            '"solicitudes":[{"reporte":"id del catalogo","filtros":{}}],"consultas":[],"mensaje":"aclaracion si falta informacion",'
            '"operacion_propuesta":{"tipo_operacion":"","resumen":"","entidad":"","parametros":{}},'
            '"referencias":[],"sugerencias":[]}. '
            'Usa conocimiento para explicar modulos, rutas y procedimientos sin inventar nada. '
            'Usa analisis para estado general, desviaciones, riesgos o recomendaciones operativas. '
            'Usa operacion exclusivamente cuando el usuario solicite explícitamente crear una incidencia, orden de trabajo o material. '
            'Para consultas de solo lectura nunca uses accion operacion. '
            'Prioriza reportes existentes si responden exactamente la pregunta. Para una consulta analitica usa accion consulta. '
            'No generes SQL ni escrituras directas. No inventes campos ni rutas inexistentes.'
        )
        context_payload = {
            'catalogo': [dict(id=k, descripcion=REGISTRY[k].descripcion) for k in available],
            'fuentes': sources or [],
            'contrato_consulta': query_engine.Query.model_json_schema(),
            'fecha_actual': datetime.now(ZoneInfo('America/La_Paz')).date().isoformat(),
            'obras': works,
            'crm_habilitado': can_crm,
            'solicitud_anterior': previous,
            'historial_conversacion': historial_reciente,
            'consultas_anteriores': previous_queries or []
        }
        raw = get_provider().complete(system_instruction, text, context_payload)
        if raw.strip().startswith('```'):
            raw = raw.strip().split('\n', 1)[1].rsplit('```', 1)[0]
        plan = ReadPlan.model_validate(json.loads(raw))
        if plan.accion == 'reportes' and (not plan.solicitudes or any(r.reporte not in available for r in plan.solicitudes)):
            raise ValueError('Capacidad fuera del catalogo')
        if plan.accion == 'crm' and not can_crm:
            raise ValueError('CRM no autorizado')
        if plan.accion == 'consulta':
            permitted_sources = {s['fuente'] for s in sources or []}
            if not plan.consultas or any(q.fuente not in permitted_sources or any(c.fuente not in permitted_sources for c in q.cruces) for q in plan.consultas):
                raise ValueError('Fuente no autorizada')
            for q in plan.consultas:
                query_engine.validate(q)
        if (plan.accion != 'consulta' and plan.consultas) or (plan.accion != 'reportes' and plan.solicitudes):
            raise ValueError('Plan inconsistente')

        # Control M1: Las preguntas de solo lectura nunca pueden disparar propuestas de acción
        if plan.accion == 'operacion':
            is_neg_prompt = bool(re.search(r'\b(no\s+(crear|crea|registrar|registres|emitir|emitas|agregar|agregues|hacer|hagas|generar|generes))\b', normalized))
            has_create_intent = bool(
                re.search(r'\b(crea|crear|registra|registrar|nueva|nuevo|emite|emitir|agrega|agregar)\b', normalized)
                and not is_neg_prompt
            )
            if not has_create_intent or not plan.operacion_propuesta:
                return ReadPlan(
                    accion='ayuda',
                    mensaje='La consulta es de lectura informativa. No se generó ninguna propuesta de modificación.'
                )

        return plan
    except ProviderError:
        if local['estado'] == 'unsupported':
            return {'estado': 'needs_clarification', 'mensaje': 'El proveedor de IA no está disponible para preparar esta consulta nueva. Las consultas conocidas siguen disponibles; puedes reintentar o seleccionar un reporte.', 'opciones': [REGISTRY[k].titulo for k in available]}
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
        return {'estado': 'needs_clarification', 'tema': 'reportes', 'mensaje': str(exc.detail), 'consultas': [q.model_dump(mode='json') for q in plan.consultas]}, []
    with repo.transaction(snapshot=True) as db:
        fresh = context(db, ctx.usuario, ctx.empresa)
        if fresh.policy() != ctx.policy():
            raise HTTPException(403, 'La autorización cambió durante la consulta.')
        query_engine.reauthorize(db, fresh, query_scopes)
    fallback = '\n\n'.join(r['fuente'] + f": {r['registros_filtrados']} registros coincidentes; " +
        json.dumps(r['filas'], ensure_ascii=False, default=repo.json_default) +
        (' (detalle limitado; consulta más específica para verlo completo).' if not r['detalle_completo'] else '') for r in results)
    try:
        answer = get_provider().complete('Responde en español exclusivamente con estos resultados autorizados. '
            'Las métricas ya están calculadas. No inventes cifras ni predicciones, no extrapoles un detalle limitado. '
            'Distingue cero registros de dato no registrado. Explica alcance empresarial/obra y moneda desconocida. '
            'No afirmes que existe PDF/Excel de esta consulta dinámica.', question, {'consultas': results})
    except ProviderError:
        answer = fallback
    response = {'estado': 'ready', 'tema': 'reportes', 'mensaje': 'Consulta autorizada realizada.',
                'respuesta': answer, 'consultas': [q.model_dump(mode='json') for q in plan.consultas],
                'resultados_consulta': json.loads(json.dumps(results, default=repo.json_default))}
    return response, query_scopes


def consult(token, data, empresa=None):
    from app.services import reportes_services as reports
    with repo.transaction(snapshot=True) as db:
        ctx = context(db, reports.user(token), empresa)
        modules = _company_modules(db, ctx)
        can_reports = ctx.rol == 'ADMINISTRADOR' or 'Visualizar_reportes' in ctx.permisos
        can_crm = ctx.rol == 'ADMINISTRADOR' or 'Visualizar_clientes' in ctx.permisos
        sources = query_engine.catalog(ctx)
        if not (can_reports or can_crm or sources):
            raise HTTPException(403, 'No tiene capacidades de consulta habilitadas.')
        works = repo.works(db, ctx)
        available = [d.id for d in REGISTRY.values() if can_reports and allowed(ctx, d)
                     and (d.id != 'stock' or ctx.rol in {'ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA'})]
        conversation = None
        previous = None
        if data.conversacion:
            try:
                UUID(data.conversacion)
            except ValueError:
                raise HTTPException(422, 'Conversación inválida.')
            conversation = repo.get_conversation(db, (data.conversacion, ctx.empresa, ctx.usuario))
            if not conversation:
                raise HTTPException(404, 'Conversación inexistente.')
            previous = conversation.get('solicitud')
            try:
                if previous:
                    pending = ReportRequest.model_validate(previous)
                    authorize(db, ctx, pending)
            except (ValueError, KeyError, HTTPException):
                previous = None
        recent = repo.conversation_inputs(db, (data.conversacion,)) if conversation else []
        topic = recent[0].get('tema') if recent else None

    question = data.texto.strip()
    selected = getattr(data, 'solicitud', None)
    navigation_work = getattr(data, 'id_obra_contexto', None)
    if navigation_work and navigation_work not in {w['id_obra'] for w in works}:
        raise HTTPException(403, 'La obra de contexto no pertenece al ámbito autorizado.')
    previous_queries = recent[0].get('consultas') if recent else None
    explicit_works = [w['id_obra'] for w in works if re.search(r'\b' + re.escape(normalize(w['nombre'])) + r'\b', normalize(question)) or (w.get('codigo') and re.search(r'\b' + re.escape(normalize(w['codigo'])) + r'\b', normalize(question)))]
    effective_work = explicit_works[0] if len(explicit_works) == 1 else navigation_work

    plan = ReadPlan(accion='reportes', solicitudes=[selected]) if selected is not None else _plan(
        question, available, works, previous, topic, can_crm, sources, previous_queries,
        recent=recent, user_role=ctx.rol, id_obra_contexto=effective_work, permisos=ctx.permisos, modulos=modules
    )
    if isinstance(plan, dict) and plan.get('solicitud') and plan.get('estado') == 'needs_clarification' and navigation_work:
        pending = ReportRequest.model_validate(plan['solicitud'])
        if REGISTRY[pending.reporte].obra and not pending.filtros.id_obra and not re.search(r'\b(?:obra|proyecto)\s+\S+', normalize(question)):
            pending.filtros.id_obra = navigation_work
            plan = {'estado': 'ready', 'mensaje': 'Consulta en la obra seleccionada.', 'solicitud': pending.model_dump(mode='json')}

    executions = []
    query_scopes = []
    analysis_scope = None

    if isinstance(plan, ReadPlan) and plan.accion == 'conocimiento':
        know = knowledge_base.buscar_conocimiento(question, ctx.rol, permisos=ctx.permisos, modulos=modules)
        if know and know.get("tipo") == "detalle_modulos":
            mod_lines = []
            for m in know.get("modulos", []):
                mod_lines.append(f"• **{m['nombre']}** (Ruta: `{m['ruta']}`): {m['descripcion']}")
            resp_txt = "Información de módulos verificada en OBRATEC:\n" + "\n".join(mod_lines)
            if know.get("procedimientos"):
                p = know["procedimientos"][0]
                resp_txt += f"\n\n**Procedimiento: {p['tema']}**\n" + "\n".join(f"{i+1}. {paso}" for i, paso in enumerate(p["pasos"]))
        elif know and know.get("tipo") == "resumen_sistema":
            resp_txt = know["mensaje"] + "\n\nMódulos habilitados:\n" + "\n".join(f"• **{m['nombre']}** (`{m['ruta']}`): {m['descripcion']}" for m in know["modulos"])
        else:
            resp_txt = "OBRATEC incluye módulos de Obras (/proyectos), Costos (/control-costos), Inventario (/inventario), Compras (/compras), Órdenes de Trabajo (/ordenes-trabajo), Incidencias (/incidencias) y Consultas Técnicas (/consultas-tecnicas)."
        
        response = {
            'estado': 'ready',
            'tema': 'conocimiento',
            'mensaje': 'Información del sistema consultada.',
            'respuesta': resp_txt,
            'sugerencias': ['¿Cómo apruebo una orden de compra?', '¿Dónde veo las estimaciones?', '¿Cómo registro una incidencia?']
        }

    elif isinstance(plan, ReadPlan) and plan.accion == 'analisis':
        with repo.transaction(snapshot=True) as db:
            fresh = context(db, ctx.usuario, ctx.empresa)
            analisis, analysis_scope = assistant_analysis.analizar_con_alcance(db, fresh, id_obra=effective_work)
        
        recs_text = "\n".join(f"{i+1}. **{r['accion']}** [{r['prioridad']}]: {r['justificacion']}" for i, r in enumerate(analisis['recomendaciones']))
        inds_text = "\n".join(f"• **{ind['titulo']}**: {ind['valor']} ({ind['detalle']})" for ind in analisis['indicadores']) if analisis['indicadores'] else "• Sin alertas críticas activas."
        
        answer = (
            f"**Diagnóstico Operativo OBRATEC (Nivel de Riesgo: {analisis['nivel_riesgo']})**\n\n"
            f"**Indicadores Clave:**\n{inds_text}\n\n"
            f"**Recomendaciones Prioritarias:**\n{recs_text}"
        )
        response = {
            'estado': 'ready',
            'tema': 'analisis',
            'mensaje': 'Diagnóstico y recomendaciones operativas generadas.',
            'respuesta': answer,
            'resultado_analisis': analisis,
            'sugerencias': ['¿Cuáles son las incidencias críticas?', '¿Qué materiales están agotados?', '¿Qué órdenes de trabajo están atrasadas?']
        }

    elif isinstance(plan, ReadPlan) and plan.accion == 'operacion' and plan.operacion_propuesta:
        normalized_q = normalize(question)
        is_neg = bool(re.search(r'\b(no\s+(crear|crea|registrar|registres|emitir|emitas|agregar|agregues|hacer|hagas|generar|generes))\b', normalized_q))
        has_create_intent = bool(
            re.search(r'\b(crea|crear|registra|registrar|nueva|nuevo|emite|emitir|agrega|agregar)\b', normalized_q)
            and not is_neg
        )
        if not has_create_intent:
            response = {
                'estado': 'ready',
                'tema': 'ayuda',
                'mensaje': 'La consulta es de lectura informativa. No se generó ninguna propuesta de modificación.',
                'respuesta': 'He analizado su consulta. Al tratarse de una consulta informativa y no de una solicitud explícita de creación, no se generó ninguna operación.',
                'sugerencias': ['¿Cómo crear una incidencia?', '¿Cómo registrar una orden de trabajo?']
            }
        else:
            op = plan.operacion_propuesta
            # proponer_operacion genera determinísticamente el resumen seguro y valida Pydantic (M1)
            propuesta_ticket = assistant_operations.proponer_operacion(
                ctx, op.tipo_operacion, op.parametros, op.resumen, id_obra_contexto=navigation_work
            )
            answer = (
                f"He preparado la siguiente operación administrativa para tu confirmación:\n\n"
                f"• **Operación:** {propuesta_ticket['entidad']}\n"
                f"• **Resumen:** {propuesta_ticket['resumen']}\n\n"
                f"Haz clic en **Confirmar** para ejecutarla de forma segura en OBRATEC."
            )
            response = {
                'estado': 'ready',
                'tema': 'operacion',
                'mensaje': 'Operación preparada para confirmación.',
                'respuesta': answer,
                'operacion_propuesta': propuesta_ticket,
                'sugerencias': ['Confirmar ejecución', 'Cancelar operación']
            }

    elif isinstance(plan, ReadPlan) and plan.accion == 'consulta':
        for q in plan.consultas:
            by_work = (q.fuente in REGISTRY and q.fuente != 'stock') or (q.fuente in query_engine.MODULES and query_engine.MODULES[q.fuente][3])
            if by_work and len(explicit_works) == 1:
                q.filtros_fuente.id_obra = explicit_works[0]
            elif by_work and effective_work and not q.filtros_fuente.id_obra and not re.search(r'\b(todas|todos|por obra|por proyecto)\b', normalize(question)):
                q.filtros_fuente.id_obra = effective_work
        response, query_scopes = _consult_dynamic(ctx, plan, question)

    elif isinstance(plan, ReadPlan) and plan.accion == 'crm':
        answer = 'OBRATEC registra el seguimiento de clientes y unidades comerciales. Consulta el reporte de Saldo Comercial para ver el estado financiero por obra.'
        response = {'estado': 'ready', 'tema': 'crm', 'mensaje': 'Módulo CRM consultado.', 'respuesta': answer, 'sugerencias': ['¿Cuál es el saldo comercial por obra?']}

    else:
        if isinstance(plan, ReadPlan):
            response = {
                'estado': 'needs_clarification', 'mensaje': 'Puedo consultar costos, avances, unidades, materiales, personal, incidencias, diagnóstico operativo y asistir en operaciones. Indica el dato o la obra que necesitas.',
                'opciones': [REGISTRY[k].titulo for k in available]}
            if plan.accion == 'ayuda' and plan.mensaje:
                response['mensaje'] = plan.mensaje
            requests = plan.solicitudes if plan.accion == 'reportes' else []
        else:
            response = plan
            requests = [ReportRequest.model_validate(plan['solicitud'])] if plan['estado'] == 'ready' else []
        for request in requests:
            if request.reporte != 'stock' and len(explicit_works) == 1:
                request.filtros.id_obra = explicit_works[0]
            elif effective_work and request.reporte != 'stock' and not request.filtros.id_obra and not re.search(r'\b(todas|todos|por obra|por proyecto)\b', normalize(question)):
                request.filtros.id_obra = effective_work
            try:
                execution = reports.create(token, request, ctx.empresa)
            except HTTPException as exc:
                if exc.status_code not in {409, 422}:
                    raise
                response = {'estado': 'needs_clarification', 'mensaje': str(exc.detail), 'solicitud': request.model_dump(mode='json'), 'obras': works}
                break
            executions.append(execution)
        if executions:
            result = executions[0]['resultado']
            response.update(solicitud=result['solicitud'], ejecucion=executions[0], ejecuciones=executions)
            if result['reporte'] == 'saldo_comercial':
                from decimal import Decimal
                losses = bool(re.search(r'\b(perdidas?|negativos?)\b', normalize(question))) or result['solicitud']['filtros'].get('estado') == 'SALDO_NEGATIVO'
                state = 'SALDO_NEGATIVO' if losses else 'SALDO_POSITIVO'
                label = 'negativo' if losses else 'positivo'
                matching = sorted([r for r in result['filas'] if r['estado'] == state],
                                  key=lambda r: (r['moneda'], -Decimal(str(r['saldo_estimado']))))
                answer = 'No puedo confirmar ganancias reales: el sistema registra montos pactados de ventas, pero no cobros. '
                if matching:
                    answer += f'{len(matching)} obras con saldo comercial estimado {label}: ' + '; '.join(
                        f"{r['obra']}: {r['saldo_estimado']} {r['moneda']}" for r in matching[:30]) + '. '
                    if len(matching) > 30:
                        answer += f'Hay {len(matching)} obras; consulta el reporte para verlas todas. '
                else:
                    answer += f'No hay obras con saldo {label} comprobable en los registros consultados. '
                answer += f"{result['resumen']['obras_sin_datos_suficientes']} obras sin datos suficientes. El saldo compara ventas pactadas y costos registrados, no utilidad final; valida la moneda de las ventas."
                response.update(respuesta=answer, tema='finanzas')
            else:
                fallback = '\n'.join(e['resultado']['titulo'] + ': ' + ', '.join(f'{k.replace("_"," ")}: {v}' for k, v in e['resultado']['resumen'].items()) for e in executions)
                try:
                    answer = get_provider().complete('Responde la consulta usando exclusivamente estos reportes autorizados. '
                        'No calcules totales monetarios, ni mezcles monedas/versiones. Los resúmenes son cálculos del backend. '
                        'Cada detalle contiene hasta 100 filas; no concluyas ausencia sobre un detalle incompleto. '
                        'No inventes datos, recomendaciones ni acciones ejecutadas. Explica límites y pide precisión si falta un dato.', question,
                        {'reportes': [{'titulo': e['resultado']['titulo'], 'resumen': e['resultado']['resumen'],
                           'advertencias': e['resultado']['advertencias'], 'recomendaciones': e['resultado']['recomendaciones'],
                           'filas': e['resultado']['filas'][:100], 'detalle_completo': len(e['resultado']['filas']) <= 100} for e in executions],
                         'preguntas_anteriores': [r['texto'] for r in recent[:5]]})
                except ProviderError:
                    answer = fallback + '. ' + result['advertencias'][0]
                response.update(respuesta=answer, tema='reportes')

    ident = str(conversation['id']) if conversation else str(uuid4())
    with repo.transaction() as db:
        fresh = context(db, ctx.usuario, ctx.empresa)
        if analysis_scope is not None:
            assistant_analysis.reautorizar(db, fresh, analysis_scope)
        if response.get('tema') == 'conocimiento':
            response = _knowledge_response(question, fresh, _company_modules(db, fresh))
        if response.get('tema') == 'crm':
            fresh.require('Visualizar_clientes')
        if query_scopes:
            if fresh.policy() != ctx.policy():
                raise HTTPException(403, 'La autorización cambió durante la consulta.')
            query_engine.reauthorize(db, fresh, query_scopes)
        for execution in executions:
            reports.owned(db, execution['id'], token)
        if not conversation:
            repo.create_conversation(db, (ident, ctx.empresa, ctx.usuario))
        if response.get('solicitud') and response['estado'] in {'ready', 'needs_clarification'}:
            repo.set_conversation_request(db, (repo.j(response['solicitud']), ident))
        
        # Persistir metadata completa incluyendo texto_respuesta, accion y operacion_propuesta
        texto_resp = response.get('respuesta')
        metadata = {
            k: v for k, v in response.items()
            if k not in {'ejecucion', 'ejecuciones', 'respuesta', 'resultados_consulta', 'resultado_analisis'}
        }
        metadata['accion'] = plan.accion if isinstance(plan, ReadPlan) else response.get('accion', 'reportes')
        if response.get('operacion_propuesta'):
            metadata['operacion_propuesta'] = response['operacion_propuesta']
            
        repo.add_message(db, (ident, question, repo.j(metadata)))

    return dict(response, conversacion=ident)
