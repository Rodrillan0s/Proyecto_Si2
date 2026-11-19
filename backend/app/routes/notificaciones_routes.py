from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException, Body
from app.classes.websocket_manager import manager
from app.utils.security import decode_access_token, verificar_token
from app.services import notificaciones_services

router = APIRouter(tags=["WebSockets Notificaciones"])


@router.websocket("/notificaciones")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    validation = decode_access_token(token)

    if not validation or (isinstance(validation, dict) and validation.get('success') is False):
        await websocket.close(code=1008)
        return

    await websocket.accept()

    payload = validation.get('payload') if isinstance(validation, dict) else None
    if not payload:
        payload = validation.get('data', validation) if isinstance(validation, dict) else validation

    try:
        nro_usuario = payload.get('nro_usuario')
    except Exception:
        nro_usuario = None

    if not nro_usuario:
        await websocket.close(code=1008)
        return

    manager.active_connections[int(nro_usuario)] = websocket

    try:
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        if int(nro_usuario) in manager.active_connections:
            del manager.active_connections[int(nro_usuario)]


@router.get('/historial')
def get_mis_notificaciones(token_data: dict = Depends(verificar_token)):
    """
    Endpoint HTTP para poblar la bandeja de entrada del usuario.
    """
    nro_usuario = token_data.get('nro_usuario')
    try:
        return notificaciones_services.listar_mis_notificaciones(nro_usuario)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put('/leer')
def update_marcar_como_leido(data: dict = Body(...), token_data: dict = Depends(verificar_token)):
    """
    Endpoint para marcar una o todas las notificaciones como leídas.
    """
    nro_usuario = token_data.get('nro_usuario')
    id_notificacion = data.get('id_notificacion')
    marcar_todo = data.get('marcar_todo', False)

    try:
        return notificaciones_services.cambiar_estado_leido(
            nro_usuario=nro_usuario,
            id_notificacion=id_notificacion,
            marcar_todo=marcar_todo,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/prueba')
def post_emitir_notificacion_prueba(
    data: dict = Body(default={}),
    token_data: dict = Depends(verificar_token),
):
    """
    Emite una notificación push en tiempo real al usuario autenticado para verificar
    conectividad WebSocket y alertas móviles.
    """
    nro_usuario = token_data.get('nro_usuario')
    if not nro_usuario:
        raise HTTPException(status_code=401, detail="Usuario no identificado.")

    titulo = str((data or {}).get("titulo") or "Alerta operativa OBRATEC").strip()
    cuerpo = str(
        (data or {}).get("cuerpo")
        or "Notificación push en tiempo real verificada correctamente en tu dispositivo móvil."
    ).strip()
    tipo = str((data or {}).get("tipo") or "OBRA").strip().upper()

    enviadas = notificaciones_services.emitir_notificacion_push_empresa(
        titulo=titulo,
        cuerpo=cuerpo,
        tipo_referencia=tipo,
        id_empresa=token_data.get("id_empresa"),
        usuarios_especificos=[int(nro_usuario)],
    )
    return {
        "success": True,
        "message": "Notificación push enviada en tiempo real.",
        "enviadas": enviadas,
    }
