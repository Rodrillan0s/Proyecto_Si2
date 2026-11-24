"""Ejecutor seguro del Motor Semántico Compartido.

Ejecuta únicamente SQL compilado desde SemanticQuerySpec / CrossModuleSpec dentro
de transacciones REPEATABLE READ, READ ONLY con timeout controlado.
"""
from decimal import Decimal
from fastapi import HTTPException
from app.repos import reportes_repos as repo
from app.services.reportes import authorization as auth
from app.services.semantic import compiler
from app.services.semantic.contracts import (
    ChartSpec,
    CrossModuleSpec,
    SemanticQuerySpec,
    UnifiedResultSet,
)


def _infer_chart(spec: SemanticQuerySpec, cols: list[dict], rows: list[dict], tipo_resultado: str) -> ChartSpec:
    requested = spec.tipo_grafico
    if requested == 'none' or not rows:
        return ChartSpec(tipo='none')

    num_cols = [c for c in cols if c['tipo'] == 'number']
    cat_cols = [c for c in cols if c['tipo'] in {'text', 'date', 'datetime'}]

    if requested != 'auto':
        eje = cat_cols[0]['campo'] if cat_cols else (cols[0]['campo'] if cols else None)
        return ChartSpec(
            tipo=requested,
            eje_x=eje,
            series=[{'campo': c['campo'], 'titulo': c['titulo']} for c in num_cols[:4]],
            titulo=spec.titulo,
        )

    if tipo_resultado == 'serie_temporal' and num_cols:
        return ChartSpec(
            tipo='line',
            eje_x='periodo',
            series=[{'campo': c['campo'], 'titulo': c['titulo']} for c in num_cols[:4]],
            titulo=spec.titulo,
        )
    if tipo_resultado == 'agregacion' and num_cols:
        if not cat_cols and len(rows) == 1:
            return ChartSpec(
                tipo='kpi',
                series=[{'campo': c['campo'], 'titulo': c['titulo']} for c in num_cols[:4]],
                titulo=spec.titulo,
            )
        if cat_cols and len(rows) <= 6 and len(num_cols) == 1:
            return ChartSpec(
                tipo='pie',
                eje_x=cat_cols[0]['campo'],
                series=[{'campo': num_cols[0]['campo'], 'titulo': num_cols[0]['titulo']}],
                titulo=spec.titulo,
            )
        if cat_cols:
            return ChartSpec(
                tipo='bar',
                eje_x=cat_cols[0]['campo'],
                series=[{'campo': c['campo'], 'titulo': c['titulo']} for c in num_cols[:4]],
                titulo=spec.titulo,
            )
    return ChartSpec(tipo='none')


def _compute_period_comparison(current_rows: list[dict], prev_rows: list[dict], spec: SemanticQuerySpec) -> dict:
    metric_keys = [m.alias for m in spec.metricas] or (['total'] if spec.tiempo and spec.tiempo.granularidad else [])
    cur_totals = {k: sum((Decimal(str(r.get(k) or 0)) for r in current_rows), Decimal(0)) for k in metric_keys}
    prv_totals = {k: sum((Decimal(str(r.get(k) or 0)) for r in prev_rows), Decimal(0)) for k in metric_keys}
    variaciones = []
    for k in metric_keys:
        diff = cur_totals[k] - prv_totals[k]
        pct = ((diff / prv_totals[k]) * Decimal(100)).quantize(Decimal('0.01')) if prv_totals[k] != 0 else None
        variaciones.append({
            'metrica': k,
            'actual': str(cur_totals[k]),
            'anterior': str(prv_totals[k]),
            'diferencia': str(diff),
            'variacion_porcentaje': str(pct) if pct is not None else None,
        })
    return {
        'periodo_actual': {'desde': str(spec.tiempo.desde), 'hasta': str(spec.tiempo.hasta)},
        'registros_actual': len(current_rows),
        'registros_anterior': len(prev_rows),
        'variaciones': variaciones,
    }


