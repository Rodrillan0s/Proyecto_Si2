"""
Orquestador principal del Asistente Comercial Inteligente y Recomendaciones (CU34).
Cubre HU147, HU148, HU149, HU150, lectura de planos y estimación paramétrica por estilos
utilizando exclusivamente DeepSeek API con Grounding determinista (cero respuestas vagas).
"""
import threading
import time
from uuid import uuid4
from app.repos import commercial_repos
from app.services.ai.providers import ProviderError, get_deepseek_provider
from app.services.commercial import blueprint_vision_service as vision_service
from app.services.commercial import commercial_query_engine as query_engine
from app.services.commercial import cost_estimation_service as cost_service
from app.services.commercial import lead_capture_service as lead_service
from app.services.commercial.contracts import (
    CommercialChatRequest,
    CommercialSearchCriteria,
    CostEstimationRequest,
    LeadContactRequest,
)

_SESSION_LOCK = threading.Lock()
_SESSIONS: dict[str, dict] = {}
SESSION_TTL_SECONDS = 3600  # 1 hora
MAX_SESSIONS = 1500

SYSTEM_PROMPT_INTENT = """Eres el motor de análisis semántico comercial de OBRATEC.
Extrae los criterios exactos de búsqueda inmobiliaria del cliente potencial.
Devuelve EXCLUSIVAMENTE un objeto JSON válido con estas claves:
{
  "intencion": "buscar_unidades | recomendar_presupuesto | comparar_unidades | estimar_costo | solicitar_contacto",
  "tipo_unidad": "DEPARTAMENTO | VIVIENDA | LOCAL | LOTE | OFICINA | null",
  "min_dormitorios": null,
  "min_banos": null,
  "superficie_min_m2": null,
  "superficie_max_m2": null,
  "presupuesto_max": null,
  "moneda": "BOB | USD",
  "zona": null,
  "estilo_acabado": "ESTANDAR | MINIMALISTA | INDUSTRIAL | CONTEMPORANEO | LUJO | null",
  "estado_construccion": "PLANIFICADO | EN_CONSTRUCCION | FINALIZADO | null",
  "caracteristicas_deseadas": []
}"""

SYSTEM_PROMPT_SYNTHESIS = """Eres el Asesor Comercial Inmobiliario Senior y Arquitecto Consultor de {nombre_empresa} en la plataforma OBRATEC.
REGLAS ESTRICTAS DE RESPUESTA (CERO RESPUESTAS VAGAS):
1. Responde de forma ejecutiva, cálida, estructurada y 100% fundamentada en los DATOS VERIFICADOS provistos.
2. Menciona SIEMPRE códigos reales de unidad (ej. UNI-000001), nombres de proyecto/obra, superficies exactas en m², precios en BOB y USD, y estado de disponibilidad.
3. Jamás inventes unidades, descuentos, ubicaciones ni precios que no estén en el bloque de datos verificados.
4. Si el cliente consulta costos o estilos, presenta con claridad el costo por m², el presupuesto total estimado y las diferencias de materiales entre estilos.
5. Finaliza con una invitación consultiva concreta (comparar unidades, cotizar otro estilo de acabado o agendar contacto con un asesor)."""


def _get_or_create_session(id_empresa: int, conversacion_id: str | None) -> dict:
    now = time.time()
    with _SESSION_LOCK:
        # Limpiar sesiones expiradas si supera el umbral
        if len(_SESSIONS) > MAX_SESSIONS:
            expired = [k for k, v in _SESSIONS.items() if now - v['updated_at'] > SESSION_TTL_SECONDS]
            for k in expired:
                _SESSIONS.pop(k, None)

        if conversacion_id and conversacion_id in _SESSIONS:
            sess = _SESSIONS[conversacion_id]
            # Aislamiento estricto: jamás reutilizar sesión de otra empresa
            if sess['id_empresa'] == id_empresa and (now - sess['updated_at'] <= SESSION_TTL_SECONDS):
                sess['updated_at'] = now
                return sess

        new_id = str(uuid4())
        sess = {
            'conversacion_id': new_id,
            'id_empresa': id_empresa,
            'created_at': now,
            'updated_at': now,
            'historial': [],
            'criterios_previos': {},
            'ultimas_unidades_vistas': [],
            'ultima_consulta': '',
        }
        _SESSIONS[new_id] = sess
        return sess


