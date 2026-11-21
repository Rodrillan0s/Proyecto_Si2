"""Repositorio comercial multi-tenant para CU34 (HUs 147, 148, 149, 150)."""
import json
import re
import unicodedata
from decimal import Decimal
from app.classes.postgres import PostgreSQL
from app.config import Config


def _slugify(value: str) -> str:
    text = unicodedata.normalize('NFKD', str(value or '')).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def _to_decimal(val, default: str = '0.00') -> Decimal:
    if val is None or val == '':
        return Decimal(default)
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal(default)


def listar_empresas_comerciales() -> list[dict]:
    """Lista las empresas constructoras registradas junto con su conteo de proyectos y unidades."""
    sql = f"""
        SELECT e.id_empresa,
               COALESCE(NULLIF(TRIM(e.nombre_empresa), ''), 'Constructora ' || e.id_empresa) AS nombre_empresa,
               e.nit,
               e.descripcion,
               (SELECT COUNT(*) FROM {Config.SCHEMA}.t_obra o WHERE o.id_empresa = e.id_empresa) AS total_obras,
               (SELECT COUNT(*)
                FROM {Config.SCHEMA}.t_unidad_construccion u
                JOIN {Config.SCHEMA}.t_estructura_obra s ON s.id_estructura = u.id_estructura
                JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = s.id_obra
                WHERE o.id_empresa = e.id_empresa) AS total_unidades
        FROM {Config.SCHEMA}.t_empresa e
        ORDER BY e.id_empresa ASC;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(sql, fetchall=True) or []
        result = []
        for r in rows:
            nombre = r[1]
            result.append({
                'id_empresa': int(r[0]),
                'slug': _slugify(nombre) or str(r[0]),
                'nombre_empresa': nombre,
                'nit': r[2],
                'descripcion': r[3],
                'total_obras': int(r[4] or 0),
                'total_unidades': int(r[5] or 0),
            })
        return result
    finally:
        db.close_connection()


def resolver_empresa_comercial(empresa_ref) -> dict | None:
    """
    Resuelve de forma estricta la empresa por ID numérico o por slug/nombre.
    Jamás aplica fallback implícito a otra empresa si no existe coincidencia exacta.
    """
    if empresa_ref is None or str(empresa_ref).strip() == '':
        return None
    raw = str(empresa_ref).strip()
    db = PostgreSQL()
    db.create_connection()
    try:
        if raw.isdigit():
            row = db.execute_query(
                f"""
                SELECT id_empresa,
                       COALESCE(NULLIF(TRIM(nombre_empresa), ''), 'Constructora ' || id_empresa),
                       nit,
                       descripcion
                FROM {Config.SCHEMA}.t_empresa
                WHERE id_empresa = %s;
                """,
                (int(raw),),
                fetchone=True,
            )
            if row:
                return {
                    'id_empresa': int(row[0]),
                    'slug': _slugify(row[1]) or str(row[0]),
                    'nombre_empresa': row[1],
                    'nit': row[2],
                    'descripcion': row[3],
                }
            return None

        target_slug = _slugify(raw)
        if not target_slug:
            return None
        rows = db.execute_query(
            f"""
            SELECT id_empresa,
                   COALESCE(NULLIF(TRIM(nombre_empresa), ''), 'Constructora ' || id_empresa),
                   nit,
                   descripcion
            FROM {Config.SCHEMA}.t_empresa
            ORDER BY id_empresa ASC;
            """,
            fetchall=True,
        ) or []
        for r in rows:
            if _slugify(r[1]) == target_slug or r[1].strip().lower() == raw.lower():
                return {
                    'id_empresa': int(r[0]),
                    'slug': _slugify(r[1]) or str(r[0]),
                    'nombre_empresa': r[1],
                    'nit': r[2],
                    'descripcion': r[3],
                }
        return None
    finally:
        db.close_connection()


def obtener_parametros_estimacion_empresa(id_empresa: int) -> dict:
    """
    Obtiene los parámetros de estimación (t_parametro_estimacion), APUs de acabado
    y materiales con precio para la empresa autorizada (con prioridad de tenant sobre global).
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(
            f"""
            SELECT id_parametro, id_empresa, categoria, codigo_clave, nombre,
                   valor_numerico, descripcion
            FROM {Config.SCHEMA}.t_parametro_estimacion
            WHERE (id_empresa = %s OR id_empresa IS NULL)
              AND activo = TRUE
            ORDER BY CASE WHEN id_empresa = %s THEN 0 ELSE 1 END, categoria, codigo_clave;
            """,
            (id_empresa, id_empresa),
            fetchall=True,
        ) or []
        parametros = {}
        for r in rows:
            cat = str(r[2] or '').upper()
            clave = str(r[3] or '').upper()
            parametros.setdefault(cat, {})
            if clave not in parametros[cat]:
                parametros[cat][clave] = {
                    'id_parametro': int(r[0]),
                    'id_empresa': r[1],
                    'categoria': cat,
                    'codigo_clave': clave,
                    'nombre': r[4],
                    'valor_numerico': _to_decimal(r[5], '1.0000'),
                    'descripcion': r[6],
                }

        apus_rows = db.execute_query(
            f"""
            SELECT a.id_analisis_precio_unitario, a.codigo, a.nombre,
                   COALESCE(um.abreviatura, um.nombre, 'u') AS unidad_medida,
                   a.precio_unitario_final, a.tipo_analisis_precio_unitario
            FROM {Config.SCHEMA}.t_analisis_precio_unitario a
            LEFT JOIN {Config.SCHEMA}.t_unidad_medida um ON um.id_unidad_medida = a.id_unidad_medida
            WHERE a.id_empresa = %s AND a.activo = TRUE
            ORDER BY CASE WHEN a.tipo_analisis_precio_unitario = 'ACABADO' THEN 0 ELSE 1 END,
                     a.id_analisis_precio_unitario ASC
            LIMIT 25;
            """,
            (id_empresa,),
            fetchall=True,
        ) or []
        apus = [
            {
                'id_apu': int(a[0]),
                'codigo': a[1],
                'nombre': a[2],
                'unidad_medida': a[3],
                'precio_unitario_final': _to_decimal(a[4], '0.00'),
                'tipo': a[5],
            }
            for a in apus_rows
        ]

        mat_rows = db.execute_query(
            f"""
            SELECT m.id_material, m.nombre_material,
                   COALESCE(m.precio, mb.precio_referencial, 0) AS precio_ref,
                   COALESCE(um.abreviatura, um.nombre, 'u') AS unidad
            FROM {Config.SCHEMA}.t_material m
            LEFT JOIN {Config.SCHEMA}.t_material_base mb ON mb.id_material_base = m.id_material_base
            LEFT JOIN {Config.SCHEMA}.t_unidad_medida um ON um.id_unidad_medida = m.id_unidad_medida
            WHERE m.id_empresa = %s AND m.estado = 'ACTIVO'
            ORDER BY m.nombre_material ASC
            LIMIT 30;
            """,
            (id_empresa,),
            fetchall=True,
        ) or []
        materiales = [
            {
                'id_material': int(m[0]),
                'nombre_material': m[1],
                'precio_referencial': _to_decimal(m[2], '0.00'),
                'unidad_medida': m[3],
            }
            for m in mat_rows
        ]

        return {
            'parametros': parametros,
            'apus': apus,
            'materiales': materiales,
        }
    finally:
        db.close_connection()