def execute_semantic_query(db, ctx, spec: SemanticQuerySpec) -> tuple[UnifiedResultSet, list[int]]:
    """Autoriza vía authorization.py, compila a SQL y devuelve UnifiedResultSet."""
    entity, scope_obras = auth.authorize_semantic_query(db, ctx, spec)

    if entity.work_column and not scope_obras:
        cutoff = repo.cutoff(db)['corte'].isoformat()
        empty_cols = [{'campo': f.name, 'titulo': f.label, 'tipo': 'text'} for f in entity.fields]
        return UnifiedResultSet(
            reporte=f'dinamico:{entity.id}',
            titulo=spec.titulo or entity.title,
            id_empresa=ctx.empresa,
            corte=cutoff,
            solicitud=spec.model_dump(mode='json'),
            columnas=empty_cols,
            columnas_disponibles=empty_cols,
            filas=[],
            resumen={'registros': 0},
            advertencias=['No existen obras asignadas en su ámbito autorizado.'],
            permisos_fuente=[entity.required_permission] if entity.required_permission else [],
            fuentes_consultadas=[entity.id],
        ), []

    sql, params, cols, warnings, tipo_resultado = compiler.compile_semantic_query(db and ctx, entity, scope_obras, spec)
    raw_rows = repo.rows(db, sql, params)

    truncated = len(raw_rows) > spec.limite
    if truncated and spec.limite >= 20000:
        raise HTTPException(422, 'La consulta excede 20.000 filas. Acota obra, fechas o filtros.')
    rows = raw_rows[:spec.limite]

    comparativa = None
    if spec.tiempo and spec.tiempo.comparar_periodo_anterior and spec.tiempo.desde and spec.tiempo.hasta:
        p_desde, p_hasta = compiler.previous_period(spec.tiempo.desde, spec.tiempo.hasta)
        prev_sql, prev_params, _, _, _ = compiler.compile_semantic_query(
            ctx, entity, scope_obras, spec, override_dates=(p_desde, p_hasta)
        )
        prev_rows = repo.rows(db, prev_sql, prev_params)[:spec.limite]
        comparativa = _compute_period_comparison(rows, prev_rows, spec)
        comparativa['periodo_anterior'] = {'desde': str(p_desde), 'hasta': str(p_hasta)}
        tipo_resultado = 'comparativa'

    if truncated:
        warnings.append(f"Se muestran los primeros {spec.limite} registros; aplica filtros más específicos para ver el detalle completo.")

    chart = _infer_chart(spec, cols, rows, tipo_resultado)
    cutoff = repo.cutoff(db)['corte'].isoformat()

    resumen = {'registros': len(rows), 'detalle_completo': not truncated}
    if tipo_resultado == 'agregacion' and len(rows) == 1:
        for c in cols:
            if c['tipo'] == 'number':
                resumen[c['campo']] = rows[0].get(c['campo'])

    result = UnifiedResultSet(
        reporte=f'dinamico:{entity.id}',
        titulo=spec.titulo or entity.title,
        id_empresa=ctx.empresa,
        corte=cutoff,
        solicitud=spec.model_dump(mode='json'),
        columnas=cols,
        columnas_disponibles=cols,
        filas=rows,
        resumen=resumen,
        advertencias=warnings or [entity.description],
        permisos_fuente=[entity.required_permission] if entity.required_permission else [],
        tipo_resultado=tipo_resultado,
        chart_spec=chart,
        comparativa_periodo=comparativa,
        metadata_dominio={
            'entidad': entity.id,
            'tiene_moneda': entity.has_currency_field,
        },
        fuentes_consultadas=[entity.id],
    )
    return result, scope_obras


def execute_cross_module(db, ctx, spec: CrossModuleSpec) -> tuple[UnifiedResultSet, list[int]]:
    """Ejecuta un cruce multidimensional por obra mediante CTEs pre-agregados."""
    permitidos, omitidos, scope_obras = auth.authorize_cross_module(db, ctx, spec)
    cutoff = repo.cutoff(db)['corte'].isoformat()
    if not scope_obras:
        return UnifiedResultSet(
            reporte='dinamico:cruce_obras',
            titulo='Análisis multidimensional de obras',
            id_empresa=ctx.empresa,
            corte=cutoff,
            solicitud=spec.model_dump(mode='json'),
            columnas=[],
            columnas_disponibles=[],
            filas=[],
            resumen={'registros': 0},
            advertencias=['No existen obras autorizadas en su ámbito.'],
            tipo_resultado='multidimensional',
            fuentes_consultadas=permitidos,
            fuentes_omitidas=omitidos,
        ), []

    sql, params, cols = compiler.compile_cross_module_works(ctx, permitidos, scope_obras, spec)
    rows = repo.rows(db, sql, params)

    warnings = ['Métricas consolidadas por obra mediante agregaciones independientes sin duplicación de filas.']
    if omitidos:
        warnings.append('Módulos omitidos por permisos: ' + ', '.join(o['modulo'] for o in omitidos))

    num_series = [{'campo': c['campo'], 'titulo': c['titulo']} for c in cols if c['tipo'] == 'number' and c['campo'] != 'id_obra']
    chart = ChartSpec(tipo='bar', eje_x='obra', series=num_series[:3], titulo='Comparativa multidimensional por obra') if rows else ChartSpec(tipo='none')

    return UnifiedResultSet(
        reporte='dinamico:cruce_obras',
        titulo='Análisis multidimensional por obra',
        id_empresa=ctx.empresa,
        corte=cutoff,
        solicitud=spec.model_dump(mode='json'),
        columnas=cols,
        columnas_disponibles=cols,
        filas=rows,
        resumen={'obras_evaluadas': len(rows)},
        advertencias=warnings,
        tipo_resultado='multidimensional',
        chart_spec=chart,
        metadata_dominio={'llave': spec.llave, 'modulos': permitidos},
        fuentes_consultadas=permitidos,
        fuentes_omitidas=omitidos,
    ), scope_obras