def _heredar_criterios_conversacion(actual: CommercialSearchCriteria, previos: dict) -> CommercialSearchCriteria:
    if not previos:
        return actual
    data = actual.model_dump()
    for campo in ('tipo_unidad', 'min_dormitorios', 'min_banos', 'presupuesto_max', 'zona', 'estilo_acabado'):
        if data.get(campo) is None and previos.get(campo) is not None:
            data[campo] = previos[campo]
            if campo == 'presupuesto_max' and previos.get('moneda'):
                data['moneda'] = previos['moneda']
    return CommercialSearchCriteria(**data)


def _construir_respuesta_determinista(
    empresa: dict,
    intencion: str,
    criterios: CommercialSearchCriteria,
    resultado_busqueda: dict,
    comparativa: dict | None,
    estimacion_costo: dict | None,
    registro_crm: dict | None,
    requiere_datos_contacto: bool,
) -> str:
    """
    Construye una respuesta comercial estructurada, exacta y sin vaguedades
    con los datos deterministas verificados del backend.
    """
    lineas = []
    nombre_emp = empresa['nombre_empresa']

    if registro_crm and registro_crm.get('registrado'):
        lineas.append(f"### Solicitud de Contacto Comercial Registrada ({nombre_emp})")
        lineas.append(registro_crm['mensaje_confirmacion'])
        if registro_crm.get('unidades_vinculadas'):
            cods = ', '.join(f"**{u['codigo']}** ({u['nombre']} - {u['obra']})" for u in registro_crm['unidades_vinculadas'])
            lineas.append(f"- **Unidades vinculadas a tu expediente:** {cods}")
        return '\n\n'.join(lineas)

    if requiere_datos_contacto:
        lineas.append(f"### Atención Comercial Personalizada — {nombre_emp}")
        lineas.append(
            "Con gusto asignaremos un asesor comercial para atenderte de inmediato y coordinar una visita o cotización formal."
        )
        lineas.append(
            "Por favor completa tu **Nombre completo** y tu número de **WhatsApp / Teléfono** (o correo electrónico) en el formulario de contacto o escríbelos directamente aquí."
        )

    if intencion == 'comparar_unidades' and comparativa and comparativa.get('unidades'):
        lineas.append(f"### Comparativa Técnica y Comercial de Alternativas ({nombre_emp})")
        res = comparativa.get('resumen_comparativo') or {}
        if res.get('opcion_mas_economica'):
            eco = res['opcion_mas_economica']
            lineas.append(
                f"- **Menor inversión total:** **{eco['codigo_unidad']} ({eco['nombre_unidad']})** con **{eco['precio_usd']} USD** ({eco['precio_bob']} BOB)."
            )
        if res.get('opcion_mas_amplia'):
            amp = res['opcion_mas_amplia']
            lineas.append(
                f"- **Mayor superficie construida:** **{amp['codigo_unidad']} ({amp['nombre_unidad']})** con **{amp['superficie_m2']} m²**."
            )
        if res.get('mejor_relacion_m2'):
            m2 = res['mejor_relacion_m2']
            lineas.append(
                f"- **Mejor costo por m²:** **{m2['codigo_unidad']}** a **{m2['costo_m2_usd']} USD/m²** ({m2['costo_m2_bob']} BOB/m²)."
            )
        for u in comparativa['unidades']:
            ventajas_txt = '; '.join(u.get('ventajas_competitivas') or [])
            lineas.append(
                f"1. **{u['codigo_unidad']} — {u['nombre_unidad']}** (*{u['nombre_obra']}*)\n"
                f"   - **Superficie y Programa:** {u['superficie_m2']} m² | {u['dormitorios']} dorm. | {u['banos']} baño(s) | Acabado `{u['especificacion_acabado']}`\n"
                f"   - **Precio y Disponibilidad:** **{u['precio_usd']} USD** ({u['precio_bob']} BOB) — Estado: `{u['disponibilidad_comercial']}` ({u['estado_construccion']})\n"
                f"   - **Diferencial:** {ventajas_txt}"
            )
        return '\n\n'.join(lineas)

    if estimacion_costo:
        p_ent = estimacion_costo['parametros_entrada']
        r_fin = estimacion_costo['resumen_financiero']
        lineas.append(
            f"### Estimación Paramétrica de Costo y Estilo — {p_ent['estilo_nombre']} ({p_ent['superficie_m2']} m²)"
        )
        lineas.append(
            f"- **Inversión Total Estimada:** **{r_fin['total_estimado_usd']} USD** (**{r_fin['total_estimado_bob']} BOB**)\n"
            f"- **Valor Unitario Ajustado:** **{r_fin['costo_m2_ajustado_usd']} USD/m²** ({r_fin['costo_m2_ajustado_bob']} BOB/m²)\n"
            f"- **Configuración Evaluada:** {p_ent['tipo_inmueble']} de {p_ent['superficie_m2']} m², {p_ent['cantidad_plantas']} planta(s), {p_ent['dormitorios']} dormitorio(s) y {p_ent['banos']} baño(s)."
        )
        desglose_txt = '\n'.join(
            f"  - **{c['capitulo']} ({c['porcentaje']}):** {c['monto_usd']} USD ({c['monto_bob']} BOB)"
            for c in estimacion_costo['desglose_capitulos']
        )
        lineas.append(f"**Desglose por Capítulos Constructivos:**\n{desglose_txt}")
        eval_p = estimacion_costo.get('evaluacion_presupuesto')
        if eval_p:
            if eval_p['alcanza_presupuesto']:
                lineas.append(
                    f"- **Análisis frente a tu presupuesto ({eval_p['presupuesto_cliente_usd']} USD):** Cubre satisfactoriamente el proyecto con un margen favorable de **{eval_p['diferencia_usd']} USD** ({eval_p['diferencia_bob']} BOB)."
                )
            else:
                lineas.append(
                    f"- **Análisis frente a tu presupuesto ({eval_p['presupuesto_cliente_usd']} USD):** Requiere una inversión adicional de **{abs(float(eval_p['diferencia_usd'])):.2f} USD**, o bien ajustar la superficie a **{eval_p['superficie_maxima_recomendada_m2']} m²** manteniendo el mismo estilo."
                )

    recomendadas = resultado_busqueda.get('unidades_recomendadas') or []
    exactas = resultado_busqueda.get('coincidencias_exactas', 0)

    if recomendadas:
        encabezado = (
            f"### Unidades Recomendadas en {nombre_emp} ({exactas} coincidencia(s) exacta(s))"
            if exactas > 0
            else f"### Alternativas Más Cercanas en {nombre_emp} según tus Criterios"
        )
        lineas.append(encabezado)
        for idx, u in enumerate(recomendadas[:4], start=1):
            razones_str = ' · '.join(u.get('razones_recomendacion') or [])
            obs_str = (
                f"\n   - *Nota comercial:* {' | '.join(u['observaciones_criterio'])}"
                if u.get('observaciones_criterio')
                else ''
            )
            lineas.append(
                f"{idx}. **{u['codigo_unidad']} — {u['nombre_unidad']}** (Proyecto: *{u['nombre_obra']}*)\n"
                f"   - **Características:** {u['tipo_unidad']} | **{u['superficie_m2']} m²** | {u['ambientes_resumen']} | Acabado `{u['especificacion_acabado']}`\n"
                f"   - **Valor Comercial:** **{u['precio_usd']} USD** (**{u['precio_bob']} BOB** · {u['costo_m2_usd']} USD/m²) — `{u['disponibilidad_comercial']}`\n"
                f"   - **Por qué te conviene (Afinidad {u['afinidad_score']}%):** {razones_str}{obs_str}"
            )
    elif not estimacion_costo and not requiere_datos_contacto:
        lineas.append(
            f"Actualmente **{nombre_emp}** no registra unidades disponibles que coincidan con esos filtros exactos en el inventario activo. "
            "Puedes consultar nuestra estimación paramétrica por m² y estilo o dejarnos tus datos para notificarte de nuevos lanzamientos."
        )

    return '\n\n'.join(lineas)


