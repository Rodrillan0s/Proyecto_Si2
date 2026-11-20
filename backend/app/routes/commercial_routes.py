"""
Rutas públicas y multi-tenant para el Asistente Comercial Inteligente (CU34: HUs 147, 148, 149, 150).
"""
import threading
import time
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from app.repos import commercial_repos
from app.services.ai.providers import ProviderError
from app.services.commercial import commercial_assistant_service as assistant_service
from app.services.commercial import lead_capture_service as lead_service
from app.services.commercial.contracts import (
    CommercialChatRequest,
    CostEstimationRequest,
    LeadContactRequest,
)
from app.utils.security import decode_access_token, es_admin_sistema

router = APIRouter(prefix='/api/public/comercial', tags=['Asistente Comercial IA (CU34)'])

_RATE_LOCK = threading.Lock()
_RATE_BUCKETS: dict[tuple[str, str], list[float]] = {}
RATE_LIMITS = {
    'chat': (30, 600),      # 30 mensajes cada 10 minutos por IP
    'plano': (8, 600),      # 8 planos cada 10 minutos por IP
    'contacto': (10, 600),  # 10 solicitudes de contacto cada 10 minutos por IP
}


def reset_rate_limits():
    with _RATE_LOCK:
        _RATE_BUCKETS.clear()


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else 'unknown'


def _enforce_rate_limit(request: Request, action: str):
    limit, window_sec = RATE_LIMITS.get(action, (30, 600))
    ip = _client_ip(request)
    now = time.time()
    key = (ip, action)
    with _RATE_LOCK:
        timestamps = [t for t in _RATE_BUCKETS.get(key, []) if now - t < window_sec]
        if len(timestamps) >= limit:
            raise HTTPException(
                status_code=429,
                detail='Se alcanzó el límite temporal de consultas comerciales para esta sesión. Intente nuevamente en unos minutos.',
            )
        timestamps.append(now)
        _RATE_BUCKETS[key] = timestamps


def _resolver_y_autorizar_empresa(empresa_ref: str, request: Request) -> dict:
    """
    Resuelve la empresa constructora por ID o slug y, si el solicitante envía
    un JWT válido de empresa (ej. CLIENTE o ADMINISTRADOR_EMPRESA), verifica que
    no intente cruzar de tenant.
    """
    empresa = commercial_repos.resolver_empresa_comercial(empresa_ref)
    if not empresa:
        raise HTTPException(
            status_code=404,
            detail=f"La empresa o catálogo comercial '{empresa_ref}' no existe.",
        )

    auth_header = request.headers.get('Authorization') or ''
    if auth_header.lower().startswith('bearer '):
        raw_token = auth_header.split(' ', 1)[1].strip()
        if raw_token:
            decoded = decode_access_token(raw_token)
            if decoded.get('success'):
                payload = decoded.get('payload') or {}
                if not es_admin_sistema(payload):
                    token_emp = payload.get('id_empresa')
                    if token_emp is not None and int(token_emp) != int(empresa['id_empresa']):
                        raise HTTPException(
                            status_code=403,
                            detail='Su sesión autenticada pertenece a otra empresa y no puede operar sobre este catálogo.',
                        )

    return empresa


@router.get('/empresas')
def get_empresas_comerciales():
    """Lista las empresas constructoras disponibles para el portal de clientes potenciales."""
    return {
        'success': True,
        'data': commercial_repos.listar_empresas_comerciales(),
    }


@router.get('/{empresa_ref}/catalogo')
def get_catalogo_empresa(empresa_ref: str, request: Request):
    """Obtiene el catálogo inicial de unidades, modelos, estilos de acabado y sugerencias."""
    empresa = _resolver_y_autorizar_empresa(empresa_ref, request)
    try:
        data = assistant_service.obtener_catalogo_inicial_comercial(empresa['id_empresa'])
        return {'success': True, 'data': data}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post('/{empresa_ref}/chat')
def post_chat_comercial(
    empresa_ref: str,
    data: CommercialChatRequest,
    request: Request,
):
    """
    Endpoint principal de conversación comercial (CU34: HUs 147, 148, 149, 150 + costos).
    """
    _enforce_rate_limit(request, 'chat')
    empresa = _resolver_y_autorizar_empresa(empresa_ref, request)
    try:
        return assistant_service.procesar_consulta_comercial(
            id_empresa=empresa['id_empresa'],
            solicitud=data,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.post('/{empresa_ref}/estimar-costo')
def post_estimar_costo(
    empresa_ref: str,
    data: CostEstimationRequest,
    request: Request,
):
    """
    Calcula una estimación paramétrica determinista de costo por m², estilo de acabado y preferencias.
    """
    _enforce_rate_limit(request, 'chat')
    empresa = _resolver_y_autorizar_empresa(empresa_ref, request)
    try:
        return assistant_service.ejecutar_estimacion_directa(
            id_empresa=empresa['id_empresa'],
            req=data,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post('/{empresa_ref}/analizar-plano')
async def post_analizar_plano(
    empresa_ref: str,
    request: Request,
    archivo: UploadFile = File(...),
    mensaje: str = Form(''),
    presupuesto_max: float | None = Form(None),
    moneda: str = Form('BOB'),
    estilo_preferido: str | None = Form(None),
    conversacion_id: str | None = Form(None),
):
    """
    Recibe la imagen de un plano arquitectónico (PNG, JPEG, WebP), extrae ambientes y superficie
    con DeepSeek Vision, calcula su presupuesto por estilos y sugiere unidades similares del catálogo.
    """
    _enforce_rate_limit(request, 'plano')
    empresa = _resolver_y_autorizar_empresa(empresa_ref, request)
    content = await archivo.read()
    if not content:
        raise HTTPException(status_code=400, detail='El archivo de imagen enviado está vacío.')
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail='La imagen del plano supera el tamaño máximo de 10 MB.')

    try:
        return assistant_service.procesar_plano_comercial(
            id_empresa=empresa['id_empresa'],
            image_bytes=content,
            mensaje_cliente=mensaje,
            presupuesto_max=presupuesto_max,
            moneda=moneda,
            estilo_preferido=estilo_preferido,
            conversacion_id=conversacion_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.post('/{empresa_ref}/solicitar-contacto')
def post_solicitar_contacto(
    empresa_ref: str,
    data: LeadContactRequest,
    request: Request,
):
    """
    Registra directamente el interés del cliente potencial en el CRM de la empresa (HU150).
    """
    _enforce_rate_limit(request, 'contacto')
    empresa = _resolver_y_autorizar_empresa(empresa_ref, request)
    try:
        token_data = _extraer_token_opcional(request)
        id_usuario_sol = token_data.get('nro_usuario') if isinstance(token_data, dict) else None
        res = lead_service.registrar_solicitud_contacto(
            id_empresa=empresa['id_empresa'],
            solicitud=data,
            id_usuario_solicitante=id_usuario_sol,
        )
        return {
            'success': True,
            'empresa': empresa,
            'data': res,
        }
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

