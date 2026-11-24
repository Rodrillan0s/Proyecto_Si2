"""
Capa de Servicios para CU33: Gestión de Garantías y Posventa
(HU161 a HU168).
Aplica validaciones de negocio, estados de transición y aislamiento multi-tenant.
"""
from datetime import date, datetime
import os
import uuid
from typing import Any, Dict, List, Optional
from app.config import Config
from app.repos import posventa_repos


class PosventaError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


CATEGORIAS_VALIDAS = {
    "PLOMERIA", "ELECTRICIDAD", "ACABADOS", "ESTRUCTURA",
    "CERRAJERIA", "HUMEDAD", "INSTALACIONES", "OTRO"
}

PRIORIDADES_VALIDAS = {"BAJA", "MEDIA", "ALTA", "URGENTE"}

ESTADOS_VALIDOS = {
    "PENDIENTE", "CLASIFICADA", "ASIGNADA", "EN_ATENCION",
    "RESUELTA", "CERRADA", "RECHAZADA"
}

TRANSICIONES_PERMITIDAS = {
    "PENDIENTE": {"CLASIFICADA", "RECHAZADA"},
    "CLASIFICADA": {"ASIGNADA", "RECHAZADA"},
    "ASIGNADA": {"EN_ATENCION", "RECHAZADA", "ASIGNADA"},
    "EN_ATENCION": {"RESUELTA", "EN_ATENCION"},
    "RESUELTA": {"CERRADA", "EN_ATENCION"},
    "CERRADA": set(),
    "RECHAZADA": set(),
}


def _obtener_empresa_usuario(token_data: dict, id_empresa_solicitada: Optional[int] = None) -> int:
    """Resuelve la empresa garantizando que los usuarios no-superadmin no traspasen su tenant."""
    rol = (token_data.get("nombre_rol") or "").upper().strip()
    emp_token = token_data.get("id_empresa")
    if rol == "ADMINISTRADOR":
        return id_empresa_solicitada or emp_token or 1
    if not emp_token:
        raise PosventaError("El usuario no tiene una constructora/empresa asociada.", 403)
    if id_empresa_solicitada and int(id_empresa_solicitada) != int(emp_token):
        raise PosventaError("No tiene autorización para operar en otra empresa.", 403)
    return int(emp_token)


# ─────────────────────────────────────────────────────────────────────────────
# 1. SERVICIOS DE GARANTÍAS (HU161, HU162)
# ─────────────────────────────────────────────────────────────────────────────

def listar_opciones_garantia(token_data: dict) -> List[Dict[str, Any]]:
    """Opciones comerciales y propietarios válidos para los formularios web/móvil."""
    id_empresa = _obtener_empresa_usuario(token_data)
    return posventa_repos.listar_opciones_garantia(id_empresa)

def registrar_garantia_inmobiliaria(
    token_data: dict,
    id_unidad: int,
    id_cliente: int,
    tipo_garantia: str,
    descripcion_cobertura: str,
    fecha_inicio: date,
    fecha_fin: date,
    condiciones: Optional[str] = None
) -> Dict[str, Any]:
    """HU161: Como Administrador_empresa, registrar garantías asociadas a unidades comercializadas."""
    id_empresa = _obtener_empresa_usuario(token_data)
    id_usuario = token_data.get("nro_usuario")

    if not tipo_garantia or not tipo_garantia.strip():
        raise PosventaError("El tipo de garantía es obligatorio (ej. ESTRUCTURAL, ACABADOS).", 422)
    if not descripcion_cobertura or not descripcion_cobertura.strip():
        raise PosventaError("La descripción de cobertura es obligatoria.", 422)
    if fecha_fin < fecha_inicio:
        raise PosventaError("La fecha de fin no puede ser anterior a la fecha de inicio.", 422)

    # Validar pertenencia de la unidad a la empresa
    unidad = posventa_repos.verificar_unidad_pertenece_empresa(id_unidad, id_empresa)
    if not unidad:
        raise PosventaError("La unidad inmobiliaria no existe o no pertenece a su constructora.", 404)

    # Validar que el cliente tenga o haya tenido vinculación con la unidad
    es_propietario = posventa_repos.verificar_cliente_propietario_unidad(id_cliente, id_unidad, id_empresa)
    if not es_propietario:
        raise PosventaError("El cliente seleccionado no tiene la unidad adquirida o asignada.", 400)

    id_garantia = posventa_repos.registrar_garantia(
        id_empresa=id_empresa,
        id_unidad=id_unidad,
        id_cliente=id_cliente,
        tipo_garantia=tipo_garantia.strip().upper(),
        descripcion_cobertura=descripcion_cobertura.strip(),
        condiciones=condiciones.strip() if condiciones else None,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        id_usuario_registro=id_usuario
    )

    garantia_creada = posventa_repos.obtener_garantia_por_id(id_garantia, id_empresa)
    return {
        "success": True,
        "message": "Garantía inmobiliaria registrada exitosamente.",
        "garantia": garantia_creada
    }


