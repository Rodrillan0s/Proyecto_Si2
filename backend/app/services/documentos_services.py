import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.repos import documentos_repos, obra_repos, bitacora_repos


MAX_PDF_SIZE = 15 * 1024 * 1024
EXTENSIONES_PERMITIDAS = {".pdf"}


class DocumentoError(ValueError):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


def _empresa_obra(id_obra, token):
    es_admin = token.get("nombre_rol") == "ADMINISTRADOR"
    id_empresa = token.get("id_empresa")

    if not es_admin and not id_empresa:
        raise DocumentoError("El token no identifica una empresa.", 403)

    obra = obra_repos.obtener_obra_detalle_sp(
        id_obra,
        None if es_admin else id_empresa
    )

    if not obra or not obra.get("success"):
        raise DocumentoError(
            "El proyecto no existe o no pertenece a su empresa.",
            404
        )

    empresa_obra = obra["data"].get("id_empresa")

    if not empresa_obra:
        raise DocumentoError("No se pudo identificar la empresa del proyecto.", 400)

    if not es_admin and str(empresa_obra) != str(id_empresa):
        raise DocumentoError("No tiene acceso a este proyecto.", 403)

    return empresa_obra


def _validar_texto(value, campo, obligatorio=True, maximo=None):
    value = str(value or "").strip()

    if obligatorio and not value:
        raise DocumentoError(f"{campo} es obligatorio.")

    if maximo and len(value) > maximo:
        raise DocumentoError(f"{campo} no puede superar los {maximo} caracteres.")

    return value or None


async def _guardar_pdf(archivo):
    if not archivo:
        raise DocumentoError("Debe adjuntar un archivo PDF.")

    extension = Path(archivo.filename or "").suffix.lower()

    if extension not in EXTENSIONES_PERMITIDAS:
        raise DocumentoError("Solo se permiten archivos PDF.")

    contenido = await archivo.read()

    if not contenido:
        raise DocumentoError("El archivo está vacío.")

    if len(contenido) > MAX_PDF_SIZE:
        raise DocumentoError("El archivo supera el límite de 15 MB.")

    if not contenido.startswith(b"%PDF-"):
        raise DocumentoError("El archivo adjunto no es un PDF válido.")

    nombre_guardado = f"{uuid.uuid4().hex}.pdf"

    # app/services/documentos_services.py -> raíz del backend
    backend_dir = Path(__file__).resolve().parents[2]
    carpeta = backend_dir / "uploads" / "documentos"
    carpeta.mkdir(parents=True, exist_ok=True)

    ruta = carpeta / nombre_guardado
    ruta.write_bytes(contenido)

    return {
        "contenido": contenido,
        "nombre_original": Path(archivo.filename).name,
        "nombre_guardado": nombre_guardado,
        "ruta": str(ruta),
        "ruta_relativa": f"uploads/documentos/{nombre_guardado}",
        "tamano": len(contenido)
    }


def _registrar_bitacora(token, accion, descripcion, ip):
    try:
        bitacora_repos.registrar_bitacora(
            id_usuario=token.get("nro_usuario"),
            modulo="DOCUMENTACION_TECNICA",
            accion=accion,
            descripcion=descripcion,
            ip=ip,
            estado="EXITOSO"
        )
    except Exception:
        # La bitácora no debe impedir que se complete una operación válida.
        pass


def _documento_autorizado(id_documento, token):
    documento = documentos_repos.obtener(id_documento)

    if not documento:
        raise DocumentoError("Documento no encontrado.", 404)

    _empresa_obra(documento["id_obra"], token)

    return documento


async def registrar(data, archivo, token, ip="unknown"):
    if not isinstance(data, dict):
        raise DocumentoError("Los datos del documento no son válidos.")

    try:
        id_obra = int(data.get("id_obra"))
    except (TypeError, ValueError):
        raise DocumentoError("El proyecto es obligatorio.")

    if id_obra <= 0:
        raise DocumentoError("El proyecto no es válido.")

    _empresa_obra(id_obra, token)

    nombre = _validar_texto(data.get("nombre"), "El nombre", maximo=150)
    descripcion = _validar_texto(
        data.get("descripcion"),
        "La descripción",
        obligatorio=False
    )
    tipo = _validar_texto(
        data.get("tipo_documento"),
        "El tipo de documento",
        maximo=50
    )
    contenido_documento = _validar_texto(
        data.get("contenido_documento"),
        "El contenido del documento"
    )

    pdf = await _guardar_pdf(archivo)
    id_documento = None

    try:
        id_documento = documentos_repos.crear_documento({
            "id_obra": id_obra,
            "nombre": nombre,
            "descripcion": descripcion,
            "tipo_documento": tipo
        })

        id_version = documentos_repos.crear_version({
            "id_documento": id_documento,
            "numero_version": 1,
            "contenido_documento": contenido_documento,
            "nombre_archivo": pdf["nombre_original"],
            "ruta_archivo": pdf["ruta_relativa"],
            "tipo_archivo": "application/pdf",
            "tamano_bytes": pdf["tamano"],
            "observaciones": data.get("observaciones"),
            "id_usuario": token.get("nro_usuario")
        })

    except Exception:
        try:
            os.remove(pdf["ruta"])
        except OSError:
            pass
        raise

    _registrar_bitacora(
        token,
        "REGISTRAR_DOCUMENTO_TECNICO",
        f"Documento {id_documento} registrado en el proyecto {id_obra}.",
        ip
    )

    return {
        "success": True,
        "message": "Documento técnico registrado exitosamente.",
        "data": {
            "id_documento": id_documento,
            "id_version": id_version,
            "version_actual": 1
        }
    }


