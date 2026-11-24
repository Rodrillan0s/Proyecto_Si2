"""
Motor determinista de búsqueda, recomendación por presupuesto/preferencias y comparación
de unidades inmobiliarias (HU147, HU148, HU149 - CU34).

Reglas innegociables:
1. Los filtros obligatorios (disponibilidad, tipología, presupuesto máximo y requisitos
   indispensables confirmados) se aplican ANTES de calcular afinidad.
2. Ninguna puntuación de afinidad puede compensar el incumplimiento de una restricción obligatoria.
3. Si ninguna unidad supera los filtros obligatorios, devuelve 0 recomendaciones válidas
   con motivos explícitos de exclusión.
"""
import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from app.services.commercial.contracts import CommercialSearchCriteria
from app.services.commercial.cost_estimation_service import (
    TIPO_CAMBIO_BOB_USD,
    enriquecer_unidad_comercial,
    estimar_mobiliario_separado,
    fecha_referencia_tc,
    normalizar_estilo,
)

TWO_DECIMALS = Decimal('0.01')

TIPOLOGIA_GRUPOS = {
    'VIVIENDA': {'VIVIENDA', 'CASA', 'DUPLEX', 'TOWNHOUSE', 'CHALET'},
    'CASA': {'VIVIENDA', 'CASA', 'DUPLEX', 'TOWNHOUSE', 'CHALET'},
    'DEPARTAMENTO': {'DEPARTAMENTO', 'PENTHOUSE', 'FLAT', 'DUPLEX'},
    'OFICINA': {'OFICINA', 'CONSULTORIO'},
    'LOCAL': {'LOCAL', 'COMERCIAL', 'TIENDA'},
    'LOTE': {'LOTE', 'TERRENO', 'PARCELA'},
}


def _norm(text: str) -> str:
    clean = unicodedata.normalize('NFKD', str(text or '')).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'\s+', ' ', clean.lower()).strip()


def _tipologia_compatible(solicitada: str | None, unidad_tipo: str | None) -> bool:
    if not solicitada:
        return True
    req = str(solicitada).strip().upper()
    actual = str(unidad_tipo or '').strip().upper()
    if not actual:
        return False
    permitidos = TIPOLOGIA_GRUPOS.get(req, {req})
    return actual in permitidos


