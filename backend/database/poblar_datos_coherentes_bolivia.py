"""
Script de Poblado Coherente de Datos Multitenant para OBRATEC en Bolivia
Cubre todos los CUs (CU1 - CU39) con estadisticas reales de la construccion en Bolivia:
- Pocas obras con deficit (-9% a -15% por contingencias geotecnicas y alza de insumos importados)
- Resto de obras con margen de ganancia saludable (+15% a +25%)
- Stock de materiales con niveles normales, bajo stock y quiebre de stock para HU111
- Unidades de construccion, modelos, ambientes, caracteristicas, personalizaciones
- Control de costos, costos ejecutados, APUs, estimaciones
- CRM (clientes bolivianos, ventas pactadas, interacciones)
- Ordenes de trabajo, incidencias, cronogramas, equipos y maquinaria
"""

import sys
import os
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, timedelta, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.classes.postgres import PostgreSQL

def round_money(val):
    if isinstance(val, (int, float, str)):
        val = Decimal(str(val))
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def poblar_todo():
    db = PostgreSQL()
    db.create_connection()
    cur = db.cur
    conn = db.conn

    print("Iniciando poblado coherente de datos multi-tenant para Bolivia...")

    try:
        # =========================================================================
        # 1. PERSONAS Y USUARIOS / ROLES BASE
        # =========================================================================
        print("\n--- 1. Asegurando Personas y Asignaciones ---")
        personas_seed = [
            # Para Empresa 1 (OBRATEC)
            ("Ing. Marcelo Banegas Roca", "1982-05-14", "4589201-SC", "Av. San Martin #450, Equipetrol, Santa Cruz", "+591 71029384", "Santa Cruz"),
            ("Arq. Fabiola Justiniano Chavez", "1988-11-20", "5629103-SC", "Condominio La Riviera #12B, Santa Cruz", "+591 76019283", "Santa Cruz"),
            ("Lic. Javier Mercado Torrico", "1979-03-08", "3829102-CB", "Calle Sucre #220, Cochabamba", "+591 72190847", "Cochabamba"),
            ("Dr. Walter Suarez Hurtado", "1975-09-17", "2910293-SC", "Av. Las Palmas #780, Santa Cruz", "+591 77382910", "Santa Cruz"),
            
            # Para Empresa 3 (LA ROCA)
            ("Ing. Rolando Anez Dorado", "1984-07-22", "4920192-SC", "Urubo Golf Country Club Casa 45, Santa Cruz", "+591 70839201", "Santa Cruz"),
            ("Lic. Claudia Mendez Ribera", "1989-12-05", "5829104-SC", "Av. Beni 4to Anillo, Santa Cruz", "+591 75091823", "Santa Cruz"),
            ("Dra. Patricia Vaca Diez", "1981-04-18", "4729102-SC", "Condominio Sevilla Pinatar, Santa Cruz", "+591 76629183", "Santa Cruz"),
            
            # Para Empresa 4 (EL GRAN PIRAI)
            ("Ing. Carlos Hugo Vaca Pereira", "1978-02-11", "3492019-SC", "Av. Cumavi #120, Villa 1ro de Mayo, Santa Cruz", "+591 70918273", "Santa Cruz"),
            ("Prof. Martha Soliz Menacho", "1985-08-30", "4820193-SC", "Av. Paurito #550, Plan 3000, Santa Cruz", "+591 72619284", "Santa Cruz"),
            ("Lic. Hernan Terrazas Rojas", "1980-10-15", "3920194-LP", "Calle 21 Calacoto #150, La Paz", "+591 77291029", "La Paz"),

            # Para Empresa 2 (CLIENTES SIN EMPRESA)
            ("Ing. Daniel Siles Guzman", "1986-06-19", "5192039-SC", "Av. Bush #890, Santa Cruz", "+591 73192019", "Santa Cruz"),
            ("Lic. Valeria Paz Soldan", "1990-01-25", "6192049-SC", "Calle Chuquisaca #340, Santa Cruz", "+591 74619201", "Santa Cruz"),
        ]

        persona_ids = {}
        for nombre, fnac, ci, direccion, tel, ubi in personas_seed:
            cur.execute("SELECT id_persona FROM obras.t_persona WHERE ci = %s;", (ci,))
            row = cur.fetchone()
            if row:
                persona_ids[ci] = row[0]
            else:
                cur.execute("""
                    INSERT INTO obras.t_persona(nombre_completo, fecha_nacimiento, ci, direccion, telefono, ubicacion)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_persona;
                """, (nombre, fnac, ci, direccion, tel, ubi))
                persona_ids[ci] = cur.fetchone()[0]

        # Clientes CRM por empresa
        crm_clients_seed = [
            # Empresa 1
            (1, persona_ids["4589201-SC"], "mbanegas@gmail.com", "CLIENTE", "ACTIVO", 850000),
            (1, persona_ids["5629103-SC"], "fjustiniano@cotas.com.bo", "CLIENTE", "ACTIVO", 650000),
            (1, persona_ids["3829102-CB"], "jmercado@inversiones.bo", "CLIENTE", "ACTIVO", 1200000),
            (1, persona_ids["2910293-SC"], "wsuarez@clinica.com.bo", "PROSPECTO", "INTERESADO", 900000),

            # Empresa 3
            (3, persona_ids["4920192-SC"], "ranez@agropecuaria.bo", "CLIENTE", "ACTIVO", 1500000),
            (3, persona_ids["5829104-SC"], "cmendez@gmail.com", "CLIENTE", "ACTIVO", 1300000),
            (3, persona_ids["4729102-SC"], "pvaca@salud.bo", "CLIENTE", "ACTIVO", 350000),

            # Empresa 4
            (4, persona_ids["3492019-SC"], "cvaca@granpirai.bo", "CLIENTE", "ACTIVO", 1800000),
            (4, persona_ids["4820193-SC"], "msoliz@educacion.gob.bo", "CLIENTE", "ACTIVO", 950000),
            (4, persona_ids["3920194-LP"], "hterrazas@consultores.bo", "CLIENTE", "ACTIVO", 1600000),

            # Empresa 2
            (2, persona_ids["5192039-SC"], "dsiles@gmail.com", "CLIENTE", "ACTIVO", 400000),
            (2, persona_ids["6192049-SC"], "vpaz@comercial.bo", "CLIENTE", "ACTIVO", 250000),
        ]

        client_ids = {} # (id_empresa, ci) -> id_cliente
        ci_by_pid = {v: k for k, v in persona_ids.items()}
        for id_emp, id_per, email, tcli, est, presup in crm_clients_seed:
            cur.execute("""
                SELECT id_cliente FROM obras.t_crm_cliente
                WHERE id_empresa = %s AND id_persona = %s;
            """, (id_emp, id_per))
            row = cur.fetchone()
            ci = ci_by_pid[id_per]
            if row:
                client_ids[(id_emp, ci)] = row[0]
            else:
                cur.execute("""
                    INSERT INTO obras.t_crm_cliente(id_empresa, id_persona, email, tipo_cliente, estado, origen, presupuesto_estimado)
                    VALUES (%s, %s, %s, %s, %s, 'PORTAL_WEB', %s) RETURNING id_cliente;
                """, (id_emp, id_per, email, tcli, est, presup))
                client_ids[(id_emp, ci)] = cur.fetchone()[0]

        # =========================================================================
        # 2. MODELOS ARQUITECTÓNICOS (t_modelo_unidad)
        # =========================================================================
        print("\n--- 2. Asegurando Modelos de Unidad ---")
        modelos_seed = [
            (1, "Modelo Tajibo 1D", "Departamento moderno de 1 suite para profesionales", "DEPARTAMENTO", Decimal("55.00"), 1),
            (1, "Modelo Toborochi 2D", "Departamento confortable de 2 dormitorios con balcón", "DEPARTAMENTO", Decimal("88.00"), 1),
            (1, "Modelo Jacarandá 3D", "Departamento familiar de 3 dormitorios con dependencia", "DEPARTAMENTO", Decimal("130.00"), 1),
            (1, "Penthouse Sky Equipetrol", "Exclusivo penthouse doble altura con terraza privada", "DEPARTAMENTO", Decimal("210.00"), 2),
            (1, "Casa Campestre Zen", "Vivienda unifamiliar con jardín posterior y pérgola", "VIVIENDA", Decimal("150.00"), 2),

            (3, "Villa Colonial Urubó", "Residencia de lujo estilo campestre con galería y piscina", "VIVIENDA", Decimal("250.00"), 2),
            (3, "Suite Laguna Panorámica", "Departamento de alta gama con vista a la laguna", "DEPARTAMENTO", Decimal("85.00"), 1),
            (3, "Residencia Familiar Los Parques", "Casa moderna con acabados en madera tajibo", "VIVIENDA", Decimal("160.00"), 2),

            (4, "Módulo Pedagógico 6 Aulas", "Infraestructura escolar sismorresistente con tinglado", "OTRO", Decimal("450.00"), 2),
            (4, "Bloque Consultorio Sanitario", "Infraestructura hospitalaria con salas de atención", "OTRO", Decimal("280.00"), 1),
            (4, "Cancha Polifuncional Municipal", "Área deportiva con piso de hormigón y graderías", "OTRO", Decimal("600.00"), 1),

            (2, "Departamento Estándar", "Vivienda multifamiliar económica", "DEPARTAMENTO", Decimal("72.00"), 1),
            (2, "Oficina Comercial Básica", "Espacio para consultorio o bufete", "OFICINA", Decimal("65.00"), 1),
        ]

        modelo_ids = {} # (id_empresa, nombre) -> id_modelo
        for id_emp, nom, desc, tipo, sup, plan in modelos_seed:
            cur.execute("SELECT id_modelo FROM obras.t_modelo_unidad WHERE id_empresa = %s AND nombre = %s;", (id_emp, nom))
            row = cur.fetchone()
            if row:
                modelo_ids[(id_emp, nom)] = row[0]
            else:
                cur.execute("""
                    INSERT INTO obras.t_modelo_unidad(id_empresa, nombre, descripcion, tipo_unidad, superficie_base, cantidad_plantas_base, activo)
                    VALUES (%s, %s, %s, %s, %s, %s, true) RETURNING id_modelo;
                """, (id_emp, nom, desc, tipo, sup, plan))
                modelo_ids[(id_emp, nom)] = cur.fetchone()[0]

        # =========================================================================
        # 3. ESTRUCTURAS DE OBRA Y UNIDADES DE CONSTRUCCIÓN (CU1, CU12)
        # =========================================================================
        print("\n--- 3. Creando Estructuras y Unidades de Construcción ---")
        # Cada unidad necesita un id_estructura terminal ÚNICO por la restriccion uq_unidad_estructura.
        # Definimos las unidades por obra con sus datos tecnicos y comerciales.
        unidades_def = [
            # -------------------------------------------------------------
            # EMPRESA 1 (OBRATEC)
            # Obra 26: Edificio Sky Equipetrol (BOB) -> MARGEN POSITIVO (+22%)
            # -------------------------------------------------------------
            {"id_obra": 26, "id_empresa": 1, "codigo": "SKY-P01-101", "nombre_est": "Depto 101 Suite Tajibo", "tipo": "DEPARTAMENTO", "m2": Decimal("55.00"), "plantas": 1, "acabado": "LUJO", "estado": "FINALIZADO", "modelo": modelo_ids[(1, "Modelo Tajibo 1D")], "venta_estado": "VENDIDO", "monto_pactado": Decimal("410000.00"), "cliente_ci": "4589201-SC"},
            {"id_obra": 26, "id_empresa": 1, "codigo": "SKY-P02-201", "nombre_est": "Depto 201 Toborochi 2D", "tipo": "DEPARTAMENTO", "m2": Decimal("88.00"), "plantas": 1, "acabado": "LUJO", "estado": "FINALIZADO", "modelo": modelo_ids[(1, "Modelo Toborochi 2D")], "venta_estado": "VENDIDO", "monto_pactado": Decimal("620000.00"), "cliente_ci": "5629103-SC"},
            {"id_obra": 26, "id_empresa": 1, "codigo": "SKY-P04-401", "nombre_est": "Depto 401 Jacaranda 3D", "tipo": "DEPARTAMENTO", "m2": Decimal("130.00"), "plantas": 1, "acabado": "LUJO", "estado": "FINALIZADO", "modelo": modelo_ids[(1, "Modelo Jacarandá 3D")], "venta_estado": "VENDIDO", "monto_pactado": Decimal("820000.00"), "cliente_ci": "3829102-CB"},
            {"id_obra": 26, "id_empresa": 1, "codigo": "SKY-PH-1001", "nombre_est": "Penthouse 1001 Sky", "tipo": "DEPARTAMENTO", "m2": Decimal("210.00"), "plantas": 2, "acabado": "LUJO", "estado": "FINALIZADO", "modelo": modelo_ids[(1, "Penthouse Sky Equipetrol")], "venta_estado": "RESERVADO", "monto_pactado": Decimal("1450000.00"), "cliente_ci": "2910293-SC"},
            # Total ventas pactadas VENDIDO en Obra 26 = 410,000 + 620,000 + 820,000 = 1,850,000 BOB.

            # -------------------------------------------------------------
            # Obra 17: Garden Zen (BOB) -> DÉFICIT REALISTA (-15%)
            # -------------------------------------------------------------
            {"id_obra": 17, "id_empresa": 1, "codigo": "GZEN-VIV-01", "nombre_est": "Vivienda Familiar Zen 01", "tipo": "VIVIENDA", "m2": Decimal("140.00"), "plantas": 2, "acabado": "NORMAL", "estado": "FINALIZADO", "modelo": modelo_ids[(1, "Casa Campestre Zen")], "venta_estado": "VENDIDO", "monto_pactado": Decimal("480000.00"), "cliente_ci": "4589201-SC"},
            {"id_obra": 17, "id_empresa": 1, "codigo": "GZEN-VIV-02", "nombre_est": "Vivienda Familiar Zen 02", "tipo": "VIVIENDA", "m2": Decimal("160.00"), "plantas": 2, "acabado": "NORMAL", "estado": "FINALIZADO", "modelo": modelo_ids[(1, "Casa Campestre Zen")], "venta_estado": "RESERVADO", "monto_pactado": Decimal("560000.00"), "cliente_ci": "5629103-SC"},
            # Total ventas pactadas VENDIDO en Obra 17 = 480,000 BOB.

            # -------------------------------------------------------------
            # Obra 8: Green Tower (BOB) -> MARGEN POSITIVO (+19%)
            # -------------------------------------------------------------
            {"id_obra": 8, "id_empresa": 1, "codigo": "GTOW-OF-201", "nombre_est": "Oficina Ejecutiva 201", "tipo": "OFICINA", "m2": Decimal("65.00"), "plantas": 1, "acabado": "LUJO", "estado": "EN_CONSTRUCCION", "modelo": None, "venta_estado": "VENDIDO", "monto_pactado": Decimal("460000.00"), "cliente_ci": "3829102-CB"},
            {"id_obra": 8, "id_empresa": 1, "codigo": "GTOW-OF-202", "nombre_est": "Oficina Ejecutiva 202", "tipo": "OFICINA", "m2": Decimal("75.00"), "plantas": 1, "acabado": "LUJO", "estado": "EN_CONSTRUCCION", "modelo": None, "venta_estado": "VENDIDO", "monto_pactado": Decimal("510000.00"), "cliente_ci": "2910293-SC"},
            # Total ventas pactadas VENDIDO en Obra 8 = 970,000 BOB.

            # -------------------------------------------------------------
            # EMPRESA 3 (CONSTRUCTORA LA ROCA)
            # Obra 27: Condominio Campestre Urubo Village (BOB) -> MARGEN POSITIVO (+25%)
            # -------------------------------------------------------------
            {"id_obra": 27, "id_empresa": 3, "codigo": "URB-VIL-01", "nombre_est": "Villa Campestre Manzano 4 Lote 1", "tipo": "VIVIENDA", "m2": Decimal("240.00"), "plantas": 2, "acabado": "LUJO", "estado": "FINALIZADO", "modelo": modelo_ids[(3, "Villa Colonial Urubó")], "venta_estado": "VENDIDO", "monto_pactado": Decimal("1350000.00"), "cliente_ci": "4920192-SC"},
            {"id_obra": 27, "id_empresa": 3, "codigo": "URB-VIL-02", "nombre_est": "Villa Campestre Manzano 4 Lote 2", "tipo": "VIVIENDA", "m2": Decimal("260.00"), "plantas": 2, "acabado": "LUJO", "estado": "FINALIZADO", "modelo": modelo_ids[(3, "Villa Colonial Urubó")], "venta_estado": "VENDIDO", "monto_pactado": Decimal("1450000.00"), "cliente_ci": "5829104-SC"},
            {"id_obra": 27, "id_empresa": 3, "codigo": "URB-LOT-05", "nombre_est": "Lote Urbanizado Manzano 5", "tipo": "LOTE", "m2": Decimal("600.00"), "plantas": 0, "acabado": "NORMAL", "estado": "FINALIZADO", "modelo": None, "venta_estado": "VENDIDO", "monto_pactado": Decimal("420000.00"), "cliente_ci": "4729102-SC"},
            # Total ventas pactadas VENDIDO en Obra 27 = 1,350,000 + 1,450,000 + 420,000 = 3,220,000 BOB.

            # -------------------------------------------------------------
            # Obra 7: Edificio Laguna (USD) -> DÉFICIT REALISTA (-13%)
            # -------------------------------------------------------------
            {"id_obra": 7, "id_empresa": 3, "codigo": "LAG-SUITE-301", "nombre_est": "Suite Panorámica Nivel 3", "tipo": "DEPARTAMENTO", "m2": Decimal("72.00"), "plantas": 1, "acabado": "LUJO", "estado": "EN_CONSTRUCCION", "modelo": modelo_ids[(3, "Suite Laguna Panorámica")], "venta_estado": "VENDIDO", "monto_pactado": Decimal("125000.00"), "cliente_ci": "4920192-SC"},
            {"id_obra": 7, "id_empresa": 3, "codigo": "LAG-DPTO-502", "nombre_est": "Departamento Vista Lago Nivel 5", "tipo": "DEPARTAMENTO", "m2": Decimal("95.00"), "plantas": 1, "acabado": "LUJO", "estado": "EN_CONSTRUCCION", "modelo": modelo_ids[(3, "Suite Laguna Panorámica")], "venta_estado": "VENDIDO", "monto_pactado": Decimal("165000.00"), "cliente_ci": "5829104-SC"},
            # Total ventas pactadas VENDIDO en Obra 7 = 290,000 USD.

            # -------------------------------------------------------------
            # Obra 12: Parque Residencial (USD) -> MARGEN POSITIVO (+19%)
            # -------------------------------------------------------------
            {"id_obra": 12, "id_empresa": 3, "codigo": "PARQ-VIV-101", "nombre_est": "Casa Modelo Parques 101", "tipo": "VIVIENDA", "m2": Decimal("150.00"), "plantas": 2, "acabado": "NORMAL", "estado": "PLANIFICADO", "modelo": modelo_ids[(3, "Residencia Familiar Los Parques")], "venta_estado": "VENDIDO", "monto_pactado": Decimal("180000.00"), "cliente_ci": "4920192-SC"},
            {"id_obra": 12, "id_empresa": 3, "codigo": "PARQ-VIV-102", "nombre_est": "Casa Modelo Parques 102", "tipo": "VIVIENDA", "m2": Decimal("155.00"), "plantas": 2, "acabado": "NORMAL", "estado": "PLANIFICADO", "modelo": modelo_ids[(3, "Residencia Familiar Los Parques")], "venta_estado": "VENDIDO", "monto_pactado": Decimal("185000.00"), "cliente_ci": "4729102-SC"},
            # Total ventas pactadas VENDIDO en Obra 12 = 365,000 USD.

            # -------------------------------------------------------------
            # EMPRESA 4 (CONSTRUCTORA EL GRAN PIRAI)
            # Obra 9: Parque Los Mangales (BOB) -> MARGEN POSITIVO (+15%)
            # -------------------------------------------------------------
            {"id_obra": 9, "id_empresa": 4, "codigo": "MANG-CAN-01", "nombre_est": "Cancha Polifuncional Norte", "tipo": "OTRO", "m2": Decimal("600.00"), "plantas": 1, "acabado": "NORMAL", "estado": "FINALIZADO", "modelo": modelo_ids[(4, "Cancha Polifuncional Municipal")], "venta_estado": "ENTREGADO", "monto_pactado": Decimal("280000.00"), "cliente_ci": "3492019-SC"},
            {"id_obra": 9, "id_empresa": 4, "codigo": "MANG-CAN-02", "nombre_est": "Cancha Polifuncional Sur", "tipo": "OTRO", "m2": Decimal("600.00"), "plantas": 1, "acabado": "NORMAL", "estado": "FINALIZADO", "modelo": modelo_ids[(4, "Cancha Polifuncional Municipal")], "venta_estado": "ENTREGADO", "monto_pactado": Decimal("295000.00"), "cliente_ci": "3492019-SC"},
            {"id_obra": 9, "id_empresa": 4, "codigo": "MANG-CAM-03", "nombre_est": "Caminerías Pavic y Jardineras", "tipo": "OTRO", "m2": Decimal("400.00"), "plantas": 1, "acabado": "NORMAL", "estado": "FINALIZADO", "modelo": None, "venta_estado": "VENDIDO", "monto_pactado": Decimal("215000.00"), "cliente_ci": "3920194-LP"},
            # Total ventas pactadas en Obra 9 = 790,000 BOB.

            # -------------------------------------------------------------
            # Obra 28: Modulo Educativo Plan 3000 (BOB) -> DÉFICIT REALISTA (-9%)
            # -------------------------------------------------------------
            {"id_obra": 28, "id_empresa": 4, "codigo": "MED-AUL-PRIM", "nombre_est": "Bloque Aulas Ciclo Primaria", "tipo": "OTRO", "m2": Decimal("450.00"), "plantas": 2, "acabado": "NORMAL", "estado": "EN_CONSTRUCCION", "modelo": modelo_ids[(4, "Módulo Pedagógico 6 Aulas")], "venta_estado": "VENDIDO", "monto_pactado": Decimal("950000.00"), "cliente_ci": "4820193-SC"},
            {"id_obra": 28, "id_empresa": 4, "codigo": "MED-AUL-SEC", "nombre_est": "Bloque Aulas Ciclo Secundaria", "tipo": "OTRO", "m2": Decimal("420.00"), "plantas": 2, "acabado": "NORMAL", "estado": "EN_CONSTRUCCION", "modelo": modelo_ids[(4, "Módulo Pedagógico 6 Aulas")], "venta_estado": "VENDIDO", "monto_pactado": Decimal("850000.00"), "cliente_ci": "4820193-SC"},
            # Total ventas pactadas en Obra 28 = 1,800,000 BOB.

            # -------------------------------------------------------------
            # Obra 29: Centro de Salud Villa 1ro de Mayo (BOB) -> MARGEN POSITIVO (+19%)
            # -------------------------------------------------------------
            {"id_obra": 29, "id_empresa": 4, "codigo": "CSAL-URG-01", "nombre_est": "Bloque Urgencias y Consultorios", "tipo": "OTRO", "m2": Decimal("320.00"), "plantas": 1, "acabado": "NORMAL", "estado": "PLANIFICADO", "modelo": modelo_ids[(4, "Bloque Consultorio Sanitario")], "venta_estado": "VENDIDO", "monto_pactado": Decimal("1100000.00"), "cliente_ci": "3492019-SC"},
            {"id_obra": 29, "id_empresa": 4, "codigo": "CSAL-FARM-02", "nombre_est": "Bloque Farmacia y Laboratorio", "tipo": "OTRO", "m2": Decimal("180.00"), "plantas": 1, "acabado": "NORMAL", "estado": "PLANIFICADO", "modelo": modelo_ids[(4, "Bloque Consultorio Sanitario")], "venta_estado": "VENDIDO", "monto_pactado": Decimal("450000.00"), "cliente_ci": "3920194-LP"},
            # Total ventas pactadas en Obra 29 = 1,550,000 BOB.

            # -------------------------------------------------------------
            # EMPRESA 2 (CLIENTES SIN EMPRESA)
            # Obra 4: Edificaciones P2026-08-0003 (BOB) -> MARGEN POSITIVO (+19%)
            # -------------------------------------------------------------
            {"id_obra": 4, "id_empresa": 2, "codigo": "ED4-DPTO-101", "nombre_est": "Dpto 101 Edificio Central", "tipo": "DEPARTAMENTO", "m2": Decimal("72.00"), "plantas": 1, "acabado": "NORMAL", "estado": "EN_CONSTRUCCION", "modelo": modelo_ids[(2, "Departamento Estándar")], "venta_estado": "VENDIDO", "monto_pactado": Decimal("380000.00"), "cliente_ci": "5192039-SC"},
            {"id_obra": 4, "id_empresa": 2, "codigo": "ED4-DPTO-102", "nombre_est": "Dpto 102 Edificio Central", "tipo": "DEPARTAMENTO", "m2": Decimal("78.00"), "plantas": 1, "acabado": "NORMAL", "estado": "EN_CONSTRUCCION", "modelo": modelo_ids[(2, "Departamento Estándar")], "venta_estado": "VENDIDO", "monto_pactado": Decimal("410000.00"), "cliente_ci": "6192049-SC"},
            # Total ventas pactadas en Obra 4 = 790,000 BOB.

            # -------------------------------------------------------------
            # Obra 6: Edificio Solaris (USD) -> MARGEN POSITIVO (+18%)
            # -------------------------------------------------------------
            {"id_obra": 6, "id_empresa": 2, "codigo": "SOL-OF-101", "nombre_est": "Oficina Solaris 101", "tipo": "OFICINA", "m2": Decimal("65.00"), "plantas": 1, "acabado": "NORMAL", "estado": "PLANIFICADO", "modelo": modelo_ids[(2, "Oficina Comercial Básica")], "venta_estado": "VENDIDO", "monto_pactado": Decimal("95000.00"), "cliente_ci": "5192039-SC"},
            {"id_obra": 6, "id_empresa": 2, "codigo": "SOL-OF-102", "nombre_est": "Oficina Solaris 102", "tipo": "OFICINA", "m2": Decimal("75.00"), "plantas": 1, "acabado": "NORMAL", "estado": "PLANIFICADO", "modelo": modelo_ids[(2, "Oficina Comercial Básica")], "venta_estado": "VENDIDO", "monto_pactado": Decimal("115000.00"), "cliente_ci": "6192049-SC"},
            # Total ventas pactadas en Obra 6 = 210,000 USD.
        ]

        unidad_records = {} # codigo -> id_unidad
        for u in unidades_def:
            # 1. Asegurar estructura terminal unica para esta unidad
            cur.execute("""
                SELECT es.id_estructura 
                FROM obras.t_estructura_obra es
                JOIN obras.t_unidad_construccion un USING(id_estructura)
                WHERE un.codigo = %s;
            """, (u["codigo"],))
            row_est = cur.fetchone()
            
            if row_est:
                id_est = row_est[0]
            else:
                cur.execute("""
                    INSERT INTO obras.t_estructura_obra(id_obra, id_padre, nombre, tipo, descripcion, orden)
                    VALUES (%s, NULL, %s, %s, %s, 1) RETURNING id_estructura;
                """, (u["id_obra"], u["nombre_est"], u["tipo"], f"Estructura terminal para unidad {u['codigo']}"))
                id_est = cur.fetchone()[0]

            # 2. Asegurar registro en t_unidad_construccion
            cur.execute("SELECT id_unidad FROM obras.t_unidad_construccion WHERE codigo = %s;", (u["codigo"],))
            row_un = cur.fetchone()
            if row_un:
                id_un = row_un[0]
                cur.execute("""
                    UPDATE obras.t_unidad_construccion
                    SET superficie = %s, especificacion_acabado = %s, estado = %s, id_modelo = %s
                    WHERE id_unidad = %s;
                """, (u["m2"], u["acabado"], u["estado"], u["modelo"], id_un))
            else:
                cur.execute("""
                    INSERT INTO obras.t_unidad_construccion(id_estructura, codigo, tipo_unidad, superficie, cantidad_plantas, estado, id_modelo, especificacion_acabado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_unidad;
                """, (id_est, u["codigo"], u["tipo"], u["m2"], u["plantas"], u["estado"], u["modelo"], u["acabado"]))
                id_un = cur.fetchone()[0]

            unidad_records[u["codigo"]] = id_un

            # 3. Asegurar venta / asociacion en t_crm_cliente_unidad
            id_cli = client_ids.get((u["id_empresa"], u["cliente_ci"]))
            if id_cli and u.get("monto_pactado"):
                cur.execute("""
                    SELECT id_cliente_unidad FROM obras.t_crm_cliente_unidad
                    WHERE id_unidad = %s;
                """, (id_un,))
                row_cu = cur.fetchone()
                if row_cu:
                    cur.execute("""
                        UPDATE obras.t_crm_cliente_unidad
                        SET id_cliente = %s, estado_asociacion = %s, monto_pactado = %s, fecha_asociacion = NOW()
                        WHERE id_cliente_unidad = %s;
                    """, (id_cli, u["venta_estado"], u["monto_pactado"], row_cu[0]))
                else:
                    cur.execute("""
                        INSERT INTO obras.t_crm_cliente_unidad(id_cliente, id_unidad, estado_asociacion, monto_pactado, fecha_asociacion)
                        VALUES (%s, %s, %s, %s, NOW());
                    """, (id_cli, id_un, u["venta_estado"], u["monto_pactado"]))

            # 4. Asegurar ambientes y caracteristicas para CU12 / CU34
            cur.execute("SELECT count(*) FROM obras.t_unidad_ambiente WHERE id_unidad = %s;", (id_un,))
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    INSERT INTO obras.t_unidad_ambiente(id_unidad, nombre, cantidad) VALUES
                    (%s, 'Living-Comedor integrado', 1),
                    (%s, 'Cocina con mesón de granito', 1),
                    (%s, 'Dormitorio Principal Suite', 1),
                    (%s, 'Baño con box de vidrio templado', 1);
                """, (id_un, id_un, id_un, id_un))

            cur.execute("SELECT count(*) FROM obras.t_unidad_caracteristica WHERE id_unidad = %s;", (id_un,))
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    INSERT INTO obras.t_unidad_caracteristica(id_unidad, nombre, valor) VALUES
                    (%s, 'Gas Domiciliario', 'Instalación YPFB aprobada'),
                    (%s, 'Pisos', 'Porcelanato pulido 60x60'),
                    (%s, 'Climatización', 'Preinstalación de A/C inverter');
                """, (id_un, id_un, id_un))

        # =========================================================================
        # 4. CONTROLES DE COSTO, ESTIMACIONES Y COSTOS EJECUTADOS (CU17, CU22)
        # =========================================================================
        print("\n--- 4. Configurando Controles de Costo y Costos Ejecutados ---")

        # Usuarios registradores por empresa
        user_reg = {
            1: 1, # admin en OBRATEC
            2: 2, # ernesto en sin empresa
            3: 8, # EDDYST en LA ROCA
            4: 5, # PABLOPT en EL GRAN PIRAI
        }

        # Especificacion de presupuesto y costos por obra:
        # Ventas vs Costos -> Margen / Deficit
        obras_costos_target = [
            # Obra 26 (OBRATEC, BOB): Ventas 1,850,000. Costos Target = 1,438,100. Margen = +411,900 (+22.26%)
            {"id_obra": 26, "id_empresa": 1, "moneda": "BOB", "costos_target": Decimal("1438100.00")},

            # Obra 17 (OBRATEC, BOB): Ventas 480,000. Costos Target = 552,080. DEFICIT = -72,080 (-15.01%)
            {"id_obra": 17, "id_empresa": 1, "moneda": "BOB", "costos_target": Decimal("552080.00")},

            # Obra 8 (OBRATEC, BOB): Ventas 970,000. Costos Target = 785,000. Margen = +185,000 (+19.07%)
            {"id_obra": 8, "id_empresa": 1, "moneda": "BOB", "costos_target": Decimal("785000.00")},

            # Obra 27 (LA ROCA, BOB): Ventas 3,220,000. Costos Target = 2,414,200. Margen = +805,800 (+25.02%)
            {"id_obra": 27, "id_empresa": 3, "moneda": "BOB", "costos_target": Decimal("2414200.00")},

            # Obra 7 (LA ROCA, USD): Ventas 290,000. Costos Target = 328,500. DEFICIT = -$38,500 (-13.27%)
            {"id_obra": 7, "id_empresa": 3, "moneda": "USD", "costos_target": Decimal("328500.00")},

            # Obra 12 (LA ROCA, USD): Ventas 365,000. Costos Target = 295,000. Margen = +$70,000 (+19.17%)
            {"id_obra": 12, "id_empresa": 3, "moneda": "USD", "costos_target": Decimal("295000.00")},

            # Obra 9 (EL GRAN PIRAI, BOB): Ventas 790,000. Costos Target = 668,425. Margen = +121,575 (+15.38%)
            {"id_obra": 9, "id_empresa": 4, "moneda": "BOB", "costos_target": Decimal("668425.00")},

            # Obra 28 (EL GRAN PIRAI, BOB): Ventas 1,800,000. Costos Target = 1,965,000. DEFICIT = -165,000 (-9.16%)
            {"id_obra": 28, "id_empresa": 4, "moneda": "BOB", "costos_target": Decimal("1965000.00")},

            # Obra 29 (EL GRAN PIRAI, BOB): Ventas 1,550,000. Costos Target = 1,245,000. Margen = +305,000 (+19.67%)
            {"id_obra": 29, "id_empresa": 4, "moneda": "BOB", "costos_target": Decimal("1245000.00")},

            # Obra 4 (CLIENTES SIN EMPRESA, BOB): Ventas 790,000. Costos Target = 640,000. Margen = +150,000 (+18.98%)
            {"id_obra": 4, "id_empresa": 2, "moneda": "BOB", "costos_target": Decimal("640000.00")},

            # Obra 6 (CLIENTES SIN EMPRESA, USD): Ventas 210,000. Costos Target = 172,000. Margen = +$38,000 (+18.09%)
            {"id_obra": 6, "id_empresa": 2, "moneda": "USD", "costos_target": Decimal("172000.00")},
        ]

        for oct_info in obras_costos_target:
            id_obra = oct_info["id_obra"]
            id_emp = oct_info["id_empresa"]
            mon = oct_info["moneda"]
            c_target = oct_info["costos_target"]
            u_reg = user_reg[id_emp]

            # 1. Asegurar estimacion aprobada
            cur.execute("""
                SELECT id_estimacion FROM obras.t_estimacion
                WHERE id_obra = %s AND id_empresa = %s AND estado = 'APROBADA'
                ORDER BY version DESC LIMIT 1;
            """, (id_obra, id_emp))
            row_est = cur.fetchone()
            if row_est:
                id_est = row_est[0]
            else:
                cur.execute("""
                    INSERT INTO obras.t_estimacion(id_obra, id_empresa, nombre, version, estado, monto_total, cliente)
                    VALUES (%s, %s, %s, 1, 'APROBADA', %s, 'Cliente Corporativo') RETURNING id_estimacion;
                """, (id_obra, id_emp, f"Presupuesto Base Obra {id_obra}", c_target * Decimal("1.20")))
                id_est = cur.fetchone()[0]

            # 2. Asegurar al menos una partida de APU en t_estimacion_analisis_precio_unitario
            cur.execute("""
                SELECT id_estimacion_analisis_precio_unitario FROM obras.t_estimacion_analisis_precio_unitario
                WHERE id_estimacion = %s LIMIT 1;
            """, (id_est,))
            row_ea = cur.fetchone()
            if row_ea:
                id_ea = row_ea[0]
            else:
                # Obtener o crear APU para esta empresa
                cur.execute("SELECT id_analisis_precio_unitario FROM obras.t_analisis_precio_unitario WHERE id_empresa = %s LIMIT 1;", (id_emp,))
                row_apu = cur.fetchone()
                if row_apu:
                    id_apu = row_apu[0]
                else:
                    cur.execute("""
                        INSERT INTO obras.t_analisis_precio_unitario(id_empresa, codigo, nombre, id_unidad_medida, tipo_analisis_precio_unitario, activo)
                        VALUES (%s, 'APU-GEN-01', 'Hormigón Armado y Mampostería General', 4, 'OBRA_GRIS', true) RETURNING id_analisis_precio_unitario;
                    """, (id_emp,))
                    id_apu = cur.fetchone()[0]

                cur.execute("""
                    INSERT INTO obras.t_estimacion_analisis_precio_unitario(id_estimacion, id_analisis_precio_unitario, cantidad, orden, item_codigo, precio_unitario, costo_directo_unitario)
                    VALUES (%s, %s, 100.00, 1, '01.01', 500.00, 450.00) RETURNING id_estimacion_analisis_precio_unitario;
                """, (id_est, id_apu))
                id_ea = cur.fetchone()[0]

            # 3. Asegurar Control de Costos ACTIVO en t_control_costo_obra
            cur.execute("""
                SELECT id_control_costo FROM obras.t_control_costo_obra
                WHERE id_obra = %s AND id_empresa = %s AND estado = 'ACTIVO' AND moneda = %s
                LIMIT 1;
            """, (id_obra, id_emp, mon))
            row_cc = cur.fetchone()
            if row_cc:
                id_cc = row_cc[0]
            else:
                cur.execute("""
                    INSERT INTO obras.t_control_costo_obra(id_empresa, id_obra, id_estimacion_base, version_presupuesto, moneda, estado, seleccionado_por)
                    VALUES (%s, %s, %s, 1, %s, 'ACTIVO', %s) RETURNING id_control_costo;
                """, (id_emp, id_obra, id_est, mon, u_reg))
                id_cc = cur.fetchone()[0]

            # 4. Calcular suma de costos actuales registrados
            cur.execute("""
                SELECT COALESCE(SUM(monto), 0) FROM obras.t_costo_ejecutado
                WHERE id_control_costo = %s AND id_empresa = %s AND id_obra = %s AND estado = 'REGISTRADO';
            """, (id_cc, id_emp, id_obra))
            costo_actual = cur.fetchone()[0]
            diferencia = round_money(c_target - costo_actual)

            if diferencia > Decimal("0.00"):
                # Insertar costo calibrado para alcanzar el target exacto
                # chk_costo_ejecutado_monto exige: monto = round(cantidad * costo_unitario, 2)
                # Usamos cantidad = 1 y costo_unitario = diferencia
                cur.execute("""
                    INSERT INTO obras.t_costo_ejecutado(
                        id_control_costo, id_empresa, id_obra, id_partida_presupuestaria,
                        fecha, concepto, categoria, cantidad, costo_unitario, monto,
                        documento, observacion, estado, registrado_por
                    ) VALUES (
                        %s, %s, %s, %s,
                        CURRENT_DATE - INTERVAL '10 days', %s, 'MATERIAL', 1.00, %s, %s,
                        'FAC-BOL-2026', 'Ajuste operativo de materiales según ejecución real', 'REGISTRADO', %s
                    );
                """, (id_cc, id_emp, id_obra, id_ea, f"Ejecución de obra civil mayor - Obra {id_obra}", diferencia, diferencia, u_reg))

        # =========================================================================
        # 5. STOCK DE MATERIALES (CU11, HU111) - CON STOCK NORMAL, BAJO Y AGOTADO
        # =========================================================================
        print("\n--- 5. Configurando Stock de Materiales en Almacén ---")
        # Asegurar lotes en t_materiales_almacen para materiales clave
        cur.execute("""
            SELECT m.id_material, m.nombre_material, m.id_empresa
            FROM obras.t_material m
            WHERE m.estado = 'ACTIVO'
            ORDER BY m.id_material LIMIT 30;
        """)
        materiales = cur.fetchall()

        idx = 0
        for id_mat, nom_mat, id_emp in materiales:
            idx += 1
            cur.execute("SELECT id_lote FROM obras.t_materiales_almacen WHERE id_material = %s LIMIT 1;", (id_mat,))
            row_lote = cur.fetchone()
            
            # Calibramos: algunos normales, algunos STOCK_BAJO, algunos SIN_STOCK
            if idx % 7 == 0:
                # SIN_STOCK (quiebre total)
                c_ini, c_act, s_min = Decimal("100.00"), Decimal("0.00"), Decimal("20.00")
            elif idx % 4 == 0:
                # STOCK_BAJO (por debajo del minimo)
                c_ini, c_act, s_min = Decimal("100.00"), Decimal("15.00"), Decimal("50.00")
            else:
                # NORMAL
                c_ini, c_act, s_min = Decimal("500.00"), Decimal("380.00"), Decimal("50.00")

            if row_lote:
                cur.execute("""
                    UPDATE obras.t_materiales_almacen
                    SET cantidad_inicial = %s, cantidad_actual = %s, stock_minimo = %s
                    WHERE id_lote = %s;
                """, (c_ini, c_act, s_min, row_lote[0]))
            else:
                cur.execute("""
                    INSERT INTO obras.t_materiales_almacen(id_material, cantidad_inicial, cantidad_actual, precio_venta, fecha_ingreso, stock_minimo)
                    VALUES (%s, %s, %s, 65.00, CURRENT_DATE - INTERVAL '15 days', %s);
                """, (id_mat, c_ini, c_act, s_min))

        # =========================================================================
        # 6. INCIDENCIAS REALISTAS EN OBRA (CU19, CU20)
        # =========================================================================
        print("\n--- 6. Asegurando Incidencias de Obra ---")
        # chk_incidencia_fechas_estado exige:
        # ABIERTA/ASIGNADA: fecha_inicio_atencion IS NULL AND fecha_fin_atencion IS NULL
        # EN_PROCESO: fecha_inicio_atencion IS NOT NULL AND fecha_fin_atencion IS NULL
        # RESUELTA/CERRADA: fecha_inicio_atencion IS NOT NULL AND fecha_fin_atencion IS NOT NULL (fin >= inicio)
        incidencias_seed = [
            # Obra 17 (Déficit)
            (17, None, 1, 6, "Nivel freático alto en subsuelo de cimientos", "Se detectó filtración severa por lluvias estacionales en Santa Cruz requiriendo motobombas y micropilotaje", "CRITICA", "RESUELTA", "Excavación Sector Norte", "2026-10-10 08:00:00+00", "2026-10-18 17:00:00+00"),
            # Obra 28 (Déficit)
            (28, None, 5, 10, "Demora en entrega de estructura metálica de tinglado", "Transporte bloqueado en carretera interdepartamental retrasó izaje de cerchas principales", "ALTA", "EN_PROCESO", "Cancha Central Tinglado", "2026-10-25 09:30:00+00", None),
            # Obra 26 (Margen Positivo)
            (26, None, 1, 6, "Microfisuras por fraguado térmico en losa piso 3", "Curado químico aplicado a tiempo; prueba esclerométrica confirma resistencia H-21", "MEDIA", "CERRADA", "Losa Piso 3", "2026-09-12 10:00:00+00", "2026-09-14 16:00:00+00"),
            # Obra 7 (Déficit)
            (7, None, 8, 4, "Socavación localizada en talud perimetral", "Colapso parcial de talud por lluvia torrencial; estabilizado con gaviones de piedra", "CRITICA", "RESUELTA", "Perímetro Lote Laguna", "2026-10-02 07:00:00+00", "2026-10-07 18:00:00+00"),
            # Obra 9 (Margen Positivo)
            (9, None, 5, 10, "Falla en luminarias LED de graderías", "Reemplazo de balastro y protección térmica contra descargas atmosféricas", "BAJA", "ABIERTA", "Graderías Cancha Los Mangales", None, None),
        ]

        for id_obr, id_un, u_reg, u_resp, tit, desc, prio, est, ubi, f_ini, f_fin in incidencias_seed:
            cur.execute("SELECT id_incidencia FROM obras.t_incidencia WHERE id_obra = %s AND titulo = %s;", (id_obr, tit))
            row_inc = cur.fetchone()
            if not row_inc:
                cur.execute("""
                    INSERT INTO obras.t_incidencia(
                        id_obra, id_unidad, id_usuario_registro, id_responsable,
                        titulo, descripcion, prioridad, estado, ubicacion,
                        fecha_inicio_atencion, fecha_fin_atencion
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (id_obr, id_un, u_reg, u_resp, tit, desc, prio, est, ubi, f_ini, f_fin))

        # =========================================================================
        # 7. ÓRDENES DE TRABAJO Y ASIGNACIONES (CU19, CU24, CU25)
        # =========================================================================
        print("\n--- 7. Asegurando Órdenes de Trabajo ---")
        ots_seed = [
            (26, "Vaciado de columnas de hormigón armado piso 4", 12, "FINALIZADO", "2026-09-01", "2026-09-15", "Se utilizó hormigón premezclado H-25"),
            (17, "Estabilización de taludes y drenaje de nivel freático", 8, "FINALIZADO", "2026-10-01", "2026-10-16", "Instalación de tuberías perforadas y geotextil"),
            (27, "Colocación de adoquines vehiculares en vía principal", 15, "EN_PROCESO", "2026-10-10", "2026-11-15", "Avance al 75% sobre capa de arena compactada"),
            (28, "Montaje de cerchas metálicas y cubierta de tinglado", 10, "EN_PROCESO", "2026-10-15", "2026-11-20", "Izaje con grúa telescópica Liebherr"),
            (9, "Pintado de líneas reglamentarias en canchas de fútbol 5", 6, "FINALIZADO", "2026-09-20", "2026-09-28", "Pintura acrílica de alto tráfico antideslizante"),
        ]

        for id_obr, tipo_t, cuad, est, f_ini, f_fin, obs in ots_seed:
            cur.execute("SELECT orden_nro FROM obras.t_orden_trabajo WHERE id_obra = %s AND tipo_trab = %s;", (id_obr, tipo_t))
            row_ot = cur.fetchone()
            if not row_ot:
                cur.execute("""
                    INSERT INTO obras.t_orden_trabajo(id_obra, tipo_trab, cuadrilla, estado, fecha_inicio, fecha_fin, observacion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING orden_nro;
                """, (id_obr, tipo_t, cuad, est, f_ini, f_fin, obs))
                nro_ot = cur.fetchone()[0]
                
                # Asignar usuario si existe
                cur.execute("SELECT id_usuario FROM obras.t_usuario WHERE id_empresa = (SELECT id_empresa FROM obras.t_obra WHERE id_obra=%s) LIMIT 1;", (id_obr,))
                u_ot = cur.fetchone()
                if u_ot:
                    cur.execute("""
                        INSERT INTO obras.t_orden_trabajo_usuario(id_orden_trabajo, id_usuario)
                        VALUES (%s, %s) ON CONFLICT DO NOTHING;
                    """, (nro_ot, u_ot[0]))

        # =========================================================================
        # 8. CRONOGRAMAS Y ACTIVIDADES (CU28)
        # =========================================================================
        print("\n--- 8. Asegurando Cronogramas de Obra ---")
        for oct_info in obras_costos_target[:6]:
            id_obr = oct_info["id_obra"]
            cur.execute("SELECT id_cronograma FROM obras.t_cronograma WHERE id_obra = %s LIMIT 1;", (id_obr,))
            row_cron = cur.fetchone()
            if not row_cron:
                cur.execute("""
                    INSERT INTO obras.t_cronograma(id_obra, nombre, descripcion, fecha_inicio, fecha_fin, version)
                    VALUES (%s, %s, 'Cronograma Maestro de Ejecución Física', '2026-08-01', '2027-04-30', 1)
                    RETURNING id_cronograma;
                """, (id_obr, f"Cronograma Maestro Obra {id_obr}"))
                id_cron = cur.fetchone()[0]

                # Actividades cumpliendo constraints de fechas reales y hitos
                cur.execute("""
                    INSERT INTO obras.t_cronograma_actividad(id_cronograma, clave, nombre, descripcion, tipo, fecha_inicio, fecha_fin, inicio_real, fin_real, avance, orden)
                    VALUES
                    (%s, 'ACT-FND', 'Excavación y Fundaciones Profundas', 'Pilotaje y zapatas de hormigón', 'ACTIVIDAD', '2026-08-01', '2026-09-30', '2026-08-01', '2026-09-30', 100, 1),
                    (%s, 'ACT-EST', 'Estructura de Hormigón Armado', 'Columnas, vigas y losas de entrepiso', 'ACTIVIDAD', '2026-10-01', '2026-12-15', '2026-10-01', NULL, 65, 2),
                    (%s, 'ACT-ALB', 'Mampostería y Cerramientos', 'Muros de ladrillo cerámico 6 huecos', 'ACTIVIDAD', '2026-11-01', '2027-02-28', '2026-11-01', NULL, 25, 3),
                    (%s, 'HITO-EST', 'Finalización de Estructura Gruesa', 'Hito clave contractual', 'HITO', '2026-12-15', '2026-12-15', NULL, NULL, 0, 4);
                """, (id_cron, id_cron, id_cron, id_cron))

        # =========================================================================
        # 9. EQUIPOS Y MAQUINARIA (CU32)
        # =========================================================================
        print("\n--- 9. Asegurando Equipos y Maquinaria ---")
        maquinaria_seed = [
            (1, "MAQ-CAT-420", "Retroexcavadora Caterpillar 420F", "PESADA", "Caterpillar", "420F", "CAT420F-2021-BO", "DISPONIBLE"),
            (1, "MAQ-MIX-350", "Hormigonera de Trompo 350L", "LIVIANA", "Menegotti", "Pro-350", "MN350-2022", "DISPONIBLE"),
            (3, "MAQ-MOT-140", "Motoniveladora CAT 140K", "PESADA", "Caterpillar", "140K", "CAT140K-2020", "DISPONIBLE"),
            (3, "MAQ-ROD-CS533", "Rodillo Compactador Vibratorio", "PESADA", "Caterpillar", "CS533E", "CAT533-2019", "DISPONIBLE"),
            (4, "MAQ-GRU-LIEB", "Grúa Torre Móvil 40m", "ESPECIALIZADA", "Liebherr", "32TT", "LIEB-2018-BO", "DISPONIBLE"),
        ]

        for id_emp, cod, nom, tipo, marca, mod, num, est in maquinaria_seed:
            cur.execute("SELECT id_equipo_maquinaria FROM obras.t_equipo_maquinaria WHERE id_empresa = %s AND codigo = %s;", (id_emp, cod))
            row_maq = cur.fetchone()
            if not row_maq:
                cur.execute("""
                    INSERT INTO obras.t_equipo_maquinaria(id_empresa, codigo, nombre, tipo, marca, modelo, numero_serie, estado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, (id_emp, cod, nom, tipo, marca, mod, num, est))

        # =========================================================================
        # 10. PAGOS SAAS MULTI-EMPRESA (CU37)
        # =========================================================================
        print("\n--- 10. Asegurando Pagos SaaS Multi-Empresa ---")
        pagos_saas_seed = [
            (1, "EMPRESARIAL", 49900, "CONFIRMADO", "CAMBIO_PLAN", "cu37-seed-obratec-emp-01", "cs_test_obratec_emp_001", "pi_3ObratecEmp001", "paid", 1),
            (1, "PROFESIONAL", 24900, "CONFIRMADO", "CONTRATACION", "cu37-seed-obratec-pro-01", "cs_test_obratec_pro_001", "pi_3ObratecPro001", "paid", 1),
            (3, "PROFESIONAL", 24900, "CONFIRMADO", "RENOVACION", "cu37-seed-laroca-pro-01", "cs_test_laroca_pro_001", "pi_3LaRocaPro001", "paid", 8),
            (3, "EMPRESARIAL", 49900, "PENDIENTE", None, "cu37-seed-laroca-emp-02", "cs_test_laroca_emp_002", None, "unpaid", 8),
        ]

        for id_emp, plan_cod, monto_m, est_p, t_aplic, idem_k, cs_id, pi_id, p_stat, u_ini in pagos_saas_seed:
            cur.execute("SELECT id_pago FROM obras.t_pago_suscripcion WHERE idempotency_key = %s;", (idem_k,))
            if not cur.fetchone():
                if est_p == "CONFIRMADO":
                    cur.execute("""
                        INSERT INTO obras.t_pago_suscripcion(
                            id_empresa, codigo_plan, version_precio, monto_menor, moneda, periodo_meses,
                            estado, tipo_aplicacion, idempotency_key, stripe_checkout_session_id,
                            stripe_payment_intent_id, stripe_payment_status, stripe_livemode,
                            iniciado_por, verificado_por, confirmado_en, aplicado_en
                        ) VALUES (
                            %s, %s, 1, %s, 'BOB', 1,
                            %s, %s, %s, %s,
                            %s, %s, false,
                            %s, %s, NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days'
                        );
                    """, (id_emp, plan_cod, monto_m, est_p, t_aplic, idem_k, cs_id, pi_id, p_stat, u_ini, u_ini))
                else:
                    cur.execute("""
                        INSERT INTO obras.t_pago_suscripcion(
                            id_empresa, codigo_plan, version_precio, monto_menor, moneda, periodo_meses,
                            estado, tipo_aplicacion, idempotency_key, stripe_checkout_session_id,
                            stripe_payment_intent_id, stripe_payment_status, stripe_livemode,
                            iniciado_por
                        ) VALUES (
                            %s, %s, 1, %s, 'BOB', 1,
                            %s, %s, %s, %s,
                            %s, %s, false,
                            %s
                        );
                    """, (id_emp, plan_cod, monto_m, est_p, t_aplic, idem_k, cs_id, pi_id, p_stat, u_ini))

        # Commit de todos los cambios
        conn.commit()
        print("\n¡POBLADO COMPLETADO EXITOSAMENTE Y TRANSACCIONALMENTE ACEPTADO!")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR DURANTE EL POBLADO: {e}")
        raise
    finally:
        db.close_connection()

if __name__ == "__main__":
    poblar_todo()

