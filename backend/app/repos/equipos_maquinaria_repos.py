from app.classes.postgres import PostgreSQL


def listar_equipos_maquinaria_fn(
    id_empresa: int,
    tipo: str = '',
    estado: str = ''
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            SELECT
                em.id_equipo_maquinaria,
                em.codigo,
                em.nombre,
                em.tipo,
                em.marca,
                em.modelo,
                em.numero_serie,
                em.descripcion,
                em.estado,
                em.id_empresa,
                e.nombre_empresa,
                em.created_at,
                em.updated_at
            FROM obras.t_equipo_maquinaria em
            INNER JOIN obras.t_empresa e
                ON e.id_empresa = em.id_empresa
            WHERE em.id_empresa = %s
        """

        params = [id_empresa]

        if tipo:
            query += " AND em.tipo = %s"
            params.append(tipo)

        if estado:
            query += " AND em.estado = %s"
            params.append(estado)

        query += " ORDER BY em.id_equipo_maquinaria DESC;"

        resultado = db.execute_query(
            query,
            tuple(params),
            fetchall=True
        )

        columnas = [
            "id_equipo_maquinaria",
            "codigo",
            "nombre",
            "tipo",
            "marca",
            "modelo",
            "numero_serie",
            "descripcion",
            "estado",
            "id_empresa",
            "nombre_empresa",
            "created_at",
            "updated_at"
        ]

        data = [
            dict(zip(columnas, fila))
            for fila in (resultado or [])
        ]

        return {
            "success": True,
            "data": data
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close_connection()


def obtener_equipo_maquinaria_fn(
    id_equipo_maquinaria: int,
    id_empresa: int
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            SELECT
                em.id_equipo_maquinaria,
                em.codigo,
                em.nombre,
                em.tipo,
                em.marca,
                em.modelo,
                em.numero_serie,
                em.descripcion,
                em.estado,
                em.id_empresa,
                e.nombre_empresa,
                em.created_at,
                em.updated_at
            FROM obras.t_equipo_maquinaria em
            INNER JOIN obras.t_empresa e
                ON e.id_empresa = em.id_empresa
            WHERE em.id_equipo_maquinaria = %s
              AND em.id_empresa = %s;
        """

        resultado = db.execute_query(
            query,
            (
                id_equipo_maquinaria,
                id_empresa
            ),
            fetchone=True
        )

        if not resultado:
            return {
                "success": False,
                "error": "El equipo o maquinaria no existe o no pertenece a la empresa."
            }

        columnas = [
            "id_equipo_maquinaria",
            "codigo",
            "nombre",
            "tipo",
            "marca",
            "modelo",
            "numero_serie",
            "descripcion",
            "estado",
            "id_empresa",
            "nombre_empresa",
            "created_at",
            "updated_at"
        ]

        data = dict(zip(columnas, resultado))

        return {
            "success": True,
            "data": data
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close_connection()


def registrar_equipo_maquinaria_fn(
    codigo: str,
    nombre: str,
    tipo: str,
    marca: str,
    modelo: str,
    numero_serie: str,
    descripcion: str,
    estado: str,
    id_empresa: int
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            INSERT INTO obras.t_equipo_maquinaria
            (
                codigo,
                nombre,
                tipo,
                marca,
                modelo,
                numero_serie,
                descripcion,
                estado,
                id_empresa
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_equipo_maquinaria;
        """

        resultado = db.execute_query(
            query,
            (
                codigo,
                nombre,
                tipo,
                marca,
                modelo,
                numero_serie,
                descripcion,
                estado,
                id_empresa
            ),
            fetchone=True,
            commit=True
        )

        if not resultado:
            return {
                "success": False,
                "error": "No se pudo registrar el equipo o maquinaria."
            }

        return {
            "success": True,
            "id_equipo_maquinaria": resultado[0]
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close_connection()


def actualizar_equipo_maquinaria_fn(
    id_equipo_maquinaria: int,
    codigo: str,
    nombre: str,
    tipo: str,
    marca: str,
    modelo: str,
    numero_serie: str,
    descripcion: str,
    estado: str,
    id_empresa: int
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            UPDATE obras.t_equipo_maquinaria
            SET
                codigo = %s,
                nombre = %s,
                tipo = %s,
                marca = %s,
                modelo = %s,
                numero_serie = %s,
                descripcion = %s,
                estado = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id_equipo_maquinaria = %s
              AND id_empresa = %s
            RETURNING id_equipo_maquinaria;
        """

        resultado = db.execute_query(
            query,
            (
                codigo,
                nombre,
                tipo,
                marca,
                modelo,
                numero_serie,
                descripcion,
                estado,
                id_equipo_maquinaria,
                id_empresa
            ),
            fetchone=True,
            commit=True
        )

        if resultado:
            return {
                "success": True,
                "id_equipo_maquinaria": resultado[0]
            }

        return {
            "success": False,
            "error": "El equipo o maquinaria no existe o no pertenece a la empresa."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close_connection()


def actualizar_estado_equipo_maquinaria_fn(
    id_equipo_maquinaria: int,
    estado: str,
    id_empresa: int
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            UPDATE obras.t_equipo_maquinaria
            SET
                estado = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id_equipo_maquinaria = %s
              AND id_empresa = %s
            RETURNING id_equipo_maquinaria, estado;
        """

        resultado = db.execute_query(
            query,
            (
                estado,
                id_equipo_maquinaria,
                id_empresa
            ),
            fetchone=True,
            commit=True
        )

        if resultado:
            return {
                "success": True,
                "id_equipo_maquinaria": resultado[0],
                "estado": resultado[1]
            }

        return {
            "success": False,
            "error": "El equipo o maquinaria no existe o no pertenece a la empresa."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close_connection()


def listar_asignaciones_equipo_maquinaria_fn(
    id_empresa: int,
    id_obra: int = None,
    id_equipo_maquinaria: int = None,
    estado: str = ''
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            SELECT
                a.id_asignacion,
                a.id_equipo_maquinaria,
                em.codigo,
                em.nombre,
                em.tipo,
                em.marca,
                em.modelo,
                a.id_obra,
                o.codigo,
                o.nombre,
                o.id_empresa,
                e.nombre_empresa,
                a.fecha_asignacion,
                a.fecha_retiro,
                a.estado,
                a.observacion,
                a.created_at,
                a.updated_at
            FROM obras.t_equipo_maquinaria_obra a
            INNER JOIN obras.t_equipo_maquinaria em
                ON em.id_equipo_maquinaria = a.id_equipo_maquinaria
            INNER JOIN obras.t_obra o
                ON o.id_obra = a.id_obra
            INNER JOIN obras.t_empresa e
                ON e.id_empresa = o.id_empresa
            WHERE em.id_empresa = %s
              AND o.id_empresa = %s
        """

        params = [
            id_empresa,
            id_empresa
        ]

        if id_obra:
            query += " AND a.id_obra = %s"
            params.append(id_obra)

        if id_equipo_maquinaria:
            query += " AND a.id_equipo_maquinaria = %s"
            params.append(id_equipo_maquinaria)

        if estado:
            query += " AND a.estado = %s"
            params.append(estado)

        query += " ORDER BY a.id_asignacion DESC;"

        resultado = db.execute_query(
            query,
            tuple(params),
            fetchall=True
        )

        columnas = [
            "id_asignacion",
            "id_equipo_maquinaria",
            "codigo_equipo",
            "nombre_equipo",
            "tipo",
            "marca",
            "modelo",
            "id_obra",
            "codigo_obra",
            "nombre_obra",
            "id_empresa",
            "nombre_empresa",
            "fecha_asignacion",
            "fecha_retiro",
            "estado",
            "observacion",
            "created_at",
            "updated_at"
        ]

        data = [
            dict(zip(columnas, fila))
            for fila in (resultado or [])
        ]

        return {
            "success": True,
            "data": data
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close_connection()


def obtener_asignacion_equipo_maquinaria_fn(
    id_asignacion: int,
    id_empresa: int
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            SELECT
                a.id_asignacion,
                a.id_equipo_maquinaria,
                em.codigo,
                em.nombre,
                em.tipo,
                em.marca,
                em.modelo,
                a.id_obra,
                o.codigo,
                o.nombre,
                o.id_empresa,
                e.nombre_empresa,
                a.fecha_asignacion,
                a.fecha_retiro,
                a.estado,
                a.observacion,
                a.created_at,
                a.updated_at
            FROM obras.t_equipo_maquinaria_obra a
            INNER JOIN obras.t_equipo_maquinaria em
                ON em.id_equipo_maquinaria = a.id_equipo_maquinaria
            INNER JOIN obras.t_obra o
                ON o.id_obra = a.id_obra
            INNER JOIN obras.t_empresa e
                ON e.id_empresa = o.id_empresa
            WHERE a.id_asignacion = %s
              AND em.id_empresa = %s
              AND o.id_empresa = %s;
        """

        resultado = db.execute_query(
            query,
            (
                id_asignacion,
                id_empresa,
                id_empresa
            ),
            fetchone=True
        )

        if not resultado:
            return {
                "success": False,
                "error": "La asignación no existe o no pertenece a la empresa."
            }

        columnas = [
            "id_asignacion",
            "id_equipo_maquinaria",
            "codigo_equipo",
            "nombre_equipo",
            "tipo",
            "marca",
            "modelo",
            "id_obra",
            "codigo_obra",
            "nombre_obra",
            "id_empresa",
            "nombre_empresa",
            "fecha_asignacion",
            "fecha_retiro",
            "estado",
            "observacion",
            "created_at",
            "updated_at"
        ]

        data = dict(zip(columnas, resultado))

        return {
            "success": True,
            "data": data
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close_connection()


def asignar_equipo_maquinaria_fn(
    id_equipo_maquinaria: int,
    id_obra: int,
    observacion: str,
    id_empresa: int
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            INSERT INTO obras.t_equipo_maquinaria_obra
            (
                id_equipo_maquinaria,
                id_obra,
                fecha_asignacion,
                estado,
                observacion
            )
            SELECT
                em.id_equipo_maquinaria,
                o.id_obra,
                CURRENT_DATE,
                'ASIGNADO',
                %s
            FROM obras.t_equipo_maquinaria em
            INNER JOIN obras.t_obra o
                ON o.id_obra = %s
            WHERE em.id_equipo_maquinaria = %s
              AND em.id_empresa = %s
              AND o.id_empresa = %s
            RETURNING id_asignacion;
        """

        resultado = db.execute_query(
            query,
            (
                observacion,
                id_obra,
                id_equipo_maquinaria,
                id_empresa,
                id_empresa
            ),
            fetchone=True,
            commit=True
        )

        if not resultado:
            return {
                "success": False,
                "error": "El equipo o la obra no existen o no pertenecen a la empresa."
            }

        return {
            "success": True,
            "id_asignacion": resultado[0]
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close_connection()


def retirar_equipo_maquinaria_fn(
    id_asignacion: int,
    observacion: str,
    id_empresa: int
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            UPDATE obras.t_equipo_maquinaria_obra a
            SET
                estado = 'RETIRADO',
                fecha_retiro = CURRENT_DATE,
                observacion = %s,
                updated_at = CURRENT_TIMESTAMP
            FROM obras.t_equipo_maquinaria em,
                 obras.t_obra o
            WHERE a.id_asignacion = %s
              AND a.id_equipo_maquinaria = em.id_equipo_maquinaria
              AND a.id_obra = o.id_obra
              AND em.id_empresa = %s
              AND o.id_empresa = %s
            RETURNING a.id_asignacion, a.estado, a.fecha_retiro;
        """

        resultado = db.execute_query(
            query,
            (
                observacion,
                id_asignacion,
                id_empresa,
                id_empresa
            ),
            fetchone=True,
            commit=True
        )

        if resultado:
            return {
                "success": True,
                "id_asignacion": resultado[0],
                "estado": resultado[1],
                "fecha_retiro": resultado[2]
            }

        return {
            "success": False,
            "error": "La asignación no existe o no pertenece a la empresa."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close_connection()