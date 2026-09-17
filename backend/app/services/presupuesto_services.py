from app.classes.postgres import PostgreSQL
from app.config import Config
from app.repos import bitacora_repos, presupuesto_repos
from app.utils.security import es_admin_sistema


# ─────────────────────────────────────────────────────────────────────────────
# Excepción propia del módulo de presupuestos
# ─────────────────────────────────────────────────────────────────────────────
class PresupuestoError(ValueError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


# ─────────────────────────────────────────────────────────────────────────────
# Validaciones Multitenant y Seguridad
# ─────────────────────────────────────────────────────────────────────────────

def _validar_obra(id_obra: int, token: dict):
    """
    Verifica que la obra exista y pertenezca a la empresa del usuario
    (o sea accesible por el administrador global).
    """
    obra = presupuesto_repos.obtener_obra_por_id(id_obra)
    if not obra:
        raise PresupuestoError("La obra especificada no existe.", status_code=404)

    es_admin = es_admin_sistema(token)
    token_empresa = token.get("id_empresa")

    if not es_admin and token_empresa and obra["id_empresa"] != token_empresa:
        raise PresupuestoError("No tiene autorización para gestionar presupuestos de esta obra.", status_code=403)

    return obra


def _validar_presupuesto(id_presupuesto: int, token: dict):
    """
    Verifica que el presupuesto exista y que la obra asociada
    pertenezca a la empresa del usuario.
    """
    presupuesto = presupuesto_repos.obtener_presupuesto_por_id(id_presupuesto)
    if not presupuesto:
        raise PresupuestoError("El presupuesto especificado no existe.", status_code=404)

    es_admin = es_admin_sistema(token)
    token_empresa = token.get("id_empresa")

    if not es_admin and token_empresa and presupuesto["id_empresa"] != token_empresa:
        raise PresupuestoError("No tiene autorización para acceder a este presupuesto.", status_code=403)

    return presupuesto


def _validar_apu(id_apu: int, token: dict):
    """
    Verifica que el APU exista y pertenezca a la empresa del usuario.
    """
    apu = presupuesto_repos.obtener_apu_detalle(id_apu)
    if not apu:
        raise PresupuestoError("El APU especificado no existe.", status_code=404)

    es_admin = es_admin_sistema(token)
    token_empresa = token.get("id_empresa")

    if not es_admin and token_empresa and apu["id_empresa"] != token_empresa:
        raise PresupuestoError("No tiene autorización para acceder a este APU.", status_code=403)

    return apu


def _resolver_empresa_para_creacion(token: dict, id_empresa_solicitada=None):
    es_admin = es_admin_sistema(token)
    if es_admin:
        if id_empresa_solicitada:
            return int(id_empresa_solicitada)
        token_empresa = token.get("id_empresa")
        if token_empresa:
            return int(token_empresa)
        raise PresupuestoError("Debe especificar el id_empresa para esta operación.", status_code=400)
    
    token_empresa = token.get("id_empresa")
    if not token_empresa:
        raise PresupuestoError("Su usuario no tiene una empresa asignada.", status_code=403)
    return int(token_empresa)


def _usuario_id(token: dict):
    return token.get("nro_usuario") or token.get("id_usuario") or 1


# ─────────────────────────────────────────────────────────────────────────────
# HU53: Crear y Gestionar Presupuestos de Obra
# ─────────────────────────────────────────────────────────────────────────────

def listar_presupuestos(id_obra: int, token: dict):
    _validar_obra(id_obra, token)
    presupuestos = presupuesto_repos.listar_presupuestos_obra(id_obra)
    return {"success": True, "data": presupuestos}


def obtener_detalle_presupuesto(id_obra: int, id_presupuesto: int, token: dict):
    _validar_obra(id_obra, token)
    presupuesto = _validar_presupuesto(id_presupuesto, token)
    
    if presupuesto["id_obra"] != id_obra:
        raise PresupuestoError("El presupuesto no corresponde a la obra indicada.", status_code=400)

    partidas = presupuesto_repos.listar_partidas_presupuesto(id_presupuesto)
    presupuesto["partidas"] = partidas

    return {"success": True, "data": presupuesto}


def crear_presupuesto(id_obra: int, data: dict, token: dict, client_ip: str):
    obra = _validar_obra(id_obra, token)

    codigo = (data.get("codigo") or "").strip()
    nombre = (data.get("nombre") or "").strip()

    if not codigo:
        raise PresupuestoError("El código del presupuesto es obligatorio.")
    if not nombre:
        raise PresupuestoError("El nombre del presupuesto es obligatorio.")

    descripcion = data.get("descripcion")
    superficie_m2 = data.get("superficie_m2")
    tipo_suelo = data.get("tipo_suelo")
    costo_m2_estimado = data.get("costo_m2_estimado")
    monto_estimado_inicial = data.get("monto_estimado_inicial")
    observaciones = data.get("observaciones")

    id_presupuesto = presupuesto_repos.crear_presupuesto(
        id_obra=id_obra,
        codigo=codigo,
        nombre=nombre,
        descripcion=descripcion,
        superficie_m2=float(superficie_m2) if superficie_m2 is not None else None,
        tipo_suelo=tipo_suelo,
        costo_m2_estimado=float(costo_m2_estimado) if costo_m2_estimado is not None else None,
        monto_estimado_inicial=float(monto_estimado_inicial) if monto_estimado_inicial is not None else None,
        observaciones=observaciones
    )

    if not id_presupuesto:
        raise PresupuestoError("No se pudo crear el presupuesto.", status_code=500)

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="CREAR_PRESUPUESTO",
        descripcion=f"Presupuesto '{codigo} - {nombre}' creado para la obra {obra['codigo']} (ID {id_obra}).",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {
        "success": True,
        "message": "Presupuesto creado exitosamente en estado BORRADOR.",
        "id_presupuesto": id_presupuesto
    }


def actualizar_presupuesto(id_obra: int, id_presupuesto: int, data: dict, token: dict, client_ip: str):
    _validar_obra(id_obra, token)
    presupuesto = _validar_presupuesto(id_presupuesto, token)

    if presupuesto["id_obra"] != id_obra:
        raise PresupuestoError("El presupuesto no corresponde a la obra indicada.", status_code=400)

    if presupuesto["estado"] in ("APROBADO", "CERRADO"):
        raise PresupuestoError("Un presupuesto APROBADO o CERRADO no se puede modificar directamente. Genere una nueva versión.", status_code=400)

    nombre = (data.get("nombre") or presupuesto["nombre"]).strip()
    descripcion = data.get("descripcion", presupuesto["descripcion"])
    superficie_m2 = data.get("superficie_m2", presupuesto["superficie_m2"])
    tipo_suelo = data.get("tipo_suelo", presupuesto["tipo_suelo"])
    costo_m2_estimado = data.get("costo_m2_estimado", presupuesto["costo_m2_estimado"])
    monto_estimado_inicial = data.get("monto_estimado_inicial", presupuesto["monto_estimado_inicial"])
    observaciones = data.get("observaciones", presupuesto["observaciones"])

    presupuesto_repos.actualizar_presupuesto(
        id_presupuesto=id_presupuesto,
        nombre=nombre,
        descripcion=descripcion,
        superficie_m2=float(superficie_m2) if superficie_m2 is not None else None,
        tipo_suelo=tipo_suelo,
        costo_m2_estimado=float(costo_m2_estimado) if costo_m2_estimado is not None else None,
        monto_estimado_inicial=float(monto_estimado_inicial) if monto_estimado_inicial is not None else None,
        observaciones=observaciones
    )

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="ACTUALIZAR_PRESUPUESTO",
        descripcion=f"Presupuesto ID {id_presupuesto} actualizado.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {"success": True, "message": "Presupuesto actualizado correctamente."}


def eliminar_presupuesto(id_obra: int, id_presupuesto: int, token: dict, client_ip: str):
    _validar_obra(id_obra, token)
    presupuesto = _validar_presupuesto(id_presupuesto, token)

    if presupuesto["estado"] != "BORRADOR":
        raise PresupuestoError("Solo se pueden eliminar presupuestos en estado BORRADOR.", status_code=400)

    presupuesto_repos.eliminar_presupuesto(id_presupuesto)

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="ELIMINAR_PRESUPUESTO",
        descripcion=f"Presupuesto ID {id_presupuesto} eliminado.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {"success": True, "message": "Presupuesto eliminado exitosamente."}


# ─────────────────────────────────────────────────────────────────────────────
# HU54: Registrar y Modificar Partidas Presupuestarias
# ─────────────────────────────────────────────────────────────────────────────

def crear_partida(id_obra: int, id_presupuesto: int, data: dict, token: dict, client_ip: str):
    _validar_obra(id_obra, token)
    presupuesto = _validar_presupuesto(id_presupuesto, token)

    if presupuesto["estado"] in ("APROBADO", "CERRADO"):
        raise PresupuestoError("No se pueden agregar partidas a un presupuesto APROBADO o CERRADO.", status_code=400)

    codigo = (data.get("codigo") or "").strip()
    if not codigo:
        codigo = presupuesto_repos.generar_codigo_partida(id_presupuesto)

    nombre = (data.get("nombre") or "").strip()
    if not nombre:
        raise PresupuestoError("El nombre de la partida es obligatorio.")

    id_apu = data.get("id_apu")
    id_unidad_medida = data.get("id_unidad_medida")
    precio_unitario = float(data.get("precio_unitario") or 0.0)

    # Si seleccionó un APU, validar y aplicar snapshot del precio unitario y unidad de medida
    if id_apu:
        apu = _validar_apu(int(id_apu), token)
        if not id_unidad_medida or int(id_unidad_medida) == 0:
            id_unidad_medida = apu["id_unidad_medida"]
        if precio_unitario <= 0:
            precio_unitario = float(apu.get("costo_directo") or apu.get("costo_unitario_total") or 0.0)

    if not id_unidad_medida:
        raise PresupuestoError("La unidad de medida de la partida es obligatoria.")

    cantidad = float(data.get("cantidad") if data.get("cantidad") is not None else 1.0)
    if cantidad <= 0:
        raise PresupuestoError("La cantidad de obra debe ser mayor a cero.")

    descripcion = data.get("descripcion")
    orden = int(data.get("orden") or 0)
    id_estructura = data.get("id_estructura")
    id_unidad_construccion = data.get("id_unidad_construccion")

    id_partida = presupuesto_repos.crear_partida(
        id_presupuesto=id_presupuesto,
        codigo=codigo,
        nombre=nombre,
        id_unidad_medida=int(id_unidad_medida),
        cantidad=cantidad,
        precio_unitario=precio_unitario,
        descripcion=descripcion,
        orden=orden,
        id_apu=int(id_apu) if id_apu else None,
        id_estructura=int(id_estructura) if id_estructura else None,
        id_unidad_construccion=int(id_unidad_construccion) if id_unidad_construccion else None
    )

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="CREAR_PARTIDA",
        descripcion=f"Partida '{codigo} - {nombre}' registrada en presupuesto ID {id_presupuesto}.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {
        "success": True,
        "message": "Partida presupuestaria registrada con éxito.",
        "id_partida": id_partida
    }


