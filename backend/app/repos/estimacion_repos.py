from app.classes.postgres import PostgreSQL
from app.config import Config
from datetime import datetime

def obtener_parametros(id_empresa: int = None):
    """
    Obtiene los parámetros vigentes para el algoritmo de estimación.
    Prioriza los parámetros específicos de la empresa sobre los globales de la plataforma.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            SELECT DISTINCT ON (categoria, codigo_clave)
                id_parametro, categoria, codigo_clave, nombre, valor_numerico, descripcion, id_empresa
            FROM {Config.SCHEMA}.t_parametro_estimacion
            WHERE activo = TRUE AND (id_empresa = %s OR id_empresa IS NULL)
            ORDER BY categoria, codigo_clave, id_empresa DESC NULLS LAST;
        """
        rows = db.execute_query(query, (id_empresa,), fetchall=True) or []
        
        parametros = {
            "costo_m2": {},
            "factor_niveles": {},
            "factor_terreno": {},
            "factor_complejidad": {}
        }
        
        for r in rows:
            cat = r[1]
            item = {
                "id_parametro": r[0],
                "codigo_clave": r[2],
                "nombre": r[3],
                "valor": float(r[4]),
                "descripcion": r[5],
                "es_personalizado": r[6] is not None
            }
            if cat == 'COSTO_M2_TIPO':
                parametros["costo_m2"][r[2]] = item
            elif cat == 'FACTOR_NIVELES':
                parametros["factor_niveles"][r[2]] = item
            elif cat == 'FACTOR_TERRENO':
                parametros["factor_terreno"][r[2]] = item
            elif cat == 'FACTOR_COMPLEJIDAD':
                parametros["factor_complejidad"][r[2]] = item
                
        return parametros
    finally:
        db.close_connection()


def resolver_clave_niveles(niveles: int) -> str:
    """Mapea la cantidad de niveles a la clave configurada."""
    try:
        n = int(niveles)
    except (ValueError, TypeError):
        n = 1
    if n <= 2:
        return '1_2'
    elif n <= 5:
        return '3_5'
    elif n <= 10:
        return '6_10'
    else:
        return 'MAS_10'


def normalizar_clave(texto: str) -> str:
    if not texto:
        return ''
    t = str(texto).strip().upper()
    t = t.replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')
    return t


def calcular_estimacion(id_empresa: int, requisitos: dict) -> dict:
    """
    Ejecuta el algoritmo de estimación determinístico:
      Costo Base = Superficie (m²) × Costo referencial por m²
      Estimación = Costo Base × Factor Niveles × Factor Terreno × Factor Complejidad
    """
    if not requisitos:
        raise ValueError("Los requisitos básicos son obligatorios para la estimación.")

    # 1. Validar y normalizar inputs
    try:
        superficie_m2 = float(requisitos.get('superficie_m2') or 0)
        if superficie_m2 <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("La superficie aproximada debe ser un número positivo mayor a 0 m².")

    try:
        niveles = int(requisitos.get('niveles') or 1)
        if niveles <= 0:
            niveles = 1
    except (ValueError, TypeError):
        niveles = 1

    tipo_obra_in = requisitos.get('tipo_obra') or 'Vivienda'
    tipo_terreno_in = requisitos.get('tipo_terreno') or 'Firme'
    complejidad_in = requisitos.get('complejidad') or 'Bajo'
    ubicacion = requisitos.get('ubicacion') or ''
    caracteristicas = requisitos.get('caracteristicas_generales') or ''
    moneda = requisitos.get('moneda') or 'BOB'

    # Normalización de claves
    norm_tipo = normalizar_clave(tipo_obra_in)
    norm_terreno = normalizar_clave(tipo_terreno_in)
    norm_complejidad = normalizar_clave(complejidad_in)

    # 2. Obtener parámetros configurables desde la BD
    params = obtener_parametros(id_empresa)

    # Resolver costo m2
    costo_m2_dict = params["costo_m2"]
    matched_costo = None
    for k, v in costo_m2_dict.items():
        if k in norm_tipo or norm_tipo in k:
            matched_costo = v
            break
    if not matched_costo:
        matched_costo = costo_m2_dict.get("OTRO", {"valor": 2500.00, "nombre": "Otro"})

    costo_ref_m2 = matched_costo["valor"]
    tipo_obra_nombre = matched_costo["nombre"]

    # Resolver factor niveles
    clave_niv = resolver_clave_niveles(niveles)
    factor_niveles_obj = params["factor_niveles"].get(clave_niv, {"valor": 1.00, "nombre": f"{niveles} niveles"})
    factor_niv = factor_niveles_obj["valor"]

    # Resolver factor terreno
    terreno_dict = params["factor_terreno"]
    matched_terreno = None
    for k, v in terreno_dict.items():
        if k in norm_terreno or norm_terreno in k:
            matched_terreno = v
            break
    if not matched_terreno:
        matched_terreno = terreno_dict.get("OTRO", {"valor": 1.05, "nombre": "Otro tipo de suelo"})

    factor_terr = matched_terreno["valor"]
    tipo_terreno_nombre = matched_terreno["nombre"]

    # Resolver factor complejidad
    comp_dict = params["factor_complejidad"]
    matched_comp = None
    for k, v in comp_dict.items():
        if k in norm_complejidad or norm_complejidad in k:
            matched_comp = v
            break
    if not matched_comp:
        matched_comp = comp_dict.get("BAJO", {"valor": 1.00, "nombre": "Bajo"})

    factor_comp = matched_comp["valor"]
    complejidad_nombre = matched_comp["nombre"]

    # 3. Cálculo matemático determinístico
    costo_base = round(superficie_m2 * costo_ref_m2, 2)
    monto_estimado = round(costo_base * factor_niv * factor_terr * factor_comp, 2)

    return {
        "tipo_obra": tipo_obra_nombre,
        "codigo_tipo_obra": matched_costo.get("codigo_clave", "OTRO"),
        "superficie_m2": round(superficie_m2, 2),
        "niveles": niveles,
        "clave_niveles": clave_niv,
        "tipo_terreno": tipo_terreno_nombre,
        "codigo_tipo_terreno": matched_terreno.get("codigo_clave", "OTRO"),
        "complejidad": complejidad_nombre,
        "codigo_complejidad": matched_comp.get("codigo_clave", "BAJO"),
        "ubicacion": ubicacion,
        "caracteristicas_generales": caracteristicas,
        "costo_referencial_m2": round(costo_ref_m2, 2),
        "factor_niveles": round(factor_niv, 4),
        "factor_terreno": round(factor_terr, 4),
        "factor_complejidad": round(factor_comp, 4),
        "factor_combinado": round(factor_niv * factor_terr * factor_comp, 4),
        "costo_base": costo_base,
        "monto_estimado": monto_estimado,
        "moneda": moneda
    }


