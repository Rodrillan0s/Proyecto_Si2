"""
Motor determinista de estimación paramétrica de costos y estilos (CU34).
Regla innegociable: todos los cálculos monetarios usan Decimal con escala explícita;
el LLM jamás calcula importes ni inventa precios.
"""
import re
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo
from app.repos import commercial_repos

TWO_DECIMALS = Decimal('0.01')
TIPO_CAMBIO_BOB_USD = Decimal('6.96')


def fecha_referencia_tc() -> str:
    return datetime.now(ZoneInfo('America/La_Paz')).date().isoformat()

DEFAULT_COSTO_M2_BOB = {
    'VIVIENDA': Decimal('2800.00'),
    'EDIFICIO': Decimal('3500.00'),
    'COMERCIAL': Decimal('3200.00'),
    'INDUSTRIAL': Decimal('2400.00'),
    'OTRO': Decimal('2500.00'),
}

ESTILOS_CATALOGO = {
    'ESTANDAR': {
        'codigo': 'ESTANDAR',
        'nombre': 'Estilo Estándar Funcional',
        'factor_default': Decimal('1.0000'),
        'acabados_incluidos': [
            'Pisos de cerámica esmaltada de alto tráfico 45x45 cm',
            'Muros revocados con pintura látex lavable mate',
            'Carpintería interior de madera prensada y aluminio serie 20',
            'Mesones de cocina en granito nacional y grifería cromada estándar',
        ],
    },
    'INDUSTRIAL': {
        'codigo': 'INDUSTRIAL',
        'nombre': 'Estilo Urbano Industrial',
        'factor_default': Decimal('1.1000'),
        'acabados_incluidos': [
            'Hormigón visto tratado con sellador poliuretánico y ladrillo visto',
            'Pisos de microcemento alisado / porcelanato gris cemento',
            'Carpintería metálica negra de perfilería esbelta y vidrio templado',
            'Iluminación en rieles electrificados LED y tuberías vistas de diseño',
        ],
    },
    'MINIMALISTA': {
        'codigo': 'MINIMALISTA',
        'nombre': 'Estilo Moderno Minimalista',
        'factor_default': Decimal('1.1500'),
        'acabados_incluidos': [
            'Porcelanato rectificado gran formato 60x120 cm tono neutro',
            'Mesones de cuarzo blanco/gris compacto y muebles sin tiradores (push-open)',
            'Carpintería de aluminio anodizado negro mate con rotura de puente térmico',
            'Cielos falsos con gargantas de luz indirecta LED cálida',
        ],
    },
    'CONTEMPORANEO': {
        'codigo': 'CONTEMPORANEO',
        'nombre': 'Estilo Contemporáneo Cálido',
        'factor_default': Decimal('1.1800'),
        'acabados_incluidos': [
            'Pisos de porcelanato maderado / ingeniería y zócalos embutidos',
            'Revestimientos alistonados de madera (wall panels) en área social',
            'Grifería monocomando negra/dorado cepillado y sanitarios suspendidos',
            'Ventanales con doble vidriado hermético (DVH) termoacústico',
        ],
    },
    'LUJO': {
        'codigo': 'LUJO',
        'nombre': 'Estilo Premium / Lujo Exclusivo',
        'factor_default': Decimal('1.3500'),
        'acabados_incluidos': [
            'Revestimientos en piedra sinterizada / mármol importado y pisos de ingeniería',
            'Cocina equipada con isla en cascada, herrajes cierre suave y grifería premium',
            'Preinstalación domótica integral (iluminación, cortinas, cerradura biométrica)',
            'Carpintería de piso a techo laqueada a medida y climatización eficiente',
        ],
    },
}

EXTRAS_COSTO_BOB = {
    'parqueo': Decimal('83520.00'),   # ~12,000 USD
    'baulera': Decimal('24360.00'),   # ~3,500 USD
    'domotica': Decimal('31320.00'),  # ~4,500 USD
}


def _q2(value: Decimal) -> Decimal:
    return value.quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)


