from datetime import date
import logging
from fastapi import APIRouter, Depends, Request, HTTPException, Path, Query
from app.services import cronograma_services as svc
from app.schemas.cronograma_schema import CronogramaCreate, CronogramaUpdate, PlanificacionUpdate
from app.utils.cronograma_errors import CronogramaError
from app.utils.security import verificar_token

router = APIRouter(prefix='/api/obras/{id_obra}/cronogramas',tags=['Cronogramas de Obra'])
log = logging.getLogger(__name__)


def ejecutar(func,*args,**kwargs):
    try:
        return func(*args,**kwargs)
    except CronogramaError as exc:
        raise HTTPException(exc.status_code,str(exc)) from exc
    except Exception as exc:
        log.exception('Error CU39')
        raise HTTPException(500,'No se pudo completar la operación de cronogramas.') from exc


def ip(request):
    return request.client.host if request.client else 'unknown'


@router.get('/')
def listar(id_obra:int=Path(gt=0),token:dict=Depends(verificar_token)):
    return ejecutar(svc.listar_cronogramas,id_obra,token)


@router.post('/',status_code=201)
def crear(datos:CronogramaCreate,request:Request,id_obra:int=Path(gt=0),token:dict=Depends(verificar_token)):
    return ejecutar(svc.crear_cronograma,id_obra,datos,token,ip(request))


@router.get('/retrasos')
def retrasos(id_obra:int=Path(gt=0),corte:date|None=None,token:dict=Depends(verificar_token)):
    return ejecutar(svc.consultar_retrasos,id_obra,token,corte)


@router.get('/{id_cronograma}')
def detalle(id_obra:int=Path(gt=0),id_cronograma:int=Path(gt=0),desde:date|None=None,
            hasta:date|None=None,corte:date|None=None,token:dict=Depends(verificar_token)):
    return ejecutar(svc.obtener_cronograma,id_obra,id_cronograma,token,desde,hasta,corte)


@router.put('/{id_cronograma}')
def actualizar(datos:CronogramaUpdate,request:Request,id_obra:int=Path(gt=0),
               id_cronograma:int=Path(gt=0),token:dict=Depends(verificar_token)):
    return ejecutar(svc.actualizar_cronograma,id_obra,id_cronograma,datos,token,ip(request))


@router.put('/{id_cronograma}/planificacion')
def planificar(datos:PlanificacionUpdate,request:Request,id_obra:int=Path(gt=0),
               id_cronograma:int=Path(gt=0),token:dict=Depends(verificar_token)):
    return ejecutar(svc.actualizar_cronograma,id_obra,id_cronograma,datos,token,ip(request),planificacion=True)


@router.delete('/{id_cronograma}')
def eliminar(request:Request,id_obra:int=Path(gt=0),id_cronograma:int=Path(gt=0),
             version:int=Query(gt=0),token:dict=Depends(verificar_token)):
    return ejecutar(svc.eliminar_cronograma,id_obra,id_cronograma,version,token,ip(request))
