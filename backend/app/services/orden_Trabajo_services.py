from app.repos import orden_Trabajo_repos, bitacora_repos

from app.repos.orden_Trabajo_repos import (
    listar_responsables_orden_trabajo_fn,
    asignar_responsable_orden_trabajo_fn,
    eliminar_responsable_orden_trabajo_fn
)
def listar_ordenes_trabajo(
    token_data: dict,
    id_empresa: int = None,
    id_obra: int = None
) -> dict:
    id_usuario = token_data.get('nro_usuario')
    rol = token_data.get('nombre_rol') or ''
    id_empresa_token = token_data.get('id_empresa')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    res = orden_Trabajo_repos.listar_ordenes_trabajo_fn(
        id_usuario=id_usuario,
        rol=rol,
        id_empresa=id_empresa,
        id_empresa_token=id_empresa_token,
        id_obra=id_obra
    )

    if not res.get('success'):
        raise ValueError(
            res.get('error', 'Error al obtener las órdenes de trabajo.')
        )

    return res


def obtener_orden_trabajo(
    orden_nro: int,
    token_data: dict
) -> dict:

    id_usuario = token_data.get('nro_usuario')
    rol = token_data.get('nombre_rol') or ''
    id_empresa_token = token_data.get('id_empresa')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    res = orden_Trabajo_repos.obtener_orden_trabajo_fn(
        orden_nro=orden_nro,
        id_usuario=id_usuario,
        rol=rol,
        id_empresa_token=id_empresa_token
    )

    if not res.get('success'):
        raise ValueError(
            res.get('error', 'No se pudo obtener la orden de trabajo.')
        )

    return res


def crear_orden_trabajo(
    data: dict,
    token_data: dict,
    client_ip: str = "unknown"
) -> dict:

    id_usuario = token_data.get('nro_usuario')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    id_obra = data.get('id_obra')

    if not id_obra:
        raise ValueError("El id_obra es obligatorio.")

    tipo_trab = (data.get('tipo_trab') or '').strip()

    if not tipo_trab:
        raise ValueError("El tipo_trab es obligatorio.")

    cuadrilla = data.get('cuadrilla')

    estado = (data.get('estado') or 'PENDIENTE').strip()

    fecha_inicio = data.get('fecha_inicio')
    fecha_fin = data.get('fecha_fin')

    observacion = (data.get('observacion') or '').strip()

    id_usuarios = data.get('id_usuarios') or []

    res = orden_Trabajo_repos.registrar_orden_trabajo_fn(
    id_obra=id_obra,
    tipo_trab=tipo_trab,
    cuadrilla=cuadrilla,
    estado=estado,
    fecha_inicio=fecha_inicio or None,
    fecha_fin=fecha_fin or None,
    observacion=observacion or None,
    id_usuarios=id_usuarios,
    id_usuario_creador=id_usuario
)

    if not res.get('success'):
        raise ValueError(
            res.get(
                'error',
                'No se pudo registrar la orden de trabajo.'
            )
        )

    bitacora_repos.registrar_bitacora(
    id_usuario=id_usuario,
    modulo="ORDEN_TRABAJO",
    accion="REGISTRAR_ORDEN",
    descripcion=f"Orden de trabajo creada para obra {id_obra}.",
    ip=client_ip,
    estado="EXITOSO"
)

    return res
