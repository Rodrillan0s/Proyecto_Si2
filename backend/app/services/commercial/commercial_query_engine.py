"""
Motor determinista de búsqueda, recomendación por presupuesto/preferencias y comparación
de unidades inmobiliarias (HU147, HU148, HU149 - CU34).
"""
import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from app.services.commercial.contracts import CommercialSearchCriteria
from app.services.commercial.cost_estimation_service import (
    TIPO_CAMBIO_BOB_USD,
    enriquecer_unidad_comercial,
    normalizar_estilo,
)

TWO_DECIMALS = Decimal('0.01')


def _norm(text: str) -> str:
    clean = unicodedata.normalize('NFKD', str(text or '')).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'\s+', ' ', clean.lower()).strip()


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
    Parser determinista local de respaldo y pre-extracción que detecta intención,
    tipo de inmueble, dormitorios, baños, metraje, presupuesto, moneda, códigos de unidad
    y estilo a partir del lenguaje natural del cliente potencial.
    """
    txt = _norm(mensaje)
    raw = str(mensaje or '')

    # 1. Detectar intención primaria
    intencion = 'buscar_unidades'
    if re.search(r'\b(contacta\w*|llamen\w*|llamar\w*|asesor\w*|visita\w*|agendar\w*|whatsapp|mi telefono|mi celular|mi correo|interesad[oa])\b', txt):
        intencion = 'solicitar_contacto'
    elif (ids_unidades_comparar and len(ids_unidades_comparar) >= 2) or re.search(
        r'\b(compar\w*|diferencia\w*|versus|\bvs\b|cual conviene|entre la unidad|lado a lado)\b', txt
    ):
        intencion = 'comparar_unidades'
    elif re.search(r'\b(cuanto cuesta construir|estimar costo|estimacion de costo|costo por m2|estilo minimalista|estilo industrial|estilo lujo|acabado\w* de lujo|remodelar|construir mi plano)\b', txt):
        intencion = 'estimar_costo'
    elif re.search(r'\b(recomiend\w*|sugier\w*|presupuesto|que me alcanza|opciones para mi|segun mi presupuesto|alternativa\w*)\b', txt):
        intencion = 'recomendar_presupuesto'

    # 2. Tipo de unidad
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
    elif re.search(r'\b(lote\w*|terreno\w*|parcela\w*)\b', txt):
        tipo_unidad = 'LOTE'

    # 3. Dormitorios y baños
    dorms = min_dormitorios
    if dorms is None:
        m_dorm = re.search(r'(\d+)\s*(?:dormitorio\w*|habitacion\w*|cuarto\w*|recamara\w*|dorm\w*)', txt)
        if m_dorm:
            dorms = int(m_dorm.group(1))
        elif 'monoambiente' in txt or 'estudio' in txt:
            dorms = 1

    banos = None
    m_bano = re.search(r'(\d+)\s*(?:bano\w*|sanitario\w*)', txt)
    if m_bano:
        banos = int(m_bano.group(1))

    # 4. Superficie (m2)
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

    # 5. Moneda y Presupuesto
    moneda_det = str(moneda or 'BOB').strip().upper()
    if re.search(r'(\busd\b|\bdolar\w*|\$us|\bus\$)', txt):
        moneda_det = 'USD'
    elif re.search(r'(\bbob\b|\bboliviano\w*|\bbs\b)', txt):
        moneda_det = 'BOB'

    pres_det = presupuesto_max
    if pres_det is None:
        # Ej: "90000 usd", "90.000 dólares", "500 mil bs", "85,000 $"
        m_mil = re.search(r'(\d+(?:[.,]\d+)?)\s*mil\s*(?:usd|dolar\w*|bob|bs|boliviano\w*)', txt)
        if m_mil:
            pres_det = float(m_mil.group(1).replace(',', '.')) * 1000.0
        else:
            m_pres = re.search(
                r'(?:presupuesto(?:\s+de|\s+maximo|\s+hasta)?|hasta| dispongo de|tengo|tope de)\s*(?:usd|\$us|bs|bob|\$)?\s*(\d{2,3}(?:[.,]\d{3})+|\d{4,9})(?:\s*(usd|dolar\w*|bs|bob|boliviano\w*|\$us|\$))?',
                txt,
            )
            if not m_pres:
                m_pres = re.search(
                    r'(\d{2,3}(?:[.,]\d{3})+|\d{4,9})\s*(usd|dolar\w*|\$us|bs|bob|boliviano\w*)',
                    txt,
                )
            if m_pres:
                num_str = m_pres.group(1).replace('.', '').replace(',', '')
                try:
                    pres_det = float(num_str)
                    unit_token = (m_pres.group(2) or '').lower()
                    if any(u in unit_token for u in ('usd', 'dolar', '$')):
                        moneda_det = 'USD'
                    elif any(u in unit_token for u in ('bs', 'bob', 'boliviano')):
                        moneda_det = 'BOB'
                except ValueError:
                    pass

    # 6. Estilo y estado constructivo
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

    # 7. Zona y características deseadas
    zona = None
    m_zona = re.search(r'\b(?:zona|barrio|sector|distrito)\s+([a-z0-9\s]{3,25}?)(?:\b(?:con|de|para|por|que|y|o|entre|hasta)\b|$|[.,;])', txt)
    if m_zona:
        zona = m_zona.group(1).strip()
    else:
        for z_cand in ('norte', 'sur', 'este', 'oeste', 'centro', 'equipetrol', 'urubo', 'calacoto', 'sopocachi', 'achumani', 'miraflores', ' Cala Cala'.lower()):
            if re.search(r'\b' + re.escape(z_cand.strip()) + r'\b', txt):
                zona = z_cand.strip()
                break

    car_deseadas = []
    for kw in ('balcon', 'terraza', 'parqueo', 'garaje', 'jardin', 'patio', 'suite', 'vestidor', 'vista', 'ascensor', 'piscina', 'churrasquera', 'baulera'):
        if re.search(r'\b' + kw + r'\b', txt):
            car_deseadas.append(kw)

    # 8. Códigos de unidad explícitos (ej. UNI-000001, A-101, etc.)
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
        caracteristicas_deseadas=car_deseadas,
        codigos_comparar=codigos,
        ids_unidades_comparar=list(ids_unidades_comparar or []),
        solo_disponibles=True,
    )


def combinar_criterios(base: CommercialSearchCriteria, llm_dict: dict | None) -> CommercialSearchCriteria:
    """Combina de forma segura los criterios extraídos por DeepSeek JSON mode con los criterios locales."""
    if not llm_dict or not isinstance(llm_dict, dict):
        return base
    merged = base.model_dump()
    for field in (
        'intencion',
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
    ):
        val = llm_dict.get(field)
        if val is not None and val != '' and merged.get(field) is None:
            merged[field] = val
    if llm_dict.get('intencion') in (
        'buscar_unidades',
        'recomendar_presupuesto',
        'comparar_unidades',
        'estimar_costo',
        'solicitar_contacto',
    ) and base.intencion == 'buscar_unidades':
        merged['intencion'] = llm_dict['intencion']

    extra_car = llm_dict.get('caracteristicas_deseadas')
    if isinstance(extra_car, list):
        existing = set(merged.get('caracteristicas_deseadas') or [])
        for c in extra_car:
            if isinstance(c, str) and c.strip():
                existing.add(_norm(c))
        merged['caracteristicas_deseadas'] = sorted(existing)

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
    Enriquece el catálogo de la empresa con precios deterministas y ejecuta
    el motor multicriterio de filtrado y recomendación (HU147 y HU148).
    """
    unidades_enriquecidas = [
        enriquecer_unidad_comercial(u, datos_parametros) for u in (unidades_raw or [])
    ]

    presupuesto_bob = None
    if criterios.presupuesto_max is not None and criterios.presupuesto_max > 0:
        p_dec = Decimal(str(criterios.presupuesto_max))
        if str(criterios.moneda or 'BOB').upper() == 'USD':
            presupuesto_bob = (p_dec * TIPO_CAMBIO_BOB_USD).quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)
        else:
            presupuesto_bob = p_dec.quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)

    evaluadas = []
    coincidencias_exactas = 0

    for u in unidades_enriquecidas:
        score = 0
        razones = []
        alertas = []
        cumple_estricto = True

        # 1. Disponibilidad comercial (0-15 pts)
        disp = u.get('disponibilidad_comercial')
        if disp == 'DISPONIBLE':
            score += 15
            razones.append('Disponibilidad comercial inmediata')
        elif disp == 'RESERVADA':
            score += 5
            alertas.append('Actualmente con reserva temporal (admite lista de espera)')
            if criterios.solo_disponibles:
                cumple_estricto = False
        else:
            cumple_estricto = False
            continue  # Excluir unidades ya vendidas/entregadas o suspendidas de recomendaciones nuevas

        # 2. Tipo de unidad (0-20 pts)
        if criterios.tipo_unidad:
            if u.get('tipo_unidad') == criterios.tipo_unidad.upper():
                score += 20
                razones.append(f"Tipología solicitada ({u['tipo_unidad']})")
            else:
                cumple_estricto = False
        else:
            score += 12

        # 3. Presupuesto (0-35 pts)
        u_precio_bob = Decimal(str(u['precio_bob']))
        if presupuesto_bob is not None and presupuesto_bob > 0:
            if u_precio_bob <= presupuesto_bob:
                ahorro_bob = (presupuesto_bob - u_precio_bob).quantize(TWO_DECIMALS)
                ahorro_pct = int(((presupuesto_bob - u_precio_bob) / presupuesto_bob) * 100)
                score += 35
                razones.append(
                    f"Dentro de tu presupuesto ({u['precio_bob']} BOB / {u['precio_usd']} USD; ahorro del {ahorro_pct}%)"
                )
            elif u_precio_bob <= (presupuesto_bob * Decimal('1.12')):
                exceso_pct = round(float(((u_precio_bob - presupuesto_bob) / presupuesto_bob) * 100), 1)
                score += 20
                alertas.append(f"Supera tu presupuesto objetivo en {exceso_pct}% (opción de preventa/negociación)")
                cumple_estricto = False
            else:
                cumple_estricto = False
        else:
            score += 20

        # 4. Dormitorios y baños (0-15 pts)
        if criterios.min_dormitorios is not None:
            if u['dormitorios'] >= criterios.min_dormitorios:
                score += 15
                razones.append(f"Cumple con {u['dormitorios']} dormitorio(s)")
            elif u['dormitorios'] == 0 and u.get('tipo_unidad') in ('DEPARTAMENTO', 'VIVIENDA'):
                # Unidad sin desglose de ambientes aún cargado pero con superficie compatible
                sup_necesaria = Decimal(str(criterios.min_dormitorios * 24))
                if Decimal(str(u['superficie_m2'])) >= sup_necesaria:
                    score += 10
                    razones.append(f"Superficie de {u['superficie_m2']} m² apta para {criterios.min_dormitorios} dormitorios")
                else:
                    cumple_estricto = False
            else:
                cumple_estricto = False
        else:
            score += 10

        if criterios.min_banos is not None and u['banos'] > 0 and u['banos'] < criterios.min_banos:
            cumple_estricto = False

        # 5. Superficie (0-10 pts)
        sup_u = float(u['superficie_m2_num'])
        if criterios.superficie_min_m2 is not None or criterios.superficie_max_m2 is not None:
            min_s = criterios.superficie_min_m2 or 0.0
            max_s = criterios.superficie_max_m2 or 999999.0
            if min_s <= sup_u <= max_s:
                score += 10
                razones.append(f"Superficie de {u['superficie_m2']} m² dentro del rango buscado")
            else:
                cumple_estricto = False
        else:
            score += 7

        # 6. Zona / Obra / Características (0-15 pts)
        texto_ubicacion = _norm(
            f"{u.get('nombre_obra') or ''} {u.get('ubicacion') or ''} {u.get('zona') or ''} {u.get('distrito') or ''}"
        )
        if criterios.zona:
            if _norm(criterios.zona) in texto_ubicacion:
                score += 10
                razones.append(f"Ubicación coincidente ({u.get('zona') or u.get('ubicacion') or u.get('nombre_obra')})")
            else:
                cumple_estricto = False

        if criterios.nombre_obra and _norm(criterios.nombre_obra) in _norm(u.get('nombre_obra') or ''):
            score += 8
            razones.append(f"Pertenece al proyecto {u.get('nombre_obra')}")

        if criterios.estado_construccion:
            if u.get('estado_construccion') == criterios.estado_construccion:
                score += 8
                razones.append(f"Etapa constructiva: {u['estado_construccion']}")
            else:
                cumple_estricto = False

        if criterios.caracteristicas_deseadas:
            texto_car = _norm(
                f"{u.get('ambientes_resumen') or ''} "
                + ' '.join(f"{c.get('nombre')} {c.get('valor')}" for c in (u.get('caracteristicas') or []))
                + f" {u.get('descripcion_unidad') or ''}"
            )
            matched_cars = [c for c in criterios.caracteristicas_deseadas if _norm(c) in texto_car]
            if matched_cars:
                score += min(10, len(matched_cars) * 5)
                razones.append(f"Incluye: {', '.join(matched_cars)}")

        if cumple_estricto:
            coincidencias_exactas += 1

        item_out = dict(u)
        item_out['afinidad_score'] = min(100, score)
        item_out['cumple_criterios_estrictos'] = cumple_estricto
        item_out['razones_recomendacion'] = razones or [
            f"Opción disponible en {u.get('nombre_obra')} ({u['superficie_m2']} m²)"
        ]
        item_out['observaciones_criterio'] = alertas
        evaluadas.append(item_out)

    # Ordenar primero las que cumplen criterios estrictos, luego por mayor score y mejor precio
    evaluadas.sort(
        key=lambda x: (
            1 if x['cumple_criterios_estrictos'] else 0,
            x['afinidad_score'],
            -float(x['precio_bob_num']),
        ),
        reverse=True,
    )

    seleccionadas = evaluadas[:top_k]
    return {
        'total_inventario_empresa': len(unidades_enriquecidas),
        'total_disponibles_evaluadas': len(evaluadas),
        'coincidencias_exactas': coincidencias_exactas,
        'presupuesto_evaluado_bob': str(presupuesto_bob) if presupuesto_bob is not None else None,
        'presupuesto_evaluado_usd': (
            str((presupuesto_bob / TIPO_CAMBIO_BOB_USD).quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP))
            if presupuesto_bob is not None
            else None
        ),
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
    características, superficie, precios (BOB/USD), costo por m², etapa y disponibilidad.
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
        for cand in (candidatas_fallback or unidades_enriquecidas or []):
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

    # Identificar líderes objetivos en cada métrica
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
        if u.get('estado_construccion') == 'FINALIZADO':
            ventajas.append('Obra finalizada para entrega inmediata')
        elif u.get('estado_construccion') == 'PLANIFICADO':
            ventajas.append('Etapa en planos/preventa con alta plusvalía proyectada')
        if u.get('especificacion_acabado') == 'LUJO':
            ventajas.append('Especificación de acabados de lujo de fábrica')

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
            'ventajas_competitivas': ventajas or ['Distribución equilibrada y respaldo constructivo'],
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

