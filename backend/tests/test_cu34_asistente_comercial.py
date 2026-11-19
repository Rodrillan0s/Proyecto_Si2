"""
Suite de pruebas unitarias e integración HTTP para CU34:
Asistente Comercial Inteligente y Recomendaciones (HUs 147, 148, 149, 150),
Visión Multimodal de Planos con DeepSeek API y Estimación Paramétrica de Costos/Estilos.
No escribe en base de datos real: utiliza dobles deterministas.
"""
import json
import struct
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app import create_app
from app.config import Config
from app.routes import commercial_routes
from app.services.ai.providers import DeepSeekProvider, ProviderError
from app.services.commercial import (
    blueprint_vision_service as vision_service,
    commercial_assistant_service as assistant_service,
    commercial_query_engine as query_engine,
    cost_estimation_service as cost_service,
    lead_capture_service as lead_service,
)
from app.services.commercial.contracts import (
    CommercialChatRequest,
    CommercialSearchCriteria,
    CostEstimationRequest,
    LeadContactRequest,
)


def _sample_png_bytes(width: int = 800, height: int = 600) -> bytes:
    """Construye una cabecera PNG válida con dimensiones reales para pruebas sin archivos externos."""
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + b'IHDR' + ihdr_data + b'\x00' * 32


def _fake_parametros_empresa():
    return {
        'parametros': {
            'COSTO_M2_TIPO': {
                'EDIFICIO': {'valor_numerico': Decimal('3500.0000')},
                'VIVIENDA': {'valor_numerico': Decimal('2800.0000')},
                'COMERCIAL': {'valor_numerico': Decimal('3200.0000')},
            },
            'FACTOR_NIVELES': {
                '1_2': {'valor_numerico': Decimal('1.0000')},
                '3_5': {'valor_numerico': Decimal('1.0800')},
            },
            'FACTOR_ESTILO': {
                'ESTANDAR': {'valor_numerico': Decimal('1.0000')},
                'MINIMALISTA': {'valor_numerico': Decimal('1.1500')},
                'INDUSTRIAL': {'valor_numerico': Decimal('1.1000')},
                'CONTEMPORANEO': {'valor_numerico': Decimal('1.1800')},
                'LUJO': {'valor_numerico': Decimal('1.3500')},
            },
        },
        'apus': [
            {
                'id_apu': 1,
                'codigo': 'APU-ACA-01',
                'nombre': 'Piso porcelanato rectificado 60x120',
                'unidad_medida': 'm2',
                'precio_unitario_final': Decimal('245.50'),
                'tipo': 'ACABADO',
            }
        ],
        'materiales': [
            {
                'id_material': 10,
                'nombre_material': 'Porcelanato Gris Neutro 60x120',
                'precio_referencial': Decimal('165.00'),
                'unidad_medida': 'm2',
            }
        ],
    }


