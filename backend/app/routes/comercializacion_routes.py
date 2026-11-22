"""
Rutas API para CU31: Gestionar comercialización de unidades inmobiliarias
(HU143, HU144, HU145, HU146).
Prefijo /api/comercializacion registrado en planes_catalog dentro del módulo 'crm'.
"""
from typing import Optional
from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse

from app.services import comercializacion_services
from app.utils.security import obtener_permisos_rol, verificar_token


router = APIRouter(tags=["Comercialización"])

PERMISOS_LECTURA_COMERCIAL = {
    "Visualizar_clientes",
    "Gestionar_comercializacion",
    "Visualizar_obras",
}
PERMISOS_ESCRITURA_COMERCIAL = {
    "Modificar_clientes",
    "Registrar_clientes",
    "Gestionar_comercializacion",
    "Modificar_obras",
}


def exigir_acceso_comercial(permisos_aceptados: set):
    """
    Valida que el usuario autenticado posea alguno de los permisos comerciales requeridos.
    Compatible con ADMINISTRADOR, ADMINISTRADOR_EMPRESA y JEFE DE OBRA.
    """
    def _dep(token_data: dict = Depends(verificar_token)):
        rol = token_data.get("nombre_rol")
        if rol == "ADMINISTRADOR":
            return token_data
        permisos_usuario = obtener_permisos_rol(rol)
        if not (permisos_usuario & permisos_aceptados):
            raise HTTPException(
                status_code=403,
                detail="No tiene permisos para realizar esta acción en el módulo de comercialización."
            )
        return token_data
    return _dep


def _ip(request: Request) -> str:
    return request.client.host if request and request.client else "unknown"


