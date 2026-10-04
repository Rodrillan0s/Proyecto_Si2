from datetime import date
from decimal import Decimal
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.services import control_costos_services as service
from app.utils.security import exigir_permiso


router = APIRouter(prefix="/api/control-costos", tags=["Control de costos y ordenes de cambio"])


CategoriaCosto = Literal["MATERIAL", "MANO_OBRA", "EQUIPO", "SUBCONTRATO", "OTRO"]
TipoCambio = Literal[
    "AUMENTO_CANTIDAD",
    "DISMINUCION_CANTIDAD",
    "CAMBIO_COSTO",
    "NUEVA_PARTIDA",
    "ELIMINACION_PARTIDA",
]


class LineaBaseRequest(BaseModel):
    id_obra: int = Field(gt=0)
    id_estimacion_base: int = Field(gt=0)


class CostoEjecutadoRequest(BaseModel):
    id_control_costo: int = Field(gt=0)
    id_partida_presupuestaria: int = Field(gt=0)
    fecha: date
    concepto: str = Field(min_length=1, max_length=250)
    categoria: CategoriaCosto
    cantidad: Decimal = Field(ge=0, max_digits=14, decimal_places=4)
    costo_unitario: Decimal = Field(ge=0, max_digits=16, decimal_places=2)
    monto: Decimal = Field(ge=0, max_digits=16, decimal_places=2)
    documento: Optional[str] = Field(default=None, max_length=120)
    observacion: Optional[str] = None


class AnularCostoRequest(BaseModel):
    motivo: str = Field(min_length=1)


class OrdenCambioDetalleRequest(BaseModel):
    id_partida_presupuestaria: Optional[int] = Field(default=None, gt=0)
    id_analisis_precio_unitario: Optional[int] = Field(default=None, gt=0)
    tipo_cambio: TipoCambio
    item_codigo_snapshot: Optional[str] = Field(default=None, max_length=40)
    descripcion_snapshot: Optional[str] = Field(default=None, max_length=250)
    unidad_snapshot: Optional[str] = Field(default=None, max_length=30)
    cantidad_delta: Decimal = Field(default=Decimal("0"), max_digits=14, decimal_places=3)
    costo_nuevo: Optional[Decimal] = Field(
        default=None, ge=0, max_digits=16, decimal_places=2
    )
    observacion: Optional[str] = None


class OrdenCambioRequest(BaseModel):
    id_control_costo: int = Field(gt=0)
    codigo: str = Field(min_length=1, max_length=40)
    titulo: str = Field(min_length=1, max_length=200)
    descripcion: Optional[str] = None
    justificacion: str = Field(min_length=1)
    fecha: date
    impacto_plazo_dias: int = 0
    detalles: List[OrdenCambioDetalleRequest] = Field(min_length=1)