def listar_unidades_comerciales(id_empresa: int) -> list[dict]:
    """
    Recupera todas las unidades inmobiliarias de la empresa con su estructura,
    obra, ubicación, modelo, ambientes, características, acabados y estado comercial CRM.
    """
    sql = f"""
        SELECT u.id_unidad,
               u.codigo AS codigo_unidad,
               e.nombre AS nombre_unidad,
               e.descripcion AS descripcion_unidad,
               e.tipo AS tipo_estructura,
               u.tipo_unidad,
               u.superficie,
               u.cantidad_plantas,
               u.estado AS estado_construccion,
               COALESCE(u.especificacion_acabado, 'NORMAL') AS especificacion_acabado,
               u.id_modelo,
               m.nombre AS modelo_nombre,
               m.descripcion AS modelo_descripcion,
               o.id_obra,
               o.nombre AS nombre_obra,
               o.codigo AS codigo_obra,
               o.estado_obra AS estado_obra,
               d.ubicacion,
               d.zona,
               d.distrito,
               COALESCE(
                   (SELECT json_agg(json_build_object('nombre', ua.nombre, 'cantidad', ua.cantidad) ORDER BY ua.nombre)
                    FROM {Config.SCHEMA}.t_unidad_ambiente ua
                    WHERE ua.id_unidad = u.id_unidad),
                   '[]'::json
               ) AS ambientes_json,
               COALESCE(
                   (SELECT json_agg(json_build_object('nombre', uc.nombre, 'valor', uc.valor) ORDER BY uc.nombre)
                    FROM {Config.SCHEMA}.t_unidad_caracteristica uc
                    WHERE uc.id_unidad = u.id_unidad),
                   '[]'::json
               ) AS caracteristicas_unidad_json,
               COALESCE(
                   (SELECT json_agg(json_build_object('nombre', mc.nombre, 'valor', mc.valor) ORDER BY mc.nombre)
                    FROM {Config.SCHEMA}.t_modelo_caracteristica mc
                    WHERE mc.id_modelo = u.id_modelo),
                   '[]'::json
               ) AS caracteristicas_modelo_json,
               COALESCE(
                   (SELECT json_agg(json_build_object('tipo', up.tipo, 'descripcion', up.descripcion) ORDER BY up.id_personalizacion DESC)
                    FROM {Config.SCHEMA}.t_unidad_personalizacion up
                    WHERE up.id_unidad = u.id_unidad),
                   '[]'::json
               ) AS personalizaciones_json,
               (SELECT cu.estado_asociacion
                FROM {Config.SCHEMA}.t_crm_cliente_unidad cu
                WHERE cu.id_unidad = u.id_unidad
                  AND cu.estado_asociacion IN ('VENDIDO', 'ENTREGADO', 'RESERVADO')
                ORDER BY CASE cu.estado_asociacion
                    WHEN 'ENTREGADO' THEN 1
                    WHEN 'VENDIDO' THEN 2
                    WHEN 'RESERVADO' THEN 3
                    ELSE 4
                END
                LIMIT 1) AS estado_crm_ocupacion,
               (SELECT cu.monto_pactado
                FROM {Config.SCHEMA}.t_crm_cliente_unidad cu
                WHERE cu.id_unidad = u.id_unidad
                  AND cu.monto_pactado IS NOT NULL
                  AND cu.monto_pactado > 0
                ORDER BY cu.updated_at DESC NULLS LAST, cu.id_cliente_unidad DESC
                LIMIT 1) AS ultimo_monto_pactado
        FROM {Config.SCHEMA}.t_unidad_construccion u
        INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
        INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
        LEFT JOIN {Config.SCHEMA}.t_detalle_obra d ON d.id_obra = o.id_obra
        LEFT JOIN {Config.SCHEMA}.t_modelo_unidad m ON m.id_modelo = u.id_modelo
        WHERE o.id_empresa = %s
        ORDER BY o.id_obra ASC, e.orden ASC NULLS LAST, u.id_unidad ASC;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(sql, (id_empresa,), fetchall=True) or []
        unidades = []
        for r in rows:
            ambientes = r[20] if isinstance(r[20], list) else json.loads(r[20] or '[]')
            car_unidad = r[21] if isinstance(r[21], list) else json.loads(r[21] or '[]')
            car_modelo = r[22] if isinstance(r[22], list) else json.loads(r[22] or '[]')
            personalizaciones = r[23] if isinstance(r[23], list) else json.loads(r[23] or '[]')

            merged_car = {}
            for item in car_modelo:
                if item and item.get('nombre'):
                    merged_car[str(item['nombre']).strip()] = str(item.get('valor') or '').strip()
            for item in car_unidad:
                if item and item.get('nombre'):
                    merged_car[str(item['nombre']).strip()] = str(item.get('valor') or '').strip()

            estado_construccion = str(r[8] or 'PLANIFICADO').upper()
            estado_crm = str(r[24] or '').upper() if r[24] else None
            if estado_crm in ('VENDIDO', 'ENTREGADO'):
                disponibilidad = 'VENDIDA'
            elif estado_crm == 'RESERVADO':
                disponibilidad = 'RESERVADA'
            elif estado_construccion == 'SUSPENDIDO':
                disponibilidad = 'NO_DISPONIBLE'
            else:
                disponibilidad = 'DISPONIBLE'

            unidades.append({
                'id_unidad': int(r[0]),
                'codigo_unidad': r[1],
                'nombre_unidad': r[2],
                'descripcion_unidad': r[3],
                'tipo_estructura': r[4],
                'tipo_unidad': str(r[5] or 'OTRO').upper(),
                'superficie_m2': _to_decimal(r[6], '0.00'),
                'cantidad_plantas': int(r[7] or 1),
                'estado_construccion': estado_construccion,
                'especificacion_acabado': str(r[9] or 'NORMAL').upper(),
                'id_modelo': int(r[10]) if r[10] is not None else None,
                'modelo_nombre': r[11],
                'modelo_descripcion': r[12],
                'id_obra': int(r[13]),
                'nombre_obra': r[14],
                'codigo_obra': r[15],
                'estado_obra': r[16],
                'ubicacion': r[17],
                'zona': r[18],
                'distrito': r[19],
                'ambientes': ambientes,
                'caracteristicas': [
                    {'nombre': k, 'valor': v} for k, v in merged_car.items()
                ],
                'caracteristicas_map': {k.lower(): v for k, v in merged_car.items()},
                'personalizaciones': personalizaciones,
                'disponibilidad_comercial': disponibilidad,
                'ultimo_monto_pactado': _to_decimal(r[25], '0.00') if r[25] is not None else None,
            })
        return unidades
    finally:
        db.close_connection()


def listar_modelos_comerciales(id_empresa: int) -> list[dict]:
    """Obtiene los modelos tipológicos activos de la empresa y sus características."""
    sql = f"""
        SELECT m.id_modelo,
               m.nombre,
               m.descripcion,
               m.tipo_unidad,
               m.superficie_base,
               m.cantidad_plantas_base,
               COALESCE(
                   (SELECT json_agg(json_build_object('nombre', mc.nombre, 'valor', mc.valor) ORDER BY mc.nombre)
                    FROM {Config.SCHEMA}.t_modelo_caracteristica mc
                    WHERE mc.id_modelo = m.id_modelo),
                   '[]'::json
               ) AS caracteristicas_json
        FROM {Config.SCHEMA}.t_modelo_unidad m
        WHERE m.id_empresa = %s AND m.activo = TRUE
        ORDER BY m.nombre ASC;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(sql, (id_empresa,), fetchall=True) or []
        modelos = []
        for r in rows:
            car = r[6] if isinstance(r[6], list) else json.loads(r[6] or '[]')
            modelos.append({
                'id_modelo': int(r[0]),
                'nombre': r[1],
                'descripcion': r[2],
                'tipo_unidad': str(r[3] or 'OTRO').upper(),
                'superficie_base': _to_decimal(r[4], '0.00') if r[4] is not None else Decimal('0.00'),
                'cantidad_plantas_base': int(r[5] or 1),
                'caracteristicas': car,
            })
        return modelos
    finally:
        db.close_connection()


