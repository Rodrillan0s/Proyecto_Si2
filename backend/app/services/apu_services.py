from app.repos import apu_repos, bitacora_repos
from app.utils.security import es_admin_sistema


class ApuError(ValueError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _usuario_id(token: dict):
    return token.get("nro_usuario") or token.get("id_usuario") or 1


def _resolver_empresa(token: dict, id_empresa_solicitada=None) -> int:
    es_admin = es_admin_sistema(token)
    if es_admin:
        if id_empresa_solicitada:
            return int(id_empresa_solicitada)
        token_empresa = token.get("id_empresa")
        if token_empresa:
            return int(token_empresa)
        # Por defecto asignar Empresa 1 si no se especifica
        return 1
    
    token_empresa = token.get("id_empresa")
    if not token_empresa:
        raise ApuError("Su usuario no tiene una empresa asignada.", status_code=403)
    return int(token_empresa)


def _validar_apu(id_apu: int, token: dict, permitir_base: bool = True):
    apu = apu_repos.obtener_apu_detalle(id_apu)
    if not apu:
        raise ApuError(f"El APU ID {id_apu} no existe.", status_code=404)

    if apu.get("es_base"):
        if permitir_base:
            return apu
        else:
            raise ApuError("No se permite modificar directamente un APU del Catálogo Base OBRATEC.", status_code=403)

    es_admin = es_admin_sistema(token)
    token_empresa = token.get("id_empresa")
    if not es_admin and token_empresa and apu["id_empresa"] != token_empresa:
        raise ApuError("No tiene autorización para acceder a este APU.", status_code=403)

    return apu


# ─────────────────────────────────────────────────────────────────────────────
# Categorías y Catálogo Base
# ─────────────────────────────────────────────────────────────────────────────

def listar_categorias():
    categorias = apu_repos.listar_categorias_apu()
    return {"success": True, "data": categorias}


def listar_catalogo_base(id_categoria: int = None, q: str = None):
    apus = apu_repos.listar_apus_base(id_categoria=id_categoria, q=q)
    return {"success": True, "data": apus}


def copiar_apu_base(id_apu_base: int, token: dict, client_ip: str, data: dict = None):
    id_empresa = _resolver_empresa(token, (data or {}).get("id_empresa"))
    base = _validar_apu(id_apu_base, token, permitir_base=True)
    if not base.get("es_base"):
        raise ApuError("El APU seleccionado no pertenece al Catálogo Base.", status_code=400)

    codigo_personalizado = (data or {}).get("codigo")
    nuevo_id = apu_repos.copiar_apu_base(id_apu_base, id_empresa, codigo_personalizado)
    if not nuevo_id:
        raise ApuError("Error al copiar el APU base hacia la empresa.", status_code=500)

    apu_creado = apu_repos.obtener_apu_detalle(nuevo_id)

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="COPIAR_APU_BASE",
        descripcion=f"APU Base '{base['nombre']}' copiado a la empresa ID {id_empresa} con código '{apu_creado['codigo']}'.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {
        "success": True,
        "message": f"APU '{apu_creado['nombre']}' copiado exitosamente a su catálogo.",
        "data": apu_creado
    }


# ─────────────────────────────────────────────────────────────────────────────
# Mis APUs (Empresa)
# ─────────────────────────────────────────────────────────────────────────────

def listar_mis_apus(token: dict, id_categoria: int = None, solo_vigentes: bool = False, q: str = None, id_obra: int = None, id_empresa_req: int = None):
    id_empresa = _resolver_empresa(token, id_empresa_req)
    apus = apu_repos.listar_mis_apus(id_empresa, id_categoria=id_categoria, solo_vigentes=solo_vigentes, q=q, id_obra=id_obra)
    return {"success": True, "data": apus}


def obtener_detalle_apu(id_apu: int, token: dict):
    apu = _validar_apu(id_apu, token, permitir_base=True)
    return {"success": True, "data": apu}