def actualizar_orden_trabajo(
    orden_nro: int,
    data: dict,
    token_data: dict,
    client_ip: str = "unknown"
) -> dict:

    id_usuario = token_data.get('nro_usuario')
    rol = token_data.get('nombre_rol') or ''
    id_empresa_token = token_data.get('id_empresa')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    tipo_trab = (data.get('tipo_trab') or '').strip()

    if not tipo_trab:
        raise ValueError("El tipo_trab es obligatorio.")

    cuadrilla = data.get('cuadrilla')
    estado = (data.get('estado') or '').strip()
    fecha_inicio = data.get('fecha_inicio')
    fecha_fin = data.get('fecha_fin')
    observacion = (data.get('observacion') or '').strip()

    res = orden_Trabajo_repos.actualizar_orden_trabajo_fn(
        orden_nro=orden_nro,
        tipo_trab=tipo_trab,
        cuadrilla=cuadrilla,
        estado=estado,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin or None,
        observacion=observacion or None,
        id_usuario=id_usuario,
        rol=rol,
        id_empresa_token=id_empresa_token
    )

    if not res.get('success'):
        raise ValueError(
            res.get(
                'error',
                'No se pudo actualizar la orden de trabajo.'
            )
        )

    bitacora_repos.registrar_bitacora(
        id_usuario=id_usuario,
        modulo="ORDEN_TRABAJO",
        accion="ACTUALIZAR_ORDEN",
        descripcion=f"Orden de trabajo {orden_nro} actualizada.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return res


def eliminar_orden_trabajo(
    orden_nro: int,
    token_data: dict,
    client_ip: str = "unknown"
) -> dict:

    id_usuario = token_data.get('nro_usuario')
    rol = token_data.get('nombre_rol') or ''
    id_empresa_token = token_data.get('id_empresa')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    res = orden_Trabajo_repos.eliminar_orden_trabajo_fn(
        orden_nro=orden_nro,
        id_usuario=id_usuario,
        rol=rol,
        id_empresa_token=id_empresa_token
    )

    if not res.get('success'):
        raise ValueError(
            res.get(
                'error',
                'No se pudo eliminar la orden de trabajo.'
            )
        )

    bitacora_repos.registrar_bitacora(
        id_usuario=id_usuario,
        modulo="ORDEN_TRABAJO",
        accion="ELIMINAR_ORDEN",
        descripcion=f"Orden de trabajo {orden_nro} eliminada.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return res


def actualizar_estado_orden_trabajo(
    orden_nro: int,
    data: dict,
    token_data: dict,
    client_ip: str = "unknown"
) -> dict:

    id_usuario = token_data.get('nro_usuario')
    rol = token_data.get('nombre_rol') or ''
    id_empresa_token = token_data.get('id_empresa')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    estado = (data.get('estado') or '').strip()

    if not estado:
        raise ValueError("El estado es obligatorio.")

    res = orden_Trabajo_repos.actualizar_estado_orden_trabajo_fn(
        orden_nro=orden_nro,
        estado=estado,
        id_usuario=id_usuario,
        rol=rol,
        id_empresa_token=id_empresa_token
    )

    if not res.get('success'):
        raise ValueError(
            res.get(
                'error',
                'No se pudo actualizar el estado de la orden de trabajo.'
            )
        )

    bitacora_repos.registrar_bitacora(
        id_usuario=id_usuario,
        modulo="ORDEN_TRABAJO",
        accion="ACTUALIZAR_ESTADO",
        descripcion=f"Estado de orden {orden_nro} actualizado a '{estado}'.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return res


def listar_historial_orden_trabajo(
    orden_nro: int,
    token_data: dict
) -> dict:

    id_usuario = token_data.get('nro_usuario')
    rol = token_data.get('nombre_rol') or ''
    id_empresa_token = token_data.get('id_empresa')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    res = orden_Trabajo_repos.listar_historial_orden_trabajo_fn(
        orden_nro=orden_nro,
        id_usuario=id_usuario,
        rol=rol,
        id_empresa_token=id_empresa_token
    )

    if not res.get('success'):
        raise ValueError(
            res.get(
                'error',
                'No se pudo obtener el historial de la orden de trabajo.'
            )
        )

    return res
def listar_responsables_orden_trabajo(
    orden_nro: int,
    token_data: dict
) -> dict:

    id_usuario = token_data.get('nro_usuario')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    res = orden_Trabajo_repos.listar_responsables_orden_trabajo_fn(
        orden_nro
    )

    if not res.get('success'):
        raise ValueError(
            res.get(
                'error',
                'No se pudieron obtener los responsables de la orden de trabajo.'
            )
        )

    return res


def asignar_responsable_orden_trabajo(
    orden_nro: int,
    data: dict,
    token_data: dict,
    client_ip: str = "unknown"
) -> dict:

    id_usuario = token_data.get('nro_usuario')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    id_responsable = data.get('id_usuario')

    if not id_responsable:
        raise ValueError("El id_usuario del responsable es obligatorio.")

    res = orden_Trabajo_repos.asignar_responsable_orden_trabajo_fn(
        orden_nro,
        id_responsable
    )

    if not res.get('success'):
        raise ValueError(
            res.get(
                'error',
                'No se pudo asignar el responsable a la orden de trabajo.'
            )
        )

    bitacora_repos.registrar_bitacora(
        id_usuario=id_usuario,
        modulo="ORDEN_TRABAJO",
        accion="ASIGNAR_RESPONSABLE",
        descripcion=(
            f"Usuario {id_responsable} asignado como responsable "
            f"de la orden de trabajo {orden_nro}."
        ),
        ip=client_ip,
        estado="EXITOSO"
    )

    return res


def eliminar_responsable_orden_trabajo(
    orden_nro: int,
    id_responsable: int,
    token_data: dict,
    client_ip: str = "unknown"
) -> dict:

    id_usuario = token_data.get('nro_usuario')

    if not id_usuario:
        raise ValueError("No se pudo identificar al usuario autenticado.")

    res = orden_Trabajo_repos.eliminar_responsable_orden_trabajo_fn(
        orden_nro,
        id_responsable
    )

    if not res.get('success'):
        raise ValueError(
            res.get(
                'error',
                'No se pudo eliminar el responsable de la orden de trabajo.'
            )
        )

    bitacora_repos.registrar_bitacora(
        id_usuario=id_usuario,
        modulo="ORDEN_TRABAJO",
        accion="ELIMINAR_RESPONSABLE",
        descripcion=(
            f"Usuario {id_responsable} retirado como responsable "
            f"de la orden de trabajo {orden_nro}."
        ),
        ip=client_ip,
        estado="EXITOSO"
    )

    return res