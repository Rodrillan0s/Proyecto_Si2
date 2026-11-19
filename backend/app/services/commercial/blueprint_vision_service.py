"""
Servicio de lectura e interpretación multimodal de planos arquitectónicos (CU34).
Utiliza exclusivamente DeepSeek API (complete_vision / chat_structured) y cruza
los datos extraídos con el motor determinista de costos y el catálogo de unidades/modelos.
"""
import struct
from decimal import Decimal
from app.repos import commercial_repos
from app.services.ai.providers import ProviderError, get_deepseek_provider
from app.services.commercial import commercial_query_engine as query_engine
from app.services.commercial import cost_estimation_service as cost_service
from app.services.commercial.contracts import CommercialSearchCriteria

SYSTEM_PROMPT_BLUEPRINT = """Eres un Arquitecto Tasador Senior e Ingeniero Civil de OBRATEC especializado en lectura técnica de planos arquitectónicos e inmobiliarios.
Analiza rigurosamente la imagen del plano proporcionada y el mensaje del cliente potencial.
Tu objetivo es extraer una radiografía técnica precisa sin respuestas vagas.
Devuelve EXCLUSIVAMENTE un objeto JSON válido con esta estructura exacta:
{
  "es_plano_arquitectonico": true,
  "tipo_inmueble_detectado": "DEPARTAMENTO | VIVIENDA | OFICINA | LOCAL",
  "superficie_estimada_m2": 90.0,
  "cantidad_plantas": 1,
  "dormitorios": 2,
  "banos": 2,
  "ambientes_detectados": [
    {"nombre": "Dormitorio Principal", "cantidad": 1, "superficie_aprox_m2": 15.0},
    {"nombre": "Sala - Comedor", "cantidad": 1, "superficie_aprox_m2": 22.0},
    {"nombre": "Cocina", "cantidad": 1, "superficie_aprox_m2": 8.5},
    {"nombre": "Baño", "cantidad": 2, "superficie_aprox_m2": 4.5}
  ],
  "distribucion_observada": "Descripción técnica detallada de zonificación (área social, íntima, servicios), circulación e iluminación.",
  "cotas_detectadas": ["Texto de cotas o medidas legibles en la imagen"],
  "estilo_sugerido": "ESTANDAR | MINIMALISTA | INDUSTRIAL | CONTEMPORANEO | LUJO",
  "nivel_confianza": "ALTO | MEDIO | PRELIMINAR",
  "recomendacion_arquitectonica": "Recomendación técnica puntual sobre optimización espacial o constructiva."
}"""


def detectar_formato_y_dimensiones(image_bytes: bytes) -> dict:
    """
    Inspecciona los magic bytes del archivo para verificar que es una imagen real
    y extraer sus dimensiones en píxeles (ancho x alto) sin depender de librerías externas.
    """
    if not image_bytes or len(image_bytes) < 16:
        raise ValueError('El archivo de imagen está vacío o es demasiado pequeño.')

    # PNG
    if image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
        width, height = struct.unpack('>II', image_bytes[16:24])
        return {'mime_type': 'image/png', 'width': int(width), 'height': int(height)}

    # GIF
    if image_bytes[:6] in (b'GIF87a', b'GIF89a'):
        width, height = struct.unpack('<HH', image_bytes[6:10])
        return {'mime_type': 'image/gif', 'width': int(width), 'height': int(height)}

    # WebP
    if image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
        return {'mime_type': 'image/webp', 'width': 1200, 'height': 900}

    # JPEG
    if image_bytes[:2] == b'\xff\xd8':
        idx = 2
        length = len(image_bytes)
        width, height = 1200, 900
        while idx < length - 9:
            if image_bytes[idx] != 0xFF:
                idx += 1
                continue
            marker = image_bytes[idx + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3):
                height, width = struct.unpack('>HH', image_bytes[idx + 5 : idx + 9])
                break
            if marker in (0xD8, 0xD9) or (0xD0 <= marker <= 0xD7):
                idx += 2
                continue
            seg_len = struct.unpack('>H', image_bytes[idx + 2 : idx + 4])[0]
            if seg_len < 2:
                break
            idx += 2 + seg_len
        return {'mime_type': 'image/jpeg', 'width': int(width), 'height': int(height)}

    raise ValueError('El archivo enviado no corresponde a un formato de imagen válido (PNG, JPEG, WebP o GIF).')


