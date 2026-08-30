from app.repos import users_repos
from app.utils import security
from werkzeug.security import generate_password_hash

def listar_usuarios(token_data: dict):
    es_superadmin = security.es_admin_sistema(token_data)
    id_empresa = None if es_superadmin else token_data.get('id_empresa')
    usuarios = users_repos.obtener_todos_los_usuarios(id_empresa)
    return {
        "success": True,
        "message": "Usuarios recuperados exitosamente",
        "data": usuarios
    }

def registrar_usuario(data: dict, token_data: dict):
    campos_requeridos = ['ci', 'nombre_completo', 'nombre_usuario', 'password', 'nro_rol']
    for campo in campos_requeridos:
        if not data.get(campo):
            raise ValueError(f"El campo '{campo}' es obligatorio.")
    if not security.password_cumple_requisitos(data.get('password')):
        raise ValueError("La contraseña no cumple los requisitos de seguridad.")
    es_admin_sistema = security.es_admin_sistema(token_data)
    id_empresa = data.get('id_empresa') if es_admin_sistema else token_data.get('id_empresa')
    if not id_empresa:
        raise ValueError('El usuario administrador no tiene una empresa asociada.')
    if not es_admin_sistema and data.get('nro_rol') in (1, 2):
        raise ValueError('No puede asignar los roles globales desde una empresa.')

    password_hash = generate_password_hash(data['password'])

    datos_persona = (
        data['ci'],
        data['nombre_completo'].upper(),
        data.get('telefono'),
        data.get('direccion')
    )
    
    datos_usuario = (
        data['nombre_usuario'].upper(), 
        password_hash, 
        data.get('correo'),
        data['ci'],
        data['nro_rol'],
        id_empresa
    )

    nuevo_id = users_repos.crear_usuario_db(datos_persona, datos_usuario)

    return {
        "success": True,
        "message": "Usuario registrado exitosamente",
        "nro_usuario": nuevo_id
    }

def actualizar_usuario(nro_usuario: int, data: dict, token_data: dict):
    if nro_usuario <= 0:
        raise ValueError("ID de usuario no válido.")
        
    campos_requeridos = ['ci', 'nombre_completo', 'nombre_usuario', 'nro_rol']
    for campo in campos_requeridos:
        if not data.get(campo):
            raise ValueError(f"El campo '{campo}' es obligatorio.")
    es_admin_sistema = security.es_admin_sistema(token_data)
    id_empresa = data.get('id_empresa') if es_admin_sistema else token_data.get('id_empresa')
    if not id_empresa:
        raise ValueError('El usuario administrador no tiene una empresa asociada.')
    if not es_admin_sistema and data.get('nro_rol') in (1, 2):
        raise ValueError('No puede asignar los roles globales desde una empresa.')

    ci = data['ci']
    
    datos_persona = (
        data['nombre_completo'].upper(),
        data.get('telefono'),
        data.get('direccion')
    )
    
    cambiar_password = False
    if data.get('password') and len(data.get('password').strip()) > 0:
        cambiar_password = True
        password_hash = generate_password_hash(data['password'])
        datos_usuario = (
            data['nombre_usuario'],
            password_hash,
            data.get('correo'),
            data['nro_rol'],
            id_empresa
        )
    else:
        datos_usuario = (
            data['nombre_usuario'],
            data.get('correo'),
            data['nro_rol'],
            id_empresa
        )

    users_repos.actualizar_usuario_db(nro_usuario, ci, datos_persona, datos_usuario, cambiar_password)

    return {
        "success": True,
        "message": "Usuario actualizado exitosamente"
    }

def borrar_usuario(nro_usuario: int, token_data: dict):
    if nro_usuario <= 0:
        raise ValueError("ID de usuario no válido.")
        
    es_superadmin = security.es_admin_sistema(token_data)
    id_empresa = None if es_superadmin else token_data.get('id_empresa')
    if not users_repos.eliminar_usuario_db(nro_usuario, id_empresa):
        raise ValueError('No puede eliminar un usuario fuera de su empresa.')
    
    return {
        "success": True,
        "message": "Usuario eliminado correctamente."
    }