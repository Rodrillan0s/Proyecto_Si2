import jwt
from datetime import datetime,timedelta,timezone
from app.config import Config
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

#INICAR PROTOCOLO DE DETECCION BEARER
bearer_scheme = HTTPBearer()

def create_access_token(nro_usuario, username, nombre_rol, id_empresa, nombre_completo,nro_taller , minutes=120):
    """
    GENERA EL JWT PARA LA SESIÓN DEL USUARIO
    """
    payload = {
        'nro_usuario': nro_usuario,
        'username': username,
        'nombre_rol': nombre_rol,
        'id_empresa': id_empresa,
        'nro_taller':nro_taller,
        'nombre_completo': nombre_completo,
        'exp': datetime.now(timezone.utc) + timedelta(minutes=minutes),
        'iat': datetime.now(timezone.utc)
    }

    # Usamos Config.TOKEN_KEY que definiste en tu archivo de configuración
    return jwt.encode(payload, Config.TOKEN_KEY, algorithm="HS256")


def decode_access_token(token: str):
    """
    DECODIFICA Y VALIDA EL JWT ENVIADO POR EL FRONTEND
    """
    try:
        payload = jwt.decode(token, Config.TOKEN_KEY, algorithms=["HS256"])
        
        return {
            'success': True,
            'message': 'TOKEN VALIDO',
            'payload': payload
        }
        
    except jwt.ExpiredSignatureError:
        return {
            'success': False,
            'message': 'Su sesión ha expirado. Por favor, inicie sesión nuevamente.'
        }
        
    except jwt.InvalidTokenError:
        return {
            'success': False,
            'message': 'Token de acceso inválido o corrupto.'
        }


def verificar_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """
    Dependencia reusable que extrae el token Bearer, lo valida con tu función 
    y retorna el payload decodificado si todo está correcto.
    """
    #OBTENEMOS EL TOKEN
    token = credentials.credentials

    #VERIFICAMOS CON FUNCION DE DECODIFICACION
    resultado = decode_access_token(token)
    
    #SI LA DECODIFICACION FALLA (TOKEN EXPIRADO O INVALIDO) RETORNAR ERROR
    if not resultado.get('success'):
        raise HTTPException(status_code=401, detail=resultado.get('message'))
        
    #SI LA VERIFICACION RETORNA EXITO RETORNAMOS EL CONTENIDO DEL TOKEN
    return resultado.get('payload')


def exigir_rol(*roles_permitidos):
    def verificar_rol(token_data: dict = Depends(verificar_token)):
        if token_data.get('nombre_rol') not in roles_permitidos:
            raise HTTPException(status_code=403, detail='No tiene permisos para realizar esta acción.')
        return token_data
    return verificar_rol


import time

_PERMISOS_ROL_CACHE = {}
_CACHE_EXPIRY = 0

def obtener_permisos_rol(nombre_rol: str) -> set:
    global _PERMISOS_ROL_CACHE, _CACHE_EXPIRY
    now = time.time()
    if now < _CACHE_EXPIRY and nombre_rol in _PERMISOS_ROL_CACHE:
        return _PERMISOS_ROL_CACHE[nombre_rol]

    from app.classes.postgres import PostgreSQL
    from app.config import Config
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            SELECT r.nombre_rol, p.nombre_permiso
            FROM {Config.SCHEMA}.t_rol r
            INNER JOIN {Config.SCHEMA}.t_rol_permiso rp ON r.id_rol = rp.id_rol
            INNER JOIN {Config.SCHEMA}.t_permiso p ON rp.id_permiso = p.id_permiso;
        """
        filas = db.execute_query(query, fetchall=True) or []
        nuevo_cache = {}
        for r_rol, p_nom in filas:
            nuevo_cache.setdefault(r_rol, set()).add(p_nom)
        _PERMISOS_ROL_CACHE = nuevo_cache
        _CACHE_EXPIRY = now + 120
        return _PERMISOS_ROL_CACHE.get(nombre_rol, set())
    finally:
        db.close_connection()

def exigir_permiso(nombre_permiso: str):
    def verificar_permiso(token_data: dict = Depends(verificar_token)):
        rol = token_data.get('nombre_rol')
        if rol == 'ADMINISTRADOR':
            return token_data
            
        permisos = obtener_permisos_rol(rol)
        if nombre_permiso not in permisos:
            raise HTTPException(status_code=403, detail='No tiene permisos para realizar esta acción.')
        return token_data
    return verificar_permiso