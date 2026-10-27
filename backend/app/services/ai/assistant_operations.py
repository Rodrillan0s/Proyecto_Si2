"""Módulo de asistencia operativa segura para el Asistente Inteligente (CU29).
Implementa el flujo de dos pasos: Propuesta con Vista Previa Tipada -> Confirmación Explícita -> Ejecución Reautorizada.
Prohíbe estrictamente eliminaciones, cambios de roles/permisos, pagos y restauraciones de BD.
"""
from datetime import datetime, timedelta
import threading
from typing import Any, Literal
from uuid import uuid4
from fastapi import HTTPException
from pydantic import BaseModel, Field, ValidationError

from app.repos import reportes_repos as repo
from app.repos import bitacora_repos
from app.services.reportes.authorization import context
from app.services import suscripcion_policy as subscription

OPERATIONS = {
    'crear_incidencia': ('Registrar_incidencias', 'incidencias'),
    'crear_orden_trabajo': ('Registrar_ordenes_trabajo', 'ordenes_trabajo'),
    'crear_material': ('Registrar_materiales', 'materiales'),
}


def _autorizar_operacion(db, ctx, tipo):
    if tipo not in OPERATIONS:
        raise HTTPException(422, 'Operación no registrada.')
    permission, module = OPERATIONS[tipo]
    ctx.require(permission)
    subscription.exigir_modulo(ctx.empresa, module, db.cur)
    if ctx.rol != 'ADMINISTRADOR':
        subscription.exigir_funcion(ctx.empresa, 'ia', db.cur)


def _contexto_ticket(db, token, propuesta, empresa=None, id_obra_contexto=None):
    if int(token.get('nro_usuario') or 0) != propuesta['id_usuario']:
        raise HTTPException(403, 'No tiene autorización sobre esta propuesta.')
    if token.get('nombre_rol') == 'ADMINISTRADOR' and empresa is None:
        raise HTTPException(422, 'Seleccione explícitamente la empresa de la operación.')
    selected = empresa if empresa is not None else token.get('id_empresa')
    ctx = context(db, propuesta['id_usuario'], selected)
    if ctx.empresa != propuesta['id_empresa'] or (token.get('nombre_rol') and token['nombre_rol'] != ctx.rol):
        raise HTTPException(403, 'La empresa o el rol de la sesión cambió.')
    if propuesta.get('politica') and propuesta['politica'] != ctx.policy():
        raise HTTPException(403, 'La identidad autorizada de la propuesta cambió.')
    if propuesta.get('contexto_obra') != id_obra_contexto:
        raise HTTPException(409, 'La obra de contexto cambió. Prepare una nueva propuesta.')
    return ctx


def _autorizar_obra(db, ctx, id_obra):
    """El alcance procede del repositorio, nunca de un atributo opcional del Context."""
    if id_obra not in {work['id_obra'] for work in repo.works(db, ctx)}:
        raise HTTPException(403, 'La obra no pertenece al ámbito autorizado de la empresa.')


class IncidenciaParams(BaseModel):
    id_obra: int = Field(gt=0, description="Identificador válido de la obra")
    titulo: str = Field(min_length=3, max_length=200)
    descripcion: str | None = Field(default=None, max_length=2000)
    prioridad: Literal["BAJA", "MEDIA", "ALTA", "CRITICA"] = "MEDIA"
    id_unidad: int | None = Field(default=None, gt=0)


class OrdenTrabajoParams(BaseModel):
    id_obra: int = Field(gt=0, description="Identificador válido de la obra")
    tipo_trab: str = Field(min_length=3, max_length=150)
    fecha_inicio: str | None = None
    fecha_fin: str | None = None
    observacion: str | None = Field(default=None, max_length=1000)


class MaterialParams(BaseModel):
    codigo: str = Field(min_length=1, max_length=50)
    nombre_material: str = Field(min_length=2, max_length=200)
    descripcion: str | None = Field(default=None, max_length=1000)
    id_categoria: int = Field(default=1, gt=0)
    id_unidad_medida: int = Field(default=1, gt=0)
    precio: float = Field(default=0.0, ge=0.0)


# Memoria de propuestas con sincronización y ciclo de vida de estados
# Estados: 'PENDIENTE' | 'EJECUTANDO' | 'EJECUTADA' | 'CANCELADA'
_propuestas_lock = threading.Lock()
_propuestas: dict[str, dict[str, Any]] = {}


