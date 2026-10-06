"""Cola durable. No arrancar desde Uvicorn ni enviar correo dentro de un lock DB."""
import json
import logging
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from app.repos import reportes_repos as repo
from app.services import reportes_services as reports
from app.services.email_service import enviar_reporte, ReportEmailError
from .authorization import context, authorize
from .contracts import ReportRequest
from .exporters import export
from .scheduling import next_run

log = logging.getLogger(__name__)


def schedule_due():
    with repo.transaction() as db:
        now = datetime.now(timezone.utc)
        due = repo.due_schedules(db)
        for item in due:
            try:
                # Una sola ocurrencia reciente. Las anteriores se omiten explícitamente.
                occurrence = item['next_run']
                if occurrence < now-timedelta(days=1):
                    candidate = next_run(item['configuracion'],now-timedelta(days=1))
                    occurrence = None
                    while candidate<=now:
                        occurrence = candidate
                        candidate = next_run(item['configuracion'],candidate)
                if occurrence:
                    reports.queue_schedule(db,item,occurrence)
                repo.advance_schedule(db,(next_run(item['configuracion'],now),'Se omitieron ocurrencias antiguas.' if item['next_run']<now-timedelta(days=1) else None,item['id']))
            except (HTTPException,ValueError) as exc:
                repo.suspend_schedule(db,(str(getattr(exc,'detail',exc))[:300],item['id']))


def claim_execution():
    with repo.transaction() as db:
        repo.expire_generations(db)
        return repo.claim_execution_row(db)


def generate(item):
    try:
        with repo.transaction(snapshot=True) as db:
            ctx = context(db,item['id_usuario'],item['id_empresa'])
            if item['programacion']:
                ctx.require('Programar_reportes')
                schedule = repo.get_schedule_enabled(db,(item['programacion'],))
                if not schedule or not schedule['habilitada']:
                    raise HTTPException(403,'La programación está pausada.')
            request = ReportRequest.model_validate(item['solicitud'])
            result,scope = reports.build(db,ctx,request)
        with repo.transaction() as db:
            repo.complete_execution(db,(repo.j(result),scope,repo.j(ctx.policy()),item['id']))
    except Exception as exc:
        fail = isinstance(exc,(HTTPException,ValueError)) or item['intentos']>=3
        with repo.transaction() as db:
            repo.fail_execution(db,('FALLIDO' if fail else 'PENDIENTE',str(exc.detail)[:300] if isinstance(exc,HTTPException) else 'Falló la generación del reporte.',item['id']))
def claim_delivery():
    with repo.transaction() as db:
        # Un proceso que murió enviando puede haber alcanzado Brevo. No duplicar.
        repo.expire_deliveries(db)
        repo.fail_deliveries_generation(db)
        return repo.claim_delivery_row(db)


def row_identity(row):
    return json.dumps(row,default=repo.json_default,sort_keys=True,ensure_ascii=False)


def recipient_result(db, item, delivery):
    sender = context(db,item['id_usuario'],item['id_empresa'])
    sender.require('Enviar_reportes')
    if item['programacion']:
        sender.require('Programar_reportes')
        schedule = repo.get_schedule_enabled(db,(item['programacion'],))
        if not schedule or not schedule['habilitada']:
            raise HTTPException(403,'La programación está pausada.')
    request = ReportRequest.model_validate(item['solicitud'])
    recipient = reports.validate_recipient(db,sender,delivery['id_usuario'],request)
    original,scope = reports.build(db,sender,request)
    original_rows = {row_identity(row) for row in original['filas']}
    result,recipient_scope = reports.build(db,recipient,request,intersect=scope,rows_allowed=original_rows,source_allowlist=original.get('permisos_fuente',[]))
    # No basta la intersección de obras: un trabajador ve únicamente sus filas.
    filtered = [row for row in result['filas'] if row_identity(row) in original_rows]
    if len(filtered)!=len(result['filas']):
        # Evitar resúmenes calculados con filas que el emisor no puede ver.
        raise HTTPException(403,'El ámbito del emisor no permite este envío al destinatario.')
    if request.reporte!='stock' and not set(scope)&set(recipient_scope):
        raise HTTPException(403,'Emisor y destinatario no comparten obras autorizadas.')
    return result,recipient,sender


def deliver(delivery):
    state,error,message_id,result = 'FALLIDO',None,None,None
    try:
        with repo.transaction(snapshot=True) as db:
            item = repo.get_execution(db,(delivery['ejecucion'],))
            result,recipient,sender = recipient_result(db,item,delivery)
        attachments = [(result['reporte']+'.'+fmt,export(result,fmt)) for fmt in delivery['formatos']]
        if sum(len(content) for _,content in attachments)>5*1024*1024:
            raise HTTPException(422,'Los adjuntos superan 5 MiB. Acota el reporte.')
        # Revalidar inmediatamente antes de la operación externa.
        with repo.transaction(snapshot=True) as db:
            fresh = context(db,sender.usuario,sender.empresa)
            rec = reports.validate_recipient(db,fresh,recipient.usuario,ReportRequest.model_validate(item['solicitud']))
            fresh.require('Enviar_reportes')
            for permission in result.get('permisos_fuente',[]):
                fresh.require(permission)
                rec.require(permission)
            _,scope = authorize(db,fresh,ReportRequest.model_validate(item['solicitud']))
            _,rec_scope = authorize(db,rec,ReportRequest.model_validate(item['solicitud']))
            if fresh.policy()!=sender.policy() or rec.policy()!=recipient.policy() or rec.correo!=recipient.correo:
                raise HTTPException(403,'La autorización cambió durante el envío.')
            ids = {r['id_obra'] for r in result['filas'] if 'id_obra' in r}
            if not ids.issubset(set(scope)&set(rec_scope)):
                raise HTTPException(403,'Se revocó acceso a una obra del reporte.')
            if item['programacion']:
                fresh.require('Programar_reportes')
                scheduled = repo.get_schedule_enabled(db,(item['programacion'],))
                if not scheduled or not scheduled['habilitada']:
                    raise HTTPException(403,'La programación está pausada.')
        message_id = enviar_reporte(recipient.correo,result['titulo'],
            'Reporte OBRATEC. Corte: '+result['corte']+'\n'+'\n'.join(result['advertencias']),attachments,delivery['identidad'])
        state = 'ACEPTADO'
    except ReportEmailError as exc:
        error = str(exc)
        state = 'INCIERTO' if exc.uncertain else 'PENDIENTE' if exc.retryable and delivery['intentos']<3 else 'FALLIDO'
    except HTTPException as exc:
        error = str(exc.detail)[:300]
    except ValueError as exc:
        error = str(exc)[:300]
    except Exception:
        error = 'No se pudo preparar o confirmar el envío.'
    with repo.transaction() as db:
        repo.complete_delivery(db,(state,error,message_id,repo.j({'corte':result['corte'],'registros':len(result['filas'])}) if result else None,delivery['id']))


def _tick():
    schedule_due()
    job = claim_execution()
    if job:
        generate(job)
    delivery = claim_delivery()
    if delivery:
        deliver(delivery)
    with repo.transaction() as db:
        repo.purge_files(db)
        repo.purge_conversations(db)
        repo.purge_results(db)
    return bool(job or delivery)


def tick():
    from app.services.backups.coordination import writer
    from app.services.backups.settings import BackupError
    try:
        with writer('REPORTES_WORKER'):
            return _tick()
    except BackupError as exc:
        if exc.code == 'BACKUP_MAINTENANCE':
            return False
        raise
