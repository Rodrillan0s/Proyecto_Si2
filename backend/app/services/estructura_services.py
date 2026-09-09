from app.repos import estructura_repos, bitacora_repos

def construir_arbol_jerarquico(nodos: list) -> list:
    """Convierte una lista plana de nodos en una estructura de árbol anidada."""
    mapa = {}
    arbol = []

    for nodo in nodos:
        nodo_id = nodo['id_estructura']
        mapa[nodo_id] = {**nodo, 'hijos': []}

    for nodo in nodos:
        nodo_id = nodo['id_estructura']
        padre_id = nodo.get('id_padre')

        if padre_id and padre_id in mapa:
            mapa[padre_id]['hijos'].append(mapa[nodo_id])
        else:
            arbol.append(mapa[nodo_id])

    return arbol

def listar_estructura(id_obra: int, token_data: dict) -> dict:
    id_empresa = None if token_data.get('nombre_rol') == 'ADMINISTRADOR' else token_data.get('id_empresa')
    
    res = estructura_repos.listar_estructura_fn(id_obra, id_empresa)
    if not res.get('success'):
        raise ValueError(res.get('error', 'Error al obtener la estructura del proyecto.'))
    
    nodos_planos = res.get('data', [])
    arbol = construir_arbol_jerarquico(nodos_planos)
    
    return {
        "success": True,
        "data": nodos_planos,
        "arbol": arbol
    }

def crear_elemento(id_obra: int, data: dict, token_data: dict, client_ip: str = "unknown") -> dict:
    id_empresa = None if token_data.get('nombre_rol') == 'ADMINISTRADOR' else token_data.get('id_empresa')

    nombre = (data.get('nombre') or '').strip()
    if not nombre:
        raise ValueError("El nombre del elemento de estructura es obligatorio.")

    tipo = (data.get('tipo') or 'Sector').strip()
    descripcion = (data.get('descripcion') or '').strip()
    id_padre = data.get('id_padre') or None
    orden = data.get('orden') or 0

    if id_padre is not None:
        padre = estructura_repos.obtener_contexto_nodo(id_padre, id_obra, id_empresa)
        if not padre:
            raise ValueError("El elemento padre seleccionado no pertenece a este proyecto.")
        if padre.get('id_unidad') is not None:
            raise ValueError("No se pueden crear elementos dentro de una unidad de construcción.")
        if str(padre.get('tipo') or '').strip().casefold() == 'ambiente':
            raise ValueError("No se pueden crear elementos dentro de un Ambiente.")

    res = estructura_repos.registrar_estructura_fn(
        id_obra=id_obra,
        id_padre=id_padre,
        nombre=nombre,
        tipo=tipo,
        descripcion=descripcion,
        orden=orden,
        id_empresa=id_empresa
    )

    if not res.get('success'):
        raise ValueError(res.get('error', 'No se pudo registrar el elemento de estructura.'))

    # Bitácora
    bitacora_repos.registrar_bitacora(
        id_usuario=token_data.get('nro_usuario'),
        modulo="ESTRUCTURA_OBRA",
        accion="REGISTRAR_ELEMENTO",
        descripcion=f"Elemento '{nombre}' ({tipo}) creado en obra {id_obra}.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return res

def actualizar_elemento(id_obra: int, id_estructura: int, data: dict, token_data: dict, client_ip: str = "unknown") -> dict:
    id_empresa = None if token_data.get('nombre_rol') == 'ADMINISTRADOR' else token_data.get('id_empresa')

    nombre = (data.get('nombre') or '').strip()
    if not nombre:
        raise ValueError("El nombre del elemento de estructura es obligatorio.")

    tipo = (data.get('tipo') or 'Sector').strip()
    descripcion = (data.get('descripcion') or '').strip()
    orden = data.get('orden')

    res = estructura_repos.actualizar_estructura_fn(
        id_estructura=id_estructura,
        id_obra=id_obra,
        nombre=nombre,
        tipo=tipo,
        descripcion=descripcion,
        orden=orden,
        id_empresa=id_empresa
    )

    if not res.get('success'):
        raise ValueError(res.get('error', 'No se pudo actualizar el elemento de estructura.'))

    bitacora_repos.registrar_bitacora(
        id_usuario=token_data.get('nro_usuario'),
        modulo="ESTRUCTURA_OBRA",
        accion="ACTUALIZAR_ELEMENTO",
        descripcion=f"Elemento {id_estructura} '{nombre}' actualizado en obra {id_obra}.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return res

def eliminar_elemento(id_obra: int, id_estructura: int, token_data: dict, client_ip: str = "unknown") -> dict:
    id_empresa = None if token_data.get('nombre_rol') == 'ADMINISTRADOR' else token_data.get('id_empresa')

    res = estructura_repos.eliminar_estructura_fn(id_estructura, id_obra, id_empresa)
    if not res.get('success'):
        raise ValueError(res.get('error', 'No se pudo eliminar el elemento de estructura.'))

    bitacora_repos.registrar_bitacora(
        id_usuario=token_data.get('nro_usuario'),
        modulo="ESTRUCTURA_OBRA",
        accion="ELIMINAR_ELEMENTO",
        descripcion=f"Elemento {id_estructura} y subelementos eliminados de obra {id_obra}.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return res

def reordenar_elemento(id_obra: int, id_estructura: int, direccion: str, token_data: dict, client_ip: str = "unknown") -> dict:
    id_empresa = None if token_data.get('nombre_rol') == 'ADMINISTRADOR' else token_data.get('id_empresa')

    if direccion.upper() not in ('UP', 'DOWN'):
        raise ValueError("Dirección de ordenamiento inválida. Use 'UP' o 'DOWN'.")

    res = estructura_repos.reordenar_estructura_fn(id_estructura, id_obra, direccion.upper(), id_empresa)
    if not res.get('success'):
        raise ValueError(res.get('error', 'No se pudo reordenar el elemento.'))

    return res