def crear_apu_empresa(data: dict, token: dict, client_ip: str):
    id_empresa = _resolver_empresa(token, data.get("id_empresa"))
    
    nombre = (data.get("nombre") or "").strip()
    if not nombre:
        raise ApuError("El nombre de la actividad (APU) es obligatorio.")

    id_categoria = data.get("id_categoria")
    if not id_categoria:
        raise ApuError("La categoría del APU es obligatoria.")

    id_unidad_medida = data.get("id_unidad_medida")
    if not id_unidad_medida:
        raise ApuError("La unidad de medida del APU es obligatoria.")

    nuevo_id = apu_repos.crear_apu_empresa(id_empresa, data)
    if not nuevo_id:
        raise ApuError("No se pudo crear el APU.", status_code=500)

    # Si se pasaron componentes iniciales
    componentes = data.get("componentes")
    if isinstance(componentes, list) and componentes:
        for c in componentes:
            try:
                apu_repos.agregar_componente_apu(
                    id_apu=nuevo_id,
                    tipo_recurso=c.get("tipo_recurso", "MATERIAL"),
                    descripcion_recurso=c.get("descripcion_recurso", ""),
                    id_unidad_medida=int(c.get("id_unidad_medida")),
                    rendimiento=float(c.get("rendimiento") or 1.0),
                    precio_unitario=float(c.get("precio_unitario") or 0.0),
                    id_recurso=c.get("id_recurso"),
                    id_material=c.get("id_material"),
                    id_mano_obra=c.get("id_mano_obra"),
                    id_equipo=c.get("id_equipo")
                )
            except Exception:
                pass
        apu_repos.recalcular_apu(nuevo_id)

    apu_creado = apu_repos.obtener_apu_detalle(nuevo_id)

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="CREAR_APU",
        descripcion=f"APU '{apu_creado['codigo']} - {apu_creado['nombre']}' creado desde cero.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {
        "success": True,
        "message": "APU creado exitosamente.",
        "data": apu_creado
    }


def actualizar_apu_empresa(id_apu: int, data: dict, token: dict, client_ip: str):
    apu = _validar_apu(id_apu, token, permitir_base=False)

    apu_repos.actualizar_apu_empresa(id_apu, data)
    apu_act = apu_repos.obtener_apu_detalle(id_apu)

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="ACTUALIZAR_APU",
        descripcion=f"APU ID {id_apu} ('{apu_act['codigo']}') actualizado.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {
        "success": True,
        "message": "APU actualizado exitosamente.",
        "data": apu_act
    }


def versionar_apu(id_apu: int, token: dict, client_ip: str):
    apu = _validar_apu(id_apu, token, permitir_base=False)

    nuevo_id = apu_repos.versionar_apu(id_apu)
    if not nuevo_id:
        raise ApuError("No se pudo generar la nueva versión del APU.", status_code=500)

    nueva_ver = apu_repos.obtener_apu_detalle(nuevo_id)

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="VERSIONAR_APU",
        descripcion=f"Nueva versión generada: {nueva_ver['codigo']} (v{nueva_ver['version']}) a partir del APU {apu['codigo']}.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {
        "success": True,
        "message": f"Nueva versión {nueva_ver['version']} generada exitosamente.",
        "data": nueva_ver
    }


def duplicar_apu(id_apu: int, token: dict, client_ip: str, data: dict = None):
    apu = _validar_apu(id_apu, token, permitir_base=True)
    id_empresa = _resolver_empresa(token, (data or {}).get("id_empresa"))
    nuevo_cod = (data or {}).get("codigo")

    nuevo_id = apu_repos.duplicar_apu(id_apu, id_empresa, nuevo_cod)
    dup = apu_repos.obtener_apu_detalle(nuevo_id)

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="DUPLICAR_APU",
        descripcion=f"APU ID {id_apu} duplicado a nuevo APU '{dup['codigo']}'.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {
        "success": True,
        "message": f"APU duplicado como '{dup['nombre']}'.",
        "data": dup
    }


def cambiar_estado_apu(id_apu: int, nuevo_estado: str, token: dict, client_ip: str):
    apu = _validar_apu(id_apu, token, permitir_base=False)
    estado_normalizado = nuevo_estado.strip().upper()
    if estado_normalizado not in ("ACTIVO", "INACTIVO"):
        raise ApuError("Estado no válido. Debe ser ACTIVO o INACTIVO.")

    apu_repos.cambiar_estado_apu(id_apu, estado_normalizado)

    bitacora_repos.registrar_bitacora(
        id_usuario=_usuario_id(token),
        modulo="Modulo_presupuestos",
        accion="CAMBIAR_ESTADO_APU",
        descripcion=f"APU '{apu['codigo']}' cambió su estado a {estado_normalizado}.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return {
        "success": True,
        "message": f"APU {'activado' if estado_normalizado == 'ACTIVO' else 'desactivado'} correctamente."
    }


# ─────────────────────────────────────────────────────────────────────────────
# Gestión de Componentes
# ─────────────────────────────────────────────────────────────────────────────