def extraer_criterios_locales(
    mensaje: str,
    presupuesto_max: float | None = None,
    moneda: str = 'BOB',
    tipo_unidad_preferido: str | None = None,
    estilo_preferido: str | None = None,
    min_dormitorios: int | None = None,
    ids_unidades_comparar: list[int] | None = None,
) -> CommercialSearchCriteria:
    """
    Parser determinista de respaldo (usado cuando DeepSeek no está disponible o para
    incorporar parámetros explícitos enviados por formulario).
    """
    txt = _norm(mensaje)
    raw = str(mensaje or '')

    intencion = 'buscar_unidades'
    if re.search(r'\b(contacta\w*|llamen\w*|llamar\w*|asesor\w*|visita\w*|agendar\w*|whatsapp|mi telefono|mi celular|mi correo)\b', txt):
        intencion = 'solicitar_contacto'
    elif (ids_unidades_comparar and len(ids_unidades_comparar) >= 2) or re.search(
        r'\b(compar\w*|diferencia\w*|versus|\bvs\b|cual conviene|lado a lado)\b', txt,
    ):
        intencion = 'comparar_unidades'
    elif re.search(r'\b(construir|proyecto personalizado|edificar|construy\w*|tengo terreno|sin terreno|disenar una casa|hacer una casa)\b', txt):
        intencion = 'proponer_proyecto'
    elif re.search(r'\b(cuanto cuesta|estimar costo|estimacion de costo|costo por m2|estilo minimalista|estilo industrial|estilo lujo|remodelar)\b', txt):
        intencion = 'estimar_costo'
    elif re.search(r'\b(recomiend\w*|sugier\w*|presupuesto|que me alcanza|opciones|alternativa\w*)\b', txt):
        intencion = 'recomendar_presupuesto'

    tipo_unidad = None
    if tipo_unidad_preferido:
        tipo_unidad = str(tipo_unidad_preferido).strip().upper()
    elif re.search(r'\b(departamento\w*|depto\w*|dpto\w*|apartamento\w*|flat)\b', txt):
        tipo_unidad = 'DEPARTAMENTO'
    elif re.search(r'\b(casa\w*|vivienda\w*|chalet|duplex|townhouse)\b', txt):
        tipo_unidad = 'VIVIENDA'
    elif re.search(r'\b(oficina\w*|consultorio\w*|despacho)\b', txt):
        tipo_unidad = 'OFICINA'
    elif re.search(r'\b(local\w*|comercial\w*|tienda\w*)\b', txt):
        tipo_unidad = 'LOCAL'
    elif re.search(r'\b(lote\w*|parcela\w*)\b', txt) and intencion != 'proponer_proyecto':
        tipo_unidad = 'LOTE'

    dorms = min_dormitorios
    if dorms is None:
        m_dorm = re.search(r'(\d+)\s*(?:dormitorio\w*|habitacion\w*|cuarto\w*|recamara\w*|dorm\w*)', txt)
        if m_dorm:
            dorms = int(m_dorm.group(1))
        else:
            word_nums = {'una': 1, 'un': 1, 'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5}
            m_word = re.search(r'\b(un|una|dos|tres|cuatro|cinco)\s+(?:dormitorio\w*|habitacion\w*|cuarto\w*)', txt)
            if m_word:
                dorms = word_nums.get(m_word.group(1))
            elif 'monoambiente' in txt or 'estudio' in txt:
                dorms = 1

    banos = None
    m_bano = re.search(r'(\d+)\s*(?:bano\w*|sanitario\w*)', txt)
    if m_bano:
        banos = int(m_bano.group(1))

    sup_min = None
    sup_max = None
    m_rango_sup = re.search(r'entre\s+(\d+(?:[.,]\d+)?)\s*(?:y|a|-)\s*(\d+(?:[.,]\d+)?)\s*(?:m2|metros|mt2)', txt)
    if m_rango_sup:
        sup_min = float(m_rango_sup.group(1).replace(',', '.'))
        sup_max = float(m_rango_sup.group(2).replace(',', '.'))
    else:
        m_sup = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:m2|metros cuadrados|mt2)', txt)
        if m_sup:
            val_sup = float(m_sup.group(1).replace(',', '.'))
            if re.search(r'(menos de|maximo|hasta)\s+' + re.escape(m_sup.group(1)), txt):
                sup_max = val_sup
            elif re.search(r'(mas de|minimo|desde|al menos)\s+' + re.escape(m_sup.group(1)), txt):
                sup_min = val_sup
            else:
                sup_min = round(val_sup * 0.85, 2)
                sup_max = round(val_sup * 1.20, 2)

    moneda_det = str(moneda or 'BOB').strip().upper()
    if re.search(r'(\busd\b|\bdolar\w*|\$us|\bus\$)', txt):
        moneda_det = 'USD'
    elif re.search(r'(\bbob\b|\bboliviano\w*|\bbs\b)', txt):
        moneda_det = 'BOB'

    pres_det = presupuesto_max
    if pres_det is None:
        m_mil = re.search(r'(\d+(?:[.,]\d+)?)\s*mil\s*(?:usd|dolar\w*|bob|bs|boliviano\w*)', txt)
        if m_mil:
            pres_det = float(m_mil.group(1).replace(',', '.')) * 1000.0
        else:
            m_pres = re.search(
                r'(?:presupuesto(?:\s+de|\s+maximo|\s+hasta|\s+a)?|hasta|dispongo de|tengo|tope de|aumento\w*(?:\s+mi\s+presupuesto)?\s+a|subo\s+a)\s*(?:usd|\$us|bs|bob|\$)?\s*(\d{2,3}(?:[.,]\d{3})+|\d{4,9})(?:\s*(usd|dolar\w*|bs|bob|boliviano\w*|\$us|\$))?',
                txt,
            )
            if not m_pres:
                m_pres = re.search(
                    r'(?:usd|\$us)\s*(\d{2,3}(?:[.,]\d{3})+|\d{4,9})',
                    txt,
                )
                if m_pres:
                    moneda_det = 'USD'
            if not m_pres:
                m_pres = re.search(
                    r'(\d{2,3}(?:[.,]\d{3})+|\d{4,9})\s*(usd|dolar\w*|\$us|bs|bob|boliviano\w*)',
                    txt,
                )
            if m_pres:
                num_str = m_pres.group(1).replace('.', '').replace(',', '')
                try:
                    pres_det = float(num_str)
                    if m_pres.lastindex and m_pres.lastindex >= 2 and m_pres.group(2):
                        unit_token = m_pres.group(2).lower()
                        if any(u in unit_token for u in ('usd', 'dolar', '$')):
                            moneda_det = 'USD'
                        elif any(u in unit_token for u in ('bs', 'bob', 'boliviano')):
                            moneda_det = 'BOB'
                except ValueError:
                    pass

    estilo = None
    if estilo_preferido:
        estilo = normalizar_estilo(estilo_preferido)
    elif 'minimalista' in txt or 'moderno' in txt:
        estilo = 'MINIMALISTA'
    elif 'industrial' in txt or 'loft' in txt:
        estilo = 'INDUSTRIAL'
    elif 'contemporaneo' in txt or 'calido' in txt:
        estilo = 'CONTEMPORANEO'
    elif 'lujo' in txt or 'premium' in txt or 'alta gama' in txt:
        estilo = 'LUJO'
    elif 'estandar' in txt or 'tradicional' in txt or 'economico' in txt:
        estilo = 'ESTANDAR'

    estado_const = None
    if re.search(r'\b(entrega inmediata|terminad[oa]|finalizad[oa]|list[oa] para habitar)\b', txt):
        estado_const = 'FINALIZADO'
    elif re.search(r'\b(en construccion|en obra|ejecucion)\b', txt):
        estado_const = 'EN_CONSTRUCCION'
    elif re.search(r'\b(preventa|en plano\w*|en pozo|planificad[oa])\b', txt):
        estado_const = 'PLANIFICADO'

    # Amoblamiento y cotización de mobiliario por separado
    amob_pref = None
    amob_indisp = False
    acepta_cotizar_mob = bool(re.search(r'\b(cotizar\s+(?:el\s+)?mobiliario|mobiliario\s+por\s+separado|amoblar\w*\s+aparte|sin\s+problema\s+cotizar\s+muebles|acepto\s+cotizar)\b', txt))
    if re.search(r'\b(sin amoblar|no amoblad[oa]|vaci[oa])\b', txt):
        amob_pref = 'SIN_AMOBLAR'
    elif re.search(r'\b(parcialmente amoblad[oa]|semi\s*amoblad[oa])\b', txt):
        amob_pref = 'PARCIALMENTE_AMOBLADA'
    elif re.search(r'\b(amoblad[oa]|con muebles|bien amoblad[oa]|equipada con muebles)\b', txt):
        amob_pref = 'AMOBLADA'
        if re.search(r'\b(indispensable|obligatori[oa]|solo amoblad[oa]|si o si amoblad[oa]|imprescindible)\b', txt):
            amob_indisp = True

    # Terreno propio para propuestas de construcción
    tiene_terreno = None
    if re.search(r'\b(no tengo terreno|sin terreno|necesito terreno|no cuento con terreno|no dispongo de terreno)\b', txt):
        tiene_terreno = False
    elif re.search(r'\b(tengo terreno|cuento con terreno|dispongo de terreno|terreno propio|en mi terreno|en mi lote)\b', txt):
        tiene_terreno = True

    zona = None
    m_zona = re.search(r'\b(?:zona|barrio|sector|distrito)\s+([a-z0-9\s]{3,25}?)(?:\b(?:con|de|para|por|que|y|o|entre|hasta)\b|$|[.,;])', txt)
    if m_zona:
        zona = m_zona.group(1).strip()
    else:
        for z_cand in ('norte', 'sur', 'este', 'oeste', 'centro', 'equipetrol', 'urubo', 'calacoto', 'sopocachi', 'achumani', 'miraflores', 'cala cala', 'tranquila'):
            if re.search(r'\b' + re.escape(z_cand) + r'\b', txt):
                zona = z_cand
                break

    car_deseadas = []
    for kw in ('balcon', 'terraza', 'parqueo', 'garaje', 'jardin', 'patio', 'suite', 'vestidor', 'vista', 'ascensor', 'piscina', 'churrasquera', 'baulera'):
        if re.search(r'\b' + kw + r'\b', txt):
            car_deseadas.append(kw)

    codigos = [m.upper() for m in re.findall(r'\b(?:UNI-\d{1,6}|[A-Z]{1,4}-\d{2,4})\b', raw, flags=re.IGNORECASE)]

    return CommercialSearchCriteria(
        intencion=intencion,
        tipo_unidad=tipo_unidad,
        min_dormitorios=dorms,
        min_banos=banos,
        superficie_min_m2=sup_min,
        superficie_max_m2=sup_max,
        presupuesto_max=pres_det,
        moneda=moneda_det,
        zona=zona,
        estilo_acabado=estilo,
        estado_construccion=estado_const,
        amoblamiento_preferido=amob_pref,
        amoblamiento_indispensable=amob_indisp,
        acepta_cotizar_mobiliario=acepta_cotizar_mob,
        tiene_terreno=tiene_terreno,
        caracteristicas_deseadas=car_deseadas,
        codigos_comparar=codigos,
        ids_unidades_comparar=list(ids_unidades_comparar or []),
        solo_disponibles=True,
    )


