"""Compilador AST -> SQL parametrizado del Motor Semántico Compartido.

SEGURIDAD:
- Todos los nombres de tablas y columnas provienen exclusivamente de EntityDef (whitelist).
- Todos los valores de usuario/LLM van como parámetros %s.
- Inyecta obligatoriamente tenant (id_empresa), alcance de obras y RLS (CLIENTE / WORKERS).
- Nunca acepta SQL libre del modelo ni del usuario.
"""
from datetime import date, timedelta
from fastapi import HTTPException
from app.services.reportes.catalog import WORKERS
from app.services.semantic.catalog import EntityDef, FieldDef
from app.services.semantic.contracts import (
    CrossModuleSpec,
    ReportSpecPatch,
    SemanticFilter,
    SemanticQuerySpec,
)

GRANULARITY_SQL = {
    'day': 'day',
    'week': 'week',
    'month': 'month',
    'quarter': 'quarter',
    'year': 'year',
}


def apply_patch(spec: SemanticQuerySpec, patch: ReportSpecPatch) -> SemanticQuerySpec:
    """Aplica una modificación incremental sobre un SemanticQuerySpec sin reconstruirlo."""
    data = spec.model_dump()
    op = patch.operacion

    if op == 'add_dimension':
        if not patch.campo:
            raise HTTPException(422, 'Indique el campo de dimensión a agregar.')
        if patch.campo not in data['dimensiones']:
            data['dimensiones'].append(patch.campo)
        if data['campos'] and patch.campo not in data['campos']:
            data['campos'].append(patch.campo)

    elif op == 'remove_dimension':
        if patch.campo and patch.campo in data['dimensiones']:
            data['dimensiones'].remove(patch.campo)

    elif op == 'add_filter':
        if not patch.filtro:
            raise HTTPException(422, 'Indique el filtro a agregar.')
        # Reemplaza filtro previo del mismo campo+operador para evitar contradicciones
        data['filtros'] = [
            f for f in data['filtros']
            if not (f['campo'] == patch.filtro.campo and f['operador'] == patch.filtro.operador)
        ]
        data['filtros'].append(patch.filtro.model_dump())

    elif op == 'remove_filter':
        if patch.campo:
            data['filtros'] = [f for f in data['filtros'] if f['campo'] != patch.campo]

    elif op == 'set_time':
        if not patch.tiempo:
            raise HTTPException(422, 'Indique la configuración temporal.')
        data['tiempo'] = patch.tiempo.model_dump()

    elif op == 'compare_periods':
        tiempo = data.get('tiempo') or {}
        if patch.tiempo:
            tiempo.update(patch.tiempo.model_dump(exclude_none=True))
        tiempo['comparar_periodo_anterior'] = True
        data['tiempo'] = tiempo

    elif op == 'set_sort':
        if patch.campo:
            data['ordenar_por'] = patch.campo
        if patch.orden:
            data['orden'] = patch.orden

    elif op == 'set_chart':
        if patch.tipo_grafico:
            data['tipo_grafico'] = patch.tipo_grafico

    elif op == 'set_limit':
        if patch.limite:
            data['limite'] = patch.limite

    elif op == 'set_title':
        data['titulo'] = patch.titulo

    return SemanticQuerySpec.model_validate(data)


def _date_expr(field_def: FieldDef) -> str:
    if field_def.data_type == 'datetime':
        return f"({field_def.sql_expr} AT TIME ZONE 'America/La_Paz')::date"
    return f"({field_def.sql_expr})::date"


def _validate_business_rules(entity: EntityDef, spec: SemanticQuerySpec, field_map: dict[str, FieldDef]) -> None:
    if spec.dimensiones and not spec.metricas:
        raise HTTPException(422, 'Las dimensiones de agrupación requieren al menos una métrica.')

    if spec.metricas:
        has_money_agg = any(
            m.operacion in {'sum', 'avg', 'min', 'max'}
            and m.campo
            and field_map[m.campo].data_type == 'money'
            for m in spec.metricas
        )
        if has_money_agg:
            if not entity.has_currency_field:
                raise HTTPException(
                    422,
                    f"La entidad '{entity.id}' no registra moneda propia; consulte registros individuales o una fuente con moneda.",
                )
            if 'moneda' not in spec.dimensiones:
                raise HTTPException(422, "Agrupa por 'moneda' para no mezclar monedas distintas.")

        if entity.versioned_by_work and any(m.operacion in {'sum', 'avg'} for m in spec.metricas):
            missing = {'id_obra', 'version'} - set(spec.dimensiones)
            if missing:
                raise HTTPException(
                    422,
                    f"Agrupa por {', '.join(sorted(missing))} para no sumar versiones distintas de presupuesto.",
                )

        has_qty_sum = any(
            m.operacion == 'sum'
            and m.campo
            and field_map[m.campo].data_type == 'quantity'
            for m in spec.metricas
        )
        if has_qty_sum:
            unit_keys = {'id_material', 'nombre_material', 'id_unidad_medida'}
            if not (set(spec.dimensiones) & unit_keys):
                raise HTTPException(
                    422,
                    'Agrupa las cantidades por material o unidad para no mezclar unidades de medida.',
                )