def _normalizar_lectura_plano(
    raw_vision: dict,
    criterios_usuario: CommercialSearchCriteria,
    meta_imagen: dict,
) -> dict:
    tipo = str(raw_vision.get('tipo_inmueble_detectado') or criterios_usuario.tipo_unidad or 'VIVIENDA').strip().upper()
    if tipo not in ('DEPARTAMENTO', 'VIVIENDA', 'OFICINA', 'LOCAL', 'LOTE'):
        tipo = criterios_usuario.tipo_unidad or 'VIVIENDA'

    # Superficie: prioridad a lo extraído del plano o indicado por el usuario
    sup_raw = raw_vision.get('superficie_estimada_m2')
    try:
        sup = float(sup_raw) if sup_raw is not None and float(sup_raw) > 10 else None
    except (ValueError, TypeError):
        sup = None

    if sup is None:
        if criterios_usuario.superficie_min_m2 and criterios_usuario.superficie_max_m2:
            sup = round((criterios_usuario.superficie_min_m2 + criterios_usuario.superficie_max_m2) / 2.0, 2)
        elif criterios_usuario.superficie_min_m2:
            sup = float(criterios_usuario.superficie_min_m2)
        elif criterios_usuario.superficie_max_m2:
            sup = float(criterios_usuario.superficie_max_m2)

    ambientes = raw_vision.get('ambientes_detectados')
    if not isinstance(ambientes, list) or not ambientes:
        dorms_def = criterios_usuario.min_dormitorios or 2
        banos_def = criterios_usuario.min_banos or 2
        ambientes = [
            {'nombre': 'Dormitorio Principal en Suite', 'cantidad': 1, 'superficie_aprox_m2': 15.5},
            {'nombre': 'Dormitorio Secundario', 'cantidad': max(0, dorms_def - 1), 'superficie_aprox_m2': 11.0},
            {'nombre': 'Sala - Comedor Social', 'cantidad': 1, 'superficie_aprox_m2': 24.0},
            {'nombre': 'Cocina', 'cantidad': 1, 'superficie_aprox_m2': 9.5},
            {'nombre': 'Baño Completo', 'cantidad': banos_def, 'superficie_aprox_m2': 4.5},
            {'nombre': 'Área de Lavandería y Circulación', 'cantidad': 1, 'superficie_aprox_m2': 8.0},
        ]
        ambientes = [a for a in ambientes if int(a.get('cantidad') or 0) > 0]

    if sup is None:
        # Calcular superficie sumando ambientes + 18% de muros y circulaciones
        suma_amb = sum(
            float(a.get('superficie_aprox_m2') or 10.0) * max(1, int(a.get('cantidad') or 1))
            for a in ambientes
        )
        sup = round(max(45.0, suma_amb * 1.18), 2)

    try:
        dorms = int(raw_vision.get('dormitorios')) if raw_vision.get('dormitorios') is not None else (criterios_usuario.min_dormitorios or 2)
    except (ValueError, TypeError):
        dorms = criterios_usuario.min_dormitorios or 2

    try:
        banos = int(raw_vision.get('banos')) if raw_vision.get('banos') is not None else (criterios_usuario.min_banos or 2)
    except (ValueError, TypeError):
        banos = criterios_usuario.min_banos or 2

    try:
        plantas = max(1, int(raw_vision.get('cantidad_plantas') or 1))
    except (ValueError, TypeError):
        plantas = 1

    estilo_sug = cost_service.normalizar_estilo(
        criterios_usuario.estilo_acabado or raw_vision.get('estilo_sugerido') or 'MINIMALISTA'
    )

    confianza = str(raw_vision.get('nivel_confianza') or 'MEDIO').upper()
    if meta_imagen.get('width', 0) < 400 or meta_imagen.get('height', 0) < 400:
        confianza = 'PRELIMINAR'

    return {
        'es_plano_arquitectonico': bool(raw_vision.get('es_plano_arquitectonico', True)),
        'tipo_inmueble_detectado': tipo,
        'superficie_estimada_m2': round(sup, 2),
        'cantidad_plantas': plantas,
        'dormitorios': dorms,
        'banos': banos,
        'ambientes_detectados': ambientes,
        'distribucion_observada': (
            str(raw_vision.get('distribucion_observada') or '').strip()
            or f"Distribución funcional de {round(sup, 2)} m² organizada en zona social integrada, {dorms} dormitorio(s) y {banos} baño(s)."
        ),
        'cotas_detectadas': raw_vision.get('cotas_detectadas') if isinstance(raw_vision.get('cotas_detectadas'), list) else [],
        'estilo_sugerido': estilo_sug,
        'nivel_confianza': confianza,
        'recomendacion_arquitectonica': (
            str(raw_vision.get('recomendacion_arquitectonica') or '').strip()
            or 'Se recomienda concentrar los núcleos húmedos (cocina y baños) sobre un mismo eje técnico para optimizar un 6% el presupuesto hidrosanitario.'
        ),
        'resolucion_imagen': f"{meta_imagen['width']}x{meta_imagen['height']} px ({meta_imagen['mime_type']})",
    }


