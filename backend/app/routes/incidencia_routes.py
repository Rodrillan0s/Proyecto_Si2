from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse

from app.services import incidencia_services
from app.utils.security import exigir_permiso, verificar_token


router = APIRouter(tags=["Incidencias"])


def acceso_registro(token=Depends(verificar_token)):
    try:
        return incidencia_services.autorizar_registro(token)
    except incidencia_services.IncidenciaError as exc:
        _raise(exc)


@router.get("/obras-registro")
def get_obras_registro(token=Depends(acceso_registro)):
    try:
        return incidencia_services.obras_registro(token)
    except incidencia_services.IncidenciaError as exc:
        _raise(exc)


def acceso_incidencia(permiso, permitir_registrador=False):
    def validar(id_incidencia: int, token=Depends(verificar_token)):
        try:
            return incidencia_services.autorizar_atencion(
                id_incidencia, token, permiso, permitir_registrador=permitir_registrador
            )
        except incidencia_services.IncidenciaError as exc:
            _raise(exc)
    return validar


def acceso_estado(id_incidencia: int, data: dict = Body(...), token=Depends(verificar_token)):
    estado = str(data.get("estado") or "").strip().upper()
    try:
        if estado == "EN_PROCESO":
            return incidencia_services.autorizar_atencion(id_incidencia, token, "Modificar_incidencias")
        if estado in incidencia_services.ACCIONES_RESPONSABLE:
            return incidencia_services.autorizar_atencion(id_incidencia, token, solo_responsable=True)
        permiso = "Cerrar_incidencias" if estado == "CERRADA" else "Modificar_incidencias"
        # Otras transiciones no reciben la excepción del responsable.
        exigir_permiso(permiso)(token)
        return token
    except incidencia_services.IncidenciaError as exc:
        _raise(exc)


