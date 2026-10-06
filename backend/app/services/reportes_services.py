import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4, UUID
from fastapi import HTTPException
from app.repos import reportes_repos as repo
from app.services.reportes.authorization import context, authorize, allowed
from app.services.reportes.catalog import REGISTRY, FIELDS
from app.services.reportes.contracts import ReportRequest, Schedule
from app.services.reportes.interpreter import interpret
from app.services.reportes.exporters import export
from app.services.reportes.scheduling import next_run, period_request


def user(token):
    return int(token['nro_usuario'])


def catalog(token, empresa=None):
    with repo.transaction(snapshot=True) as db:
        ctx = context(db,user(token),empresa)
        ctx.require('Visualizar_reportes')
        definitions = [dict(id=d.id,titulo=d.titulo,descripcion=d.descripcion,requiere_obra=d.obra,fechas=d.fecha,fecha_campo=d.fecha_campo,
                            campos=[dict(campo=k,titulo=k.replace('_',' ').capitalize()) for k in FIELDS.get(d.id,'').split()]) for d in REGISTRY.values()
                       if allowed(ctx,d) and (d.id!='stock' or ctx.rol in {'ADMINISTRADOR','ADMINISTRADOR_EMPRESA'})]
        return {'reportes':definitions,'obras':repo.works(db,ctx), 'acciones':list(ctx.permisos) if ctx.rol!='ADMINISTRADOR' else ['Visualizar_reportes','Exportar_reportes','Enviar_reportes','Programar_reportes','Administrar_programaciones_reportes'], 'id_empresa':ctx.empresa}