def _raise(exc: comercializacion_services.ComercializacionError):
    raise HTTPException(status_code=exc.status_code, detail=str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# HU143 y HU145: LISTADO, RESUMEN/KPIs, DETALLE Y DISPONIBILIDAD
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/unidades")
def get_unidades_comerciales(
    id_obra: Optional[int] = None,
    estado_comercial: Optional[str] = None,
    publicado: Optional[bool] = None,
    tipo_unidad: Optional[str] = None,
    solo_disponibles: bool = False,
    q: Optional[str] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    page: int = 1,
    limit: int = Query(20, le=100),
    id_empresa: Optional[int] = None,
    token=Depends(exigir_acceso_comercial(PERMISOS_LECTURA_COMERCIAL)),
):
    """
    Lista unidades inmobiliarias con datos comerciales, precios, publicación
    y disponibilidad efectiva (excluyendo unidades reservadas/vendidas en CRM).
    """
    try:
        return comercializacion_services.listar_unidades(
            token=token,
            id_obra=id_obra,
            estado_comercial=estado_comercial,
            publicado=publicado,
            tipo_unidad=tipo_unidad,
            solo_disponibles=solo_disponibles,
            q=q,
            precio_min=precio_min,
            precio_max=precio_max,
            page=page,
            limit=limit,
            id_empresa_solicitada=id_empresa,
        )
    except comercializacion_services.ComercializacionError as exc:
        _raise(exc)


@router.get("/resumen")
def get_resumen_comercial(
    id_obra: Optional[int] = None,
    id_empresa: Optional[int] = None,
    token=Depends(exigir_acceso_comercial(PERMISOS_LECTURA_COMERCIAL)),
):
    """Retorna métricas y KPIs agregados del inventario comercial (HU145)."""
    try:
        return comercializacion_services.obtener_resumen(
            token=token,
            id_obra=id_obra,
            id_empresa_solicitada=id_empresa,
        )
    except comercializacion_services.ComercializacionError as exc:
        _raise(exc)


@router.get("/unidades/{id_unidad}")
def get_unidad_comercial(
    id_unidad: int,
    id_empresa: Optional[int] = None,
    token=Depends(exigir_acceso_comercial(PERMISOS_LECTURA_COMERCIAL)),
):
    """Obtiene ficha comercial detallada con fotos, estado CRM e historial."""
    try:
        return comercializacion_services.obtener_detalle_unidad(
            token=token,
            id_unidad=id_unidad,
            id_empresa_solicitada=id_empresa,
        )
    except comercializacion_services.ComercializacionError as exc:
        _raise(exc)


@router.get("/unidades/{id_unidad}/disponibilidad")
def get_disponibilidad_unidad(
    id_unidad: int,
    id_empresa: Optional[int] = None,
    token=Depends(exigir_acceso_comercial(PERMISOS_LECTURA_COMERCIAL)),
):
    """Consulta disponibilidad comercial efectiva, bloqueo CRM y transiciones permitidas (HU145)."""
    try:
        return comercializacion_services.consultar_disponibilidad_unidad(
            token=token,
            id_unidad=id_unidad,
            id_empresa_solicitada=id_empresa,
        )
    except comercializacion_services.ComercializacionError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# HU143: PUBLICAR, ACTUALIZAR DATOS COMERCIALES Y GESTIONAR FOTOGRAFÍAS
# ─────────────────────────────────────────────────────────────────────────────
@router.patch("/unidades/{id_unidad}")
def patch_unidad_comercial(
    id_unidad: int,
    request: Request,
    datos: dict = Body(...),
    id_empresa: Optional[int] = None,
    token=Depends(exigir_acceso_comercial(PERMISOS_ESCRITURA_COMERCIAL)),
):
    """
    Actualiza atributos comerciales (precio_venta, publicado_comercial,
    moneda_comercial, descripcion_comercial, estado_comercial).
    NO modifica el estado constructivo existente.
    """
    try:
        return comercializacion_services.actualizar_comercializacion(
            token=token,
            id_unidad=id_unidad,
            datos=datos,
            id_empresa_solicitada=id_empresa,
            ip=_ip(request),
        )
    except comercializacion_services.ComercializacionError as exc:
        _raise(exc)


@router.patch("/unidades/{id_unidad}/publicacion")
def patch_publicacion_unidad(
    id_unidad: int,
    request: Request,
    datos: dict = Body(...),
    id_empresa: Optional[int] = None,
    token=Depends(exigir_acceso_comercial(PERMISOS_ESCRITURA_COMERCIAL)),
):
    """Publica o despublica comercialmente una unidad inmobiliaria (HU143)."""
    try:
        publicado = datos.get("publicado_comercial")
        if publicado is None:
            publicado = datos.get("publicado")
        return comercializacion_services.cambiar_publicacion_unidad(
            token=token,
            id_unidad=id_unidad,
            publicado=publicado,
            id_empresa_solicitada=id_empresa,
            ip=_ip(request),
        )
    except comercializacion_services.ComercializacionError as exc:
        _raise(exc)


@router.get("/unidades/{id_unidad}/fotografias")
def get_fotografias_unidad(
    id_unidad: int,
    id_empresa: Optional[int] = None,
    token=Depends(exigir_acceso_comercial(PERMISOS_LECTURA_COMERCIAL)),
):
    """Lista la galería fotográfica de la unidad (HU143)."""
    try:
        return comercializacion_services.listar_fotografias(
            token=token,
            id_unidad=id_unidad,
            id_empresa_solicitada=id_empresa,
        )
    except comercializacion_services.ComercializacionError as exc:
        _raise(exc)


@router.post("/unidades/{id_unidad}/fotografias", status_code=201)
async def post_fotografia_unidad(
    id_unidad: int,
    request: Request,
    archivo: UploadFile = File(...),
    es_principal: bool = Form(default=False),
    orden: int = Form(default=1),
    id_empresa: Optional[int] = None,
    token=Depends(exigir_acceso_comercial(PERMISOS_ESCRITURA_COMERCIAL)),
):
    """Sube una fotografía comercial validando MIME, tamaño y tenant (HU143)."""
    try:
        return await comercializacion_services.subir_fotografia(
            token=token,
            id_unidad=id_unidad,
            archivo=archivo,
            es_principal=es_principal,
            orden=orden,
            id_empresa_solicitada=id_empresa,
            ip=_ip(request),
        )
    except comercializacion_services.ComercializacionError as exc:
        _raise(exc)


@router.patch("/unidades/{id_unidad}/fotografias/{id_fotografia}/principal")
def patch_fotografia_principal(
    id_unidad: int,
    id_fotografia: int,
    request: Request,
    id_empresa: Optional[int] = None,
    token=Depends(exigir_acceso_comercial(PERMISOS_ESCRITURA_COMERCIAL)),
):
    """Marca una fotografía como principal dentro de la galería de la unidad (HU143)."""
    try:
        return comercializacion_services.marcar_fotografia_principal(
            token=token,
            id_unidad=id_unidad,
            id_fotografia=id_fotografia,
            id_empresa_solicitada=id_empresa,
            ip=_ip(request),
        )
    except comercializacion_services.ComercializacionError as exc:
        _raise(exc)


@router.delete("/unidades/{id_unidad}/fotografias/{id_fotografia}")
def delete_fotografia_unidad(
    id_unidad: int,
    id_fotografia: int,
    request: Request,
    id_empresa: Optional[int] = None,
    token=Depends(exigir_acceso_comercial(PERMISOS_ESCRITURA_COMERCIAL)),
):
    """Elimina una fotografía de la unidad y promueve otra si era principal (HU143)."""
    try:
        return comercializacion_services.eliminar_fotografia(
            token=token,
            id_unidad=id_unidad,
            id_fotografia=id_fotografia,
            id_empresa_solicitada=id_empresa,
            ip=_ip(request),
        )
    except comercializacion_services.ComercializacionError as exc:
        _raise(exc)


@router.get("/unidades/{id_unidad}/fotografias/{id_fotografia}/archivo")
def get_archivo_fotografia_unidad(
    id_unidad: int,
    id_fotografia: int,
    id_empresa: Optional[int] = None,
    token=Depends(exigir_acceso_comercial(PERMISOS_LECTURA_COMERCIAL)),
):
    """Sirve el archivo físico de la fotografía validando pertenencia a empresa y prevención de path traversal."""
    try:
        info = comercializacion_services.obtener_archivo_fotografia(
            token=token,
            id_unidad=id_unidad,
            id_fotografia=id_fotografia,
            id_empresa_solicitada=id_empresa,
        )
        return FileResponse(
            path=info["ruta"],
            media_type=info["tipo_mime"],
            filename=info["nombre_archivo"],
        )
    except comercializacion_services.ComercializacionError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# HU144: REGISTRAR RESERVAS DE UNIDADES INMOBILIARIAS
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/unidades/{id_unidad}/reservas", status_code=201)
def post_reserva_unidad(
    id_unidad: int,
    request: Request,
    datos: dict = Body(...),
    id_empresa: Optional[int] = None,
    token=Depends(exigir_acceso_comercial(PERMISOS_ESCRITURA_COMERCIAL)),
):
    """
    Registra una reserva comercial para un cliente existente de la misma empresa
    actualizando estado comercial, asociación CRM e historial en una sola transacción (HU144).
    """
    try:
        return comercializacion_services.registrar_reserva(
            token=token,
            id_unidad=id_unidad,
            datos=datos,
            id_empresa_solicitada=id_empresa,
            ip=_ip(request),
        )
    except comercializacion_services.ComercializacionError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# HU145: CONTROL DE ESTADO COMERCIAL, CANCELACIÓN DE RESERVA Y CONFIRMACIÓN DE VENTA
# ─────────────────────────────────────────────────────────────────────────────
@router.patch("/unidades/{id_unidad}/estado")
def patch_estado_comercial_unidad(
    id_unidad: int,
    request: Request,
    datos: dict = Body(...),
    id_empresa: Optional[int] = None,
    token=Depends(exigir_acceso_comercial(PERMISOS_ESCRITURA_COMERCIAL)),
):
    """Actualiza el estado comercial validando transiciones coherentes y sincronización CRM (HU145)."""
    try:
        return comercializacion_services.cambiar_estado_comercial(
            token=token,
            id_unidad=id_unidad,
            datos=datos,
            id_empresa_solicitada=id_empresa,
            ip=_ip(request),
        )
    except comercializacion_services.ComercializacionError as exc:
        _raise(exc)


@router.post("/unidades/{id_unidad}/cancelar-reserva")
def post_cancelar_reserva_unidad(
    id_unidad: int,
    request: Request,
    datos: Optional[dict] = Body(default=None),
    id_empresa: Optional[int] = None,
    token=Depends(exigir_acceso_comercial(PERMISOS_ESCRITURA_COMERCIAL)),
):
    """Cancela/libera una reserva activa pasando la unidad a DISPONIBLE y sincronizando CRM (HU145)."""
    try:
        return comercializacion_services.cancelar_reserva(
            token=token,
            id_unidad=id_unidad,
            datos=datos,
            id_empresa_solicitada=id_empresa,
            ip=_ip(request),
        )
    except comercializacion_services.ComercializacionError as exc:
        _raise(exc)


@router.post("/unidades/{id_unidad}/confirmar-venta")
def post_confirmar_venta_unidad(
    id_unidad: int,
    request: Request,
    datos: Optional[dict] = Body(default=None),
    id_empresa: Optional[int] = None,
    token=Depends(exigir_acceso_comercial(PERMISOS_ESCRITURA_COMERCIAL)),
):
    """Confirma la venta de la unidad pasándola a VENDIDA y sincronizando CRM e historial (HU145)."""
    try:
        return comercializacion_services.confirmar_venta(
            token=token,
            id_unidad=id_unidad,
            datos=datos,
            id_empresa_solicitada=id_empresa,
            ip=_ip(request),
        )
    except comercializacion_services.ComercializacionError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# HU146: HISTORIAL COMERCIAL DE LA UNIDAD
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/unidades/{id_unidad}/historial")
def get_historial_comercial(
    id_unidad: int,
    tipo_evento: Optional[str] = None,
    limit: int = Query(100, le=500),
    id_empresa: Optional[int] = None,
    token=Depends(exigir_acceso_comercial(PERMISOS_LECTURA_COMERCIAL)),
):
    """Consulta la trazabilidad histórica cronológica de eventos comerciales de la unidad (HU146)."""
    try:
        return comercializacion_services.listar_historial(
            token=token,
            id_unidad=id_unidad,
            tipo_evento=tipo_evento,
            limit=limit,
            id_empresa_solicitada=id_empresa,
        )
    except comercializacion_services.ComercializacionError as exc:
        _raise(exc)
