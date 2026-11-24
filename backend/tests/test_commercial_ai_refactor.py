"""Pruebas obligatorias de la Refactorización de IA Comercial de OBRATEC (CU34)."""
from decimal import Decimal
from unittest.mock import patch
import pytest

from app.services.ai.providers import ProviderError
from app.services.commercial import commercial_assistant_service as cas
from app.services.commercial import commercial_query_engine as cqe
from app.services.commercial import project_proposal_engine as ppe
from app.services.commercial.contracts import CommercialChatRequest, CommercialSearchCriteria


def _unit(
    id_unidad: int,
    codigo: str,
    tipo: str = 'VIVIENDA',
    precio_usd: float | None = 75000.0,
    disponibilidad: str = 'DISPONIBLE',
    amoblamiento: str = 'DESCONOCIDO',
    dormitorios: int = 3,
    banos: int = 2,
    superficie: float = 110.0,
    zona: str = 'Norte',
    publicado: bool = True,
    costo_mobiliario_usd: float | None = None,
    ultimo_monto_pactado: float | None = None,
):
    return {
        'id_unidad': id_unidad,
        'codigo_unidad': codigo,
        'nombre_unidad': f'Unidad {codigo}',
        'descripcion_unidad': 'Cocina equipada con mesón y closets empotrados',
        'tipo_estructura': 'VIVIENDA',
        'tipo_unidad': tipo,
        'superficie_m2': Decimal(str(superficie)),
        'cantidad_plantas': 1,
        'estado_construccion': 'FINALIZADO',
        'especificacion_acabado': 'NORMAL',
        'id_modelo': 1,
        'modelo_nombre': 'Modelo Base',
        'modelo_descripcion': 'Modelo referencial',
        'id_obra': 10,
        'nombre_obra': 'Residencial Los Pinos',
        'codigo_obra': 'OBR-10',
        'estado_obra': 'EN_EJECUCION',
        'ubicacion': f'Zona {zona}',
        'zona': zona,
        'distrito': zona,
        'ambientes': [
            {'nombre': 'Dormitorio', 'cantidad': dormitorios},
            {'nombre': 'Baño', 'cantidad': banos},
            {'nombre': 'Cocina', 'cantidad': 1},
        ],
        'caracteristicas': [{'nombre': 'Closets', 'valor': 'Sí'}],
        'caracteristicas_map': {'closets': 'Sí'},
        'personalizaciones': [],
        'disponibilidad_comercial': disponibilidad,
        'publicado_comercial': publicado,
        'precio_venta': Decimal(str(precio_usd)) if precio_usd is not None else None,
        'moneda_comercial': 'USD',
        'estado_amoblamiento': amoblamiento,
        'costo_mobiliario_estimado': Decimal(str(costo_mobiliario_usd)) if costo_mobiliario_usd is not None else None,
        'ultimo_monto_pactado': Decimal(str(ultimo_monto_pactado)) if ultimo_monto_pactado is not None else None,
    }


def _params_empresa(id_empresa: int = 1, con_mobiliario: bool = False):
    params = {
        'COSTO_M2_TIPO': {
            'VIVIENDA': {'id_empresa': id_empresa, 'valor_numerico': Decimal('2800.00')},
            'EDIFICIO': {'id_empresa': id_empresa, 'valor_numerico': Decimal('3500.00')},
        },
        'FACTOR_ESTILO': {
            'ESTANDAR': {'id_empresa': id_empresa, 'valor_numerico': Decimal('1.0000')},
            'MINIMALISTA': {'id_empresa': id_empresa, 'valor_numerico': Decimal('1.1500')},
            'LUJO': {'id_empresa': id_empresa, 'valor_numerico': Decimal('1.3500')},
        },
    }
    if con_mobiliario:
        params['COSTO_MOBILIARIO_M2'] = {
            'ESTANDAR': {'id_empresa': id_empresa, 'valor_numerico': Decimal('450.00')},
        }
    return {
        'parametros': params,
        'apus': [{'id_apu': 1, 'codigo': 'APU-01', 'nombre': 'Muro ladrillo', 'unidad_medida': 'm2', 'precio_unitario_final': Decimal('180.00')}],
        'materiales': [{'id_material': 1, 'nombre_material': 'Cemento', 'unidad_medida': 'bolsa', 'precio_referencial': Decimal('55.00')}],
    }


