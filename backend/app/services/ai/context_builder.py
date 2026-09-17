from app.classes.postgres import PostgreSQL
from app.config import Config
from app.repos import crm_repos


class ContextBuilder:
    """
    Construye contextos mínimos, sanitizados y autorizados para la IA.
    Asegura que Gemini NUNCA reciba toda la base de datos ni datos de otras empresas (HU109).
    """

    @staticmethod
    def construir_contexto_crm(id_empresa: int) -> dict:
        # 1. Obtener nombre de la empresa
        db = PostgreSQL()
        db.create_connection()
        try:
            emp_row = db.execute_query(
                f"SELECT nombre_empresa FROM {Config.SCHEMA}.t_empresa WHERE id_empresa = %s;",
                (id_empresa,), fetchone=True
            )
            nombre_empresa = emp_row[0] if emp_row else f"Empresa #{id_empresa}"

            # 2. Métricas generales del CRM
            metricas = crm_repos.obtener_metricas_crm(id_empresa)

            # 3. Prospectos activos en etapas clave (especialmente EN_NEGOCIACION e INTERESADO)
            sql_prospectos = f"""
                SELECT c.id_cliente, p.nombre_completo, c.estado, c.presupuesto_estimado,
                       c.origen, pu.nombre_completo AS asesor
                FROM {Config.SCHEMA}.t_crm_cliente c
                INNER JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = c.id_persona
                LEFT JOIN {Config.SCHEMA}.t_usuario u ON u.id_usuario = c.id_usuario_asignado
                LEFT JOIN {Config.SCHEMA}.t_persona pu ON pu.id_persona = u.id_persona
                WHERE c.id_empresa = %s AND c.tipo_cliente = 'PROSPECTO' AND c.estado IN ('EN_NEGOCIACION', 'INTERESADO', 'CONTACTADO')
                ORDER BY c.presupuesto_estimado DESC NULLS LAST
                LIMIT 10;
            """
            rows_p = db.execute_query(sql_prospectos, (id_empresa,), fetchall=True) or []
            prospectos_destacados = []
            for r in rows_p:
                prospectos_destacados.append({
                    "id_cliente": r[0],
                    "nombre": r[1],
                    "etapa": r[2],
                    "presupuesto": float(r[3]) if r[3] is not None else "No informado",
                    "origen": r[4],
                    "asesor_asignado": r[5] or "Sin asignar"
                })

            # 4. Últimas 5 interacciones registradas
            sql_interacciones = f"""
                SELECT p.nombre_completo AS cliente, i.tipo, i.asunto, i.detalle,
                       i.fecha_interaccion, i.fecha_proximo_contacto, pu.nombre_completo AS usuario
                FROM {Config.SCHEMA}.t_crm_interaccion i
                INNER JOIN {Config.SCHEMA}.t_crm_cliente c ON c.id_cliente = i.id_cliente
                INNER JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = c.id_persona
                INNER JOIN {Config.SCHEMA}.t_usuario u ON u.id_usuario = i.id_usuario
                INNER JOIN {Config.SCHEMA}.t_persona pu ON pu.id_persona = u.id_persona
                WHERE c.id_empresa = %s
                ORDER BY i.fecha_interaccion DESC
                LIMIT 5;
            """
            rows_i = db.execute_query(sql_interacciones, (id_empresa,), fetchall=True) or []
            ultimas_interacciones = []
            for r in rows_i:
                ultimas_interacciones.append({
                    "cliente": r[0],
                    "tipo": r[1],
                    "asunto": r[2],
                    "detalle": r[3],
                    "fecha": r[4].strftime("%Y-%m-%d %H:%M") if r[4] else None,
                    "proximo_seguimiento": r[5].strftime("%Y-%m-%d") if r[5] else None,
                    "registrado_por": r[6]
                })

            # 5. Resumen de unidades asociadas activas
            sql_unidades = f"""
                SELECT p.nombre_completo AS cliente, u.codigo AS codigo_unidad,
                       o.nombre AS proyecto, cu.estado_asociacion, cu.monto_pactado
                FROM {Config.SCHEMA}.t_crm_cliente_unidad cu
                INNER JOIN {Config.SCHEMA}.t_crm_cliente c ON c.id_cliente = cu.id_cliente
                INNER JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = c.id_persona
                INNER JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = cu.id_unidad
                INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
                INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
                WHERE c.id_empresa = %s AND cu.estado_asociacion IN ('INTERESADO', 'RESERVADO', 'VENDIDO')
                ORDER BY cu.fecha_asociacion DESC
                LIMIT 10;
            """
            rows_u = db.execute_query(sql_unidades, (id_empresa,), fetchall=True) or []
            unidades_activas = []
            for r in rows_u:
                unidades_activas.append({
                    "cliente": r[0],
                    "unidad": r[1],
                    "proyecto": r[2],
                    "estado": r[3],
                    "monto_pactado": float(r[4]) if r[4] is not None else None
                })

            return {
                "empresa_autorizada": nombre_empresa,
                "metricas_crm": metricas,
                "prospectos_en_seguimiento": prospectos_destacados,
                "ultimas_interacciones": ultimas_interacciones,
                "unidades_asociadas_recientes": unidades_activas
            }
        finally:
            db.close_connection()
