from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from app.services import crm_services
from app.utils.security import exigir_permiso, exigir_rol, verificar_token, obtener_permisos_rol


router = APIRouter(tags=["CRM"])


def _ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _raise(exc):
    raise HTTPException(status_code=exc.status_code, detail=str(exc))


def acceso_emision_comunicaciones(token_data: dict = Depends(verificar_token)):
    rol = str(token_data.get("nombre_rol") or "").strip().upper()
    if rol == "ADMINISTRADOR":
        return token_data
    roles_permitidos = {"ADMINISTRADOR", "ADMINISTRADOR_EMPRESA", "JEFE DE OBRA", "JEFE_OBRA", "RESPONSABLE"}
    permisos = obtener_permisos_rol(rol)
    if rol in roles_permitidos or "Modificar_clientes" in permisos or "Registrar_clientes" in permisos:
        return token_data
    raise HTTPException(status_code=403, detail="No tiene permisos para enviar comunicaciones a clientes.")


def acceso_gestion_solicitudes(token_data: dict = Depends(verificar_token)):
    rol = str(token_data.get("nombre_rol") or "").strip().upper()
    if rol == "ADMINISTRADOR":
        return token_data
    roles_permitidos = {"ADMINISTRADOR", "ADMINISTRADOR_EMPRESA", "JEFE DE OBRA", "JEFE_OBRA", "RESPONSABLE"}
    permisos = obtener_permisos_rol(rol)
    if rol in roles_permitidos or "Modificar_clientes" in permisos or "Modificar_obras" in permisos:
        return token_data
    raise HTTPException(status_code=403, detail="No tiene permisos para gestionar solicitudes de clientes.")


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/crm/clientes
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/clientes")
def get_clientes(
    tipo_cliente: str = None,
    estado: str = None,
    q: str = None,
    id_usuario_asignado: int = None,
    page: int = 1,
    limit: int = Query(20, le=100),
    id_empresa: int = None,
    token=Depends(exigir_permiso("Visualizar_clientes")),
):
    try:
        return crm_services.listar(
            token=token,
            tipo_cliente=tipo_cliente,
            estado=estado,
            q=q,
            id_usuario_asignado=id_usuario_asignado,
            page=page,
            limit=limit,
            id_empresa_solicitada=id_empresa
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/crm/clientes/metricas
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/clientes/metricas")
def get_metricas(
    id_empresa: int = None,
    token=Depends(exigir_permiso("Visualizar_clientes")),
):
    try:
        return crm_services.obtener_metricas(token=token, id_empresa_solicitada=id_empresa)
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/crm/asesores
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/asesores")
def get_asesores(
    id_empresa: int = None,
    token=Depends(exigir_permiso("Visualizar_clientes")),
):
    try:
        return crm_services.listar_asesores(token=token, id_empresa_solicitada=id_empresa)
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/crm/clientes/unidades-disponibles
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/clientes/unidades-disponibles")
def get_unidades_disponibles(
    id_obra: int = None,
    id_empresa: int = None,
    token=Depends(exigir_permiso("Visualizar_clientes")),
):
    try:
        return crm_services.listar_unidades_disponibles(
            token=token, id_obra=id_obra, id_empresa_solicitada=id_empresa
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/crm/cliente/unidades
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/cliente/unidades")
def get_unidades_cliente(
    token=Depends(exigir_rol("CLIENTE")),
):
    try:
        return crm_services.listar_unidades_cliente_autenticado(token)
    except crm_services.CrmError as exc:
        _raise(exc)


@router.get("/cliente/unidades/{id_unidad}/fotografias")
def get_fotografias_cliente(
    id_unidad: int,
    token=Depends(exigir_rol("CLIENTE")),
):
    try:
        return crm_services.listar_fotografias_cliente_autenticado(id_unidad, token)
    except crm_services.CrmError as exc:
        _raise(exc)


@router.get("/cliente/unidades/{id_unidad}/fotografias/{id_fotografia}/archivo")
def get_archivo_fotografia_cliente(
    id_unidad: int,
    id_fotografia: int,
    token=Depends(exigir_rol("CLIENTE")),
):
    try:
        ruta, nombre, tipo_mime = crm_services.obtener_archivo_fotografia_cliente_autenticado(
            id_unidad,
            id_fotografia,
            token,
        )
        return FileResponse(ruta, media_type=tipo_mime, filename=nombre)
    except crm_services.CrmError as exc:
        _raise(exc)


@router.get("/cliente/comunicaciones")
def get_comunicaciones_cliente(
    token=Depends(exigir_rol("CLIENTE")),
):
    try:
        return crm_services.listar_comunicaciones_cliente_autenticado(token)
    except crm_services.CrmError as exc:
        _raise(exc)


@router.post("/comunicaciones", status_code=201)
def post_crear_comunicacion(
    request: Request,
    data: dict = Body(...),
    token=Depends(acceso_emision_comunicaciones),
):
    try:
        return crm_services.crear_comunicacion_cliente(
            data=data,
            token=token,
            ip=_ip(request),
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# HU117: SOLICITUDES DE CLIENTE
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/cliente/solicitudes")
def get_solicitudes_cliente(
    token=Depends(exigir_rol("CLIENTE")),
):
    try:
        return crm_services.listar_solicitudes_cliente_autenticado(token)
    except crm_services.CrmError as exc:
        _raise(exc)


@router.get("/cliente/solicitudes/{id_solicitud}")
def get_detalle_solicitud_cliente(
    id_solicitud: int,
    token=Depends(exigir_rol("CLIENTE")),
):
    try:
        return crm_services.obtener_detalle_solicitud_cliente_autenticado(id_solicitud, token)
    except crm_services.CrmError as exc:
        _raise(exc)


@router.post("/cliente/solicitudes", status_code=201)
def post_solicitud_cliente(
    request: Request,
    data: dict = Body(...),
    token=Depends(exigir_rol("CLIENTE")),
):
    try:
        return crm_services.registrar_solicitud_cliente_autenticado(
            data=data,
            token=token,
            ip=_ip(request),
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# HU117: GESTIÓN DE SOLICITUDES POR CONSTRUCTORA
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/solicitudes")
def get_solicitudes_constructora(
    id_obra: int = None,
    estado: str = None,
    token=Depends(acceso_gestion_solicitudes),
):
    try:
        return crm_services.listar_solicitudes_constructora(
            token=token,
            id_obra=id_obra,
            estado=estado,
        )
    except crm_services.CrmError as exc:
        _raise(exc)


@router.post("/solicitudes/{id_solicitud}/responder")
def responder_solicitud_constructora(
    id_solicitud: int,
    request: Request,
    data: dict = Body(...),
    token=Depends(acceso_gestion_solicitudes),
):
    try:
        return crm_services.responder_solicitud_constructora(
            id_solicitud=id_solicitud,
            data=data,
            token=token,
            ip=_ip(request),
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/crm/clientes
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/clientes", status_code=201)
def post_cliente(
    request: Request,
    data: dict = Body(...),
    id_empresa: int = None,
    token=Depends(exigir_permiso("Registrar_clientes")),
):
    try:
        return crm_services.registrar(
            data=data,
            token=token,
            ip=_ip(request),
            id_empresa_solicitada=id_empresa
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/crm/clientes/{id_cliente}
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/clientes/{id_cliente}")
def get_cliente_detalle(
    id_cliente: int,
    id_empresa: int = None,
    token=Depends(exigir_permiso("Visualizar_clientes")),
):
    try:
        return crm_services.obtener_detalle_historial(
            id_cliente=id_cliente,
            token=token,
            id_empresa_solicitada=id_empresa
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/crm/clientes/{id_cliente}
# ─────────────────────────────────────────────────────────────────────────────
@router.put("/clientes/{id_cliente}")
def put_cliente(
    id_cliente: int,
    request: Request,
    data: dict = Body(...),
    id_empresa: int = None,
    token=Depends(exigir_permiso("Modificar_clientes")),
):
    try:
        return crm_services.actualizar(
            id_cliente=id_cliente,
            data=data,
            token=token,
            ip=_ip(request),
            id_empresa_solicitada=id_empresa
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /api/crm/clientes/{id_cliente}/clasificacion
# ─────────────────────────────────────────────────────────────────────────────
@router.patch("/clientes/{id_cliente}/clasificacion")
def patch_clasificacion(
    id_cliente: int,
    request: Request,
    data: dict = Body(...),
    id_empresa: int = None,
    token=Depends(exigir_permiso("Modificar_clientes")),
):
    try:
        nuevo_estado = data.get("estado")
        nota = data.get("nota")
        return crm_services.clasificar_prospecto(
            id_cliente=id_cliente,
            nuevo_estado=nuevo_estado,
            token=token,
            ip=_ip(request),
            id_empresa_solicitada=id_empresa,
            nota=nota
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/crm/clientes/{id_cliente}/interacciones
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/clientes/{id_cliente}/interacciones", status_code=201)
def post_interaccion(
    id_cliente: int,
    request: Request,
    data: dict = Body(...),
    id_empresa: int = None,
    token=Depends(exigir_permiso("Modificar_clientes")),
):
    try:
        return crm_services.registrar_interaccion(
            id_cliente=id_cliente,
            data=data,
            token=token,
            ip=_ip(request),
            id_empresa_solicitada=id_empresa
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/crm/clientes/{id_cliente}/unidades
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/clientes/{id_cliente}/unidades", status_code=201)
def post_asociar_unidad(
    id_cliente: int,
    request: Request,
    data: dict = Body(...),
    id_empresa: int = None,
    token=Depends(exigir_permiso("Modificar_clientes")),
):
    try:
        return crm_services.asociar_unidad(
            id_cliente=id_cliente,
            data=data,
            token=token,
            ip=_ip(request),
            id_empresa_solicitada=id_empresa
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /api/crm/asociaciones/{id_cliente_unidad}/estado
# ─────────────────────────────────────────────────────────────────────────────
@router.patch("/asociaciones/{id_cliente_unidad}/estado")
def patch_estado_asociacion(
    id_cliente_unidad: int,
    request: Request,
    data: dict = Body(...),
    id_empresa: int = None,
    token=Depends(exigir_permiso("Modificar_clientes")),
):
    try:
        nuevo_estado = data.get("estado_asociacion")
        observaciones = data.get("observaciones")
        return crm_services.cambiar_estado_asociacion(
            id_cliente_unidad=id_cliente_unidad,
            nuevo_estado=nuevo_estado,
            observaciones=observaciones,
            token=token,
            ip=_ip(request),
            id_empresa_solicitada=id_empresa
        )
    except crm_services.CrmError as exc:
        _raise(exc)