def _limpiar_expiradas():
    """Limpia propuestas expiradas. DEBE llamarse con _propuestas_lock adquirido."""
    ahora = datetime.now()
    expiradas = [k for k, v in _propuestas.items() if v.get("expira_en") and v["expira_en"] < ahora]
    for k in expiradas:
        _propuestas.pop(k, None)


def proponer_operacion(ctx, tipo_operacion: str, parametros: dict, resumen: str | None = None,
                      id_obra_contexto=None) -> dict:
    """Valida los parámetros de forma estricta, autoriza preliminarmente y almacena la propuesta."""
    tipo = tipo_operacion.strip().lower()

    with _propuestas_lock:
        _limpiar_expiradas()

    if tipo == "crear_incidencia":
        ctx.require("Registrar_incidencias")
        try:
            p_inc = IncidenciaParams(**(parametros or {}))
        except ValidationError as e:
            raise HTTPException(422, f"Parámetros de incidencia inválidos: {e.errors()}")
        
        # Validar pertenencia de la obra a la empresa autorizada
        with repo.transaction(snapshot=True) as db:
            _autorizar_obra(db, ctx, p_inc.id_obra)
            
        entidad = "Incidencia de Obra"
        params_validados = p_inc.model_dump()
        resumen_backend = (
            f"Crear incidencia '{p_inc.titulo}' con prioridad {p_inc.prioridad} "
            f"en obra ID {p_inc.id_obra}."
        )

    elif tipo == "crear_orden_trabajo":
        ctx.require("Registrar_ordenes_trabajo")
        try:
            p_ot = OrdenTrabajoParams(**(parametros or {}))
        except ValidationError as e:
            raise HTTPException(422, f"Parámetros de orden de trabajo inválidos: {e.errors()}")

        with repo.transaction(snapshot=True) as db:
            _autorizar_obra(db, ctx, p_ot.id_obra)

        entidad = "Orden de Trabajo"
        params_validados = p_ot.model_dump()
        resumen_backend = f"Crear orden de trabajo '{p_ot.tipo_trab}' para obra ID {p_ot.id_obra}."

    elif tipo == "crear_material":
        ctx.require("Registrar_materiales")
        try:
            p_mat = MaterialParams(**(parametros or {}))
        except ValidationError as e:
            raise HTTPException(422, f"Parámetros de material inválidos: {e.errors()}")

        entidad = "Material de Catálogo"
        params_validados = p_mat.model_dump()
        resumen_backend = f"Crear material '{p_mat.nombre_material}' ({p_mat.codigo}) en el catálogo de la empresa."

    else:
        raise HTTPException(400, f"La operación '{tipo_operacion}' no está permitida o no es de bajo riesgo.")

    with repo.transaction(snapshot=True) as db:
        ctx = context(db, ctx.usuario, ctx.empresa)
        _autorizar_operacion(db, ctx, tipo)
        if id_obra_contexto is not None:
            _autorizar_obra(db, ctx, id_obra_contexto)
    id_propuesta = str(uuid4())
    ahora = datetime.now()
    expira_en = ahora + timedelta(minutes=15)

    propuesta = {
        "id_propuesta": id_propuesta,
        "tipo_operacion": tipo,
        "entidad": entidad,
        "parametros": params_validados,
        "resumen": resumen_backend,  # Resumen determinista y seguro generado en backend
        "id_usuario": ctx.usuario,
        "id_empresa": ctx.empresa,
        "politica": ctx.policy(),
        "contexto_obra": id_obra_contexto,
        "estado": "PENDIENTE",
        "creado_en": ahora,
        "expira_en": expira_en,
        "resultado": None,
    }

    with _propuestas_lock:
        _propuestas[id_propuesta] = propuesta

    return {
        "id_propuesta": id_propuesta,
        "tipo_operacion": tipo,
        "entidad": entidad,
        "parametros": params_validados,
        "resumen": resumen_backend,
        "requiere_confirmacion": True,
        "expira_en": expira_en.isoformat(),
    }


