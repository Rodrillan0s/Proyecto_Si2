from app.repos import users_repos
from werkzeug.security import generate_password_hash
import re


def listar_usuarios():
    usuarios = users_repos.obtener_todos_los_usuarios()
    return {
        "success": True,
        "message": "Usuarios recuperados exitosamente",
        "data": usuarios
    }


def registrar_usuario(data: dict):
    campos_requeridos = [
        'username',
        'password',
        'correo',
        'id_empresa',
        'id_rol',
        'nombre_completo',
        'fecha_nacimiento',
        'ci',
        'direccion',
        'telefono',
        'telefono_ref',
        'ubicacion'
    ]

    # VALIDAR CAMPOS OBLIGATORIOS
    for campo in campos_requeridos:
        if campo not in data or data[campo] is None or str(data[campo]).strip() == "":
            raise ValueError(f"El campo '{campo}' es obligatorio.")

    # VALIDAR ID EMPRESA
    try:
        id_empresa = int(data['id_empresa'])
        if id_empresa <= 0:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError("El ID de empresa debe ser un número entero positivo.")

    # VALIDAR ID ROL
    try:
        id_rol = int(data['id_rol'])
        if id_rol <= 0:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError("El ID de rol debe ser un número entero positivo.")

    # VALIDAR CI
    if not str(data['ci']).isdigit():
        raise ValueError("El CI debe contener solamente números.")

    # VALIDAR TELÉFONO
    if not str(data['telefono']).isdigit():
        raise ValueError("El teléfono debe contener solamente números.")

    # VALIDAR TELÉFONO DE REFERENCIA
    if not str(data['telefono_ref']).isdigit():
        raise ValueError("El teléfono de referencia debe contener solamente números.")

    # VALIDAR CORREO
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', data['correo']):
        raise ValueError("El correo electrónico no tiene un formato válido.")

    # VALIDAR CONTRASEÑA
    if len(data['password']) < 6:
        raise ValueError("La contraseña debe tener al menos 6 caracteres.")

    # GENERAR HASH DE CONTRASEÑA
    password_hash = generate_password_hash(data['password'])

    datos = {
        "username": data['username'].upper(),
        "password": password_hash,
        "correo": data['correo'],
        "id_empresa": id_empresa,
        "id_rol": id_rol,
        "nombre_completo": data['nombre_completo'].upper(),
        "fecha_nacimiento": data['fecha_nacimiento'],
        "ci": data['ci'],
        "direccion": data['direccion'],
        "telefono": data['telefono'],
        "telefono_ref": data['telefono_ref'],
        "ubicacion": data['ubicacion']
    }

    users_repos.crear_usuario_db(datos)

    return {
        "success": True,
        "message": "Usuario registrado exitosamente"
    }


def borrar_usuario(id_usuario: int):
    # VALIDAR ID DE USUARIO
    if id_usuario <= 0:
        raise ValueError("ID de usuario no válido.")

    users_repos.eliminar_usuario_db(id_usuario)

    return {
        "success": True,
        "message": "Usuario eliminado correctamente."
    }