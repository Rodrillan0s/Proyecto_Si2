from fastapi import APIRouter, Body, Depends, HTTPException, Request
from app.services import unidad_services
from app.utils.security import exigir_permiso


router = APIRouter(prefix="/api/proyectos/{id_obra}/unidades", tags=["Unidades de Construcción"])


def _ip(request: Request):
    return request.client.host if request.client else "unknown"


@router.get("/")
def get_unidades(id_obra: int, token_data: dict = Depends(exigir_permiso("Visualizar_obras"))):
    try:
        return unidad_services.listar_unidades(id_obra, token_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/")
def post_unidad(id_obra: int, request: Request, data: dict = Body(...),
                token_data: dict = Depends(exigir_permiso("Modificar_obras"))):
    try:
        return unidad_services.registrar_unidad(id_obra, data, token_data, _ip(request))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/modelos")
def get_modelos(id_obra: int, token_data: dict = Depends(exigir_permiso("Visualizar_obras"))):
    try:
        return unidad_services.listar_modelos(id_obra, token_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/modelos")
def post_modelo(id_obra: int, request: Request, data: dict = Body(...),
                token_data: dict = Depends(exigir_permiso("Modificar_obras"))):
    try:
        return unidad_services.guardar_modelo(id_obra, data, token_data, client_ip=_ip(request))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/modelos/{id_modelo}")
def put_modelo(id_obra: int, id_modelo: int, request: Request, data: dict = Body(...),
               token_data: dict = Depends(exigir_permiso("Modificar_obras"))):
    try:
        return unidad_services.guardar_modelo(id_obra, data, token_data, id_modelo, _ip(request))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/materiales-disponibles")
def get_materiales(id_obra: int, token_data: dict = Depends(exigir_permiso("Visualizar_obras"))):
    try:
        return unidad_services.listar_materiales(id_obra, token_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{id_unidad}")
def get_unidad(id_obra: int, id_unidad: int,
               token_data: dict = Depends(exigir_permiso("Visualizar_obras"))):
    try:
        return unidad_services.obtener_unidad(id_obra, id_unidad, token_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{id_unidad}")
def put_unidad(id_obra: int, id_unidad: int, request: Request, data: dict = Body(...),
               token_data: dict = Depends(exigir_permiso("Modificar_obras"))):
    try:
        return unidad_services.actualizar_unidad(id_obra, id_unidad, data, token_data, _ip(request))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{id_unidad}")
def delete_unidad(id_obra: int, id_unidad: int, request: Request,
                  token_data: dict = Depends(exigir_permiso("Modificar_obras"))):
    try:
        return unidad_services.eliminar_unidad(
            id_obra, id_unidad, token_data, _ip(request)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{id_unidad}/estado")
def patch_estado(id_obra: int, id_unidad: int, request: Request, data: dict = Body(...),
                 token_data: dict = Depends(exigir_permiso("Modificar_obras"))):
    try:
        return unidad_services.cambiar_estado(id_obra, id_unidad, data, token_data, _ip(request))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id_unidad}/personalizaciones")
def post_personalizacion(id_obra: int, id_unidad: int, request: Request, data: dict = Body(...),
                         token_data: dict = Depends(exigir_permiso("Modificar_obras"))):
    try:
        return unidad_services.agregar_personalizacion(id_obra, id_unidad, data, token_data, _ip(request))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{id_unidad}/personalizaciones/{id_personalizacion}")
def delete_personalizacion(id_obra: int, id_unidad: int, id_personalizacion: int,
                           request: Request,
                           token_data: dict = Depends(exigir_permiso("Modificar_obras"))):
    try:
        return unidad_services.eliminar_personalizacion(
            id_obra, id_unidad, id_personalizacion, token_data, _ip(request)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{id_unidad}/materiales")
def put_materiales(id_obra: int, id_unidad: int, request: Request, data: dict = Body(...),
                   token_data: dict = Depends(exigir_permiso("Modificar_obras"))):
    try:
        return unidad_services.reemplazar_materiales(id_obra, id_unidad, data, token_data, _ip(request))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