def obtener_catalogo_inicial_comercial(id_empresa: int) -> dict:
    """
    Devuelve el resumen del portafolio comercial de la empresa, sus unidades enriquecidas,
    modelos tipológicos y estilos de acabado disponibles para el portal de clientes.
    """
    empresa = commercial_repos.resolver_empresa_comercial(id_empresa)
    if not empresa:
        raise ValueError(f"La empresa ID {id_empresa} no existe.")

    datos_parametros = commercial_repos.obtener_parametros_estimacion_empresa(id_empresa)
    unidades_raw = commercial_repos.listar_unidades_comerciales(id_empresa)
    modelos = commercial_repos.listar_modelos_comerciales(id_empresa)

    resultado = query_engine.filtrar_y_recomendar_unidades(
        unidades_raw=unidades_raw,
        datos_parametros=datos_parametros,
        criterios=CommercialSearchCriteria(solo_disponibles=False),
        top_k=12,
    )

    estilos = [
        {
            'codigo': cod,
            'nombre': meta['nombre'],
            'factor_referencial': str(meta['factor_default']),
            'acabados_incluidos': meta['acabados_incluidos'],
        }
        for cod, meta in cost_service.ESTILOS_CATALOGO.items()
    ]

    return {
        'empresa': empresa,
        'resumen_inventario': {
            'total_unidades': resultado['total_inventario_empresa'],
            'unidades_disponibles': resultado['total_disponibles_evaluadas'],
            'total_modelos': len(modelos),
        },
        'unidades_destacadas': resultado['unidades_recomendadas'],
        'modelos': modelos,
        'estilos_acabado': estilos,
        'preguntas_sugeridas': [
            '¿Qué departamentos o viviendas tienen disponibles actualmente?',
            'Tengo un presupuesto de 85.000 USD, ¿qué opciones me recomiendan?',
            'Compárame las 3 mejores unidades disponibles en relación precio y superficie',
            '¿Cuánto cuesta construir o personalizar 110 m² en estilo Minimalista vs Lujo?',
            'Quiero que un asesor comercial me contacte para agendar una visita',
        ],
    }


