from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from app.repos import bitacora_repos, control_costos_repos


CATEGORIAS_COSTO = {"MATERIAL", "MANO_OBRA", "EQUIPO", "SUBCONTRATO", "OTRO"}
ESTADOS_COSTO = {"REGISTRADO", "ANULADO"}
ESTADOS_ORDEN = {"PENDIENTE", "APROBADA", "RECHAZADA"}
TIPOS_CAMBIO = {
    "AUMENTO_CANTIDAD",
    "DISMINUCION_CANTIDAD",
    "CAMBIO_COSTO",
    "NUEVA_PARTIDA",
    "ELIMINACION_PARTIDA",
}
CENTAVOS = Decimal("0.01")
MILÉSIMAS = Decimal("0.001")


class ControlCostosError(ValueError):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


def _empresa(token):
    value = token.get("id_empresa")
    if not value and token.get("nombre_rol") == "ADMINISTRADOR":
        raise ControlCostosError(
            "Seleccione una empresa activa para operar control de costos.", 403
        )
    if not value:
        raise ControlCostosError("El token no identifica una empresa.", 403)
    return int(value)


def _usuario(token):
    value = token.get("nro_usuario")
    if not value:
        raise ControlCostosError("El token no identifica al usuario.", 403)
    return int(value)


def _texto(value, label, obligatorio=True, max_len=None):
    result = str(value or "").strip()
    if obligatorio and not result:
        raise ControlCostosError(f"{label} es obligatorio.")
    if max_len and len(result) > max_len:
        raise ControlCostosError(f"{label} no puede superar {max_len} caracteres.")
    return result or None


def _decimal(value, label, *, nonnegative=True, scale=None):
    if isinstance(value, bool):
        raise ControlCostosError(f"{label} debe ser un numero valido.")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ControlCostosError(f"{label} debe ser un numero valido.") from exc
    if not result.is_finite():
        raise ControlCostosError(f"{label} debe ser un numero finito.")
    if nonnegative and result < 0:
        raise ControlCostosError(f"{label} no puede ser negativo.")
    if scale is not None:
        result = result.quantize(scale, rounding=ROUND_HALF_UP)
    return result


def _porcentaje(numerador, denominador):
    denominator = Decimal(denominador or 0)
    if denominator == 0:
        return None
    return (Decimal(numerador or 0) * Decimal("100") / denominator).quantize(
        CENTAVOS, rounding=ROUND_HALF_UP
    )


def _log(token, action, description, ip):
    bitacora_repos.registrar_bitacora(
        _usuario(token), "CONTROL_COSTOS", action, description, ip, "EXITOSO"
    )


def listar_presupuestos_aprobados(id_obra, token):
    if id_obra <= 0:
        raise ControlCostosError("La obra debe ser valida.")
    return {
        "success": True,
        "data": control_costos_repos.listar_presupuestos_aprobados(
            _empresa(token), id_obra
        ),
    }


def crear_linea_base(data, token, ip="unknown"):
    empresa = _empresa(token)
    usuario = _usuario(token)
    if data["id_obra"] <= 0 or data["id_estimacion_base"] <= 0:
        raise ControlCostosError("La obra y el presupuesto base deben ser validos.")
    try:
        result = control_costos_repos.crear_linea_base(
            empresa, data["id_obra"], data["id_estimacion_base"], usuario
        )
    except control_costos_repos.ControlCostosConflictError as exc:
        raise ControlCostosError(str(exc), 409) from exc
    if not result:
        raise ControlCostosError(
            "El presupuesto no existe, no pertenece a la obra y empresa, o no esta APROBADO.",
            400,
        )
    _log(
        token,
        "SELECCIONAR_LINEA_BASE",
        f"Estimacion {data['id_estimacion_base']} seleccionada para obra {data['id_obra']}.",
        ip,
    )
    return {"success": True, "data": result}


def obtener_linea_base(id_obra, token):
    result = control_costos_repos.obtener_linea_base(_empresa(token), id_obra)
    if not result:
        raise ControlCostosError("La obra no tiene una linea base ACTIVA.", 404)
    return {"success": True, "data": result}


