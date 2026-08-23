from app.config import Config
from app.classes.postgres import PostgreSQL

def get_profile(nro_usuario):
    db=PostgreSQL()

    try:
        db.create_connection()

        query=f'''
            SELECT B.ci, A.username, NULL AS fecha_registro, A.id_usuario,
                   'ACTIVO' AS estado, A.id_rol, A.id_empresa, E.nombre_empresa,
                   B.nombre_completo, B.telefono, A.correo, B.direccion,
                   C.nombre_rol, 0 AS cant_vehiculos
            FROM {Config.SCHEMA}.t_usuario A
            LEFT JOIN {Config.SCHEMA}.t_persona B ON A.id_persona = B.id_persona
            LEFT JOIN {Config.SCHEMA}.t_rol C ON A.id_rol = C.id_rol
            LEFT JOIN {Config.SCHEMA}.t_empresa E ON E.id_empresa = A.id_empresa
            WHERE A.id_usuario = %s;
        '''

        user=db.execute_query(query,(nro_usuario,),fetchone=True)

        columns=[]
        for column in  db.cur.description:
            columns.append(column[0])
        print(columns) 
        
        data=dict(zip(columns,user))

        print(data)

        return data

    except Exception as e:
        raise ValueError(f'ERROR: {str(e)}')
    finally:
        db.close_connection()

def update_profile(data:dict):
    db=PostgreSQL()
    try:
        db.create_connection()

       #PREPARAR INSERT PERSONA
        query=f"""
            UPDATE {Config.SCHEMA}.t_persona
            SET telefono=%s, direccion=%s
            WHERE ci=%s
        """
        params=(data['telefono'], data['direccion'], data['ci'])

        db.execute_query(query, params)

        query_user = f"""
            UPDATE {Config.SCHEMA}.t_usuario
            SET correo=%s
            WHERE id_usuario=%s
        """
        db.execute_query(query_user, (data['correo'], data['nro_usuario']))

        if data.get('password_hash'):
            query_user=f"""
            UPDATE {Config.SCHEMA}.t_usuario
            SET password=%s
            WHERE id_usuario=%s
            """
            param_user=(data['password_hash'],data['nro_usuario'])
            db.execute_query(query_user,param_user)

        db.conn.commit()
        
        return {
            'success':True,
            'message':'Perfil Actualizado Correctamente.'
        }  
            
        
    except Exception as e:
        raise ValueError(f'ERROR: {str(e)}')