def procesar_consulta_comercial(
    id_empresa: int,
    solicitud: CommercialChatRequest,
    provider=None,
) -> dict:
    """
    Procesa una consulta en lenguaje natural del cliente potencial (CU34: HUs 147, 148, 149, 150 + costos).
    """
    empresa = commercial_repos.resolver_empresa_comercial(id_empresa)
    if not empresa:
        raise ValueError(f"La empresa ID {id_empresa} no existe.")

    sesion = _get_or_create_session(id_empresa, solicitud.conversacion_id)
    ai_provider = provider or get_deepseek_provider()

    # 1. Pre-extracción determinista local
    criterios_base = query_engine.extraer_criterios_locales(
        mensaje=solicitud.mensaje,
        presupuesto_max=solicitud.presupuesto_max,
        moneda=solicitud.moneda,
        tipo_unidad_preferido=solicitud.tipo_unidad_preferido,
        estilo_preferido=solicitud.estilo_preferido,
        min_dormitorios=solicitud.min_dormitorios,
        ids_unidades_comparar=solicitud.ids_unidades_comparar,
    )

    # 2. Enriquecimiento estructurado con DeepSeek JSON Mode (si está disponible)
    llm_criterios = None
    try:
        llm_criterios = ai_provider.chat_structured(
            system=SYSTEM_PROMPT_INTENT,
            prompt=solicitud.mensaje,
            context={'criterios_previos': sesion['criterios_previos']},
            history=sesion['historial'][-4:],
        )
    except ProviderError:
        llm_criterios = None

    criterios = query_engine.combinar_criterios(criterios_base, llm_criterios)
    criterios = _heredar_criterios_conversacion(criterios, sesion['criterios_previos'])

    # 3. Cargar inventario real y parámetros de la empresa autorizada
    datos_parametros = commercial_repos.obtener_parametros_estimacion_empresa(id_empresa)
    unidades_raw = commercial_repos.listar_unidades_comerciales(id_empresa)

    resultado_busqueda = query_engine.filtrar_y_recomendar_unidades(
        unidades_raw=unidades_raw,
        datos_parametros=datos_parametros,
        criterios=criterios,
        top_k=6,
    )

    intencion = criterios.intencion
    comparativa = None
    estimacion_costo = None
    registro_crm = None
    requiere_datos_contacto = False

    # 4. Ejecutar motores específicos según la intención detectada
    if solicitud.contacto is not None:
        intencion = 'solicitar_contacto'
        registro_crm = lead_service.registrar_solicitud_contacto(
            id_empresa=id_empresa,
            solicitud=solicitud.contacto,
            contexto_conversacion=sesion,
        )
    elif intencion == 'solicitar_contacto':
        extraidos = lead_service.extraer_datos_contacto_de_texto(solicitud.mensaje)
        if extraidos['nombre_completo'] and extraidos['tiene_medio_contacto']:
            req_lead = LeadContactRequest(
                nombre_completo=extraidos['nombre_completo'],
                telefono=extraidos['telefono'],
                email=extraidos['email'],
                presupuesto_estimado=criterios.presupuesto_max,
                moneda=criterios.moneda,
                unidades_interes=sesion['ultimas_unidades_vistas'][:3],
                notas=solicitud.mensaje,
                conversacion_id=sesion['conversacion_id'],
            )
            registro_crm = lead_service.registrar_solicitud_contacto(
                id_empresa=id_empresa,
                solicitud=req_lead,
                contexto_conversacion=sesion,
            )
        else:
            requiere_datos_contacto = True

    if intencion == 'comparar_unidades':
        ids_comp = list(criterios.ids_unidades_comparar or [])
        if not ids_comp and not criterios.codigos_comparar:
            ids_comp = list(sesion['ultimas_unidades_vistas'][:3])
        comparativa = query_engine.comparar_alternativas_inmobiliarias(
            unidades_enriquecidas=resultado_busqueda['todas_enriquecidas'],
            ids_solicitud=ids_comp,
            codigos_solicitud=criterios.codigos_comparar,
            candidatas_fallback=resultado_busqueda['unidades_recomendadas'],
        )

    if intencion == 'estimar_costo' or criterios.estilo_acabado is not None:
        sup_calculo = (
            criterios.superficie_min_m2
            or criterios.superficie_max_m2
            or (
                resultado_busqueda['unidades_recomendadas'][0]['superficie_m2_num']
                if resultado_busqueda['unidades_recomendadas']
                else 90.0
            )
        )
        estimacion_costo = cost_service.estimar_costo_constructivo(
            id_empresa=id_empresa,
            superficie_m2=sup_calculo,
            tipo_inmueble=criterios.tipo_unidad or 'DEPARTAMENTO',
            estilo_acabado=criterios.estilo_acabado or 'MINIMALISTA',
            cantidad_plantas=1,
            dormitorios=criterios.min_dormitorios or 2,
            banos=criterios.min_banos or 2,
            presupuesto_objetivo=criterios.presupuesto_max,
            moneda_objetivo=criterios.moneda,
            incluir_parqueo='parqueo' in (criterios.caracteristicas_deseadas or []),
            incluir_baulera='baulera' in (criterios.caracteristicas_deseadas or []),
            datos_parametros=datos_parametros,
        )

    # 5. Construir respuesta fundamentada (Síntesis DeepSeek sobre datos verificados o fallback determinista)
    respuesta_base = _construir_respuesta_determinista(
        empresa=empresa,
        intencion=intencion,
        criterios=criterios,
        resultado_busqueda=resultado_busqueda,
        comparativa=comparativa,
        estimacion_costo=estimacion_costo,
        registro_crm=registro_crm,
        requiere_datos_contacto=requiere_datos_contacto,
    )

    respuesta_final = respuesta_base
    try:
        contexto_verificado = {
            'empresa': empresa['nombre_empresa'],
            'intencion_resuelta': intencion,
            'criterios_aplicados': criterios.model_dump(),
            'unidades_recomendadas': [
                {
                    'id_unidad': u['id_unidad'],
                    'codigo': u['codigo_unidad'],
                    'nombre': u['nombre_unidad'],
                    'obra': u['nombre_obra'],
                    'tipo': u['tipo_unidad'],
                    'superficie_m2': u['superficie_m2'],
                    'ambientes': u['ambientes_resumen'],
                    'precio_bob': u['precio_bob'],
                    'precio_usd': u['precio_usd'],
                    'costo_m2_usd': u['costo_m2_usd'],
                    'disponibilidad': u['disponibilidad_comercial'],
                    'estado_construccion': u['estado_construccion'],
                    'afinidad_score': u['afinidad_score'],
                    'razones': u['razones_recomendacion'],
                }
                for u in resultado_busqueda['unidades_recomendadas'][:4]
            ],
            'comparativa': comparativa,
            'estimacion_costo': estimacion_costo['resumen_financiero'] if estimacion_costo else None,
            'comparativa_estilos': estimacion_costo['comparativa_estilos'] if estimacion_costo else None,
            'registro_crm': registro_crm,
            'requiere_datos_contacto': requiere_datos_contacto,
        }
        sintesis_llm = ai_provider.complete(
            system=SYSTEM_PROMPT_SYNTHESIS.format(nombre_empresa=empresa['nombre_empresa']),
            prompt=solicitud.mensaje,
            context=contexto_verificado,
        )
        if sintesis_llm and len(sintesis_llm.strip()) > 30:
            respuesta_final = sintesis_llm.strip()
    except ProviderError:
        respuesta_final = respuesta_base

    # 6. Actualizar estado de sesión conversacional
    with _SESSION_LOCK:
        sesion['ultima_consulta'] = solicitud.mensaje
        sesion['criterios_previos'] = {
            k: v
            for k, v in criterios.model_dump().items()
            if v is not None and v != [] and k not in ('intencion', 'codigos_comparar', 'ids_unidades_comparar')
        }
        if resultado_busqueda['unidades_recomendadas']:
            sesion['ultimas_unidades_vistas'] = [
                u['id_unidad'] for u in resultado_busqueda['unidades_recomendadas'][:4]
            ]
        sesion['historial'].append({'role': 'user', 'content': solicitud.mensaje})
        sesion['historial'].append({'role': 'assistant', 'content': respuesta_final[:1200]})
        sesion['historial'] = sesion['historial'][-10:]

    return {
        'success': True,
        'conversacion_id': sesion['conversacion_id'],
        'empresa': empresa,
        'intencion': intencion,
        'criterios_aplicados': criterios.model_dump(),
        'respuesta': respuesta_final,
        'resumen_estructurado': respuesta_base,
        'unidades_recomendadas': resultado_busqueda['unidades_recomendadas'],
        'coincidencias_exactas': resultado_busqueda['coincidencias_exactas'],
        'comparativa': comparativa,
        'estimacion_costo': estimacion_costo,
        'registro_crm': registro_crm,
        'requiere_datos_contacto': requiere_datos_contacto,
    }


