from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from app.services import compras_services
from app.utils.security import exigir_permiso

router = APIRouter(tags=["Compras"])


def _ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _raise(exc):
    raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("")
def listar_ordenes(
    estado: str = None,
    id_proveedor: int = None,
    fecha_desde: str = None,
    fecha_hasta: str = None,
    q: str = None,
    page: int = 1,
    limit: int = Query(20, le=100),
    id_empresa: int = None,
    token=Depends(exigir_permiso("Visualizar_ordenes_compra")),
):
    try:
        return compras_services.listar_ordenes(
            token=token,
            estado=estado,
            id_proveedor=id_proveedor,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            q=q,
            page=page,
            limit=limit,
            id_empresa=id_empresa
        )
    except compras_services.ComprasError as exc:
        _raise(exc)


@router.post("", status_code=201)
def crear_orden(
    request: Request,
    data: dict = Body(...),
    token=Depends(exigir_permiso("Registrar_ordenes_compra")),
):
    try:
        return compras_services.crear_orden(data, token, _ip(request))
    except compras_services.ComprasError as exc:
        _raise(exc)


@router.get("/{id_orden}")
def detalle_orden(
    id_orden: int,
    id_empresa: int = None,
    token=Depends(exigir_permiso("Visualizar_ordenes_compra")),
):
    try:
        return compras_services.detalle_orden(token, id_orden, id_empresa)
    except compras_services.ComprasError as exc:
        _raise(exc)


@router.patch("/{id_orden}/estado")
def cambiar_estado(
    id_orden: int,
    request: Request,
    data: dict = Body(...),
    token=Depends(exigir_permiso("Registrar_ordenes_compra")),
):
    try:
        return compras_services.cambiar_estado(id_orden, data, token, _ip(request))
    except compras_services.ComprasError as exc:
        _raise(exc)


@router.post("/{id_orden}/aprobar")
def aprobar_orden(
    id_orden: int,
    request: Request,
    data: dict = Body(default={}),
    token=Depends(exigir_permiso("Aprobar_ordenes_compra")),
):
    try:
        data["accion"] = "APROBADA"
        return compras_services.aprobar_rechazar(id_orden, data, token, _ip(request))
    except compras_services.ComprasError as exc:
        _raise(exc)


@router.post("/{id_orden}/rechazar")
def rechazar_orden(
    id_orden: int,
    request: Request,
    data: dict = Body(...),
    token=Depends(exigir_permiso("Aprobar_ordenes_compra")),
):
    try:
        data["accion"] = "RECHAZADA"
        return compras_services.aprobar_rechazar(id_orden, data, token, _ip(request))
    except compras_services.ComprasError as exc:
        _raise(exc)


@router.post("/{id_orden}/recepciones", status_code=201)
def registrar_recepcion(
    id_orden: int,
    request: Request,
    data: dict = Body(...),
    token=Depends(exigir_permiso("Recepcionar_ordenes_compra")),
):
    try:
        return compras_services.registrar_recepcion(id_orden, data, token, _ip(request))
    except compras_services.ComprasError as exc:
        _raise(exc)
