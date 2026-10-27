"""Análisis determinista de salud operativa, desviaciones y recomendaciones de OBRATEC.
Mantiene cálculos financieros y conteos estrictamente en backend con agregaciones SQL y funciones almacenadas,
prohibiendo alucinaciones matemáticas del modelo de lenguaje y aplicando RBAC estricto por dominio y fila.
"""
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from app.repos import reportes_repos as repo
from app.services.reportes.catalog import WORKERS
from app.repos import assistant_repos

SOURCE_PERMISSIONS = {
    'incidencias': 'Visualizar_incidencias',
    'ordenes_trabajo': 'Visualizar_ordenes_trabajo',
    'inventario': 'Visualizar_inventario',
    'consultas_tecnicas': 'Visualizar_consultas_tecnicas',
}


def fuentes_permitidas(ctx):
    if ctx.rol == 'CLIENTE':
        return set()
    sources = {source for source, permission in SOURCE_PERMISSIONS.items() if _tiene_permiso(ctx, permission)}
    if ctx.rol not in {'ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA'}:
        sources.discard('inventario')
    if ctx.rol in WORKERS:
        sources.discard('consultas_tecnicas')
    return sources


def reautorizar(db, ctx, alcance):
    if ctx.policy() != alcance['politica'] or set(alcance['fuentes']) - fuentes_permitidas(ctx):
        raise HTTPException(403, 'Los permisos del diagnóstico cambiaron. Realice una nueva consulta.')
    if not set(alcance['obras']).issubset({w['id_obra'] for w in repo.works(db, ctx)}):
        raise HTTPException(403, 'Las obras autorizadas del diagnóstico cambiaron.')
    if ctx.rol in WORKERS:
        assistant_repos.reauthorize_diagnostic_records(db, ctx, alcance.get('registros', {}))


def _tiene_permiso(ctx, permiso: str) -> bool:
    if ctx.rol == "ADMINISTRADOR":
        return True
    return permiso in ctx.permisos


