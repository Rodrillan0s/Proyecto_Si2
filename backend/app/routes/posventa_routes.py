"""
Rutas API para CU33: Gestión de Garantías y Servicio Posventa
(HU161, HU162, HU163, HU164, HU165, HU166, HU167, HU168).
Prefijo /api/posventa protegido por JWT y RBAC multi-tenant.
"""
from datetime import date
import os
from typing import Optional
from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.services import posventa_services
from app.utils.security import verificar_token


router = APIRouter(tags=["Garantías y Posventa"])


def _raise(exc: posventa_services.PosventaError):
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


# ─────────────────────────────────────────────────────────────────────────────
# PYDANTIC SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class RegistrarGarantiaDTO(BaseModel):
    id_unidad: int = Field(..., description="ID de la unidad inmobiliaria comercializada")
    id_cliente: int = Field(..., description="ID del cliente propietario")
    tipo_garantia: str = Field(..., description="Tipo de garantía (ej. ESTRUCTURAL, ACABADOS)")
    descripcion_cobertura: str = Field(..., description="Descripción detallada de la cobertura")
    condiciones: Optional[str] = Field(None, description="Términos y condiciones")
    fecha_inicio: date = Field(..., description="Fecha de inicio de vigencia")
    fecha_fin: date = Field(..., description="Fecha de caducidad de la garantía")


class RegistrarSolicitudDTO(BaseModel):
    id_unidad: int = Field(..., description="ID de la unidad inmobiliaria donde ocurrió el defecto")
    titulo: str = Field(..., description="Título resumen del reclamo")
    descripcion_defecto: str = Field(..., description="Descripción detallada del problema")
    id_cliente: Optional[int] = Field(None, description="Opcional si es registrado por el propio cliente")
    id_garantia: Optional[int] = Field(None, description="Garantía asociada si el cliente la selecciona")


class ClasificarSolicitudDTO(BaseModel):
    categoria: str = Field(..., description="Especialidad (ej. PLOMERIA, ELECTRICIDAD, ACABADOS)")
    prioridad: str = Field(..., description="BAJA, MEDIA, ALTA o URGENTE")
    aplica_garantia: bool = Field(..., description="Si el problema entra dentro de cobertura")
    id_garantia: Optional[int] = Field(None, description="ID de garantía vigente aplicable")
    observaciones: Optional[str] = Field(None, description="Observaciones de clasificación")


class AsignarResponsableDTO(BaseModel):
    id_supervisor: int = Field(..., description="ID del supervisor o técnico designado")
    fecha_estimada_visita: date = Field(..., description="Fecha estimada de atención/visita")
    instrucciones_tecnicas: Optional[str] = Field(None, description="Instrucciones internas de obra")


class AtenderSolicitudDTO(BaseModel):
    nuevo_estado: str = Field(..., description="EN_ATENCION, RESUELTA o CERRADA")
    acciones_realizadas: str = Field(..., description="Detalle de bitácora o solución aplicada")
    materiales_utilizados: Optional[str] = Field(None, description="Materiales e insumos empleados")
    motivo_cierre: Optional[str] = Field(None, description="Observaciones finales de cierre")


# ─────────────────────────────────────────────────────────────────────────────
# 1. GARANTÍAS (HU161, HU162)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/opciones-garantia")
def listar_opciones_garantia(token_data: dict = Depends(verificar_token)):
    """Unidad-cliente elegibles dentro del tenant del usuario autenticado."""
    try:
        return posventa_services.listar_opciones_garantia(token_data)
    except posventa_services.PosventaError as exc:
        _raise(exc)


@router.post("/garantias", status_code=201)
def registrar_garantia(dto: RegistrarGarantiaDTO, token_data: dict = Depends(verificar_token)):
    """HU161: Registrar garantías asociadas a unidades comercializadas (Administrador_empresa)."""
    try:
        return posventa_services.registrar_garantia_inmobiliaria(
            token_data=token_data,
            id_unidad=dto.id_unidad,
            id_cliente=dto.id_cliente,
            tipo_garantia=dto.tipo_garantia,
            descripcion_cobertura=dto.descripcion_cobertura,
            fecha_inicio=dto.fecha_inicio,
            fecha_fin=dto.fecha_fin,
            condiciones=dto.condiciones
        )
    except posventa_services.PosventaError as exc:
        _raise(exc)


@router.get("/garantias")
def listar_garantias(
    id_unidad: Optional[int] = Query(None),
    id_cliente: Optional[int] = Query(None),
    id_obra: Optional[int] = Query(None),
    estado: Optional[str] = Query(None),
    token_data: dict = Depends(verificar_token)
):
    """HU162: Consultar garantías inmobiliarias y su vigencia (Cliente / Admin)."""
    try:
        return posventa_services.consultar_garantias(
            token_data=token_data,
            id_unidad=id_unidad,
            id_cliente=id_cliente,
            id_obra=id_obra,
            estado=estado
        )
    except posventa_services.PosventaError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# 2. SOLICITUDES DE POSVENTA (HU163, HU164, HU165, HU166, HU167, HU168)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/solicitudes", status_code=201)