def normalizar_estilo(estilo_raw: str | None) -> str:
    if not estilo_raw:
        return 'ESTANDAR'
    clean = str(estilo_raw).strip().upper()
    aliases = {
        'NORMAL': 'ESTANDAR',
        'BASICO': 'ESTANDAR',
        'CLASICO': 'ESTANDAR',
        'ESTÁNDAR': 'ESTANDAR',
        'MODERNO': 'MINIMALISTA',
        'MINIMAL': 'MINIMALISTA',
        'URBANO': 'INDUSTRIAL',
        'LOFT': 'INDUSTRIAL',
        'CALIDO': 'CONTEMPORANEO',
        'CONTEMPORÁNEO': 'CONTEMPORANEO',
        'PREMIUM': 'LUJO',
        'EXCLUSIVO': 'LUJO',
        'ALTA_GAMA': 'LUJO',
    }
    if clean in ESTILOS_CATALOGO:
        return clean
    if clean in aliases:
        return aliases[clean]
    for key in ESTILOS_CATALOGO:
        if key in clean:
            return key
    return 'ESTANDAR'


def _mapear_tipo_costo(tipo_unidad: str | None) -> str:
    t = str(tipo_unidad or 'DEPARTAMENTO').strip().upper()
    if t in ('DEPARTAMENTO', 'EDIFICIO'):
        return 'EDIFICIO'
    if t in ('VIVIENDA', 'CASA', 'DUPLEX', 'PENTHOUSE'):
        return 'VIVIENDA'
    if t in ('LOCAL', 'OFICINA', 'COMERCIAL'):
        return 'COMERCIAL'
    if t in ('INDUSTRIAL', 'GALPON'):
        return 'INDUSTRIAL'
    return 'OTRO'


def _factor_niveles(plantas: int, parametros: dict) -> Decimal:
    niveles_cat = parametros.get('FACTOR_NIVELES') or {}
    if plantas <= 2:
        clave, fallback = '1_2', Decimal('1.0000')
    elif plantas <= 5:
        clave, fallback = '3_5', Decimal('1.0800')
    elif plantas <= 10:
        clave, fallback = '6_10', Decimal('1.1500')
    else:
        clave, fallback = 'MAS_10', Decimal('1.2500')
    item = niveles_cat.get(clave)
    return Decimal(str(item['valor_numerico'])) if item else fallback


def _costo_m2_base_bob(tipo_unidad: str, parametros: dict) -> Decimal:
    clave = _mapear_tipo_costo(tipo_unidad)
    cat = parametros.get('COSTO_M2_TIPO') or {}
    item = cat.get(clave)
    if item and item.get('valor_numerico') and Decimal(str(item['valor_numerico'])) > 0:
        return _q2(Decimal(str(item['valor_numerico'])))
    return DEFAULT_COSTO_M2_BOB.get(clave, Decimal('2800.00'))


def _factor_estilo(estilo_codigo: str, parametros: dict) -> Decimal:
    codigo = normalizar_estilo(estilo_codigo)
    cat_estilo = parametros.get('FACTOR_ESTILO') or {}
    if codigo in cat_estilo:
        return Decimal(str(cat_estilo[codigo]['valor_numerico']))
    # Fallback hacia FACTOR_COMPLEJIDAD si existe en la BD
    cat_comp = parametros.get('FACTOR_COMPLEJIDAD') or {}
    if codigo == 'LUJO' and 'ALTO' in cat_comp:
        return Decimal(str(cat_comp['ALTO']['valor_numerico']))
    if codigo in ('MINIMALISTA', 'CONTEMPORANEO', 'INDUSTRIAL') and 'MEDIO' in cat_comp:
        return Decimal(str(cat_comp['MEDIO']['valor_numerico']))
    return ESTILOS_CATALOGO[codigo]['factor_default']


