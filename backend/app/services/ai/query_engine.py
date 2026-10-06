"""Planes de lectura generados por IA sobre fuentes autorizadas, sin SQL libre."""
from datetime import date, datetime
import json
from decimal import Decimal, InvalidOperation
from typing import Literal
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from app.services.reportes.contracts import Filters, ReportRequest
from app.services.reportes.catalog import REGISTRY, FIELDS, WORKERS
from app.services.reportes.authorization import allowed, authorize


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Condition(Strict):
    campo: str = Field(max_length=80)
    operador: Literal['eq', 'ne', 'lt', 'lte', 'gt', 'gte', 'contains', 'in', 'is_null']
    valor: str | int | float | bool | list[str | int | float] | None = None
    comparar_campo: str | None = Field(default=None, max_length=80)


class Metric(Strict):
    operacion: Literal['count', 'count_distinct', 'sum', 'avg', 'min', 'max']
    campo: str | None = Field(default=None, max_length=80)
    nombre: str = Field(pattern=r'^[a-z][a-z0-9_]{0,59}$')


class Lookup(Strict):
    fuente: str = Field(max_length=60)
    campo: str = Field(max_length=80)
    clave: str = Field(max_length=80)
    prefijo: str = Field(pattern=r'^[a-z][a-z0-9_]{0,19}$')


class Query(Strict):
    fuente: str = Field(max_length=60)
    filtros_fuente: Filters = Field(default_factory=Filters)
    condiciones: list[Condition] = Field(default_factory=list, max_length=12)
    cruces: list[Lookup] = Field(default_factory=list, max_length=2)
    campos: list[str] = Field(default_factory=list, max_length=30)
    agrupar_por: list[str] = Field(default_factory=list, max_length=6)
    metricas: list[Metric] = Field(default_factory=list, max_length=8)
    ordenar_por: str | None = Field(default=None, max_length=80)
    orden: Literal['asc', 'desc'] = 'asc'
    limite: int = Field(default=30, ge=1, le=100)


# Campos revisados contra repositorios e inventario. No se exponen contactos o credenciales.
MODULES = {
    'obras': ('Visualizar_obras', 't_obra', 'id_obra codigo nombre estado_obra fecha_inicio fecha_fin moneda', True),
    'materiales': ('Visualizar_materiales', 't_material', 'id_material codigo nombre_material precio id_proveedor id_categoria id_unidad_medida estado', False),
    'proveedores': ('Visualizar_proveedores', 't_proveedor', 'id_proveedor nombre estado', False),
    'compras': ('Visualizar_ordenes_compra', 't_orden_compra', 'id_orden_compra id_proveedor numero_orden fecha estado subtotal total', False),
    'maquinaria': ('Visualizar_equipos_maquinaria', 't_equipo_maquinaria', 'id_equipo_maquinaria codigo nombre tipo marca modelo estado', False),
    'asignaciones_maquinaria': ('Visualizar_equipos_maquinaria', 't_equipo_maquinaria_obra', 'id_asignacion id_equipo_maquinaria id_obra fecha_asignacion fecha_retiro estado', True),
    'compras_detalle': ('Visualizar_ordenes_compra', 't_orden_compra_detalle', 'id_detalle id_orden_compra id_material cantidad_solicitada cantidad_recibida precio_unitario subtotal', False),
    'apu': ('Visualizar_estimaciones', 't_analisis_precio_unitario', 'id_analisis_precio_unitario id_obra codigo nombre id_unidad_medida tipo_analisis_precio_unitario calidad activo rendimiento costo_materiales costo_directo precio_unitario_final', True),
    'ordenes_trabajo': ('Visualizar_ordenes_trabajo', 't_orden_trabajo', 'orden_nro id_obra tipo_trab estado fecha_inicio fecha_fin', True),
    'crm_clientes': ('Visualizar_clientes', 't_crm_cliente', 'id_cliente nombre_completo tipo_cliente estado origen presupuesto_estimado id_usuario_asignado created_at', False),
    'usuarios': ('Visualizar_usuarios', 't_usuario', 'id_usuario username nombre_completo id_rol estado', False),
    'mano_de_obra': ('Visualizar_mano_obra', 't_mano_obra', 'id_mano_obra nombre id_unidad_medida costo_unitario activo', False),
}

