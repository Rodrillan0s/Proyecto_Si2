from datetime import date
from typing import Literal
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, ConfigDict
from app.repos import suscripcion_repos as repo
from app.services import suscripcion_services as service
from app.utils.security import verificar_token, exigir_rol
from app.services import planes_services
from app.services.planes_catalog import MODULOS
from app.repos import planes_repos

router = APIRouter(prefix='/api/suscripciones', tags=['Suscripciones'])


class Asignacion(BaseModel):
    codigo_plan: str = Field(min_length=1, max_length=20)
    estado: Literal['ACTIVA', 'SUSPENDIDA', 'CANCELADA'] = 'ACTIVA'
    fecha_inicio: date
    fecha_fin: date | None = None


class ConfiguracionPlan(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    version: int = Field(ge=1, strict=True)
    nombre: str = Field(min_length=1,max_length=80)
    descripcion: str = Field(max_length=1000)
    modulos: list[str] = Field(max_length=15)
    limite_usuarios: int = Field(ge=1,le=100000,strict=True)
    limite_obras: int = Field(ge=1,le=100000,strict=True)
    consultas_ia_mes: int = Field(ge=0,le=1000000,strict=True)
    nivel_reportes: Literal['NINGUNO','OPERATIVOS','TODOS']
    exportar_reportes: bool = Field(strict=True)
    automatizar_reportes: bool = Field(strict=True)


class GuardarPlan(ConfiguracionPlan):
    confirmacion: str = Field(min_length=64,max_length=64)


@router.get('/configuracion/modulos')
def modulos(token: dict = Depends(exigir_rol('ADMINISTRADOR'))):
    return {'data':[{'codigo':k,'nombre':v} for k,v in MODULOS.items()]}


@router.post('/planes/{codigo}/previsualizar')
def previsualizar_plan(codigo: str,datos: ConfiguracionPlan,token: dict = Depends(exigir_rol('ADMINISTRADOR'))):
    return {'data':planes_services.configurar(token,codigo,datos.model_dump())}


@router.put('/planes/{codigo}')
def configurar_plan(codigo: str,datos: GuardarPlan,token: dict = Depends(exigir_rol('ADMINISTRADOR'))):
    valor=datos.model_dump(exclude={'confirmacion'})
    return {'data':planes_services.configurar(token,codigo,valor,datos.confirmacion)}


@router.get('/planes/{codigo}/historial')
def historial_plan(codigo: str,token: dict = Depends(exigir_rol('ADMINISTRADOR'))):
    planes_services.exigir_global(token)
    with planes_repos.transaccion() as cur:
        if not planes_repos.obtener(cur,codigo):
            from fastapi import HTTPException
            raise HTTPException(404,'Plan no encontrado.')
    return {'data':planes_repos.historial(codigo)}


@router.get('/planes')
def planes(token: dict = Depends(verificar_token)):
    return {'success': True, 'data': repo.listar_planes()}


@router.get('/mi-empresa')
def mi_empresa(id_empresa: int | None = Query(default=None, gt=0), token: dict = Depends(verificar_token)):
    return {'success': True, 'data': service.consultar(token, id_empresa)}


@router.get('/empresas')
def empresas(token: dict = Depends(exigir_rol('ADMINISTRADOR'))):
    return {'success': True, 'data': [service.enriquecer(f) for f in repo.listar_suscripciones()]}


@router.get('/empresas/{id_empresa}/historial')
def historial(id_empresa: int, token: dict = Depends(exigir_rol('ADMINISTRADOR'))):
    service.consultar(token, id_empresa)
    return {'success': True, 'data': repo.historial(id_empresa)}


@router.put('/empresas/{id_empresa}')
def asignar(id_empresa: int, datos: Asignacion, token: dict = Depends(exigir_rol('ADMINISTRADOR'))):
    return {'success': True, 'data': service.asignar(token, id_empresa, datos.model_dump())}