def listar(id_obra, token):
    try:
        id_obra = int(id_obra)
    except (TypeError, ValueError):
        raise DocumentoError("El proyecto no es válido.")

    _empresa_obra(id_obra, token)

    return {
        "success": True,
        "data": documentos_repos.listar(id_obra)
    }


def detalle(id_documento, token):
    documento = _documento_autorizado(id_documento, token)

    return {
        "success": True,
        "data": documento
    }


async def crear_version(id_documento, data, archivo, token, ip="unknown"):
    documento = _documento_autorizado(id_documento, token)

    if documento["estado"] != "ACTIVO":
        raise DocumentoError("No se pueden agregar versiones a un documento inactivo.", 409)

    contenido_documento = _validar_texto(
        data.get("contenido_documento"),
        "El contenido del documento"
    )

    observaciones = _validar_texto(
        data.get("observaciones"),
        "Las observaciones",
        obligatorio=False
    )

    pdf = await _guardar_pdf(archivo)
    numero_version = int(documento["version_actual"] or 0) + 1

    try:
        id_version = documentos_repos.crear_version({
            "id_documento": id_documento,
            "numero_version": numero_version,
            "contenido_documento": contenido_documento,
            "nombre_archivo": pdf["nombre_original"],
            "ruta_archivo": pdf["ruta_relativa"],
            "tipo_archivo": "application/pdf",
            "tamano_bytes": pdf["tamano"],
            "observaciones": observaciones,
            "id_usuario": token.get("nro_usuario")
        })
    except Exception:
        try:
            os.remove(pdf["ruta"])
        except OSError:
            pass
        raise

    _registrar_bitacora(
        token,
        "REGISTRAR_VERSION_DOCUMENTO",
        f"Versión {numero_version} registrada para el documento {id_documento}.",
        ip
    )

    return {
        "success": True,
        "message": "Nueva versión registrada exitosamente.",
        "data": {
            "id_version": id_version,
            "id_documento": id_documento,
            "numero_version": numero_version
        }
    }


def historial(id_documento, token):
    documento = _documento_autorizado(id_documento, token)

    return {
        "success": True,
        "data": {
            "documento": documento,
            "versiones": documentos_repos.listar_versiones(id_documento)
        }
    }


def obtener_archivo(id_documento, id_version, token):
    _documento_autorizado(id_documento, token)

    version = documentos_repos.obtener_version(id_documento, id_version)

    if not version:
        raise DocumentoError("La versión solicitada no existe.", 404)

    ruta_relativa = version[3]
    backend_dir = Path(__file__).resolve().parents[2]
    carpeta_documentos = (backend_dir / "uploads" / "documentos").resolve()
    ruta = (backend_dir / ruta_relativa).resolve()

    # Evita que una ruta almacenada en BD permita salir de la carpeta de documentos.
    if carpeta_documentos not in ruta.parents or not ruta.is_file():
        raise DocumentoError("El archivo PDF no se encuentra almacenado.", 404)

    return {
        "ruta": str(ruta),
        "nombre_archivo": version[2],
        "tipo_archivo": version[4] or "application/pdf"
    }


def cambiar_estado(id_documento, estado, token, ip="unknown"):
    _documento_autorizado(id_documento, token)

    estado = str(estado or "").strip().upper()

    if estado not in ("ACTIVO", "INACTIVO"):
        raise DocumentoError("El estado indicado no es válido.")

    if not documentos_repos.cambiar_estado(id_documento, estado):
        raise DocumentoError("No se pudo actualizar el documento.", 404)

    _registrar_bitacora(
        token,
        "CAMBIAR_ESTADO_DOCUMENTO",
        f"Documento {id_documento} cambiado a {estado}.",
        ip
    )

    return {
        "success": True,
        "message": "Estado del documento actualizado exitosamente."
    }