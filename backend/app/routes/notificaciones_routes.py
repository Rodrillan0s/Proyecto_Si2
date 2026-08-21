from flask import Blueprint, request
from flask_socketio import ConnectionRefusedError, join_room
from app.services import notificaciones_services
from app.utils.security import decode_access_token

router = Blueprint('notificaciones_routes', __name__)

def register_notificaciones_sockets(socketio):
    
    @socketio.on('connect')
    def handle_connect(auth):
        print("[SOCKET] Intento de conexión recibido.")
        
        # Intentamos obtener token de auth o de query params
        token = None
        if auth and isinstance(auth, dict):
            token = auth.get('token')
        
        if not token:
            token = request.args.get('token')
            
        if not token:
            print("[SOCKET] Error: No se envió token.")
            raise ConnectionRefusedError('Token no proporcionado.')

        print(f'[SOCKET] TOKEN RECIBIDO: {token[:30]}')
        validation = decode_access_token(token)
        if not validation.get('success'):
            print("[SOCKET] Error: Token inválido.")
            raise ConnectionRefusedError('Token inválido.')

        payload = validation.get('payload', {})
        user_id = payload.get('user_id', payload.get('id_usuario'))

        # Llamamos al servicio para unirlo a su sala
        notificaciones_services.manejar_conexion_usuario(user_id)
        print(f"[SOCKET] Usuario {user_id} conectado exitosamente.")

    @socketio.on('disconnect')
    def handle_disconnect():
        print("[SOCKET] Cliente desconectado.")