from app.repos import auth_repos
from app.utils import security
from app.classes.postgres import PostgreSQL
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timezone, timedelta
import hashlib

def loguear_usuario(data: dict, user_agent: str = None, client_ip: str = None):
    identificador = data.get('ci')
    password = data.get('password')

    if not identificador or not password:
        raise ValueError("El correo, usuario o CI y la contraseña son obligatorios.")

    db = PostgreSQL()
    db.create_connection()
    try:
        res_db = auth_repos.obtener_usuario_por_login_sp(identificador, db=db)

        if not res_db.get("success"):
            raise ValueError(res_db.get("error", "El usuario no existe o está bloqueado."))

        id_usuario = res_db['id_usuario']
        password_hash = res_db['password_hash']
        # VERIFICAR CONTRASEÑA
        is_valid = False
        try:
            is_valid = check_password_hash(password_hash, password)
        except Exception:
            pass
        if not is_valid:
            is_valid = (password_hash == password)

        if not is_valid:
            # REGISTRAR INTENTOS ERRONEOS AL LOGUEARSE
            res_fallo = auth_repos.registrar_intento_fallido_sp(id_usuario, db=db)
            intentos = res_fallo.get('intentos_fallidos', 0)
            
            if intentos >= 5:
                raise ValueError("Has alcanzado el límite máximo de intentos fallidos. Tu cuenta ha sido bloqueada por 15 minutos.")
            else:
                intentos_restantes = 5 - intentos
                raise ValueError(f"Contraseña incorrecta. Te quedan {intentos_restantes} intento(s) antes de bloquear la cuenta.")

        # VERIFICAR DISPOSITIVOS CONOCIDOS
        fingerprint = f"{user_agent or 'unknown_ua'}"
        dispositivo_hash = hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()
        
        dispositivos_conocidos = res_db.get('dispositivos_conocidos') or []
        verificacion_requerida = False

        if dispositivo_hash not in dispositivos_conocidos:
            verificacion_requerida = True

        # REGISTRAR LOGIN CORRECTO
        auth_repos.login_exitoso_sp(id_usuario, dispositivo_hash, db=db)

        # GENERAR TOKEN JWT DE ACCESO
        token = security.create_access_token(
            id_usuario,
            res_db['username'],
            res_db["nombre_rol"],
            res_db['id_empresa'],
            res_db['nombre_completo'],
            None
        )

        return {
            "success": True,
            "message": "Login exitoso",
            "verificacion_requerida": verificacion_requerida,
            "usuario": {
                "nro_usuario": id_usuario,
                "ci": res_db['ci'],
                "nombre_completo": res_db['nombre_completo'],
                "correo": res_db['correo'],
                "nombre_rol": res_db['nombre_rol'],
                "telefono": res_db['telefono'],
                "id_empresa": res_db["id_empresa"],
                "nombre_empresa": res_db["nombre_empresa"],
                "nro_taller": None
            },
            "token": token
        }
    finally:
        db.close_connection()

def registrar_nuevo_usuario(data: dict):
    
    #VALIDAR CAMPOS OBLIGATORIOS
    campos_obligatorios = ['ci', 'nombre_completo', 'nombre_usuario', 'password']
    for campo in campos_obligatorios:
        if not data.get(campo):
            raise ValueError(f"El campo '{campo}' es obligatorio.")
            
    #VALIDAR QUE EL NOMBRE DE USUARIO NO ESTE EN USO
    nombre_usuario = data.get('nombre_usuario').upper()
    if auth_repos.existe_nombre_usuario(nombre_usuario):
        raise ValueError(f"El nombre de usuario '{nombre_usuario}' ya se encuentra registrado.")

    #VALIDAR SI LA PERSONA YA EXISTE PARA NO REGISTRARLA
    ci = data.get('ci')
    persona_existe = auth_repos.existe_persona_por_ci(ci)
            
    #PREPARAR DATOS Y ENCRIPTAR LA CONSTRASEÑA
    password_plana = data.get('password')
    data['password_hash'] = generate_password_hash(password_plana)
    data['estado'] = 'ACTIVO'
    
    #INSERTAR EN DB
    nro_usuario = auth_repos.registrar_usuario_bd(data, persona_existe)
    
    if not nro_usuario:
        raise ValueError("No se pudo generar el identificador del nuevo usuario.")
        
    #RETORNAR RESPUESTA EXITOSA
    return {
        "success": True,
        "message": "Usuario registrado exitosamente.",
        "data": {
            "nro_usuario": nro_usuario,
            "ci": ci,
            "nombre_usuario": nombre_usuario
        }
    }