from app.classes.postgres import PostgreSQL
from psycopg2 import errors


class ProveedorConflictError(Exception):
    pass


# ─────────────────────────────────────────────────────────────────────────────
# Mapeador de fila → dict
# ─────────────────────────────────────────────────────────────────────────────
_FIELDS = (
    "id_proveedor", "nombre", "nit", "telefono", "email",
    "direccion", "contacto", "estado", "id_empresa",
    "created_at", "updated_at",
)


def _proveedor(row):
    return dict(zip(_FIELDS, row))


# ─────────────────────────────────────────────────────────────────────────────
# LISTAR (paginado)
# ─────────────────────────────────────────────────────────────────────────────
def listar(id_empresa, q=None, estado=None, page=1, limit=20):
    filtros = ["p.id_empresa = %s"]
    params = [id_empresa]

    if q:
        filtros.append(
            "(p.nombre ILIKE %s OR p.nit ILIKE %s OR p.email ILIKE %s OR p.contacto ILIKE %s)"
        )
        like = f"%{q}%"
        params += [like, like, like, like]
    if estado:
        filtros.append("p.estado = %s")
        params.append(estado)

    where = " AND ".join(filtros)

    base_sql = f"""
        SELECT p.id_proveedor, p.nombre, p.nit, p.telefono, p.email,
               p.direccion, p.contacto, p.estado, p.id_empresa,
               p.created_at, p.updated_at
        FROM obras.t_proveedor p
        WHERE {where}
    """

    db = PostgreSQL()
    db.create_connection()
    try:
        count_sql = f"SELECT COUNT(*) FROM obras.t_proveedor p WHERE {where}"
        total = db.execute_query(count_sql, tuple(params), fetchone=True)[0]

        rows = db.execute_query(
            base_sql + " ORDER BY p.nombre, p.id_proveedor LIMIT %s OFFSET %s",
            tuple(params + [limit, (page - 1) * limit]),
            fetchall=True,
        ) or []
        return [_proveedor(r) for r in rows], total
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# OBTENER (fila única)
# ─────────────────────────────────────────────────────────────────────────────
def obtener(id_empresa, id_proveedor):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            SELECT p.id_proveedor, p.nombre, p.nit, p.telefono, p.email,
                   p.direccion, p.contacto, p.estado, p.id_empresa,
                   p.created_at, p.updated_at
            FROM obras.t_proveedor p
            WHERE p.id_empresa = %s AND p.id_proveedor = %s
            """,
            (id_empresa, id_proveedor),
            fetchone=True,
        )
        if not row:
            return None
        return _proveedor(row)
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# CREAR
# ─────────────────────────────────────────────────────────────────────────────
def crear(id_empresa, data):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            INSERT INTO obras.t_proveedor
                (nombre, nit, telefono, email, direccion, contacto, estado, id_empresa)
            VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVO', %s)
            RETURNING id_proveedor
            """,
            (
                data["nombre"], data["nit"],
                data.get("telefono"), data.get("email"),
                data.get("direccion"), data.get("contacto"),
                id_empresa,
            ),
            fetchone=True,
        )
        db.conn.commit()
        return row[0]
    except errors.UniqueViolation as exc:
        db.conn.rollback()
        raise ProveedorConflictError("Ya existe un proveedor con ese NIT en su empresa.") from exc
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# ACTUALIZAR
# ─────────────────────────────────────────────────────────────────────────────
def actualizar(id_empresa, id_proveedor, data):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            UPDATE obras.t_proveedor
            SET nombre    = %s,
                nit       = %s,
                telefono  = %s,
                email     = %s,
                direccion = %s,
                contacto  = %s
            WHERE id_proveedor = %s AND id_empresa = %s
            RETURNING id_proveedor
            """,
            (
                data["nombre"], data["nit"],
                data.get("telefono"), data.get("email"),
                data.get("direccion"), data.get("contacto"),
                id_proveedor, id_empresa,
            ),
            fetchone=True,
        )
        if not row:
            db.conn.rollback()
            return False
        db.conn.commit()
        return True
    except errors.UniqueViolation as exc:
        db.conn.rollback()
        raise ProveedorConflictError("Ya existe un proveedor con ese NIT en su empresa.") from exc
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# CAMBIAR ESTADO
# ─────────────────────────────────────────────────────────────────────────────
def cambiar_estado(id_empresa, id_proveedor, estado):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            UPDATE obras.t_proveedor
            SET estado = %s
            WHERE id_proveedor = %s AND id_empresa = %s
            RETURNING id_proveedor
            """,
            (estado, id_proveedor, id_empresa),
            fetchone=True,
            commit=True,
        )
        return bool(row)
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# MATERIALES DE UN PROVEEDOR
# ─────────────────────────────────────────────────────────────────────────────
def listar_materiales_de_proveedor(id_proveedor, id_empresa):
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(
            """
            SELECT m.id_material, m.codigo, m.nombre_material, m.descripcion,
                   m.estado, pm.created_at AS asociado_en
            FROM obras.t_proveedor_material pm
            JOIN obras.t_material m ON m.id_material = pm.id_material
            WHERE pm.id_proveedor = %s AND m.id_empresa = %s
            ORDER BY m.nombre_material, m.id_material
            """,
            (id_proveedor, id_empresa),
            fetchall=True,
        ) or []
        fields = ("id_material", "codigo", "nombre_material", "descripcion", "estado", "asociado_en")
        return [dict(zip(fields, r)) for r in rows]
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# ASOCIAR MATERIAL
# ─────────────────────────────────────────────────────────────────────────────
def asociar_material(id_proveedor, id_material):
    """
    Inserta la asociación. Devuelve True si se insertó, False si ya existía.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        affected = db.execute_query(
            """
            INSERT INTO obras.t_proveedor_material (id_proveedor, id_material)
            VALUES (%s, %s)
            ON CONFLICT (id_proveedor, id_material) DO NOTHING
            """,
            (id_proveedor, id_material),
        )
        db.conn.commit()
        return (affected or 0) > 0
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# DESASOCIAR MATERIAL
# ─────────────────────────────────────────────────────────────────────────────
def desasociar_material(id_proveedor, id_material):
    db = PostgreSQL()
    db.create_connection()
    try:
        affected = db.execute_query(
            "DELETE FROM obras.t_proveedor_material WHERE id_proveedor=%s AND id_material=%s",
            (id_proveedor, id_material),
        )
        db.conn.commit()
        return (affected or 0) > 0
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# VERIFICAR EXISTENCIA DE MATERIAL
# ─────────────────────────────────────────────────────────────────────────────
def material_existe(id_material, id_empresa):
    db = PostgreSQL()
    db.create_connection()
    try:
        return bool(
            db.execute_query(
                "SELECT 1 FROM obras.t_material WHERE id_material=%s AND id_empresa=%s",
                (id_material, id_empresa),
                fetchone=True,
            )
        )
    finally:
        db.close_connection()