def resolver_amoblamiento_unidad(unidad: dict) -> tuple[str, Decimal | None]:
    """
    Determina de forma verificable el estado de amoblamiento de la unidad:
    AMOBLADA | PARCIALMENTE_AMOBLADA | SIN_AMOBLAR | DESCONOCIDO.
    Jamás infiere amoblamiento por cocina, baños, closets o nivel de acabados.
    """
    valid = {'AMOBLADA', 'PARCIALMENTE_AMOBLADA', 'SIN_AMOBLAR', 'DESCONOCIDO'}
    col_val = str(unidad.get('estado_amoblamiento') or '').strip().upper()
    estado = col_val if col_val in valid else 'DESCONOCIDO'

    if estado == 'DESCONOCIDO':
        cmap = {str(k).strip().lower(): str(v or '').strip() for k, v in (unidad.get('caracteristicas_map') or {}).items()}
        for key in ('estado_amoblamiento', 'amoblamiento', 'amoblado', 'amoblada', 'mobiliario', 'incluye_mobiliario'):
            if key not in cmap:
                continue
            val = cmap[key].lower()
            if any(t in val for t in ('parcial', 'semi')):
                estado = 'PARCIALMENTE_AMOBLADA'
                break
            if any(t in val for t in ('sin amoblar', 'no amobl', 'vacio', 'vacío', 'no incluye', 'false')) or val == 'no':
                estado = 'SIN_AMOBLAR'
                break
            if any(t in val for t in ('amoblad', 'equipad', 'completo', 'completa', 'incluye mobiliario', 'true')) or val in ('si', 'sí'):
                estado = 'AMOBLADA'
                break

    costo_mob_bob = None
    raw_mob = unidad.get('costo_mobiliario_estimado')
    if raw_mob is not None:
        try:
            dec = Decimal(str(raw_mob))
            if dec > 0:
                mon = str(unidad.get('moneda_comercial') or 'BOB').upper()
                costo_mob_bob = _q2(dec * TIPO_CAMBIO_BOB_USD) if mon == 'USD' else _q2(dec)
        except Exception:
            pass
    return estado, costo_mob_bob


def _extraer_precio_publicado_bob(unidad: dict) -> tuple[Decimal | None, str | None]:
    """
    Obtiene únicamente el precio comercial publicado oficial (t_unidad_construccion.precio_venta
    o característica explícita de lista). Jamás expone montos pactados de terceros en CRM.
    """
    pv = unidad.get('precio_venta')
    if pv is not None:
        try:
            amount = Decimal(str(pv))
            if amount > 0:
                mon = str(unidad.get('moneda_comercial') or 'BOB').strip().upper()
                if mon == 'USD':
                    return _q2(amount * TIPO_CAMBIO_BOB_USD), 'PRECIO_PUBLICADO'
                return _q2(amount), 'PRECIO_PUBLICADO'
        except Exception:
            pass

    cmap = unidad.get('caracteristicas_map') or {}
    for key in ('precio_venta', 'precio_lista', 'precio_publicado', 'valor_comercial', 'precio_usd', 'precio_bob', 'precio'):
        raw_val = cmap.get(key)
        if raw_val:
            num_match = re.search(r'(\d+(?:[.,]\d+)?)', str(raw_val).replace(',', ''))
            if num_match:
                try:
                    amount = Decimal(num_match.group(1))
                    if amount > 0:
                        if 'usd' in key or '$' in str(raw_val) or 'usd' in str(raw_val).lower():
                            return _q2(amount * TIPO_CAMBIO_BOB_USD), 'PRECIO_PUBLICADO'
                        return _q2(amount), 'PRECIO_PUBLICADO'
                except Exception:
                    pass

    return None, None


