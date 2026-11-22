"""
Servicio de negocio para CU31: Comercialización de unidades inmobiliarias
(HU143, HU144, HU145, HU146).
Implementa reglas de negocio, máquina de estados comercial, sincronización con CRM,
gestión segura de fotografías (MIME, magic bytes, límite de tamaño y prevención de path traversal),
transacciones atómicas y aislamiento multi-tenant estricto.
"""
import re
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import UploadFile

from app.classes.postgres import PostgreSQL
from app.config import Config
from app.repos import bitacora_repos, comercializacion_repos
from app.utils.security import es_admin_sistema


ESTADOS_COMERCIALES = {"DISPONIBLE", "RESERVADA", "VENDIDA", "NO_DISPONIBLE"}
MONEDAS_VALIDAS = {"BOB", "USD"}
TIPOS_EVENTO_HISTORIAL = {
    "PUBLICACION",
    "DESPUBLICACION",
    "ACTUALIZACION_PRECIO",
    "ACTUALIZACION_COMERCIAL",
    "FOTOGRAFIA_AGREGADA",
    "FOTOGRAFIA_ELIMINADA",
    "RESERVA",
    "CANCELACION",
    "VENTA",
    "CAMBIO_ESTADO",
}

# Configuración de seguridad para fotografías (HU143)
MAX_FOTO_BYTES = 10 * 1024 * 1024  # 10 MB
EXTENSIONES_FOTO_VALIDAS = {".jpg", ".jpeg", ".png", ".webp"}
MIMES_FOTO_VALIDOS = {"image/jpeg", "image/jpg", "image/png", "image/webp"}

# Transiciones comerciales permitidas por estado origen (HU145)
TRANSICIONES_COMERCIALES = {
    "DISPONIBLE": {"RESERVADA", "VENDIDA", "NO_DISPONIBLE"},
    "RESERVADA": {"DISPONIBLE", "VENDIDA"},
    "NO_DISPONIBLE": {"DISPONIBLE"},
    "VENDIDA": set(),  # Estado comercial terminal
}


