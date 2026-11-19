from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from app.services import documentos_services
from app.utils.security import exigir_permiso


router = APIRouter(tags=["Documentación Técnica"])


def _ip(request):
    return request.client.host if request.client else "unknown"


def _raise(exc):
    raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.post("", status_code=201)
async def post_documento(
    request: Request,
    id_obra: int = Form(...),
    nombre: str = Form(...),
    tipo_documento: str = Form(...),
    descripcion: str = Form(default=""),
    contenido_documento: str = Form(...),
    observaciones: str = Form(default=""),
    archivo: UploadFile = File(...),
    token=Depends(exigir_permiso("Registrar_documentos_tecnicos"))
):
    try:
        data = {
            "id_obra": id_obra,
            "nombre": nombre,
            "tipo_documento": tipo_documento,
            "descripcion": descripcion,
            "contenido_documento": contenido_documento,
            "observaciones": observaciones
        }
        return await documentos_services.registrar(data, archivo, token, _ip(request))
    except documentos_services.DocumentoError as exc:
        _raise(exc)


@router.get("/obra/{id_obra}")
def get_documentos_obra(
    id_obra: int,
    token=Depends(exigir_permiso("Visualizar_documentos_tecnicos"))
):
    try:
        return documentos_services.listar(id_obra, token)
    except documentos_services.DocumentoError as exc:
        _raise(exc)


@router.get("/{id_documento}/historial")
def get_historial(
    id_documento: int,
    token=Depends(exigir_permiso("Visualizar_documentos_tecnicos"))
):
    try:
        return documentos_services.historial(id_documento, token)
    except documentos_services.DocumentoError as exc:
        _raise(exc)


@router.post("/{id_documento}/versiones", status_code=201)
async def post_version(
    id_documento: int,
    request: Request,
    contenido_documento: str = Form(...),
    observaciones: str = Form(default=""),
    archivo: UploadFile = File(...),
    token=Depends(exigir_permiso("Modificar_documentos_tecnicos"))
):
    try:
        data = {
            "contenido_documento": contenido_documento,
            "observaciones": observaciones
        }
        return await documentos_services.crear_version(
            id_documento,
            data,
            archivo,
            token,
            _ip(request)
        )
    except documentos_services.DocumentoError as exc:
        _raise(exc)


@router.get("/{id_documento}/versiones/{id_version}/descargar")
def get_descargar_version(
    id_documento: int,
    id_version: int,
    token=Depends(exigir_permiso("Visualizar_documentos_tecnicos"))
):
    try:
        archivo = documentos_services.obtener_archivo(
            id_documento,
            id_version,
            token
        )
        return FileResponse(
            path=archivo["ruta"],
            media_type=archivo["tipo_archivo"],
            filename=archivo["nombre_archivo"]
        )
    except documentos_services.DocumentoError as exc:
        _raise(exc)


@router.get("/{id_documento}")
def get_documento(
    id_documento: int,
    token=Depends(exigir_permiso("Visualizar_documentos_tecnicos"))
):
    try:
        return documentos_services.detalle(id_documento, token)
    except documentos_services.DocumentoError as exc:
        _raise(exc)


@router.patch("/{id_documento}/estado")
def patch_estado(
    id_documento: int,
    request: Request,
    data: dict = Body(...),
    token=Depends(exigir_permiso("Modificar_documentos_tecnicos"))
):
    try:
        return documentos_services.cambiar_estado(
            id_documento,
            data.get("estado"),
            token,
            _ip(request)
        )
    except documentos_services.DocumentoError as exc:
        _raise(exc)