def _fake_unidades_empresa_1():
    return [
        {
            'id_unidad': 101,
            'codigo_unidad': 'UNI-000101',
            'nombre_unidad': 'Departamento 4B Torre Norte',
            'descripcion_unidad': 'Departamento con balcón panorámico y cocina integrada',
            'tipo_estructura': 'DEPARTAMENTO',
            'tipo_unidad': 'DEPARTAMENTO',
            'superficie_m2': Decimal('88.00'),
            'cantidad_plantas': 1,
            'estado_construccion': 'EN_CONSTRUCCION',
            'especificacion_acabado': 'NORMAL',
            'id_modelo': 1,
            'modelo_nombre': 'Modelo Florencia 3D',
            'modelo_descripcion': '3 dormitorios y 2 baños con balcón',
            'id_obra': 10,
            'nombre_obra': 'Condominio Las Palmas',
            'codigo_obra': 'OBR-010',
            'estado_obra': 'ACTIVO',
            'ubicacion': 'Av. Banzer Km 5',
            'zona': 'Norte',
            'distrito': 'Distrito 2',
            'ambientes': [
                {'nombre': 'Dormitorio Principal', 'cantidad': 1},
                {'nombre': 'Dormitorio Secundario', 'cantidad': 2},
                {'nombre': 'Baño', 'cantidad': 2},
                {'nombre': 'Sala Comedor con Balcón', 'cantidad': 1},
            ],
            'caracteristicas': [
                {'nombre': 'Orientación', 'valor': 'Norte'},
                {'nombre': 'Balcón', 'valor': 'Sí'},
                {'nombre': 'precio_usd', 'valor': '78000'},
            ],
            'caracteristicas_map': {
                'orientación': 'Norte',
                'balcón': 'Sí',
                'precio_usd': '78000',
            },
            'personalizaciones': [],
            'disponibilidad_comercial': 'DISPONIBLE',
            'ultimo_monto_pactado': None,
        },
        {
            'id_unidad': 102,
            'codigo_unidad': 'UNI-000102',
            'nombre_unidad': 'Penthouse 8A Torre Norte',
            'descripcion_unidad': 'Penthouse de lujo con terraza y parqueo doble',
            'tipo_estructura': 'DEPARTAMENTO',
            'tipo_unidad': 'DEPARTAMENTO',
            'superficie_m2': Decimal('145.00'),
            'cantidad_plantas': 2,
            'estado_construccion': 'FINALIZADO',
            'especificacion_acabado': 'LUJO',
            'id_modelo': 2,
            'modelo_nombre': 'Modelo Penthouse Imperial',
            'modelo_descripcion': 'Dúplex de lujo',
            'id_obra': 10,
            'nombre_obra': 'Condominio Las Palmas',
            'codigo_obra': 'OBR-010',
            'estado_obra': 'ACTIVO',
            'ubicacion': 'Av. Banzer Km 5',
            'zona': 'Norte',
            'distrito': 'Distrito 2',
            'ambientes': [
                {'nombre': 'Dormitorio en Suite', 'cantidad': 3},
                {'nombre': 'Baño', 'cantidad': 3},
                {'nombre': 'Terraza con Churrasquera', 'cantidad': 1},
            ],
            'caracteristicas': [{'nombre': 'Parqueo', 'valor': '2 incluidos'}],
            'caracteristicas_map': {'parqueo': '2 incluidos'},
            'personalizaciones': [],
            'disponibilidad_comercial': 'DISPONIBLE',
            'ultimo_monto_pactado': None,
        },
        {
            'id_unidad': 103,
            'codigo_unidad': 'UNI-000103',
            'nombre_unidad': 'Vivienda Familiar B-12',
            'descripcion_unidad': 'Casa de 2 plantas con jardín privado',
            'tipo_estructura': 'VIVIENDA',
            'tipo_unidad': 'VIVIENDA',
            'superficie_m2': Decimal('120.00'),
            'cantidad_plantas': 2,
            'estado_construccion': 'PLANIFICADO',
            'especificacion_acabado': 'NORMAL',
            'id_modelo': 3,
            'modelo_nombre': 'Modelo Toscana Casa',
            'modelo_descripcion': 'Vivienda familiar en condominio cerrado',
            'id_obra': 11,
            'nombre_obra': 'Urbanización Jardines del Sur',
            'codigo_obra': 'OBR-011',
            'estado_obra': 'ACTIVO',
            'ubicacion': 'Zona Sur Calle 14',
            'zona': 'Sur',
            'distrito': 'Distrito 5',
            'ambientes': [
                {'nombre': 'Dormitorio', 'cantidad': 3},
                {'nombre': 'Baño', 'cantidad': 2},
            ],
            'caracteristicas': [{'nombre': 'Jardín', 'valor': '40 m2'}],
            'caracteristicas_map': {'jardín': '40 m2'},
            'personalizaciones': [],
            'disponibilidad_comercial': 'DISPONIBLE',
            'ultimo_monto_pactado': None,
        },
    ]