def actualizar_partida(id_obra: int, id_presupuesto: int, id_partida: int, data: dict, token: dict, client_ip: str):
    _validar_obra(id_obra, token)
    presupuesto = _validar_presupuesto(id_presupuesto, token)

    if presupuesto["estado"] in ("APROBADO", "CERRADO"):
        raise PresupuestoError("No se pueden modificar partidas de un presupuesto APROBADO o CERRADO.", status_code=400)

    partida = presupuesto_repos.obtener_partida_por_id(id_partida)
    if not partida or partida["id_presupuesto"] != id_presupuesto:
        raise PresupuestoError("La partida no existe en el presupuesto indicado.", status_code=404)

    codigo = (data.get("codigo") or partida["codigo"]).strip()
    nombre = (data.get("nombre") or partida["nombre"]).strip()
    id_unidad_medida = data.get("id_unidad_medida") or partida["id_unidad_medida"]
    cantidad = float(data.get("cantidad") if data.get("cantidad") is not None else partida["cantidad"])
    if cantidad <= 0:
        raise PresupuestoError("La cantidad de obra debe ser mayor a cero.")

    precio_unitario = float(data.get("precio_unitario") if data.get("precio_unitario") is not None else partida["precio_unitario"])
    descripcion = data.get("descripcion", partida["descripcion"])
    orden = int(data.get("orden") if data.get("orden") is not None else partida["orden"])
    id_apu = data.get("id_apu", partida["id_apu"])

    if id_apu and int(id_apu) != (partida.get("id_apu") or 0):
        apu = _validar_apu(int(id_apu), token)
        if "precio_unitario" not in data or float(data.get("precio_unitario") or 0) <= 0:
            precio_unitario = float(apu.get("costo_directo") or apu.get("costo_unitario_total") or 0.0)
        if "id_unidad_medida" not in data:
            id_unidad_medida = apu["id_unidad_medida"]

    presupuesto_repos.actualizar_partida(
        id_partida=id_partida,
        codigo=codigo,
        nombre=nombre,
        id_unidad_medida=int(id_unidad_medida),
        cantidad=cantidad,
        precio_unitario=precio_unitario,
        descripcion=descripcion,
        orden=orden,
        id_apu=int(id_apu) if id_apu else None
    )

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="ACTUALIZAR_PARTIDA",
        descripcion=f"Partida ID {id_partida} actualizada.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {"success": True, "message": "Partida actualizada con éxito."}


