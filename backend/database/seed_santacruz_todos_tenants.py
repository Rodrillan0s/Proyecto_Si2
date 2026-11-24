"""
Sembrado transaccional e idempotente de datos empresariales reales basados en
Santa Cruz de la Sierra (Bolivia) para TODOS los tenants de obras.t_empresa.

Cubre:
- Obras y detalles georreferenciados en zonas reales de Santa Cruz (UV/Manzana, GPS)
- Unidades inmobiliarias (VIVIENDA, DEPARTAMENTO, OFICINA, LOCAL, LOTE) con precios
  publicados USD, amoblamiento verificable y ambientes/características reales
- Parámetros de estimación constructiva + mobiliario por m² por empresa
- Incidencias operativas y órdenes de trabajo realistas de obra cruceña
- Garantías y solicitudes posventa (CU42) para todos los tenants
- Notificaciones operativas para bandeja móvil push
"""
from datetime import date, timedelta
import psycopg2
from app.config import Config


SCZ_PROJECTS = [
    {
        'suffix': 'SCZ-URU',
        'nombre': 'Condominio Colinas del Urubó',
        'zona': 'Urubó',
        'distrito': 'Porongo / Urubó',
        'ubicacion': 'Av. Mario Foianini Km 4.5, Urubó, Santa Cruz de la Sierra',
        'uv': 'UV-URU1',
        'manzana': 'MZ-14',
        'lat': -17.7524,
        'lng': -63.2318,
        'presupuesto': 1850000.00,
        'desc': 'Condominio cerrado de viviendas unifamiliares de 1 y 2 plantas con áreas verdes, club house y seguridad 24/7.',
    },
    {
        'suffix': 'SCZ-EQP',
        'nombre': 'Torre Residencial Equipetrol Norte',
        'zona': 'Equipetrol',
        'distrito': 'Distrito 1',
        'ubicacion': 'Calle 8 Este entre Av. San Martín y Canal Isuto, Equipetrol, Santa Cruz de la Sierra',
        'uv': 'UV-059',
        'manzana': 'MZ-22',
        'lat': -17.7642,
        'lng': -63.1965,
        'presupuesto': 2400000.00,
        'desc': 'Edificio mixto de departamentos modernos, oficinas ejecutivas y locales comerciales con certificación energética.',
    },
    {
        'suffix': 'SCZ-REM',
        'nombre': 'Urbanización Remanso Norte',
        'zona': 'Zona Norte',
        'distrito': 'Distrito 5',
        'ubicacion': 'Av. Banzer 7mo Anillo, Urb. El Remanso, Santa Cruz de la Sierra',
        'uv': 'UV-112',
        'manzana': 'MZ-08',
        'lat': -17.7168,
        'lng': -63.1642,
        'presupuesto': 1320000.00,
        'desc': 'Proyecto habitacional de casas familiares funcionales y lotes urbanizados con servicios básicos SAGUAPAC y CRE.',
    },
]

