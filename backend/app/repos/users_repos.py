from app.classes.postgres import PostgreSQL
from app.config import Config

# --- LEER USUARIOS ---
def obtener_todos_los_usuarios():
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
select id_usuario,username,correo,nombre_completo,
fecha_nacimiento,ci,direccion,telefono,nombre_empresa,nombre_rol,a.id_rol,
a.id_empresa
from  obras.t_usuario  a 
inner join obras.t_persona b on a.id_persona=b.id_persona s
inner join obras.t_empresa c on c.id_empresa=a.id_empresa
inner join obras.t_rol d on a.id_rol=d.id_rol
where estado='ACTIVO'
        """
        resultados = db.execute_query(query, fetchall=True)
        
        usuarios = []
        if resultados:
            for r in resultados:
                usuarios.append({
                    "id_usuario": r[0],
                    "username": r[1], 
                    "correo": r[2], 
                    "nombre_completo": r[3],
                    "fecha_nacimiento": r[4],
                    "ci": r[5], 
                    "direccion": r[6], 
                    "telefono": r[7],
                    "nombre_empresa": r[8], 
                    "nombre_rol": r[9], 
                    "id_rol": r[10],
                    "id_empresa": r[11]
                })
        return usuarios
    finally:
        db.close_connection()

# --- REGISTRAR USUARIO ---
def crear_usuario_db(datos):
    db = PostgreSQL()
    db.create_connection()

    try:
        # Validar campos obligatorios
        campos_obligatorios = [
            "username",
            "password",
            "correo",
            "id_empresa",
            "id_rol",
            "nombre_completo",
            "fecha_nacimiento",
            "ci",
            "direccion",
            "telefono",
            "telefono_ref",
            "ubicacion"
        ]

        for campo in campos_obligatorios:
            if campo not in datos or datos[campo] is None or str(datos[campo]).strip() == "":
                raise ValueError(f"El campo '{campo}' es obligatorio")

        # Validar ID de empresa
        try:
            datos["id_empresa"] = int(datos["id_empresa"])
        except (ValueError, TypeError):
            raise ValueError("El ID de empresa debe ser numérico")

        # Validar ID de rol
        try:
            datos["id_rol"] = int(datos["id_rol"])
        except (ValueError, TypeError):
            raise ValueError("El ID de rol debe ser numérico")

        # Validar CI
        if not str(datos["ci"]).isdigit():
            raise ValueError("El CI debe contener solamente números")

        # Validar teléfono
        if not str(datos["telefono"]).isdigit():
            raise ValueError("El teléfono debe contener solamente números")

        # Validar teléfono de referencia
        if not str(datos["telefono_ref"]).isdigit():
            raise ValueError("El teléfono de referencia debe contener solamente números")

        # Llamar al procedimiento
        query = f"""
            CALL obras.p_registrar_usuario(
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            );
        """

        parametros = (
            datos["username"],
            datos["password"],
            datos["correo"],
            datos["id_empresa"],
            datos["id_rol"],
            datos["nombre_completo"],
            datos["fecha_nacimiento"],
            datos["ci"],
            datos["direccion"],
            datos["telefono"],
            datos["telefono_ref"],
            datos["ubicacion"]
        )

        db.execute_query(
            query,
            parametros,
            commit=True
        )

        return True

    finally:
        db.close_connection()


# --- ELIMINAR USUARIO (SOFT DELETE) ---
def eliminar_usuario_db(id_usuario):
    db = PostgreSQL()
    db.create_connection()

    try:
        # Validar que el ID sea numérico
        try:
            id_usuario = int(id_usuario)
        except (ValueError, TypeError):
            raise ValueError("El ID del usuario debe ser numérico")

        query = f"""
            UPDATE OBRAS.t_usuario
            SET estado = 'INACTIVO'
            WHERE id_usuario = %s;
        """

        resultado = db.execute_query(
            query,
            (id_usuario,),
            commit=True
        )

        return True

    finally:
        db.close_connection()