def agregar_componente(id_apu: int, data: dict, token: dict, client_ip: str):
    apu = _validar_apu(id_apu, token, permitir_base=False)

    tipo = (data.get("tipo_recurso") or "").strip().upper()
    if tipo not in ("MATERIAL", "MANO_OBRA", "EQUIPO"):
        raise ApuError("El tipo de recurso debe ser MATERIAL, MANO_OBRA o EQUIPO.")

    desc = (data.get("descripcion_recurso") or "").strip()
    if not desc:
        raise ApuError("La descripción del recurso es obligatoria.")

    id_um = data.get("id_unidad_medida")
    if not id_um:
        raise ApuError("La unidad de medida es obligatoria.")

    rend = float(data.get("rendimiento") or data.get("cantidad") or 1.0)
    pu = float(data.get("precio_unitario") or 0.0)

    id_comp = apu_repos.agregar_componente_apu(
        id_apu=id_apu,
        tipo_recurso=tipo,
        descripcion_recurso=desc,
        id_unidad_medida=int(id_um),
        rendimiento=rend,
        precio_unitario=pu,
        id_recurso=data.get("id_recurso"),
        id_material=data.get("id_material"),
        id_mano_obra=data.get("id_mano_obra"),
        id_equipo=data.get("id_equipo")
    )

    apu_act = apu_repos.obtener_apu_detalle(id_apu)
    return {
        "success": True,
        "message": "Componente agregado al APU.",
        "id_componente": id_comp,
        "apu": apu_act
    }


def actualizar_componente(id_apu: int, id_componente: int, data: dict, token: dict, client_ip: str):
    _validar_apu(id_apu, token, permitir_base=False)

    tipo = (data.get("tipo_recurso") or "").strip().upper()
    desc = (data.get("descripcion_recurso") or "").strip()
    id_um = data.get("id_unidad_medida")
    rend = float(data.get("rendimiento") or data.get("cantidad") or 1.0)
    pu = float(data.get("precio_unitario") or 0.0)

    apu_repos.actualizar_componente_apu(
        id_componente=id_componente,
        tipo_recurso=tipo,
        descripcion_recurso=desc,
        id_unidad_medida=int(id_um),
        rendimiento=rend,
        precio_unitario=pu,
        id_recurso=data.get("id_recurso"),
        id_material=data.get("id_material"),
        id_mano_obra=data.get("id_mano_obra"),
        id_equipo=data.get("id_equipo")
    )

    apu_act = apu_repos.obtener_apu_detalle(id_apu)
    return {
        "success": True,
        "message": "Componente actualizado correctamente.",
        "apu": apu_act
    }


def eliminar_componente(id_apu: int, id_componente: int, token: dict, client_ip: str):
    _validar_apu(id_apu, token, permitir_base=False)

    apu_repos.eliminar_componente_apu(id_componente)
    apu_act = apu_repos.obtener_apu_detalle(id_apu)

    return {
        "success": True,
        "message": "Componente eliminado del APU.",
        "apu": apu_act
    }


# ─────────────────────────────────────────────────────────────────────────────
# Recursos auxiliares y correlativos
# ─────────────────────────────────────────────────────────────────────────────

def listar_materiales_catalogo(token: dict, q: str = None, id_empresa_req: int = None):
    id_empresa = _resolver_empresa(token, id_empresa_req)
    mats = apu_repos.listar_materiales_empresa(id_empresa, q)
    return {"success": True, "data": mats}


def listar_mano_obra_catalogo(token: dict, q: str = None, id_empresa_req: int = None):
    id_empresa = _resolver_empresa(token, id_empresa_req)
    mo = apu_repos.listar_mano_obra_empresa(id_empresa, q)
    return {"success": True, "data": mo}


def listar_equipos_catalogo(token: dict, q: str = None, id_empresa_req: int = None):
    id_empresa = _resolver_empresa(token, id_empresa_req)
    eq = apu_repos.listar_equipos_empresa(id_empresa, q)
    return {"success": True, "data": eq}


def listar_unidades_medida():
    ums = apu_repos.listar_unidades_medida()
    return {"success": True, "data": ums}


def sugerir_codigo_apu(token: dict, id_empresa_req: int = None):
    id_empresa = _resolver_empresa(token, id_empresa_req)
    cod = apu_repos.generar_codigo_siguiente_apu(id_empresa)
    return {"success": True, "codigo": cod}