def eliminar_partida(id_obra: int, id_presupuesto: int, id_partida: int, token: dict, client_ip: str):
    _validar_obra(id_obra, token)
    presupuesto = _validar_presupuesto(id_presupuesto, token)

    if presupuesto["estado"] in ("APROBADO", "CERRADO"):
        raise PresupuestoError("No se pueden eliminar partidas de un presupuesto APROBADO o CERRADO.", status_code=400)

    partida = presupuesto_repos.obtener_partida_por_id(id_partida)
    if not partida or partida["id_presupuesto"] != id_presupuesto:
        raise PresupuestoError("La partida no pertenece al presupuesto indicado.", status_code=404)

    presupuesto_repos.eliminar_partida(id_partida)

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="ELIMINAR_PARTIDA",
        descripcion=f"Partida ID {id_partida} eliminada del presupuesto ID {id_presupuesto}.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {"success": True, "message": "Partida eliminada con éxito."}


# ─────────────────────────────────────────────────────────────────────────────
# HU57: Asociar APU a Partida (Snapshot de Precio)
# ─────────────────────────────────────────────────────────────────────────────

def asociar_apu_a_partida(id_obra: int, id_presupuesto: int, id_partida: int, data: dict, token: dict, client_ip: str):
    _validar_obra(id_obra, token)
    presupuesto = _validar_presupuesto(id_presupuesto, token)

    if presupuesto["estado"] in ("APROBADO", "CERRADO"):
        raise PresupuestoError("No se puede modificar un presupuesto APROBADO o CERRADO.", status_code=400)

    id_apu = data.get("id_apu")
    if not id_apu:
        raise PresupuestoError("Debe seleccionar un APU para asociar.")

    _validar_apu(id_apu, token)

    partida = presupuesto_repos.obtener_partida_por_id(id_partida)
    if not partida or partida["id_presupuesto"] != id_presupuesto:
        raise PresupuestoError("La partida no pertenece al presupuesto indicado.", status_code=404)

    res = presupuesto_repos.asociar_apu_a_partida(id_partida, id_apu)
    if not res.get("success"):
        raise PresupuestoError(res.get("error", "Error al asociar APU a la partida."))

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="ASOCIAR_APU_PARTIDA",
        descripcion=f"APU ID {id_apu} asociado a Partida ID {id_partida} con precio unitario congelado de {res['precio_unitario_aplicado']}.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {
        "success": True,
        "message": "APU asociado a la partida con éxito (costo unitario congelado como snapshot).",
        "data": res
    }