def analizar_con_alcance(db, ctx, id_obra: int | None = None):
    """Evalúa indicadores cruzados de obras, inventario, órdenes de trabajo e incidencias.
    Aplica autorización individual por dominio (A3) y consume funciones reales de PostgreSQL (A4).
    Retorna nivel de riesgo, indicadores, recomendaciones, fuentes consultadas y omitidas.
    """
    hoy = datetime.now(ZoneInfo("America/La_Paz")).date()
    empresa = ctx.empresa
    obras_autorizadas = [w["id_obra"] for w in repo.works(db, ctx)]
    permitidas = fuentes_permitidas(ctx)
    alcance = dict(politica=ctx.policy(), obras=[], fuentes=[], registros={})

    if id_obra:
        if id_obra not in obras_autorizadas:
            raise HTTPException(403, "La obra no pertenece al ámbito autorizado del usuario.")
        obras_filtro = [id_obra]
    else:
        obras_filtro = obras_autorizadas

    if not obras_filtro:
        return {
            "tipo": "analisis_salud",
            "fecha_corte": hoy.isoformat(),
            "nivel_riesgo": "BAJO",
            "puntos_riesgo": 0,
            "indicadores": [],
            "recomendaciones": [{
                "prioridad": "BAJA",
                "accion": "Sin obras asignadas",
                "justificacion": "No existen obras autorizadas para evaluar en el contexto actual."
            }],
            "obras_evaluadas": 0,
            "fuentes_consultadas": [],
            "fuentes_omitidas": [{"modulo": "global", "motivo": "Sin obras autorizadas"}],
        }, alcance

    indicadores = []
    recomendaciones = []
    fuentes_consultadas = []
    alcance['obras'] = obras_filtro
    alcance['fuentes'] = fuentes_consultadas
    fuentes_omitidas = []
    puntos_riesgo = 0

    es_trabajador = ctx.rol in WORKERS or ctx.rol == "TRABAJADOR"

    # 1. Indicador: Incidencias críticas abiertas (A3)
    if 'incidencias' in permitidas:
        fuentes_consultadas.append("incidencias")
        # Restricción por fila para trabajadores: solo sus asignadas o reportadas
        if es_trabajador:
            filtro_trabajador = "AND (i.id_responsable = %s OR i.id_usuario_registro = %s)"
            params_inc = (empresa, obras_filtro, ctx.usuario, ctx.usuario)
        else:
            filtro_trabajador = ""
            params_inc = (empresa, obras_filtro)

        sql_inc = f"""
            SELECT i.id_incidencia, i.id_obra, o.nombre AS obra, i.titulo, i.prioridad, i.created_at
            FROM obras.t_incidencia i
            JOIN obras.t_obra o ON o.id_obra = i.id_obra
            WHERE o.id_empresa = %s
              AND i.id_obra = ANY(%s)
              AND i.prioridad IN ('ALTA', 'CRITICA')
              AND i.estado IN ('ABIERTA', 'ASIGNADA', 'EN_PROCESO')
              {filtro_trabajador}
            ORDER BY i.created_at ASC
        """
        incidencias_criticas = repo.rows(db, sql_inc, params_inc)
        alcance['registros']['incidencias'] = [i['id_incidencia'] for i in incidencias_criticas]

        if incidencias_criticas:
            puntos_riesgo += len(incidencias_criticas) * 2
            indicadores.append({
                "codigo": "INCIDENCIAS_CRITICAS",
                "titulo": "Incidencias de alta prioridad activas",
                "valor": len(incidencias_criticas),
                "estado": "CRITICO" if any(i["prioridad"] == "CRITICA" for i in incidencias_criticas) else "ALERTA",
                "detalle": f"{len(incidencias_criticas)} incidencia(s) crítica(s) o alta(s) pendientes de resolución."
            })
            recomendaciones.append({
                "prioridad": "ALTA",
                "accion": "Resolver incidencias prioritarias",
                "justificacion": f"Existen {len(incidencias_criticas)} problemas críticos en campo (ej. '{incidencias_criticas[0]['titulo']}' en obra {incidencias_criticas[0]['obra']})."
            })
    else:
        fuentes_omitidas.append({"modulo": "incidencias", "motivo": "Sin permiso Visualizar_incidencias"})

    # 2. Indicador: Órdenes de Trabajo atrasadas (A3)
    if 'ordenes_trabajo' in permitidas:
        fuentes_consultadas.append("ordenes_trabajo")
        if es_trabajador:
            filtro_ot_trab = """AND EXISTS (
                SELECT 1 FROM obras.t_orden_trabajo_usuario otu
                WHERE otu.id_orden_trabajo = ot.orden_nro AND otu.id_usuario = %s
            )"""
            params_ot = (empresa, obras_filtro, hoy, ctx.usuario)
        else:
            filtro_ot_trab = ""
            params_ot = (empresa, obras_filtro, hoy)

        sql_ot = f"""
            SELECT ot.orden_nro, ot.id_obra, o.nombre AS obra, ot.tipo_trab, ot.fecha_fin, ot.estado
            FROM obras.t_orden_trabajo ot
            JOIN obras.t_obra o ON o.id_obra = ot.id_obra
            WHERE o.id_empresa = %s
              AND ot.id_obra = ANY(%s)
              AND ot.fecha_fin < %s
              AND ot.estado NOT IN ('FINALIZADA', 'CANCELADA')
              {filtro_ot_trab}
            ORDER BY ot.fecha_fin ASC
        """
        ots_atrasadas = repo.rows(db, sql_ot, params_ot)
        alcance['registros']['ordenes_trabajo'] = [ot['orden_nro'] for ot in ots_atrasadas]

        if ots_atrasadas:
            puntos_riesgo += len(ots_atrasadas) * 2
            indicadores.append({
                "codigo": "OTS_ATRASADAS",
                "titulo": "Órdenes de Trabajo vencidas",
                "valor": len(ots_atrasadas),
                "estado": "ALERTA",
                "detalle": f"{len(ots_atrasadas)} OT(s) superaron su fecha límite de finalización."
            })
            recomendaciones.append({
                "prioridad": "MEDIA",
                "accion": "Reprogramar o inspeccionar OTs atrasadas",
                "justificacion": f"{len(ots_atrasadas)} orden(es) como 'OT-{ots_atrasadas[0]['orden_nro']}: {ots_atrasadas[0]['tipo_trab']}' vencieron el {ots_atrasadas[0]['fecha_fin']}."
            })
    else:
        fuentes_omitidas.append({"modulo": "ordenes_trabajo", "motivo": "Sin permiso Visualizar_ordenes_trabajo"})

    # 3. Indicador: Déficit de Stock de Materiales (A3, A4)
    # Exclusivo para usuarios con permiso de materiales o administradores
    if 'inventario' in permitidas:
        fuentes_consultadas.append("inventario")
        # Función oficial existente en PostgreSQL: fn_listar_inventario_empresa (A4)
        materiales_deficit = repo.rows(
            db,
            "SELECT id_material, codigo, nombre_material, precio, stock_actual, stock_minimo, total_count "
            "FROM obras.fn_listar_inventario_empresa(%s, NULL, 'SIN_STOCK', NULL, 20, 0)",
            (empresa,)
        )

        if materiales_deficit:
            puntos_riesgo += min(len(materiales_deficit), 4)
            indicadores.append({
                "codigo": "STOCK_AGOTADO",
                "titulo": "Materiales con stock agotado",
                "valor": int(materiales_deficit[0]['total_count']),
                "estado": "CRITICO",
                "detalle": f"{materiales_deficit[0]['total_count']} materiales registran stock cero; muestra de hasta 20."
            })
            recomendaciones.append({
                "prioridad": "ALTA",
                "accion": "Generar requisiciones de compra para insumos agotados",
                "justificacion": f"Insumos críticos como '{materiales_deficit[0]['nombre_material']}' ({materiales_deficit[0]['codigo']}) están sin existencias en almacén."
            })
    else:
        fuentes_omitidas.append({"modulo": "inventario", "motivo": "Requiere permiso Visualizar_inventario y ámbito empresarial"})

    # 4. Indicador: Consultas Técnicas (RFI) pendientes (A3)
    if 'consultas_tecnicas' in permitidas:
        fuentes_consultadas.append("consultas_tecnicas")
        rfis_pendientes = repo.rows(db, """
            SELECT ct.id_consulta_tecnica, ct.codigo, ct.asunto, o.nombre AS obra, ct.created_at
            FROM obras.t_consulta_tecnica ct
            JOIN obras.t_obra o ON o.id_obra = ct.id_obra
            WHERE ct.id_empresa = %s
              AND ct.id_obra = ANY(%s)
              AND ct.estado IN ('ABIERTA', 'ASIGNADA')
            ORDER BY ct.created_at ASC
        """, (empresa, obras_filtro))

        if rfis_pendientes:
            puntos_riesgo += 1
            indicadores.append({
                "codigo": "CONSULTAS_TECNICAS_PENDIENTES",
                "titulo": "Consultas técnicas RFI sin responder",
                "valor": len(rfis_pendientes),
                "estado": "INFORMATIVO",
                "detalle": f"{len(rfis_pendientes)} aclaración(es) técnica(s) pendientes de respuesta."
            })
    else:
        fuentes_omitidas.append({"modulo": "consultas_tecnicas", "motivo": "Sin permiso Visualizar_consultas_tecnicas"})

    # Evaluación determinista del nivel de riesgo
    if puntos_riesgo >= 5:
        nivel_riesgo = "ALTO"
    elif puntos_riesgo >= 2:
        nivel_riesgo = "MEDIO"
    else:
        nivel_riesgo = "BAJO"

    if not recomendaciones:
        recomendaciones.append({
            "prioridad": "BAJA",
            "accion": "Mantener supervisión periódica",
            "justificacion": "No se detectaron desviaciones críticas en los dominios y proyectos evaluados."
        })

    return {
        "tipo": "analisis_salud",
        "fecha_corte": hoy.isoformat(),
        "nivel_riesgo": nivel_riesgo,
        "puntos_riesgo": puntos_riesgo,
        "indicadores": indicadores,
        "recomendaciones": recomendaciones,
        "obras_evaluadas": len(obras_filtro),
        "fuentes_consultadas": fuentes_consultadas,
        "fuentes_omitidas": fuentes_omitidas,
    }, alcance


def analizar_salud_operativa(db, ctx, id_obra: int | None = None) -> dict[str, Any]:
    return analizar_con_alcance(db, ctx, id_obra)[0]
