from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Query, UploadFile, File
from fastapi.responses import Response
from app.utils.security import verificar_token
from app.services import reportes_services as service
from app.services.reportes.contracts import ReportRequest, Interpretation, Delivery, Schedule, SchedulePatch

router = APIRouter(prefix='/api/reportes',tags=['Reportes'])
voice_router = APIRouter(prefix='/api/voz',tags=['Voz'])


@router.get('/catalogo')
def catalog(id_empresa: int | None=Query(None,gt=0),token=Depends(verificar_token)):
    return service.catalog(token,id_empresa)


@router.post('/interpretar')
def interpret(data: Interpretation,id_empresa: int | None=Query(None,gt=0),token=Depends(verificar_token)):
    return service.interpretation(token,data,id_empresa)


@router.get('/ejecuciones')
def history(id_empresa: int | None=Query(None,gt=0),token=Depends(verificar_token)):
    return service.history(token,id_empresa)


@router.post('/ejecuciones')
def create(data: ReportRequest,id_empresa: int | None=Query(None,gt=0),token=Depends(verificar_token)):
    return service.create(token,data,id_empresa)


@router.get('/ejecuciones/{ident}')
def execution(ident: UUID,token=Depends(verificar_token)):
    return service.get_execution(token,str(ident))


@router.post('/ejecuciones/{ident}/exportaciones')
def export(ident: UUID,formato: Literal['pdf','xlsx'],token=Depends(verificar_token)):
    return service.export_execution(token,str(ident),formato)


@router.get('/archivos/{ident}')
def download(ident: UUID,token=Depends(verificar_token)):
    content,name,format = service.download(token,str(ident))
    mime = 'application/pdf' if format=='pdf' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return Response(content,media_type=mime,headers={'Content-Disposition':f'attachment; filename="{name}"','Cache-Control':'private, no-store'})


@router.get('/destinatarios')
def recipients(id_empresa: int | None=Query(None,gt=0),token=Depends(verificar_token)):
    return service.recipients(token,id_empresa)


@router.post('/ejecuciones/{ident}/envios')
def send(ident: UUID,data: Delivery,idempotency_key: UUID=Header(...),token=Depends(verificar_token)):
    return service.send(token,str(ident),data,str(idempotency_key))


@router.get('/ejecuciones/{ident}/envios')
def deliveries(ident: UUID,token=Depends(verificar_token)):
    return service.delivery_history(token,str(ident))


@router.get('/programaciones')
def schedules(id_empresa: int | None=Query(None,gt=0),token=Depends(verificar_token)):
    return service.schedules(token,id_empresa)


@router.post('/programaciones')
def schedule(data: Schedule,id_empresa: int | None=Query(None,gt=0),token=Depends(verificar_token)):
    return service.create_schedule(token,data,id_empresa)


@router.patch('/programaciones/{ident}')
def toggle(ident: UUID,data: SchedulePatch,token=Depends(verificar_token)):
    return service.change_schedule(token,str(ident),data.habilitada)


@router.post('/programaciones/{ident}/ejecutar')
def run(ident: UUID,token=Depends(verificar_token)):
    return service.change_schedule(token,str(ident),execute=True)


@voice_router.post('/transcribir')
def voice(audio: UploadFile=File(...),token=Depends(verificar_token),id_empresa: int | None=Query(None,gt=0)):
    service.catalog(token,id_empresa)
    content = audio.file.read(5*1024*1024+1)
    if not content or len(content)>5*1024*1024:
        raise HTTPException(422,'La grabación debe tener entre 1 byte y 5 MiB.')
    from app.services.reportes.speech import transcribe
    return transcribe(content)