def _contar_ambientes(ambientes: list[dict], caracteristicas_map: dict) -> tuple[int, int, str]:
    dormitorios = 0
    banos = 0
    partes = []
    for amb in ambientes or []:
        nombre = str(amb.get('nombre') or '').strip()
        cant = int(amb.get('cantidad') or 1)
        if not nombre:
            continue
        partes.append(f"{cant} {nombre}")
        low = nombre.lower()
        if any(w in low for w in ('dormitorio', 'habitacion', 'habitación', 'cuarto', 'recamara', 'suite')):
            dormitorios += cant
        elif any(w in low for w in ('bano', 'baño', 'toilette', 'sanitario', 'aseo')):
            banos += cant

    if dormitorios == 0:
        for k, v in (caracteristicas_map or {}).items():
            if any(w in k for w in ('dormitorio', 'habitacion', 'habitación', 'cuarto')):
                m = re.search(r'(\d+)', str(v))
                if m:
                    dormitorios = int(m.group(1))
                    break
    if banos == 0:
        for k, v in (caracteristicas_map or {}).items():
            if any(w in k for w in ('bano', 'baño', 'sanitario')):
                m = re.search(r'(\d+)', str(v))
                if m:
                    banos = int(m.group(1))
                    break

    resumen = ', '.join(partes) if partes else 'Distribución configurable según plano'
    return dormitorios, banos, resumen


def estimar_mobiliario_separado(superficie_m2: Decimal, parametros: dict | None = None) -> dict | None:
    """
    Calcula un costo referencial de mobiliario adicional únicamente si existen parámetros
    de amoblamiento configurados (o devuelve un rango referencial explícitamente marcado como estimado).
    """
    param_mob = ((parametros or {}).get('COSTO_MOBILIARIO_M2') or {}).get('ESTANDAR')
    if param_mob and param_mob.get('valor_numerico'):
        m2_bob = _q2(Decimal(str(param_mob['valor_numerico'])))
        mob_bob = _q2(superficie_m2 * m2_bob)
        return {
            'disponible': True,
            'monto_bob': str(mob_bob),
            'monto_usd': str(_q2(mob_bob / TIPO_CAMBIO_BOB_USD)),
            'tipo_precio': 'ESTIMACION_PARAMETRICA',
            'fuente': 'PARAMETRO_EMPRESA_MOBILIARIO',
            'nota': 'Cotización referencial de mobiliario separada del precio del inmueble.',
        }
    return None


def enriquecer_unidad_comercial(unidad: dict, datos_parametros: dict) -> dict:
    """
    Calcula y adjunta precios deterministas (BOB y USD) diferenciando precio publicado
    de estimación paramétrica, estado verificable de amoblamiento y tipo de cambio con fecha.
    """
    parametros = (datos_parametros or {}).get('parametros') or {}
    superficie = Decimal(str(unidad.get('superficie_m2') or '0.00'))
    superficie_estimada = False
    if superficie <= 0:
        superficie = Decimal('65.00')
        superficie_estimada = True

    plantas = max(1, int(unidad.get('cantidad_plantas') or 1))
    acabado = str(unidad.get('especificacion_acabado') or 'NORMAL').upper()
    estilo_unidad = 'LUJO' if acabado == 'LUJO' else 'ESTANDAR'

    precio_pub_bob, tipo_precio = _extraer_precio_publicado_bob(unidad)
    if precio_pub_bob is not None and precio_pub_bob > 0:
        precio_bob = precio_pub_bob
        fuente_precio = 'PRECIO_PUBLICADO'
        es_estimacion = False
    else:
        costo_m2_base = _costo_m2_base_bob(unidad.get('tipo_unidad'), parametros)
        f_niveles = _factor_niveles(plantas, parametros)
        f_estilo = _factor_estilo(estilo_unidad, parametros)
        margen_comercial = Decimal('1.1800')
        precio_bob = _q2(superficie * costo_m2_base * f_niveles * f_estilo * margen_comercial)
        fuente_precio = 'ESTIMACION_PARAMETRICA'
        tipo_precio = 'ESTIMACION_PARAMETRICA'
        es_estimacion = True

    precio_usd = _q2(precio_bob / TIPO_CAMBIO_BOB_USD)
    costo_m2_bob = _q2(precio_bob / superficie) if superficie > 0 else Decimal('0.00')
    costo_m2_usd = _q2(precio_usd / superficie) if superficie > 0 else Decimal('0.00')

    dormitorios, banos, ambientes_resumen = _contar_ambientes(
        unidad.get('ambientes') or [],
        unidad.get('caracteristicas_map') or {},
    )
    estado_amoblamiento, costo_mob_bob = resolver_amoblamiento_unidad(unidad)
    costo_mob_usd = _q2(costo_mob_bob / TIPO_CAMBIO_BOB_USD) if costo_mob_bob is not None else None

    enriquecida = dict(unidad)
    enriquecida.pop('ultimo_monto_pactado', None)  # Jamás exponer montos pactados de terceros
    enriquecida.update({
        'superficie_m2': str(_q2(superficie)),
        'superficie_m2_num': float(_q2(superficie)),
        'superficie_estimada': superficie_estimada,
        'dormitorios': dormitorios,
        'banos': banos,
        'ambientes_resumen': ambientes_resumen,
        'precio_bob': str(precio_bob),
        'precio_usd': str(precio_usd),
        'precio_bob_num': float(precio_bob),
        'precio_usd_num': float(precio_usd),
        'costo_m2_bob': str(costo_m2_bob),
        'costo_m2_usd': str(costo_m2_usd),
        'fuente_precio': fuente_precio,
        'tipo_precio': tipo_precio,
        'es_estimacion_precio': es_estimacion,
        'estado_amoblamiento': estado_amoblamiento,
        'costo_mobiliario_bob': str(costo_mob_bob) if costo_mob_bob is not None else None,
        'costo_mobiliario_usd': str(costo_mob_usd) if costo_mob_usd is not None else None,
        'tipo_cambio_referencia': str(TIPO_CAMBIO_BOB_USD),
        'fecha_referencia_tc': fecha_referencia_tc(),
    })
    return enriquecida