MONEY = {'precio','precio_unitario','precio_unitario_final','monto','monto_total','subtotal','total',
         'presupuesto_estimado','costo_materiales','costo_directo','costo_unitario','saldo_estimado',
         'monto_pactado','costos_registrados','costo_presupuestado','presupuesto_revisado','costo_ejecutado'}


def field_owner(query, field):
    for lookup in query.cruces:
        if field and field.startswith(lookup.prefijo+'_'):
            return lookup.fuente, lookup.prefijo+'_', field[len(lookup.prefijo)+1:]
    return query.fuente, '', field


def fields(source):
    if source in REGISTRY:
        return set(FIELDS[source].split())
    if source in MODULES:
        return set(MODULES[source][2].split())
    raise HTTPException(422, 'Fuente de consulta desconocida.')


def permitted(ctx, source):
    if source in REGISTRY:
        return ((ctx.rol == 'ADMINISTRADOR' or 'Visualizar_reportes' in ctx.permisos)
                and allowed(ctx, REGISTRY[source])
                and (source != 'stock' or ctx.rol in {'ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA'}))
    if source not in MODULES or ctx.rol == 'CLIENTE' or ctx.rol in WORKERS:
        return False
    return ctx.rol == 'ADMINISTRADOR' or MODULES[source][0] in ctx.permisos


def catalog(ctx):
    sources = list(REGISTRY) + list(MODULES)
    return [dict(fuente=s, campos=sorted(fields(s)),
                 descripcion=REGISTRY[s].descripcion if s in REGISTRY else f'Lectura del módulo {s}.',
                 empresa=(s == 'stock' or (s in MODULES and not MODULES[s][3])),
                 fechas=REGISTRY[s].fecha if s in REGISTRY else False)
            for s in sources if permitted(ctx, s)]


def validate(query):
    valid = fields(query.fuente)
    prefixes = set()
    relation_keys = {'id_obra','id_material','id_proveedor','id_usuario','id_orden_compra','id_equipo_maquinaria'}
    for lookup in query.cruces:
        if lookup.prefijo in prefixes or lookup.campo not in valid or lookup.clave not in fields(lookup.fuente) or lookup.clave not in relation_keys:
            raise HTTPException(422, 'Cruce fuera de las relaciones registradas.')
        # Solo relaciones por el mismo identificador, nunca una combinación arbitraria.
        if lookup.campo != lookup.clave and not any(lookup.campo == prefix + '_' + lookup.clave for prefix in prefixes):
            raise HTTPException(422, 'El cruce debe usar el mismo identificador de recurso.')
        prefixes.add(lookup.prefijo)
        additions = {lookup.prefijo + '_' + k for k in fields(lookup.fuente)}
        if additions & valid:
            raise HTTPException(422, 'El prefijo del cruce duplica campos.')
        valid |= additions
    refs = set(query.campos + query.agrupar_por)
    refs.update(c.campo for c in query.condiciones)
    refs.update(c.comparar_campo for c in query.condiciones if c.comparar_campo)
    refs.update(m.campo for m in query.metricas if m.campo)
    names = [m.nombre for m in query.metricas]
    if refs - valid or len(names) != len(set(names)) or set(names) & valid:
        raise HTTPException(422, 'Campos o métricas fuera del contrato de la fuente.')
    if len(query.campos) != len(set(query.campos)) or len(query.agrupar_por) != len(set(query.agrupar_por)):
        raise HTTPException(422, 'No repitas campos en la consulta.')
    if any(m.operacion != 'count' and not m.campo for m in query.metricas):
        raise HTTPException(422, 'La métrica necesita un campo.')
    if query.agrupar_por and not query.metricas:
        raise HTTPException(422, 'La agrupación necesita métricas.')
    # Evitar mezclar monedas o sumar versiones de un presupuesto como si fueran partidas.
    if query.metricas:
        required = {'moneda'} & valid if any(m.operacion in {'sum', 'avg'} for m in query.metricas) else set()
        for metric in query.metricas:
            source, prefix, column = field_owner(query, metric.campo)
            if metric.operacion in {'sum','avg','min','max'} and column in MONEY:
                if 'moneda' not in fields(source):
                    raise HTTPException(422, 'Esta fuente no registra moneda; no puedo agregar importes como una métrica monetaria fiable. Consulta registros individuales o una fuente con moneda.')
                required.add(prefix+'moneda')
                if source=='presupuestario':
                    required.update({prefix+'id_obra',prefix+'version'})
        if query.fuente == 'presupuestario' and any(m.operacion in {'sum', 'avg'} for m in query.metricas):
            required.update({'id_obra', 'version'})
        if required - set(query.agrupar_por):
            raise HTTPException(422, 'Agrupa por ' + ', '.join(sorted(required)) + ' para no mezclar monedas o versiones.')
        quantities = {'stock_actual','stock_minimo','cantidad_asignada','cantidad_solicitada','cantidad_recibida'}
        if any(m.operacion == 'sum' and m.campo in quantities for m in query.metricas):
            unit_groups = {'id_material','id_unidad_medida','unidad_nombre','unidad_abreviatura'}
            if not set(query.agrupar_por) & unit_groups:
                raise HTTPException(422, 'Agrupa las cantidades por material o unidad para no mezclar unidades.')
        output = set(query.agrupar_por) | set(names)
        if query.campos and set(query.campos) - output:
            raise HTTPException(422, 'Los campos de salida deben pertenecer a la agrupación.')
    else:
        output = valid
    if query.ordenar_por and query.ordenar_por not in output:
        raise HTTPException(422, 'Ordenación fuera de los campos de salida.')
    for c in query.condiciones:
        if c.operador == 'in' and (not isinstance(c.valor, list) or len(c.valor) > 50):
            raise HTTPException(422, 'El filtro in admite hasta 50 valores.')
        if isinstance(c.valor, str) and len(c.valor) > 200:
            raise HTTPException(422, 'Valor de filtro demasiado extenso.')
    return query