class _OfflineProvider:
    def chat_structured(self, **kwargs):
        raise ProviderError('offline')

    def complete(self, **kwargs):
        raise ProviderError('offline')


class _StubDeepSeekProvider:
    def __init__(self, structured_payload: dict):
        self.structured_payload = structured_payload

    def chat_structured(self, **kwargs):
        return dict(self.structured_payload)

    def complete(self, **kwargs):
        raise ProviderError('use deterministic text for assertion')


class TestCommercialHardFiltersAndAffinity:
    def test_1_zero_recommendations_when_only_reserved_overbudget_or_office(self):
        """Caso 1: USD 80.000, casa amoblada, solo reservadas / fuera de presupuesto / oficina -> 0 recomendaciones."""
        unidades = [
            _unit(1, 'CASA-RES', tipo='VIVIENDA', precio_usd=72000, disponibilidad='RESERVADA', amoblamiento='AMOBLADA'),
            _unit(2, 'CASA-CARA', tipo='VIVIENDA', precio_usd=95000, disponibilidad='DISPONIBLE', amoblamiento='AMOBLADA'),
            _unit(3, 'OFI-01', tipo='OFICINA', precio_usd=65000, disponibilidad='DISPONIBLE', amoblamiento='AMOBLADA'),
        ]
        crit = CommercialSearchCriteria(
            intencion='recomendar_presupuesto',
            tipo_unidad='VIVIENDA',
            presupuesto_max=80000,
            moneda='USD',
            amoblamiento_preferido='AMOBLADA',
        )
        res = cqe.filtrar_y_recomendar_unidades(unidades, _params_empresa(), crit)
        assert res['unidades_recomendadas'] == []
        assert res['coincidencias_exactas'] == 0
        assert res['motivos_exclusion']['no_disponible_o_reservada'] == 1
        assert res['motivos_exclusion']['fuera_de_presupuesto'] == 1
        assert res['motivos_exclusion']['tipologia_incompatible'] == 1

    def test_2_available_in_budget_unknown_furnishing_warns_and_does_not_infer(self):
        """Caso 2: Vivienda disponible en presupuesto con mobiliario DESCONOCIDO -> recomienda con advertencia."""
        unidades = [
            _unit(10, 'CASA-10', tipo='VIVIENDA', precio_usd=76000, disponibilidad='DISPONIBLE', amoblamiento='DESCONOCIDO'),
        ]
        crit = CommercialSearchCriteria(
            tipo_unidad='VIVIENDA',
            presupuesto_max=80000,
            moneda='USD',
            amoblamiento_preferido='AMOBLADA',
        )
        res = cqe.filtrar_y_recomendar_unidades(unidades, _params_empresa(), crit)
        assert len(res['unidades_recomendadas']) == 1
        u = res['unidades_recomendadas'][0]
        assert u['estado_amoblamiento'] == 'DESCONOCIDO'
        assert any('DESCONOCIDO' in obs for obs in u['observaciones_criterio'])
        assert u['afinidad_score'] < 95  # Penalizado por dato desconocido

    def test_3_furnished_available_in_budget_is_valid_top_recommendation(self):
        """Caso 3: Vivienda amoblada disponible dentro del presupuesto -> recomendación válida prioritaria."""
        unidades = [
            _unit(11, 'CASA-DESC', tipo='VIVIENDA', precio_usd=75000, disponibilidad='DISPONIBLE', amoblamiento='DESCONOCIDO'),
            _unit(12, 'CASA-AMOB', tipo='VIVIENDA', precio_usd=78000, disponibilidad='DISPONIBLE', amoblamiento='AMOBLADA'),
        ]
        crit = CommercialSearchCriteria(
            tipo_unidad='VIVIENDA',
            presupuesto_max=80000,
            moneda='USD',
            amoblamiento_preferido='AMOBLADA',
        )
        res = cqe.filtrar_y_recomendar_unidades(unidades, _params_empresa(), crit)
        assert len(res['unidades_recomendadas']) == 2
        assert res['unidades_recomendadas'][0]['codigo_unidad'] == 'CASA-AMOB'
        assert res['unidades_recomendadas'][0]['estado_amoblamiento'] == 'AMOBLADA'
        assert res['unidades_recomendadas'][0]['afinidad_score'] > res['unidades_recomendadas'][1]['afinidad_score']

    def test_4_furnished_over_budget_is_strictly_excluded(self):
        """Caso 4: Vivienda amoblada que supera el presupuesto (incluso por poco) -> excluir."""
        unidades = [
            _unit(13, 'CASA-82K', tipo='VIVIENDA', precio_usd=82000, disponibilidad='DISPONIBLE', amoblamiento='AMOBLADA'),
        ]
        crit = CommercialSearchCriteria(
            tipo_unidad='VIVIENDA',
            presupuesto_max=80000,
            moneda='USD',
            amoblamiento_preferido='AMOBLADA',
        )
        res = cqe.filtrar_y_recomendar_unidades(unidades, _params_empresa(), crit)
        assert res['unidades_recomendadas'] == []
        assert res['motivos_exclusion']['fuera_de_presupuesto'] == 1

    def test_5_client_accepts_separate_furniture_quote(self):
        """Caso 5: Cliente acepta cotizar mobiliario por separado -> alternativas diferenciadas."""
        unidades = [
            _unit(14, 'CASA-SINMOB', tipo='VIVIENDA', precio_usd=70000, disponibilidad='DISPONIBLE', amoblamiento='SIN_AMOBLAR', costo_mobiliario_usd=6500),
        ]
        crit = CommercialSearchCriteria(
            tipo_unidad='VIVIENDA',
            presupuesto_max=80000,
            moneda='USD',
            amoblamiento_preferido='AMOBLADA',
            amoblamiento_indispensable=True,
            acepta_cotizar_mobiliario=True,
        )
        res = cqe.filtrar_y_recomendar_unidades(unidades, _params_empresa(con_mobiliario=True), crit)
        assert len(res['unidades_recomendadas']) == 1
        u = res['unidades_recomendadas'][0]
        assert u['tipo_precio'] == 'PRECIO_PUBLICADO'
        assert u['cotizacion_mobiliario_separada']['disponible'] is True
        assert u['cotizacion_mobiliario_separada']['tipo_precio'] == 'COSTO_MOBILIARIO_ADICIONAL'
        assert u['cotizacion_mobiliario_separada']['encaja_presupuesto_con_mobiliario'] is True
        assert 'ultimo_monto_pactado' not in u

    def test_never_exposes_third_party_agreed_price(self):
        """Seguridad: nunca exponer ultimo_monto_pactado de terceros."""
        unidades = [
            _unit(15, 'CASA-NOPUB', tipo='VIVIENDA', precio_usd=None, disponibilidad='DISPONIBLE', ultimo_monto_pactado=500000),
        ]
        crit = CommercialSearchCriteria(tipo_unidad='VIVIENDA')
        res = cqe.filtrar_y_recomendar_unidades(unidades, _params_empresa(), crit)
        u = res['unidades_recomendadas'][0]
        assert 'ultimo_monto_pactado' not in u
        assert u['tipo_precio'] == 'ESTIMACION_PARAMETRICA'
        assert u['es_estimacion_precio'] is True


