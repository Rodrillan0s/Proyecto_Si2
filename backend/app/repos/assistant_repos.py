"""Lecturas modulares parametrizadas; ningún SQL o identificador proviene del modelo."""
from fastapi import HTTPException
from app.repos import reportes_repos as repo


def read_module(db, ctx, query):
    from app.services.ai.query_engine import MODULES
    _, table, columns, by_work = MODULES[query.fuente]
    if any(v is not None for k, v in query.filtros_fuente.model_dump().items() if k != 'id_obra'):
        raise HTTPException(422, 'Esta fuente usa condiciones por campo para fechas y estados.')
    if query.filtros_fuente.id_obra and not by_work:
        raise HTTPException(422, 'Esta fuente es empresarial; no tiene distribución por obra.')
    names = columns.split()
    # Comprobar objetos actuales sin migrar ni suponer aplicada la fotografía documentada.
    parent_tables = {'t_orden_trabajo','t_equipo_maquinaria_obra','t_orden_compra_detalle'}
    required = (set(names) - {'nombre_completo'}) | ({'id_empresa'} if table not in parent_tables else set())
    if table in {'t_usuario','t_crm_cliente'}:
        required.add('id_persona')
    actual = repo.rows(db, 'SELECT column_name FROM information_schema.columns WHERE table_schema=%s AND table_name=%s', ('obras', table))
    if required - {r['column_name'] for r in actual}:
        raise HTTPException(503, 'La fuente del módulo no coincide con el esquema disponible.')
    sql = 'SELECT ' + ','.join('p.nombre_completo' if c=='nombre_completo' else 's.' + c for c in names) + ' FROM obras.' + table + ' s '
    scope, params = [], [ctx.empresa]
    if table == 't_equipo_maquinaria_obra':
        sql += 'JOIN obras.t_obra o ON o.id_obra=s.id_obra JOIN obras.t_equipo_maquinaria em ON em.id_equipo_maquinaria=s.id_equipo_maquinaria WHERE o.id_empresa=%s AND em.id_empresa=o.id_empresa '
    elif table == 't_orden_trabajo':
        sql += 'JOIN obras.t_obra o ON o.id_obra=s.id_obra WHERE o.id_empresa=%s '
    elif table == 't_orden_compra_detalle':
        sql += 'JOIN obras.t_orden_compra oc ON oc.id_orden_compra=s.id_orden_compra JOIN obras.t_material m ON m.id_material=s.id_material WHERE oc.id_empresa=%s AND m.id_empresa=oc.id_empresa '
    elif table == 't_crm_cliente':
        sql += 'JOIN obras.t_persona p ON p.id_persona=s.id_persona WHERE s.id_empresa=%s '
    elif table == 't_usuario':
        sql += 'LEFT JOIN obras.t_persona p ON p.id_persona=s.id_persona WHERE s.id_empresa=%s '
    else:
        sql += 'WHERE s.id_empresa=%s '
    if by_work:
        scope = [w['id_obra'] for w in repo.works(db, ctx)]
        if query.filtros_fuente.id_obra:
            if query.filtros_fuente.id_obra not in scope:
                raise HTTPException(403, 'La obra no pertenece al ámbito autorizado.')
            scope = [query.filtros_fuente.id_obra]
        sql += 'AND (s.id_obra=ANY(%s)' + (' OR s.id_obra IS NULL' if table=='t_analisis_precio_unitario' and not query.filtros_fuente.id_obra else '') + ') '
        params.append(scope)
    sql += 'ORDER BY s.' + names[0] + ' LIMIT 20001'
    return repo.rows(db, sql, params), scope