def decimal(value):
    try:
        result = Decimal(str(value))
        if not result.is_finite():
            raise InvalidOperation()
        return result
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(422, 'La operación requiere valores numéricos finitos.')


def matches(row, condition):
    from app.services.reportes.interpreter import normalize
    a = row.get(condition.campo)
    b = row.get(condition.comparar_campo) if condition.comparar_campo else condition.valor
    op = condition.operador
    if op == 'is_null':
        return (a is None) == (b is not False)
    if a is None or b is None:
        return op == 'eq' and a is b
    if op == 'contains':
        return normalize(str(b)) in normalize(str(a))
    if op == 'in':
        return any(matches(row, Condition(campo=condition.campo, operador='eq', valor=item)) for item in b)
    if isinstance(a, (int, float, Decimal)) and not isinstance(a, bool):
        a, b = decimal(a), decimal(b)
    elif isinstance(a, (date, datetime)):
        a, b = a.isoformat(), str(b)
    else:
        a, b = normalize(str(a)), normalize(str(b))
    return {'eq': lambda: a == b, 'ne': lambda: a != b, 'lt': lambda: a < b,
            'lte': lambda: a <= b, 'gt': lambda: a > b, 'gte': lambda: a >= b}[op]()


def evaluate(query, rows):
    validate(query)
    if len(rows) > 20000:
        raise HTTPException(422, 'Más de 20.000 filas: acota la fuente antes de consultar.')
    selected = [r for r in rows if all(matches(r, c) for c in query.condiciones)]
    matched = len(selected)
    if query.metricas:
        groups = {}
        for row in selected:
            key = tuple(row.get(k) for k in query.agrupar_por)
            groups.setdefault(key, []).append(row)
        if not query.agrupar_por and not groups:
            groups[()] = []
        selected = []
        for key, group in groups.items():
            result = dict(zip(query.agrupar_por, key))
            for metric in query.metricas:
                values = [r[metric.campo] for r in group if r.get(metric.campo) is not None] if metric.campo else []
                if metric.operacion == 'count':
                    value = len(values) if metric.campo else len(group)
                elif metric.operacion == 'count_distinct':
                    value = len(set(values))
                elif metric.operacion in {'sum', 'avg'}:
                    numbers = [decimal(v) for v in values]
                    value = sum(numbers, Decimal(0)) if metric.operacion == 'sum' else (sum(numbers, Decimal(0))/len(numbers) if numbers else None)
                else:
                    value = (min(values) if metric.operacion == 'min' else max(values)) if values else None
                result[metric.nombre] = value
            selected.append(result)
    if query.ordenar_por:
        key = query.ordenar_por
        monetary = field_owner(query,key)[2] in MONEY or any(m.nombre == key and field_owner(query,m.campo)[2] in MONEY for m in query.metricas)
        if monetary and len({r.get('moneda') for r in selected if r.get('moneda') is not None})>1:
            raise HTTPException(422, 'Selecciona una moneda para ordenar importes; no se comparan monedas distintas.')
        selected = sorted([r for r in selected if r.get(key) is not None], key=lambda r: r[key], reverse=query.orden == 'desc') + [r for r in selected if r.get(key) is None]
    count = len(selected)
    output_fields = fields(query.fuente)
    for lookup in query.cruces:
        output_fields |= {lookup.prefijo + '_' + k for k in fields(lookup.fuente)}
    columns = query.campos or (query.agrupar_por + [m.nombre for m in query.metricas] if query.metricas else sorted(output_fields))
    result = dict(fuente=query.fuente, registros_filtrados=matched, total_resultados=count,
                detalle_completo=count <= query.limite, columnas=columns,
                filas=[{k: r.get(k) for k in columns} for r in selected[:query.limite]])
    if len(json.dumps(result, default=str, ensure_ascii=False).encode('utf-8'))>200000:
        raise HTTPException(422, 'El detalle es demasiado extenso; reduce campos o límite de filas.')
    return result