class TestProjectProposalEngine:
    def test_7_client_with_land_requests_construction(self):
        """Caso 7: Cliente dispone de terreno y solicita construir -> 3 escenarios preliminares."""
        crit = CommercialSearchCriteria(
            intencion='proponer_proyecto',
            tipo_unidad='VIVIENDA',
            presupuesto_max=80000,
            moneda='USD',
            min_dormitorios=3,
            tiene_terreno=True,
        )
        prop = ppe.generar_propuesta_proyecto(1, crit, _params_empresa())
        assert prop['viable'] is True
        assert prop['es_propuesta_preliminar'] is True
        assert prop['terreno']['estado'] == 'TERRENO_PROPIO'
        assert len(prop['escenarios']) == 3
        assert [e['escenario'] for e in prop['escenarios']] == ['Económico', 'Equilibrado', 'Superior']
        assert prop['tiempo_estimado'] is None  # No inventa plazos sin cronograma

    def test_8_client_without_land_differentiates_land_vs_construction(self):
        """Caso 8: Cliente sin terreno -> diferencia adquisición del terreno y construcción."""
        crit = CommercialSearchCriteria(
            intencion='proponer_proyecto',
            tipo_unidad='VIVIENDA',
            presupuesto_max=80000,
            moneda='USD',
            tiene_terreno=False,
        )
        prop = ppe.generar_propuesta_proyecto(1, crit, _params_empresa(), lotes_disponibles=[])
        assert prop['viable'] is True
        assert prop['terreno']['estado'] == 'SIN_TERRENO'
        assert prop['terreno']['incluido_en_presupuesto_construccion'] is False
        assert 'terreno' in prop['terreno']['nota'].lower()

    def test_10_insufficient_economic_data_reports_limitations_without_inventing(self):
        """Caso 10: Sin parámetros/APUs/materiales -> informa limitaciones sin inventar precios."""
        crit = CommercialSearchCriteria(
            intencion='proponer_proyecto',
            tipo_unidad='VIVIENDA',
            presupuesto_max=80000,
            moneda='USD',
            tiene_terreno=True,
        )
        prop = ppe.generar_propuesta_proyecto(1, crit, {'parametros': {}, 'apus': [], 'materiales': []})
        assert prop['viable'] is False
        assert prop['informacion_insuficiente'] is True
        assert prop['nivel_confianza'] == 'BAJO'
        assert len(prop['partidas_no_estimables']) >= 2