def _compile_filter(flt: SemanticFilter, fdef: FieldDef, params: list) -> str:
    expr = fdef.sql_expr
    op = flt.operador
    val = flt.valor

    if op == 'is_null':
        return f"({expr} IS NULL)" if val is not False else f"({expr} IS NOT NULL)"
    if op == 'contains':
        if not isinstance(val, str) or len(val) > 200:
            raise HTTPException(422, 'El filtro contains requiere un texto de hasta 200 caracteres.')
        params.append(f"%{val.strip()}%")
        return f"({expr}::text ILIKE %s)"
    if op == 'in':
        if not isinstance(val, list) or not val or len(val) > 50:
            raise HTTPException(422, 'El filtro in requiere entre 1 y 50 valores.')
        params.append(val)
        return f"({expr} = ANY(%s))"
    if op == 'between':
        if not isinstance(val, list) or len(val) != 2:
            raise HTTPException(422, 'El filtro between requiere exactamente 2 valores [inicio, fin].')
        params.extend([val[0], val[1]])
        return f"({expr} BETWEEN %s AND %s)"

    sql_ops = {'eq': '=', 'ne': '<>', 'lt': '<', 'lte': '<=', 'gt': '>', 'gte': '>='}
    if val is None:
        raise HTTPException(422, f"El operador '{op}' requiere un valor.")
    if fdef.data_type == 'text' and op in {'eq', 'ne'} and isinstance(val, str):
        params.append(val.strip().upper())
        return f"(UPPER({expr}::text) {sql_ops[op]} %s)"
    params.append(val)
    return f"({expr} {sql_ops[op]} %s)"


