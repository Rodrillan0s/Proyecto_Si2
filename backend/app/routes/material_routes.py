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


@router.post("/categorias", status_code=201)
def post_categoria(request: Request, data: dict = Body(...), token=Depends(exigir_permiso("Registrar_materiales"))):
    try: return material_services.crear_categoria(data, token, _ip(request))
    except material_services.MaterialError as exc: _raise(exc)


@router.get("/base")
def get_catalogo_base(
    q: str = None,
    id_categoria: int = None,
    id_empresa: int = None,
    page: int = 1,
    limit: int = Query(100, le=200),
    token=Depends(exigir_permiso("Visualizar_materiales"))
):
    try:
        return material_services.catalogo_base(token, q, id_categoria, id_empresa, page, limit)
    except material_services.MaterialError as exc:
        _raise(exc)


@router.get("/base/{id_material_base}")
def get_detalle_base(
    id_material_base: int,
    token=Depends(exigir_permiso("Visualizar_materiales"))
):
    try:
        return material_services.detalle_base(id_material_base, token)
    except material_services.MaterialError as exc:
        _raise(exc)


@router.post("/adoptar", status_code=201)
def post_adoptar_material(
    request: Request,
    data: dict = Body(...),
    token=Depends(exigir_permiso("Registrar_materiales"))
):
    try:
        return material_services.adoptar(data, token, _ip(request))
    except material_services.MaterialError as exc:
        _raise(exc)


@router.get("")
def get_materiales(q: str = None, id_categoria: int = None, estado: str = None,
                   stock_bajo: bool = None, page: int = 1, limit: int = Query(20, le=100),
                   id_empresa: int = None,
                   token=Depends(exigir_permiso("Visualizar_materiales"))):
    try: return material_services.listar(token,q,id_categoria,estado,stock_bajo,page,limit,id_empresa)
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