def combinar_criterios(
    base: CommercialSearchCriteria,
    llm_dict: dict | None,
    explicit_overrides: dict | None = None,
) -> CommercialSearchCriteria:
    """
    Combina la extracción semántica de DeepSeek (fuente primaria) con el respaldo local
    y los campos explícitos del formulario. DeepSeek prevalece sobre las heurísticas regex
    cuando devuelve valores estructurados válidos.
    """
    if not llm_dict or not isinstance(llm_dict, dict):
        return base

    merged = base.model_dump()
    overrides = explicit_overrides or {}

    valid_intentions = {
        'buscar_unidades',
        'recomendar_presupuesto',
        'comparar_unidades',
        'estimar_costo',
        'proponer_proyecto',
        'solicitar_contacto',
        'consulta_general',
    }
    if llm_dict.get('intencion') in valid_intentions:
        merged['intencion'] = llm_dict['intencion']

    for field in (
        'tipo_unidad',
        'min_dormitorios',
        'min_banos',
        'superficie_min_m2',
        'superficie_max_m2',
        'presupuesto_max',
        'moneda',
        'zona',
        'nombre_obra',
        'estilo_acabado',
        'estado_construccion',
        'amoblamiento_preferido',
        'superficie_terreno_m2',
        'plazo_deseado_meses',
        'pregunta_aclaracion',
    ):
        val = llm_dict.get(field)
        if val is not None and val != '' and overrides.get(field) is None:
            merged[field] = val

    for bfield in ('amoblamiento_indispensable', 'acepta_cotizar_mobiliario', 'necesita_aclaracion'):
        if isinstance(llm_dict.get(bfield), bool):
            merged[bfield] = llm_dict[bfield] or bool(merged.get(bfield))

    if isinstance(llm_dict.get('tiene_terreno'), bool):
        merged['tiene_terreno'] = llm_dict['tiene_terreno']

    for lfield in ('caracteristicas_deseadas', 'restricciones_indispensables'):
        extra = llm_dict.get(lfield)
        if isinstance(extra, list):
            existing = set(merged.get(lfield) or [])
            for item in extra:
                if isinstance(item, str) and item.strip():
                    existing.add(_norm(item))
            merged[lfield] = sorted(existing)

    try:
        return CommercialSearchCriteria(**merged)
    except Exception:
        return base


