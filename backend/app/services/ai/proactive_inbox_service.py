"""Servicio proactivo consolidado de pendientes priorizados por perfil y permisos.

Consolida pendientes de múltiples módulos respetando:
- Aislamiento multiempresa (ctx.empresa)
- Ámbito de obras autorizadas (repo.works)
- RBAC de authorization.py (ctx.permisos / ctx.rol)
- RLS por fila para CLIENTE y WORKERS
- Enlaces directos a rutas reales del frontend Angular
"""
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from app.repos import reportes_repos as repo
from app.services.reportes.catalog import WORKERS


PRIORITY_ORDER = {'CRITICA': 0, 'ALTA': 1, 'MEDIA': 2, 'BAJA': 3}


def _has(ctx, permiso: str) -> bool:
    return ctx.rol == 'ADMINISTRADOR' or permiso in ctx.permisos


def consultar_pendientes(
    db,
    ctx,
    horizonte_dias: int = 7,
    id_obra: int | None = None,
) -> dict[str, Any]:
    """Devuelve bandeja consolidada y priorizada de pendientes según el perfil del actor."""
    horizonte = max(1, min(int(horizonte_dias or 7), 60))
    hoy = datetime.now(ZoneInfo('America/La_Paz')).date()
    limite_fecha = hoy + timedelta(days=horizonte)

    obras_autorizadas = [w['id_obra'] for w in repo.works(db, ctx)]
    if id_obra is not None:
        if id_obra not in obras_autorizadas:
            raise HTTPException(403, 'La obra solicitada no pertenece a su ámbito autorizado.')
        obras_filtro = [id_obra]
    else:
        obras_filtro = obras_autorizadas

    es_worker = ctx.rol in WORKERS
    es_cliente = ctx.rol == 'CLIENTE'
    items: list[dict[str, Any]] = []
    fuentes_consultadas: list[str] = []
    fuentes_omitidas: list[dict[str, str]] = []

    # 1. Incidencias activas (no CLIENTE)
    if not es_cliente and obras_filtro and _has(ctx, 'Visualizar_incidencias'):
        fuentes_consultadas.append('incidencias')
        extra = 'AND (i.id_responsable = %s OR i.id_usuario_registro = %s)' if es_worker else ''
        params = [ctx.empresa, obras_filtro] + ([ctx.usuario, ctx.usuario] if es_worker else [])
        rows = repo.rows(db, f"""
            SELECT i.id_incidencia, i.id_obra, o.nombre AS obra, i.titulo, i.prioridad, i.estado, i.created_at
            FROM obras.t_incidencia i
            JOIN obras.t_obra o ON o.id_obra = i.id_obra
            WHERE o.id_empresa = %s AND i.id_obra = ANY(%s)
              AND i.estado IN ('ABIERTA', 'ASIGNADA', 'EN_PROCESO')
              {extra}
            ORDER BY CASE i.prioridad WHEN 'CRITICA' THEN 0 WHEN 'ALTA' THEN 1 WHEN 'MEDIA' THEN 2 ELSE 3 END, i.created_at ASC
            LIMIT 15
        """, params)
        for r in rows:
            prio = r['prioridad'] if r['prioridad'] in PRIORITY_ORDER else 'MEDIA'
            items.append({
                'modulo': 'Incidencias',
                'tipo': 'INCIDENCIA_ACTIVA',
                'id_recurso': r['id_incidencia'],
                'titulo': r['titulo'],
                'obra': r['obra'],
                'fecha_limite': None,
                'prioridad': prio,
                'motivo': f"Incidencia en estado {r['estado']} (prioridad {prio})",
                'ruta_angular': f"/incidencias/{r['id_incidencia']}",
            })

    # 2. Órdenes de trabajo vencidas o por vencer (no CLIENTE)
    if not es_cliente and obras_filtro and _has(ctx, 'Visualizar_obras'):
        fuentes_consultadas.append('ordenes_trabajo')
        extra = (
            'AND EXISTS(SELECT 1 FROM obras.t_orden_trabajo_usuario otu WHERE otu.id_orden_trabajo = ot.orden_nro AND otu.id_usuario = %s)'
            if es_worker else ''
        )
        params = [ctx.empresa, obras_filtro, limite_fecha] + ([ctx.usuario] if es_worker else [])
        rows = repo.rows(db, f"""
            SELECT ot.orden_nro, ot.id_obra, o.nombre AS obra, ot.tipo_trab, ot.fecha_fin, ot.estado
            FROM obras.t_orden_trabajo ot
            JOIN obras.t_obra o ON o.id_obra = ot.id_obra
            WHERE o.id_empresa = %s AND ot.id_obra = ANY(%s)
              AND ot.estado NOT IN ('FINALIZADA', 'CANCELADA')
              AND ot.fecha_fin IS NOT NULL AND ot.fecha_fin <= %s
              {extra}
            ORDER BY ot.fecha_fin ASC
            LIMIT 15
        """, params)
        for r in rows:
            vencida = r['fecha_fin'] < hoy
            items.append({
                'modulo': 'Órdenes de trabajo',
                'tipo': 'OT_VENCIDA' if vencida else 'OT_PROXIMA',
                'id_recurso': r['orden_nro'],
                'titulo': f"OT #{r['orden_nro']} · {r['tipo_trab']}",
                'obra': r['obra'],
                'fecha_limite': r['fecha_fin'].isoformat(),
                'prioridad': 'ALTA' if vencida else 'MEDIA',
                'motivo': 'Orden de trabajo vencida' if vencida else f"Vence el {r['fecha_fin'].isoformat()}",
                'ruta_angular': '/ordenes-trabajo',
            })

    # 3. Actividades de cronograma vencidas o próximas (CU39)
    if not es_cliente and obras_filtro and _has(ctx, 'Visualizar_cronograma'):
        fuentes_consultadas.append('cronogramas')
        rows = repo.rows(db, """
            SELECT ca.id_cronograma, ca.clave, cr.id_obra, o.nombre AS obra, ca.nombre, ca.tipo, ca.fecha_fin, ca.avance
            FROM obras.t_cronograma_actividad ca
            JOIN obras.t_cronograma cr ON cr.id_cronograma = ca.id_cronograma
            JOIN obras.t_obra o ON o.id_obra = cr.id_obra
            WHERE o.id_empresa = %s AND cr.id_obra = ANY(%s)
              AND ca.fin_real IS NULL AND ca.fecha_fin <= %s
            ORDER BY ca.fecha_fin ASC
            LIMIT 15
        """, (ctx.empresa, obras_filtro, limite_fecha))
        for r in rows:
            vencida = r['fecha_fin'] < hoy
            items.append({
                'modulo': 'Cronogramas',
                'tipo': 'ACTIVIDAD_RETRASADA' if vencida else 'ACTIVIDAD_PROXIMA',
                'id_recurso': f"{r['id_cronograma']}:{r['clave']}",
                'titulo': f"{r['nombre']} ({r['avance']}%)",
                'obra': r['obra'],
                'fecha_limite': r['fecha_fin'].isoformat(),
                'prioridad': 'ALTA' if vencida else 'MEDIA',
                'motivo': 'Actividad/hito con fin previsto vencido' if vencida else f"Fin previsto {r['fecha_fin'].isoformat()}",
                'ruta_angular': f"/proyectos/{r['id_obra']}/cronogramas",
            })

    # 4. Aprobaciones pendientes: Órdenes de cambio (CU17)
    if not es_cliente and not es_worker and obras_filtro and _has(ctx, 'Aprobar_ordenes_cambio'):
        fuentes_consultadas.append('aprobaciones_ordenes_cambio')
        rows = repo.rows(db, """
            SELECT ocm.id_orden_cambio, ocm.codigo, ocm.titulo, ocm.fecha, o.nombre AS obra
            FROM obras.t_orden_cambio ocm
            JOIN obras.t_obra o ON o.id_obra = ocm.id_obra
            WHERE o.id_empresa = %s AND ocm.id_obra = ANY(%s) AND ocm.estado = 'PENDIENTE'
            ORDER BY ocm.fecha ASC
            LIMIT 10
        """, (ctx.empresa, obras_filtro))
        for r in rows:
            items.append({
                'modulo': 'Control de costos',
                'tipo': 'APROBACION_ORDEN_CAMBIO',
                'id_recurso': r['id_orden_cambio'],
                'titulo': f"Orden de cambio {r['codigo']} · {r['titulo']}",
                'obra': r['obra'],
                'fecha_limite': r['fecha'].isoformat() if r['fecha'] else None,
                'prioridad': 'ALTA',
                'motivo': 'Pendiente de aprobación presupuestaria',
                'ruta_angular': '/control-costos',
            })

    # 5. Compras pendientes de aprobación o recepción
    if not es_cliente and not es_worker and _has(ctx, 'Visualizar_ordenes_compra'):
        fuentes_consultadas.append('compras')
        rows = repo.rows(db, """
            SELECT oc.id_orden_compra, oc.numero_orden, oc.estado, oc.fecha
            FROM obras.t_orden_compra oc
            WHERE oc.id_empresa = %s AND oc.estado IN ('SOLICITADA', 'APROBADA', 'RECIBIDA_PARCIAL')
            ORDER BY oc.fecha ASC
            LIMIT 10
        """, (ctx.empresa,))
        for r in rows:
            es_aprob = r['estado'] == 'SOLICITADA'
            items.append({
                'modulo': 'Compras',
                'tipo': 'COMPRA_POR_APROBAR' if es_aprob else 'COMPRA_POR_RECIBIR',
                'id_recurso': r['id_orden_compra'],
                'titulo': f"Orden de compra {r['numero_orden']}",
                'obra': None,
                'fecha_limite': r['fecha'].isoformat() if r['fecha'] else None,
                'prioridad': 'ALTA' if es_aprob else 'MEDIA',
                'motivo': 'Pendiente de aprobación' if es_aprob else f"Pendiente de recepción ({r['estado']})",
                'ruta_angular': '/compras',
            })

    # 6. Seguimientos CRM vencidos o próximos
    if not es_cliente and not es_worker and _has(ctx, 'Visualizar_clientes'):
        fuentes_consultadas.append('crm_seguimientos')
        rows = repo.rows(db, """
            SELECT ci.id_interaccion, p.nombre_completo AS cliente, ci.asunto, ci.fecha_proximo_contacto
            FROM obras.t_crm_interaccion ci
            JOIN obras.t_crm_cliente c ON c.id_cliente = ci.id_cliente
            JOIN obras.t_persona p ON p.id_persona = c.id_persona
            WHERE c.id_empresa = %s
              AND ci.fecha_proximo_contacto IS NOT NULL
              AND ci.fecha_proximo_contacto <= %s
            ORDER BY ci.fecha_proximo_contacto ASC
            LIMIT 10
        """, (ctx.empresa, limite_fecha))
        for r in rows:
            venc = r['fecha_proximo_contacto'] < hoy
            items.append({
                'modulo': 'Clientes',
                'tipo': 'SEGUIMIENTO_CRM',
                'id_recurso': r['id_interaccion'],
                'titulo': f"Seguimiento con {r['cliente']}: {r['asunto']}",
                'obra': None,
                'fecha_limite': r['fecha_proximo_contacto'].isoformat(),
                'prioridad': 'ALTA' if venc else 'MEDIA',
                'motivo': 'Seguimiento comercial vencido' if venc else f"Programado para {r['fecha_proximo_contacto'].isoformat()}",
                'ruta_angular': '/crm',
            })

    # 7. Garantías y Posventa (CU42 — todos los perfiles según alcance)
    try:
        fuentes_consultadas.append('posventa')
        if es_cliente:
            rows = repo.rows(db, """
                SELECT sp.id_solicitud_posventa, sp.titulo, sp.estado, u.codigo AS unidad, o.nombre AS obra
                FROM obras.t_solicitud_posventa sp
                JOIN obras.t_crm_cliente c ON c.id_cliente = sp.id_cliente
                JOIN obras.t_unidad_construccion u ON u.id_unidad = sp.id_unidad
                JOIN obras.t_estructura_obra s ON s.id_estructura = u.id_estructura
                JOIN obras.t_obra o ON o.id_obra = s.id_obra
                WHERE sp.id_empresa = %s AND c.id_persona = %s
                  AND sp.estado NOT IN ('RESUELTA', 'CERRADA')
                ORDER BY sp.creado_en ASC
                LIMIT 10
            """, (ctx.empresa, ctx.persona))
        elif es_worker:
            rows = repo.rows(db, """
                SELECT sp.id_solicitud_posventa, sp.titulo, sp.estado, u.codigo AS unidad, o.nombre AS obra
                FROM obras.t_solicitud_posventa sp
                JOIN obras.t_unidad_construccion u ON u.id_unidad = sp.id_unidad
                JOIN obras.t_estructura_obra s ON s.id_estructura = u.id_estructura
                JOIN obras.t_obra o ON o.id_obra = s.id_obra
                WHERE sp.id_empresa = %s AND sp.id_responsable = %s
                  AND sp.estado NOT IN ('RESUELTA', 'CERRADA')
                ORDER BY sp.creado_en ASC
                LIMIT 10
            """, (ctx.empresa, ctx.usuario))
        else:
            rows = repo.rows(db, """
                SELECT sp.id_solicitud_posventa, sp.titulo, sp.estado, u.codigo AS unidad, o.nombre AS obra
                FROM obras.t_solicitud_posventa sp
                JOIN obras.t_unidad_construccion u ON u.id_unidad = sp.id_unidad
                JOIN obras.t_estructura_obra s ON s.id_estructura = u.id_estructura
                JOIN obras.t_obra o ON o.id_obra = s.id_obra
                WHERE sp.id_empresa = %s AND s.id_obra = ANY(%s)
                  AND sp.estado NOT IN ('RESUELTA', 'CERRADA')
                ORDER BY sp.creado_en ASC
                LIMIT 10
            """, (ctx.empresa, obras_filtro)) if obras_filtro else []
        for r in rows:
            items.append({
                'modulo': 'Garantías y posventa',
                'tipo': 'POSVENTA_ABIERTA',
                'id_recurso': r['id_solicitud_posventa'],
                'titulo': f"Posventa #{r['id_solicitud_posventa']} ({r['unidad']}): {r['titulo']}",
                'obra': r['obra'],
                'fecha_limite': None,
                'prioridad': 'ALTA' if r['estado'] == 'REGISTRADA' else 'MEDIA',
                'motivo': f"Solicitud en estado {r['estado']}",
                'ruta_angular': '/posventa',
            })
    except Exception:
        fuentes_omitidas.append({'modulo': 'posventa', 'motivo': 'Módulo posventa no disponible en este esquema'})

    # Ordenar por prioridad y fecha límite
    items.sort(key=lambda it: (PRIORITY_ORDER.get(it['prioridad'], 9), it['fecha_limite'] or '9999-12-31'))

    resumen = {p: sum(1 for it in items if it['prioridad'] == p) for p in ('CRITICA', 'ALTA', 'MEDIA', 'BAJA')}
    return {
        'fecha_corte': hoy.isoformat(),
        'horizonte_dias': horizonte,
        'total_pendientes': len(items),
        'resumen_por_prioridad': resumen,
        'items': items[:30],
        'fuentes_consultadas': fuentes_consultadas,
        'fuentes_omitidas': fuentes_omitidas,
    }
