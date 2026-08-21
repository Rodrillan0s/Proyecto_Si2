# app/services/notificaciones_services.py
from flask_socketio import join_room
from datetime import datetime

def manejar_conexion_usuario(user_id: int):
    nombre_sala = f"user_{user_id}"
    join_room(nombre_sala)
    print(f"[SOCKET SERVICE] Conexión establecida. Usuario {user_id} asignado a la sala: {nombre_sala}")
    return {"status": "connected", "room": nombre_sala}

# --- NUEVA FUNCIÓN ---
def emitir_notificacion_masiva(socketio_instance, clientes_ids, asunto, mensaje, canal):
    """
    Recibe la instancia de socketio y la lista de IDs de clientes.
    Emite el evento 'nueva_notificacion' a cada sala individual.
    """
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    payload_socket = {
        "asunto": asunto,
        "mensaje": mensaje,
        "canal": canal,
        "fecha": fecha_actual
    }

    enviados = 0
    for cliente_id in clientes_ids:
        room_name = f"user_{cliente_id}"
        # Emitimos el evento a la sala específica de este cliente
        socketio_instance.emit('nueva_notificacion', payload_socket, room=room_name)
        enviados += 1
        
    print(f"[SOCKET EMIT] Notificación enviada a {enviados} clientes por el canal {canal}.")
    return enviados