def filtrar_y_recomendar_unidades(
    unidades_raw: list[dict],
    datos_parametros: dict,
    criterios: CommercialSearchCriteria,
    top_k: int = 6,
) -> dict:
    """
    Motor comercial en dos fases estrictas:
    - Fase 1 (Restricciones obligatorias): filtra disponibilidad, tipología, presupuesto máximo
      y requisitos indispensables confirmados. Las descartadas JAMÁS entran a recomendaciones.
    - Fase 2 (Afinidad verificable): puntúa únicamente unidades elegibles sobre criterios
      activos y verificables, penalizando datos desconocidos relevantes.
    """
    unidades_enriquecidas = [
        enriquecer_unidad_comercial(u, datos_parametros) for u in (unidades_raw or [])
    ]
    parametros = (datos_parametros or {}).get('parametros') or {}

    presupuesto_bob = None
    if criterios.presupuesto_max is not None and criterios.presupuesto_max > 0:
        p_dec = Decimal(str(criterios.presupuesto_max))
        if str(criterios.moneda or 'BOB').upper() == 'USD':
            presupuesto_bob = (p_dec * TIPO_CAMBIO_BOB_USD).quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)
        else:
            presupuesto_bob = p_dec.quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)

    motivos_exclusion = {
        'no_disponible_o_reservada': 0,
        'tipologia_incompatible': 0,
        'fuera_de_presupuesto': 0,
        'amoblamiento_incompatible': 0,
        'requisito_indispensable_incumplido': 0,
    }
    indispensables = {_norm(r) for r in (criterios.restricciones_indispensables or [])}

    # --- FASE 1: RESTRICCIONES OBLIGATORIAS ---
    elegibles = []
    for u in unidades_enriquecidas:
        disp = str(u.get('disponibilidad_comercial') or '').upper()
        publicado = u.get('publicado_comercial', True)

        if criterios.solo_disponibles:
            if disp != 'DISPONIBLE' or publicado is False:
                motivos_exclusion['no_disponible_o_reservada'] += 1
                continue
        else:
            if disp in ('VENDIDA', 'NO_DISPONIBLE'):
                motivos_exclusion['no_disponible_o_reservada'] += 1
                continue

        if criterios.tipo_unidad and not _tipologia_compatible(criterios.tipo_unidad, u.get('tipo_unidad')):
            motivos_exclusion['tipologia_incompatible'] += 1
            continue

        u_precio_bob = Decimal(str(u['precio_bob']))
        if presupuesto_bob is not None and presupuesto_bob > 0 and u_precio_bob > presupuesto_bob:
            motivos_exclusion['fuera_de_presupuesto'] += 1
            continue

        amob_u = str(u.get('estado_amoblamiento') or 'DESCONOCIDO').upper()
        if (
            criterios.amoblamiento_indispensable
            and criterios.amoblamiento_preferido
            and not criterios.acepta_cotizar_mobiliario
        ):
            if criterios.amoblamiento_preferido == 'AMOBLADA' and amob_u != 'AMOBLADA':
                motivos_exclusion['amoblamiento_incompatible'] += 1
                continue
            if criterios.amoblamiento_preferido == 'SIN_AMOBLAR' and amob_u != 'SIN_AMOBLAR':
                motivos_exclusion['amoblamiento_incompatible'] += 1
                continue

        if 'dormitorios' in indispensables and criterios.min_dormitorios is not None:
            if int(u.get('dormitorios') or 0) < criterios.min_dormitorios:
                motivos_exclusion['requisito_indispensable_incumplido'] += 1
                continue

        if 'banos' in indispensables and criterios.min_banos is not None:
            if int(u.get('banos') or 0) < criterios.min_banos:
                motivos_exclusion['requisito_indispensable_incumplido'] += 1
                continue

        if 'zona' in indispensables and criterios.zona:
            loc = _norm(f"{u.get('nombre_obra') or ''} {u.get('ubicacion') or ''} {u.get('zona') or ''} {u.get('distrito') or ''}")
            if _norm(criterios.zona) not in loc:
                motivos_exclusion['requisito_indispensable_incumplido'] += 1
                continue

        elegibles.append(u)

    # --- FASE 2: MOTOR DE AFINIDAD VERIFICABLE (SOLO SOBRE ELEGIBLES) ---
    evaluadas = []
    for u in elegibles:
        puntos_obtenidos = 0.0
        puntos_posibles = 0.0
        razones = []
        alertas = []

        # Disponibilidad confirmada (base verificable)
        puntos_posibles += 15.0
        if u.get('disponibilidad_comercial') == 'DISPONIBLE':
            puntos_obtenidos += 15.0
            razones.append('Disponible para comercialización inmediata')
        else:
            puntos_obtenidos += 5.0
            alertas.append(f"Estado comercial: {u.get('disponibilidad_comercial')}")

        # Transparencia de precio (publicado vs estimación)
        if u.get('es_estimacion_precio'):
            alertas.append(
                f"Precio estimado paramétricamente (no publicado; TC {u['tipo_cambio_referencia']} al {u['fecha_referencia_tc']})."
            )
        else:
            razones.append(f"Precio publicado confirmado ({u['precio_usd']} USD / {u['precio_bob']} BOB)")

        # Presupuesto
        if presupuesto_bob is not None and presupuesto_bob > 0:
            puntos_posibles += 25.0
            u_precio_bob = Decimal(str(u['precio_bob']))
            ahorro_pct = int(((presupuesto_bob - u_precio_bob) / presupuesto_bob) * 100)
            puntos_obtenidos += 25.0
            razones.append(
                f"Dentro del presupuesto máximo ({u['precio_usd']} USD; margen disponible {ahorro_pct}%)"
            )

        # Tipología
        if criterios.tipo_unidad:
            puntos_posibles += 15.0
            puntos_obtenidos += 15.0
            razones.append(f"Tipología compatible ({u['tipo_unidad']})")

        # Amoblamiento (preferencia puntuable + penalización por dato desconocido)
        amob_u = str(u.get('estado_amoblamiento') or 'DESCONOCIDO').upper()
        cotizacion_mobiliario = None
        if criterios.amoblamiento_preferido:
            puntos_posibles += 20.0
            if amob_u == criterios.amoblamiento_preferido:
                puntos_obtenidos += 20.0
                razones.append(f"Estado de amoblamiento verificado: {amob_u}")
            elif criterios.amoblamiento_preferido == 'AMOBLADA' and amob_u == 'PARCIALMENTE_AMOBLADA':
                puntos_obtenidos += 12.0
                alertas.append('Parcialmente amoblada; puede cotizarse equipamiento complementario por separado.')
            elif amob_u == 'DESCONOCIDO':
                puntos_obtenidos += 4.0  # Penalización explícita por información desconocida
                alertas.append(
                    'Mobiliario no registrado (DESCONOCIDO). No se asume amoblada; puedes cotizar mobiliario por separado.'
                )
            else:
                puntos_obtenidos += 2.0
                alertas.append(
                    f"Unidad registrada como {amob_u} (solicitaste {criterios.amoblamiento_preferido}); se puede cotizar amoblamiento aparte."
                )

            if amob_u in ('SIN_AMOBLAR', 'DESCONOCIDO', 'PARCIALMENTE_AMOBLADA') and (
                criterios.acepta_cotizar_mobiliario or u.get('costo_mobiliario_bob')
            ):
                if u.get('costo_mobiliario_bob'):
                    mob_bob = Decimal(str(u['costo_mobiliario_bob']))
                    cotizacion_mobiliario = {
                        'disponible': True,
                        'monto_bob': str(mob_bob),
                        'monto_usd': str((mob_bob / TIPO_CAMBIO_BOB_USD).quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)),
                        'tipo_precio': 'COSTO_MOBILIARIO_ADICIONAL',
                        'nota': 'Paquete de mobiliario cotizado por separado del inmueble.',
                    }
                else:
                    cotizacion_mobiliario = estimar_mobiliario_separado(Decimal(str(u['superficie_m2'])), parametros)
                    if cotizacion_mobiliario is None:
                        cotizacion_mobiliario = {
                            'disponible': False,
                            'tipo_precio': 'NO_ESTIMABLE',
                            'nota': 'Sin tarifario de mobiliario cargado en la empresa; requiere cotización de proveedor o asesor.',
                        }
                if cotizacion_mobiliario.get('disponible') and presupuesto_bob is not None:
                    total_con_mob = Decimal(str(u['precio_bob'])) + Decimal(str(cotizacion_mobiliario['monto_bob']))
                    cotizacion_mobiliario['total_inmueble_mas_mobiliario_bob'] = str(total_con_mob.quantize(TWO_DECIMALS))
                    cotizacion_mobiliario['total_inmueble_mas_mobiliario_usd'] = str(
                        (total_con_mob / TIPO_CAMBIO_BOB_USD).quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)
                    )
                    cotizacion_mobiliario['encaja_presupuesto_con_mobiliario'] = total_con_mob <= presupuesto_bob

        # Dormitorios
        if criterios.min_dormitorios is not None:
            puntos_posibles += 15.0
            dorms_u = int(u.get('dormitorios') or 0)
            if dorms_u >= criterios.min_dormitorios:
                puntos_obtenidos += 15.0
                razones.append(f"Cuenta con {dorms_u} dormitorio(s)")
            elif dorms_u == 0:
                puntos_obtenidos += 4.0
                alertas.append('Cantidad de dormitorios no registrada en la ficha de ambientes.')
            else:
                puntos_obtenidos += 3.0
                alertas.append(f"Registra {dorms_u} dormitorio(s) (preferiste {criterios.min_dormitorios}).")

        # Baños
        if criterios.min_banos is not None:
            puntos_posibles += 8.0
            banos_u = int(u.get('banos') or 0)
            if banos_u >= criterios.min_banos:
                puntos_obtenidos += 8.0
                razones.append(f"Cuenta con {banos_u} baño(s)")
            elif banos_u == 0:
                puntos_obtenidos += 2.0
                alertas.append('Cantidad de baños no registrada en la ficha.')

        # Superficie
        sup_u = float(u['superficie_m2_num'])
        if criterios.superficie_min_m2 is not None or criterios.superficie_max_m2 is not None:
            puntos_posibles += 12.0
            min_s = criterios.superficie_min_m2 or 0.0
            max_s = criterios.superficie_max_m2 or 999999.0
            if min_s <= sup_u <= max_s:
                puntos_obtenidos += 12.0
                razones.append(f"Superficie verificada de {u['superficie_m2']} m²")
            else:
                puntos_obtenidos += 3.0
                alertas.append(f"Superficie de {u['superficie_m2']} m² fuera del rango preferido.")

        # Zona
        if criterios.zona:
            puntos_posibles += 12.0
            texto_ubicacion = _norm(
                f"{u.get('nombre_obra') or ''} {u.get('ubicacion') or ''} {u.get('zona') or ''} {u.get('distrito') or ''}"
            )
            if _norm(criterios.zona) in texto_ubicacion:
                puntos_obtenidos += 12.0
                razones.append(f"Ubicación coincidente ({u.get('zona') or u.get('ubicacion') or u.get('nombre_obra')})")
            elif not texto_ubicacion.strip():
                puntos_obtenidos += 3.0
                alertas.append('Ubicación/zona detallada no registrada en el proyecto.')
            else:
                puntos_obtenidos += 2.0
                alertas.append(f"Ubicada en {u.get('zona') or u.get('ubicacion') or u.get('nombre_obra')}.")

        # Estilo / Acabados
        if criterios.estilo_acabado:
            puntos_posibles += 8.0
            if normalizar_estilo(u.get('especificacion_acabado')) == normalizar_estilo(criterios.estilo_acabado):
                puntos_obtenidos += 8.0
                razones.append(f"Acabado compatible ({u.get('especificacion_acabado')})")
            else:
                puntos_obtenidos += 3.0

        # Características adicionales
        if criterios.caracteristicas_deseadas:
            puntos_posibles += 10.0
            texto_car = _norm(
                f"{u.get('ambientes_resumen') or ''} "
                + ' '.join(f"{c.get('nombre')} {c.get('valor')}" for c in (u.get('caracteristicas') or []))
                + f" {u.get('descripcion_unidad') or ''}"
            )
            matched = [c for c in criterios.caracteristicas_deseadas if _norm(c) in texto_car]
            if matched:
                ratio = len(matched) / max(1, len(criterios.caracteristicas_deseadas))
                puntos_obtenidos += 10.0 * ratio
                razones.append(f"Incluye: {', '.join(matched)}")

        afinidad = int(round((puntos_obtenidos / puntos_posibles) * 100)) if puntos_posibles > 0 else 0
        afinidad = max(0, min(100, afinidad))

        item_out = dict(u)
        item_out['afinidad_score'] = afinidad
        item_out['cumple_criterios_estrictos'] = True
        item_out['razones_recomendacion'] = razones
        item_out['observaciones_criterio'] = alertas
        if cotizacion_mobiliario is not None:
            item_out['cotizacion_mobiliario_separada'] = cotizacion_mobiliario
        evaluadas.append(item_out)

    evaluadas.sort(
        key=lambda x: (
            x['afinidad_score'],
            0 if x.get('es_estimacion_precio') else 1,
            -float(x['precio_bob_num']),
        ),
        reverse=True,
    )

    seleccionadas = evaluadas[:top_k]
    return {
        'total_inventario_empresa': len(unidades_enriquecidas),
        'total_disponibles_evaluadas': len(evaluadas),
        'coincidencias_exactas': len(evaluadas),
        'presupuesto_evaluado_bob': str(presupuesto_bob) if presupuesto_bob is not None else None,
        'presupuesto_evaluado_usd': (
            str((presupuesto_bob / TIPO_CAMBIO_BOB_USD).quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP))
            if presupuesto_bob is not None
            else None
        ),
        'tipo_cambio_referencia': str(TIPO_CAMBIO_BOB_USD),
        'fecha_referencia_tc': fecha_referencia_tc(),
        'motivos_exclusion': motivos_exclusion,
        'unidades_recomendadas': seleccionadas,
        'todas_enriquecidas': unidades_enriquecidas,
    }


