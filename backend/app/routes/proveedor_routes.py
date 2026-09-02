from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request

from app.services import proveedor_services
from app.utils.security import exigir_permiso


router = APIRouter(tags=["Proveedores"])


def _ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _raise(exc):
    raise HTTPException(status_code=exc.status_code, detail=str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/proveedores
# ─────────────────────────────────────────────────────────────────────────────
@router.get("")
def get_proveedores(
    q: str = None,
    estado: str = None,
    page: int = 1,
    limit: int = Query(20, le=100),
    token=Depends(exigir_permiso("Visualizar_proveedores")),
):
    try:
        return proveedor_services.listar(token, q, estado, page, limit)
    except proveedor_services.ProveedorError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/proveedores
# ─────────────────────────────────────────────────────────────────────────────
@router.post("", status_code=201)
def post_proveedor(
    request: Request,
    data: dict = Body(...),
    token=Depends(exigir_permiso("Registrar_proveedores")),
):
    try:
        return proveedor_services.registrar(data, token, _ip(request))
    except proveedor_services.ProveedorError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/proveedores/{id_proveedor}
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{id_proveedor}")
def get_proveedor(
    id_proveedor: int,
    token=Depends(exigir_permiso("Visualizar_proveedores")),
):
    try:
        return proveedor_services.detalle(id_proveedor, token)
    except proveedor_services.ProveedorError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/proveedores/{id_proveedor}
# ─────────────────────────────────────────────────────────────────────────────
@router.put("/{id_proveedor}")
def put_proveedor(
    id_proveedor: int,
    request: Request,
    data: dict = Body(...),
    token=Depends(exigir_permiso("Modificar_proveedores")),
):
    try:
        return proveedor_services.modificar(id_proveedor, data, token, _ip(request))
    except proveedor_services.ProveedorError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /api/proveedores/{id_proveedor}/estado
# ─────────────────────────────────────────────────────────────────────────────
@router.patch("/{id_proveedor}/estado")
def patch_estado(
    id_proveedor: int,
    request: Request,
    data: dict = Body(...),
    token=Depends(exigir_permiso("Modificar_proveedores")),
):
    try:
        return proveedor_services.cambiar_estado(
            id_proveedor, data.get("estado"), token, _ip(request)
        )
    except proveedor_services.ProveedorError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/proveedores/{id_proveedor}/materiales
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{id_proveedor}/materiales")
def get_materiales_proveedor(
    id_proveedor: int,
    token=Depends(exigir_permiso("Visualizar_proveedores")),
):
    try:
        return proveedor_services.listar_materiales(id_proveedor, token)
    except proveedor_services.ProveedorError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/proveedores/{id_proveedor}/materiales
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/{id_proveedor}/materiales", status_code=201)
def post_materiales_proveedor(
    id_proveedor: int,
    request: Request,
    data: dict = Body(...),
    token=Depends(exigir_permiso("Registrar_proveedores")),
):
    """
    Cuerpo esperado: { "ids_material": [1, 2, 3] }
    """
    ids_material = data.get("ids_material", [])
    try:
        return proveedor_services.asociar_materiales(
            id_proveedor, ids_material, token, _ip(request)
        )
    except proveedor_services.ProveedorError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# DELETE /api/proveedores/{id_proveedor}/materiales/{id_material}
# ─────────────────────────────────────────────────────────────────────────────
@router.delete("/{id_proveedor}/materiales/{id_material}")
def delete_material_proveedor(
    id_proveedor: int,
    id_material: int,
    request: Request,
    token=Depends(exigir_permiso("Modificar_proveedores")),
):
    try:
        return proveedor_services.desasociar_material(
            id_proveedor, id_material, token, _ip(request)
        )
    except proveedor_services.ProveedorError as exc:
        _raise(exc)
