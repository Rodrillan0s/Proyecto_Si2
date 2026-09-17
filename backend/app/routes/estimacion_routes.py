from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.services import estimacion_services as service
from app.utils.security import exigir_permiso

router = APIRouter(prefix='/api/estimaciones', tags=['Estimaciones APU'])


class ApuRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)
    id_unidad_medida: int
    descripcion: Optional[str] = None
    id_obra: Optional[int] = None
    id_padre: Optional[int] = None
    id_estructura: Optional[int] = None
    tipo_analisis_precio_unitario: str = 'OBRA_GRIS'
    calidad: Optional[str] = None


class InsumoRequest(BaseModel):
    tipo_insumo: str
    nombre: str = Field(min_length=1, max_length=200)
    id_unidad_medida: int
    cantidad: float = Field(ge=0)
    precio_unitario: float = Field(ge=0)
    id_material: Optional[int] = None
    id_mano_obra: Optional[int] = None
    orden: int = 1


def _ip(request: Request) -> str:
    return request.client.host if request.client else 'unknown'


def _call(callback, *args):
    try:
        return callback(*args)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/analisis_precio_unitario')
def listar_apu(id_obra: Optional[int] = None, tipo_analisis_precio_unitario: Optional[str] = None, calidad: Optional[str] = None, activo: Optional[bool] = True, token=Depends(exigir_permiso('Visualizar_estimaciones'))):
    return _call(service.list_apu, token, {'id_obra': id_obra, 'tipo_analisis_precio_unitario': tipo_analisis_precio_unitario, 'calidad': calidad, 'activo': activo})


@router.get('/analisis_precio_unitario/{id_apu}')
def detalle_apu(id_apu: int, token=Depends(exigir_permiso('Visualizar_estimaciones'))):
    return _call(service.get_apu, id_apu, token)


@router.post('/analisis_precio_unitario', status_code=201)
def crear_apu(request: Request, data: ApuRequest, token=Depends(exigir_permiso('Registrar_estimaciones'))):
    return _call(service.create_apu, data.model_dump(), token, _ip(request))


@router.put('/analisis_precio_unitario/{id_apu}')
def actualizar_apu(id_apu: int, request: Request, data: dict = Body(...), token=Depends(exigir_permiso('Modificar_estimaciones'))):
    return _call(service.update_apu, id_apu, data, token, _ip(request))


@router.delete('/analisis_precio_unitario/{id_apu}')
def eliminar_apu(id_apu: int, request: Request, token=Depends(exigir_permiso('Eliminar_estimaciones'))):
    return {'success': True, 'message': 'Use baja lógica mediante activo=false.', 'data': _call(service.update_apu, id_apu, {'activo': False}, token, _ip(request))}