def comparar_alternativas_inmobiliarias(
    unidades_enriquecidas: list[dict],
    ids_solicitud: list[int] | None = None,
    codigos_solicitud: list[str] | None = None,
    candidatas_fallback: list[dict] | None = None,
) -> dict:
    """
    Construye la matriz comparativa estructurada lado a lado (HU149) evaluando
    características, superficie, precios (BOB/USD), tipo de precio, amoblamiento,
    costo por m², etapa y disponibilidad.
    """
    seleccion = []
    seen_ids = set()

    ids_set = {int(i) for i in (ids_solicitud or []) if i is not None}
    cods_set = {str(c).strip().upper() for c in (codigos_solicitud or []) if c}

    for u in unidades_enriquecidas or []:
        if u['id_unidad'] in ids_set or str(u.get('codigo_unidad') or '').upper() in cods_set:
            if u['id_unidad'] not in seen_ids:
                seleccion.append(u)
                seen_ids.add(u['id_unidad'])

    if len(seleccion) < 2:
        for cand in (candidatas_fallback or []):
            if cand['id_unidad'] not in seen_ids:
                seleccion.append(cand)
                seen_ids.add(cand['id_unidad'])
            if len(seleccion) >= 3:
                break

    seleccion = seleccion[:4]
    if not seleccion:
        return {
            'total_comparadas': 0,
            'unidades': [],
            'resumen_comparativo': {},
        }

    menor_precio = min(seleccion, key=lambda x: float(x['precio_bob_num']))
    mayor_superficie = max(seleccion, key=lambda x: float(x['superficie_m2_num']))
    mejor_costo_m2 = min(seleccion, key=lambda x: float(Decimal(str(x['costo_m2_bob']))))

    comparadas_out = []
    for u in seleccion:
        ventajas = []
        if u['id_unidad'] == menor_precio['id_unidad'] and len(seleccion) > 1:
            ventajas.append('Menor inversión total requerida')
        if u['id_unidad'] == mayor_superficie['id_unidad'] and len(seleccion) > 1:
            ventajas.append(f"Mayor amplitud espacial ({u['superficie_m2']} m²)")
        if u['id_unidad'] == mejor_costo_m2['id_unidad'] and len(seleccion) > 1:
            ventajas.append(f"Mejor relación precio/m² ({u['costo_m2_usd']} USD/m²)")
        if u.get('estado_amoblamiento') == 'AMOBLADA':
            ventajas.append('Unidad amoblada verificada')
        if u.get('estado_construccion') == 'FINALIZADO':
            ventajas.append('Obra finalizada para entrega inmediata')

        comparadas_out.append({
            'id_unidad': u['id_unidad'],
            'codigo_unidad': u['codigo_unidad'],
            'nombre_unidad': u['nombre_unidad'],
            'nombre_obra': u['nombre_obra'],
            'obra': u['nombre_obra'],
            'ubicacion': u.get('ubicacion') or u.get('zona') or 'Ubicación registrada en proyecto',
            'tipo_unidad': u['tipo_unidad'],
            'disponibilidad_comercial': u['disponibilidad_comercial'],
            'estado_construccion': u['estado_construccion'],
            'estado_amoblamiento': u.get('estado_amoblamiento', 'DESCONOCIDO'),
            'superficie_m2': u['superficie_m2'],
            'cantidad_plantas': u['cantidad_plantas'],
            'dormitorios': u['dormitorios'],
            'banos': u['banos'],
            'ambientes_resumen': u['ambientes_resumen'],
            'especificacion_acabado': u['especificacion_acabado'],
            'precio_bob': u['precio_bob'],
            'precio_usd': u['precio_usd'],
            'costo_m2_bob': u['costo_m2_bob'],
            'costo_m2_usd': u['costo_m2_usd'],
            'fuente_precio': u['fuente_precio'],
            'tipo_precio': u.get('tipo_precio', u['fuente_precio']),
            'ventajas_competitivas': ventajas or ['Distribución verificada y respaldo constructivo'],
        })

    return {
        'total_comparadas': len(comparadas_out),
        'unidades': comparadas_out,
        'matriz_comparativa': comparadas_out,
        'resumen_comparativo': {
            'opcion_mas_economica': {
                'id_unidad': menor_precio['id_unidad'],
                'codigo_unidad': menor_precio['codigo_unidad'],
                'nombre_unidad': menor_precio['nombre_unidad'],
                'precio_bob': menor_precio['precio_bob'],
                'precio_usd': menor_precio['precio_usd'],
            },
            'opcion_mas_amplia': {
                'id_unidad': mayor_superficie['id_unidad'],
                'codigo_unidad': mayor_superficie['codigo_unidad'],
                'nombre_unidad': mayor_superficie['nombre_unidad'],
                'superficie_m2': mayor_superficie['superficie_m2'],
            },
            'mejor_relacion_m2': {
                'id_unidad': mejor_costo_m2['id_unidad'],
                'codigo_unidad': mejor_costo_m2['codigo_unidad'],
                'nombre_unidad': mejor_costo_m2['nombre_unidad'],
                'costo_m2_bob': mejor_costo_m2['costo_m2_bob'],
                'costo_m2_usd': mejor_costo_m2['costo_m2_usd'],
            },
        },
    }
