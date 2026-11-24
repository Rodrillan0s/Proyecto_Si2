"""
Motor de propuestas de proyectos de construcción personalizados (OBRATEC IA Comercial).

Se activa cuando ninguna unidad del inventario cumple las restricciones del cliente o cuando
el cliente solicita explícitamente construir un proyecto propio.

Reglas estrictas:
- Reutiliza cost_estimation_service.py y los datos reales de t_parametro_estimacion,
  t_analisis_precio_unitario y t_material.
- Nunca inventa precios unitarios, rendimientos ni tiempos de ejecución si faltan datos.
- Diferencia explícitamente adquisición de terreno vs. costo de construcción.
- Genera hasta 3 escenarios (Económico, Equilibrado, Superior) cuando existen datos suficientes.
- Recopila información faltante de forma progresiva (máximo 2 preguntas por turno).
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from app.services.commercial.contracts import CommercialSearchCriteria
from app.services.commercial import cost_estimation_service as cost_service

TWO_DECIMALS = Decimal('0.01')


def _q2(val: Decimal) -> Decimal:
    return val.quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)


def _hay_base_economica_verificable(datos_parametros: dict | None) -> tuple[bool, list[str]]:
    """
    Comprueba si la empresa dispone de parámetros de costo, APUs o materiales con precio
    para fundamentar una propuesta preliminar sin inventar tarifas.
    """
    datos = datos_parametros or {}
    parametros = datos.get('parametros') or {}
    apus = datos.get('apus') or []
    materiales = datos.get('materiales') or []

    fuentes = []
    if parametros.get('COSTO_M2_TIPO'):
        fuentes.append(f"t_parametro_estimacion ({len(parametros['COSTO_M2_TIPO'])} parámetros m²)")
    if apus:
        fuentes.append(f"t_analisis_precio_unitario ({len(apus)} APUs activos)")
    if materiales:
        fuentes.append(f"t_material ({len(materiales)} materiales con precio referencial)")
    return bool(fuentes), fuentes


def _preguntas_progresivas(criterios: CommercialSearchCriteria) -> list[str]:
    """Devuelve como máximo 2 preguntas prioritarias para afinar la propuesta sin abrumar al cliente."""
    preguntas = []
    if criterios.presupuesto_max is None or criterios.presupuesto_max <= 0:
        preguntas.append('¿Cuál es tu presupuesto aproximado y en qué moneda (USD o BOB)?')
    if criterios.tiene_terreno is None:
        preguntas.append('¿Cuentas ya con un terreno propio o necesitarías adquirir uno aparte?')
    if criterios.superficie_min_m2 is None and criterios.superficie_max_m2 is None and criterios.min_dormitorios is None:
        preguntas.append('¿Cuántos dormitorios o cuántos m² aproximados te gustaría construir?')
    if not criterios.zona and len(preguntas) < 2:
        preguntas.append('¿En qué zona o ciudad planeas desarrollar el proyecto?')
    return preguntas[:2]


def _distribuir_ambientes(superficie_m2: Decimal, dormitorios: int, banos: int) -> list[str]:
    ambientes = [
        f"{dormitorios} dormitorio(s)" + (' (1 en suite)' if dormitorios >= 3 else ''),
        f"{banos} baño(s)",
        'Sala - comedor integrado',
        'Cocina funcional',
        'Área de lavandería / servicio',
    ]
    if superficie_m2 >= Decimal('120'):
        ambientes.append('Galería / patio o terraza social')
    if superficie_m2 >= Decimal('150'):
        ambientes.append('Escritorio / estar familiar')
    return ambientes


def generar_propuesta_proyecto(
    id_empresa: int,
    criterios: CommercialSearchCriteria,
    datos_parametros: dict | None,
    lotes_disponibles: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Elabora una propuesta conceptual y preliminar de construcción personalizada
    con 3 escenarios (Económico, Equilibrado, Superior) fundamentados en datos reales.
    """
    tiene_base, fuentes_verificadas = _hay_base_economica_verificable(datos_parametros)
    fecha_ref = cost_service.fecha_referencia_tc()
    tc = cost_service.TIPO_CAMBIO_BOB_USD
    preguntas = _preguntas_progresivas(criterios)

    aviso_alcance = (
        'Propuesta conceptual y preliminar generada con fines orientativos. '
        'No constituye diseño arquitectónico aprobado, proyecto estructural ni presupuesto contractual definitivo.'
    )

    if not tiene_base:
        return {
            'viable': False,
            'informacion_insuficiente': True,
            'motivo': (
                'La empresa no cuenta actualmente con parámetros de costo por m², APUs ni precios '
                'de materiales cargados en el sistema para calcular una estimación económica verificable.'
            ),
            'fuentes_verificadas': [],
            'partidas_no_estimables': [
                'Costo unitario por m² de construcción',
                'Presupuesto preliminar por escenarios',
                'Tiempo estimado de ejecución',
            ],
            'preguntas_progresivas': preguntas,
            'nivel_confianza': 'BAJO',
            'moneda_referencia': criterios.moneda or 'USD',
            'tipo_cambio_referencia': str(tc),
            'fecha_referencia': fecha_ref,
            'aviso_alcance': aviso_alcance,
        }

    tipo_inmueble = criterios.tipo_unidad or 'VIVIENDA'
    if tipo_inmueble == 'LOTE':
        tipo_inmueble = 'VIVIENDA'

    dormitorios = criterios.min_dormitorios or 3
    banos = criterios.min_banos or max(2, dormitorios - 1)
    parametros = (datos_parametros or {}).get('parametros') or {}

    presupuesto_bob = None
    presupuesto_usd = None
    if criterios.presupuesto_max is not None and criterios.presupuesto_max > 0:
        p_dec = Decimal(str(criterios.presupuesto_max))
        if str(criterios.moneda or 'BOB').upper() == 'USD':
            presupuesto_usd = _q2(p_dec)
            presupuesto_bob = _q2(p_dec * tc)
        else:
            presupuesto_bob = _q2(p_dec)
            presupuesto_usd = _q2(p_dec / tc)

    # Determinar superficie objetivo realista
    sup_solicitada = None
    if criterios.superficie_min_m2 and criterios.superficie_max_m2:
        sup_solicitada = _q2(Decimal(str((criterios.superficie_min_m2 + criterios.superficie_max_m2) / 2.0)))
    elif criterios.superficie_min_m2:
        sup_solicitada = _q2(Decimal(str(criterios.superficie_min_m2)))
    elif criterios.superficie_max_m2:
        sup_solicitada = _q2(Decimal(str(criterios.superficie_max_m2)))

    # Si no se especificó superficie pero sí presupuesto, derivar superficie alcanzable con el costo real base
    costo_base_estandar = cost_service._costo_m2_base_bob(tipo_inmueble, parametros)
    if sup_solicitada is None:
        if presupuesto_bob is not None and costo_base_estandar > 0:
            sup_est = _q2((presupuesto_bob / costo_base_estandar) * Decimal('0.88'))
            sup_solicitada = max(Decimal('45.00'), min(sup_est, Decimal('320.00')))
        else:
            sup_solicitada = Decimal(str(max(65, dormitorios * 35)))

    # Diferenciación explícita de terreno vs construcción
    terreno_info: dict[str, Any]
    if criterios.tiene_terreno is True:
        terreno_info = {
            'estado': 'TERRENO_PROPIO',
            'incluido_en_presupuesto_construccion': False,
            'nota': 'El cliente declara disponer de terreno propio; el presupuesto se destina exclusivamente a obra civil y acabados.',
        }
    elif criterios.tiene_terreno is False:
        lotes_ref = [
            {
                'codigo_unidad': l.get('codigo_unidad'),
                'nombre_unidad': l.get('nombre_unidad'),
                'nombre_obra': l.get('nombre_obra'),
                'superficie_m2': l.get('superficie_m2'),
                'precio_usd': l.get('precio_usd'),
                'precio_bob': l.get('precio_bob'),
            }
            for l in (lotes_disponibles or [])[:3]
        ]
        terreno_info = {
            'estado': 'SIN_TERRENO',
            'incluido_en_presupuesto_construccion': False,
            'costo_terreno_estimado': None,
            'nota': (
                'La adquisición del terreno NO está incluida en el presupuesto de construcción y debe '
                'cotizarse de forma separada según ubicación, superficie y normativa urbana.'
            ),
            'lotes_referencia_empresa': lotes_ref,
        }
    else:
        terreno_info = {
            'estado': 'POR_CONFIRMAR',
            'incluido_en_presupuesto_construccion': False,
            'nota': (
                'Aún no se confirmó si cuentas con terreno propio. Los escenarios estiman únicamente '
                'la construcción (sin compra de terreno).'
            ),
        }

    # Construcción de los 3 escenarios: Económico, Equilibrado, Superior
    escenarios_config = [
        ('Económico', 'ESTANDAR', Decimal('0.92'), 'Prioriza optimizar el presupuesto con materiales funcionales de alta durabilidad.'),
        ('Equilibrado', 'MINIMALISTA', Decimal('1.00'), 'Balance óptimo entre calidad constructiva, diseño moderno y control de inversión.'),
        ('Superior', 'LUJO', Decimal('1.05'), 'Prioriza acabados premium, mayor equipamiento y especificaciones superiores.'),
    ]

    escenarios = []
    mob_param = cost_service.estimar_mobiliario_separado(sup_solicitada, parametros)

    for nombre_esc, cod_estilo, factor_sup, enfoque in escenarios_config:
        sup_esc = _q2(max(Decimal('40.00'), sup_solicitada * factor_sup))
        est = cost_service.estimar_costo_constructivo(
            id_empresa=id_empresa,
            superficie_m2=sup_esc,
            tipo_inmueble=tipo_inmueble,
            estilo_acabado=cod_estilo,
            cantidad_plantas=1 if sup_esc <= Decimal('140') else 2,
            dormitorios=dormitorios,
            banos=banos,
            presupuesto_objetivo=presupuesto_usd if presupuesto_usd is not None else None,
            moneda_objetivo='USD',
            datos_parametros=datos_parametros,
        )
        r_fin = est['resumen_financiero']
        eval_p = est.get('evaluacion_presupuesto') or {}
        escenarios.append({
            'escenario': nombre_esc,
            'enfoque': enfoque,
            'codigo_estilo': cod_estilo,
            'estilo_nombre': est['parametros_entrada']['estilo_nombre'],
            'tipologia': tipo_inmueble,
            'superficie_aprox_m2': str(sup_esc),
            'dormitorios': dormitorios,
            'banos': banos,
            'distribucion_ambientes': _distribuir_ambientes(sup_esc, dormitorios, banos),
            'materiales_acabados': est.get('especificaciones_estilo') or [],
            'mobiliario_equipamiento': (
                mob_param
                if mob_param is not None
                else {
                    'disponible': False,
                    'nota': (
                        'Mobiliario suelto no incluido en el costo de obra civil; se cotiza por separado.'
                        if criterios.amoblamiento_preferido
                        else 'Opcional: no incluido en la estimación de obra civil.'
                    ),
                }
            ),
            'presupuesto_preliminar_bob': r_fin['total_estimado_bob'],
            'presupuesto_preliminar_usd': r_fin['total_estimado_usd'],
            'costo_m2_bob': r_fin['costo_m2_ajustado_bob'],
            'costo_m2_usd': r_fin['costo_m2_ajustado_usd'],
            'desglose_capitulos': est['desglose_capitulos'],
            'encaja_presupuesto': eval_p.get('alcanza_presupuesto') if eval_p else None,
            'diferencia_presupuesto_usd': eval_p.get('diferencia_usd') if eval_p else None,
            'superficie_max_presupuesto_m2': eval_p.get('superficie_maxima_recomendada_m2') if eval_p else None,
        })

    # Partidas no estimables y nivel de confianza real
    partidas_no_estimables = [
        'Adquisición de terreno y gastos notariales/registrales',
        'Estudio de suelos, topografía, licencias municipales y acometidas externas',
        'Plazo exacto de ejecución (requiere cronograma técnico y rendimientos de obra confirmados)',
    ]
    if mob_param is None:
        partidas_no_estimables.append('Paquete de mobiliario y equipamiento suelto (sin tarifario cargado)')

    tiene_param_empresa = any(
        p.get('id_empresa') == id_empresa
        for p in (parametros.get('COSTO_M2_TIPO') or {}).values()
    )
    if tiene_param_empresa and (datos_parametros or {}).get('apus'):
        confianza = 'ALTO'
    elif parametros.get('COSTO_M2_TIPO'):
        confianza = 'MEDIO'
    else:
        confianza = 'BAJO'

    supuestos = [
        f"Tipo de cambio referencial aplicado: 1 USD = {tc} BOB (fecha {fecha_ref}).",
        f"Superficie base evaluada: {sup_solicitada} m² para {tipo_inmueble} de {dormitorios} dormitorio(s) y {banos} baño(s).",
        'Costos calculados sobre parámetros constructivos y APUs vigentes de la empresa; no incluyen terreno ni mobiliario suelto.',
    ]

    return {
        'viable': True,
        'informacion_insuficiente': False,
        'es_propuesta_preliminar': True,
        'tipologia': tipo_inmueble,
        'superficie_referencia_m2': str(sup_solicitada),
        'terreno': terreno_info,
        'escenarios': escenarios,
        'costos_confirmados': [],
        'costos_estimados': [
            'Obra gris, instalaciones y acabados por m² (estimación paramétrica determinista)',
        ],
        'alcance_incluido': [
            'Estructura y obra gris',
            'Instalaciones eléctricas, hidrosanitarias y básicas',
            'Acabados interiores y exteriores según estilo seleccionado',
        ],
        'alcance_excluido': [
            'Compra de terreno',
            'Trámites municipales, planos visados y estudio de suelos',
            'Mobiliario suelto y electrodomésticos (cotizable aparte)',
        ],
        'supuestos': supuestos,
        'partidas_no_estimables': partidas_no_estimables,
        'tiempo_estimado': None,
        'nota_tiempo': 'No se estima un plazo fijo sin cronograma y rendimientos de cuadrilla validados.',
        'fuentes_verificadas': fuentes_verificadas,
        'nivel_confianza': confianza,
        'moneda_referencia': criterios.moneda or 'USD',
        'tipo_cambio_referencia': str(tc),
        'fecha_referencia': fecha_ref,
        'preguntas_progresivas': preguntas,
        'aviso_alcance': aviso_alcance,
    }
