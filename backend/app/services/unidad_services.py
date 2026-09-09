from app.repos import unidad_repos, bitacora_repos, estructura_repos
from decimal import Decimal, InvalidOperation


TIPOS_UNIDAD = {"VIVIENDA", "DEPARTAMENTO", "LOCAL", "LOTE", "OFICINA", "OTRO"}
ESTADOS_UNIDAD = {"PLANIFICADO", "EN_CONSTRUCCION", "FINALIZADO", "SUSPENDIDO"}


def _id_empresa(token_data: dict):
    return None if token_data.get("nombre_rol") == "ADMINISTRADOR" else token_data.get("id_empresa")


def _empresa_del_proyecto(id_obra: int, token_data: dict) -> int:
    empresa = unidad_repos.obtener_empresa_proyecto(id_obra, _id_empresa(token_data))
    if not empresa:
        raise ValueError("El proyecto no existe o no pertenece a su empresa.")
    return empresa


def _numero_no_negativo(value, campo: str, entero=False, permitir_nulo=False):
    if value is None and permitir_nulo:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{campo} debe ser un número válido.")
    try:
        decimal = Decimal(str(value).strip())
        if not decimal.is_finite():
            raise InvalidOperation
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{campo} debe ser un número válido.")
    if entero and decimal != decimal.to_integral_value():
        raise ValueError(f"{campo} debe ser un número entero válido.")
    parsed = int(decimal) if entero else float(decimal)
    if parsed < 0:
        raise ValueError(f"{campo} no puede ser negativo.")
    return parsed


def _validar_colecciones(data: dict):
    ambientes = data.get("ambientes") or []
    caracteristicas = data.get("caracteristicas") or []
    if not isinstance(ambientes, list) or not isinstance(caracteristicas, list):
        raise ValueError("Ambientes y características deben ser listas.")
    nombres = set()
    for item in ambientes:
        if not isinstance(item, dict):
            raise ValueError("Cada ambiente debe ser un objeto válido.")
        nombre = str(item.get("nombre") or "").strip()
        if not nombre:
            raise ValueError("Cada ambiente debe tener nombre.")
        cantidad = _numero_no_negativo(item.get("cantidad"), "La cantidad del ambiente", entero=True)
        if cantidad <= 0:
            raise ValueError("La cantidad de cada ambiente debe ser mayor que cero.")
        key = nombre.casefold()
        if key in nombres:
            raise ValueError(f"El ambiente '{nombre}' está duplicado.")
        nombres.add(key)
        item["nombre"] = nombre
        item["cantidad"] = cantidad
    nombres.clear()
    for item in caracteristicas:
        if not isinstance(item, dict):
            raise ValueError("Cada característica debe ser un objeto válido.")
        nombre = str(item.get("nombre") or "").strip()
        valor = str(item.get("valor") or "").strip()
        if not nombre or not valor:
            raise ValueError("Cada característica debe tener nombre y valor.")
        key = nombre.casefold()
        if key in nombres:
            raise ValueError(f"La característica '{nombre}' está duplicada.")
        nombres.add(key)
        item["nombre"] = nombre
        item["valor"] = valor


def _validar_unidad(data: dict, creando=False) -> dict:
    normalized = dict(data)
    if creando and not data.get("id_estructura") and not str(data.get("nombre") or "").strip():
        raise ValueError("El nombre de la unidad es obligatorio.")
    if not creando and not str(data.get("nombre") or "").strip():
        raise ValueError("El nombre de la unidad es obligatorio.")
    normalized["nombre"] = str(data.get("nombre") or "").strip()
    normalized["descripcion"] = str(data.get("descripcion") or "").strip()
    tipo = str(data.get("tipo_unidad") or "OTRO").strip().upper()
    if tipo not in TIPOS_UNIDAD:
        raise ValueError("Tipo de unidad no válido.")
    normalized["tipo_unidad"] = tipo
    if creando:
        estado = str(data.get("estado") or "PLANIFICADO").strip().upper()
        if estado not in ESTADOS_UNIDAD:
            raise ValueError("Estado de unidad no válido.")
        normalized["estado"] = estado
    normalized["superficie"] = _numero_no_negativo(
        data.get("superficie"), "La superficie", permitir_nulo=creando and data.get("id_modelo") is not None
    )
    normalized["cantidad_plantas"] = _numero_no_negativo(
        data.get("cantidad_plantas"), "La cantidad de plantas", entero=True,
        permitir_nulo=creando and data.get("id_modelo") is not None
    )
    _validar_colecciones(normalized)
    return normalized


def listar_unidades(id_obra: int, token_data: dict):
    _empresa_del_proyecto(id_obra, token_data)
    return unidad_repos.listar_unidades(id_obra, _id_empresa(token_data))