# ─────────────────────────────────────────────────────────────────────────────
# HU55: Crear y Gestionar APU (Análisis de Precios Unitarios)
# ─────────────────────────────────────────────────────────────────────────────

def listar_apus(token: dict, id_obra: int = None, q: str = None, id_empresa: int = None, solo_vigentes: bool = False):
    id_emp = _resolver_empresa_para_creacion(token, id_empresa)
    apus = presupuesto_repos.listar_apus_empresa(id_emp, id_obra=id_obra, q=q, solo_vigentes=solo_vigentes)
    return {"success": True, "data": apus}


def obtener_detalle_apu(id_apu: int, token: dict):
    apu = _validar_apu(id_apu, token)
    return {"success": True, "data": apu}


def sugerir_codigo_apu(token: dict, id_empresa: int = None):
    id_emp = _resolver_empresa_para_creacion(token, id_empresa)
    codigo = presupuesto_repos.generar_codigo_apu(id_emp)
    return {"success": True, "codigo": codigo}


def sugerir_codigo_partida(id_presupuesto: int, token: dict):
    _validar_presupuesto(id_presupuesto, token)
    codigo = presupuesto_repos.generar_codigo_partida(id_presupuesto)
    return {"success": True, "codigo": codigo}


def listar_equipos_catalogo(token: dict, id_empresa: int = None, q: str = None):
    id_emp = _resolver_empresa_para_creacion(token, id_empresa)
    equipos = presupuesto_repos.listar_equipos(id_emp, q=q)
    return {"success": True, "data": equipos}


def listar_mano_obra_catalogo(token: dict, id_empresa: int = None, q: str = None):
    id_emp = _resolver_empresa_para_creacion(token, id_empresa)
    mano_obra = presupuesto_repos.listar_mano_obra_catalogo(id_emp, q=q)
    return {"success": True, "data": mano_obra}


def crear_apu(data: dict, token: dict, client_ip: str):
    id_empresa = _resolver_empresa_para_creacion(token, data.get("id_empresa"))

    codigo = (data.get("codigo") or "").strip()
    if not codigo:
        codigo = presupuesto_repos.generar_codigo_apu(id_empresa)

    nombre = (data.get("nombre") or "").strip()
    id_unidad_medida = data.get("id_unidad_medida")

    if not nombre:
        raise PresupuestoError("El nombre de la actividad (APU) es obligatorio.")
    if not id_unidad_medida:
        raise PresupuestoError("La unidad de medida del APU es obligatoria.")

    descripcion = data.get("descripcion")
    rendimiento_base = float(data.get("rendimiento_base") or 1.0)
    if rendimiento_base <= 0:
        raise PresupuestoError("El rendimiento base debe ser mayor a cero.")

    id_obra = data.get("id_obra")
    if id_obra:
        _validar_obra(id_obra, token)

    id_apu = presupuesto_repos.crear_apu(
        id_empresa=id_empresa,
        codigo=codigo,
        nombre=nombre,
        id_unidad_medida=int(id_unidad_medida),
        descripcion=descripcion,
        rendimiento_base=rendimiento_base,
        id_obra=int(id_obra) if id_obra else None,
        codigo_base=codigo
    )

    if not id_apu:
        raise PresupuestoError("No se pudo registrar el APU. Verifique que el código no esté duplicado.", status_code=400)

    componentes = data.get("componentes")
    if isinstance(componentes, list) and componentes:
        for comp in componentes:
            try:
                presupuesto_repos.agregar_componente_apu(
                    id_apu=id_apu,
                    tipo_recurso=comp.get("tipo_recurso", "MATERIAL"),
                    descripcion_recurso=comp.get("descripcion_recurso", ""),
                    id_unidad_medida=int(comp.get("id_unidad_medida")),
                    cantidad=float(comp.get("rendimiento") or comp.get("cantidad") or 1.0),
                    precio_unitario=float(comp.get("precio_unitario") or 0.0),
                    id_recurso=comp.get("id_recurso"),
                    rendimiento=float(comp.get("rendimiento") or comp.get("cantidad") or 1.0)
                )
            except Exception:
                pass
        presupuesto_repos.recalcular_costo_unitario_apu(id_apu)

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="CREAR_APU",
        descripcion=f"APU '{codigo} - {nombre}' registrado para la empresa ID {id_empresa}.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {
        "success": True,
        "message": "APU creado exitosamente.",
        "id_apu": id_apu,
        "codigo": codigo
    }


