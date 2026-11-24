"""
Router CU42 – Garantías Inmobiliarias y Servicio Posventa (HU161–HU168).
Prefijo: /api/posventa
"""
from fastapi import APIRouter, Body, Depends, HTTPException, Request

from app.services import garantia_posventa_services as service
from app.utils.security import exigir_rol, verificar_token

router = APIRouter(prefix="/api/posventa", tags=["Garantías y Posventa (CU42)"])


def _ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _raise(exc: service.PosventaError):
    raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/catalogos")
def get_catalogos(token: dict = Depends(verificar_token)):
    return {
        "success": True,
        "data": {
            "categorias": list(service.CATEGORIAS_POSVENTA),
            "estados": list(service.ESTADOS_POSVENTA),
        },
    }


@router.post("/garantias", status_code=201)
def post_garantia(
    request: Request,
    data: dict = Body(...),
    token: dict = Depends(verificar_token),
):
    try:
        return service.registrar_garantia(data, token, _ip(request))
    except service.PosventaError as exc:
        _raise(exc)


@router.get("/garantias")
def get_garantias(
    id_unidad: int | None = None,
    token: dict = Depends(verificar_token),
):
    try:
        return service.listar_garantias(token, id_unidad=id_unidad)
    except service.PosventaError as exc:
        _raise(exc)


@router.post("/solicitudes", status_code=201)
def post_solicitud(
    request: Request,
    data: dict = Body(...),
    token: dict = Depends(exigir_rol("CLIENTE")),
):
    try:
        return service.registrar_solicitud_posventa(data, token, _ip(request))
    except service.PosventaError as exc:
        _raise(exc)


@router.get("/solicitudes")
def get_solicitudes(
    id_unidad: int | None = None,
    estado: str | None = None,
    categoria: str | None = None,
    token: dict = Depends(verificar_token),
):
    try:
        return service.listar_solicitudes(
            token, id_unidad=id_unidad, estado=estado, categoria=categoria
        )
    except service.PosventaError as exc:
        _raise(exc)


@router.get("/solicitudes/{id_solicitud}")
def get_detalle_solicitud(
    id_solicitud: int,
    token: dict = Depends(verificar_token),
):
    try:
        return service.obtener_seguimiento_solicitud(id_solicitud, token)
    except service.PosventaError as exc:
        _raise(exc)


@router.patch("/solicitudes/{id_solicitud}/clasificar")
def patch_clasificar(
    id_solicitud: int,
    request: Request,
    data: dict = Body(...),
    token: dict = Depends(verificar_token),
):
    try:
        return service.clasificar_solicitud(id_solicitud, data, token, _ip(request))
    except service.PosventaError as exc:
        _raise(exc)


@router.patch("/solicitudes/{id_solicitud}/asignar")
def patch_asignar(
    id_solicitud: int,
    request: Request,
    data: dict = Body(...),
    token: dict = Depends(verificar_token),
):
    try:
        return service.asignar_responsable(id_solicitud, data, token, _ip(request))
    except service.PosventaError as exc:
        _raise(exc)


@router.patch("/solicitudes/{id_solicitud}/atencion")
def patch_atencion(
    id_solicitud: int,
    request: Request,
    data: dict = Body(...),
    token: dict = Depends(verificar_token),
):
    try:
        return service.gestionar_atencion(id_solicitud, data, token, _ip(request))
    except service.PosventaError as exc:
        _raise(exc)


@router.get("/unidades/{id_unidad}/historial")
def get_historial_unidad(
    id_unidad: int,
    token: dict = Depends(verificar_token),
):
    try:
        return service.consultar_historial_unidad(id_unidad, token)
    except service.PosventaError as exc:
        _raise(exc)