def build(db, ctx, request, intersect=None, rows_allowed=None, source_allowlist=None):
    definition, scope = authorize(db,ctx,request)
    if intersect is not None and request.reporte!='stock':
        scope = sorted(set(scope)&set(intersect))
    data = repo.datasets(db,ctx,request,scope)
    # No se trunca: el usuario debe acotar un resultado excesivo.
    if len(data)>20000:
        raise HTTPException(422,'El reporte excede 20.000 filas. Acota obra, fechas o búsqueda.')
    # Las funciones del inventario incluyen campos internos que no son columnas del reporte.
    hidden = {'total_count','id_empresa','nombre_empresa'}
    data = [{k:v for k,v in row.items() if k not in hidden} for row in data]
    if rows_allowed is not None:
        data = [row for row in data if json.dumps(row,default=repo.json_default,sort_keys=True,ensure_ascii=False) in rows_allowed]
    def column_type(key):
        values = [row[key] for row in data if row.get(key) is not None]
        if any(isinstance(v,datetime) for v in values):
            return 'datetime'
        if any(isinstance(v,date) for v in values):
            return 'date'
        if any(isinstance(v,(Decimal,int,float)) and not isinstance(v,bool) for v in values):
            return 'number'
        return 'text'
    columns = [{'campo':k,'titulo':k.replace('_',' ').capitalize(), 'tipo':column_type(k)}
               for k in (data[0] if data else FIELDS.get(request.reporte,'').split())]
    available_columns = list(columns)
    presentation = request.presentacion
    fields = {c['campo'] for c in columns}
    if any(k not in fields for k in presentation.columnas) or (presentation.ordenar_por and presentation.ordenar_por not in fields):
        raise HTTPException(422, 'Selecciona columnas y ordenación del reporte actual.')
    if len(presentation.columnas) != len(set(presentation.columnas)):
        raise HTTPException(422, 'No repitas columnas en la presentación.')
    if presentation.columnas:
        indexed = {c['campo']: c for c in columns}
        columns = [indexed[k] for k in presentation.columnas]
    if presentation.ordenar_por:
        key = presentation.ordenar_por
        populated = [r for r in data if r.get(key) is not None]
        data = sorted(populated, key=lambda r: r[key], reverse=presentation.orden=='desc') + [r for r in data if r.get(key) is None]
    summary = {'registros':len(data)}
    warnings = [definition.descripcion]
    recommendations = []
    source_permissions = list(definition.permisos_extra)
    if request.reporte=='costos_periodo':
        totals = {}
        for row in data:
            key = (row['id_obra'], row['obra'], row['moneda'])
            totals[key] = totals.get(key, Decimal(0)) + Decimal(str(row['monto']))
        summary['costos_por_obra'] = [dict(id_obra=k[0], obra=k[1], moneda=k[2], monto_registrado=v) for k,v in totals.items()]
    if request.reporte=='estado_unidades':
        summary['unidades_por_estado'] = {state:sum(r['estado']==state for r in data) for state in sorted({r['estado'] for r in data if r['estado']})}
    if request.reporte=='saldo_comercial':
        summary.update(obras_con_saldo_positivo=sum(r['saldo_estimado'] is not None and r['saldo_estimado']>0 for r in data),
                       obras_con_saldo_negativo=sum(r['saldo_estimado'] is not None and r['saldo_estimado']<0 for r in data),
                       obras_sin_datos_suficientes=sum(r['saldo_estimado'] is None for r in data))
        warnings.append('Los montos CRM no tienen moneda propia: se muestran bajo la moneda de la obra; valida esa correspondencia. Sin cobros registrados no puede afirmarse ganancia realizada.')
    if request.reporte=='comparativo_costos':
        for key in ('costo_presupuestado','presupuesto_revisado','costo_ejecutado','variacion_revisada'):
            summary[key] = sum((Decimal(str(r.get(key) or 0)) for r in data),Decimal(0))
        summary['moneda'] = data[0]['moneda'] if data else None
        if summary['variacion_revisada']>0:
            recommendations.append({'accion':'Revisar partidas cuyo costo ejecutado supera el presupuesto revisado.', 'evidencia':str(summary['variacion_revisada']), 'tipo':'regla'})
        warnings.append('Menor gasto que el presupuesto no demuestra ahorro ni avance físico.')
    if request.reporte=='stock':
        can_read_purchases = (ctx.rol=='ADMINISTRADOR' or 'Visualizar_ordenes_compra' in ctx.permisos) and (source_allowlist is None or 'Visualizar_ordenes_compra' in source_allowlist)
        pending = {r['id_material']:Decimal(str(r['pendiente'])) for r in repo.pending_purchases(db,ctx.empresa)} if can_read_purchases else {}
        if can_read_purchases:
            source_permissions.append('Visualizar_ordenes_compra')
        shortages = [r for r in data if Decimal(str(r['stock_actual'] or 0))<Decimal(str(r['stock_minimo'] or 0))]
        summary['materiales_bajo_minimo'] = len(shortages)
        for r in shortages[:20]:
            deficit = Decimal(str(r['stock_minimo'] or 0))-Decimal(str(r['stock_actual'] or 0))
            recommendation = {'accion':f"Revisar reposición de {r['nombre_material']}", 'deficit_minimo':str(deficit), 'tipo':'regla'}
            if can_read_purchases:
                incoming = pending.get(r['id_material'],Decimal(0))
                recommendation.update(pendiente_recepcion=str(incoming),reposicion_minima_sugerida=str(max(deficit-incoming,Decimal(0))))
            recommendations.append(recommendation)
        warnings.append('Reposición mínima por stock registrado, descontando compras aprobadas cuando tienes permiso. Verifica demanda y entrega; no es una orden de compra ni una optimización de precios.')
    if request.reporte=='avance_ejecutivo':
        values = [Decimal(str(r['porcentaje_avance'])) for r in data if r['porcentaje_avance'] is not None]
        summary['unidades_sin_avance'] = len(data)-len(values)
        summary['avance_promedio_registrado'] = (sum(values)/len(values)).quantize(Decimal('.01')) if values else None
        if request.filtros.desde or request.filtros.hasta:
            warnings.append('El avance corresponde al último registro dentro del período; unidades sin registro se muestran sin avance. El estado de la unidad es el actual.')
    if request.reporte in {'asignacion_personal','utilizacion_personal'}:
        summary['personas_distintas'] = len({row['id_usuario'] for row in data})
    if request.reporte=='utilizacion_personal':
        summary['ordenes_distintas'] = len({row['orden_nro'] for row in data})
    if request.reporte in {'incidencias','incidencias_criticas'}:
        summary['incidencias_criticas'] = sum(row['prioridad']=='CRITICA' for row in data)
    if request.reporte=='presupuestario':
        warnings.append('Cada fila es una versión. No se suman versiones ni monedas distintas.')
    cutoff = repo.cutoff(db)['corte']
    result = {'version':1,'reporte':definition.id,'titulo':(presentation.titulo or '').strip() or definition.titulo,'id_empresa':ctx.empresa,
              'corte':cutoff.isoformat(),'solicitud':request.model_dump(mode='json'),'columnas':columns,
              'filas':data,'resumen':summary,'advertencias':warnings,'recomendaciones':recommendations,'permisos_fuente':source_permissions}
    result['columnas_disponibles'] = available_columns
    return result,scope