def actualizar_apu(id_apu: int, data: dict, token: dict, client_ip: str):
    apu = _validar_apu(id_apu, token)

    en_uso = presupuesto_repos.apu_en_uso_por_partidas(id_apu)
    target_id_apu = id_apu
    nueva_version_creada = False
    if en_uso:
        target_id_apu = presupuesto_repos.versionar_apu_transaccional(id_apu)
        nueva_version_creada = True

    codigo = (data.get("codigo") or apu["codigo"]).strip()
    nombre = (data.get("nombre") or apu["nombre"]).strip()
    id_unidad_medida = data.get("id_unidad_medida") or apu["id_unidad_medida"]
    descripcion = data.get("descripcion", apu["descripcion"])
    rendimiento_base = float(data.get("rendimiento_base") if data.get("rendimiento_base") is not None else apu["rendimiento_base"])
    estado = data.get("estado", apu["estado"])

    presupuesto_repos.actualizar_apu(
        id_apu=target_id_apu,
        codigo=codigo if not nueva_version_creada else (apu.get("codigo_base") + f"-v{apu.get('version', 1) + 1}"),
        nombre=nombre,
        id_unidad_medida=int(id_unidad_medida),
        descripcion=descripcion,
        rendimiento_base=rendimiento_base,
        estado=estado
    )

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="ACTUALIZAR_APU",
        descripcion=f"APU ID {id_apu} actualizado (Versión target: {target_id_apu}).",
        ip=client_ip,
        estado="EXITOSO"
    )

    msg = "APU actualizado exitosamente."
    if nueva_version_creada:
        msg = f"Se generó automáticamente una nueva versión del APU debido a que la versión anterior ya está asignada a presupuestos de obra."

    return {
        "success": True,
        "message": msg,
        "id_apu": target_id_apu,
        "nueva_version": nueva_version_creada
    }


# ─────────────────────────────────────────────────────────────────────────────
# HU56: Asociar Recursos (Componentes) al APU
# ─────────────────────────────────────────────────────────────────────────────

def agregar_componente_apu(id_apu: int, data: dict, token: dict, client_ip: str):
    apu = _validar_apu(id_apu, token)

    tipo_recurso = (data.get("tipo_recurso") or "").strip().upper()
    if tipo_recurso not in ("MATERIAL", "MANO_OBRA", "EQUIPO"):
        raise PresupuestoError("El tipo de recurso debe ser MATERIAL, MANO_OBRA o EQUIPO.")

    descripcion_recurso = (data.get("descripcion_recurso") or "").strip()
    id_unidad_medida = data.get("id_unidad_medida")

    if not descripcion_recurso:
        raise PresupuestoError("La descripción del recurso es obligatoria.")
    if not id_unidad_medida:
        raise PresupuestoError("La unidad de medida del componente es obligatoria.")

    # Rendimiento unitario
    rendimiento = float(data.get("rendimiento") if data.get("rendimiento") is not None else (data.get("cantidad") or 1.0))
    if rendimiento <= 0:
        raise PresupuestoError("El rendimiento del recurso debe ser mayor a cero.")

    precio_unitario = float(data.get("precio_unitario") or 0.0)
    if precio_unitario < 0:
        raise PresupuestoError("El precio o costo unitario no puede ser negativo.")

    id_recurso = data.get("id_recurso")

    # Validación de pertenencia al catálogo correspondiente
    if tipo_recurso == "MATERIAL" and id_recurso:
        db = PostgreSQL(); db.create_connection()
        try:
            mat = db.execute_query(
                "SELECT id_material, precio, id_empresa FROM obras.t_material WHERE id_material = %s;",
                (id_recurso,), fetchone=True
            )
            if not mat:
                raise PresupuestoError("El material seleccionado no existe en el catálogo.")
            if mat[2] != apu["id_empresa"] and not es_admin_sistema(token):
                raise PresupuestoError("El material pertenece a otra empresa.", status_code=403)
            if precio_unitario <= 0 and mat[1]:
                precio_unitario = float(mat[1])
        finally:
            db.close_connection()

    elif tipo_recurso == "MANO_OBRA" and id_recurso:
        db = PostgreSQL(); db.create_connection()
        try:
            mo = db.execute_query(
                "SELECT id_mano_obra, costo_unitario, id_empresa FROM obras.t_mano_obra WHERE id_mano_obra = %s;",
                (id_recurso,), fetchone=True
            )
            if not mo:
                raise PresupuestoError("La cuadrilla/mano de obra seleccionada no existe.")
            if mo[2] != apu["id_empresa"] and not es_admin_sistema(token):
                raise PresupuestoError("La mano de obra pertenece a otra empresa.", status_code=403)
            if precio_unitario <= 0 and mo[1]:
                precio_unitario = float(mo[1])
        finally:
            db.close_connection()

    elif tipo_recurso == "EQUIPO" and id_recurso:
        db = PostgreSQL(); db.create_connection()
        try:
            eq = db.execute_query(
                "SELECT id_equipo, costo_unitario, id_empresa FROM obras.t_equipo WHERE id_equipo = %s;",
                (id_recurso,), fetchone=True
            )
            if not eq:
                raise PresupuestoError("El equipo seleccionado no existe.")
            if eq[2] != apu["id_empresa"] and not es_admin_sistema(token):
                raise PresupuestoError("El equipo pertenece a otra empresa.", status_code=403)
            if precio_unitario <= 0 and eq[1]:
                precio_unitario = float(eq[1])
        finally:
            db.close_connection()

    # Si el APU está en uso, versionar automáticamente
    target_id_apu = id_apu
    nueva_version_creada = False
    if presupuesto_repos.apu_en_uso_por_partidas(id_apu):
        target_id_apu = presupuesto_repos.versionar_apu_transaccional(id_apu)
        nueva_version_creada = True

    id_componente = presupuesto_repos.agregar_componente_apu(
        id_apu=target_id_apu,
        tipo_recurso=tipo_recurso,
        descripcion_recurso=descripcion_recurso,
        id_unidad_medida=int(id_unidad_medida),
        cantidad=rendimiento,
        precio_unitario=precio_unitario,
        id_recurso=int(id_recurso) if id_recurso else None,
        rendimiento=rendimiento
    )

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="AGREGAR_COMPONENTE_APU",
        descripcion=f"Recurso '{descripcion_recurso}' ({tipo_recurso}) agregado al APU ID {target_id_apu}.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {
        "success": True,
        "message": "Componente agregado al APU con éxito." if not nueva_version_creada else "Se generó una nueva versión del APU con el nuevo componente incorporado.",
        "id_componente": id_componente,
        "id_apu": target_id_apu,
        "nueva_version": nueva_version_creada
    }


