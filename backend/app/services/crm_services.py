import re
from app.classes.postgres import PostgreSQL
from app.config import Config
from app.repos import bitacora_repos, crm_repos
from app.utils.security import es_admin_sistema


# ─────────────────────────────────────────────────────────────────────────────
# Constantes de Negocio CRM
# ─────────────────────────────────────────────────────────────────────────────
TIPOS_CLIENTE = {"PROSPECTO", "CLIENTE"}

ESTADOS_PROSPECTO = {
    "NUEVO", "CONTACTADO", "INTERESADO", "NEGOCIACION", "EN_NEGOCIACION", "RESERVADO", "VENDIDO", "CONVERTIDO", "PERDIDO"
}

ESTADOS_CLIENTE = {
    "ACTIVO", "INACTIVO", "NUEVO", "CONTACTADO", "INTERESADO", "NEGOCIACION", "EN_NEGOCIACION", "RESERVADO", "VENDIDO"
}

ORIGENES_VALIDOS = {
    "DIRECTO", "WEB", "REFERIDO", "REDES_SOCIALES", "VISITA_OBRA", "LLAMADA", "OTRO"
}

TIPOS_INTERACCION = {
    "LLAMADA", "MENSAJE", "REUNION", "VISITA", "CONSULTA", "SEGUIMIENTO", "OBSERVACION", "OBSERVACIONES", "CORREO", "NOTA", "OTRO"
}

ESTADOS_ASOCIACION_UNIDAD = {
    "INTERESADO", "RESERVADO", "VENDIDO", "ENTREGADO", "CANCELADO"
}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ─────────────────────────────────────────────────────────────────────────────
# Excepción propia del módulo CRM
# ─────────────────────────────────────────────────────────────────────────────
class CrmError(ValueError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de validación y contexto multiempresa
# ─────────────────────────────────────────────────────────────────────────────
def _empresa(token: dict, id_empresa_solicitada=None, obligatorio: bool = True):
    """
    Resuelve y valida estrictamente el id_empresa para aislar los datos.
    - Administrador global: puede operar sobre la empresa solicitada (validando existencia)
      o su empresa por defecto.
    - Usuario de empresa: estrictamente atado a token['id_empresa'].
    """
    es_admin = es_admin_sistema(token)
    if es_admin:
        if id_empresa_solicitada is not None and str(id_empresa_solicitada).strip() != "":
            try:
                emp_id = int(id_empresa_solicitada)
                # Validar existencia real de la empresa
                db = PostgreSQL()
                db.create_connection()
                try:
                    existe = db.execute_query(
                        f"SELECT 1 FROM {Config.SCHEMA}.t_empresa WHERE id_empresa = %s;",
                        (emp_id,), fetchone=True
                    )
                    if not existe:
                        raise CrmError(f"La empresa ID {emp_id} no existe.", 404)
                finally:
                    db.close_connection()
                return emp_id
            except (ValueError, TypeError):
                raise CrmError("El ID de empresa proporcionado no es válido.", 400)
        if not obligatorio:
            return None
        return token.get("id_empresa") or 1

    empresa_usuario = token.get("id_empresa")
    if not empresa_usuario:
        raise CrmError("El token no identifica una empresa autorizada.", 403)

    if id_empresa_solicitada is not None and str(id_empresa_solicitada).strip() != "":
        try:
            if int(id_empresa_solicitada) != int(empresa_usuario):
                raise CrmError("Acceso no autorizado a datos de otra empresa.", 403)
        except (ValueError, TypeError):
            raise CrmError("El ID de empresa proporcionado no es válido.", 400)

    return empresa_usuario


def _validar_usuario_empresa(id_usuario: int, id_empresa: int):
    if not id_usuario:
        return None
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            f"SELECT 1 FROM {Config.SCHEMA}.t_usuario WHERE id_usuario = %s AND id_empresa = %s;",
            (id_usuario, id_empresa), fetchone=True
        )
        if not row:
            raise CrmError(f"El usuario ID {id_usuario} no pertenece a la empresa autorizada.", 403)
        return id_usuario
    finally:
        db.close_connection()


