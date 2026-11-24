"""Extractor desacoplado y honesto para análisis de planos (imágenes y PDFs).

SEPARACIÓN ESTRICTA DE CAPAS:
1. Validación real de formato (magic bytes PNG/JPEG/WebP/GIF/PDF) y resolución.
2. Extracción textual vectorial para PDFs (cuando el plano es CAD exportado a PDF).
3. Adaptador multimodal opcional (ej. GeminiProvider si GEMINI_API_KEY está configurado)
   para lectura visual real; NUNCA asume que DeepSeek textual puede ver píxeles.
4. REGLA ANTI-ALUCINACIÓN: si no hay extractor visual disponible o la imagen no es legible,
   NO fabrica ambientes ni superficies por defecto; devuelve explícitamente datos_no_legibles
   y nivel_confianza='PRELIMINAR' para que el usuario confirme los datos.
"""
import io
import re
import struct
from typing import Any
from app.config import Config

MAX_BLUEPRINT_BYTES = 10 * 1024 * 1024  # 10 MiB

ADVERTENCIA_PROFESIONAL = (
    'Esta lectura es orientativa y se basa únicamente en la información legible del archivo '
    'y los datos proporcionados por el usuario. No sustituye cómputos métricos ni validación '
    'de un arquitecto o ingeniero civil colegiado.'
)


def inspect_file(file_bytes: bytes) -> dict[str, Any]:
    """Valida magic bytes y extrae metadatos reales (PNG, JPEG, WebP, GIF o PDF)."""
    if not file_bytes or len(file_bytes) < 16:
        raise ValueError('El archivo está vacío o es demasiado pequeño.')
    if len(file_bytes) > MAX_BLUEPRINT_BYTES:
        raise ValueError('El archivo supera el límite máximo permitido de 10 MB.')

    if file_bytes.startswith(b'%PDF-'):
        return {'mime_type': 'application/pdf', 'kind': 'pdf', 'width': None, 'height': None, 'size_bytes': len(file_bytes)}
    if file_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
        w, h = struct.unpack('>II', file_bytes[16:24])
        return {'mime_type': 'image/png', 'kind': 'image', 'width': int(w), 'height': int(h), 'size_bytes': len(file_bytes)}
    if file_bytes[:6] in (b'GIF87a', b'GIF89a'):
        w, h = struct.unpack('<HH', file_bytes[6:10])
        return {'mime_type': 'image/gif', 'kind': 'image', 'width': int(w), 'height': int(h), 'size_bytes': len(file_bytes)}
    if file_bytes[:4] == b'RIFF' and file_bytes[8:12] == b'WEBP':
        return {'mime_type': 'image/webp', 'kind': 'image', 'width': None, 'height': None, 'size_bytes': len(file_bytes)}
    if file_bytes[:2] == b'\xff\xd8':
        w, h = _jpeg_dimensions(file_bytes)
        return {'mime_type': 'image/jpeg', 'kind': 'image', 'width': w, 'height': h, 'size_bytes': len(file_bytes)}

    raise ValueError('Formato no soportado. Envía un plano en PNG, JPEG, WebP o PDF.')


def _jpeg_dimensions(data: bytes) -> tuple[int | None, int | None]:
    idx, length = 2, len(data)
    while idx < length - 9:
        if data[idx] != 0xFF:
            idx += 1
            continue
        marker = data[idx + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3):
            h, w = struct.unpack('>HH', data[idx + 5:idx + 9])
            return int(w), int(h)
        if marker in (0xD8, 0xD9) or (0xD0 <= marker <= 0xD7):
            idx += 2
            continue
        seg_len = struct.unpack('>H', data[idx + 2:idx + 4])[0]
        if seg_len < 2:
            break
        idx += 2 + seg_len
    return None, None