def actualizar_componente_apu(id_apu: int, id_componente: int, data: dict, token: dict, client_ip: str):
    _validar_apu(id_apu, token)

    tipo_recurso = (data.get("tipo_recurso") or "").strip().upper()
    if tipo_recurso not in ("MATERIAL", "MANO_OBRA", "EQUIPO"):
        raise PresupuestoError("El tipo de recurso debe ser MATERIAL, MANO_OBRA o EQUIPO.")

    descripcion_recurso = (data.get("descripcion_recurso") or "").strip()
    id_unidad_medida = data.get("id_unidad_medida")

    if not descripcion_recurso:
        raise PresupuestoError("La descripción del recurso es obligatoria.")
    if not id_unidad_medida:
        raise PresupuestoError("La unidad de medida del componente es obligatoria.")

    rendimiento = float(data.get("rendimiento") if data.get("rendimiento") is not None else (data.get("cantidad") or 1.0))
    if rendimiento <= 0:
        raise PresupuestoError("El rendimiento del recurso debe ser mayor a cero.")

    precio_unitario = float(data.get("precio_unitario") or 0.0)
    if precio_unitario < 0:
        raise PresupuestoError("El precio no puede ser negativo.")

    id_recurso = data.get("id_recurso")

    # Si está en uso, versionar
    target_id_apu = id_apu
    nueva_version_creada = False
    target_id_componente = id_componente
    if presupuesto_repos.apu_en_uso_por_partidas(id_apu):
        target_id_apu = presupuesto_repos.versionar_apu_transaccional(id_apu)
        nueva_version_creada = True
        # En la nueva versión buscamos el componente clonado correspondiente
        det = presupuesto_repos.obtener_apu_detalle(target_id_apu)
        clonados = [c for c in (det.get("componentes") or []) if c["descripcion_recurso"] == descripcion_recurso and c["tipo_recurso"] == tipo_recurso]
        if clonados:
            target_id_componente = clonados[0]["id_componente"]

    presupuesto_repos.actualizar_componente_apu(
        id_componente=target_id_componente,
        tipo_recurso=tipo_recurso,
        descripcion_recurso=descripcion_recurso,
        id_unidad_medida=int(id_unidad_medida),
        cantidad=rendimiento,
        precio_unitario=precio_unitario,
        id_recurso=int(id_recurso) if id_recurso else None,
        rendimiento=rendimiento
    )

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="ACTUALIZAR_COMPONENTE_APU",
        descripcion=f"Componente ID {target_id_componente} del APU ID {target_id_apu} actualizado.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {
        "success": True,
        "message": "Componente del APU actualizado con éxito.",
        "id_apu": target_id_apu,
        "nueva_version": nueva_version_creada
    }