def _log(token: dict, accion: str, descripcion: str, ip: str, estado: str = "EXITOSO"):
    try:
        bitacora_repos.registrar_bitacora(
            id_usuario=token.get("nro_usuario"),
            modulo="CRM",
            accion=accion,
            descripcion=descripcion,
            ip=ip or "unknown",
            estado=estado
        )
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# 1. LISTAR CLIENTES / PROSPECTOS
# ─────────────────────────────────────────────────────────────────────────────
def listar(token: dict, tipo_cliente: str = None, estado: str = None, q: str = None,
           id_usuario_asignado: int = None, page: int = 1, limit: int = 20, id_empresa_solicitada=None):
    emp_id = _empresa(token, id_empresa_solicitada, obligatorio=not es_admin_sistema(token))
    return crm_repos.listar_clientes(
        id_empresa=emp_id,
        tipo_cliente=tipo_cliente,
        estado=estado,
        q=q,
        id_usuario_asignado=id_usuario_asignado,
        page=page,
        limit=limit
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. OBTENER DETALLE E HISTORIAL COMPLETO (HU81)
# ─────────────────────────────────────────────────────────────────────────────
def obtener_detalle_historial(id_cliente: int, token: dict, id_empresa_solicitada=None):
    emp_id = _empresa(token, id_empresa_solicitada, obligatorio=not es_admin_sistema(token))
    cliente = crm_repos.obtener_cliente_por_id(id_cliente, emp_id)
    if not cliente:
        raise CrmError(f"Cliente con ID {id_cliente} no encontrado en la empresa autorizada.", 404)

    interacciones = crm_repos.listar_interacciones_cliente(id_cliente)
    unidades = crm_repos.listar_unidades_cliente(id_cliente)

    return {
        "success": True,
        "data": {
            "cliente": cliente,
            "interacciones": interacciones,
            "unidades_asociadas": unidades
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. REGISTRAR CLIENTE / PROSPECTO (HU80, HU82)
# ─────────────────────────────────────────────────────────────────────────────
def registrar(data: dict, token: dict, ip: str, id_empresa_solicitada=None):
    emp_id = _empresa(token, id_empresa_solicitada, obligatorio=True)

    # 1. Datos personales obligatorios
    nombre_completo = str(data.get("nombre_completo") or "").strip()
    if not nombre_completo:
        raise CrmError("El nombre completo del cliente/prospecto es obligatorio.")

    ci = str(data.get("ci") or "").strip() or None
    telefono = str(data.get("telefono") or "").strip() or None
    telefono_ref = str(data.get("telefono_ref") or "").strip() or None
    direccion = str(data.get("direccion") or "").strip() or None
    ubicacion = str(data.get("ubicacion") or "").strip() or None
    email = str(data.get("email") or "").strip() or None

    if email and not _EMAIL_RE.match(email):
        raise CrmError("El formato de correo electrónico no es válido.")

    # 2. Clasificación
    tipo_cliente = str(data.get("tipo_cliente") or "PROSPECTO").strip().upper()
    if tipo_cliente not in TIPOS_CLIENTE:
        raise CrmError(f"Tipo de cliente no válido. Debe ser uno de: {', '.join(TIPOS_CLIENTE)}")

    estado = str(data.get("estado") or ("NUEVO" if tipo_cliente == "PROSPECTO" else "ACTIVO")).strip().upper()
    if tipo_cliente == "PROSPECTO" and estado not in ESTADOS_PROSPECTO:
        raise CrmError(f"Estado de prospecto no válido. Debe ser uno de: {', '.join(ESTADOS_PROSPECTO)}")
    elif tipo_cliente == "CLIENTE" and estado not in ESTADOS_CLIENTE:
        raise CrmError(f"Estado de cliente comercial no válido. Debe ser uno de: {', '.join(ESTADOS_CLIENTE)}")

    # 3. Datos comerciales
    origen = str(data.get("origen") or "DIRECTO").strip().upper()
    if origen not in ORIGENES_VALIDOS:
        origen = "OTRO"

    presupuesto_estimado = data.get("presupuesto_estimado")
    if presupuesto_estimado is not None and str(presupuesto_estimado).strip() != "":
        try:
            presupuesto_estimado = float(presupuesto_estimado)
            if presupuesto_estimado < 0:
                raise CrmError("El presupuesto estimado no puede ser negativo.")
        except (ValueError, TypeError):
            raise CrmError("El presupuesto estimado debe ser un valor numérico válido.")
    else:
        presupuesto_estimado = None

    notas = str(data.get("notas") or "").strip() or None

    id_usuario_asignado = data.get("id_usuario_asignado")
    if id_usuario_asignado:
        try:
            id_usuario_asignado = int(id_usuario_asignado)
            _validar_usuario_empresa(id_usuario_asignado, emp_id)
        except (ValueError, TypeError):
            id_usuario_asignado = None

    # 4. Gestión de Persona en `t_persona` (Reutilizar si ya existe por CI)
    id_persona = None
    if ci:
        persona_existente = crm_repos.buscar_persona_por_ci(ci)
        if persona_existente:
            id_persona = persona_existente["id_persona"]
            # Actualizar datos de contacto si cambiaron
            crm_repos.actualizar_persona(
                id_persona,
                nombre_completo=nombre_completo,
                telefono=telefono,
                telefono_ref=telefono_ref,
                direccion=direccion,
                ubicacion=ubicacion
            )

    if not id_persona:
        id_persona = crm_repos.crear_persona(
            nombre_completo=nombre_completo,
            ci=ci,
            telefono=telefono,
            telefono_ref=telefono_ref,
            direccion=direccion,
            ubicacion=ubicacion
        )

    # 5. Validar unicidad (id_empresa, id_persona)
    db = PostgreSQL()
    db.create_connection()
    try:
        ya_existe = db.execute_query(
            f"SELECT id_cliente FROM {Config.SCHEMA}.t_crm_cliente WHERE id_empresa = %s AND id_persona = %s;",
            (emp_id, id_persona), fetchone=True
        )
        if ya_existe:
            raise CrmError("Esta persona ya se encuentra registrada en el CRM de esta empresa.", 409)
    finally:
        db.close_connection()

    # 6. Registrar en `t_crm_cliente`
    id_cliente = crm_repos.crear_cliente_crm(
        id_empresa=emp_id,
        id_persona=id_persona,
        email=email,
        tipo_cliente=tipo_cliente,
        estado=estado,
        origen=origen,
        presupuesto_estimado=presupuesto_estimado,
        notas=notas,
        id_usuario_asignado=id_usuario_asignado
    )

    accion_log = "CREAR_CLIENTE" if tipo_cliente == "CLIENTE" else "CREAR_PROSPECTO"
    _log(token, accion_log, f"{tipo_cliente} '{nombre_completo}' registrado con ID {id_cliente}.", ip)

    return {
        "success": True,
        "message": f"{'Cliente comercial' if tipo_cliente == 'CLIENTE' else 'Prospecto'} registrado exitosamente.",
        "id_cliente": id_cliente
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. ACTUALIZAR CLIENTE (HU80, HU81)
# ─────────────────────────────────────────────────────────────────────────────
def actualizar(id_cliente: int, data: dict, token: dict, ip: str, id_empresa_solicitada=None):
    emp_id = _empresa(token, id_empresa_solicitada, obligatorio=True)
    cliente = crm_repos.obtener_cliente_por_id(id_cliente, emp_id)
    if not cliente:
        raise CrmError(f"Cliente con ID {id_cliente} no encontrado en la empresa autorizada.", 404)

    # Datos personales
    id_persona = cliente["id_persona"]
    nombre_completo = data.get("nombre_completo")
    ci = data.get("ci")
    telefono = data.get("telefono")
    telefono_ref = data.get("telefono_ref")
    direccion = data.get("direccion")
    ubicacion = data.get("ubicacion")

    crm_repos.actualizar_persona(
        id_persona,
        nombre_completo=str(nombre_completo).strip() if nombre_completo is not None else None,
        ci=str(ci).strip() if ci is not None else None,
        telefono=str(telefono).strip() if telefono is not None else None,
        telefono_ref=str(telefono_ref).strip() if telefono_ref is not None else None,
        direccion=str(direccion).strip() if direccion is not None else None,
        ubicacion=str(ubicacion).strip() if ubicacion is not None else None
    )

    # Datos comerciales
    email = data.get("email")
    if email and not _EMAIL_RE.match(str(email).strip()):
        raise CrmError("El formato de correo electrónico no es válido.")

    origen = data.get("origen")
    if origen and str(origen).strip().upper() not in ORIGENES_VALIDOS:
        origen = "OTRO"

    presupuesto_estimado = data.get("presupuesto_estimado")
    if presupuesto_estimado is not None and str(presupuesto_estimado).strip() != "":
        try:
            presupuesto_estimado = float(presupuesto_estimado)
        except (ValueError, TypeError):
            raise CrmError("El presupuesto estimado debe ser un valor numérico válido.")

    notas = data.get("notas")
    id_usuario_asignado = data.get("id_usuario_asignado")
    if id_usuario_asignado:
        try:
            id_usuario_asignado = int(id_usuario_asignado)
            _validar_usuario_empresa(id_usuario_asignado, emp_id)
        except (ValueError, TypeError):
            id_usuario_asignado = None

    crm_repos.actualizar_cliente_crm(
        id_cliente,
        emp_id,
        email=str(email).strip() if email is not None else None,
        origen=str(origen).strip().upper() if origen is not None else None,
        presupuesto_estimado=presupuesto_estimado,
        notas=str(notas).strip() if notas is not None else None,
        id_usuario_asignado=id_usuario_asignado
    )

    _log(token, "MODIFICAR_CLIENTE", f"Cliente ID {id_cliente} modificado.", ip)
    return {"success": True, "message": "Datos actualizados exitosamente."}


# ─────────────────────────────────────────────────────────────────────────────
# 5. CLASIFICAR PROSPECTO / CONVERTIR A CLIENTE (HU83)
# ─────────────────────────────────────────────────────────────────────────────
def clasificar_prospecto(id_cliente: int, nuevo_estado: str, token: dict, ip: str, id_empresa_solicitada=None, nota: str = None):
    emp_id = _empresa(token, id_empresa_solicitada, obligatorio=True)
    cliente = crm_repos.obtener_cliente_por_id(id_cliente, emp_id)
    if not cliente:
        raise CrmError(f"Cliente con ID {id_cliente} no encontrado en la empresa autorizada.", 404)

    estado_upper = str(nuevo_estado or "").strip().upper()
    if estado_upper == "EN_NEGOCIACION":
        estado_upper = "NEGOCIACION"

    estado_anterior = cliente["estado"]
    tipo_actual = cliente["tipo_cliente"]

    # Transición a CLIENTE (Venta concretada o conversión explícita)
    if estado_upper in ("CONVERTIDO", "CLIENTE", "VENDIDO", "RESERVADO") and tipo_actual == "PROSPECTO":
        nuevo_tipo = "CLIENTE"
        estado_final = "ACTIVO" if estado_upper in ("CONVERTIDO", "CLIENTE") else estado_upper
        ok = crm_repos.cambiar_clasificacion_crm(id_cliente, emp_id, nuevo_tipo, estado_final)
        if not ok:
            raise CrmError("No se pudo actualizar la clasificación del cliente.")

        # Registrar automáticamente en el historial cronológico
        id_usuario = token.get("nro_usuario") or cliente.get("id_usuario_asignado")
        if id_usuario:
            crm_repos.registrar_interaccion(
                id_cliente=id_cliente,
                id_usuario=id_usuario,
                tipo="SEGUIMIENTO",
                asunto=f"Evolución comercial: {estado_anterior} -> {estado_final} ({nuevo_tipo})",
                detalle=nota.strip() if nota and str(nota).strip() else f"El prospecto avanzó a {nuevo_tipo} ({estado_final}) en el pipeline comercial."
            )

        _log(token, "CONVERTIR_PROSPECTO_CLIENTE", f"Prospecto ID {id_cliente} convertido a {nuevo_tipo} / {estado_final}.", ip)
        return {
            "success": True,
            "message": f"Cliente comercial actualizado a {estado_final}.",
            "tipo_cliente": nuevo_tipo,
            "estado": estado_final
        }

    if tipo_actual == "PROSPECTO":
        if estado_upper not in ESTADOS_PROSPECTO:
            raise CrmError(f"Estado no válido para prospecto. Debe ser uno de: {', '.join(sorted(ESTADOS_PROSPECTO))}")
        ok = crm_repos.cambiar_clasificacion_crm(id_cliente, emp_id, "PROSPECTO", estado_upper)
        if not ok:
            raise CrmError("No se pudo actualizar el estado del prospecto.")

        # Registrar automáticamente en el historial cronológico
        id_usuario = token.get("nro_usuario") or cliente.get("id_usuario_asignado")
        if id_usuario:
            crm_repos.registrar_interaccion(
                id_cliente=id_cliente,
                id_usuario=id_usuario,
                tipo="SEGUIMIENTO",
                asunto=f"Avance comercial: {estado_anterior} -> {estado_upper}",
                detalle=nota.strip() if nota and str(nota).strip() else f"El prospecto avanzó de {estado_anterior} a {estado_upper} en el pipeline comercial."
            )

        _log(token, "CAMBIAR_ESTADO_PROSPECTO", f"Prospecto ID {id_cliente} cambió de estado a {estado_upper}.", ip)
        return {
            "success": True,
            "message": f"Estado de prospecto actualizado a {estado_upper}.",
            "tipo_cliente": "PROSPECTO",
            "estado": estado_upper
        }
    else:
        if estado_upper not in ESTADOS_CLIENTE:
            raise CrmError(f"Estado no válido para cliente comercial. Debe ser uno de: {', '.join(sorted(ESTADOS_CLIENTE))}")
        ok = crm_repos.cambiar_clasificacion_crm(id_cliente, emp_id, "CLIENTE", estado_upper)
        if not ok:
            raise CrmError("No se pudo actualizar el estado del cliente comercial.")

        # Registrar automáticamente en el historial cronológico
        id_usuario = token.get("nro_usuario") or cliente.get("id_usuario_asignado")
        if id_usuario:
            crm_repos.registrar_interaccion(
                id_cliente=id_cliente,
                id_usuario=id_usuario,
                tipo="SEGUIMIENTO",
                asunto=f"Avance comercial: {estado_anterior} -> {estado_upper}",
                detalle=nota.strip() if nota and str(nota).strip() else f"El cliente comercial avanzó de {estado_anterior} a {estado_upper}."
            )

        _log(token, "CAMBIAR_ESTADO_CLIENTE", f"Cliente ID {id_cliente} cambió de estado a {estado_upper}.", ip)
        return {
            "success": True,
            "message": f"Estado de cliente comercial actualizado a {estado_upper}.",
            "tipo_cliente": "CLIENTE",
            "estado": estado_upper
        }


# ─────────────────────────────────────────────────────────────────────────────
# 6. REGISTRAR INTERACCIÓN COMERCIAL (HU84)
# ─────────────────────────────────────────────────────────────────────────────
def registrar_interaccion(id_cliente: int, data: dict, token: dict, ip: str, id_empresa_solicitada=None):
    emp_id = _empresa(token, id_empresa_solicitada, obligatorio=True)
    cliente = crm_repos.obtener_cliente_por_id(id_cliente, emp_id)
    if not cliente:
        raise CrmError(f"Cliente con ID {id_cliente} no encontrado en la empresa autorizada.", 404)

    id_usuario = token.get("nro_usuario")
    if not id_usuario:
        raise CrmError("No se puede identificar el usuario responsable de la interacción.", 401)

    tipo = str(data.get("tipo") or "LLAMADA").strip().upper()
    if tipo not in TIPOS_INTERACCION:
        tipo = "OTRO"

    asunto = str(data.get("asunto") or "").strip()
    if not asunto:
        raise CrmError("El asunto de la interacción es obligatorio.")

    detalle = str(data.get("detalle") or "").strip()
    if not detalle:
        raise CrmError("El detalle de la interacción es obligatorio.")

    fecha_interaccion = data.get("fecha_interaccion") or None
    fecha_proximo_contacto = data.get("fecha_proximo_contacto") or None

    id_interaccion = crm_repos.registrar_interaccion(
        id_cliente=id_cliente,
        id_usuario=id_usuario,
        tipo=tipo,
        asunto=asunto,
        detalle=detalle,
        fecha_interaccion=fecha_interaccion,
        fecha_proximo_contacto=fecha_proximo_contacto
    )

    _log(token, "REGISTRAR_INTERACCION", f"Interacción tipo {tipo} registrada para cliente ID {id_cliente}.", ip)
    return {
        "success": True,
        "message": "Interacción comercial registrada exitosamente.",
        "id_interaccion": id_interaccion
    }


# ─────────────────────────────────────────────────────────────────────────────
# 7. ASOCIAR CLIENTE CON UNIDAD INMOBILIARIA (HU85)
# ─────────────────────────────────────────────────────────────────────────────
def asociar_unidad(id_cliente: int, data: dict, token: dict, ip: str, id_empresa_solicitada=None):
    emp_id = _empresa(token, id_empresa_solicitada, obligatorio=True)

    # 1. Validar cliente
    cliente = crm_repos.obtener_cliente_por_id(id_cliente, emp_id)
    if not cliente:
        raise CrmError(f"Cliente con ID {id_cliente} no encontrado en la empresa autorizada.", 404)

    id_unidad = data.get("id_unidad")
    if not id_unidad:
        raise CrmError("El ID de la unidad es obligatorio.")
    try:
        id_unidad = int(id_unidad)
    except (ValueError, TypeError):
        raise CrmError("El ID de la unidad debe ser un número entero válido.")

    # 2. Validar que la unidad pertenece a la misma empresa autorizada
    info_unidad = crm_repos.obtener_empresa_unidad(id_unidad)
    if not info_unidad:
        raise CrmError(f"La unidad ID {id_unidad} no existe en el sistema.", 404)

    if int(info_unidad["id_empresa"]) != int(emp_id):
        raise CrmError("Violación de aislamiento multitenant: la unidad pertenece a otra empresa.", 403)

    # 3. Validar estado de asociación
    estado_asociacion = str(data.get("estado_asociacion") or "INTERESADO").strip().upper()
    if estado_asociacion not in ESTADOS_ASOCIACION_UNIDAD:
        raise CrmError(f"Estado de asociación no válido. Opciones: {', '.join(ESTADOS_ASOCIACION_UNIDAD)}")

    monto_pactado = data.get("monto_pactado")
    if monto_pactado is not None and str(monto_pactado).strip() != "":
        try:
            monto_pactado = float(monto_pactado)
            if monto_pactado < 0:
                raise CrmError("El monto pactado no puede ser negativo.")
        except (ValueError, TypeError):
            raise CrmError("El monto pactado debe ser numérico.")
    else:
        monto_pactado = None

    observaciones = str(data.get("observaciones") or "").strip() or None

    # 4. Validar disponibilidad si se intenta reservar o vender
    if estado_asociacion in ("RESERVADO", "VENDIDO"):
        db = PostgreSQL()
        db.create_connection()
        try:
            ocupada = db.execute_query(
                f"""SELECT id_cliente FROM {Config.SCHEMA}.t_crm_cliente_unidad 
                    WHERE id_unidad = %s AND estado_asociacion IN ('RESERVADO', 'VENDIDO') AND id_cliente != %s;""",
                (id_unidad, id_cliente), fetchone=True
            )
            if ocupada:
                raise CrmError("La unidad ya cuenta con una reserva o venta activa con otro cliente.", 409)
        finally:
            db.close_connection()

    try:
        id_asoc = crm_repos.asociar_cliente_unidad(
            id_cliente=id_cliente,
            id_unidad=id_unidad,
            estado_asociacion=estado_asociacion,
            monto_pactado=monto_pactado,
            observaciones=observaciones
        )
    except Exception as exc:
        if "uq_crm_unidad_reservada_vendida" in str(exc):
            raise CrmError("La unidad ya tiene una reserva o venta activa.", 409)
        if "uq_crm_cliente_unidad_activa" in str(exc):
            raise CrmError("El cliente ya tiene una asociación activa para esta misma unidad.", 409)
        raise CrmError(f"Error al asociar la unidad: {exc}")

    _log(token, "ASOCIAR_CLIENTE_UNIDAD",
         f"Unidad {info_unidad['codigo_unidad']} asociada a cliente ID {id_cliente} ({estado_asociacion}).", ip)

    # Registrar automáticamente en historial cronológico del cliente
    id_usuario = token.get("nro_usuario") or cliente.get("id_usuario_asignado")
    if id_usuario:
        asunto_it = f"Unidad {info_unidad['codigo_unidad']} asociada ({estado_asociacion})"
        det_it = f"Se asoció la unidad {info_unidad['codigo_unidad']} ({info_unidad['tipo_unidad']}) del proyecto {info_unidad['nombre_obra']} en estado {estado_asociacion}."
        if monto_pactado:
            det_it += f" Monto pactado: ${monto_pactado:,.2f}."
        if observaciones:
            det_it += f" Observaciones: {observaciones}."
        crm_repos.registrar_interaccion(
            id_cliente=id_cliente,
            id_usuario=id_usuario,
            tipo="SEGUIMIENTO",
            asunto=asunto_it,
            detalle=det_it
        )

    return {
        "success": True,
        "message": "Unidad asociada al cliente exitosamente.",
        "id_cliente_unidad": id_asoc
    }


def cambiar_estado_asociacion(id_cliente_unidad: int, nuevo_estado: str, observaciones: str, token: dict, ip: str, id_empresa_solicitada=None):
    emp_id = _empresa(token, id_empresa_solicitada, obligatorio=True)
    estado_upper = str(nuevo_estado or "").strip().upper()
    if estado_upper not in ESTADOS_ASOCIACION_UNIDAD:
        raise CrmError(f"Estado no válido. Opciones: {', '.join(ESTADOS_ASOCIACION_UNIDAD)}")

    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            f"""SELECT cu.id_cliente, c.id_empresa, cu.id_unidad, u.codigo AS codigo_unidad, o.nombre AS nombre_obra
                FROM {Config.SCHEMA}.t_crm_cliente_unidad cu
                INNER JOIN {Config.SCHEMA}.t_crm_cliente c ON c.id_cliente = cu.id_cliente
                INNER JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = cu.id_unidad
                INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
                INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
                WHERE cu.id_cliente_unidad = %s;""",
            (id_cliente_unidad,), fetchone=True
        )
        if not row:
            raise CrmError(f"Asociación ID {id_cliente_unidad} no encontrada.", 404)
        if int(row[1]) != int(emp_id):
            raise CrmError("Acceso no autorizado a datos de otra empresa.", 403)

        id_cliente_asoc = row[0]
        id_unidad_asoc = row[2]
        codigo_unidad = row[3]
        nombre_obra = row[4]

        # Validar colisión si el nuevo estado es RESERVADO o VENDIDO
        if estado_upper in ("RESERVADO", "VENDIDO"):
            ocupada = db.execute_query(
                f"""SELECT id_cliente FROM {Config.SCHEMA}.t_crm_cliente_unidad 
                    WHERE id_unidad = %s AND estado_asociacion IN ('RESERVADO', 'VENDIDO') 
                      AND id_cliente_unidad != %s;""",
                (id_unidad_asoc, id_cliente_unidad), fetchone=True
            )
            if ocupada:
                raise CrmError("La unidad ya cuenta con una reserva o venta activa con otro cliente.", 409)
    finally:
        db.close_connection()

    try:
        res = crm_repos.cambiar_estado_asociacion_unidad(id_cliente_unidad, estado_upper, observaciones)
        if not res:
            raise CrmError("No se pudo actualizar el estado de la asociación.")
    except Exception as exc:
        if "uq_crm_unidad_reservada_vendida" in str(exc):
            raise CrmError("La unidad ya cuenta con una reserva o venta activa en el sistema.", 409)
        raise CrmError(f"Error al actualizar la unidad: {exc}")

    # Registrar automáticamente en historial del cliente
    id_usuario = token.get("nro_usuario")
    if id_usuario:
        det_it = f"El estado de la unidad {codigo_unidad} ({nombre_obra}) cambió a {estado_upper}."
        if observaciones:
            det_it += f" Observaciones: {observaciones}."
        crm_repos.registrar_interaccion(
            id_cliente=id_cliente_asoc,
            id_usuario=id_usuario,
            tipo="SEGUIMIENTO",
            asunto=f"Unidad {codigo_unidad} actualizada a {estado_upper}",
            detalle=det_it
        )

    _log(token, "CAMBIAR_ESTADO_ASOCIACION", f"Asociación ID {id_cliente_unidad} actualizada a {estado_upper}.", ip)
    return {"success": True, "message": f"Estado de asociación actualizado a {estado_upper}."}


def listar_unidades_disponibles(token: dict, id_obra: int = None, id_empresa_solicitada=None):
    emp_id = _empresa(token, id_empresa_solicitada, obligatorio=True)
    return {
        "success": True,
        "data": crm_repos.listar_unidades_disponibles_empresa(emp_id, id_obra)
    }


# ─────────────────────────────────────────────────────────────────────────────
# 8. MÉTRICAS CRM (HU109)
# ─────────────────────────────────────────────────────────────────────────────
def obtener_metricas(token: dict, id_empresa_solicitada=None):
    emp_id = _empresa(token, id_empresa_solicitada, obligatorio=True)
    return {
        "success": True,
        "data": crm_repos.obtener_metricas_crm(emp_id)
    }


# ─────────────────────────────────────────────────────────────────────────────
# 9. ASESORES / RESPONSABLES COMERCIALES (HU80, HU82)
# ─────────────────────────────────────────────────────────────────────────────
def listar_asesores(token: dict, id_empresa_solicitada=None):
    emp_id = _empresa(token, id_empresa_solicitada, obligatorio=True)
    return {
        "success": True,
        "data": crm_repos.listar_asesores_empresa(emp_id)
    }