@router.post('/analisis_precio_unitario/{id_apu}/duplicar', status_code=201)
def duplicar_apu(id_apu: int, request: Request, token=Depends(exigir_permiso('Registrar_estimaciones'))):
    from app.repos import estimacion_repos
    try:
        result = estimacion_repos.duplicate_apu(id_apu, service._empresa(token))
        if not result:
            raise ValueError('La partida no existe o no pertenece a su empresa.')
        service._log(token, 'DUPLICAR_APU', f'Partida {id_apu} duplicada.', _ip(request))
        return {'success': True, 'data': result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/analisis_precio_unitario/{id_apu}/insumos')
def listar_insumos(id_apu: int, token=Depends(exigir_permiso('Visualizar_estimaciones'))):
    return _call(service.list_insumos, id_apu, token)


@router.post('/analisis_precio_unitario/{id_apu}/insumos', status_code=201)
def agregar_insumo(id_apu: int, request: Request, data: InsumoRequest, token=Depends(exigir_permiso('Modificar_estimaciones'))):
    return _call(service.create_insumo, id_apu, data.model_dump(), token, _ip(request))


@router.put('/analisis_precio_unitario/{id_apu}/insumos/{insumo_id}')
def actualizar_insumo(insumo_id: int, data: dict = Body(...), token=Depends(exigir_permiso('Modificar_estimaciones'))):
    from app.repos import estimacion_repos
    try:
        result = estimacion_repos.update_insumo(insumo_id, data, service._empresa(token))
        if not result:
            raise ValueError('El insumo no existe o no pertenece a su empresa.')
        return {'success': True, 'data': result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete('/analisis_precio_unitario/{id_apu}/insumos/{insumo_id}')
def eliminar_insumo(insumo_id: int, token=Depends(exigir_permiso('Modificar_estimaciones'))):
    from app.repos import estimacion_repos
    return {'success': True, 'data': estimacion_repos.delete_where('t_analisi_precio_unitario_insumo', 'id_analisis_precio_unitario_insumo', insumo_id, service._empresa(token))}


@router.get('/mano-obra')
def listar_mano_obra(token=Depends(exigir_permiso('Visualizar_mano_obra'))):
    from app.repos.estimacion_repos import _query
    return {'success': True, 'data': _query('SELECT * FROM obras.t_mano_obra WHERE id_empresa=%s AND activo=true ORDER BY nombre', (service._empresa(token),), fetchall=True)}


@router.post('/mano-obra', status_code=201)
def crear_mano_obra(request: Request, data: dict = Body(...), token=Depends(exigir_permiso('Registrar_mano_obra'))):
    from app.repos.estimacion_repos import _query
    result = _query('INSERT INTO obras.t_mano_obra(nombre,descripcion,id_unidad_medida,costo_unitario,id_empresa) VALUES (%s,%s,%s,ROUND(%s::numeric,2),%s) RETURNING id_mano_obra', (data.get('nombre'), data.get('descripcion'), data.get('id_unidad_medida'), data.get('costo_unitario'), service._empresa(token)), fetchone=True, commit=True)
    service._log(token, 'CREAR_MANO_OBRA', f"Cuadrilla creada: {data.get('nombre')}", _ip(request))
    return {'success': True, 'data': result}


@router.get('')
def listar_estimaciones(id_obra: Optional[int] = None, token=Depends(exigir_permiso('Visualizar_estimaciones'))):
    return service.list_estimaciones(token, id_obra)


@router.get('/{id_estimacion}')
def detalle_estimacion(id_estimacion: int, token=Depends(exigir_permiso('Visualizar_estimaciones'))):
    return _call(service.get_estimacion, id_estimacion, token)


@router.post('', status_code=201)
def crear_estimacion(request: Request, data: dict = Body(...), token=Depends(exigir_permiso('Registrar_estimaciones'))):
    return _call(service.create_estimacion, data, token, _ip(request))


@router.put('/{id_estimacion}')
def actualizar_estimacion(id_estimacion: int, request: Request, data: dict = Body(...), token=Depends(exigir_permiso('Modificar_estimaciones'))):
    return _call(service.update_estimacion, id_estimacion, data, token, _ip(request))


@router.post('/{id_estimacion}/analisis_precio_unitario')
def agregar_apu_estimacion(id_estimacion: int, request: Request, data: dict = Body(...), token=Depends(exigir_permiso('Modificar_estimaciones'))):
    return _call(service.add_estimacion_apu, id_estimacion, data, token, _ip(request))


@router.post('/{id_estimacion}/aprobar')
def aprobar_estimacion(id_estimacion: int, request: Request, token=Depends(exigir_permiso('Modificar_estimaciones'))):
    return _call(service.approve_estimacion, id_estimacion, token, _ip(request))


@router.put('/{id_estimacion}/analisis_precio_unitario/{det_id}')
def actualizar_detalle_estimacion(det_id: int, data: dict = Body(...), token=Depends(exigir_permiso('Modificar_estimaciones'))):
    from app.repos import estimacion_repos
    result = estimacion_repos.update_estimacion_apu(det_id, data, service._empresa(token))
    if not result:
        raise HTTPException(status_code=400, detail='El detalle no existe o no pertenece a su empresa.')
    return {'success': True, 'data': result}


@router.delete('/{id_estimacion}/analisis_precio_unitario/{det_id}')
def eliminar_detalle_estimacion(det_id: int, token=Depends(exigir_permiso('Modificar_estimaciones'))):
    from app.repos import estimacion_repos
    return {'success': True, 'data': estimacion_repos.delete_estimacion_apu(det_id, service._empresa(token))}