class DeepSeekMultimodalProviderTests(unittest.TestCase):
    def test_complete_vision_sends_base64_image_and_json_mode(self):
        fake_resp = MagicMock(status_code=200)
        fake_resp.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': json.dumps({
                            'es_plano_arquitectonico': True,
                            'tipo_inmueble_detectado': 'DEPARTAMENTO',
                            'superficie_estimada_m2': 92.5,
                            'cantidad_plantas': 1,
                            'dormitorios': 3,
                            'banos': 2,
                            'estilo_sugerido': 'MINIMALISTA',
                        })
                    }
                }
            ]
        }
        png_bytes = _sample_png_bytes(1024, 768)
        with patch.object(Config, 'DEEPSEEK_API_KEY', 'sk-test-key'), patch.object(
            Config, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com'
        ), patch.object(Config, 'DEEPSEEK_VISION_MODEL', 'deepseek-flash'), patch(
            'app.services.ai.providers.requests.post', return_value=fake_resp
        ) as mock_post:
            res = DeepSeekProvider().complete_vision(
                system='Analiza este plano.',
                prompt='Plano de 3 dormitorios',
                image_bytes=png_bytes,
                mime_type='image/png',
                json_mode=True,
            )
            self.assertEqual(res['tipo_inmueble_detectado'], 'DEPARTAMENTO')
            self.assertEqual(res['superficie_estimada_m2'], 92.5)
            sent_json = mock_post.call_args.kwargs['json']
            self.assertEqual(sent_json['model'], 'deepseek-flash')
            self.assertEqual(sent_json['response_format'], {'type': 'json_object'})
            user_content = sent_json['messages'][1]['content']
            self.assertEqual(user_content[1]['type'], 'image_url')
            self.assertTrue(user_content[1]['image_url']['url'].startswith('data:image/png;base64,'))

    def test_complete_vision_rejects_invalid_mime_or_empty(self):
        provider = DeepSeekProvider()
        with self.assertRaises(ProviderError) as exc_empty:
            provider.complete_vision('sys', 'prompt', b'')
        self.assertEqual(exc_empty.exception.status_code, 400)

        with self.assertRaises(ProviderError) as exc_mime:
            provider.complete_vision('sys', 'prompt', b'1234567890123456', mime_type='application/exe')
        self.assertEqual(exc_mime.exception.status_code, 400)