class ComercializacionError(ValueError):
    """Excepción de dominio para errores comerciales."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _directorio_base_uploads() -> Path:
    """Retorna el directorio base seguro para fotografías de comercialización."""
    backend_dir = Path(__file__).resolve().parents[2]
    base = (backend_dir / "uploads" / "comercializacion").resolve()
    base.mkdir(parents=True, exist_ok=True)
    return base


def _verificar_ruta_segura(ruta_objetivo: Path, directorio_base: Optional[Path] = None) -> Path:
    """
    Previene ataques de Path Traversal asegurando que la ruta resuelta
    esté estrictamente contenida dentro del directorio base de comercialización.
    """
    base = (directorio_base or _directorio_base_uploads()).resolve()
    resuelta = ruta_objetivo.resolve()
    try:
        resuelta.relative_to(base)
    except ValueError:
        raise ComercializacionError("Acceso denegado: ruta de archivo fuera del directorio permitido.", 403)
    return resuelta


def _sanitizar_nombre_archivo(nombre: str) -> str:
    """Extrae el basename y limpia caracteres peligrosos evitando path traversal."""
    crudo = str(nombre or "").replace("\\", "/")
    if ".." in crudo:
        raise ComercializacionError("Nombre de archivo inválido: secuencia '..' no permitida.", 400)
    limpio = Path(crudo).name.strip()
    limpio = re.sub(r"[^A-Za-z0-9._\- ]", "_", limpio)
    if not limpio or limpio in {".", ".."}:
        raise ComercializacionError("Nombre de archivo inválido.", 400)
    return limpio[:200]


def _detectar_mime_real(contenido: bytes) -> Optional[str]:
    """Verifica los magic bytes binarios de la imagen."""
    if contenido.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if contenido.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(contenido) >= 12 and contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP":
        return "image/webp"
    return None


def _resolver_empresa(token: dict, id_empresa_solicitada=None, obligatorio: bool = True) -> Optional[int]:
    """
    Resuelve y valida estrictamente el id_empresa del actor.
    - Administrador global: puede indicar una empresa (validada contra BD) o usar su asignada.
    - Usuario de empresa: NUNCA confía en id_empresa enviado por frontend;
      está estrictamente atado a token['id_empresa']. Si intenta forzar un id_empresa
      distinto de su token en operaciones sensibles o consultas, o si no tiene empresa, se controla.
    """
    if not isinstance(token, dict):
        raise ComercializacionError("Token de autenticación inválido.", 401)

    if es_admin_sistema(token):
        if id_empresa_solicitada is not None and str(id_empresa_solicitada).strip() != "":
            try:
                emp_id = int(id_empresa_solicitada)
                db = PostgreSQL()
                db.create_connection()
                try:
                    existe = db.execute_query(
                        f"SELECT 1 FROM {Config.SCHEMA}.t_empresa WHERE id_empresa = %s;",
                        (emp_id,),
                        fetchone=True
                    )
                    if not existe:
                        raise ComercializacionError(f"La empresa ID {emp_id} no existe.", 404)
                    return emp_id
                finally:
                    db.close_connection()
            except (ValueError, TypeError):
                raise ComercializacionError("id_empresa debe ser un número entero válido.", 400)
        return int(token.get("id_empresa") or 1)

    emp_token = token.get("id_empresa")
    if obligatorio and not emp_token:
        raise ComercializacionError("Usuario sin empresa asignada.", 403)
    return int(emp_token) if emp_token is not None else None


def _validar_precio(valor, campo: str = "precio_venta", permitir_nulo: bool = True) -> Optional[float]:
    if valor is None:
        if permitir_nulo:
            return None
        raise ComercializacionError(f"{campo} es obligatorio y no puede ser nulo.", 400)
    if isinstance(valor, bool):
        raise ComercializacionError(f"{campo} debe ser un número válido.", 400)
    try:
        dec = Decimal(str(valor).strip())
        if not dec.is_finite():
            raise InvalidOperation
    except (InvalidOperation, TypeError, ValueError):
        raise ComercializacionError(f"{campo} debe ser un número decimal válido.", 400)
    if dec < Decimal("0"):
        raise ComercializacionError(f"{campo} no puede ser negativo.", 400)
    return float(dec)


def _validar_fecha_vencimiento(valor) -> Optional[str]:
    if valor is None or str(valor).strip() == "":
        return None
    if isinstance(valor, date) and not isinstance(valor, datetime):
        fecha_obj = valor
    else:
        texto = str(valor).strip()[:10]
        try:
            fecha_obj = date.fromisoformat(texto)
        except ValueError:
            raise ComercializacionError("fecha_vencimiento_reserva debe tener formato YYYY-MM-DD válido.", 400)
    return fecha_obj.isoformat()


def _log_bitacora(token: dict, accion: str, descripcion: str, ip: str = "unknown", estado: str = "EXITOSO"):
    try:
        user_id = token.get("nro_usuario") or token.get("id_usuario")
        bitacora_repos.registrar_bitacora(
            id_usuario=user_id,
            modulo="CRM",
            accion=accion,
            descripcion=descripcion,
            ip=ip or "unknown",
            estado=estado
        )
    except Exception:
        pass


def _mapear_excepcion_repo(exc: Exception):
    """Traduce excepciones controladas de transacciones del repositorio a ComercializacionError."""
    if isinstance(exc, ComercializacionError):
        raise exc
    if isinstance(exc, LookupError):
        raise ComercializacionError(str(exc), 404)
    if isinstance(exc, PermissionError):
        raise ComercializacionError(str(exc), 403)
    if isinstance(exc, RuntimeError):
        msg = str(exc)
        if msg.startswith(("CONFLICTO_RESERVA:", "CONFLICTO_ESTADO:", "CONFLICTO_CLIENTE:")):
            raise ComercializacionError(msg.split(":", 1)[1], 409)
        if msg.startswith(("ESTADO_INCONSISTENTE:", "SIN_RESERVA_ACTIVA:", "CLIENTE_REQUERIDO:")):
            raise ComercializacionError(msg.split(":", 1)[1], 400)
        raise ComercializacionError(msg, 400)
    raise exc


# ─────────────────────────────────────────────────────────────────────────────
# LISTADO, DETALLE, DISPONIBILIDAD Y RESUMEN (HU143, HU145)
# ─────────────────────────────────────────────────────────────────────────────
def listar_unidades(
    token: dict,
    id_obra: Optional[int] = None,
    estado_comercial: Optional[str] = None,
    publicado: Optional[bool] = None,
    tipo_unidad: Optional[str] = None,
    solo_disponibles: bool = False,
    q: Optional[str] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    page: int = 1,
    limit: int = 20,
    id_empresa_solicitada: Optional[int] = None
) -> Dict:
    """Lista unidades de construcción bajo la perspectiva de comercialización con filtros."""
    id_empresa = _resolver_empresa(token, id_empresa_solicitada)
    if not id_empresa:
        raise ComercializacionError("Debe especificar una empresa para consultar unidades comerciales.", 400)

    if estado_comercial:
        estado_clean = estado_comercial.strip().upper()
        if estado_clean not in ESTADOS_COMERCIALES:
            raise ComercializacionError(
                f"Estado comercial inválido '{estado_comercial}'. Válidos: {', '.join(sorted(ESTADOS_COMERCIALES))}",
                400
            )
    else:
        estado_clean = None

    p_min = _validar_precio(precio_min, "precio_min") if precio_min is not None else None
    p_max = _validar_precio(precio_max, "precio_max") if precio_max is not None else None
    if p_min is not None and p_max is not None and p_min > p_max:
        raise ComercializacionError("precio_min no puede ser mayor que precio_max.", 400)

    page = int(getattr(page, "default", page) or 1)
    limit = int(getattr(limit, "default", limit) or 20)
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 20

    kwargs_repo = dict(
        id_empresa=id_empresa,
        id_obra=id_obra,
        estado_comercial=estado_clean,
        publicado=publicado,
        tipo_unidad=tipo_unidad,
        solo_disponibles=solo_disponibles,
        q=q,
        page=page,
        limit=limit
    )
    if p_min is not None:
        kwargs_repo["precio_min"] = p_min
    if p_max is not None:
        kwargs_repo["precio_max"] = p_max

    unidades, total = comercializacion_repos.listar_unidades_comercializacion(**kwargs_repo)

    return {
        "data": unidades,
        "total": total,
        "page": page,
        "limit": limit
    }


def obtener_detalle_unidad(token: dict, id_unidad: int, id_empresa_solicitada: Optional[int] = None) -> Dict:
    """Obtiene la ficha técnica y comercial completa de una unidad."""
    id_empresa = _resolver_empresa(token, id_empresa_solicitada)
    if not id_empresa:
        raise ComercializacionError("Empresa no identificada.", 400)

    unidad = comercializacion_repos.obtener_unidad_comercial(id_unidad=id_unidad, id_empresa=id_empresa)
    if not unidad:
        raise ComercializacionError(f"La unidad con ID {id_unidad} no existe o no pertenece a su empresa autorizada.", 404)

    return unidad


def consultar_disponibilidad_unidad(token: dict, id_unidad: int, id_empresa_solicitada: Optional[int] = None) -> Dict:
    """Consulta el estado comercial, disponibilidad efectiva y transiciones permitidas (HU145)."""
    unidad = obtener_detalle_unidad(token, id_unidad, id_empresa_solicitada)
    estado_actual = unidad.get("estado_comercial") or "DISPONIBLE"
    asoc = unidad.get("asociacion_crm")
    bloqueada_crm = bool(asoc and asoc.get("estado_asociacion") in ("RESERVADO", "VENDIDO", "ENTREGADO"))
    disponible_efectiva = (estado_actual == "DISPONIBLE") and not bloqueada_crm

    return {
        "id_unidad": unidad["id_unidad"],
        "codigo": unidad["codigo"],
        "estado_constructivo": unidad.get("estado_constructivo"),
        "estado_comercial": estado_actual,
        "publicado_comercial": unidad.get("publicado_comercial", False),
        "disponible_efectiva": disponible_efectiva,
        "bloqueada_por_crm": bloqueada_crm,
        "asociacion_crm": asoc,
        "transiciones_permitidas": sorted(TRANSICIONES_COMERCIALES.get(estado_actual, set())),
    }


def obtener_resumen(token: dict, id_obra: Optional[int] = None, id_empresa_solicitada: Optional[int] = None) -> Dict:
    """Métricas y KPIs comerciales resumidos del catálogo inmobiliario (HU145)."""
    id_empresa = _resolver_empresa(token, id_empresa_solicitada)
    if not id_empresa:
        raise ComercializacionError("Empresa no identificada.", 400)

    return comercializacion_repos.obtener_resumen_comercial(id_empresa=id_empresa, id_obra=id_obra)


# ─────────────────────────────────────────────────────────────────────────────
# HU143: PUBLICAR Y ACTUALIZAR UNIDADES + FOTOGRAFÍAS
# ─────────────────────────────────────────────────────────────────────────────
def actualizar_comercializacion(
    token: dict,
    id_unidad: int,
    datos: dict,
    id_empresa_solicitada: Optional[int] = None,
    ip: str = "unknown"
) -> Dict:
    """
    Actualiza atributos comerciales (precio, publicación, estado comercial, descripción).
    NO modifica el estado constructivo (físico) de la unidad.
    Registra trazabilidad en el historial comercial y bitácora.
    """
    if not isinstance(datos, dict):
        raise ComercializacionError("El cuerpo de la solicitud debe ser un objeto JSON válido.", 400)

    if "estado" in datos or "estado_constructivo" in datos:
        raise ComercializacionError(
            "No está permitido modificar el estado constructivo de la unidad desde el módulo de comercialización.",
            400
        )

    id_empresa = _resolver_empresa(token, id_empresa_solicitada)
    if not id_empresa:
        raise ComercializacionError("Empresa no identificada.", 400)

    unidad_actual = comercializacion_repos.obtener_unidad_comercial(id_unidad=id_unidad, id_empresa=id_empresa)
    if not unidad_actual:
        raise ComercializacionError(f"La unidad con ID {id_unidad} no existe o no pertenece a su empresa autorizada.", 404)

    estado_ant = unidad_actual.get("estado_comercial") or "DISPONIBLE"
    precio_ant = unidad_actual.get("precio_venta")
    moneda_ant = unidad_actual.get("moneda_comercial") or "BOB"
    pub_ant = bool(unidad_actual.get("publicado_comercial", False))
    desc_ant = unidad_actual.get("descripcion_comercial")

    publicado_comercial = datos.get("publicado_comercial")
    if publicado_comercial is not None:
        publicado_comercial = bool(publicado_comercial)

    actualizar_precio = "precio_venta" in datos
    precio_venta = None
    if actualizar_precio:
        precio_venta = _validar_precio(datos.get("precio_venta"), "precio_venta", permitir_nulo=True)

    moneda_comercial = datos.get("moneda_comercial")
    if moneda_comercial is not None:
        moneda_clean = str(moneda_comercial).strip().upper()
        if moneda_clean not in MONEDAS_VALIDAS:
            raise ComercializacionError(
                f"Moneda comercial '{moneda_comercial}' inválida. Válidas: {', '.join(sorted(MONEDAS_VALIDAS))}",
                400
            )
        moneda_comercial = moneda_clean

    actualizar_descripcion = "descripcion_comercial" in datos
    descripcion_comercial = datos.get("descripcion_comercial")
    if descripcion_comercial is not None:
        descripcion_comercial = str(descripcion_comercial).strip()

    estado_comercial = datos.get("estado_comercial")
    if estado_comercial is not None:
        estado_clean = str(estado_comercial).strip().upper()
        if estado_clean not in ESTADOS_COMERCIALES:
            raise ComercializacionError(
                f"Estado comercial inválido '{estado_comercial}'. Válidos: {', '.join(sorted(ESTADOS_COMERCIALES))}",
                400
            )
        _validar_transicion_estado_directa(unidad_actual, estado_ant, estado_clean)
        estado_comercial = estado_clean

    # Construir eventos de historial comercial
    usuario_id = token.get("nro_usuario") or token.get("id_usuario")
    estado_efectivo = estado_comercial or estado_ant
    precio_efectivo = precio_venta if actualizar_precio else precio_ant
    moneda_efectiva = moneda_comercial or moneda_ant
    eventos_historial: List[Dict] = []

    if publicado_comercial is not None and publicado_comercial != pub_ant:
        tipo_ev = "PUBLICACION" if publicado_comercial else "DESPUBLICACION"
        accion_txt = "publicada en el catálogo comercial" if publicado_comercial else "retirada de publicación comercial"
        eventos_historial.append({
            "tipo_evento": tipo_ev,
            "estado_anterior": estado_ant,
            "estado_nuevo": estado_efectivo,
            "precio_venta": precio_efectivo,
            "observacion": f"Unidad {unidad_actual.get('codigo')} {accion_txt}.",
            "id_usuario": usuario_id,
        })

    if (actualizar_precio and precio_venta != precio_ant) or (moneda_comercial and moneda_comercial != moneda_ant):
        eventos_historial.append({
            "tipo_evento": "ACTUALIZACION_PRECIO",
            "estado_anterior": estado_ant,
            "estado_nuevo": estado_efectivo,
            "precio_venta": precio_efectivo,
            "observacion": f"Actualización de precio de venta a {precio_efectivo} {moneda_efectiva}",
            "id_usuario": usuario_id,
        })

    if estado_comercial and estado_comercial != estado_ant:
        eventos_historial.append({
            "tipo_evento": "CAMBIO_ESTADO",
            "estado_anterior": estado_ant,
            "estado_nuevo": estado_comercial,
            "precio_venta": precio_efectivo,
            "observacion": datos.get("observacion") or f"Cambio de estado comercial de {estado_ant} a {estado_comercial}",
            "id_usuario": usuario_id,
        })

    if actualizar_descripcion and descripcion_comercial != desc_ant and not eventos_historial:
        eventos_historial.append({
            "tipo_evento": "ACTUALIZACION_COMERCIAL",
            "estado_anterior": estado_ant,
            "estado_nuevo": estado_efectivo,
            "precio_venta": precio_efectivo,
            "observacion": "Actualización de descripción e información comercial de la unidad.",
            "id_usuario": usuario_id,
        })

    comercializacion_repos.actualizar_unidad_comercial(
        id_unidad=id_unidad,
        id_empresa=id_empresa,
        publicado_comercial=publicado_comercial,
        precio_venta=precio_venta,
        actualizar_precio=actualizar_precio,
        moneda_comercial=moneda_comercial,
        descripcion_comercial=descripcion_comercial,
        actualizar_descripcion=actualizar_descripcion,
        estado_comercial=estado_comercial,
        eventos_historial=eventos_historial
    )

    _log_bitacora(
        token=token,
        accion="MODIFICAR_UNIDAD_COMERCIAL",
        descripcion=f"Actualización comercial de unidad {unidad_actual.get('codigo')} (ID {id_unidad})",
        ip=ip
    )

    return comercializacion_repos.obtener_unidad_comercial(id_unidad=id_unidad, id_empresa=id_empresa)


def cambiar_publicacion_unidad(
    token: dict,
    id_unidad: int,
    publicado: bool,
    id_empresa_solicitada: Optional[int] = None,
    ip: str = "unknown"
) -> Dict:
    """Publica o despublica comercialmente una unidad inmobiliaria (HU143)."""
    if publicado is None:
        raise ComercializacionError("Debe especificar el valor booleano 'publicado_comercial' o 'publicado'.", 400)
    return actualizar_comercializacion(
        token=token,
        id_unidad=id_unidad,
        datos={"publicado_comercial": bool(publicado)},
        id_empresa_solicitada=id_empresa_solicitada,
        ip=ip
    )


def listar_fotografias(token: dict, id_unidad: int, id_empresa_solicitada: Optional[int] = None) -> Dict:
    """Lista las fotografías comerciales de una unidad (HU143)."""
    id_empresa = _resolver_empresa(token, id_empresa_solicitada)
    if not id_empresa:
        raise ComercializacionError("Empresa no identificada.", 400)

    if not comercializacion_repos.verificar_pertenencia_unidad_empresa(id_unidad, id_empresa):
        raise ComercializacionError(f"La unidad con ID {id_unidad} no existe o no pertenece a su empresa autorizada.", 404)

    fotos = comercializacion_repos.listar_fotografias_unidad(id_unidad=id_unidad, id_empresa=id_empresa)
    return {
        "id_unidad": id_unidad,
        "fotografias": fotos,
        "total": len(fotos)
    }


async def subir_fotografia(
    token: dict,
    id_unidad: int,
    archivo: UploadFile,
    es_principal: bool = False,
    orden: int = 1,
    id_empresa_solicitada: Optional[int] = None,
    ip: str = "unknown"
) -> Dict:
    """
    Valida y almacena una fotografía para la unidad (HU143):
    - Valida pertenencia a empresa.
    - Sanitiza nombre contra Path Traversal.
    - Valida extensión, tipo MIME, magic bytes reales y tamaño máximo (10 MB).
    - Registra en BD y en historial comercial atómicamente.
    """
    id_empresa = _resolver_empresa(token, id_empresa_solicitada)
    if not id_empresa:
        raise ComercializacionError("Empresa no identificada.", 400)

    unidad = comercializacion_repos.obtener_unidad_comercial(id_unidad=id_unidad, id_empresa=id_empresa)
    if not unidad:
        raise ComercializacionError(f"La unidad con ID {id_unidad} no existe o no pertenece a su empresa autorizada.", 404)

    if not archivo or not archivo.filename:
        raise ComercializacionError("Debe adjuntar un archivo de imagen válido.", 400)

    nombre_limpio = _sanitizar_nombre_archivo(archivo.filename)
    ext = Path(nombre_limpio).suffix.lower()
    if ext not in EXTENSIONES_FOTO_VALIDAS:
        raise ComercializacionError(
            f"Extensión de archivo '{ext}' no permitida. Solo se admiten: {', '.join(sorted(EXTENSIONES_FOTO_VALIDAS))}",
            400
        )

    content_type = (archivo.content_type or "").lower().strip()
    if content_type and content_type not in MIMES_FOTO_VALIDOS and content_type != "application/octet-stream":
        raise ComercializacionError(f"Tipo MIME '{content_type}' no permitido para fotografías.", 400)

    contenido = await archivo.read()
    if not contenido:
        raise ComercializacionError("El archivo de imagen está vacío.", 400)

    if len(contenido) > MAX_FOTO_BYTES:
        raise ComercializacionError("La fotografía supera el tamaño máximo permitido de 10 MB.", 400)

    mime_detectado = _detectar_mime_real(contenido)
    if not mime_detectado:
        raise ComercializacionError("El contenido binario no corresponde a una imagen JPEG, PNG o WEBP válida.", 400)

    base_dir = _directorio_base_uploads()
    carpeta_unidad = (base_dir / f"empresa_{id_empresa}" / f"unidad_{id_unidad}").resolve()
    _verificar_ruta_segura(carpeta_unidad, base_dir)
    carpeta_unidad.mkdir(parents=True, exist_ok=True)

    nombre_fisico = f"{uuid.uuid4().hex}{ext}"
    ruta_fisica = _verificar_ruta_segura(carpeta_unidad / nombre_fisico, base_dir)
    ruta_relativa = f"uploads/comercializacion/empresa_{id_empresa}/unidad_{id_unidad}/{nombre_fisico}"

    ruta_fisica.write_bytes(contenido)
    try:
        usuario_id = token.get("nro_usuario") or token.get("id_usuario")
        foto_creada = comercializacion_repos.crear_fotografia_unidad_transaccional(
            id_unidad=id_unidad,
            id_empresa=id_empresa,
            ruta_archivo=ruta_relativa,
            nombre_archivo=nombre_limpio,
            tipo_mime=mime_detectado,
            tamano_bytes=len(contenido),
            es_principal=bool(es_principal),
            orden=max(1, int(orden or 1)),
            id_usuario=usuario_id,
            estado_actual=unidad.get("estado_comercial") or "DISPONIBLE",
            precio_actual=unidad.get("precio_venta")
        )
    except Exception:
        if ruta_fisica.exists():
            try:
                ruta_fisica.unlink()
            except Exception:
                pass
        raise

    _log_bitacora(
        token=token,
        accion="SUBIR_FOTOGRAFIA_UNIDAD",
        descripcion=f"Fotografía '{nombre_limpio}' agregada a unidad {unidad.get('codigo')} (ID {id_unidad})",
        ip=ip
    )
    return foto_creada


def marcar_fotografia_principal(
    token: dict,
    id_unidad: int,
    id_fotografia: int,
    id_empresa_solicitada: Optional[int] = None,
    ip: str = "unknown"
) -> Dict:
    """Marca una fotografía existente de la unidad como principal (HU143)."""
    id_empresa = _resolver_empresa(token, id_empresa_solicitada)
    if not id_empresa:
        raise ComercializacionError("Empresa no identificada.", 400)

    usuario_id = token.get("nro_usuario") or token.get("id_usuario")
    resultado = comercializacion_repos.marcar_fotografia_principal_transaccional(
        id_fotografia=id_fotografia,
        id_unidad=id_unidad,
        id_empresa=id_empresa,
        id_usuario=usuario_id
    )
    if not resultado:
        raise ComercializacionError("La fotografía o la unidad no existen o no pertenecen a su empresa autorizada.", 404)

    _log_bitacora(
        token=token,
        accion="MARCAR_FOTO_PRINCIPAL_UNIDAD",
        descripcion=f"Fotografía ID {id_fotografia} marcada como principal en unidad ID {id_unidad}",
        ip=ip
    )
    return resultado


def eliminar_fotografia(
    token: dict,
    id_unidad: int,
    id_fotografia: int,
    id_empresa_solicitada: Optional[int] = None,
    ip: str = "unknown"
) -> Dict:
    """Elimina una fotografía de la unidad validando pertenencia a empresa y ruta segura (HU143)."""
    id_empresa = _resolver_empresa(token, id_empresa_solicitada)
    if not id_empresa:
        raise ComercializacionError("Empresa no identificada.", 400)

    usuario_id = token.get("nro_usuario") or token.get("id_usuario")
    eliminada = comercializacion_repos.eliminar_fotografia_unidad_transaccional(
        id_fotografia=id_fotografia,
        id_unidad=id_unidad,
        id_empresa=id_empresa,
        id_usuario=usuario_id
    )
    if not eliminada:
        raise ComercializacionError("La fotografía o la unidad no existen o no pertenecen a su empresa autorizada.", 404)

    # Eliminar archivo físico solo si su ruta resuelta está dentro del directorio seguro
    ruta_rel = str(eliminada.get("ruta_archivo") or "")
    if ruta_rel and ".." not in ruta_rel:
        try:
            backend_dir = Path(__file__).resolve().parents[2]
            ruta_abs = _verificar_ruta_segura(backend_dir / ruta_rel, _directorio_base_uploads())
            if ruta_abs.exists() and ruta_abs.is_file():
                ruta_abs.unlink()
        except Exception:
            pass

    _log_bitacora(
        token=token,
        accion="ELIMINAR_FOTOGRAFIA_UNIDAD",
        descripcion=f"Fotografía ID {id_fotografia} eliminada de unidad ID {id_unidad}",
        ip=ip
    )
    return {
        "eliminado": True,
        "id_fotografia": id_fotografia,
        "id_unidad": id_unidad,
        "nombre_archivo": eliminada.get("nombre_archivo")
    }


def obtener_archivo_fotografia(
    token: dict,
    id_unidad: int,
    id_fotografia: int,
    id_empresa_solicitada: Optional[int] = None
) -> Dict:
    """Resuelve y valida la ruta segura en disco de una fotografía verificando tenant (HU143)."""
    id_empresa = _resolver_empresa(token, id_empresa_solicitada)
    if not id_empresa:
        raise ComercializacionError("Empresa no identificada.", 400)

    foto = comercializacion_repos.obtener_fotografia_unidad(
        id_fotografia=id_fotografia,
        id_unidad=id_unidad,
        id_empresa=id_empresa
    )
    if not foto:
        raise ComercializacionError("La fotografía no existe o no pertenece a su empresa autorizada.", 404)

    ruta_rel = str(foto.get("ruta_archivo") or "")
    if not ruta_rel or ".." in ruta_rel:
        raise ComercializacionError("Ruta de fotografía inválida.", 403)

    backend_dir = Path(__file__).resolve().parents[2]
    ruta_segura = _verificar_ruta_segura(backend_dir / ruta_rel, _directorio_base_uploads())
    if not ruta_segura.exists() or not ruta_segura.is_file():
        raise ComercializacionError("El archivo físico de la fotografía no se encuentra en el servidor.", 404)

    return {
        "ruta": str(ruta_segura),
        "tipo_mime": foto.get("tipo_mime") or "image/jpeg",
        "nombre_archivo": _sanitizar_nombre_archivo(foto.get("nombre_archivo") or ruta_segura.name),
    }


# ─────────────────────────────────────────────────────────────────────────────
# HU144: REGISTRAR RESERVA DE UNIDAD INMOBILIARIA
# ─────────────────────────────────────────────────────────────────────────────
def registrar_reserva(
    token: dict,
    id_unidad: int,
    datos: dict,
    id_empresa_solicitada: Optional[int] = None,
    ip: str = "unknown"
) -> Dict:
    """
    Registra atómicamente una reserva para un cliente existente de la misma empresa:
    - Valida tenant de unidad y cliente (impide cliente de empresa A con unidad de empresa B).
    - Impide doble reserva o reserva de unidad vendida/no disponible.
    - Guarda monto_reserva, fecha_vencimiento_reserva e id_usuario_registro en t_crm_cliente_unidad.
    - Cambia estado_comercial a RESERVADA y registra historial comercial en una transacción.
    """
    if not isinstance(datos, dict):
        raise ComercializacionError("Datos de reserva inválidos.", 400)

    id_empresa = _resolver_empresa(token, id_empresa_solicitada)
    if not id_empresa:
        raise ComercializacionError("Empresa no identificada.", 400)

    id_cliente_raw = datos.get("id_cliente")
    if id_cliente_raw is None or isinstance(id_cliente_raw, bool):
        raise ComercializacionError("El campo 'id_cliente' es obligatorio para registrar una reserva.", 400)
    try:
        id_cliente = int(id_cliente_raw)
    except (ValueError, TypeError):
        raise ComercializacionError("El campo 'id_cliente' debe ser un entero válido.", 400)

    monto_reserva = _validar_precio(
        datos.get("monto_reserva", 0),
        campo="monto_reserva",
        permitir_nulo=False
    )
    monto_pactado = _validar_precio(
        datos.get("monto_pactado"),
        campo="monto_pactado",
        permitir_nulo=True
    )
    fecha_vencimiento = _validar_fecha_vencimiento(
        datos.get("fecha_vencimiento_reserva") or datos.get("fecha_vencimiento")
    )
    observaciones = str(datos.get("observaciones") or datos.get("observacion") or "").strip() or None
    usuario_id = token.get("nro_usuario") or token.get("id_usuario")

    try:
        resultado = comercializacion_repos.registrar_reserva_transaccional(
            id_unidad=id_unidad,
            id_empresa=id_empresa,
            id_cliente=id_cliente,
            monto_reserva=monto_reserva,
            monto_pactado=monto_pactado,
            fecha_vencimiento_reserva=fecha_vencimiento,
            observaciones=observaciones,
            id_usuario=usuario_id
        )
    except Exception as exc:
        _mapear_excepcion_repo(exc)

    _log_bitacora(
        token=token,
        accion="REGISTRAR_RESERVA_UNIDAD",
        descripcion=(
            f"Reserva registrada en unidad {resultado.get('codigo_unidad')} (ID {id_unidad}) "
            f"para cliente ID {id_cliente} por monto {monto_reserva}"
        ),
        ip=ip
    )
    return resultado


# ─────────────────────────────────────────────────────────────────────────────
# HU145: CONTROL DE DISPONIBILIDAD, TRANSICIONES, CANCELACIÓN Y VENTA
# ─────────────────────────────────────────────────────────────────────────────
def _validar_transicion_estado_directa(unidad_actual: Dict, estado_ant: str, estado_nuevo: str):
    """Valida que un cambio de estado mediante PATCH sea coherente con la máquina de estados y CRM."""
    if estado_nuevo == estado_ant:
        return

    if estado_ant == "VENDIDA":
        raise ComercializacionError(
            "Una unidad con venta confirmada (VENDIDA) no puede revertirse a otro estado comercial.",
            400
        )

    permitidos = TRANSICIONES_COMERCIALES.get(estado_ant, set())
    if estado_nuevo not in permitidos:
        raise ComercializacionError(
            f"Transición de estado comercial inválida de '{estado_ant}' a '{estado_nuevo}'.",
            400
        )

    asoc = unidad_actual.get("asociacion_crm")
    estado_asoc = asoc.get("estado_asociacion") if asoc else None

    if estado_nuevo == "DISPONIBLE" and estado_asoc in ("RESERVADO", "VENDIDO", "ENTREGADO"):
        raise ComercializacionError(
            f"No se puede marcar la unidad como DISPONIBLE porque tiene una asociación activa en CRM ({estado_asoc}). "
            "Utilice la operación de cancelar/liberar reserva.",
            400
        )

    if estado_nuevo == "RESERVADA" and estado_asoc != "RESERVADO":
        raise ComercializacionError(
            "Para pasar una unidad a RESERVADA debe registrar una reserva vinculada a un cliente de la empresa.",
            400
        )

    if estado_nuevo == "VENDIDA" and estado_asoc not in ("RESERVADO", "VENDIDO"):
        raise ComercializacionError(
            "Para pasar una unidad a VENDIDA debe confirmar la venta vinculada a una reserva o cliente de la empresa.",
            400
        )


def cancelar_reserva(
    token: dict,
    id_unidad: int,
    datos: Optional[dict] = None,
    id_empresa_solicitada: Optional[int] = None,
    ip: str = "unknown"
) -> Dict:
    """
    Cancela/libera la reserva activa de una unidad (HU145):
    - Transiciona estado_comercial de RESERVADA -> DISPONIBLE.
    - Sincroniza t_crm_cliente_unidad a estado 'CANCELADO'.
    - Registra evento 'CANCELACION' en t_unidad_historial_comercial.
    """
    id_empresa = _resolver_empresa(token, id_empresa_solicitada)
    if not id_empresa:
        raise ComercializacionError("Empresa no identificada.", 400)

    payload = datos if isinstance(datos, dict) else {}
    motivo = str(payload.get("motivo") or payload.get("observaciones") or payload.get("observacion") or "").strip() or None
    usuario_id = token.get("nro_usuario") or token.get("id_usuario")

    try:
        resultado = comercializacion_repos.cancelar_reserva_transaccional(
            id_unidad=id_unidad,
            id_empresa=id_empresa,
            motivo=motivo,
            id_usuario=usuario_id
        )
    except Exception as exc:
        _mapear_excepcion_repo(exc)

    _log_bitacora(
        token=token,
        accion="CANCELAR_RESERVA_UNIDAD",
        descripcion=f"Reserva cancelada y unidad {resultado.get('codigo_unidad')} (ID {id_unidad}) liberada a DISPONIBLE",
        ip=ip
    )
    return resultado


def confirmar_venta(
    token: dict,
    id_unidad: int,
    datos: Optional[dict] = None,
    id_empresa_solicitada: Optional[int] = None,
    ip: str = "unknown"
) -> Dict:
    """
    Confirma la venta de una unidad inmobiliaria (HU145):
    - Transiciona estado_comercial a VENDIDA.
    - Sincroniza t_crm_cliente_unidad a estado 'VENDIDO'.
    - Registra evento 'VENTA' en t_unidad_historial_comercial.
    """
    id_empresa = _resolver_empresa(token, id_empresa_solicitada)
    if not id_empresa:
        raise ComercializacionError("Empresa no identificada.", 400)

    payload = datos if isinstance(datos, dict) else {}
    id_cliente_raw = payload.get("id_cliente")
    id_cliente = None
    if id_cliente_raw is not None:
        if isinstance(id_cliente_raw, bool):
            raise ComercializacionError("id_cliente debe ser un entero válido.", 400)
        try:
            id_cliente = int(id_cliente_raw)
        except (ValueError, TypeError):
            raise ComercializacionError("id_cliente debe ser un entero válido.", 400)

    monto_pactado = _validar_precio(payload.get("monto_pactado"), "monto_pactado", permitir_nulo=True)
    observaciones = str(payload.get("observaciones") or payload.get("observacion") or "").strip() or None
    usuario_id = token.get("nro_usuario") or token.get("id_usuario")

    try:
        resultado = comercializacion_repos.confirmar_venta_transaccional(
            id_unidad=id_unidad,
            id_empresa=id_empresa,
            id_cliente=id_cliente,
            monto_pactado=monto_pactado,
            observaciones=observaciones,
            id_usuario=usuario_id
        )
    except Exception as exc:
        _mapear_excepcion_repo(exc)

    _log_bitacora(
        token=token,
        accion="CONFIRMAR_VENTA_UNIDAD",
        descripcion=f"Venta confirmada para unidad {resultado.get('codigo_unidad')} (ID {id_unidad})",
        ip=ip
    )
    return resultado


def cambiar_estado_comercial(
    token: dict,
    id_unidad: int,
    datos: dict,
    id_empresa_solicitada: Optional[int] = None,
    ip: str = "unknown"
) -> Dict:
    """
    Controlador unificado de cambio de estado comercial (HU145):
    - Soporta transiciones coherentes entre DISPONIBLE, RESERVADA, VENDIDA y NO_DISPONIBLE.
    - Si se solicita pasar de RESERVADA a DISPONIBLE con flag cancelar_reserva=True, ejecuta liberación atómica.
    - Si se solicita pasar a VENDIDA, ejecuta confirmación de venta sincronizada con CRM.
    """
    if not isinstance(datos, dict) or not datos.get("estado_comercial"):
        raise ComercializacionError("Debe especificar el nuevo 'estado_comercial'.", 400)

    nuevo_estado = str(datos.get("estado_comercial")).strip().upper()
    if nuevo_estado not in ESTADOS_COMERCIALES:
        raise ComercializacionError(
            f"Estado comercial inválido '{nuevo_estado}'. Válidos: {', '.join(sorted(ESTADOS_COMERCIALES))}",
            400
        )

    if nuevo_estado == "RESERVADA":
        return registrar_reserva(
            token=token,
            id_unidad=id_unidad,
            datos=datos,
            id_empresa_solicitada=id_empresa_solicitada,
            ip=ip
        )

    if nuevo_estado == "VENDIDA":
        return confirmar_venta(
            token=token,
            id_unidad=id_unidad,
            datos=datos,
            id_empresa_solicitada=id_empresa_solicitada,
            ip=ip
        )

    if nuevo_estado == "DISPONIBLE" and datos.get("cancelar_reserva"):
        return cancelar_reserva(
            token=token,
            id_unidad=id_unidad,
            datos=datos,
            id_empresa_solicitada=id_empresa_solicitada,
            ip=ip
        )

    return actualizar_comercializacion(
        token=token,
        id_unidad=id_unidad,
        datos={
            "estado_comercial": nuevo_estado,
            "observacion": datos.get("observacion") or datos.get("observaciones"),
        },
        id_empresa_solicitada=id_empresa_solicitada,
        ip=ip
    )


# ─────────────────────────────────────────────────────────────────────────────
# HU146: CONSULTAR HISTORIAL COMERCIAL DE UNIDADES
# ─────────────────────────────────────────────────────────────────────────────
def listar_historial(
    token: dict,
    id_unidad: int,
    tipo_evento: Optional[str] = None,
    limit: int = 100,
    id_empresa_solicitada: Optional[int] = None
) -> Dict:
    """Consulta cronológicamente el historial comercial inmutable de la unidad (HU146)."""
    id_empresa = _resolver_empresa(token, id_empresa_solicitada)
    if not id_empresa:
        raise ComercializacionError("Empresa no identificada.", 400)

    if not comercializacion_repos.verificar_pertenencia_unidad_empresa(id_unidad, id_empresa):
        raise ComercializacionError(f"La unidad con ID {id_unidad} no existe o no pertenece a su empresa autorizada.", 404)

    if tipo_evento and tipo_evento.strip():
        ev_clean = tipo_evento.strip().upper()
        if ev_clean not in TIPOS_EVENTO_HISTORIAL:
            raise ComercializacionError(
                f"Tipo de evento '{tipo_evento}' inválido. Válidos: {', '.join(sorted(TIPOS_EVENTO_HISTORIAL))}",
                400
            )
    else:
        ev_clean = None

    limit_val = getattr(limit, "default", limit)
    limit_safe = min(max(1, int(limit_val or 100)), 500)
    kwargs_hist = dict(id_unidad=id_unidad, id_empresa=id_empresa, limit=limit_safe)
    if ev_clean:
        kwargs_hist["tipo_evento"] = ev_clean

    eventos = comercializacion_repos.listar_historial_unidad(**kwargs_hist)
    return {
        "id_unidad": id_unidad,
        "historial": eventos,
        "total": len(eventos)
    }