def ejecutar_estimacion_directa(id_empresa: int, req: CostEstimationRequest) -> dict:
    empresa = commercial_repos.resolver_empresa_comercial(id_empresa)
    if not empresa:
        raise ValueError(f"La empresa ID {id_empresa} no existe.")

    estimacion = cost_service.estimar_costo_constructivo(
        id_empresa=id_empresa,
        superficie_m2=req.superficie_m2,
        tipo_inmueble=req.tipo_inmueble,
        estilo_acabado=req.estilo_acabado,
        cantidad_plantas=req.cantidad_plantas,
        dormitorios=req.dormitorios,
        banos=req.banos,
        presupuesto_objetivo=req.presupuesto_objetivo,
        moneda_objetivo=req.moneda,
        incluir_parqueo=req.incluir_parqueo,
        incluir_baulera=req.incluir_baulera,
        incluir_domotica=req.incluir_domotica,
    )
    return {
        'success': True,
        'empresa': empresa,
        'estimacion': estimacion,
    }


def procesar_plano_comercial(
    id_empresa: int,
    image_bytes: bytes,
    mensaje_cliente: str = '',
    presupuesto_max: float | None = None,
    moneda: str = 'BOB',
    estilo_preferido: str | None = None,
    conversacion_id: str | None = None,
    provider=None,
) -> dict:
    empresa = commercial_repos.resolver_empresa_comercial(id_empresa)
    if not empresa:
        raise ValueError(f"La empresa ID {id_empresa} no existe.")

    sesion = _get_or_create_session(id_empresa, conversacion_id)
    resultado_plano = vision_service.analizar_plano_y_cotizar(
        id_empresa=id_empresa,
        image_bytes=image_bytes,
        mensaje_cliente=mensaje_cliente,
        presupuesto_max=presupuesto_max,
        moneda=moneda,
        estilo_preferido=estilo_preferido,
        provider=provider,
    )

    lectura = resultado_plano['lectura_plano']
    est = resultado_plano['estimacion_costo']
    r_fin = est['resumen_financiero']
    unidades_sim = resultado_plano['unidades_similares_disponibles']

    amb_str = ', '.join(
        f"{a.get('cantidad', 1)}x {a.get('nombre')} (~{a.get('superficie_aprox_m2', 10)} m²)"
        for a in lectura['ambientes_detectados']
    )
    respuesta_texto = (
        f"### Radiografía Técnica de tu Plano y Cotización ({empresa['nombre_empresa']})\n\n"
        f"- **Tipología y Superficie Estimada:** `{lectura['tipo_inmueble_detectado']}` de **{lectura['superficie_estimada_m2']} m²** en {lectura['cantidad_plantas']} planta(s) (Confianza: `{lectura['nivel_confianza']}`).\n"
        f"- **Programa de Ambientes Detectado:** {amb_str}.\n"
        f"- **Distribución Espacial:** {lectura['distribucion_observada']}\n"
        f"- **Presupuesto Constructivo Estimado ({est['parametros_entrada']['estilo_nombre']}):** **{r_fin['total_estimado_usd']} USD** (**{r_fin['total_estimado_bob']} BOB** a razón de {r_fin['costo_m2_usd']} USD/m²).\n"
        f"- **Recomendación Técnica:** {lectura['recomendacion_arquitectonica']}"
    )
    if unidades_sim:
        u_top = unidades_sim[0]
        respuesta_texto += (
            f"\n\n**Equivalencia en nuestro Catálogo:** Tu plano guarda alta afinidad con nuestra unidad **{u_top['codigo_unidad']} ({u_top['nombre_unidad']})** en *{u_top['nombre_obra']}* ({u_top['superficie_m2']} m², valor **{u_top['precio_usd']} USD**)."
        )

    with _SESSION_LOCK:
        if unidades_sim:
            sesion['ultimas_unidades_vistas'] = [u['id_unidad'] for u in unidades_sim[:4]]
        sesion['ultima_consulta'] = f"[Análisis de Plano {lectura['superficie_estimada_m2']} m²] {mensaje_cliente}"

    return {
        'success': True,
        'conversacion_id': sesion['conversacion_id'],
        'empresa': empresa,
        'respuesta': respuesta_texto,
        **resultado_plano,
    }