def obtener_unidad(id_obra: int, id_unidad: int, token_data: dict):
    res = unidad_repos.obtener_unidad_detalle(id_obra, id_unidad, _id_empresa(token_data))
    if not res.get("success"):
        raise ValueError(res.get("error"))
    return res


def registrar_unidad(id_obra: int, data: dict, token_data: dict, client_ip="unknown"):
    _empresa_del_proyecto(id_obra, token_data)
    normalized = _validar_unidad(data, creando=True)
    id_empresa = _id_empresa(token_data)
    id_estructura = normalized.get("id_estructura")
    id_padre = normalized.get("id_padre")

    if id_estructura is not None:
        nodo = estructura_repos.obtener_contexto_nodo(id_estructura, id_obra, id_empresa)
        if not nodo:
            raise ValueError("El nodo no existe o no pertenece al proyecto.")
        if nodo.get("id_unidad") is not None:
            raise ValueError("El nodo ya representa una unidad de construcción.")
        if str(nodo.get("tipo") or "").strip().casefold() == "ambiente":
            raise ValueError("Un Ambiente no se puede convertir en unidad de construcción.")
        if nodo.get("tiene_hijos"):
            raise ValueError("No se puede convertir en unidad un nodo que contiene elementos dentro.")
    elif id_padre is not None:
        padre = estructura_repos.obtener_contexto_nodo(id_padre, id_obra, id_empresa)
        if not padre:
            raise ValueError("El elemento padre no pertenece al proyecto.")
        if padre.get("id_unidad") is not None:
            raise ValueError("No se pueden crear unidades dentro de otra unidad de construcción.")
        if str(padre.get("tipo") or "").strip().casefold() == "ambiente":
            raise ValueError("No se pueden crear unidades dentro de un Ambiente.")

    res = unidad_repos.registrar_unidad_fn(
        id_obra, id_empresa, token_data.get("nro_usuario"), normalized
    )
    if not res.get("success"):
        raise ValueError(res.get("error", "No se pudo registrar la unidad."))
    bitacora_repos.registrar_bitacora(
        id_usuario=token_data.get("nro_usuario"), modulo="UNIDADES_CONSTRUCCION",
        accion="REGISTRAR_UNIDAD",
        descripcion=f"Unidad {res.get('codigo')} registrada en obra {id_obra}.",
        ip=client_ip, estado="EXITOSO"
    )
    return res


def actualizar_unidad(id_obra: int, id_unidad: int, data: dict, token_data: dict, client_ip="unknown"):
    normalized = _validar_unidad(data)
    res = unidad_repos.actualizar_unidad_fn(id_obra, id_unidad, _id_empresa(token_data), normalized)
    if not res.get("success"):
        raise ValueError(res.get("error", "No se pudo actualizar la unidad."))
    bitacora_repos.registrar_bitacora(
        id_usuario=token_data.get("nro_usuario"), modulo="UNIDADES_CONSTRUCCION",
        accion="ACTUALIZAR_UNIDAD", descripcion=f"Unidad {id_unidad} actualizada en obra {id_obra}.",
        ip=client_ip, estado="EXITOSO"
    )
    return res


def eliminar_unidad(id_obra: int, id_unidad: int, token_data: dict, client_ip="unknown"):
    _empresa_del_proyecto(id_obra, token_data)
    res = unidad_repos.eliminar_unidad_fn(
        id_obra, id_unidad, _id_empresa(token_data)
    )
    if not res.get("success"):
        raise ValueError(res.get("error", "No se pudo eliminar la unidad."))
    bitacora_repos.registrar_bitacora(
        id_usuario=token_data.get("nro_usuario"), modulo="UNIDADES_CONSTRUCCION",
        accion="ELIMINAR_UNIDAD",
        descripcion=f"Unidad {res.get('codigo') or id_unidad} eliminada de obra {id_obra}.",
        ip=client_ip, estado="EXITOSO"
    )
    return res


def cambiar_estado(id_obra, id_unidad, data, token_data, client_ip="unknown"):
    estado = str(data.get("estado") or "").strip().upper()
    if estado not in ESTADOS_UNIDAD:
        raise ValueError("Estado de unidad no válido.")
    observacion = str(data.get("observacion") or "").strip()
    res = unidad_repos.cambiar_estado_fn(
        id_obra, id_unidad, _id_empresa(token_data), estado,
        token_data.get("nro_usuario"), observacion
    )
    if not res.get("success"):
        raise ValueError(res.get("error"))
    bitacora_repos.registrar_bitacora(
        id_usuario=token_data.get("nro_usuario"), modulo="UNIDADES_CONSTRUCCION",
        accion="CAMBIAR_ESTADO_UNIDAD", descripcion=f"Unidad {id_unidad} cambió a {estado}.",
        ip=client_ip, estado="EXITOSO"
    )
    return res


def listar_modelos(id_obra, token_data):
    return unidad_repos.listar_modelos(_empresa_del_proyecto(id_obra, token_data))


