from app.repos import equipos_maquinaria_repos, bitacora_repos


def listar_equipos_maquinaria(
    token_data: dict,
    tipo: str = '',
    estado: str = ''
) -> dict:

    id_usuario = token_data.get('nro_usuario')
    id_empresa_token = token_data.get('id_empresa')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    if not id_empresa_token:
        raise ValueError("No se pudo identificar la empresa del usuario autenticado.")

    res = equipos_maquinaria_repos.listar_equipos_maquinaria_fn(
        id_empresa=id_empresa_token,
        tipo=tipo,
        estado=estado
    )

    if not res.get('success'):
        raise ValueError(
            res.get(
                'error',
                'Error al obtener los equipos y maquinaria.'
            )
        )

    return res


def obtener_equipo_maquinaria(
    id_equipo_maquinaria: int,
    token_data: dict
) -> dict:

    id_usuario = token_data.get('nro_usuario')
    id_empresa_token = token_data.get('id_empresa')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    if not id_empresa_token:
        raise ValueError("No se pudo identificar la empresa del usuario autenticado.")

    res = equipos_maquinaria_repos.obtener_equipo_maquinaria_fn(
        id_equipo_maquinaria=id_equipo_maquinaria,
        id_empresa=id_empresa_token
    )

    if not res.get('success'):
        raise ValueError(
            res.get(
                'error',
                'No se pudo obtener el equipo o maquinaria.'
            )
        )

    return res