def listar_costos(token, id_obra=None, id_control_costo=None,
                  id_partida=None, estado=None):
    if estado is not None:
        estado = estado.upper().strip()
        if estado not in ESTADOS_COSTO:
            raise ControlCostosError("Estado de costo invalido.")
    return {
        "success": True,
        "data": control_costos_repos.listar_costos(
            _empresa(token), id_obra, id_control_costo, id_partida, estado
        ),
    }


def registrar_costo(data, token, ip="unknown"):
    empresa = _empresa(token)
    usuario = _usuario(token)
    clean = dict(data)
    clean["concepto"] = _texto(data.get("concepto"), "El concepto", max_len=250)
    clean["documento"] = _texto(
        data.get("documento"), "El documento", obligatorio=False, max_len=120
    )
    clean["observacion"] = _texto(
        data.get("observacion"), "La observacion", obligatorio=False
    )
    clean["categoria"] = str(data.get("categoria") or "").strip().upper()
    if clean["categoria"] not in CATEGORIAS_COSTO:
        raise ControlCostosError("La categoria del costo es invalida.")
    clean["cantidad"] = _decimal(data.get("cantidad"), "La cantidad", scale=Decimal("0.0001"))
    clean["costo_unitario"] = _decimal(
        data.get("costo_unitario"), "El costo unitario", scale=CENTAVOS
    )
    clean["monto"] = _decimal(data.get("monto"), "El monto", scale=CENTAVOS)
    expected = (clean["cantidad"] * clean["costo_unitario"]).quantize(
        CENTAVOS, rounding=ROUND_HALF_UP
    )
    if clean["monto"] != expected:
        raise ControlCostosError(
            f"El monto debe ser cantidad por costo_unitario: {expected}."
        )
    line = control_costos_repos.obtener_linea_base_por_id(
        clean["id_control_costo"], empresa, exigir_activa=True
    )
    if not line:
        raise ControlCostosError("La linea base no existe o no esta ACTIVA.", 404)
    part = control_costos_repos.obtener_partida_base(
        clean["id_partida_presupuestaria"], line["id_estimacion_base"], empresa
    )
    if not part:
        raise ControlCostosError(
            "La partida no pertenece exactamente a la estimacion base.", 400
        )
    result = control_costos_repos.crear_costo(clean, empresa, usuario)
    if not result:
        raise ControlCostosError("No se pudo registrar el costo ejecutado.", 400)
    _log(
        token,
        "REGISTRAR_COSTO_EJECUTADO",
        f"Costo {result['id_costo_ejecutado']} registrado por {clean['monto']}.",
        ip,
    )
    return {"success": True, "data": result}


def anular_costo(id_costo, motivo, token, ip="unknown"):
    reason = _texto(motivo, "El motivo de anulacion")
    result = control_costos_repos.anular_costo(
        id_costo, reason, _empresa(token), _usuario(token)
    )
    if not result:
        raise ControlCostosError(
            "El costo no existe, no pertenece a su empresa o ya fue anulado.", 409
        )
    _log(token, "ANULAR_COSTO_EJECUTADO", f"Costo {id_costo} anulado.", ip)
    return {"success": True, "data": result}


def _comparacion(id_obra, token):
    empresa = _empresa(token)
    line = control_costos_repos.obtener_linea_base(empresa, id_obra)
    if not line:
        raise ControlCostosError("La obra no tiene una linea base ACTIVA.", 404)
    rows = control_costos_repos.comparacion_por_obra(empresa, id_obra)
    original = sum((Decimal(row["costo_presupuestado"] or 0) for row in rows), Decimal("0"))
    changes = sum((Decimal(row["impacto_ordenes_aprobadas"] or 0) for row in rows), Decimal("0"))
    revised = sum((Decimal(row["presupuesto_revisado"] or 0) for row in rows), Decimal("0"))
    executed = sum((Decimal(row["costo_ejecutado"] or 0) for row in rows), Decimal("0"))
    variation_original = executed - original
    variation_revised = executed - revised
    totals = {
        "costo_presupuestado_original": original.quantize(CENTAVOS),
        "impacto_ordenes_aprobadas": changes.quantize(CENTAVOS),
        "presupuesto_revisado": revised.quantize(CENTAVOS),
        "costo_ejecutado": executed.quantize(CENTAVOS),
        "variacion_original": variation_original.quantize(CENTAVOS),
        "variacion_original_porcentaje": _porcentaje(variation_original, original),
        "variacion_revisada": variation_revised.quantize(CENTAVOS),
        "variacion_revisada_porcentaje": _porcentaje(variation_revised, revised),
    }
    return line, rows, totals