def eliminar_componente_apu(id_apu: int, id_componente: int, token: dict, client_ip: str):
    _validar_apu(id_apu, token)
    
    target_id_apu = id_apu
    nueva_version_creada = False
    target_id_componente = id_componente
    if presupuesto_repos.apu_en_uso_por_partidas(id_apu):
        target_id_apu = presupuesto_repos.versionar_apu_transaccional(id_apu)
        nueva_version_creada = True
        # Buscar componente equivalente en la nueva versión
        det_orig = presupuesto_repos.obtener_apu_detalle(id_apu)
        orig_comp = next((c for c in (det_orig.get("componentes") or []) if c["id_componente"] == id_componente), None)
        if orig_comp:
            det_new = presupuesto_repos.obtener_apu_detalle(target_id_apu)
            clon = next((c for c in (det_new.get("componentes") or []) if c["descripcion_recurso"] == orig_comp["descripcion_recurso"] and c["tipo_recurso"] == orig_comp["tipo_recurso"]), None)
            if clon:
                target_id_componente = clon["id_componente"]

    presupuesto_repos.eliminar_componente_apu(target_id_componente)

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="ELIMINAR_COMPONENTE_APU",
        descripcion=f"Componente ID {target_id_componente} eliminado del APU ID {target_id_apu}.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {
        "success": True,
        "message": "Componente eliminado del APU con éxito.",
        "id_apu": target_id_apu,
        "nueva_version": nueva_version_creada
    }


# ─────────────────────────────────────────────────────────────────────────────
# HU58: Consolidado, Aprobación de Línea Base y Versionado
# ─────────────────────────────────────────────────────────────────────────────

def obtener_consolidado(id_obra: int, id_presupuesto: int, token: dict):
    _validar_obra(id_obra, token)
    p = _validar_presupuesto(id_presupuesto, token)
    if p["id_obra"] != id_obra:
        raise PresupuestoError("El presupuesto no corresponde a la obra indicada.", status_code=400)

    consolidado = presupuesto_repos.obtener_presupuesto_consolidado(id_presupuesto)
    if not consolidado:
        raise PresupuestoError("No se pudo obtener el consolidado del presupuesto.", status_code=404)

    return {"success": True, "data": consolidado}


def aprobar_presupuesto(id_obra: int, id_presupuesto: int, token: dict, client_ip: str):
    _validar_obra(id_obra, token)
    p = _validar_presupuesto(id_presupuesto, token)
    if p["id_obra"] != id_obra:
        raise PresupuestoError("El presupuesto no corresponde a la obra indicada.", status_code=400)

    res = presupuesto_repos.aprobar_presupuesto_transaccional(id_presupuesto)
    if "error" in res:
        raise PresupuestoError(res["error"], status_code=res.get("status_code", 400))

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="APROBAR_PRESUPUESTO_LINEA_BASE",
        descripcion=f"Presupuesto ID {id_presupuesto} (v{res['version']}) aprobado como línea base vigente de la obra ID {id_obra}.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {
        "success": True,
        "message": f"Presupuesto v{res['version']} aprobado y establecido como línea base vigente.",
        "data": res
    }


def cambiar_estado(id_obra: int, id_presupuesto: int, nuevo_estado: str, token: dict, client_ip: str):
    _validar_obra(id_obra, token)
    p = _validar_presupuesto(id_presupuesto, token)
    if p["id_obra"] != id_obra:
        raise PresupuestoError("El presupuesto no corresponde a la obra indicada.", status_code=400)

    nuevo_estado = (nuevo_estado or "").strip().upper()
    if nuevo_estado not in ("BORRADOR", "EN_REVISION", "APROBADO", "CERRADO"):
        raise PresupuestoError("Estado inválido. Debe ser BORRADOR, EN_REVISION, APROBADO o CERRADO.")

    res = presupuesto_repos.cambiar_estado_presupuesto(id_presupuesto, nuevo_estado)
    if "error" in res:
        raise PresupuestoError(res["error"], status_code=res.get("status_code", 400))

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="CAMBIAR_ESTADO_PRESUPUESTO",
        descripcion=f"Presupuesto ID {id_presupuesto} cambió de estado a '{nuevo_estado}'.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {
        "success": True,
        "message": f"Estado del presupuesto actualizado a {nuevo_estado}.",
        "data": res
    }


def versionar_presupuesto(id_obra: int, id_presupuesto: int, data: dict, token: dict, client_ip: str):
    _validar_obra(id_obra, token)
    p = _validar_presupuesto(id_presupuesto, token)
    if p["id_obra"] != id_obra:
        raise PresupuestoError("El presupuesto no corresponde a la obra indicada.", status_code=400)

    nuevo_codigo = data.get("codigo")
    nombre = data.get("nombre")

    nuevo_presupuesto = presupuesto_repos.crear_nueva_version_presupuesto(
        id_presupuesto_origen=id_presupuesto,
        nuevo_codigo=nuevo_codigo,
        nombre=nombre
    )

    if not nuevo_presupuesto:
        raise PresupuestoError("No se pudo generar la nueva versión del presupuesto.")

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="VERSIONAR_PRESUPUESTO",
        descripcion=f"Nueva versión {nuevo_presupuesto['version']} generada a partir del presupuesto ID {id_presupuesto}.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {
        "success": True,
        "message": f"Nueva versión {nuevo_presupuesto['version']} creada exitosamente en estado BORRADOR.",
        "data": nuevo_presupuesto
    }