def compile_semantic_query(
    ctx,
    entity: EntityDef,
    scope_obras: list[int],
    spec: SemanticQuerySpec,
    *,
    override_dates: tuple[date | None, date | None] | None = None,
) -> tuple[str, list, list[dict], list[str], str]:
    """Compila SemanticQuerySpec a SQL parametrizado seguro."""
    field_map = entity.field_map()
    from_sql = entity.base_from

    # Agregar relaciones autorizadas
    rel_map = entity.relation_map()
    for rel_name in spec.relaciones:
        rel = rel_map[rel_name]
        from_sql += ' ' + rel.join_sql
        for rf in rel.fields:
            field_map[f"{rel_name}_{rf.name}"] = rf

    # Validar todos los campos referenciados contra whitelist
    referenced = set(spec.dimensiones + spec.campos)
    referenced.update(f.campo for f in spec.filtros)
    referenced.update(m.campo for m in spec.metricas if m.campo)
    if spec.tiempo and spec.tiempo.campo_fecha:
        referenced.add(spec.tiempo.campo_fecha)
    unknown = referenced - set(field_map.keys())
    if unknown:
        raise HTTPException(422, f"Campos no permitidos en '{entity.id}': {', '.join(sorted(unknown))}")

    for m in spec.metricas:
        if m.operacion != 'count' and not m.campo:
            raise HTTPException(422, f"La métrica '{m.alias}' requiere un campo.")
        if m.operacion in {'sum', 'avg'} and m.campo and not field_map[m.campo].aggregatable:
            raise HTTPException(422, f"El campo '{m.campo}' no admite operación '{m.operacion}'.")

    _validate_business_rules(entity, spec, field_map)

    where_clauses: list[str] = []
    params: list = []

    # 1. Aislamiento obligatorio de empresa (tenant)
    if entity.tenant_clause:
        where_clauses.append(f"({entity.tenant_clause})")
        params.append(ctx.empresa)

    # 2. Aislamiento obligatorio de obras autorizadas
    if entity.work_column:
        where_clauses.append(f"({entity.work_column} = ANY(%s))")
        params.append(scope_obras)

    # 3. Row-Level Security por perfil (CLIENTE / WORKERS)
    if ctx.rol == 'CLIENTE' and entity.cliente_row_clause:
        where_clauses.append(f"({entity.cliente_row_clause})")
        params.append(ctx.persona)
    elif ctx.rol in WORKERS and entity.worker_row_clause:
        where_clauses.append(f"({entity.worker_row_clause})")
        placeholder_count = entity.worker_row_clause.count('%s')
        params.extend([ctx.usuario] * placeholder_count)

    # 4. Filtros dinámicos parametrizados
    for flt in spec.filtros:
        where_clauses.append(_compile_filter(flt, field_map[flt.campo], params))

    # 5. Filtro temporal
    date_field_name = None
    desde, hasta = (None, None)
    granularidad = None
    if spec.tiempo:
        date_field_name = spec.tiempo.campo_fecha or entity.default_date_field
        if not date_field_name or date_field_name not in field_map:
            raise HTTPException(422, f"La entidad '{entity.id}' no dispone de campo de fecha para filtro temporal.")
        if override_dates is not None:
            desde, hasta = override_dates
        else:
            desde, hasta = spec.tiempo.desde, spec.tiempo.hasta
        granularidad = spec.tiempo.granularidad
        dexpr = _date_expr(field_map[date_field_name])
        if desde:
            where_clauses.append(f"({dexpr} >= %s)")
            params.append(desde)
        if hasta:
            where_clauses.append(f"({dexpr} <= %s)")
            params.append(hasta)

    # 6. SELECT + GROUP BY
    select_parts: list[str] = []
    group_parts: list[str] = []
    output_cols: list[dict] = []
    valid_order_keys: set[str] = set()

    is_time_series = bool(granularidad and date_field_name)
    is_agg = bool(spec.metricas or is_time_series)

    if is_agg:
        if is_time_series:
            trunc_unit = GRANULARITY_SQL[granularidad]
            fdef_d = field_map[date_field_name]
            ts_expr = (
                f"DATE_TRUNC('{trunc_unit}', {fdef_d.sql_expr} AT TIME ZONE 'America/La_Paz')::date"
                if fdef_d.data_type == 'datetime'
                else f"DATE_TRUNC('{trunc_unit}', {fdef_d.sql_expr})::date"
            )
            select_parts.append(f"{ts_expr} AS periodo")
            group_parts.append(ts_expr)
            output_cols.append({'campo': 'periodo', 'titulo': 'Período', 'tipo': 'date'})
            valid_order_keys.add('periodo')

        for dim in spec.dimensiones:
            fdef = field_map[dim]
            select_parts.append(f"{fdef.sql_expr} AS {dim}")
            group_parts.append(fdef.sql_expr)
            output_cols.append({'campo': dim, 'titulo': fdef.label, 'tipo': _public_type(fdef.data_type)})
            valid_order_keys.add(dim)

        metricas = spec.metricas or []
        if not metricas:
            # Serie temporal sin métrica explícita -> conteo
            select_parts.append('COUNT(*) AS total')
            output_cols.append({'campo': 'total', 'titulo': 'Total', 'tipo': 'number'})
            valid_order_keys.add('total')
        else:
            for m in metricas:
                if m.operacion == 'count':
                    mexpr = f"COUNT({field_map[m.campo].sql_expr})" if m.campo else 'COUNT(*)'
                elif m.operacion == 'count_distinct':
                    mexpr = f"COUNT(DISTINCT {field_map[m.campo].sql_expr})"
                else:
                    mexpr = f"{m.operacion.upper()}({field_map[m.campo].sql_expr})"
                select_parts.append(f"{mexpr} AS {m.alias}")
                output_cols.append({'campo': m.alias, 'titulo': m.alias.replace('_', ' ').capitalize(), 'tipo': 'number'})
                valid_order_keys.add(m.alias)
    else:
        chosen = spec.campos or [f.name for f in entity.fields]
        for cname in chosen:
            fdef = field_map[cname]
            select_parts.append(f"{fdef.sql_expr} AS {cname}")
            output_cols.append({'campo': cname, 'titulo': fdef.label, 'tipo': _public_type(fdef.data_type)})
            valid_order_keys.add(cname)

    # 7. ORDER BY
    direction = 'ASC' if spec.orden == 'asc' else 'DESC'
    if spec.ordenar_por:
        if spec.ordenar_por not in valid_order_keys:
            raise HTTPException(422, f"Ordenación '{spec.ordenar_por}' fuera de las columnas de salida.")
        order_sql = f"ORDER BY {spec.ordenar_por} {direction} NULLS LAST"
    elif is_time_series:
        order_sql = 'ORDER BY periodo ASC'
    elif is_agg and output_cols:
        order_sql = f"ORDER BY {output_cols[-1]['campo']} DESC NULLS LAST"
    elif entity.default_order:
        order_sql = f"ORDER BY {entity.default_order}"
    else:
        order_sql = ''

    where_sql = (' WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''
    group_sql = (' GROUP BY ' + ', '.join(group_parts)) if group_parts else ''

    # Traer limite + 1 para detectar si hay más registros sin truncamiento silencioso
    fetch_limit = min(spec.limite, 20000) + 1
    params.append(fetch_limit)

    sql = f"SELECT {', '.join(select_parts)} FROM {from_sql}{where_sql}{group_sql} {order_sql} LIMIT %s"
    tipo_resultado = 'serie_temporal' if is_time_series else ('agregacion' if is_agg else 'tabular')
    warnings = list(entity.warnings)
    return sql, params, output_cols, warnings, tipo_resultado


def compile_cross_module_works(
    ctx,
    modulos_permitidos: list[str],
    scope_obras: list[int],
    spec: CrossModuleSpec,
) -> tuple[str, list, list[dict]]:
    """Compila cruce multi-módulo por id_obra usando CTEs pre-agregados (cero fan-out)."""
    ctes: list[str] = []
    joins: list[str] = []
    selects: list[str] = ['o.id_obra', 'o.codigo', 'o.nombre AS obra', 'o.estado_obra', 'o.moneda']
    cols: list[dict] = [
        {'campo': 'id_obra', 'titulo': 'ID Obra', 'tipo': 'number'},
        {'campo': 'codigo', 'titulo': 'Código', 'tipo': 'text'},
        {'campo': 'obra', 'titulo': 'Obra', 'tipo': 'text'},
        {'campo': 'estado_obra', 'titulo': 'Estado', 'tipo': 'text'},
        {'campo': 'moneda', 'titulo': 'Moneda', 'tipo': 'text'},
    ]
    params: list = []

    if 'retrasos' in modulos_permitidos:
        ctes.append("""
            cte_retrasos AS (
                SELECT cr.id_obra,
                       COUNT(*) FILTER (WHERE ca.fin_real IS NULL AND ca.fecha_fin < CURRENT_DATE) AS actividades_retrasadas,
                       COALESCE(ROUND(AVG(ca.avance)::numeric, 2), 0) AS avance_cronograma_pct
                FROM obras.t_cronograma_actividad ca
                JOIN obras.t_cronograma cr ON cr.id_cronograma = ca.id_cronograma
                JOIN obras.t_obra ob ON ob.id_obra = cr.id_obra
                WHERE ob.id_empresa = %s AND cr.id_obra = ANY(%s)
                GROUP BY cr.id_obra
            )
        """)
        params.extend([ctx.empresa, scope_obras])
        joins.append('LEFT JOIN cte_retrasos cr_r ON cr_r.id_obra = o.id_obra')
        selects.extend([
            'COALESCE(cr_r.actividades_retrasadas, 0) AS actividades_retrasadas',
            'COALESCE(cr_r.avance_cronograma_pct, 0) AS avance_cronograma_pct',
        ])
        cols.extend([
            {'campo': 'actividades_retrasadas', 'titulo': 'Actividades retrasadas', 'tipo': 'number'},
            {'campo': 'avance_cronograma_pct', 'titulo': 'Avance cronograma (%)', 'tipo': 'number'},
        ])

    if 'incidencias_criticas' in modulos_permitidos:
        ctes.append("""
            cte_inc AS (
                SELECT i.id_obra,
                       COUNT(*) FILTER (WHERE i.prioridad = 'CRITICA' AND i.estado NOT IN ('RESUELTA','CERRADA')) AS incidencias_criticas,
                       COUNT(*) FILTER (WHERE i.estado NOT IN ('RESUELTA','CERRADA')) AS incidencias_abiertas
                FROM obras.t_incidencia i
                JOIN obras.t_obra ob ON ob.id_obra = i.id_obra
                WHERE ob.id_empresa = %s AND i.id_obra = ANY(%s)
                GROUP BY i.id_obra
            )
        """)
        params.extend([ctx.empresa, scope_obras])
        joins.append('LEFT JOIN cte_inc inc ON inc.id_obra = o.id_obra')
        selects.extend([
            'COALESCE(inc.incidencias_criticas, 0) AS incidencias_criticas',
            'COALESCE(inc.incidencias_abiertas, 0) AS incidencias_abiertas',
        ])
        cols.extend([
            {'campo': 'incidencias_criticas', 'titulo': 'Incidencias críticas', 'tipo': 'number'},
            {'campo': 'incidencias_abiertas', 'titulo': 'Incidencias abiertas', 'tipo': 'number'},
        ])

    if 'costos' in modulos_permitidos:
        ctes.append("""
            cte_costos AS (
                SELECT cc.id_obra,
                       COALESCE(SUM(ce.monto) FILTER (WHERE ce.estado = 'REGISTRADO'), 0) AS costo_ejecutado
                FROM obras.t_control_costo_obra cc
                LEFT JOIN obras.t_costo_ejecutado ce ON ce.id_control_costo = cc.id_control_costo AND ce.id_empresa = cc.id_empresa
                WHERE cc.id_empresa = %s AND cc.id_obra = ANY(%s) AND cc.estado = 'ACTIVO'
                GROUP BY cc.id_obra
            )
        """)
        params.extend([ctx.empresa, scope_obras])
        joins.append('LEFT JOIN cte_costos cst ON cst.id_obra = o.id_obra')
        selects.append('COALESCE(cst.costo_ejecutado, 0) AS costo_ejecutado')
        cols.append({'campo': 'costo_ejecutado', 'titulo': 'Costo ejecutado', 'tipo': 'number'})

    if 'ordenes_trabajo' in modulos_permitidos:
        ctes.append("""
            cte_ot AS (
                SELECT ot.id_obra,
                       COUNT(*) FILTER (WHERE ot.fecha_fin < CURRENT_DATE AND ot.estado NOT IN ('FINALIZADA','CANCELADA')) AS ots_vencidas
                FROM obras.t_orden_trabajo ot
                JOIN obras.t_obra ob ON ob.id_obra = ot.id_obra
                WHERE ob.id_empresa = %s AND ot.id_obra = ANY(%s)
                GROUP BY ot.id_obra
            )
        """)
        params.extend([ctx.empresa, scope_obras])
        joins.append('LEFT JOIN cte_ot otm ON otm.id_obra = o.id_obra')
        selects.append('COALESCE(otm.ots_vencidas, 0) AS ots_vencidas')
        cols.append({'campo': 'ots_vencidas', 'titulo': 'OTs vencidas', 'tipo': 'number'})

    if 'posventa' in modulos_permitidos:
        ctes.append("""
            cte_posv AS (
                SELECT s.id_obra,
                       COUNT(*) FILTER (WHERE sp.estado NOT IN ('RESUELTA','CERRADA')) AS posventa_abierta
                FROM obras.t_solicitud_posventa sp
                JOIN obras.t_unidad_construccion u ON u.id_unidad = sp.id_unidad
                JOIN obras.t_estructura_obra s ON s.id_estructura = u.id_estructura
                WHERE sp.id_empresa = %s AND s.id_obra = ANY(%s)
                GROUP BY s.id_obra
            )
        """)
        params.extend([ctx.empresa, scope_obras])
        joins.append('LEFT JOIN cte_posv pv ON pv.id_obra = o.id_obra')
        selects.append('COALESCE(pv.posventa_abierta, 0) AS posventa_abierta')
        cols.append({'campo': 'posventa_abierta', 'titulo': 'Posventa abierta', 'tipo': 'number'})

    params.extend([ctx.empresa, scope_obras, spec.limite])
    valid_order = {c['campo'] for c in cols}
    order_col = spec.ordenar_por if spec.ordenar_por in valid_order else cols[-1]['campo']
    direction = 'ASC' if spec.orden == 'asc' else 'DESC'

    sql = (
        f"WITH {', '.join(ctes)} "
        f"SELECT {', '.join(selects)} "
        f"FROM obras.t_obra o {' '.join(joins)} "
        f"WHERE o.id_empresa = %s AND o.id_obra = ANY(%s) "
        f"ORDER BY {order_col} {direction} NULLS LAST LIMIT %s"
    )
    return sql, params, cols


def previous_period(desde: date, hasta: date) -> tuple[date, date]:
    span_days = (hasta - desde).days + 1
    prev_hasta = desde - timedelta(days=1)
    prev_desde = prev_hasta - timedelta(days=span_days - 1)
    return prev_desde, prev_hasta


def _public_type(dtype: str) -> str:
    if dtype in {'number', 'money', 'quantity'}:
        return 'number'
    if dtype in {'date', 'datetime'}:
        return dtype
    return 'text'