class OrdenCambioUpdateRequest(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    descripcion: Optional[str] = None
    justificacion: str = Field(min_length=1)
    fecha: date
    impacto_plazo_dias: int = 0
    detalles: List[OrdenCambioDetalleRequest] = Field(min_length=1)


class AprobarOrdenRequest(BaseModel):
    comentario: Optional[str] = None


class RechazarOrdenRequest(BaseModel):
    motivo: str = Field(min_length=1)


def _ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _raise(exc):
    raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/obras/{id_obra}/presupuestos-aprobados")
def get_presupuestos_aprobados(
    id_obra: int,
    token=Depends(exigir_permiso("Visualizar_control_costos")),
):
    try:
        return service.listar_presupuestos_aprobados(id_obra, token)
    except service.ControlCostosError as exc:
        _raise(exc)


@router.post("/lineas-base", status_code=201)
def post_linea_base(
    data: LineaBaseRequest,
    request: Request,
    token=Depends(exigir_permiso("Registrar_costos_ejecutados")),
):
    try:
        return service.crear_linea_base(data.model_dump(), token, _ip(request))
    except service.ControlCostosError as exc:
        _raise(exc)


@router.get("/obras/{id_obra}/linea-base")
def get_linea_base(
    id_obra: int,
    token=Depends(exigir_permiso("Visualizar_control_costos")),
):
    try:
        return service.obtener_linea_base(id_obra, token)
    except service.ControlCostosError as exc:
        _raise(exc)


@router.get("/costos")
def get_costos(
    id_obra: Optional[int] = Query(default=None, gt=0),
    id_control_costo: Optional[int] = Query(default=None, gt=0),
    id_partida: Optional[int] = Query(default=None, gt=0),
    estado: Optional[str] = None,
    token=Depends(exigir_permiso("Visualizar_control_costos")),
):
    try:
        return service.listar_costos(
            token, id_obra, id_control_costo, id_partida, estado
        )
    except service.ControlCostosError as exc:
        _raise(exc)


@router.post("/costos", status_code=201)
def post_costo(
    data: CostoEjecutadoRequest,
    request: Request,
    token=Depends(exigir_permiso("Registrar_costos_ejecutados")),
):
    try:
        return service.registrar_costo(data.model_dump(), token, _ip(request))
    except service.ControlCostosError as exc:
        _raise(exc)


@router.post("/costos/{id_costo}/anular")
def post_anular_costo(
    id_costo: int,
    data: AnularCostoRequest,
    request: Request,
    token=Depends(exigir_permiso("Anular_costos_ejecutados")),
):
    try:
        return service.anular_costo(id_costo, data.motivo, token, _ip(request))
    except service.ControlCostosError as exc:
        _raise(exc)


@router.get("/obras/{id_obra}/resumen")
def get_resumen(
    id_obra: int,
    token=Depends(exigir_permiso("Visualizar_control_costos")),
):
    try:
        return service.obtener_resumen(id_obra, token)
    except service.ControlCostosError as exc:
        _raise(exc)


@router.get("/obras/{id_obra}/comparacion")
def get_comparacion(
    id_obra: int,
    token=Depends(exigir_permiso("Visualizar_control_costos")),
):
    try:
        return service.obtener_comparacion(id_obra, token)
    except service.ControlCostosError as exc:
        _raise(exc)


@router.get("/ordenes-cambio")
def get_ordenes_cambio(
    id_obra: Optional[int] = Query(default=None, gt=0),
    id_control_costo: Optional[int] = Query(default=None, gt=0),
    estado: Optional[str] = None,
    token=Depends(exigir_permiso("Visualizar_control_costos")),
):
    try:
        return service.listar_ordenes(token, id_obra, id_control_costo, estado)
    except service.ControlCostosError as exc:
        _raise(exc)


@router.get("/ordenes-cambio/{id_orden}")
def get_orden_cambio(
    id_orden: int,
    token=Depends(exigir_permiso("Visualizar_control_costos")),
):
    try:
        return service.obtener_orden(id_orden, token)
    except service.ControlCostosError as exc:
        _raise(exc)


@router.post("/ordenes-cambio", status_code=201)
def post_orden_cambio(
    data: OrdenCambioRequest,
    request: Request,
    token=Depends(exigir_permiso("Registrar_ordenes_cambio")),
):
    try:
        return service.crear_orden(data.model_dump(), token, _ip(request))
    except service.ControlCostosError as exc:
        _raise(exc)


@router.put("/ordenes-cambio/{id_orden}")
def put_orden_cambio(
    id_orden: int,
    data: OrdenCambioUpdateRequest,
    request: Request,
    token=Depends(exigir_permiso("Modificar_ordenes_cambio")),
):
    try:
        return service.actualizar_orden(
            id_orden, data.model_dump(), token, _ip(request)
        )
    except service.ControlCostosError as exc:
        _raise(exc)


@router.post("/ordenes-cambio/{id_orden}/aprobar")
def post_aprobar_orden(
    id_orden: int,
    data: AprobarOrdenRequest,
    request: Request,
    token=Depends(exigir_permiso("Aprobar_ordenes_cambio")),
):
    try:
        return service.aprobar_orden(
            id_orden, data.comentario, token, _ip(request)
        )
    except service.ControlCostosError as exc:
        _raise(exc)


@router.post("/ordenes-cambio/{id_orden}/rechazar")
def post_rechazar_orden(
    id_orden: int,
    data: RechazarOrdenRequest,
    request: Request,
    token=Depends(exigir_permiso("Aprobar_ordenes_cambio")),
):
    try:
        return service.rechazar_orden(
            id_orden, data.motivo, token, _ip(request)
        )
    except service.ControlCostosError as exc:
        _raise(exc)


@router.get("/ordenes-cambio/{id_orden}/historial")
def get_historial_orden(
    id_orden: int,
    token=Depends(exigir_permiso("Visualizar_control_costos")),
):
    try:
        return service.listar_historial(id_orden, token)
    except service.ControlCostosError as exc:
        _raise(exc)