def guardar_modelo(id_obra, data, token_data, id_modelo=None, client_ip="unknown"):
    empresa = _empresa_del_proyecto(id_obra, token_data)
    nombre = str(data.get("nombre") or "").strip()
    tipo = str(data.get("tipo_unidad") or "OTRO").strip().upper()
    if not nombre:
        raise ValueError("El nombre del modelo es obligatorio.")
    if tipo not in TIPOS_UNIDAD:
        raise ValueError("Tipo de unidad no válido.")
    normalized = dict(data, nombre=nombre, tipo_unidad=tipo)
    normalized["superficie_base"] = _numero_no_negativo(data.get("superficie_base"), "La superficie base", permitir_nulo=True)
    normalized["cantidad_plantas_base"] = _numero_no_negativo(data.get("cantidad_plantas_base"), "La cantidad de plantas base", entero=True, permitir_nulo=True)
    normalized["ambientes"] = []
    _validar_colecciones(normalized)
    res = unidad_repos.guardar_modelo(empresa, normalized, id_modelo)
    if not res.get("success"):
        raise ValueError(res.get("error"))
    bitacora_repos.registrar_bitacora(
        id_usuario=token_data.get("nro_usuario"), modulo="UNIDADES_CONSTRUCCION",
        accion="GUARDAR_MODELO_UNIDAD", descripcion=f"Modelo de unidad '{nombre}' guardado.",
        ip=client_ip, estado="EXITOSO"
    )
    return res


def agregar_personalizacion(id_obra, id_unidad, data, token_data, client_ip="unknown"):
    tipo = str(data.get("tipo") or "OTRO").strip().upper()
    descripcion = str(data.get("descripcion") or "").strip()
    if not descripcion:
        raise ValueError("La descripción de la personalización es obligatoria.")
    res = unidad_repos.agregar_personalizacion(id_obra, id_unidad, _id_empresa(token_data), tipo, descripcion)
    if not res.get("success"):
        raise ValueError(res.get("error"))
    bitacora_repos.registrar_bitacora(
        id_usuario=token_data.get("nro_usuario"), modulo="UNIDADES_CONSTRUCCION",
        accion="REGISTRAR_PERSONALIZACION", descripcion=f"Personalización agregada a unidad {id_unidad}.",
        ip=client_ip, estado="EXITOSO"
    )
    return res


def eliminar_personalizacion(id_obra, id_unidad, id_personalizacion, token_data, client_ip="unknown"):
    res = unidad_repos.eliminar_personalizacion(
        id_obra, id_unidad, id_personalizacion, _id_empresa(token_data)
    )
    if not res.get("success"):
        raise ValueError(res.get("error"))
    bitacora_repos.registrar_bitacora(
        id_usuario=token_data.get("nro_usuario"), modulo="UNIDADES_CONSTRUCCION",
        accion="ELIMINAR_PERSONALIZACION", descripcion=f"Personalización {id_personalizacion} eliminada.",
        ip=client_ip, estado="EXITOSO"
    )
    return res


def listar_materiales(id_obra, token_data):
    empresa = _empresa_del_proyecto(id_obra, token_data)
    return unidad_repos.listar_materiales_disponibles(empresa)


def reemplazar_materiales(id_obra, id_unidad, data, token_data, client_ip="unknown"):
    materiales = data.get("materiales") or []
    if not isinstance(materiales, list):
        raise ValueError("Los materiales deben enviarse como una lista.")
    ids = set()
    for item in materiales:
        if not isinstance(item, dict):
            raise ValueError("Cada asociación de material debe ser un objeto válido.")
        item["id_material"] = _numero_no_negativo(
            item.get("id_material"), "El identificador del material", entero=True
        )
        if item["id_material"] <= 0:
            raise ValueError("Cada asociación debe indicar un material válido.")
        item["cantidad"] = _numero_no_negativo(item.get("cantidad"), "La cantidad del material")
        if item["cantidad"] <= 0:
            raise ValueError("La cantidad del material debe ser mayor que cero.")
        key = (item["id_material"], str(item.get("uso_ubicacion") or "").casefold())
        if key in ids:
            raise ValueError("No puede repetir el mismo material y uso.")
        ids.add(key)
    empresa = _empresa_del_proyecto(id_obra, token_data)
    res = unidad_repos.reemplazar_materiales(id_obra, id_unidad, empresa, materiales)
    if not res.get("success"):
        raise ValueError(res.get("error"))
    bitacora_repos.registrar_bitacora(
        id_usuario=token_data.get("nro_usuario"), modulo="UNIDADES_CONSTRUCCION",
        accion="ASOCIAR_MATERIALES_UNIDAD", descripcion=f"Materiales actualizados en unidad {id_unidad}.",
        ip=client_ip, estado="EXITOSO"
    )
    return res
