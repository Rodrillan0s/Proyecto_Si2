from app.repos import profile_repos
from app.utils import security
from werkzeug.security import check_password_hash, generate_password_hash
import re

def obtener_perfil_usuario(nro_usuario):

    if not nro_usuario:
        raise ValueError('Debe Estar Logueado para ver su perfil.')
    
    usuario_db=profile_repos.get_profile(nro_usuario)

    if not usuario_db:
        raise ValueError('El usuario no se encuentra registrado en el Sistema.')
    
    return {
        'success':True,
        'message':'Datos del Usuario Obtenido Exitosamente',
        'data':usuario_db
    }

def actualizar_perfil_usuario(nro_usuario: int, datos_perfil: dict):
    datos_perfil['nro_usuario'] = nro_usuario
    
   
    password_plano = datos_perfil.get('password')
    if password_plano:
        datos_perfil['password_hash'] = generate_password_hash(password_plano) 
    else:
        
        datos_perfil['password_hash'] = None

    return profile_repos.update_profile(datos_perfil)

def cambiar_password_usuario(nro_usuario: int, datos: dict):
    password_actual = datos.get('password_actual')
    password_nueva = datos.get('password_nueva')
    confirmar_password = datos.get('confirmar_password')

    passwords = (password_actual, password_nueva, confirmar_password)
    if any(not isinstance(password, str) or not password for password in passwords):
        raise ValueError('Los tres campos de contraseña son obligatorios')

    if password_nueva != confirmar_password:
        raise ValueError('Las contraseñas no coinciden')

    cumple_requisitos = (
        len(password_nueva) >= 8
        and re.search(r'[A-Z]', password_nueva)
        and re.search(r'[a-z]', password_nueva)
        and re.search(r'[0-9]', password_nueva)
        and re.search(r'[^A-Za-z0-9\s]', password_nueva)
    )
    if not cumple_requisitos:
        raise ValueError('La nueva contraseña no cumple los requisitos de seguridad')

    password_hash = profile_repos.get_password_hash(nro_usuario)
    if not password_hash:
        raise ValueError('Usuario no encontrado')

    if not check_password_hash(password_hash, password_actual):
        raise ValueError('La contraseña actual es incorrecta')

    nuevo_password_hash = generate_password_hash(password_nueva)
    profile_repos.update_password(nro_usuario, nuevo_password_hash)

    return {
        'success': True,
        'message': 'Contraseña actualizada correctamente'
    }