def extract_pdf_vector_text(pdf_bytes: bytes) -> str:
    """Extrae texto vectorial de planos PDF (ej. rótulos y cotas CAD) si pypdf está instalado."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        chunks = [(page.extract_text() or '').strip() for page in reader.pages[:5]]
        return '\n'.join(c for c in chunks if c)
    except Exception:
        return ''


def _parse_vector_measurements(text: str) -> dict[str, Any]:
    """Extrae cotas y superficies explícitas de texto vectorial sin inventar valores."""
    cotas = re.findall(r'\b\d+(?:[.,]\d{1,2})?\s*(?:m2|m²|mt2|m\b|cm\b)', text, flags=re.IGNORECASE)
    sup_match = re.search(r'(?:superficie|area|área)[^\d]{0,20}(\d+(?:[.,]\d{1,2})?)\s*(?:m2|m²|mt2)', text, flags=re.IGNORECASE)
    superficie = float(sup_match.group(1).replace(',', '.')) if sup_match else None
    ambientes = []
    for kw in ('dormitorio', 'baño', 'bano', 'cocina', 'sala', 'comedor', 'estar', 'lavanderia', 'garaje', 'parqueo', 'terraza', 'balcon', 'oficina'):
        count = len(re.findall(r'\b' + kw + r'\w*\b', text, flags=re.IGNORECASE))
        if count > 0:
            ambientes.append({'nombre': kw.capitalize(), 'cantidad': count})
    return {
        'superficie_m2': superficie,
        'ambientes_detectados': ambientes,
        'cotas_detectadas': list(dict.fromkeys(cotas))[:20],
    }


def extract_blueprint(file_bytes: bytes, user_message: str = '', vision_adapter=None) -> dict[str, Any]:
    """Ejecuta extracción honesta separando extracción visual/vectorial del cálculo posterior."""
    meta = inspect_file(file_bytes)
    datos_no_legibles: list[str] = []
    advertencias: list[str] = [ADVERTENCIA_PROFESIONAL]

    # Caso 1: PDF con texto vectorial
    if meta['kind'] == 'pdf':
        vec_text = extract_pdf_vector_text(file_bytes)
        if vec_text:
            parsed = _parse_vector_measurements(vec_text)
            if parsed['superficie_m2'] is None:
                datos_no_legibles.append('superficie_m2')
            if not parsed['ambientes_detectados']:
                datos_no_legibles.append('ambientes_detectados')
            return {
                'meta_archivo': meta,
                'modo_extraccion': 'PDF_VECTORIAL',
                'nivel_confianza': 'VERIFICADO_VECTORIAL' if not datos_no_legibles else 'PRELIMINAR',
                'superficie_m2': parsed['superficie_m2'],
                'ambientes_detectados': parsed['ambientes_detectados'],
                'cotas_detectadas': parsed['cotas_detectadas'],
                'texto_extraido': vec_text[:3000],
                'datos_no_legibles': datos_no_legibles,
                'advertencias': advertencias,
            }
        datos_no_legibles.extend(['superficie_m2', 'ambientes_detectados', 'cotas_detectadas'])
        advertencias.append('El PDF no contiene texto vectorial seleccionable (posible plano escaneado) y requiere un servicio OCR/multimodal activo.')
        return {
            'meta_archivo': meta,
            'modo_extraccion': 'NO_LEGIBLE_SIN_VISION',
            'nivel_confianza': 'PRELIMINAR',
            'superficie_m2': None,
            'ambientes_detectados': [],
            'cotas_detectadas': [],
            'texto_extraido': '',
            'datos_no_legibles': datos_no_legibles,
            'advertencias': advertencias,
        }

    # Caso 2: Imagen -> comprobar resolución
    if (meta.get('width') and meta['width'] < 400) or (meta.get('height') and meta['height'] < 400):
        advertencias.append('La resolución de la imagen es baja (< 400 px); las cotas pueden no ser legibles con precisión.')

    # Adaptador multimodal opcional explícito (no asume que DeepSeek textual ve imágenes)
    if vision_adapter is not None:
        raw = vision_adapter.extract(file_bytes, meta['mime_type'], user_message)
        if isinstance(raw, dict):
            sup = raw.get('superficie_estimada_m2')
            ambs = raw.get('ambientes_detectados') or []
            if not sup:
                datos_no_legibles.append('superficie_m2')
            if not ambs:
                datos_no_legibles.append('ambientes_detectados')
            return {
                'meta_archivo': meta,
                'modo_extraccion': 'EXTRACTOR_MULTIMODAL',
                'nivel_confianza': raw.get('nivel_confianza') or ('VISUAL_MEDIO' if not datos_no_legibles else 'PRELIMINAR'),
                'superficie_m2': float(sup) if sup else None,
                'ambientes_detectados': ambs,
                'cotas_detectadas': raw.get('cotas_detectadas') or [],
                'texto_extraido': raw.get('distribucion_observada') or '',
                'datos_no_legibles': datos_no_legibles,
                'advertencias': advertencias,
            }

    # Sin adaptador multimodal configurado: honestidad total (cero fabricación de ambientes)
    datos_no_legibles.extend(['superficie_m2', 'ambientes_detectados', 'cotas_detectadas'])
    advertencias.append(
        f"El modelo textual actual ({Config.DEEPSEEK_MODEL}) no inspecciona píxeles directamente. "
        "Indica la superficie en m² y los ambientes principales (o configura un extractor multimodal/OCR) "
        "para calcular la estimación paramétrica y comparar opciones del catálogo."
    )
    return {
        'meta_archivo': meta,
        'modo_extraccion': 'SIN_EXTRACTOR_MULTIMODAL',
        'nivel_confianza': 'PRELIMINAR',
        'superficie_m2': None,
        'ambientes_detectados': [],
        'cotas_detectadas': [],
        'texto_extraido': '',
        'datos_no_legibles': datos_no_legibles,
        'advertencias': advertencias,
    }