SCZ_UNITS_TEMPLATE = [
    # (code_suffix, nombre, tipo, sup, plantas, estado_const, acabado, precio_usd, estado_com, amoblamiento, costo_mob_usd, dorms, banos, project_idx)
    ('CASA-AMOB-78', 'Casa Jardín Urubó A-01', 'VIVIENDA', 118.0, 1, 'FINALIZADO', 'NORMAL', 78500.00, 'DISPONIBLE', 'AMOBLADA', None, 3, 2, 0),
    ('CASA-PARC-74', 'Casa Familiar Remanso B-02', 'VIVIENDA', 112.0, 1, 'FINALIZADO', 'NORMAL', 74000.00, 'DISPONIBLE', 'PARCIALMENTE_AMOBLADA', 4200.00, 3, 2, 2),
    ('CASA-SINM-69', 'Casa Funcional Norte B-03', 'VIVIENDA', 105.0, 1, 'FINALIZADO', 'NORMAL', 69500.00, 'DISPONIBLE', 'SIN_AMOBLAR', 6500.00, 3, 2, 2),
    ('CASA-DESC-76', 'Casa Moderna Remanso B-04', 'VIVIENDA', 115.0, 1, 'EN_CONSTRUCCION', 'NORMAL', 76000.00, 'DISPONIBLE', 'DESCONOCIDO', 6800.00, 3, 2, 2),
    ('CASA-LUJO-158', 'Residencia Premium Urubó A-05', 'VIVIENDA', 225.0, 2, 'FINALIZADO', 'LUJO', 158000.00, 'DISPONIBLE', 'AMOBLADA', None, 4, 4, 0),
    ('CASA-RES-72', 'Casa Esquina Remanso B-06', 'VIVIENDA', 110.0, 1, 'FINALIZADO', 'NORMAL', 72000.00, 'RESERVADA', 'AMOBLADA', None, 3, 2, 2),
    ('DPTO-EQP-84', 'Departamento Sky Equipetrol 4B', 'DEPARTAMENTO', 92.0, 1, 'FINALIZADO', 'LUJO', 84500.00, 'DISPONIBLE', 'AMOBLADA', None, 2, 2, 1),
    ('DPTO-EQP-68', 'Departamento Ejecutivo 2A', 'DEPARTAMENTO', 74.0, 1, 'EN_CONSTRUCCION', 'NORMAL', 68000.00, 'DISPONIBLE', 'SIN_AMOBLAR', 4800.00, 2, 2, 1),
    ('OFI-EQP-62', 'Oficina Corporativa Equipetrol 1C', 'OFICINA', 64.0, 1, 'FINALIZADO', 'NORMAL', 62000.00, 'DISPONIBLE', 'SIN_AMOBLAR', None, 0, 1, 1),
    ('LOTE-URU-42', 'Lote Urbanizado Colinas L-12', 'LOTE', 300.0, 1, 'FINALIZADO', 'NORMAL', 42000.00, 'DISPONIBLE', 'SIN_AMOBLAR', None, 0, 0, 0),
]

SCZ_PARAMS = [
    ('COSTO_M2_TIPO', 'VIVIENDA', 'Costo m² Vivienda Santa Cruz', 2850.00),
    ('COSTO_M2_TIPO', 'EDIFICIO', 'Costo m² Edificio Santa Cruz', 3550.00),
    ('COSTO_M2_TIPO', 'COMERCIAL', 'Costo m² Comercial Santa Cruz', 3200.00),
    ('COSTO_M2_TIPO', 'INDUSTRIAL', 'Costo m² Industrial Santa Cruz', 2450.00),
    ('FACTOR_ESTILO', 'ESTANDAR', 'Factor Estilo Estándar', 1.0000),
    ('FACTOR_ESTILO', 'INDUSTRIAL', 'Factor Estilo Industrial', 1.1000),
    ('FACTOR_ESTILO', 'MINIMALISTA', 'Factor Estilo Minimalista', 1.1500),
    ('FACTOR_ESTILO', 'CONTEMPORANEO', 'Factor Estilo Contemporáneo', 1.1800),
    ('FACTOR_ESTILO', 'LUJO', 'Factor Estilo Lujo', 1.3500),
    ('COSTO_MOBILIARIO_M2', 'ESTANDAR', 'Referencia Mobiliario por m² Santa Cruz', 420.00),
]