def execute(db, ctx, queries):
    from app.repos import assistant_repos
    from app.services import reportes_services as reports
    result, scopes = [], []
    cache = {}
    def read(source):
        if not permitted(ctx, source.fuente):
            raise HTTPException(403, 'La fuente no está habilitada para tu cuenta.')
        key = (source.fuente, source.filtros_fuente.model_dump_json())
        if key not in cache:
            if source.fuente in REGISTRY:
                request = ReportRequest(reporte=source.fuente, filtros=source.filtros_fuente)
                _, scope = authorize(db, ctx, request)
                report, _ = reports.build(db, ctx, request, source_allowlist=[])
                rows, warning = report['filas'], report['advertencias']
            else:
                rows, scope = assistant_repos.read_module(db, ctx, source)
                warning = ['Datos registrados del módulo; no acredita cobros, disponibilidad futura ni predicciones.']
            if len(rows)>20000:
                raise HTTPException(422, 'Acota la fuente: más de 20.000 filas.')
            cache[key] = rows, scope, warning
        return cache[key]
    for query in queries:
        validate(query)
        rows, scope, warning = read(query)
        scopes.append((query, scope))
        for lookup in query.cruces:
            target = Query(fuente=lookup.fuente)
            # Lectura completa para el cruce; el límite de presentación no limita sus métricas.
            right, right_scope, right_warning = read(target)
            warning = warning + right_warning
            index = {}
            for row in right:
                key = row.get(lookup.clave)
                if key is None:
                    continue
                if key in index:
                    raise HTTPException(422, 'El cruce multiplica filas; selecciona una fuente con identificador único.')
                index[key] = row
            rows = [dict(row, **{lookup.prefijo+'_'+k: index.get(row.get(lookup.campo),{}).get(k)
                                for k in fields(lookup.fuente)}) for row in rows]
            scopes.append((target, right_scope))
        result.append(dict(evaluate(query, rows), advertencias=warning))
        if len(json.dumps(result, default=str, ensure_ascii=False).encode('utf-8'))>200000:
            raise HTTPException(422, 'El conjunto de consultas es demasiado extenso; reduce campos o filas.')
    return result, scopes


def reauthorize(db, ctx, scopes):
    from app.repos import reportes_repos as repo
    for query, scope in scopes:
        if not permitted(ctx, query.fuente):
            raise HTTPException(403, 'Los permisos de consulta cambiaron.')
        if query.fuente in REGISTRY:
            _, current = authorize(db, ctx, ReportRequest(reporte=query.fuente, filtros=query.filtros_fuente))
        else:
            current = [w['id_obra'] for w in repo.works(db, ctx)] if MODULES[query.fuente][3] else []
        if not set(scope).issubset(current):
            raise HTTPException(403, 'El ámbito autorizado cambió durante la consulta.')