def create(token, request, empresa=None):
    with repo.transaction(snapshot=True) as db:
        ctx = context(db,user(token),empresa)
        result,scope = build(db,ctx,request)
    ident = str(uuid4())
    with repo.transaction() as db:
        # Revalidar antes de persistir el resultado de la lectura.
        fresh = context(db,ctx.usuario,ctx.empresa)
        _,fresh_scope = authorize(db,fresh,request)
        if fresh.policy()!=ctx.policy() or not set(scope).issubset(fresh_scope):
            raise HTTPException(403,'La autorización cambió durante la consulta.')
        repo.insert_ready_execution(db,(ident,ctx.empresa,ctx.usuario,repo.j(request.model_dump(mode='json')),repo.j(ctx.policy()),scope,repo.j(result)))
    return {'id':ident,'estado':'LISTO','resultado':json.loads(json.dumps(result,default=repo.json_default))}


def owned(db, ident, token, action='Visualizar_reportes'):
    item = repo.get_execution(db,(ident,))
    if not item:
        raise HTTPException(404,'Reporte inexistente.')
    ctx = context(db,user(token),item['id_empresa'])
    if ctx.usuario != item['id_usuario']:
        raise HTTPException(403,'El reporte pertenece a otro actor.')
    _,scope = authorize(db,ctx,ReportRequest.model_validate(item['solicitud']),action)
    for permission in (item.get('resultado') or {}).get('permisos_fuente',[]):
        ctx.require(permission)
    if ctx.policy()!=item['politica'] or not set(item['alcance']).issubset(scope):
        raise HTTPException(403,'El acceso al reporte cambió. Genera una nueva consulta.')
    return item,ctx


def get_execution(token, ident):
    with repo.transaction(snapshot=True) as db:
        item,_ = owned(db,ident,token)
        return {'id':str(item['id']),'estado':item['estado'],'resultado':item['resultado'],'error':item['error']}


def history(token, empresa=None):
    with repo.transaction(snapshot=True) as db:
        ctx = context(db,user(token),empresa)
        ctx.require('Visualizar_reportes')
        return repo.list_executions(db,(ctx.empresa,ctx.usuario))


def export_execution(token, ident, format):
    if format not in {'pdf','xlsx'}:
        raise HTTPException(422,'Elige PDF o XLSX.')
    with repo.transaction(snapshot=True) as db:
        item,_ = owned(db,ident,token,'Exportar_reportes')
        if not item['resultado']:
            raise HTTPException(410,'El resultado caducó. Genera un reporte nuevo.')
        if item['estado']!='LISTO':
            raise HTTPException(409,'El reporte todavía no está disponible.')
    try:
        content = export(item['resultado'],format)
    except ValueError as exc:
        raise HTTPException(422,str(exc))
    if len(content)>5*1024*1024:
        raise HTTPException(422,'El archivo supera 5 MiB. Acota el reporte para exportarlo.')
    with repo.transaction() as db:
        owned(db,ident,token,'Exportar_reportes')
        result = repo.save_file(db,(str(uuid4()),ident,format,f"{item['solicitud']['reporte']}.{format}",content,hashlib.sha256(content).hexdigest()))
    return result