def consultar_garantias(
    token_data: dict,
    id_unidad: Optional[int] = None,
    id_cliente: Optional[int] = None,
    id_obra: Optional[int] = None,
    estado: Optional[str] = None
) -> List[Dict[str, Any]]:
    """HU162: Como Cliente (o Admin), consultar garantías asociadas."""
    id_empresa = _obtener_empresa_usuario(token_data)
    rol = (token_data.get("nombre_rol") or "").upper().strip()
    id_usuario = token_data.get("nro_usuario")

    def _clean(v):
        return None if hasattr(v, "default") else v

    id_unidad = _clean(id_unidad)
    id_cliente = _clean(id_cliente)
    id_obra = _clean(id_obra)
    estado = _clean(estado)

    # Si es CLIENTE, forzar a consultar ÚNICAMENTE sus propias garantías
    if rol == "CLIENTE":
        cliente_info = posventa_repos.obtener_cliente_por_usuario(id_usuario, id_empresa)
        if not cliente_info:
            return []
        id_cliente = cliente_info["id_cliente"]

    return posventa_repos.listar_garantias(
        id_empresa=id_empresa,
        id_unidad=id_unidad,
        id_cliente=id_cliente,
        id_obra=id_obra,
        estado=estado
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. SOLICITUDES DE POSVENTA (HU163, HU164, HU165, HU166, HU167)
# ─────────────────────────────────────────────────────────────────────────────

def registrar_solicitud_posventa(
    token_data: dict,
    id_unidad: int,
    titulo: str,
    descripcion_defecto: str,
    id_cliente: Optional[int] = None,
    id_garantia: Optional[int] = None
) -> Dict[str, Any]:
    """HU163: Como Cliente (o Admin en su nombre), registrar solicitud de posventa."""
    id_empresa = _obtener_empresa_usuario(token_data)
    id_usuario = token_data.get("nro_usuario")
    rol = (token_data.get("nombre_rol") or "").upper().strip()

    if not titulo or not titulo.strip():
        raise PosventaError("El título de la solicitud es obligatorio.", 422)
    if not descripcion_defecto or not descripcion_defecto.strip():
        raise PosventaError("Debe detallar el defecto o problema identificado.", 422)

    # Identificar al cliente
    if rol == "CLIENTE":
        cliente_info = posventa_repos.obtener_cliente_por_usuario(id_usuario, id_empresa)
        if not cliente_info:
            raise PosventaError("No se encontró su perfil de cliente en la empresa.", 403)
        id_cliente_efectivo = cliente_info["id_cliente"]
    else:
        if not id_cliente:
            raise PosventaError("Debe indicar el cliente propietario de la unidad.", 422)
        id_cliente_efectivo = id_cliente

    # Validar que la unidad pertenece a la empresa y al cliente
    unidad = posventa_repos.verificar_unidad_pertenece_empresa(id_unidad, id_empresa)
    if not unidad:
        raise PosventaError("La unidad inmobiliaria no existe o no pertenece a la constructora.", 404)

    es_propietario = posventa_repos.verificar_cliente_propietario_unidad(id_cliente_efectivo, id_unidad, id_empresa)
    if not es_propietario:
        raise PosventaError("El cliente no figura como propietario de la unidad seleccionada.", 403)

    # Si se pasó una garantía, validar que pertenezca a la misma unidad
    if id_garantia:
        gar = posventa_repos.obtener_garantia_por_id(id_garantia, id_empresa)
        if not gar or gar["id_unidad"] != id_unidad:
            raise PosventaError("La garantía especificada no corresponde a esta unidad inmobiliaria.", 400)

    id_solicitud, codigo_ticket = posventa_repos.registrar_solicitud(
        id_empresa=id_empresa,
        id_unidad=id_unidad,
        id_cliente=id_cliente_efectivo,
        titulo=titulo.strip(),
        descripcion_defecto=descripcion_defecto.strip(),
        id_garantia=id_garantia,
        id_usuario_registro=id_usuario
    )

    solicitud_detalle = posventa_repos.obtener_solicitud_detalle(id_solicitud, id_empresa)
    return {
        "success": True,
        "message": f"Solicitud registrada exitosamente con código de ticket: {codigo_ticket}",
        "codigo_ticket": codigo_ticket,
        "solicitud": solicitud_detalle
    }


def clasificar_solicitud_posventa(
    token_data: dict,
    id_solicitud: int,
    categoria: str,
    prioridad: str,
    aplica_garantia: bool,
    id_garantia: Optional[int] = None,
    observaciones: Optional[str] = None
) -> Dict[str, Any]:
    """HU164: Como Administrador_empresa, clasificar categoría, prioridad y validar garantía."""
    id_empresa = _obtener_empresa_usuario(token_data)
    id_usuario = token_data.get("nro_usuario")

    categoria_upper = categoria.strip().upper() if categoria else ""
    if categoria_upper not in CATEGORIAS_VALIDAS:
        raise PosventaError(f"Categoría inválida. Debe ser una de: {', '.join(sorted(CATEGORIAS_VALIDAS))}", 422)

    prioridad_upper = prioridad.strip().upper() if prioridad else ""
    if prioridad_upper not in PRIORIDADES_VALIDAS:
        raise PosventaError(f"Prioridad inválida. Debe ser una de: {', '.join(sorted(PRIORIDADES_VALIDAS))}", 422)

    solicitud = posventa_repos.obtener_solicitud_detalle(id_solicitud, id_empresa)
    if not solicitud:
        raise PosventaError("La solicitud de posventa no existe o no pertenece a su constructora.", 404)

    if solicitud["estado"] not in ("PENDIENTE", "CLASIFICADA"):
        raise PosventaError(f"No se puede clasificar una solicitud en estado {solicitud['estado']}.", 400)

    # Si aplica garantía, validar que la garantía exista, esté vigente y corresponda a la unidad
    if aplica_garantia:
        if not id_garantia:
            raise PosventaError("Debe seleccionar la garantía vigente aplicable.", 422)
        gar = posventa_repos.obtener_garantia_por_id(id_garantia, id_empresa)
        if not gar:
            raise PosventaError("La garantía especificada no existe.", 404)
        if gar["id_unidad"] != solicitud["id_unidad"]:
            raise PosventaError("La garantía seleccionada no corresponde a la unidad de la solicitud.", 400)
        if gar["estado"] == "VENCIDA":
            raise PosventaError("La garantía seleccionada ya se encuentra vencida.", 400)

    ok = posventa_repos.clasificar_solicitud(
        id_solicitud=id_solicitud,
        id_empresa=id_empresa,
        categoria=categoria_upper,
        prioridad=prioridad_upper,
        aplica_garantia=aplica_garantia,
        id_garantia=id_garantia if aplica_garantia else None,
        observaciones=observaciones.strip() if observaciones else None,
        id_usuario_clasifica=id_usuario
    )
    if not ok:
        raise PosventaError("No se pudo clasificar la solicitud.", 500)

    actualizada = posventa_repos.obtener_solicitud_detalle(id_solicitud, id_empresa)
    return {
        "success": True,
        "message": "Solicitud clasificada correctamente y habilitada para asignación de obra.",
        "solicitud": actualizada
    }


def asignar_responsable_atencion(
    token_data: dict,
    id_solicitud: int,
    id_supervisor: int,
    fecha_estimada_visita: date,
    instrucciones_tecnicas: Optional[str] = None
) -> Dict[str, Any]:
    """HU165: Como Jefe de Obra, asignar supervisor responsable y fecha de visita."""
    id_empresa = _obtener_empresa_usuario(token_data)
    id_usuario = token_data.get("nro_usuario")

    solicitud = posventa_repos.obtener_solicitud_detalle(id_solicitud, id_empresa)
    if not solicitud:
        raise PosventaError("La solicitud de posventa no existe o no pertenece a su constructora.", 404)

    if solicitud["estado"] not in ("CLASIFICADA", "ASIGNADA"):
        raise PosventaError(f"Solo se pueden asignar solicitudes en estado CLASIFICADA o ASIGNADA (actual: {solicitud['estado']}).", 400)

    # Validar que el supervisor esté en la lista de personal disponible
    supervisores = posventa_repos.listar_supervisores_disponibles(id_empresa)
    sup_ids = {s["id_usuario"] for s in supervisores}
    if id_supervisor not in sup_ids:
        raise PosventaError("El usuario seleccionado no es un supervisor técnico activo de la constructora.", 400)

    ok = posventa_repos.asignar_supervisor_solicitud(
        id_solicitud=id_solicitud,
        id_empresa=id_empresa,
        id_supervisor=id_supervisor,
        fecha_estimada_visita=fecha_estimada_visita,
        instrucciones_tecnicas=instrucciones_tecnicas.strip() if instrucciones_tecnicas else None,
        id_usuario_asigna=id_usuario
    )
    if not ok:
        raise PosventaError("No se pudo asignar el responsable a la solicitud.", 500)

    actualizada = posventa_repos.obtener_solicitud_detalle(id_solicitud, id_empresa)
    return {
        "success": True,
        "message": f"Solicitud asignada al supervisor con visita programada para {fecha_estimada_visita}.",
        "solicitud": actualizada
    }


def gestionar_atencion_solicitud(
    token_data: dict,
    id_solicitud: int,
    nuevo_estado: str,
    acciones_realizadas: str,
    materiales_utilizados: Optional[str] = None,
    motivo_cierre: Optional[str] = None
) -> Dict[str, Any]:
    """HU166: Como Supervisor, registrar avances, bitácora de visita, insumos y cierre."""
    id_empresa = _obtener_empresa_usuario(token_data)
    id_usuario = token_data.get("nro_usuario")
    rol = (token_data.get("nombre_rol") or "").upper().strip()

    nuevo_estado_upper = nuevo_estado.strip().upper()
    if nuevo_estado_upper not in ("EN_ATENCION", "RESUELTA", "CERRADA"):
        raise PosventaError("El nuevo estado debe ser EN_ATENCION, RESUELTA o CERRADA.", 422)

    if not acciones_realizadas or not acciones_realizadas.strip():
        raise PosventaError("Debe describir las acciones técnicas o visita realizada.", 422)

    solicitud = posventa_repos.obtener_solicitud_detalle(id_solicitud, id_empresa)
    if not solicitud:
        raise PosventaError("La solicitud de posventa no existe o no pertenece a su constructora.", 404)

    # Validar transiciones
    permitidos = TRANSICIONES_PERMITIDAS.get(solicitud["estado"], set())
    if nuevo_estado_upper not in permitidos and nuevo_estado_upper != solicitud["estado"]:
        raise PosventaError(f"Transición de estado no permitida desde '{solicitud['estado']}' hacia '{nuevo_estado_upper}'.", 400)

    # Si es supervisor, verificar que esté asignado a esta solicitud
    if "SUPERVISOR" in rol and solicitud.get("id_supervisor_asignado") != id_usuario:
        raise PosventaError("Solo el supervisor asignado a este ticket puede registrar la atención.", 403)

    ok = posventa_repos.registrar_atencion_tecnica(
        id_solicitud=id_solicitud,
        id_empresa=id_empresa,
        id_supervisor=id_usuario,
        nuevo_estado=nuevo_estado_upper,
        acciones_realizadas=acciones_realizadas.strip(),
        materiales_utilizados=materiales_utilizados.strip() if materiales_utilizados else None,
        motivo_cierre=motivo_cierre.strip() if motivo_cierre else None
    )
    if not ok:
        raise PosventaError("No se pudo actualizar la atención del ticket.", 500)

    actualizada = posventa_repos.obtener_solicitud_detalle(id_solicitud, id_empresa)
    return {
        "success": True,
        "message": f"Estado de atención actualizado a '{nuevo_estado_upper}'.",
        "solicitud": actualizada
    }


def adjuntar_evidencia_solicitud(
    token_data: dict,
    id_solicitud: int,
    tipo_evidencia: str,
    nombre_archivo: str,
    contenido_bytes: bytes,
    tipo_mime: Optional[str] = None
) -> Dict[str, Any]:
    """Adjunta una fotografía o evidencia (reportada por cliente o de reparación del supervisor)."""
    id_empresa = _obtener_empresa_usuario(token_data)
    id_usuario = token_data.get("nro_usuario")

    tipo_ev_upper = tipo_evidencia.strip().upper()
    if tipo_ev_upper not in ("CLIENTE_REPORTE", "SUPERVISOR_REPARACION", "DOCUMENTO_ADJUNTO"):
        raise PosventaError("Tipo de evidencia inválido.", 422)

    solicitud = posventa_repos.obtener_solicitud_detalle(id_solicitud, id_empresa)
    if not solicitud:
        raise PosventaError("La solicitud no existe en su empresa.", 404)

    # Directorio de almacenamiento seguro
    directorio_destino = os.path.join("uploads", "posventa", str(id_empresa), str(id_solicitud))
    os.makedirs(directorio_destino, exist_ok=True)

    ext = os.path.splitext(nombre_archivo)[1]
    nombre_guardado = f"{uuid.uuid4().hex[:12]}{ext}"
    ruta_guardado = os.path.join(directorio_destino, nombre_guardado)

    with open(ruta_guardado, "wb") as f:
        f.write(contenido_bytes)

    id_evidencia = posventa_repos.agregar_evidencia(
        id_solicitud=id_solicitud,
        tipo_evidencia=tipo_ev_upper,
        ruta_archivo=ruta_guardado.replace("\\", "/"),
        nombre_archivo=nombre_archivo,
        tipo_mime=tipo_mime,
        tamano_bytes=len(contenido_bytes),
        id_usuario=id_usuario
    )

    return {
        "success": True,
        "message": "Evidencia adjuntada exitosamente al ticket.",
        "id_evidencia": id_evidencia,
        "nombre_archivo": nombre_archivo,
        "ruta_archivo": ruta_guardado.replace("\\", "/")
    }


def consultar_solicitudes_posventa(
    token_data: dict,
    id_cliente: Optional[int] = None,
    id_supervisor: Optional[int] = None,
    id_obra: Optional[int] = None,
    id_unidad: Optional[int] = None,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    categoria: Optional[str] = None
) -> List[Dict[str, Any]]:
    """HU167 y HU168: Consultar listado de solicitudes según el rol del usuario."""
    id_empresa = _obtener_empresa_usuario(token_data)
    rol = (token_data.get("nombre_rol") or "").upper().strip()
    id_usuario = token_data.get("nro_usuario")

    def _clean(v):
        return None if hasattr(v, "default") else v

    id_cliente = _clean(id_cliente)
    id_supervisor = _clean(id_supervisor)
    id_obra = _clean(id_obra)
    id_unidad = _clean(id_unidad)
    estado = _clean(estado)
    prioridad = _clean(prioridad)
    categoria = _clean(categoria)

    # Si es CLIENTE, solo sus propios reclamos
    if rol == "CLIENTE":
        cliente_info = posventa_repos.obtener_cliente_por_usuario(id_usuario, id_empresa)
        if not cliente_info:
            return []
        id_cliente = cliente_info["id_cliente"]

    # Si es SUPERVISOR, priorizar las asignadas a él si no se solicita otra cosa
    elif "SUPERVISOR" in rol and not id_supervisor:
        id_supervisor = id_usuario

    return posventa_repos.listar_solicitudes(
        id_empresa=id_empresa,
        id_cliente=id_cliente,
        id_supervisor=id_supervisor,
        id_obra=id_obra,
        id_unidad=id_unidad,
        estado=estado,
        prioridad=prioridad,
        categoria=categoria
    )


def consultar_detalle_solicitud_posventa(token_data: dict, id_solicitud: int) -> Dict[str, Any]:
    """HU167: Detalle completo de una solicitud con timeline y evidencias."""
    id_empresa = _obtener_empresa_usuario(token_data)
    rol = (token_data.get("nombre_rol") or "").upper().strip()
    id_usuario = token_data.get("nro_usuario")

    solicitud = posventa_repos.obtener_solicitud_detalle(id_solicitud, id_empresa)
    if not solicitud:
        raise PosventaError("Solicitud no encontrada o no pertenece a su constructora.", 404)

    # Verificación de pertenencia si es CLIENTE
    if rol == "CLIENTE":
        cliente_info = posventa_repos.obtener_cliente_por_usuario(id_usuario, id_empresa)
        if not cliente_info or solicitud["id_cliente"] != cliente_info["id_cliente"]:
            raise PosventaError("No está autorizado para ver esta solicitud.", 403)

    return solicitud


def consultar_historial_y_metricas(token_data: dict) -> Dict[str, Any]:
    """HU168: Historial integral y métricas para auditoría y control de calidad."""
    id_empresa = _obtener_empresa_usuario(token_data)
    metricas = posventa_repos.obtener_metricas_posventa(id_empresa)
    return {
        "success": True,
        "metricas": metricas
    }


def obtener_supervisores_empresa(token_data: dict, id_obra: Optional[int] = None) -> List[Dict[str, Any]]:
    """Lista supervisores disponibles para el dropdown de asignación en obra."""
    id_empresa = _obtener_empresa_usuario(token_data)
    return posventa_repos.listar_supervisores_disponibles(id_empresa, id_obra)