def registrar_solicitud(dto: RegistrarSolicitudDTO, token_data: dict = Depends(verificar_token)):
    """HU163: Registrar solicitud de posventa posterior a la entrega (Cliente / Admin)."""
    try:
        return posventa_services.registrar_solicitud_posventa(
            token_data=token_data,
            id_unidad=dto.id_unidad,
            titulo=dto.titulo,
            descripcion_defecto=dto.descripcion_defecto,
            id_cliente=dto.id_cliente,
            id_garantia=dto.id_garantia
        )
    except posventa_services.PosventaError as exc:
        _raise(exc)


@router.get("/solicitudes")
def listar_solicitudes(
    id_cliente: Optional[int] = Query(None),
    id_supervisor: Optional[int] = Query(None),
    id_obra: Optional[int] = Query(None),
    id_unidad: Optional[int] = Query(None),
    estado: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    token_data: dict = Depends(verificar_token)
):
    """HU167 y HU168: Consultar listado de solicitudes de posventa."""
    try:
        return posventa_services.consultar_solicitudes_posventa(
            token_data=token_data,
            id_cliente=id_cliente,
            id_supervisor=id_supervisor,
            id_obra=id_obra,
            id_unidad=id_unidad,
            estado=estado,
            prioridad=prioridad,
            categoria=categoria
        )
    except posventa_services.PosventaError as exc:
        _raise(exc)


@router.get("/solicitudes/{id_solicitud}")
def obtener_detalle_solicitud(id_solicitud: int, token_data: dict = Depends(verificar_token)):
    """HU167: Consultar seguimiento de ticket, línea de tiempo y evidencias."""
    try:
        return posventa_services.consultar_detalle_solicitud_posventa(token_data, id_solicitud)
    except posventa_services.PosventaError as exc:
        _raise(exc)


@router.post("/solicitudes/{id_solicitud}/clasificar")
def clasificar_solicitud(
    id_solicitud: int,
    dto: ClasificarSolicitudDTO,
    token_data: dict = Depends(verificar_token)
):
    """HU164: Clasificar solicitud por especialidad, prioridad y validar cobertura de garantía (Admin)."""
    try:
        return posventa_services.clasificar_solicitud_posventa(
            token_data=token_data,
            id_solicitud=id_solicitud,
            categoria=dto.categoria,
            prioridad=dto.prioridad,
            aplica_garantia=dto.aplica_garantia,
            id_garantia=dto.id_garantia,
            observaciones=dto.observaciones
        )
    except posventa_services.PosventaError as exc:
        _raise(exc)


@router.post("/solicitudes/{id_solicitud}/asignar")
def asignar_responsable(
    id_solicitud: int,
    dto: AsignarResponsableDTO,
    token_data: dict = Depends(verificar_token)
):
    """HU165: Asignar supervisor y programar fecha estimada de atención (Jefe de Obra)."""
    try:
        return posventa_services.asignar_responsable_atencion(
            token_data=token_data,
            id_solicitud=id_solicitud,
            id_supervisor=dto.id_supervisor,
            fecha_estimada_visita=dto.fecha_estimada_visita,
            instrucciones_tecnicas=dto.instrucciones_tecnicas
        )
    except posventa_services.PosventaError as exc:
        _raise(exc)


@router.post("/solicitudes/{id_solicitud}/atender")
def registrar_atencion(
    id_solicitud: int,
    dto: AtenderSolicitudDTO,
    token_data: dict = Depends(verificar_token)
):
    """HU166: Gestionar atención, bitácora de visita, materiales y cambio de estado (Supervisor)."""
    try:
        return posventa_services.gestionar_atencion_solicitud(
            token_data=token_data,
            id_solicitud=id_solicitud,
            nuevo_estado=dto.nuevo_estado,
            acciones_realizadas=dto.acciones_realizadas,
            materiales_utilizados=dto.materiales_utilizados,
            motivo_cierre=dto.motivo_cierre
        )
    except posventa_services.PosventaError as exc:
        _raise(exc)


@router.post("/solicitudes/{id_solicitud}/evidencias", status_code=201)
async def subir_evidencia(
    id_solicitud: int,
    tipo_evidencia: str = Form("CLIENTE_REPORTE"),
    archivo: UploadFile = File(...),
    token_data: dict = Depends(verificar_token)
):
    """HU163 / HU166: Adjuntar fotografía o evidencia de posventa."""
    try:
        contenido = await archivo.read()
        return posventa_services.adjuntar_evidencia_solicitud(
            token_data=token_data,
            id_solicitud=id_solicitud,
            tipo_evidencia=tipo_evidencia,
            nombre_archivo=archivo.filename,
            contenido_bytes=contenido,
            tipo_mime=archivo.content_type
        )
    except posventa_services.PosventaError as exc:
        _raise(exc)


@router.get("/supervisores")
def listar_supervisores(id_obra: Optional[int] = Query(None), token_data: dict = Depends(verificar_token)):
    """Lista supervisores disponibles para asignación técnica en posventa."""
    try:
        return posventa_services.obtener_supervisores_empresa(token_data, id_obra)
    except posventa_services.PosventaError as exc:
        _raise(exc)


@router.get("/metricas")
def consultar_metricas(token_data: dict = Depends(verificar_token)):
    """HU168: Métricas consolidadas e historial para auditoría de posventa."""
    try:
        return posventa_services.consultar_historial_y_metricas(token_data)
    except posventa_services.PosventaError as exc:
        _raise(exc)