class CommercialDomainEngineTests(unittest.TestCase):
    def test_hu147_and_hu148_natural_language_search_and_budget_recommendation(self):
        criterios = query_engine.extraer_criterios_locales(
            'Busco un departamento de 3 dormitorios en la zona Norte con balcón y presupuesto hasta 85.000 USD'
        )
        self.assertEqual(criterios.tipo_unidad, 'DEPARTAMENTO')
        self.assertEqual(criterios.min_dormitorios, 3)
        self.assertEqual(criterios.moneda, 'USD')
        self.assertEqual(criterios.presupuesto_max, 85000.0)
        self.assertEqual(criterios.zona, 'norte')
        self.assertIn('balcon', criterios.caracteristicas_deseadas)

        res = query_engine.filtrar_y_recomendar_unidades(
            unidades_raw=_fake_unidades_empresa_1(),
            datos_parametros=_fake_parametros_empresa(),
            criterios=criterios,
        )
        self.assertGreaterEqual(res['coincidencias_exactas'], 1)
        top = res['unidades_recomendadas'][0]
        self.assertEqual(top['codigo_unidad'], 'UNI-000101')
        self.assertTrue(top['cumple_criterios_estrictos'])
        self.assertEqual(top['precio_usd'], '78000.00')

    def test_hu149_side_by_side_unit_comparison(self):
        res_busq = query_engine.filtrar_y_recomendar_unidades(
            unidades_raw=_fake_unidades_empresa_1(),
            datos_parametros=_fake_parametros_empresa(),
            criterios=CommercialSearchCriteria(solo_disponibles=True),
        )
        comp = query_engine.comparar_alternativas_inmobiliarias(
            unidades_enriquecidas=res_busq['todas_enriquecidas'],
            ids_solicitud=[101, 102, 103],
        )
        self.assertEqual(comp['total_comparadas'], 3)
        self.assertEqual(comp['resumen_comparativo']['opcion_mas_amplia']['id_unidad'], 102)
        self.assertTrue(all('costo_m2_usd' in u and 'ventajas_competitivas' in u for u in comp['unidades']))

    def test_parametric_cost_estimation_decimal_precision_and_styles(self):
        est = cost_service.estimar_costo_constructivo(
            id_empresa=1,
            superficie_m2=100.0,
            tipo_inmueble='DEPARTAMENTO',
            estilo_acabado='MINIMALISTA',
            cantidad_plantas=1,
            dormitorios=3,
            banos=2,
            presupuesto_objetivo=70000.0,
            moneda_objetivo='USD',
            incluir_parqueo=True,
            datos_parametros=_fake_parametros_empresa(),
        )
        # 3500 BOB/m2 * 1.00 (1 planta) * 1.15 (Minimalista) = 4025.00 BOB/m2
        # 100 m2 * 4025 = 402,500.00 BOB + 83,520.00 (parqueo) = 486,020.00 BOB
        self.assertEqual(est['resumen_financiero']['costo_m2_ajustado_bob'], '4025.00')
        self.assertEqual(est['resumen_financiero']['subtotal_edificacion_bob'], '402500.00')
        self.assertEqual(est['resumen_financiero']['total_estimado_bob'], '486020.00')
        self.assertEqual(len(est['comparativa_estilos']), 5)
        self.assertTrue(est['evaluacion_presupuesto']['alcanza_presupuesto'])

    def test_blueprint_vision_analysis_and_catalog_matching(self):
        png_bytes = _sample_png_bytes(1200, 900)
        fake_provider = MagicMock()
        fake_provider.complete_vision.return_value = {
            'es_plano_arquitectonico': True,
            'tipo_inmueble_detectado': 'DEPARTAMENTO',
            'superficie_estimada_m2': 86.0,
            'cantidad_plantas': 1,
            'dormitorios': 3,
            'banos': 2,
            'ambientes_detectados': [
                {'nombre': 'Dormitorio Principal', 'cantidad': 1, 'superficie_aprox_m2': 15.0},
                {'nombre': 'Dormitorio Secundario', 'cantidad': 2, 'superficie_aprox_m2': 11.0},
                {'nombre': 'Sala Comedor', 'cantidad': 1, 'superficie_aprox_m2': 24.0},
            ],
            'distribucion_observada': 'Planta funcional con ventilación cruzada.',
            'estilo_sugerido': 'MINIMALISTA',
            'nivel_confianza': 'ALTO',
        }
        with patch(
            'app.repos.commercial_repos.obtener_parametros_estimacion_empresa',
            return_value=_fake_parametros_empresa(),
        ), patch(
            'app.repos.commercial_repos.listar_modelos_comerciales',
            return_value=[
                {
                    'id_modelo': 1,
                    'nombre': 'Modelo Florencia 3D',
                    'descripcion': '3 dormitorios',
                    'tipo_unidad': 'DEPARTAMENTO',
                    'superficie_base': Decimal('88.00'),
                    'cantidad_plantas_base': 1,
                    'caracteristicas': [],
                }
            ],
        ), patch(
            'app.repos.commercial_repos.listar_unidades_comerciales',
            return_value=_fake_unidades_empresa_1(),
        ):
            res = vision_service.analizar_plano_y_cotizar(
                id_empresa=1,
                image_bytes=png_bytes,
                mensaje_cliente='Quiero cotizar este plano en estilo minimalista',
                presupuesto_max=80000,
                moneda='USD',
                provider=fake_provider,
            )
            self.assertEqual(res['modo_analisis'], 'DEEPSEEK_VISION_MULTIMODAL')
            self.assertEqual(res['lectura_plano']['superficie_estimada_m2'], 86.0)
            self.assertEqual(res['modelos_similares_catalogo'][0]['nombre'], 'Modelo Florencia 3D')
            self.assertGreaterEqual(len(res['unidades_similares_disponibles']), 1)