def estimar_costo_constructivo(
    id_empresa: int,
    superficie_m2: float | Decimal,
    tipo_inmueble: str = 'DEPARTAMENTO',
    estilo_acabado: str = 'MINIMALISTA',
    cantidad_plantas: int = 1,
    dormitorios: int = 2,
    banos: int = 2,
    presupuesto_objetivo: float | Decimal | None = None,
    moneda_objetivo: str = 'BOB',
    incluir_parqueo: bool = False,
    incluir_baulera: bool = False,
    incluir_domotica: bool = False,
    datos_parametros: dict | None = None,
) -> dict:
    """
    Calcula una estimación paramétrica determinista desglosada por capítulos constructivos,
    estilo de acabado, adicionales y comparativa entre los 5 estilos del catálogo.
    """
    if datos_parametros is None:
        datos_parametros = commercial_repos.obtener_parametros_estimacion_empresa(id_empresa)
    parametros = (datos_parametros or {}).get('parametros') or {}
    apus = (datos_parametros or {}).get('apus') or []
    materiales = (datos_parametros or {}).get('materiales') or []

    sup = _q2(Decimal(str(superficie_m2)))
    if sup <= 0:
        raise ValueError('La superficie en m² debe ser mayor a cero.')

    plantas = max(1, int(cantidad_plantas or 1))
    estilo_cod = normalizar_estilo(estilo_acabado)
    estilo_info = ESTILOS_CATALOGO[estilo_cod]

    costo_m2_base_bob = _costo_m2_base_bob(tipo_inmueble, parametros)
    f_niveles = _factor_niveles(plantas, parametros)
    f_estilo = _factor_estilo(estilo_cod, parametros)

    # Recargo moderado por densidad de núcleos húmedos si supera el estándar (más de 2 baños)
    banos_int = max(1, int(banos or 1))
    recargo_nucleos_humedos = Decimal('1.0000') + (Decimal('0.0250') * max(0, banos_int - 2))

    costo_m2_ajustado_bob = _q2(costo_m2_base_bob * f_niveles * f_estilo * recargo_nucleos_humedos)
    subtotal_edificacion_bob = _q2(sup * costo_m2_ajustado_bob)

    # Desglose por capítulos constructivos (suma exacta = subtotal_edificacion_bob)
    cap_obra_gris_bob = _q2(subtotal_edificacion_bob * Decimal('0.52'))
    cap_instalaciones_bob = _q2(subtotal_edificacion_bob * Decimal('0.18'))
    cap_acabados_bob = _q2(subtotal_edificacion_bob - cap_obra_gris_bob - cap_instalaciones_bob)

    # Adicionales seleccionados
    extras_detalle = []
    total_extras_bob = Decimal('0.00')
    if incluir_parqueo:
        monto = EXTRAS_COSTO_BOB['parqueo']
        total_extras_bob += monto
        extras_detalle.append({'concepto': 'Parqueo vehicular cubierto', 'monto_bob': str(monto), 'monto_usd': str(_q2(monto / TIPO_CAMBIO_BOB_USD))})
    if incluir_baulera:
        monto = EXTRAS_COSTO_BOB['baulera']
        total_extras_bob += monto
        extras_detalle.append({'concepto': 'Baulera / depósito privado', 'monto_bob': str(monto), 'monto_usd': str(_q2(monto / TIPO_CAMBIO_BOB_USD))})
    if incluir_domotica and estilo_cod != 'LUJO':
        monto = EXTRAS_COSTO_BOB['domotica']
        total_extras_bob += monto
        extras_detalle.append({'concepto': 'Paquete de automatización domótica', 'monto_bob': str(monto), 'monto_usd': str(_q2(monto / TIPO_CAMBIO_BOB_USD))})

    total_estimado_bob = _q2(subtotal_edificacion_bob + total_extras_bob)
    total_estimado_usd = _q2(total_estimado_bob / TIPO_CAMBIO_BOB_USD)
    costo_m2_ajustado_usd = _q2(costo_m2_ajustado_bob / TIPO_CAMBIO_BOB_USD)

    # Comparativa transparente entre los 5 estilos para la misma superficie
    comparativa_estilos = []
    for cod, meta in ESTILOS_CATALOGO.items():
        fac = _factor_estilo(cod, parametros)
        m2_bob = _q2(costo_m2_base_bob * f_niveles * fac * recargo_nucleos_humedos)
        tot_bob = _q2((sup * m2_bob) + total_extras_bob)
        tot_usd = _q2(tot_bob / TIPO_CAMBIO_BOB_USD)
        comparativa_estilos.append({
            'codigo_estilo': cod,
            'estilo_codigo': cod,
            'nombre_estilo': meta['nombre'],
            'factor_aplicado': str(_q2(fac)),
            'costo_m2_bob': str(m2_bob),
            'costo_m2_usd': str(_q2(m2_bob / TIPO_CAMBIO_BOB_USD)),
            'total_bob': str(tot_bob),
            'total_usd': str(tot_usd),
            'seleccionado': cod == estilo_cod,
            'es_seleccionado': cod == estilo_cod,
        })

    # Evaluación frente al presupuesto objetivo del cliente (si lo indicó)
    evaluacion_presupuesto = None
    if presupuesto_objetivo is not None and Decimal(str(presupuesto_objetivo)) > 0:
        mon = str(moneda_objetivo or 'BOB').strip().upper()
        pres_input = _q2(Decimal(str(presupuesto_objetivo)))
        pres_bob = _q2(pres_input * TIPO_CAMBIO_BOB_USD) if mon == 'USD' else pres_input
        pres_usd = _q2(pres_bob / TIPO_CAMBIO_BOB_USD)
        diferencia_bob = _q2(pres_bob - total_estimado_bob)
        diferencia_usd = _q2(diferencia_bob / TIPO_CAMBIO_BOB_USD)
        superficie_max_alcanzable_m2 = _q2(
            max(Decimal('0.00'), (pres_bob - total_extras_bob)) / costo_m2_ajustado_bob
        ) if costo_m2_ajustado_bob > 0 else Decimal('0.00')

        alcanza = diferencia_bob >= Decimal('0.00')
        evaluacion_presupuesto = {
            'presupuesto_cliente_bob': str(pres_bob),
            'presupuesto_cliente_usd': str(pres_usd),
            'alcanza_presupuesto': alcanza,
            'diferencia_bob': str(diferencia_bob),
            'diferencia_usd': str(diferencia_usd),
            'superficie_maxima_recomendada_m2': str(superficie_max_alcanzable_m2),
            'recomendacion': (
                f"✓ Tu presupuesto de {pres_usd} USD cubre este estilo con una holgura de {diferencia_usd} USD."
                if alcanza
                else f"⚠ Excede tu presupuesto en {abs(diferencia_usd)} USD. Con tu presupuesto puedes construir hasta {superficie_max_alcanzable_m2} m² o elegir un estilo de menor factor."
            ),
        }

    return {
        'parametros_entrada': {
            'superficie_m2': str(sup),
            'tipo_inmueble': str(tipo_inmueble or 'DEPARTAMENTO').upper(),
            'estilo_codigo': estilo_cod,
            'estilo_nombre': estilo_info['nombre'],
            'cantidad_plantas': plantas,
            'dormitorios': int(dormitorios or 2),
            'banos': banos_int,
        },
        'factores_aplicados': {
            'costo_base_m2_bob': str(costo_m2_base_bob),
            'factor_niveles': str(_q2(f_niveles)),
            'factor_estilo': str(_q2(f_estilo)),
            'factor_nucleos_humedos': str(_q2(recargo_nucleos_humedos)),
            'tipo_cambio_referencial': str(TIPO_CAMBIO_BOB_USD),
        },
        'resumen_financiero': {
            'costo_m2_ajustado_bob': str(costo_m2_ajustado_bob),
            'costo_m2_ajustado_usd': str(costo_m2_ajustado_usd),
            'costo_m2_bob': str(costo_m2_ajustado_bob),
            'costo_m2_usd': str(costo_m2_ajustado_usd),
            'subtotal_edificacion_bob': str(subtotal_edificacion_bob),
            'total_adicionales_bob': str(_q2(total_extras_bob)),
            'total_estimado_bob': str(total_estimado_bob),
            'total_estimado_usd': str(total_estimado_usd),
        },
        'desglose_capitulos': [
            {
                'capitulo': 'Obra Gris y Estructura Sismorresistente',
                'porcentaje': '52%',
                'porcentaje_incidencia': 52,
                'monto_bob': str(cap_obra_gris_bob),
                'monto_usd': str(_q2(cap_obra_gris_bob / TIPO_CAMBIO_BOB_USD)),
            },
            {
                'capitulo': 'Instalaciones Hidrosanitarias, Eléctricas y Gas',
                'porcentaje': '18%',
                'porcentaje_incidencia': 18,
                'monto_bob': str(cap_instalaciones_bob),
                'monto_usd': str(_q2(cap_instalaciones_bob / TIPO_CAMBIO_BOB_USD)),
            },
            {
                'capitulo': f"Acabados y Terminaciones ({estilo_info['nombre']})",
                'porcentaje': '30%',
                'porcentaje_incidencia': 30,
                'monto_bob': str(cap_acabados_bob),
                'monto_usd': str(_q2(cap_acabados_bob / TIPO_CAMBIO_BOB_USD)),
            },
        ],
        'adicionales': extras_detalle,
        'especificaciones_estilo': estilo_info['acabados_incluidos'],
        'comparativa_estilos': comparativa_estilos,
        'evaluacion_presupuesto': evaluacion_presupuesto,
        'partidas_apu_referencia': [
            {
                'codigo': a['codigo'],
                'nombre': a['nombre'],
                'unidad': a['unidad_medida'],
                'precio_unitario_bob': str(_q2(a['precio_unitario_final'])),
            }
            for a in apus[:6]
        ],
        'materiales_referencia': [
            {
                'nombre': m['nombre_material'],
                'unidad': m['unidad_medida'],
                'precio_bob': str(_q2(m['precio_referencial'])),
            }
            for m in materiales[:6]
            if m['precio_referencial'] > 0
        ],
    }

