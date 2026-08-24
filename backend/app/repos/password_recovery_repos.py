from app.classes.postgres import PostgreSQL
from app.config import Config


class PasswordRecoveryRepositoryError(Exception):
    """Error interno y controlado de persistencia para CU08."""


def buscar_usuarios_por_correo(correo_normalizado: str):
    db = PostgreSQL()

    try:
        db.create_connection()
        if db.conn is None or db.cur is None:
            raise PasswordRecoveryRepositoryError(
                "No se pudo establecer la conexion con la base de datos."
            )

        query = f"""
            SELECT id_usuario, correo, estado
            FROM {Config.SCHEMA}.t_usuario
            WHERE LOWER(TRIM(correo)) = %s
            ORDER BY id_usuario
            LIMIT 2;
        """
        resultados = db.execute_query(
            query,
            (correo_normalizado,),
            fetchall=True,
        )

        return [
            {
                "id_usuario": fila[0],
                "correo": fila[1],
                "estado": fila[2],
            }
            for fila in (resultados or [])
        ]
    except PasswordRecoveryRepositoryError:
        raise
    except Exception as exc:
        raise PasswordRecoveryRepositoryError(
            "No se pudo consultar al usuario para recuperacion."
        ) from exc
    finally:
        db.close_connection()


def actualizar_password(id_usuario: int, password_hash: str):
    db = PostgreSQL()

    try:
        db.create_connection()
        if db.conn is None or db.cur is None:
            raise PasswordRecoveryRepositoryError(
                "No se pudo establecer la conexion con la base de datos."
            )

        query = f"""
            UPDATE {Config.SCHEMA}.t_usuario
            SET password = %s
            WHERE id_usuario = %s;
        """
        filas_afectadas = db.execute_query(
            query,
            (password_hash, id_usuario),
            commit=True,
        )

        return filas_afectadas == 1
    except PasswordRecoveryRepositoryError:
        raise
    except Exception as exc:
        raise PasswordRecoveryRepositoryError(
            "No se pudo actualizar la contrasena del usuario."
        ) from exc
    finally:
        db.close_connection()