def registrar_equipo_maquinaria(
    data: dict,
    token_data: dict,
    client_ip: str = "unknown"
) -> dict:

    id_usuario = token_data.get('nro_usuario')
    id_empresa_token = token_data.get('id_empresa')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    if not id_empresa_token:
        raise ValueError("No se pudo identificar la empresa del usuario autenticado.")

    codigo = (data.get('codigo') or '').strip()

    if not codigo:
        raise ValueError("El código es obligatorio.")

    nombre = (data.get('nombre') or '').strip()

    if not nombre:
        raise ValueError("El nombre es obligatorio.")

    tipo = (data.get('tipo') or '').strip()
    marca = (data.get('marca') or '').strip()
    modelo = (data.get('modelo') or '').strip()
    numero_serie = (data.get('numero_serie') or '').strip()
    descripcion = (data.get('descripcion') or '').strip()
    estado = (data.get('estado') or 'DISPONIBLE').strip()

    res = equipos_maquinaria_repos.registrar_equipo_maquinaria_fn(
        codigo=codigo,
        nombre=nombre,
        tipo=tipo or None,
        marca=marca or None,
        modelo=modelo or None,
        numero_serie=numero_serie or None,
        descripcion=descripcion or None,
        estado=estado,
        id_empresa=id_empresa_token
    )

    if not res.get('success'):
        raise ValueError(
            res.get(
                'error',
                'No se pudo registrar el equipo o maquinaria.'
            )
        )

    bitacora_repos.registrar_bitacora(
        id_usuario=id_usuario,
        modulo="EQUIPO_MAQUINARIA",
        accion="REGISTRAR_EQUIPO",
        descripcion=f"Equipo o maquinaria '{nombre}' registrado.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return res


def actualizar_equipo_maquinaria(
    id_equipo_maquinaria: int,
    data: dict,
    token_data: dict,
    client_ip: str = "unknown"
) -> dict:

    id_usuario = token_data.get('nro_usuario')
    id_empresa_token = token_data.get('id_empresa')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    if not id_empresa_token:
        raise ValueError("No se pudo identificar la empresa del usuario autenticado.")

    codigo = (data.get('codigo') or '').strip()

    if not codigo:
        raise ValueError("El código es obligatorio.")

    nombre = (data.get('nombre') or '').strip()

    if not nombre:
        raise ValueError("El nombre es obligatorio.")

    tipo = (data.get('tipo') or '').strip()
    marca = (data.get('marca') or '').strip()
    modelo = (data.get('modelo') or '').strip()
    numero_serie = (data.get('numero_serie') or '').strip()
    descripcion = (data.get('descripcion') or '').strip()
    estado = (data.get('estado') or '').strip()

    if not estado:
        raise ValueError("El estado es obligatorio.")

    res = equipos_maquinaria_repos.actualizar_equipo_maquinaria_fn(
        id_equipo_maquinaria=id_equipo_maquinaria,
        codigo=codigo,
        nombre=nombre,
        tipo=tipo or None,
        marca=marca or None,
        modelo=modelo or None,
        numero_serie=numero_serie or None,
        descripcion=descripcion or None,
        estado=estado,
        id_empresa=id_empresa_token
    )

    if not res.get('success'):
        raise ValueError(
            res.get(
                'error',
                'No se pudo actualizar el equipo o maquinaria.'
            )
        )

    bitacora_repos.registrar_bitacora(
        id_usuario=id_usuario,
        modulo="EQUIPO_MAQUINARIA",
        accion="ACTUALIZAR_EQUIPO",
        descripcion=f"Equipo o maquinaria {id_equipo_maquinaria} actualizado.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return res


def actualizar_estado_equipo_maquinaria(
    id_equipo_maquinaria: int,
    data: dict,
    token_data: dict,
    client_ip: str = "unknown"
) -> dict:

    id_usuario = token_data.get('nro_usuario')
    id_empresa_token = token_data.get('id_empresa')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    if not id_empresa_token:
        raise ValueError("No se pudo identificar la empresa del usuario autenticado.")

    estado = (data.get('estado') or '').strip()

    if not estado:
        raise ValueError("El estado es obligatorio.")

    res = equipos_maquinaria_repos.actualizar_estado_equipo_maquinaria_fn(
        id_equipo_maquinaria=id_equipo_maquinaria,
        estado=estado,
        id_empresa=id_empresa_token
    )

    if not res.get('success'):
        raise ValueError(
            res.get(
                'error',
                'No se pudo actualizar el estado del equipo o maquinaria.'
            )
        )

    bitacora_repos.registrar_bitacora(
        id_usuario=id_usuario,
        modulo="EQUIPO_MAQUINARIA",
        accion="ACTUALIZAR_ESTADO",
        descripcion=(
            f"Estado del equipo o maquinaria "
            f"{id_equipo_maquinaria} actualizado a '{estado}'."
        ),
        ip=client_ip,
        estado="EXITOSO"
    )

    return res


def listar_asignaciones_equipo_maquinaria(
    token_data: dict,
    id_obra: int = None,
    id_equipo_maquinaria: int = None,
    estado: str = ''
) -> dict:

    id_usuario = token_data.get('nro_usuario')
    id_empresa_token = token_data.get('id_empresa')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    if not id_empresa_token:
        raise ValueError("No se pudo identificar la empresa del usuario autenticado.")

    res = equipos_maquinaria_repos.listar_asignaciones_equipo_maquinaria_fn(
        id_empresa=id_empresa_token,
        id_obra=id_obra,
        id_equipo_maquinaria=id_equipo_maquinaria,
        estado=estado
    )

    if not res.get('success'):
        raise ValueError(
            res.get(
                'error',
                'No se pudieron obtener las asignaciones de equipos y maquinaria.'
            )
        )

    return res


def obtener_asignacion_equipo_maquinaria(
    id_asignacion: int,
    token_data: dict
) -> dict:

    id_usuario = token_data.get('nro_usuario')
    id_empresa_token = token_data.get('id_empresa')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    if not id_empresa_token:
        raise ValueError("No se pudo identificar la empresa del usuario autenticado.")

    res = equipos_maquinaria_repos.obtener_asignacion_equipo_maquinaria_fn(
        id_asignacion=id_asignacion,
        id_empresa=id_empresa_token
    )

    if not res.get('success'):
        raise ValueError(
            res.get(
                'error',
                'No se pudo obtener la asignación del equipo o maquinaria.'
            )
        )

    return res


def asignar_equipo_maquinaria(
    data: dict,
    token_data: dict,
    client_ip: str = "unknown"
) -> dict:

    id_usuario = token_data.get('nro_usuario')
    id_empresa_token = token_data.get('id_empresa')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    if not id_empresa_token:
        raise ValueError("No se pudo identificar la empresa del usuario autenticado.")

    id_equipo_maquinaria = data.get('id_equipo_maquinaria')

    if not id_equipo_maquinaria:
        raise ValueError("El id_equipo_maquinaria es obligatorio.")

    id_obra = data.get('id_obra')

    if not id_obra:
        raise ValueError("El id_obra es obligatorio.")

    observacion = (data.get('observacion') or '').strip()

    res = equipos_maquinaria_repos.asignar_equipo_maquinaria_fn(
        id_equipo_maquinaria=id_equipo_maquinaria,
        id_obra=id_obra,
        observacion=observacion or None,
        id_empresa=id_empresa_token
    )

    if not res.get('success'):
        raise ValueError(
            res.get(
                'error',
                'No se pudo asignar el equipo o maquinaria.'
            )
        )

    bitacora_repos.registrar_bitacora(
        id_usuario=id_usuario,
        modulo="EQUIPO_MAQUINARIA",
        accion="ASIGNAR_EQUIPO",
        descripcion=(
            f"Equipo o maquinaria {id_equipo_maquinaria} "
            f"asignado a la obra {id_obra}."
        ),
        ip=client_ip,
        estado="EXITOSO"
    )

    return res


def retirar_equipo_maquinaria(
    id_asignacion: int,
    data: dict,
    token_data: dict,
    client_ip: str = "unknown"
) -> dict:

    id_usuario = token_data.get('nro_usuario')
    id_empresa_token = token_data.get('id_empresa')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    if not id_empresa_token:
        raise ValueError("No se pudo identificar la empresa del usuario autenticado.")

    observacion = (data.get('observacion') or '').strip()

    res = equipos_maquinaria_repos.retirar_equipo_maquinaria_fn(
        id_asignacion=id_asignacion,
        observacion=observacion or None,
        id_empresa=id_empresa_token
    )

    if not res.get('success'):
        raise ValueError(
            res.get(
                'error',
                'No se pudo retirar el equipo o maquinaria.'
            )
        )

    bitacora_repos.registrar_bitacora(
        id_usuario=id_usuario,
        modulo="EQUIPO_MAQUINARIA",
        accion="RETIRAR_EQUIPO",
        descripcion=f"Asignación {id_asignacion} retirada.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return res