def obtener_comparacion(id_obra, token):
    line, rows, totals = _comparacion(id_obra, token)
    return {
        "success": True,
        "data": {"linea_base": line, "partidas": rows, "totales": totals},
    }


def obtener_resumen(id_obra, token):
    line, rows, totals = _comparacion(id_obra, token)
    empresa = _empresa(token)
    costs = control_costos_repos.listar_costos(
        empresa, id_obra=id_obra, id_control_costo=line["id_control_costo"]
    )
    orders = control_costos_repos.listar_ordenes(
        empresa, id_obra=id_obra, id_control_costo=line["id_control_costo"]
    )
    totals.update(
        {
            "total_partidas": len(rows),
            "total_costos_registrados": sum(1 for item in costs if item["estado"] == "REGISTRADO"),
            "total_costos_anulados": sum(1 for item in costs if item["estado"] == "ANULADO"),
            "ordenes_pendientes": sum(1 for item in orders if item["estado"] == "PENDIENTE"),
            "ordenes_aprobadas": sum(1 for item in orders if item["estado"] == "APROBADA"),
            "ordenes_rechazadas": sum(1 for item in orders if item["estado"] == "RECHAZADA"),
        }
    )
    return {"success": True, "data": {"linea_base": line, "resumen": totals}}


def _preparar_detalles(raw_details, line, empresa):
    if not raw_details:
        raise ControlCostosError("La orden debe tener al menos un detalle.")
    prepared = []
    for index, raw in enumerate(raw_details, start=1):
        change_type = str(raw.get("tipo_cambio") or "").strip().upper()
        if change_type not in TIPOS_CAMBIO:
            raise ControlCostosError(f"Tipo de cambio invalido en el detalle {index}.")
        observation = _texto(
            raw.get("observacion"), "La observacion", obligatorio=False
        )
        if change_type == "NUEVA_PARTIDA":
            if raw.get("id_partida_presupuestaria") is not None:
                raise ControlCostosError(
                    f"La nueva partida del detalle {index} no puede referenciar una partida existente."
                )
            apu = None
            if raw.get("id_analisis_precio_unitario") is not None:
                apu = control_costos_repos.obtener_apu_para_cambio(
                    raw["id_analisis_precio_unitario"], empresa, line["id_obra"]
                )
                if not apu:
                    raise ControlCostosError(
                        f"El APU del detalle {index} no pertenece a la empresa u obra.", 400
                    )
            code = _texto(
                raw.get("item_codigo_snapshot") or (apu and apu["codigo"]),
                f"El codigo snapshot del detalle {index}",
                max_len=40,
            )
            description = _texto(
                raw.get("descripcion_snapshot") or (apu and apu["nombre"]),
                f"La descripcion snapshot del detalle {index}",
                max_len=250,
            )
            unit = _texto(
                raw.get("unidad_snapshot") or (apu and apu["unidad"]),
                f"La unidad snapshot del detalle {index}",
                max_len=30,
            )
            delta = _decimal(
                raw.get("cantidad_delta"), f"La cantidad delta del detalle {index}",
                nonnegative=False, scale=MILÉSIMAS,
            )
            if delta <= 0:
                raise ControlCostosError(
                    f"La cantidad de una nueva partida debe ser mayor que cero en el detalle {index}."
                )
            new_cost_source = raw.get("costo_nuevo")
            if new_cost_source is None and apu:
                new_cost_source = apu["costo_directo"]
            new_cost = _decimal(
                new_cost_source, f"El costo nuevo del detalle {index}", scale=CENTAVOS
            )
            impact = (delta * new_cost).quantize(CENTAVOS, rounding=ROUND_HALF_UP)
            prepared.append(
                {
                    "id_partida_presupuestaria": None,
                    "id_analisis_precio_unitario": raw.get("id_analisis_precio_unitario"),
                    "tipo_cambio": change_type,
                    "item_codigo_snapshot": code,
                    "descripcion_snapshot": description,
                    "unidad_snapshot": unit,
                    "cantidad_anterior": Decimal("0.000"),
                    "cantidad_delta": delta,
                    "cantidad_revisada": delta,
                    "costo_anterior": Decimal("0.00"),
                    "costo_nuevo": new_cost,
                    "impacto_costo": impact,
                    "observacion": observation,
                }
            )
            continue

        part_id = raw.get("id_partida_presupuestaria")
        if part_id is None:
            raise ControlCostosError(
                f"El detalle {index} debe referenciar una partida de la linea base."
            )
        part = control_costos_repos.obtener_partida_base(
            part_id, line["id_estimacion_base"], empresa
        )
        if not part:
            raise ControlCostosError(
                f"La partida del detalle {index} no pertenece a la estimacion base."
            )
        previous_quantity = _decimal(
            part.get("cantidad_revisada_actual", part["cantidad"]),
            "La cantidad anterior", scale=MILÉSIMAS
        )
        previous_cost = _decimal(
            part.get("costo_revisado_actual", part["costo_directo_unitario"]),
            "El costo anterior", scale=CENTAVOS
        )
        delta = _decimal(
            raw.get("cantidad_delta", 0), f"La cantidad delta del detalle {index}",
            nonnegative=False, scale=MILÉSIMAS,
        )
        new_cost = previous_cost
        if change_type == "AUMENTO_CANTIDAD":
            if delta <= 0:
                raise ControlCostosError(
                    f"El aumento requiere una cantidad delta positiva en el detalle {index}."
                )
            revised_quantity = previous_quantity + delta
            impact = delta * previous_cost
        elif change_type == "DISMINUCION_CANTIDAD":
            if delta >= 0:
                raise ControlCostosError(
                    f"La disminucion requiere una cantidad delta negativa en el detalle {index}."
                )
            revised_quantity = previous_quantity + delta
            if revised_quantity < 0:
                raise ControlCostosError(
                    f"La cantidad revisada no puede ser negativa en el detalle {index}."
                )
            impact = delta * previous_cost
        elif change_type == "CAMBIO_COSTO":
            delta = Decimal("0.000")
            revised_quantity = previous_quantity
            new_cost = _decimal(
                raw.get("costo_nuevo"), f"El costo nuevo del detalle {index}", scale=CENTAVOS
            )
            impact = previous_quantity * (new_cost - previous_cost)
        else:
            delta = -previous_quantity
            revised_quantity = Decimal("0.000")
            new_cost = Decimal("0.00")
            impact = -(previous_quantity * previous_cost)
        impact = impact.quantize(CENTAVOS, rounding=ROUND_HALF_UP)
        prepared.append(
            {
                "id_partida_presupuestaria": part_id,
                "id_analisis_precio_unitario": part["id_analisis_precio_unitario"],
                "tipo_cambio": change_type,
                "item_codigo_snapshot": part["item_codigo"],
                "descripcion_snapshot": part["descripcion_partida"],
                "unidad_snapshot": part["unidad"],
                "cantidad_anterior": previous_quantity,
                "cantidad_delta": delta,
                "cantidad_revisada": revised_quantity,
                "costo_anterior": previous_cost,
                "costo_nuevo": new_cost,
                "impacto_costo": impact,
                "observacion": observation,
            }
        )
    return prepared