def registrar_lead_comercial_transaccional(
    id_empresa: int,
    nombre_completo: str,
    telefono: str | None = None,
    email: str | None = None,
    ci: str | None = None,
    presupuesto_estimado: Decimal | None = None,
    notas: str | None = None,
    unidades_interes: list[int] | None = None,
    resumen_interaccion: str | None = None,
) -> dict:
    """
    Registra de forma atómica el interés comercial de un prospecto (HU150):
    1. Valida pertenencia de las unidades a id_empresa.
    2. Crea o actualiza t_persona.
    3. Crea o actualiza t_crm_cliente (tipo PROSPECTO, estado INTERESADO, origen WEB).
    4. Asocia las unidades solicitadas en t_crm_cliente_unidad (estado INTERESADO).
    5. Registra la interacción en t_crm_interaccion vinculada al asesor/responsable activo de la empresa.
    """
    unidades_ids = sorted({int(uid) for uid in (unidades_interes or []) if uid is not None and int(uid) > 0})
    db = PostgreSQL()
    db.create_connection()
    try:
        # 1. Verificar existencia de la empresa
        emp_row = db.execute_query(
            f"SELECT id_empresa, nombre_empresa FROM {Config.SCHEMA}.t_empresa WHERE id_empresa = %s;",
            (id_empresa,),
            fetchone=True,
        )
        if not emp_row:
            raise ValueError(f"La empresa ID {id_empresa} no existe.")

        # 2. Verificar pertenencia estricta de todas las unidades a id_empresa
        unidades_verificadas = []
        if unidades_ids:
            u_rows = db.execute_query(
                f"""
                SELECT u.id_unidad, u.codigo, e.nombre, o.nombre
                FROM {Config.SCHEMA}.t_unidad_construccion u
                INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
                INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
                WHERE u.id_unidad = ANY(%s) AND o.id_empresa = %s;
                """,
                (unidades_ids, id_empresa),
                fetchall=True,
            ) or []
            if len(u_rows) != len(unidades_ids):
                raise PermissionError(
                    "Una o más unidades seleccionadas no existen o no pertenecen a la empresa consultada."
                )
            unidades_verificadas = [
                {'id_unidad': int(ur[0]), 'codigo': ur[1], 'nombre': ur[2], 'obra': ur[3]}
                for ur in u_rows
            ]

        # 3. Resolver asesor / responsable activo de la empresa para asignación y registro de interacción
        asesor_row = db.execute_query(
            f"""
            SELECT u.id_usuario, COALESCE(NULLIF(TRIM(p.nombre_completo), ''), u.username)
            FROM {Config.SCHEMA}.t_usuario u
            JOIN {Config.SCHEMA}.t_rol r ON r.id_rol = u.id_rol
            LEFT JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = u.id_persona
            WHERE u.id_empresa = %s AND u.estado = 'ACTIVO'
            ORDER BY CASE
                WHEN r.nombre_rol = 'ADMINISTRADOR_EMPRESA' THEN 1
                WHEN r.nombre_rol = 'JEFE DE OBRA' THEN 2
                WHEN r.nombre_rol = 'ADMINISTRADOR' THEN 3
                ELSE 4
            END, u.id_usuario ASC
            LIMIT 1;
            """,
            (id_empresa,),
            fetchone=True,
        )
        id_asesor = int(asesor_row[0]) if asesor_row else None
        nombre_asesor = asesor_row[1] if asesor_row else 'Equipo Comercial'

        # 4. Localizar persona previa en el CRM de la empresa (por CI, email o teléfono) o crear nueva
        id_persona = None
        id_cliente_existente = None
        estado_actual = None

        if ci:
            p_row = db.execute_query(
                f"""
                SELECT p.id_persona, c.id_cliente, c.estado
                FROM {Config.SCHEMA}.t_persona p
                LEFT JOIN {Config.SCHEMA}.t_crm_cliente c
                       ON c.id_persona = p.id_persona AND c.id_empresa = %s
                WHERE LOWER(TRIM(p.ci)) = LOWER(TRIM(%s))
                ORDER BY c.id_cliente NULLS LAST, p.id_persona ASC
                LIMIT 1;
                """,
                (id_empresa, ci),
                fetchone=True,
            )
            if p_row:
                id_persona = int(p_row[0])
                id_cliente_existente = int(p_row[1]) if p_row[1] is not None else None
                estado_actual = p_row[2]

        if not id_persona and (email or telefono):
            c_row = db.execute_query(
                f"""
                SELECT c.id_persona, c.id_cliente, c.estado
                FROM {Config.SCHEMA}.t_crm_cliente c
                JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = c.id_persona
                WHERE c.id_empresa = %s
                  AND (
                      (%s IS NOT NULL AND LOWER(TRIM(c.email)) = LOWER(TRIM(%s)))
                      OR (%s IS NOT NULL AND TRIM(p.telefono) = TRIM(%s))
                  )
                ORDER BY c.id_cliente ASC
                LIMIT 1;
                """,
                (id_empresa, email, email, telefono, telefono),
                fetchone=True,
            )
            if c_row:
                id_persona = int(c_row[0])
                id_cliente_existente = int(c_row[1])
                estado_actual = c_row[2]

        if id_persona:
            db.execute_query(
                f"""
                UPDATE {Config.SCHEMA}.t_persona
                SET nombre_completo = COALESCE(NULLIF(%s, ''), nombre_completo),
                    telefono = COALESCE(NULLIF(%s, ''), telefono),
                    ci = COALESCE(NULLIF(%s, ''), ci)
                WHERE id_persona = %s;
                """,
                (nombre_completo, telefono, ci, id_persona),
            )
        else:
            new_p = db.execute_query(
                f"""
                INSERT INTO {Config.SCHEMA}.t_persona (nombre_completo, ci, telefono)
                VALUES (%s, %s, %s)
                RETURNING id_persona;
                """,
                (nombre_completo, ci, telefono),
                fetchone=True,
            )
            id_persona = int(new_p[0])

        # 5. Crear o actualizar registro en t_crm_cliente
        presupuesto_num = float(presupuesto_estimado) if presupuesto_estimado is not None else None
        if id_cliente_existente:
            nuevo_estado = estado_actual
            if estado_actual in ('NUEVO', 'CONTACTADO', 'PERDIDO'):
                nuevo_estado = 'INTERESADO'
            db.execute_query(
                f"""
                UPDATE {Config.SCHEMA}.t_crm_cliente
                SET email = COALESCE(NULLIF(%s, ''), email),
                    estado = %s,
                    presupuesto_estimado = COALESCE(%s, presupuesto_estimado),
                    notas = CASE
                        WHEN notas IS NULL OR TRIM(notas) = '' THEN %s
                        WHEN %s IS NULL OR TRIM(%s) = '' THEN notas
                        ELSE notas || E'\\n[Asistente IA Comercial]: ' || %s
                    END,
                    id_usuario_asignado = COALESCE(id_usuario_asignado, %s)
                WHERE id_cliente = %s AND id_empresa = %s;
                """,
                (
                    email,
                    nuevo_estado,
                    presupuesto_num,
                    notas,
                    notas,
                    notas,
                    notas,
                    id_asesor,
                    id_cliente_existente,
                    id_empresa,
                ),
            )
            id_cliente = id_cliente_existente
            es_nuevo = False
        else:
            cli_row = db.execute_query(
                f"""
                INSERT INTO {Config.SCHEMA}.t_crm_cliente (
                    id_empresa, id_persona, email, tipo_cliente, estado,
                    origen, presupuesto_estimado, notas, id_usuario_asignado
                )
                VALUES (%s, %s, %s, 'PROSPECTO', 'INTERESADO', 'WEB', %s, %s, %s)
                RETURNING id_cliente;
                """,
                (id_empresa, id_persona, email, presupuesto_num, notas, id_asesor),
                fetchone=True,
            )
            id_cliente = int(cli_row[0])
            es_nuevo = True

        # 6. Asociar unidades de interés en t_crm_cliente_unidad sin duplicar asociaciones activas
        asociaciones_creadas = []
        for u_info in unidades_verificadas:
            uid = u_info['id_unidad']
            ya_asociada = db.execute_query(
                f"""
                SELECT id_cliente_unidad
                FROM {Config.SCHEMA}.t_crm_cliente_unidad
                WHERE id_cliente = %s AND id_unidad = %s
                  AND estado_asociacion IN ('INTERESADO', 'RESERVADO', 'VENDIDO');
                """,
                (id_cliente, uid),
                fetchone=True,
            )
            if not ya_asociada:
                asoc_row = db.execute_query(
                    f"""
                    INSERT INTO {Config.SCHEMA}.t_crm_cliente_unidad (
                        id_cliente, id_unidad, estado_asociacion, observaciones
                    )
                    VALUES (%s, %s, 'INTERESADO', %s)
                    RETURNING id_cliente_unidad;
                    """,
                    (
                        id_cliente,
                        uid,
                        notas or 'Interés registrado desde el Asistente Comercial IA (CU34).',
                    ),
                    fetchone=True,
                )
                if asoc_row:
                    asociaciones_creadas.append(int(asoc_row[0]))

        # 7. Registrar interacción comercial en t_crm_interaccion si existe usuario asesor en la empresa
        id_interaccion = None
        if id_asesor:
            detalle_texto = (
                resumen_interaccion
                or notas
                or f"Solicitud de contacto comercial registrada para {nombre_completo}."
            )
            int_row = db.execute_query(
                f"""
                INSERT INTO {Config.SCHEMA}.t_crm_interaccion (
                    id_cliente, id_usuario, tipo, asunto, detalle
                )
                VALUES (%s, %s, 'CONSULTA', %s, %s)
                RETURNING id_interaccion;
                """,
                (
                    id_cliente,
                    id_asesor,
                    'Solicitud de contacto - Asistente Comercial IA (CU34)',
                    detalle_texto,
                ),
                fetchone=True,
            )
            if int_row:
                id_interaccion = int(int_row[0])

        db.conn.commit()
        return {
            'id_cliente': id_cliente,
            'id_persona': id_persona,
            'es_nuevo_prospecto': es_nuevo,
            'estado': 'INTERESADO',
            'origen': 'WEB',
            'asesor_asignado': nombre_asesor,
            'unidades_vinculadas': unidades_verificadas,
            'asociaciones_creadas': asociaciones_creadas,
            'id_interaccion': id_interaccion,
        }
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()

