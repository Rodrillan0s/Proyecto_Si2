# app/services/auth_services.py
from werkzeug.security import generate_password_hash, check_password_hash
from app.repos import auth_repos
from app.utils import security
from app.classes.postgre import PostgreSQL  # Importamos la clase de DB aquí

def register_new_user(data: dict) -> tuple[dict, int]:
    # VALIDACION: SELECCIONAR CAMPOS REQUERIDOS PARA EL REGISTRO
    required_fields = ['user', 'doc', 'name', 'mail', 'number', 'password']

    for field in required_fields:
        if field not in data:
            return {'success': False, 'message': 'Debe Ingresar Todos los Campos Requeridos'}, 400
        
    # ORGANIZAR TODOS LO PARAMETROS
    user_name = data.get('user').upper()
    doc = data.get('doc')
    name = data.get('name').upper()
    mail = data.get('mail').lower()
    number = data.get('number')
    direction = data.get('dir')
    password = data.get('password')
    id_role = 4  # ROL NRO.4 = CLIENTE

    accion = 'REGISTRO DE USUARIO'

    if direction:
        direction = direction.upper()

    db = PostgreSQL()
    
    try:
        db.create_connection()

        #VALIDAMOS SI EL USUARIO YA EXISTE
        if auth_repos.check_user_exists(db, doc, mail, user_name):
            return {'success': False, 'message': 'El usuario ya se encuentra registrado.'}, 409

        # ENCRIPTAR CONTRASEÑA
        password_hash = generate_password_hash(password=password, method='pbkdf2:sha256')  

        # INSERTAR USUARIO A LA BASE DE DATOS
        filas_afectadas = auth_repos.insert_user(
            db=db, user=user_name, doc=doc, name=name, mail=mail, 
            number=number, direction=direction, password_hash=password_hash, id_role=id_role
        )
            
        #LANZAMOS UN ERROR PARA QUE VAYA AL EXCEPT
        if not filas_afectadas or filas_afectadas < 1:
            raise Exception('Hubo un problema al registrar el usuario en la base de datos.')
            
        new_user_row = auth_repos.get_user_id_by_username(db, user_name)
        
        if new_user_row:
            new_user_id = new_user_row[0] 
            #GUARDAMOS EN LA BITACORA
            db.insert_log(accion=accion, id_user=new_user_id)
            
        db.conn.commit()
        return {'success': True, 'message': 'Usuario Registrado Exitosamente'}, 201

    except Exception as e:
        if db.conn:
            db.conn.rollback()
        return {'success': False, 'message': str(e)}, 500
        
    finally:
        db.close_connection()


def validate_user(data: dict) -> tuple[dict, int]:
    user_input = data.get('user_input', '').upper()
    password = data.get('password')
    accion = 'INICIO DE SESION'

    if not user_input or not password:
        return {'success': False, 'message': 'Debe Ingresar Correo y Contraseña'}, 400

    db = PostgreSQL() 
    try:
        db.create_connection() 

        result = auth_repos.extract_login_user(db, user_input=user_input)

        if not result:
            return {'success': False, 'message': 'El Usuario Ingresado No Existe'}, 404
        
        # ORGANIZAR LOS DATOS DE LA DB
        user_id = result[0]
        user_name = result[1]
        password_hash = result[2]
        name = result[3]
        mail = result[4]
        role_id = result[5]
        account_stat = result[6]
        id_empresa = result[7]

        # INICIO DE SESION FALLIDO: CUENTA SUSPENDIDA
        if account_stat != 'ACTIVO':
            return {'success': False, 'message': 'La cuenta se encuentra Inactiva o Suspendida.'}, 403
        
        # INICIO DE SESION FALLIDO: CONTRASEÑA INCORRECTA
        if not check_password_hash(password_hash, password):
            return {'success': False, 'message': 'Contraseña Incorrecta.'}, 401
        
        # INICIO DE SESION EXITOSO: LOG Y TOKEN
        db.insert_log(accion=accion, id_user=user_id)
        
        token = security.create_access_token(
            user_id=user_id,
            user_name=user_name,
            role=role_id,
            id_tenant=id_empresa,
            name=name
        )
        
        
        db.conn.commit()
        
        print(f"Login exitoso para el usuario: {user_name}")
        return {
            'success': True,
            'message': 'Inicio de Sesion Exitoso',
            'access_token': token,
            'user': {
                'id_usuario': user_id,
                'nombre_razon_social': name,
                'correo': mail,
                'id_rol': role_id,
                'id_empresa': id_empresa
            }
        }, 200

    except Exception as e:
        if db.conn:
            db.conn.rollback()
        return {'success': False, 'message': f'ERROR : {e}'}, 500
        
    finally:
        db.close_connection()