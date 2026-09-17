from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from app.services import inventario_services
from app.utils.security import exigir_permiso

router = APIRouter(tags=["Inventario"])


def _ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _raise(exc):
    raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/stock")
def listar_stock(
    id_categoria: int = None,
    estado_stock: str = None,
    q: str = None,
    page: int = 1,
    limit: int = Query(50, le=100),
    id_empresa: int = None,
    token=Depends(exigir_permiso("Visualizar_inventario")),
):
    try:
        return inventario_services.listar_stock(
            token=token,
            id_categoria=id_categoria,
            estado_stock=estado_stock,
            q=q,
            page=page,
            limit=limit,
            id_empresa=id_empresa
        )
    except inventario_services.InventarioError as exc:
        _raise(exc)


@router.get("/kpis")
def obtener_kpis(
    id_empresa: int = None,
    token=Depends(exigir_permiso("Visualizar_inventario")),
):
    try:
        return inventario_services.obtener_kpis(token=token, id_empresa=id_empresa)
    except inventario_services.InventarioError as exc:
        _raise(exc)


@router.get("/movimientos")
def listar_movimientos(
    id_material: int = None,
    tipo_movimiento: str = None,
    page: int = 1,
    limit: int = Query(50, le=100),
    id_empresa: int = None,
    token=Depends(exigir_permiso("Visualizar_inventario")),
):
    try:
        return inventario_services.listar_movimientos(
            token=token,
            id_material=id_material,
            tipo_movimiento=tipo_movimiento,
            page=page,
            limit=limit,
            id_empresa=id_empresa
        )
    except inventario_services.InventarioError as exc:
        _raise(exc)


@router.post("/ajuste")
def registrar_ajuste(
    request: Request,
    data: dict = Body(...),
    token=Depends(exigir_permiso("Modificar_inventario")),
):
    try:
        return inventario_services.registrar_ajuste(data, token, _ip(request))
    except inventario_services.InventarioError as exc:
        _raise(exc)