def guardar_estimacion(id_obra: int, calculo: dict, db_conn=None) -> int:
    """
    Inserta el registro de estimación congelada en obras.t_obra_estimacion.
    Puede reutilizar una conexión existente o crear una propia.
    """
    cerrar_al_final = False
    if db_conn is None:
        db = PostgreSQL()
        db.create_connection()
        cerrar_al_final = True
    else:
        db = db_conn

    try:
        query = f"""
            INSERT INTO {Config.SCHEMA}.t_obra_estimacion (
                id_obra, tipo_obra, superficie_m2, niveles, tipo_terreno, complejidad,
                ubicacion, caracteristicas_generales, costo_referencial_m2,
                factor_niveles, factor_terreno, factor_complejidad,
                costo_base, monto_estimado, moneda, fecha_estimacion
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
            ) RETURNING id_estimacion;
        """
        params = (
            id_obra,
            calculo["tipo_obra"],
            calculo["superficie_m2"],
            calculo["niveles"],
            calculo["tipo_terreno"],
            calculo["complejidad"],
            calculo.get("ubicacion") or "",
            calculo.get("caracteristicas_generales") or "",
            calculo["costo_referencial_m2"],
            calculo["factor_niveles"],
            calculo["factor_terreno"],
            calculo["factor_complejidad"],
            calculo["costo_base"],
            calculo["monto_estimado"],
            calculo.get("moneda") or "BOB"
        )
        row = db.execute_query(query, params, fetchone=True, commit=True)
        return row[0] if row else None
    finally:
        if cerrar_al_final:
            db.close_connection()


def obtener_estimacion_obra(id_obra: int) -> dict:
    """
    Recupera la estimación preliminar registrada para una obra.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            SELECT id_estimacion, id_obra, tipo_obra, superficie_m2, niveles,
                   tipo_terreno, complejidad, ubicacion, caracteristicas_generales,
                   costo_referencial_m2, factor_niveles, factor_terreno, factor_complejidad,
                   costo_base, monto_estimado, moneda, fecha_estimacion
            FROM {Config.SCHEMA}.t_obra_estimacion
            WHERE id_obra = %s
            ORDER BY id_estimacion DESC
            LIMIT 1;
        """
        row = db.execute_query(query, (id_obra,), fetchone=True)
        if not row:
            return None

        return {
            "id_estimacion": row[0],
            "id_obra": row[1],
            "tipo_obra": row[2],
            "superficie_m2": float(row[3]),
            "niveles": int(row[4]),
            "tipo_terreno": row[5],
            "complejidad": row[6],
            "ubicacion": row[7],
            "caracteristicas_generales": row[8],
            "costo_referencial_m2": float(row[9]),
            "factor_niveles": float(row[10]),
            "factor_terreno": float(row[11]),
            "factor_complejidad": float(row[12]),
            "costo_base": float(row[13]),
            "monto_estimado": float(row[14]),
            "moneda": row[15],
            "fecha_estimacion": row[16].isoformat() if row[16] else None
        }
    finally:
        db.close_connection()