# ─────────────────────────────────────────────────────────────────────────────
# HU59: Costos Ejecutados
# ─────────────────────────────────────────────────────────────────────────────

def listar_costos_ejecutados(id_obra: int, filters: dict, token: dict):
    _validar_obra(id_obra, token)
    res = presupuesto_repos.listar_costos_ejecutados(
        id_obra=id_obra,
        id_partida=filters.get("id_partida"),
        tipo_recurso=filters.get("tipo_recurso"),
        origen_costo=filters.get("origen_costo"),
        fecha_inicio=filters.get("fecha_inicio"),
        fecha_fin=filters.get("fecha_fin")
    )
    return {"success": True, "data": res}


def registrar_costo_ejecutado(id_obra: int, data: dict, token: dict, client_ip: str):
    _validar_obra(id_obra, token)

    descripcion = (data.get("descripcion") or "").strip()
    if not descripcion:
        raise PresupuestoError("La descripción del costo ejecutado es obligatoria.")

    cantidad = float(data.get("cantidad") or 1.0)
    if cantidad <= 0:
        raise PresupuestoError("La cantidad debe ser mayor a cero.")

    costo_unitario = float(data.get("costo_unitario") or 0.0)
    if costo_unitario < 0:
        raise PresupuestoError("El costo unitario no puede ser negativo.")

    tipo_recurso = (data.get("tipo_recurso") or "MATERIAL").strip().upper()
    if tipo_recurso not in ("MATERIAL", "MANO_OBRA", "EQUIPO", "OTRO"):
        raise PresupuestoError("Tipo de recurso inválido. Debe ser MATERIAL, MANO_OBRA, EQUIPO u OTRO.")

    origen_costo = (data.get("origen_costo") or "REGISTRO_MANUAL").strip().upper()
    if origen_costo not in ('REGISTRO_MANUAL', 'ALMACEN', 'COMPRA', 'MANO_OBRA', 'EQUIPO', 'SUBCONTRATO', 'OTRO'):
        raise PresupuestoError("Origen de costo inválido.")

    id_partida = data.get("id_partida")
    if id_partida:
        p = presupuesto_repos.obtener_partida_por_id(int(id_partida))
        if not p:
            raise PresupuestoError("La partida asociada no existe.")

    id_usuario = _usuario_id(token)

    id_costo = presupuesto_repos.registrar_costo_ejecutado(
        id_obra=id_obra,
        descripcion=descripcion,
        cantidad=cantidad,
        costo_unitario=costo_unitario,
        id_usuario_registro=id_usuario,
        id_partida=int(id_partida) if id_partida else None,
        codigo_costo=data.get("codigo_costo"),
        origen_costo=origen_costo,
        tipo_recurso=tipo_recurso,
        id_unidad_medida=data.get("id_unidad_medida"),
        fecha=data.get("fecha"),
        observacion=data.get("observacion")
    )

    if not id_costo:
        raise PresupuestoError("No se pudo registrar el costo ejecutado.")

    bitacora_repos.registrar_bitacora(
        id_usuario=id_usuario,
        modulo="Modulo_presupuestos",
        accion="REGISTRAR_COSTO_EJECUTADO",
        descripcion=f"Costo ejecutado '{descripcion}' por {round(cantidad * costo_unitario, 2)} registrado en obra ID {id_obra}.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {
        "success": True,
        "message": "Costo ejecutado registrado correctamente.",
        "id_costo_ejecutado": id_costo
    }


def eliminar_costo_ejecutado(id_obra: int, id_costo_ejecutado: int, token: dict, client_ip: str):
    _validar_obra(id_obra, token)
    ok = presupuesto_repos.eliminar_costo_ejecutado(id_costo_ejecutado)
    if not ok:
        raise PresupuestoError("No se encontró el registro de costo ejecutado o no se pudo eliminar.")

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="ELIMINAR_COSTO_EJECUTADO",
        descripcion=f"Costo ejecutado ID {id_costo_ejecutado} eliminado de la obra ID {id_obra}.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {"success": True, "message": "Costo ejecutado eliminado correctamente."}


# ─────────────────────────────────────────────────────────────────────────────
# HU60: Comparativa Presupuestado vs Ejecutado
# ─────────────────────────────────────────────────────────────────────────────

def obtener_comparativa(id_obra: int, id_presupuesto: int = None, token: dict = None):
    _validar_obra(id_obra, token)
    if id_presupuesto:
        p = _validar_presupuesto(id_presupuesto, token)
        if p["id_obra"] != id_obra:
            raise PresupuestoError("El presupuesto no corresponde a la obra indicada.", status_code=400)

    comparativa = presupuesto_repos.obtener_comparativa_presupuesto_ejecutado(id_obra, id_presupuesto)
    return {"success": True, "data": comparativa}