def cancelar_propuesta(token: dict, id_propuesta: str, ip: str = "unknown", *, empresa=None,
                      id_obra_contexto=None) -> dict:
    """Cancela una propuesta de operación autenticada del usuario."""
    usuario_token = int(token.get("nro_usuario") or 0)
    with _propuestas_lock:
        _limpiar_expiradas()
        propuesta = _propuestas.get(id_propuesta)
        if not propuesta:
            raise HTTPException(404, "La propuesta de operación no existe o ya ha expirado.")

        if usuario_token != propuesta["id_usuario"]:
            raise HTTPException(403, "No tiene autorización para cancelar esta propuesta.")

        with repo.transaction(snapshot=True) as db:
            _contexto_ticket(db, token, propuesta, empresa, id_obra_contexto)

        if propuesta["estado"] != "PENDIENTE":
            raise HTTPException(409, f"La propuesta no está pendiente (estado actual: {propuesta['estado']}).")

        propuesta["estado"] = "CANCELADA"
        _propuestas.pop(id_propuesta, None)

    try:
        bitacora_repos.registrar_bitacora(
            usuario_token, "ASISTENTE_IA", "CANCELAR_OPERACION",
            f"Cancelada propuesta {id_propuesta} de tipo {propuesta['tipo_operacion']}.", ip, "EXITOSO"
        )
    except Exception:
        pass

    return {
        "success": True,
        "id_propuesta": id_propuesta,
        "mensaje": "Operación cancelada exitosamente."
    }


