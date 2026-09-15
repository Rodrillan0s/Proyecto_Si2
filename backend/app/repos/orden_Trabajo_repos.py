from app.classes.postgres import PostgreSQL


def listar_ordenes_trabajo_fn(
    id_usuario: int,
    rol: str = '',
    id_empresa: int = None,
    id_empresa_token: int = None,
    id_obra: int = None
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            SELECT
                ot.orden_nro,
                ot.id_obra,
                o.codigo,
                o.nombre,
                o.id_empresa,
                e.nombre_empresa,
                ot.tipo_trab,
                ot.cuadrilla,
                ot.estado,
                ot.fecha_inicio,
                ot.fecha_fin,
                ot.observacion
            FROM obras.t_orden_trabajo ot
            INNER JOIN obras.t_obra o
                ON o.id_obra = ot.id_obra
            LEFT JOIN obras.t_empresa e
                ON e.id_empresa = o.id_empresa
        """
        condiciones = []
        params = []

        if rol == 'ADMINISTRADOR':
            if id_empresa:
                condiciones.append("o.id_empresa = %s")
                params.append(id_empresa)
        elif rol in ('ADMINISTRADOR_EMPRESA', 'JEFE_DE_OBRA', 'SUPERVISOR_OBRA'):
            empresa_filtro = id_empresa_token or id_empresa
            if empresa_filtro:
                condiciones.append("o.id_empresa = %s")
                params.append(empresa_filtro)
        else:
            condiciones.append("""
                EXISTS (
                    SELECT 1 FROM obras.t_orden_trabajo_usuario otu
                    WHERE otu.id_orden_trabajo = ot.orden_nro
                      AND otu.id_usuario = %s
                )
            """)
            params.append(id_usuario)

        if id_obra:
            condiciones.append("ot.id_obra = %s")
            params.append(id_obra)

        if condiciones:
            query += " WHERE " + " AND ".join(condiciones)

        query += " ORDER BY ot.orden_nro DESC;"

        resultado = db.execute_query(
            query,
            tuple(params),
            fetchall=True
        )

        columnas = [
            "orden_nro",
            "id_obra",
            "codigo",
            "nombre",
            "id_empresa",
            "nombre_empresa",
            "tipo_trab",
            "cuadrilla",
            "estado",
            "fecha_inicio",
            "fecha_fin",
            "observacion"
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


def obtener_orden_trabajo_fn(
    orden_nro: int,
    id_usuario: int,
    rol: str = '',
    id_empresa_token: int = None
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            SELECT
                ot.orden_nro,
                ot.id_obra,
                o.codigo,
                o.nombre,
                o.id_empresa,
                e.nombre_empresa,
                ot.tipo_trab,
                ot.cuadrilla,
                ot.estado,
                ot.fecha_inicio,
                ot.fecha_fin,
                ot.observacion
            FROM obras.t_orden_trabajo ot
            INNER JOIN obras.t_obra o
                ON o.id_obra = ot.id_obra
            LEFT JOIN obras.t_empresa e
                ON e.id_empresa = o.id_empresa
            WHERE ot.orden_nro = %s
        """
        params = [orden_nro]

        if rol == 'ADMINISTRADOR':
            pass
        elif rol in ('ADMINISTRADOR_EMPRESA', 'JEFE_DE_OBRA', 'SUPERVISOR_OBRA'):
            if id_empresa_token:
                query += " AND o.id_empresa = %s"
                params.append(id_empresa_token)
        else:
            query += """
                AND EXISTS (
                    SELECT 1 FROM obras.t_orden_trabajo_usuario otu
                    WHERE otu.id_orden_trabajo = ot.orden_nro
                      AND otu.id_usuario = %s
                )
            """
            params.append(id_usuario)

        resultado = db.execute_query(
            query,
            tuple(params),
            fetchone=True
        )

        if not resultado:
            return {
                "success": False,
                "error": "La orden no existe o no tiene permisos para visualizarla."
            }

        columnas = [
            "orden_nro",
            "id_obra",
            "codigo",
            "nombre",
            "id_empresa",
            "nombre_empresa",
            "tipo_trab",
            "cuadrilla",
            "estado",
            "fecha_inicio",
            "fecha_fin",
            "observacion"
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


def registrar_orden_trabajo_fn(
    id_obra: int,
    tipo_trab: str,
    cuadrilla: int,
    estado: str,
    fecha_inicio,
    fecha_fin,
    observacion: str,
    id_usuarios: list,
    id_usuario_creador: int
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            INSERT INTO obras.t_orden_trabajo
            (
                id_obra,
                tipo_trab,
                cuadrilla,
                estado,
                fecha_inicio,
                fecha_fin,
                observacion
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING orden_nro;
        """

        resultado = db.execute_query(
            query,
            (
                id_obra,
                tipo_trab,
                cuadrilla,
                estado,
                fecha_inicio,
                fecha_fin,
                observacion
            ),
            fetchone=True,
            commit=True
        )

        if not resultado:
            raise ValueError(
                "No se pudo registrar la orden de trabajo."
            )

        orden_nro = resultado[0]

        query_usuario = """
            INSERT INTO obras.t_orden_trabajo_usuario
            (
                id_orden_trabajo,
                id_usuario
            )
            VALUES (%s, %s);
        """

        db.execute_query(
            query_usuario,
            (
                orden_nro,
                id_usuario_creador
            ),
            commit=True
        )

        for id_usuario in id_usuarios:
            if id_usuario == id_usuario_creador:
                continue

            db.execute_query(
                query_usuario,
                (
                    orden_nro,
                    id_usuario
                ),
                commit=True
            )

        return {
            "success": True,
            "orden_nro": orden_nro
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close_connection()


def actualizar_orden_trabajo_fn(
    orden_nro: int,
    tipo_trab: str,
    cuadrilla: int,
    estado: str,
    fecha_inicio,
    fecha_fin,
    observacion: str,
    id_usuario: int,
    rol: str = '',
    id_empresa_token: int = None
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            UPDATE obras.t_orden_trabajo ot
            SET
                tipo_trab = %s,
                cuadrilla = %s,
                estado = %s,
                fecha_inicio = %s,
                fecha_fin = %s,
                observacion = %s
            WHERE ot.orden_nro = %s
        """
        params = [
            tipo_trab,
            cuadrilla,
            estado,
            fecha_inicio,
            fecha_fin,
            observacion,
            orden_nro
        ]

        if rol == 'ADMINISTRADOR':
            pass
        elif rol in ('ADMINISTRADOR_EMPRESA', 'JEFE_DE_OBRA', 'SUPERVISOR_OBRA'):
            if id_empresa_token:
                query += """
                    AND EXISTS (
                        SELECT 1
                        FROM obras.t_obra o
                        WHERE o.id_obra = ot.id_obra
                          AND o.id_empresa = %s
                    )
                """
                params.append(id_empresa_token)
        else:
            query += """
                AND EXISTS (
                    SELECT 1
                    FROM obras.t_orden_trabajo_usuario otu
                    WHERE otu.id_orden_trabajo = ot.orden_nro
                      AND otu.id_usuario = %s
                )
            """
            params.append(id_usuario)

        query += " RETURNING ot.orden_nro;"

        resultado = db.execute_query(
            query,
            tuple(params),
            fetchone=True,
            commit=True
        )

        if resultado:
            return {
                "success": True,
                "orden_nro": resultado[0]
            }

        return {
            "success": False,
            "error": "La orden no existe o no tiene permisos para modificarla."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close_connection()


def eliminar_orden_trabajo_fn(
    orden_nro: int,
    id_usuario: int,
    rol: str = '',
    id_empresa_token: int = None
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            UPDATE obras.t_orden_trabajo ot
            SET estado = 'CANCELADO'
            WHERE ot.orden_nro = %s
        """
        params = [orden_nro]

        if rol == 'ADMINISTRADOR':
            pass
        elif rol in ('ADMINISTRADOR_EMPRESA', 'JEFE_DE_OBRA', 'SUPERVISOR_OBRA'):
            if id_empresa_token:
                query += """
                    AND EXISTS (
                        SELECT 1
                        FROM obras.t_obra o
                        WHERE o.id_obra = ot.id_obra
                          AND o.id_empresa = %s
                    )
                """
                params.append(id_empresa_token)
        else:
            query += """
                AND EXISTS (
                    SELECT 1
                    FROM obras.t_orden_trabajo_usuario otu
                    WHERE otu.id_orden_trabajo = ot.orden_nro
                      AND otu.id_usuario = %s
                )
            """
            params.append(id_usuario)

        query += " RETURNING ot.orden_nro, ot.estado;"

        resultado = db.execute_query(
            query,
            tuple(params),
            fetchone=True,
            commit=True
        )

        if resultado:
            return {
                "success": True,
                "orden_nro": resultado[0],
                "estado": resultado[1]
            }

        return {
            "success": False,
            "error": "La orden no existe o no tiene permisos para cancelarla."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close_connection()


def actualizar_estado_orden_trabajo_fn(
    orden_nro: int,
    estado: str,
    id_usuario: int,
    rol: str = '',
    id_empresa_token: int = None
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            UPDATE obras.t_orden_trabajo ot
            SET estado = %s
            WHERE ot.orden_nro = %s
        """
        params = [estado, orden_nro]

        if rol == 'ADMINISTRADOR':
            pass
        elif rol in ('ADMINISTRADOR_EMPRESA', 'JEFE_DE_OBRA', 'SUPERVISOR_OBRA'):
            if id_empresa_token:
                query += """
                    AND EXISTS (
                        SELECT 1
                        FROM obras.t_obra o
                        WHERE o.id_obra = ot.id_obra
                          AND o.id_empresa = %s
                    )
                """
                params.append(id_empresa_token)
        else:
            query += """
                AND EXISTS (
                    SELECT 1
                    FROM obras.t_orden_trabajo_usuario otu
                    WHERE otu.id_orden_trabajo = ot.orden_nro
                      AND otu.id_usuario = %s
                )
            """
            params.append(id_usuario)

        query += " RETURNING ot.orden_nro, ot.estado;"

        resultado = db.execute_query(
            query,
            tuple(params),
            fetchone=True,
            commit=True
        )

        if resultado:
            return {
                "success": True,
                "orden_nro": resultado[0],
                "estado": resultado[1]
            }

        return {
            "success": False,
            "error": "La orden no existe o no tiene permisos para modificar su estado."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close_connection()


def listar_historial_orden_trabajo_fn(
    orden_nro: int,
    id_usuario: int,
    rol: str = '',
    id_empresa_token: int = None
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            SELECT
                ot.orden_nro,
                ot.id_obra,
                o.codigo,
                o.nombre,
                o.id_empresa,
                e.nombre_empresa,
                ot.tipo_trab,
                ot.cuadrilla,
                ot.estado,
                ot.fecha_inicio,
                ot.fecha_fin,
                ot.observacion
            FROM obras.t_orden_trabajo ot
            INNER JOIN obras.t_obra o
                ON o.id_obra = ot.id_obra
            LEFT JOIN obras.t_empresa e
                ON e.id_empresa = o.id_empresa
            WHERE ot.orden_nro = %s
        """
        params = [orden_nro]

        if rol == 'ADMINISTRADOR':
            pass
        elif rol in ('ADMINISTRADOR_EMPRESA', 'JEFE_DE_OBRA', 'SUPERVISOR_OBRA'):
            if id_empresa_token:
                query += " AND o.id_empresa = %s"
                params.append(id_empresa_token)
        else:
            query += """
                AND EXISTS (
                    SELECT 1
                    FROM obras.t_orden_trabajo_usuario otu
                    WHERE otu.id_orden_trabajo = ot.orden_nro
                      AND otu.id_usuario = %s
                )
            """
            params.append(id_usuario)

        query += " ORDER BY ot.orden_nro DESC;"

        resultado = db.execute_query(
            query,
            tuple(params),
            fetchall=True
        )

        columnas = [
            "orden_nro",
            "id_obra",
            "codigo",
            "nombre",
            "id_empresa",
            "nombre_empresa",
            "tipo_trab",
            "cuadrilla",
            "estado",
            "fecha_inicio",
            "fecha_fin",
            "observacion"
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


def listar_responsables_orden_trabajo_fn(
    orden_nro: int
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            SELECT
                u.id_usuario,
                u.username,
                p.nombre_completo,
                u.correo,
                p.telefono,
                u.id_rol,
                r.nombre_rol,
                u.id_empresa,
                e.nombre_empresa,
                otu.fecha_asignacion
            FROM obras.t_orden_trabajo_usuario otu
            INNER JOIN obras.t_usuario u
                ON u.id_usuario = otu.id_usuario
            LEFT JOIN obras.t_rol r
                ON r.id_rol = u.id_rol
            LEFT JOIN obras.t_persona p
                ON p.id_persona = u.id_usuario
            LEFT JOIN obras.t_empresa e
                ON e.id_empresa = u.id_empresa
            WHERE otu.id_orden_trabajo = %s
              AND u.estado = 'ACTIVO'
            ORDER BY p.nombre_completo;
        """

        resultado = db.execute_query(
            query,
            (orden_nro,),
            fetchall=True
        )

        columnas = [
            "id_usuario",
            "username",
            "nombre_completo",
            "correo",
            "telefono",
            "id_rol",
            "nombre_rol",
            "id_empresa",
            "nombre_empresa",
            "fecha_asignacion"
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


def asignar_responsable_orden_trabajo_fn(
    orden_nro,
    id_usuario
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            INSERT INTO obras.t_orden_trabajo_usuario
            (
                id_orden_trabajo,
                id_usuario
            )
            VALUES (%s, %s);
        """

        resultado = db.execute_query(
            query,
            (
                orden_nro,
                id_usuario
            ),
            commit=True
        )

        return {
            "success": True,
            "resultado": resultado
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close_connection()


def eliminar_responsable_orden_trabajo_fn(
    orden_nro,
    id_usuario
):
    db = PostgreSQL()
    db.create_connection()

    try:
        query = """
            DELETE FROM obras.t_orden_trabajo_usuario
            WHERE id_orden_trabajo = %s
              AND id_usuario = %s;
        """

        resultado = db.execute_query(
            query,
            (
                orden_nro,
                id_usuario
            ),
            commit=True
        )

        return {
            "success": True,
            "resultado": resultado
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close_connection()