def listar_ordenes(token, id_obra=None, id_control_costo=None, estado=None):
    if estado is not None:
        estado = estado.upper().strip()
        if estado not in ESTADOS_ORDEN:
            raise ControlCostosError("Estado de orden invalido.")
    return {
        "success": True,
        "data": control_costos_repos.listar_ordenes(
            _empresa(token), id_obra, id_control_costo, estado
        ),
    }


def obtener_orden(id_orden, token):
    result = control_costos_repos.obtener_orden(id_orden, _empresa(token))
    if not result:
        raise ControlCostosError("La orden de cambio no existe.", 404)
    return {"success": True, "data": result}


def crear_orden(data, token, ip="unknown"):
    empresa = _empresa(token)
    usuario = _usuario(token)
    line = control_costos_repos.obtener_linea_base_por_id(
        data["id_control_costo"], empresa, exigir_activa=True
    )
    if not line:
        raise ControlCostosError("La linea base no existe o no esta ACTIVA.", 404)
    clean = dict(data)
    clean["codigo"] = _texto(data.get("codigo"), "El codigo", max_len=40)
    clean["titulo"] = _texto(data.get("titulo"), "El titulo", max_len=200)
    clean["descripcion"] = _texto(
        data.get("descripcion"), "La descripcion", obligatorio=False
    )
    clean["justificacion"] = _texto(data.get("justificacion"), "La justificacion")
    details = _preparar_detalles(data.get("detalles"), line, empresa)
    total = sum((item["impacto_costo"] for item in details), Decimal("0.00"))
    try:
        result = control_costos_repos.crear_orden(
            clean, details, total.quantize(CENTAVOS), empresa, usuario, ip
        )
    except control_costos_repos.ControlCostosConflictError as exc:
        raise ControlCostosError(str(exc), 409) from exc
    if not result:
        raise ControlCostosError("No se pudo crear la orden de cambio.", 400)
    _log(token, "CREAR_ORDEN_CAMBIO", f"Orden {result['id_orden_cambio']} creada.", ip)
    return obtener_orden(result["id_orden_cambio"], token)