def download(token, ident):
    with repo.transaction(snapshot=True) as db:
        file = repo.get_file(db,(ident,))
        if not file:
            raise HTTPException(404,'El archivo no existe o ha caducado.')
        owned(db,file['ejecucion'],token,'Exportar_reportes')
        return bytes(file['contenido']),file['nombre'],file['formato']


def interpretation(token, data, empresa=None):
    with repo.transaction() as db:
        ctx = context(db,user(token),empresa)
        ctx.require('Visualizar_reportes')
        works = repo.works(db,ctx)
        available = [d.id for d in REGISTRY.values() if allowed(ctx,d) and (d.id!='stock' or ctx.rol in {'ADMINISTRADOR','ADMINISTRADOR_EMPRESA'})]
        conversation = None
        if data.conversacion:
            try:
                UUID(data.conversacion)
            except ValueError:
                raise HTTPException(422,'Conversación inválida.')
            conversation = repo.get_conversation(db,(data.conversacion,ctx.empresa,ctx.usuario))
            if not conversation:
                raise HTTPException(404,'La conversación no pertenece a esta sesión o ha expirado.')
        previous = conversation['solicitud'] if conversation else None
        if previous:
            authorize(db,ctx,ReportRequest.model_validate(previous))
        response = interpret(data.texto,available,works,previous)
        if response['estado']=='unsupported' and data.usar_ia:
            from app.services.ai.providers import get_provider, ProviderError
            try:
                proposed = get_provider().interpret_request(data.texto,[dict(id=k,descripcion=REGISTRY[k].descripcion) for k in available],works,previous)
                candidate = ReportRequest.model_validate(proposed)
                authorize(db,ctx,candidate)
                response = {'estado':'ready','solicitud':candidate.model_dump(mode='json'),'mensaje':'Solicitud interpretada; revisa los filtros antes de generar.'}
            except (ProviderError,ValueError,HTTPException):
                response['mensaje'] += ' La interpretación local sigue disponible.'
        if response['estado']=='ready':
            try:
                candidate = ReportRequest.model_validate(response['solicitud'])
                authorize(db,ctx,candidate)
            except ValueError:
                response = {'estado':'needs_clarification','mensaje':'Revisa las fechas: usa AAAA-MM-DD y una fecha inicial anterior a la final.'}
            except HTTPException as exc:
                if exc.status_code != 422:
                    raise
                response = {'estado':'needs_clarification','mensaje':str(exc.detail),'obras':works}
        ident = str(conversation['id']) if conversation else str(uuid4())
        if not conversation:
            repo.create_conversation(db,(ident,ctx.empresa,ctx.usuario))
        if response['estado']=='ready':
            repo.set_conversation_request(db,(repo.j(response['solicitud']),ident))
        repo.add_message(db,(ident,data.texto,repo.j(response)))
        return dict(response,conversacion=ident)


def recipients(token, empresa=None):
    with repo.transaction(snapshot=True) as db:
        ctx = context(db,user(token),empresa)
        ctx.require('Enviar_reportes')
        # Trabajadores/clientes nunca reciben un directorio empresarial.
        if ctx.rol not in {'ADMINISTRADOR','ADMINISTRADOR_EMPRESA','JEFE DE OBRA'}:
            return [{'id_usuario':ctx.usuario,'nombre': 'Mi cuenta'}]
        return repo.list_recipients(db,(ctx.empresa,))


def validate_recipient(db, sender, receiver, request):
    recipient = context(db,receiver,sender.empresa)
    if recipient.rol=='ADMINISTRADOR' or not recipient.correo:
        raise HTTPException(422,'Selecciona un destinatario de la empresa con correo configurado.')
    if sender.rol not in {'ADMINISTRADOR','ADMINISTRADOR_EMPRESA','JEFE DE OBRA'} and sender.usuario!=receiver:
        raise HTTPException(403,'Solo puede enviar a su propia cuenta.')
    authorize(db,recipient,request,'Exportar_reportes')
    return recipient


