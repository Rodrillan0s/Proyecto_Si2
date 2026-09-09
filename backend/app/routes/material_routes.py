from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request

from app.services import material_services
from app.utils.security import exigir_permiso


router = APIRouter(tags=["Materiales"])


def _ip(request): return request.client.host if request.client else "unknown"
def _raise(exc): raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/categorias")
def get_categorias(token=Depends(exigir_permiso("Visualizar_materiales"))):
    try: return material_services.categorias(token)
    except material_services.MaterialError as exc: _raise(exc)


@router.get("/unidades-medida")
def get_unidades_medida(token=Depends(exigir_permiso("Visualizar_materiales"))):
    try: return material_services.unidades_medida(token)
    except material_services.MaterialError as exc: _raise(exc)


@router.get("")
def get_materiales(q: str = None, id_categoria: int = None, estado: str = None,
                   stock_bajo: bool = None, page: int = 1, limit: int = Query(20, le=100),
                   token=Depends(exigir_permiso("Visualizar_materiales"))):
    try: return material_services.listar(token,q,id_categoria,estado,stock_bajo,page,limit)
    except material_services.MaterialError as exc: _raise(exc)


@router.get("/{id_material}")
def get_material(id_material: int, token=Depends(exigir_permiso("Visualizar_materiales"))):
    try: return material_services.detalle(id_material,token)
    except material_services.MaterialError as exc: _raise(exc)


@router.post("", status_code=201)
def post_material(request: Request, data: dict = Body(...), token=Depends(exigir_permiso("Registrar_materiales"))):
    try: return material_services.registrar(data,token,_ip(request))
    except material_services.MaterialError as exc: _raise(exc)


@router.put("/{id_material}")
def put_material(id_material: int, request: Request, data: dict = Body(...),
                 token=Depends(exigir_permiso("Modificar_materiales"))):
    try: return material_services.modificar(id_material,data,token,_ip(request))
    except material_services.MaterialError as exc: _raise(exc)


@router.patch("/{id_material}/estado")
def patch_estado(id_material: int, request: Request, data: dict = Body(...),
                 token=Depends(exigir_permiso("Desactivar_materiales"))):
    try: return material_services.cambiar_estado(id_material,data.get("estado"),token,_ip(request))
    except material_services.MaterialError as exc: _raise(exc)