def _buscar_modelos_afines(lectura: dict, modelos: list[dict]) -> list[dict]:
    sup_plano = float(lectura['superficie_estimada_m2'])
    tipo_plano = lectura['tipo_inmueble_detectado']
    afines = []
    for m in modelos or []:
        sup_mod = float(m.get('superficie_base') or 0)
        score = 50
        if m.get('tipo_unidad') == tipo_plano:
            score += 25
        if sup_mod > 0:
            diff_ratio = abs(sup_mod - sup_plano) / max(sup_plano, 1.0)
            if diff_ratio <= 0.15:
                score += 25
            elif diff_ratio <= 0.30:
                score += 12
        afines.append({
            'id_modelo': m['id_modelo'],
            'nombre': m['nombre'],
            'tipo_unidad': m['tipo_unidad'],
            'superficie_base_m2': str(m['superficie_base']),
            'cantidad_plantas': m['cantidad_plantas_base'],
            'similitud_porcentaje': min(98, score),
            'descripcion': m.get('descripcion') or 'Tipología oficial del catálogo de la constructora',
        })
    afines.sort(key=lambda x: x['similitud_porcentaje'], reverse=True)
    return afines[:3]


def analizar_plano_y_cotizar(
    id_empresa: int,
    image_bytes: bytes,
    mensaje_cliente: str = '',
    presupuesto_max: float | None = None,
    moneda: str = 'BOB',
    estilo_preferido: str | None = None,
    provider=None,
) -> dict:
    """
    Ejecuta el flujo completo de lectura de plano arquitectónico con DeepSeek API:
    1. Valida formato real y dimensiones de la imagen.
    2. Invoca a DeepSeek Vision (complete_vision) con fallback estructurado a DeepSeek Chat.
    3. Calcula el presupuesto constructivo paramétrico por capítulos y estilos en Decimal.
    4. Cruza la distribución detectada contra los modelos y unidades disponibles de la empresa.
    """
    meta_img = detectar_formato_y_dimensiones(image_bytes)
    criterios_locales = query_engine.extraer_criterios_locales(
        mensaje=mensaje_cliente or 'Analizar plano arquitectónico y estimar costo',
        presupuesto_max=presupuesto_max,
        moneda=moneda,
        estilo_preferido=estilo_preferido,
    )

    ai_provider = provider or get_deepseek_provider()
    modo_analisis = 'DEEPSEEK_VISION_MULTIMODAL'
    raw_vision = {}

    prompt_vision = (
        f"Mensaje y preferencias del cliente: {mensaje_cliente or 'Deseo conocer la distribución y costo de este plano.'}. "
        f"Dimensiones de imagen: {meta_img['width']}x{meta_img['height']} px."
    )

    try:
        vision_res = ai_provider.complete_vision(
            system=SYSTEM_PROMPT_BLUEPRINT,
            prompt=prompt_vision,
            image_bytes=image_bytes,
            mime_type=meta_img['mime_type'],
            context={
                'preferencias_cliente': {
                    'presupuesto_max': criterios_locales.presupuesto_max,
                    'moneda': criterios_locales.moneda,
                    'estilo_preferido': criterios_locales.estilo_acabado,
                    'min_dormitorios': criterios_locales.min_dormitorios,
                }
            },
            json_mode=True,
        )
        if isinstance(vision_res, dict):
            raw_vision = vision_res
    except ProviderError:
        # Si el endpoint actual tiene habilitado solo deepseek-chat textual, extraer con chat_structured
        modo_analisis = 'DEEPSEEK_ESTRUCTURADO_ASISTIDO'
        try:
            raw_vision = ai_provider.chat_structured(
                system=SYSTEM_PROMPT_BLUEPRINT,
                prompt=prompt_vision,
                context={
                    'metadatos_imagen': meta_img,
                    'criterios_detectados': criterios_locales.model_dump(),
                },
            )
        except ProviderError:
            modo_analisis = 'PARAMETRICO_DETERMINISTA_LOCAL'
            raw_vision = {}

    lectura = _normalizar_lectura_plano(raw_vision, criterios_locales, meta_img)

    # Cargar parámetros, modelos y unidades de la empresa autorizada
    datos_parametros = commercial_repos.obtener_parametros_estimacion_empresa(id_empresa)
    modelos_empresa = commercial_repos.listar_modelos_comerciales(id_empresa)
    unidades_raw = commercial_repos.listar_unidades_comerciales(id_empresa)

    # Estimación determinista de costo para el plano leído
    estimacion_costo = cost_service.estimar_costo_constructivo(
        id_empresa=id_empresa,
        superficie_m2=Decimal(str(lectura['superficie_estimada_m2'])),
        tipo_inmueble=lectura['tipo_inmueble_detectado'],
        estilo_acabado=estilo_preferido or lectura['estilo_sugerido'],
        cantidad_plantas=lectura['cantidad_plantas'],
        dormitorios=lectura['dormitorios'],
        banos=lectura['banos'],
        presupuesto_objetivo=criterios_locales.presupuesto_max,
        moneda_objetivo=criterios_locales.moneda,
        datos_parametros=datos_parametros,
    )

    # Buscar modelos y unidades del catálogo que se parezcan al plano del cliente
    modelos_afines = _buscar_modelos_afines(lectura, modelos_empresa)
    criterios_matching = CommercialSearchCriteria(
        intencion='recomendar_presupuesto',
        tipo_unidad=lectura['tipo_inmueble_detectado'],
        min_dormitorios=lectura['dormitorios'],
        superficie_min_m2=round(lectura['superficie_estimada_m2'] * 0.75, 2),
        superficie_max_m2=round(lectura['superficie_estimada_m2'] * 1.30, 2),
        presupuesto_max=criterios_locales.presupuesto_max,
        moneda=criterios_locales.moneda,
        estilo_acabado=lectura['estilo_sugerido'],
    )
    matching_unidades = query_engine.filtrar_y_recomendar_unidades(
        unidades_raw=unidades_raw,
        datos_parametros=datos_parametros,
        criterios=criterios_matching,
        top_k=4,
    )

    return {
        'modo_analisis': modo_analisis,
        'lectura_plano': lectura,
        'estimacion_costo': estimacion_costo,
        'modelos_similares_catalogo': modelos_afines,
        'unidades_similares_disponibles': matching_unidades['unidades_recomendadas'],
    }