def enqueue_delivery(db, execution, recipients, formats, identity):
    for receiver in set(recipients):
        repo.insert_delivery(db,(str(uuid4()),execution,receiver,repo.j(list(set(formats))),f'{identity}:{receiver}'))


def send(token, ident, delivery, key):
    with repo.transaction() as db:
        item,ctx = owned(db,ident,token,'Enviar_reportes')
        if item['estado']!='LISTO':
            raise HTTPException(409,'El reporte todavía no está listo.')
        request = ReportRequest.model_validate(item['solicitud'])
        for receiver in set(delivery.destinatarios):
            validate_recipient(db,ctx,receiver,request)
        enqueue_delivery(db,ident,delivery.destinatarios,delivery.formatos,f'manual:{ident}:{key}')
        return {'estado':'PENDIENTE','mensaje':'Envío encolado para el worker.'}


def delivery_history(token, ident):
    with repo.transaction(snapshot=True) as db:
        owned(db,ident,token)
        return repo.list_deliveries(db,(ident,))


def create_schedule(token, config, empresa=None):
    value = config.model_dump(mode='json')
    due = next_run(value)
    with repo.transaction() as db:
        ctx = context(db,user(token),empresa)
        ctx.require('Programar_reportes')
        ctx.require('Enviar_reportes')
        authorize(db,ctx,ReportRequest.model_validate(period_request(value,due)))
        for receiver in set(config.destinatarios):
            validate_recipient(db,ctx,receiver,config.solicitud)
        ident = str(uuid4())
        repo.insert_schedule(db,(ident,ctx.empresa,ctx.usuario,repo.j(value),config.habilitada,due))
        for receiver in set(config.destinatarios):
            repo.insert_schedule_recipient(db,(ident,receiver))
        return {'id':ident,'next_run':due,'habilitada':config.habilitada}


def schedules(token, empresa=None):
    with repo.transaction(snapshot=True) as db:
        ctx = context(db,user(token),empresa)
        ctx.require('Programar_reportes')
        admin = ctx.rol=='ADMINISTRADOR' or 'Administrar_programaciones_reportes' in ctx.permisos
        return repo.list_schedules(db,(ctx.empresa,admin,ctx.usuario))


def change_schedule(token, ident, enabled=None, execute=False):
    with repo.transaction() as db:
        item = repo.get_schedule_locked(db,(ident,))
        if not item:
            raise HTTPException(404,'Programación inexistente.')
        ctx = context(db,user(token),item['id_empresa'])
        ctx.require('Programar_reportes')
        if ctx.usuario!=item['id_usuario']:
            ctx.require('Administrar_programaciones_reportes')
        owner = context(db,item['id_usuario'],item['id_empresa'])
        owner.require('Programar_reportes')
        config = item['configuracion']
        authorize(db,owner,ReportRequest.model_validate(period_request(config,datetime.now(timezone.utc))))
        if execute:
            if not item['habilitada']:
                raise HTTPException(409,'Activa la programación antes de ejecutarla.')
            return queue_schedule(db,item,datetime.now(timezone.utc))
        due = next_run(config)
        return repo.toggle_schedule(db,(enabled,due,ident))


def queue_schedule(db, item, occurrence):
    ctx = context(db,item['id_usuario'],item['id_empresa'])
    ctx.require('Programar_reportes')
    ctx.require('Enviar_reportes')
    request = ReportRequest.model_validate(period_request(item['configuracion'],occurrence))
    _,scope = authorize(db,ctx,request)
    ident = str(uuid4())
    record = repo.insert_scheduled_execution(db,(ident,ctx.empresa,ctx.usuario,item['id'],occurrence,repo.j(request.model_dump(mode='json')),repo.j(ctx.policy()),scope))
    enqueue_delivery(db,str(record['id']),item['configuracion']['destinatarios'],item['configuracion']['formatos'],f"schedule:{item['id']}:{occurrence.isoformat()}")
    return {'id':str(record['id']),'estado':'PENDIENTE'}


def assistant(token, data, empresa=None):
    from app.services.ai.assistant_service import consult
    return consult(token, data, empresa)