class CommercialRoutesAndMultiTenantTests(unittest.TestCase):
    def setUp(self):
        commercial_routes.reset_rate_limits()
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_chat_and_lead_capture_hu150_with_tenant_isolation(self):
        empresa_1 = {
            'id_empresa': 1,
            'slug': 'constructora-alpha',
            'nombre_empresa': 'Constructora Alpha S.A.',
            'nit': 10203040,
            'descripcion': 'Líder en edificios residenciales',
        }
        with patch(
            'app.repos.commercial_repos.resolver_empresa_comercial',
            return_value=empresa_1,
        ), patch(
            'app.repos.commercial_repos.obtener_parametros_estimacion_empresa',
            return_value=_fake_parametros_empresa(),
        ), patch(
            'app.repos.commercial_repos.listar_unidades_comerciales',
            return_value=_fake_unidades_empresa_1(),
        ), patch(
            'app.repos.commercial_repos.registrar_lead_comercial_transaccional',
            return_value={
                'id_cliente': 55,
                'id_persona': 99,
                'es_nuevo_prospecto': True,
                'estado': 'INTERESADO',
                'origen': 'WEB',
                'asesor_asignado': 'Ing. Ana Suárez',
                'unidades_vinculadas': [
                    {'id_unidad': 101, 'codigo': 'UNI-000101', 'nombre': 'Departamento 4B', 'obra': 'Condominio Las Palmas'}
                ],
                'asociaciones_creadas': [201],
                'id_interaccion': 301,
            },
        ):
            # 1. Consulta en lenguaje natural (HU147 / HU148)
            r_chat = self.client.post(
                '/api/public/comercial/constructora-alpha/chat',
                json={
                    'mensaje': 'Busco departamento de 3 dormitorios en la zona Norte hasta 85000 USD',
                    'moneda': 'USD',
                },
            )
            self.assertEqual(r_chat.status_code, 200)
            body = r_chat.json()
            self.assertTrue(body['success'])
            self.assertIn('UNI-000101', body['resumen_estructurado'])
            conv_id = body['conversacion_id']

            # 2. Solicitud de contacto (HU150) desde el asistente
            r_lead = self.client.post(
                '/api/public/comercial/constructora-alpha/solicitar-contacto',
                json={
                    'nombre_completo': 'Roberto Paz',
                    'telefono': '77011223',
                    'email': 'roberto.paz@example.com',
                    'presupuesto_estimado': 80000,
                    'moneda': 'USD',
                    'unidades_interes': [101],
                    'conversacion_id': conv_id,
                },
            )
            self.assertEqual(r_lead.status_code, 200)
            lead_body = r_lead.json()
            self.assertTrue(lead_body['data']['registrado'])
            self.assertEqual(lead_body['data']['id_cliente_crm'], 55)

    def test_cross_tenant_jwt_is_rejected_with_403(self):
        empresa_1 = {
            'id_empresa': 1,
            'slug': 'constructora-alpha',
            'nombre_empresa': 'Constructora Alpha S.A.',
            'nit': 10203040,
            'descripcion': 'Constructora 1',
        }
        with patch(
            'app.repos.commercial_repos.resolver_empresa_comercial',
            return_value=empresa_1,
        ), patch(
            'app.routes.commercial_routes.decode_access_token',
            return_value={
                'success': True,
                'payload': {
                    'nro_usuario': 12,
                    'nombre_rol': 'ADMINISTRADOR_EMPRESA',
                    'id_empresa': 2,  # Otra empresa distinta a la 1
                },
            },
        ):
            r = self.client.get(
                '/api/public/comercial/constructora-alpha/catalogo',
                headers={'Authorization': 'Bearer fake-jwt-empresa-2'},
            )
            self.assertEqual(r.status_code, 403)


if __name__ == '__main__':
    unittest.main()