def run_seed():
    conn = psycopg2.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id_tipo_obra FROM obras.t_tipo_obra ORDER BY id_tipo_obra LIMIT 1")
            row_tipo = cur.fetchone()
            id_tipo_obra = row_tipo[0] if row_tipo else None

            cur.execute("SELECT id_empresa, nombre_empresa FROM obras.t_empresa ORDER BY id_empresa")
            empresas = cur.fetchall()
            hoy = date.today()

            for id_emp, nombre_emp in empresas:
                print(f"\n=== Poblando tenant {id_emp}: {nombre_emp} ===")

                # Usuario responsable del tenant (para incidencias, posventa, notificaciones)
                cur.execute(
                    "SELECT id_usuario FROM obras.t_usuario WHERE id_empresa = %s ORDER BY id_usuario LIMIT 3",
                    (id_emp,),
                )
                usr_rows = [r[0] for r in cur.fetchall()]
                if not usr_rows:
                    cur.execute("SELECT id_usuario FROM obras.t_usuario ORDER BY id_usuario LIMIT 1")
                    usr_rows = [cur.fetchone()[0]]
                usr_main = usr_rows[0]

                # 1. Parámetros de estimación por empresa
                for cat, clave, nom_p, val_p in SCZ_PARAMS:
                    cur.execute(
                        """
                        SELECT id_parametro FROM obras.t_parametro_estimacion
                        WHERE id_empresa = %s AND categoria = %s AND codigo_clave = %s
                        """,
                        (id_emp, cat, clave),
                    )
                    if not cur.fetchone():
                        cur.execute(
                            """
                            INSERT INTO obras.t_parametro_estimacion
                                (id_empresa, categoria, codigo_clave, nombre, valor_numerico, descripcion, activo)
                            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                            """,
                            (id_emp, cat, clave, nom_p, val_p, 'Parámetro calibrado para mercado de Santa Cruz de la Sierra.'),
                        )

                # 2. Enriquecer detalles de obras existentes sin ubicación de Santa Cruz
                cur.execute(
                    """
                    UPDATE obras.t_detalle_obra d
                    SET ubicacion = COALESCE(NULLIF(TRIM(d.ubicacion), ''), 'Av. Beni 3er Anillo Interno, Santa Cruz de la Sierra'),
                        zona = COALESCE(NULLIF(TRIM(d.zona), ''), 'Equipetrol / Norte'),
                        distrito = COALESCE(NULLIF(TRIM(d.distrito), ''), 'Distrito 1'),
                        latitud = COALESCE(d.latitud, -17.7685),
                        longitud = COALESCE(d.longitud, -63.1812)
                    FROM obras.t_obra o
                    WHERE d.id_obra = o.id_obra AND o.id_empresa = %s
                    """,
                    (id_emp,),
                )

                # 3. Crear/asegurar 3 proyectos emblemáticos de Santa Cruz por tenant
                obras_scz_ids = []
                for idx_p, proj in enumerate(SCZ_PROJECTS):
                    cod_obra = f"{proj['suffix']}-E{id_emp}"
                    cur.execute(
                        "SELECT id_obra FROM obras.t_obra WHERE id_empresa = %s AND codigo = %s",
                        (id_emp, cod_obra),
                    )
                    r_obra = cur.fetchone()
                    if r_obra:
                        id_obra = r_obra[0]
                    else:
                        cur.execute(
                            """
                            INSERT INTO obras.t_obra
                                (id_tipo_obra, estado_obra, fecha_inicio, fecha_fin, id_empresa, codigo,
                                 nombre, moneda, descripcion, presupuesto_objetivo, estado_estimacion)
                            VALUES (%s, 'EN_EJECUCION', %s, %s, %s, %s, %s, 'USD', %s, %s, 'APROBADA')
                            RETURNING id_obra
                            """,
                            (
                                id_tipo_obra,
                                hoy - timedelta(days=180 - idx_p * 30),
                                hoy + timedelta(days=240 + idx_p * 45),
                                id_emp,
                                cod_obra,
                                f"{proj['nombre']} ({nombre_emp.split()[-1]})",
                                proj['desc'],
                                proj['presupuesto'],
                            ),
                        )
                        id_obra = cur.fetchone()[0]
                        cur.execute(
                            """
                            INSERT INTO obras.t_detalle_obra
                                (id_obra, ubicacion, latitud, longitud, zona, distrito, uv, manzana, observacion)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                id_obra, proj['ubicacion'], proj['lat'], proj['lng'],
                                proj['zona'], proj['distrito'], proj['uv'], proj['manzana'],
                                'Proyecto verificado en Santa Cruz de la Sierra.',
                            ),
                        )
                    obras_scz_ids.append(id_obra)

                # 4. Actualizar unidades existentes que no tenían precio_venta
                cur.execute(
                    """
                    UPDATE obras.t_unidad_construccion u
                    SET precio_venta = COALESCE(u.precio_venta, GREATEST(58000, ROUND(COALESCE(u.superficie, 90) * 720, 2))),
                        moneda_comercial = COALESCE(NULLIF(TRIM(u.moneda_comercial), ''), 'USD'),
                        publicado_comercial = TRUE,
                        estado_comercial = COALESCE(NULLIF(TRIM(u.estado_comercial), ''), 'DISPONIBLE')
                    FROM obras.t_estructura_obra e
                    JOIN obras.t_obra o ON o.id_obra = e.id_obra
                    WHERE u.id_estructura = e.id_estructura AND o.id_empresa = %s
                    """,
                    (id_emp,),
                )

                # 5. Insertar portafolio completo de unidades en Santa Cruz para el tenant
                unidades_creadas_ids = []
                for idx_u, tpl in enumerate(SCZ_UNITS_TEMPLATE, start=1):
                    (
                        u_suf, u_nom, u_tipo, u_sup, u_plantas, u_est_const, u_acab,
                        u_precio_usd, u_est_com, u_amob, u_costo_mob, u_dorms, u_banos, p_idx
                    ) = tpl
                    id_obra_u = obras_scz_ids[p_idx]
                    u_codigo = f"E{id_emp}-{u_suf}"

                    cur.execute(
                        """
                        SELECT u.id_unidad
                        FROM obras.t_unidad_construccion u
                        JOIN obras.t_estructura_obra e ON e.id_estructura = u.id_estructura
                        JOIN obras.t_obra o ON o.id_obra = e.id_obra
                        WHERE o.id_empresa = %s AND u.codigo = %s
                        """,
                        (id_emp, u_codigo),
                    )
                    r_u = cur.fetchone()
                    if r_u:
                        id_unidad = r_u[0]
                    else:
                        cur.execute(
                            """
                            INSERT INTO obras.t_estructura_obra (id_obra, nombre, tipo, descripcion, orden)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING id_estructura
                            """,
                            (id_obra_u, u_nom, u_tipo, f"{u_nom} — Santa Cruz de la Sierra", idx_u),
                        )
                        id_est = cur.fetchone()[0]
                        cur.execute(
                            """
                            INSERT INTO obras.t_unidad_construccion
                                (id_estructura, codigo, tipo_unidad, superficie, cantidad_plantas, estado,
                                 especificacion_acabado, publicado_comercial, precio_venta, moneda_comercial,
                                 descripcion_comercial, estado_comercial, estado_amoblamiento, costo_mobiliario_estimado)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, %s, 'USD', %s, %s, %s, %s)
                            RETURNING id_unidad
                            """,
                            (
                                id_est, u_codigo, u_tipo, u_sup, u_plantas, u_est_const, u_acab,
                                u_precio_usd,
                                f"{u_nom} ubicada en {SCZ_PROJECTS[p_idx]['zona']}, Santa Cruz de la Sierra.",
                                u_est_com, u_amob, u_costo_mob,
                            ),
                        )
                        id_unidad = cur.fetchone()[0]

                        # Ambientes
                        if u_dorms > 0:
                            cur.execute(
                                "INSERT INTO obras.t_unidad_ambiente (id_unidad, nombre, cantidad) VALUES (%s, 'Dormitorio', %s)",
                                (id_unidad, u_dorms),
                            )
                        if u_banos > 0:
                            cur.execute(
                                "INSERT INTO obras.t_unidad_ambiente (id_unidad, nombre, cantidad) VALUES (%s, 'Baño', %s)",
                                (id_unidad, u_banos),
                            )
                        if u_tipo in ('VIVIENDA', 'DEPARTAMENTO'):
                            cur.execute(
                                "INSERT INTO obras.t_unidad_ambiente (id_unidad, nombre, cantidad) VALUES (%s, 'Sala - Comedor', 1), (%s, 'Cocina', 1)",
                                (id_unidad, id_unidad),
                            )
                        # Características reales
                        cur.execute(
                            """
                            INSERT INTO obras.t_unidad_caracteristica (id_unidad, nombre, valor)
                            VALUES (%s, 'Parqueo', 'Cubierto'), (%s, 'Servicios', 'CRE + SAGUAPAC + Fibra Óptica')
                            """,
                            (id_unidad, id_unidad),
                        )
                    unidades_creadas_ids.append(id_unidad)

                # 6. Incidencias y Órdenes de trabajo realistas de Santa Cruz
                incidencias_scz = [
                    ('Drenaje pluvial en acceso principal', 'Acumulación de agua tras lluvia intensa; requiere nivelación de cuneta y rejilla.', 'ALTA', 'ABIERTA'),
                    ('Curado de losa por alta temperatura', 'Reforzar curado húmedo en losa nivel 2 por temperatura de 36°C en Santa Cruz.', 'MEDIA', 'EN_PROCESO'),
                    ('Acometida trifásica CRE pendiente de inspección', 'Coordinar inspección de medidor definitivo con CRE en bloque norte.', 'CRITICA', 'ASIGNADA'),
                ]
                for i_idx, (tit, desc_i, prio, est_i) in enumerate(incidencias_scz):
                    obra_target = obras_scz_ids[i_idx % len(obras_scz_ids)]
                    cur.execute(
                        "SELECT id_incidencia FROM obras.t_incidencia WHERE id_obra = %s AND titulo = %s",
                        (obra_target, tit),
                    )
                    if not cur.fetchone():
                        cur.execute(
                            """
                            INSERT INTO obras.t_incidencia
                                (id_obra, id_unidad, id_usuario_registro, id_responsable, titulo, descripcion,
                                 prioridad, estado, ubicacion, fecha_inicio_atencion)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CASE WHEN %s = 'EN_PROCESO' THEN NOW() ELSE NULL END)
                            """,
                            (
                                obra_target, unidades_creadas_ids[i_idx], usr_main, usr_main,
                                tit, desc_i, prio, est_i, SCZ_PROJECTS[i_idx % len(SCZ_PROJECTS)]['zona'], est_i,
                            ),
                        )

                ots_scz = [
                    ('Impermeabilización de losa y terrazas', 6, 'EN_PROGRESO', 5),
                    ('Instalación red hidrosanitaria SAGUAPAC', 5, 'PENDIENTE', 10),
                    ('Colocación de porcelanato rectificado 60x120', 4, 'EN_PROGRESO', 7),
                ]
                for o_idx, (tipo_t, cuad, est_ot, dias_fin) in enumerate(ots_scz):
                    obra_target = obras_scz_ids[o_idx % len(obras_scz_ids)]
                    cur.execute(
                        "SELECT orden_nro FROM obras.t_orden_trabajo WHERE id_obra = %s AND tipo_trab = %s",
                        (obra_target, tipo_t),
                    )
                    if not cur.fetchone():
                        cur.execute(
                            """
                            INSERT INTO obras.t_orden_trabajo
                                (id_obra, tipo_trab, cuadrilla, estado, fecha_inicio, fecha_fin, observacion)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                obra_target, tipo_t, cuad, est_ot,
                                hoy - timedelta(days=3), hoy + timedelta(days=dias_fin),
                                'Orden programada para ejecución en Santa Cruz de la Sierra.',
                            ),
                        )

                # 7. Garantías y Posventa (CU42) para el tenant
                cur.execute(
                    "SELECT id_cliente FROM obras.t_crm_cliente WHERE id_empresa = %s ORDER BY id_cliente LIMIT 3",
                    (id_emp,),
                )
                clientes_emp = [r[0] for r in cur.fetchall()]
                if clientes_emp and unidades_creadas_ids:
                    garantias_tpl = [
                        ('ESTRUCTURAL', 'Cobertura estructural de cimientos, columnas y losas según normativa NB 1225001.', 1825, 'VIGENTE'),
                        ('INSTALACIONES', 'Cobertura de instalaciones eléctricas (CRE) e hidrosanitarias (SAGUAPAC).', 730, 'VIGENTE'),
                        ('ACABADOS', 'Cobertura de carpintería de aluminio, revestimientos cerámicos y pintura.', 365, 'VIGENTE'),
                    ]
                    posventa_tpl = [
                        ('Ajuste de burlete en ventanal de terraza', 'Ingreso leve de viento durante surazo en dormitorio principal.', 'CARPINTERIA', 'REGISTRADA'),
                        ('Revisión de presión en ducha baño visitas', 'Se solicita calibración de válvula mezcladora en segundo baño.', 'PLOMERIA', 'ASIGNADA'),
                        ('Sellado perimetral en galería posterior', 'Preventivo de humedad tras lluvias estacionales de Santa Cruz.', 'IMPERMEABILIZACION', 'EN_ATENCION'),
                    ]
                    for g_idx, (gtipo, gdesc, gdias, _gest) in enumerate(garantias_tpl):
                        id_u_g = unidades_creadas_ids[g_idx % len(unidades_creadas_ids)]
                        id_c_g = clientes_emp[g_idx % len(clientes_emp)]
                        g_cod = f"GAR-E{id_emp}-{g_idx + 1:03d}"
                        cur.execute(
                            "SELECT id_garantia FROM obras.t_garantia_inmobiliaria WHERE id_empresa = %s AND id_unidad = %s AND tipo_garantia = %s",
                            (id_emp, id_u_g, gtipo),
                        )
                        r_g = cur.fetchone()
                        if r_g:
                            id_gar = r_g[0]
                        else:
                            cur.execute(
                                """
                                INSERT INTO obras.t_garantia_inmobiliaria
                                    (id_empresa, id_unidad, codigo, tipo_garantia, descripcion,
                                     fecha_inicio, fecha_fin, observaciones, id_usuario_registro)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                RETURNING id_garantia
                                """,
                                (
                                    id_emp, id_u_g, g_cod, gtipo, gdesc,
                                    hoy - timedelta(days=45), hoy + timedelta(days=gdias),
                                    'Sujeto a uso residencial normal y mantenimiento preventivo en Santa Cruz.',
                                    usr_main,
                                ),
                            )
                            id_gar = cur.fetchone()[0]

                        ptit, pdesc, pcat, pest = posventa_tpl[g_idx]
                        cur.execute(
                            "SELECT id_solicitud_posventa FROM obras.t_solicitud_posventa WHERE id_empresa = %s AND titulo = %s",
                            (id_emp, ptit),
                        )
                        if not cur.fetchone():
                            cur.execute(
                                """
                                INSERT INTO obras.t_solicitud_posventa
                                    (id_empresa, id_unidad, id_cliente, id_garantia, titulo, descripcion,
                                     categoria, estado, id_responsable, id_usuario_creacion)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                                (id_emp, id_u_g, id_c_g, id_gar, ptit, pdesc, pcat, pest, usr_main, usr_main),
                            )

                # 8. Notificaciones push realistas para los usuarios del tenant
                for u_not in usr_rows[:2]:
                    clave_ev = f"SCZ-RESUMEN-E{id_emp}-U{u_not}"
                    cur.execute(
                        "SELECT id_notificacion FROM obras.notificacion WHERE clave_evento = %s",
                        (clave_ev,),
                    )
                    if not cur.fetchone():
                        cur.execute(
                            """
                            INSERT INTO obras.notificacion
                                (titulo, cuerpo, tipo_referencia, nro_usuario, leido, id_empresa, id_obra, clave_evento)
                            VALUES (%s, %s, 'OBRA', %s, FALSE, %s, %s, %s)
                            """,
                            (
                                f"Actualización operativa · {SCZ_PROJECTS[0]['nombre']}",
                                "Portafolio comercial, incidencias, garantías y órdenes de trabajo de Santa Cruz actualizados.",
                                u_not, id_emp, obras_scz_ids[0], clave_ev,
                            ),
                        )

            conn.commit()
            print("\n✅ Sembrado completo de Santa Cruz de la Sierra confirmado para TODOS los tenants.")

            # Resumen final verificado
            cur.execute("""
                SELECT e.id_empresa, e.nombre_empresa,
                       (SELECT COUNT(*) FROM obras.t_obra o WHERE o.id_empresa = e.id_empresa) AS obras,
                       (SELECT COUNT(*) FROM obras.t_unidad_construccion u
                        JOIN obras.t_estructura_obra s ON s.id_estructura = u.id_estructura
                        JOIN obras.t_obra o ON o.id_obra = s.id_obra
                        WHERE o.id_empresa = e.id_empresa) AS unidades,
                       (SELECT COUNT(*) FROM obras.t_incidencia i
                        JOIN obras.t_obra o ON o.id_obra = i.id_obra
                        WHERE o.id_empresa = e.id_empresa) AS incidencias,
                       (SELECT COUNT(*) FROM obras.t_orden_trabajo ot
                        JOIN obras.t_obra o ON o.id_obra = ot.id_obra
                        WHERE o.id_empresa = e.id_empresa) AS ots,
                       (SELECT COUNT(*) FROM obras.t_garantia_inmobiliaria g WHERE g.id_empresa = e.id_empresa) AS garantias,
                       (SELECT COUNT(*) FROM obras.t_solicitud_posventa p WHERE p.id_empresa = e.id_empresa) AS posventa
                FROM obras.t_empresa e
                ORDER BY e.id_empresa
            """)
            print("\nRESUMEN FINAL POR TENANT (id, nombre, obras, unidades, incidencias, ots, garantias, posventa):")
            for r in cur.fetchall():
                print(" ", r)
    finally:
        conn.close()


if __name__ == '__main__':
    run_seed()