def actualizar_orden(id_orden, data, token, ip="unknown"):
    empresa = _empresa(token)
    usuario = _usuario(token)
    current = control_costos_repos.obtener_orden(id_orden, empresa)
    if not current:
        raise ControlCostosError("La orden de cambio no existe.", 404)
    if current["estado"] != "PENDIENTE":
        raise ControlCostosError("Solo una orden PENDIENTE puede modificarse.", 409)
    line = control_costos_repos.obtener_linea_base_por_id(
        current["id_control_costo"], empresa, exigir_activa=True
    )
    if not line:
        raise ControlCostosError("La linea base no existe o no esta ACTIVA.", 409)
    clean = dict(data)
    clean["titulo"] = _texto(data.get("titulo"), "El titulo", max_len=200)
    clean["descripcion"] = _texto(
        data.get("descripcion"), "La descripcion", obligatorio=False
    )
    clean["justificacion"] = _texto(data.get("justificacion"), "La justificacion")
    details = _preparar_detalles(data.get("detalles"), line, empresa)
    total = sum((item["impacto_costo"] for item in details), Decimal("0.00"))
    result = control_costos_repos.actualizar_orden(
        id_orden, clean, details, total.quantize(CENTAVOS),
        empresa, usuario, ip,
    )
    if not result:
        raise ControlCostosError("La orden ya no esta PENDIENTE.", 409)
    _log(token, "MODIFICAR_ORDEN_CAMBIO", f"Orden {id_orden} modificada.", ip)
    return obtener_orden(id_orden, token)


def aprobar_orden(id_orden, comentario, token, ip="unknown"):
    return _decidir_orden(id_orden, "APROBADA", comentario, token, ip)


def rechazar_orden(id_orden, motivo, token, ip="unknown"):
    reason = _texto(motivo, "El motivo de rechazo")
    return _decidir_orden(id_orden, "RECHAZADA", reason, token, ip)


def _decidir_orden(id_orden, state, reason, token, ip):
    empresa = _empresa(token)
    usuario = _usuario(token)
    current = control_costos_repos.obtener_orden(id_orden, empresa)
    if not current:
        raise ControlCostosError("La orden de cambio no existe.", 404)
    if current["estado"] != "PENDIENTE":
        raise ControlCostosError("Solo una orden PENDIENTE puede decidirse.", 409)
    if not current.get("detalles"):
        raise ControlCostosError("No se puede decidir una orden sin detalles.", 409)
    result = control_costos_repos.decidir_orden(
        id_orden, state, reason, empresa, usuario, ip
    )
    if not result:
        raise ControlCostosError("La orden ya no esta PENDIENTE.", 409)
    action = "APROBAR_ORDEN_CAMBIO" if state == "APROBADA" else "RECHAZAR_ORDEN_CAMBIO"
    _log(token, action, f"Orden {id_orden} cambiada a {state}.", ip)
    return {"success": True, "data": result}


def listar_historial(id_orden, token):
    empresa = _empresa(token)
    if not control_costos_repos.obtener_orden(id_orden, empresa):
        raise ControlCostosError("La orden de cambio no existe.", 404)
    return {
        "success": True,
        "data": control_costos_repos.listar_historial(id_orden, empresa),
    }