class TestUnifiedCommercialConversationAndSecurity:
    def test_6_budget_increase_preserves_previous_preferences(self):
        """Caso 6: Cliente aumenta presupuesto -> actualiza presupuesto sin perder tipología, dormitorios, zona ni amoblamiento."""
        unidades = [
            _unit(20, 'CASA-88K', tipo='VIVIENDA', precio_usd=88000, disponibilidad='DISPONIBLE', amoblamiento='AMOBLADA', dormitorios=3, zona='Tranquila'),
        ]
        emp = {'id_empresa': 1, 'slug': 'obratec', 'nombre_empresa': 'OBRATEC', 'nit': 123, 'descripcion': ''}
        with patch('app.repos.commercial_repos.resolver_empresa_comercial', return_value=emp), \
             patch('app.repos.commercial_repos.obtener_parametros_estimacion_empresa', return_value=_params_empresa()), \
             patch('app.repos.commercial_repos.listar_unidades_comerciales', return_value=unidades):
            r1 = cas.procesar_consulta_comercial(
                1,
                CommercialChatRequest(mensaje='Tengo USD 80.000 y quiero una casa amoblada de 3 habitaciones en zona tranquila'),
                provider=_OfflineProvider(),
            )
            assert r1['unidades_recomendadas'] == []
            assert r1['propuesta_proyecto']['viable'] is True  # Caso 9: ninguna cumple -> ofrece proyecto

            r2 = cas.procesar_consulta_comercial(
                1,
                CommercialChatRequest(
                    mensaje='¿Y si aumento mi presupuesto a USD 90.000?',
                    conversacion_id=r1['conversacion_id'],
                ),
                provider=_OfflineProvider(),
            )
            crit2 = r2['criterios_aplicados']
            assert crit2['presupuesto_max'] == 90000.0
            assert crit2['moneda'] == 'USD'
            assert crit2['tipo_unidad'] == 'VIVIENDA'
            assert crit2['min_dormitorios'] == 3
            assert crit2['amoblamiento_preferido'] == 'AMOBLADA'
            assert len(r2['unidades_recomendadas']) == 1
            assert r2['unidades_recomendadas'][0]['codigo_unidad'] == 'CASA-88K'
            # Coherencia texto vs tarjetas
            assert 'CASA-88K' in r2['respuesta']
            assert 'AMOBLADA' in r2['respuesta']

    def test_9_no_matching_property_automatically_offers_custom_project_proposal(self):
        """Caso 9: Ninguna propiedad cumple, pero existen datos -> ofrece propuesta personalizada."""
        unidades = [
            _unit(30, 'CASA-RES', tipo='VIVIENDA', precio_usd=70000, disponibilidad='RESERVADA', amoblamiento='AMOBLADA'),
        ]
        emp = {'id_empresa': 1, 'slug': 'obratec', 'nombre_empresa': 'OBRATEC', 'nit': 123, 'descripcion': ''}
        with patch('app.repos.commercial_repos.resolver_empresa_comercial', return_value=emp), \
             patch('app.repos.commercial_repos.obtener_parametros_estimacion_empresa', return_value=_params_empresa()), \
             patch('app.repos.commercial_repos.listar_unidades_comerciales', return_value=unidades):
            r = cas.procesar_consulta_comercial(
                1,
                CommercialChatRequest(mensaje='Tengo USD 80.000 y quiero una casa bien amoblada'),
                provider=_StubDeepSeekProvider({
                    'intencion': 'recomendar_presupuesto',
                    'tipo_unidad': 'VIVIENDA',
                    'presupuesto_max': 80000,
                    'moneda': 'USD',
                    'amoblamiento_preferido': 'AMOBLADA',
                }),
            )
            assert r['unidades_recomendadas'] == []
            assert r['coincidencias_exactas'] == 0
            assert r['propuesta_proyecto'] is not None
            assert r['propuesta_proyecto']['viable'] is True
            assert len(r['propuesta_proyecto']['escenarios']) == 3
            assert 'CASA-RES' not in r['respuesta']
            assert 'Sin coincidencias disponibles' in r['respuesta']
            assert 'Propuesta Preliminar de Proyecto Personalizado' in r['respuesta']

    def test_multitenant_session_isolation(self):
        """Aislamiento multiempresa: la conversación de empresa 1 no puede reutilizarse en empresa 2."""
        emp1 = {'id_empresa': 1, 'slug': 'emp1', 'nombre_empresa': 'Empresa Uno', 'nit': 1, 'descripcion': ''}
        emp2 = {'id_empresa': 2, 'slug': 'emp2', 'nombre_empresa': 'Empresa Dos', 'nit': 2, 'descripcion': ''}
        with patch('app.repos.commercial_repos.obtener_parametros_estimacion_empresa', return_value=_params_empresa()), \
             patch('app.repos.commercial_repos.listar_unidades_comerciales', return_value=[]):
            with patch('app.repos.commercial_repos.resolver_empresa_comercial', return_value=emp1):
                r1 = cas.procesar_consulta_comercial(
                    1,
                    CommercialChatRequest(mensaje='Quiero una casa de USD 80.000 en zona norte'),
                    provider=_OfflineProvider(),
                )
            with patch('app.repos.commercial_repos.resolver_empresa_comercial', return_value=emp2):
                r2 = cas.procesar_consulta_comercial(
                    2,
                    CommercialChatRequest(mensaje='¿Qué opciones hay?', conversacion_id=r1['conversacion_id']),
                    provider=_OfflineProvider(),
                )
            assert r2['conversacion_id'] != r1['conversacion_id']
            assert r2['criterios_aplicados']['presupuesto_max'] is None
            assert r2['criterios_aplicados']['zona'] is None