def ejecutar_propuesta(token: dict, id_propuesta: str, ip: str = "unknown", *, empresa=None,
                       id_obra_contexto=None) -> dict:
    """Ejecuta una propuesta validada previamente, verificando reautorización y registrando auditoría."""
    usuario_token = int(token.get("nro_usuario") or 0)

    # 1. Inspección y reclamo atómico del ticket SIN consumir anticipadamente si no es del usuario (M3/M4)
    with _propuestas_lock:
        _limpiar_expiradas()
        propuesta = _propuestas.get(id_propuesta)
        if not propuesta:
            raise HTTPException(404, "La propuesta de operación expiró, fue cancelada o no existe.")

        # Validar propiedad ANTES de alterar el ticket (M3)
        if usuario_token != propuesta["id_usuario"]:
            raise HTTPException(403, "No tiene autorización para confirmar esta propuesta.")

        if propuesta["estado"] != "PENDIENTE":
            raise HTTPException(409, f"La propuesta no está pendiente de ejecución (estado actual: {propuesta['estado']}).")

        # Marcar en ejecución
        propuesta["estado"] = "EJECUTANDO"

    tipo = propuesta["tipo_operacion"]
    params = propuesta["parametros"]
    id_empresa_propuesta = propuesta["id_empresa"]

    # 2. Re-autorización fresca RBAC, tenencia de recurso y restricciones SaaS (A1, A2)
    from app.services import suscripcion_policy

    try:
        with repo.transaction(snapshot=True) as db:
            # Contexto fresco con la empresa objetivo vinculada al ticket
            ctx_fresco = _contexto_ticket(db, token, propuesta, empresa, id_obra_contexto)
            _autorizar_operacion(db, ctx_fresco, tipo)

            # Revalidar permiso RBAC específico de la acción
            if tipo == "crear_incidencia":
                ctx_fresco.require("Registrar_incidencias")
                id_obra = params.get("id_obra")
                obra_row = repo.one(db, "SELECT id_empresa FROM obras.t_obra WHERE id_obra = %s", (id_obra,))
                if not obra_row or obra_row["id_empresa"] != id_empresa_propuesta:
                    raise HTTPException(403, f"La obra {id_obra} no pertenece a la empresa {id_empresa_propuesta} del ticket.")
                _autorizar_obra(db, ctx_fresco, id_obra)

            elif tipo == "crear_orden_trabajo":
                ctx_fresco.require("Registrar_ordenes_trabajo")
                id_obra = params.get("id_obra")
                obra_row = repo.one(db, "SELECT id_empresa FROM obras.t_obra WHERE id_obra = %s", (id_obra,))
                if not obra_row or obra_row["id_empresa"] != id_empresa_propuesta:
                    raise HTTPException(403, f"La obra {id_obra} no pertenece a la empresa {id_empresa_propuesta} del ticket.")
                _autorizar_obra(db, ctx_fresco, id_obra)

            elif tipo == "crear_material":
                ctx_fresco.require("Registrar_materiales")

        # Revalidar política SaaS de escritura sobre la empresa del ticket (A1)
        # La política se comprobó sobre la misma lectura de autorización arriba.

    except Exception:
        # Revertir estado a PENDIENTE en caso de fallo de reautorización o validación previa
        with _propuestas_lock:
            propuesta["estado"] = "PENDIENTE"
        raise

    # 3. Preparar token forzado con la empresa objetivo del ticket (A2)
    token_empresa = dict(token)
    token_empresa["id_empresa"] = id_empresa_propuesta

    resultado = {}
    try:
        if tipo == "crear_incidencia":
            from app.services import incidencia_services
            from app.services.incidencia_services import IncidenciaError

            data_crear = {
                "id_obra": params["id_obra"],
                "titulo": params["titulo"],
                "descripcion": params.get("descripcion") or params["titulo"],
                "prioridad": params.get("prioridad", "MEDIA"),
                "id_unidad": params.get("id_unidad"),
            }
            resp = incidencia_services.registrar(data_crear, token_empresa, ip=ip)
            # El contrato real de incidencia_services.registrar devuelve 'id_incidencia' en raíz (B2)
            id_incidencia = resp.get("id_incidencia")
            resultado = {
                "id_incidencia": id_incidencia,
                "message": resp.get("message", "Incidencia registrada exitosamente."),
            }
            try:
                bitacora_repos.registrar_bitacora(
                    usuario_token, "ASISTENTE_IA", "CREAR_INCIDENCIA",
                    f"Incidencia {id_incidencia} creada por asistente IA para obra {params['id_obra']}.", ip, "EXITOSO"
                )
            except Exception:
                pass

        elif tipo == "crear_orden_trabajo":
            from app.services import orden_Trabajo_services

            data_ot = {
                "id_obra": params["id_obra"],
                "tipo_trab": params["tipo_trab"],
                "fecha_inicio": params.get("fecha_inicio"),
                "fecha_fin": params.get("fecha_fin"),
                "observacion": params.get("observacion") or "Creada mediante Asistente Operativo OBRATEC.",
            }
            # Contrato real: crear_orden_trabajo(data, token_data, client_ip) (A5)
            resp = orden_Trabajo_services.crear_orden_trabajo(data_ot, token_empresa, client_ip=ip)
            orden_nro = resp.get("orden_nro") or resp.get("data", {}).get("orden_nro")
            resultado = {
                "orden_nro": orden_nro,
                "success": True,
                "message": "Orden de trabajo creada exitosamente.",
            }
            try:
                bitacora_repos.registrar_bitacora(
                    usuario_token, "ASISTENTE_IA", "CREAR_ORDEN_TRABAJO",
                    f"Orden de trabajo {orden_nro} creada por asistente IA para obra {params['id_obra']}.", ip, "EXITOSO"
                )
            except Exception:
                pass

        elif tipo == "crear_material":
            from app.services import material_services
            from app.services.material_services import MaterialError

            data_mat = {
                "id_empresa": id_empresa_propuesta,
                "codigo": params["codigo"],
                "nombre_material": params["nombre_material"],
                "descripcion": params.get("descripcion", ""),
                "id_categoria": params.get("id_categoria", 1),
                "id_unidad_medida": params.get("id_unidad_medida", 1),
                "precio": params.get("precio", 0.0),
            }
            # Contrato real: registrar(data, token, ip) (A5)
            resp = material_services.registrar(data_mat, token_empresa, ip=ip)
            id_material = resp.get("id_material")
            resultado = {
                "id_material": id_material,
                "success": True,
                "message": resp.get("message", "Material registrado exitosamente."),
            }
            try:
                bitacora_repos.registrar_bitacora(
                    usuario_token, "ASISTENTE_IA", "CREAR_MATERIAL",
                    f"Material {id_material} ({params['codigo']}) creado por asistente IA.", ip, "EXITOSO"
                )
            except Exception:
                pass

    except Exception as e:
        # Revertir estado a PENDIENTE ante fallos para que el usuario no pierda el contexto ni quede bloqueado
        with _propuestas_lock:
            propuesta["estado"] = "PENDIENTE"

        # Mapeo de errores de dominio para no arrojar 500 (M5)
        status_code = getattr(e, "status_code", None)
        if isinstance(e, HTTPException):
            raise
        if status_code:
            raise HTTPException(status_code, str(e))
        if isinstance(e, ValueError):
            raise HTTPException(400, str(e))
        raise HTTPException(500, f"Error en la ejecución de la operación: {str(e)}")

    # 4. Consumir y cerrar ticket exitosamente
    with _propuestas_lock:
        propuesta["estado"] = "EJECUTADA"
        propuesta["resultado"] = resultado
        _propuestas.pop(id_propuesta, None)

    return {
        "success": True,
        "mensaje": f"{propuesta['entidad']} ejecutada y creada correctamente.",
        "tipo_operacion": tipo,
        "entidad": propuesta["entidad"],
        "resultado": resultado,
    }