def _ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _raise(exc):
    raise HTTPException(status_code=exc.status_code, detail=str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/incidencias/
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/")
def get_incidencias(
    id_obra: int = None,
    id_unidad: int = None,
    prioridad: str = None,
    estado: str = None,
    busqueda: str = None,
    id_responsable: int = None,
    page: int = 1,
    limit: int = Query(20, le=100),
    token=Depends(verificar_token),
):
    try:
        return incidencia_services.listar(
            token, id_obra, id_unidad, prioridad, estado, busqueda, id_responsable, page, limit
        )
    except incidencia_services.IncidenciaError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/incidencias/
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/", status_code=201)
def post_incidencia(
    request: Request,
    data: dict = Body(...),
    token=Depends(acceso_registro),
):
    try:
        return incidencia_services.registrar(data, token, _ip(request))
    except incidencia_services.IncidenciaError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/incidencias/{id_incidencia}
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{id_incidencia}")
def get_incidencia(
    id_incidencia: int,
    token=Depends(acceso_incidencia("Visualizar_incidencias")),
):
    try:
        return incidencia_services.obtener(id_incidencia, token)
    except incidencia_services.IncidenciaError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/incidencias/{id_incidencia}
# ─────────────────────────────────────────────────────────────────────────────
@router.put("/{id_incidencia}")
def put_incidencia(
    id_incidencia: int,
    request: Request,
    data: dict = Body(...),
    token=Depends(exigir_permiso("Modificar_incidencias")),
):
    try:
        return incidencia_services.actualizar(id_incidencia, data, token, _ip(request))
    except incidencia_services.IncidenciaError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/incidencias/{id_incidencia}/responsables
# HU71: candidatos válidos para el selector del modal "Asignar responsable".
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{id_incidencia}/responsables")
def get_responsables(
    id_incidencia: int,
    token=Depends(exigir_permiso("Asignar_incidencias")),
):
    try:
        return incidencia_services.obtener_responsables(id_incidencia, token)
    except incidencia_services.IncidenciaError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /api/incidencias/{id_incidencia}/responsable
# ─────────────────────────────────────────────────────────────────────────────
@router.patch("/{id_incidencia}/responsable")
def patch_responsable(
    id_incidencia: int,
    request: Request,
    data: dict = Body(...),
    token=Depends(exigir_permiso("Asignar_incidencias")),
):
    try:
        return incidencia_services.asignar_responsable(id_incidencia, data, token, _ip(request))
    except incidencia_services.IncidenciaError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /api/incidencias/{id_incidencia}/estado
# ─────────────────────────────────────────────────────────────────────────────
@router.patch("/{id_incidencia}/estado")
def patch_estado(
    id_incidencia: int,
    request: Request,
    data: dict = Body(...),
    token=Depends(acceso_estado),
):
    try:
        return incidencia_services.cambiar_estado(id_incidencia, data, token, _ip(request))
    except incidencia_services.IncidenciaError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# Órdenes de trabajo afectadas (relación M:N incidencia <-> OT)
# Seleccionarlas reutiliza el permiso Asignar_incidencias (mismo actor que
# asigna el responsable); no se crean permisos nuevos.
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{id_incidencia}/ordenes-trabajo")
def get_ordenes_trabajo(
    id_incidencia: int,
    token=Depends(acceso_incidencia("Visualizar_incidencias")),
):
    try:
        return incidencia_services.listar_ordenes_trabajo(id_incidencia, token)
    except incidencia_services.IncidenciaError as exc:
        _raise(exc)


@router.get("/{id_incidencia}/ordenes-trabajo/disponibles")
def get_ordenes_trabajo_disponibles(
    id_incidencia: int,
    token=Depends(exigir_permiso("Asignar_incidencias")),
):
    try:
        return incidencia_services.listar_ordenes_trabajo_disponibles(id_incidencia, token)
    except incidencia_services.IncidenciaError as exc:
        _raise(exc)


@router.put("/{id_incidencia}/ordenes-trabajo")
def put_ordenes_trabajo(
    id_incidencia: int,
    request: Request,
    data: dict = Body(...),
    token=Depends(exigir_permiso("Asignar_incidencias")),
):
    try:
        return incidencia_services.actualizar_ordenes_trabajo(id_incidencia, data, token, _ip(request))
    except incidencia_services.IncidenciaError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/incidencias/{id_incidencia}/seguimiento
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{id_incidencia}/seguimiento")
def get_seguimiento(
    id_incidencia: int,
    token=Depends(acceso_incidencia("Visualizar_incidencias")),
):
    try:
        return incidencia_services.listar_seguimiento(id_incidencia, token)
    except incidencia_services.IncidenciaError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/incidencias/{id_incidencia}/seguimiento
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/{id_incidencia}/seguimiento", status_code=201)
def post_seguimiento(
    id_incidencia: int,
    request: Request,
    data: dict = Body(...),
    token=Depends(acceso_incidencia("Modificar_incidencias")),
):
    try:
        return incidencia_services.registrar_seguimiento(id_incidencia, data, token, _ip(request))
    except incidencia_services.IncidenciaError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# HU73 – Evidencias fotográficas (almacenamiento local, ver incidencia_services)
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{id_incidencia}/evidencias")
def get_evidencias(
    id_incidencia: int,
    token=Depends(acceso_incidencia("Visualizar_incidencias")),
):
    try:
        return incidencia_services.listar_evidencias(id_incidencia, token)
    except incidencia_services.IncidenciaError as exc:
        _raise(exc)


@router.post("/{id_incidencia}/evidencias", status_code=201)
async def post_evidencia(
    id_incidencia: int,
    request: Request,
    archivo: UploadFile = File(...),
    token=Depends(acceso_incidencia("Modificar_incidencias", permitir_registrador=True)),
):
    try:
        contenido = await archivo.read()
        return incidencia_services.adjuntar_evidencia(
            id_incidencia, token, archivo.filename, archivo.content_type, contenido, _ip(request)
        )
    except incidencia_services.IncidenciaError as exc:
        _raise(exc)


@router.get("/{id_incidencia}/evidencias/{id_evidencia}/archivo")
def get_evidencia_archivo(
    id_incidencia: int,
    id_evidencia: int,
    token=Depends(acceso_incidencia("Visualizar_incidencias")),
):
    try:
        ruta, nombre, tipo_mime = incidencia_services.obtener_ruta_evidencia(
            id_incidencia, id_evidencia, token
        )
        return FileResponse(ruta, media_type=tipo_mime, filename=nombre)
    except incidencia_services.IncidenciaError as exc:
        _raise(exc)
