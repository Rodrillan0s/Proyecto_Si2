from app.classes.postgres import PostgreSQL


def crear_documento(data):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            INSERT INTO obras.t_documento_tecnico
                (id_obra, nombre, descripcion, tipo_documento)
            VALUES (%s, %s, %s, %s)
            RETURNING id_documento;
            """,
            (
                data["id_obra"],
                data["nombre"],
                data.get("descripcion"),
                data["tipo_documento"]
            ),
            fetchone=True
        )
        db.conn.commit()
        return row[0]
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


def crear_version(data):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            INSERT INTO obras.t_documento_tecnico_version
                (
                    id_documento,
                    numero_version,
                    contenido_documento,
                    nombre_archivo,
                    ruta_archivo,
                    tipo_archivo,
                    tamano_bytes,
                    observaciones,
                    id_usuario
                )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_version;
            """,
            (
                data["id_documento"],
                data["numero_version"],
                data["contenido_documento"],
                data["nombre_archivo"],
                data["ruta_archivo"],
                data.get("tipo_archivo", "application/pdf"),
                data["tamano_bytes"],
                data.get("observaciones"),
                data["id_usuario"]
            ),
            fetchone=True
        )

        db.execute_query(
            """
            UPDATE obras.t_documento_tecnico
            SET version_actual = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id_documento = %s;
            """,
            (data["numero_version"], data["id_documento"])
        )

        db.conn.commit()
        return row[0]
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


def obtener(id_documento):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            SELECT
                d.id_documento,
                d.id_obra,
                d.nombre,
                d.descripcion,
                d.tipo_documento,
                d.version_actual,
                d.estado,
                d.created_at,
                d.updated_at,
                v.id_version,
                v.nombre_archivo,
                v.ruta_archivo,
                v.tamano_bytes,
                v.created_at
            FROM obras.t_documento_tecnico d
            LEFT JOIN obras.t_documento_tecnico_version v
                ON v.id_documento = d.id_documento
                AND v.numero_version = d.version_actual
            WHERE d.id_documento = %s;
            """,
            (id_documento,),
            fetchone=True
        )

        if not row:
            return None

        return {
            "id_documento": row[0],
            "id_obra": row[1],
            "nombre": row[2],
            "descripcion": row[3],
            "tipo_documento": row[4],
            "version_actual": row[5],
            "estado": row[6],
            "created_at": str(row[7]) if row[7] else None,
            "updated_at": str(row[8]) if row[8] else None,
            "archivo_actual": {
                "id_version": row[9],
                "nombre_archivo": row[10],
                "ruta_archivo": row[11],
                "tamano_bytes": row[12],
                "created_at": str(row[13]) if row[13] else None
            } if row[9] else None
        }
    finally:
        db.close_connection()


def listar(id_obra):
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(
            """
            SELECT
                d.id_documento,
                d.id_obra,
                d.nombre,
                d.descripcion,
                d.tipo_documento,
                d.version_actual,
                d.estado,
                d.created_at,
                d.updated_at,
                v.nombre_archivo,
                v.tamano_bytes
            FROM obras.t_documento_tecnico d
            LEFT JOIN obras.t_documento_tecnico_version v
                ON v.id_documento = d.id_documento
                AND v.numero_version = d.version_actual
            WHERE d.id_obra = %s
            ORDER BY d.updated_at DESC, d.id_documento DESC;
            """,
            (id_obra,),
            fetchall=True
        ) or []

        return [
            {
                "id_documento": r[0],
                "id_obra": r[1],
                "nombre": r[2],
                "descripcion": r[3],
                "tipo_documento": r[4],
                "version_actual": r[5],
                "estado": r[6],
                "created_at": str(r[7]) if r[7] else None,
                "updated_at": str(r[8]) if r[8] else None,
                "nombre_archivo": r[9],
                "tamano_bytes": r[10]
            }
            for r in rows
        ]
    finally:
        db.close_connection()


def listar_versiones(id_documento):
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(
            """
            SELECT
                v.id_version,
                v.id_documento,
                v.numero_version,
                v.nombre_archivo,
                v.ruta_archivo,
                v.tipo_archivo,
                v.tamano_bytes,
                v.observaciones,
                v.id_usuario,
                v.created_at,
                u.username
            FROM obras.t_documento_tecnico_version v
            LEFT JOIN obras.t_usuario u
                ON u.id_usuario = v.id_usuario
            WHERE v.id_documento = %s
            ORDER BY v.numero_version DESC;
            """,
            (id_documento,),
            fetchall=True
        ) or []

        return [
            {
                "id_version": r[0],
                "id_documento": r[1],
                "numero_version": r[2],
                "nombre_archivo": r[3],
                "ruta_archivo": r[4],
                "tipo_archivo": r[5],
                "tamano_bytes": r[6],
                "observaciones": r[7],
                "id_usuario": r[8],
                "created_at": str(r[9]) if r[9] else None,
                "username": r[10]
            }
            for r in rows
        ]
    finally:
        db.close_connection()


def obtener_version(id_documento, id_version):
    db = PostgreSQL()
    db.create_connection()
    try:
        return db.execute_query(
            """
            SELECT
                id_version,
                numero_version,
                nombre_archivo,
                ruta_archivo,
                tipo_archivo,
                tamano_bytes
            FROM obras.t_documento_tecnico_version
            WHERE id_documento = %s AND id_version = %s;
            """,
            (id_documento, id_version),
            fetchone=True
        )
    finally:
        db.close_connection()


def cambiar_estado(id_documento, estado):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            UPDATE obras.t_documento_tecnico
            SET estado = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id_documento = %s
            RETURNING id_documento;
            """,
            (estado, id_documento),
            fetchone=True
        )
        db.conn.commit()
        return bool(row)
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()