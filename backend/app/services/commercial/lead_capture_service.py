"""
Servicio de captura y calificación de prospectos comerciales hacia el CRM (HU150 - CU34).
"""
import re
from decimal import Decimal, ROUND_HALF_UP
from app.repos import commercial_repos
from app.services.commercial.contracts import LeadContactRequest
from app.services.commercial.cost_estimation_service import TIPO_CAMBIO_BOB_USD

_EMAIL_RE = re.compile(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)')
_PHONE_RE = re.compile(r'(?:\+?591[\s-]?)?([67]\d{7}|\d{7,12})')


def extraer_datos_contacto_de_texto(mensaje: str) -> dict:
    """
    Detecta si el cliente potencial proporcionó nombre, teléfono/WhatsApp o correo
    directamente en un mensaje de texto conversacional.
    """
    txt = str(mensaje or '').strip()
    email_match = _EMAIL_RE.search(txt)
    email = email_match.group(1) if email_match else None

    phone_match = _PHONE_RE.search(txt)
    telefono = phone_match.group(1) if phone_match else None

    nombre = None
    m_nombre = re.search(
        r'(?:me llamo|mi nombre es|soy)\s+([A-ZÁÉÍÓÚÑa-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑa-záéíóúñ]+){1,3})',
        txt,
        flags=re.IGNORECASE,
    )
    if m_nombre:
        candidato = m_nombre.group(1).strip()
        # Evitar falsos positivos como "soy un cliente interesado"
        palabras_excluidas = {'cliente', 'interesado', 'interesada', 'inversionista', 'comprador'}
        if not any(w in candidato.lower().split() for w in palabras_excluidas):
            nombre = candidato.title()

    return {
        'nombre_completo': nombre,
        'telefono': telefono,
        'email': email,
        'tiene_medio_contacto': bool(telefono or email),
    }


def registrar_solicitud_contacto(
    id_empresa: int,
    solicitud: LeadContactRequest,
    contexto_conversacion: dict | None = None,
    id_usuario_solicitante: int | None = None,
) -> dict:
    """
    Valida y registra formalmente el interés del cliente potencial en el CRM de la empresa.
    """
    nombre = str(solicitud.nombre_completo or '').strip()
    if len(nombre) < 2:
        raise ValueError('Por favor indique su nombre completo para registrar la solicitud de contacto.')

    telefono = str(solicitud.telefono or '').strip() or None
    email = str(solicitud.email or '').strip() or None
    ci = str(solicitud.ci or '').strip() or None

    if not telefono and not email:
        raise ValueError('Debe proporcionar al menos un número de teléfono/WhatsApp o correo electrónico.')

    if email and not _EMAIL_RE.fullmatch(email):
        raise ValueError('El formato del correo electrónico proporcionado no es válido.')

    presupuesto_bob = None
    if solicitud.presupuesto_estimado is not None and solicitud.presupuesto_estimado > 0:
        p_dec = Decimal(str(solicitud.presupuesto_estimado))
        if str(solicitud.moneda or 'BOB').strip().upper() == 'USD':
            presupuesto_bob = (p_dec * TIPO_CAMBIO_BOB_USD).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            presupuesto_bob = p_dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    unidades_ids = list(solicitud.unidades_interes or [])
    if not unidades_ids and contexto_conversacion:
        unidades_ids = list(contexto_conversacion.get('ultimas_unidades_vistas') or [])[:3]

    partes_nota = []
    if solicitud.notas:
        partes_nota.append(solicitud.notas.strip())
    if solicitud.horario_preferido:
        partes_nota.append(f"Horario preferido: {solicitud.horario_preferido.strip()}")
    if solicitud.presupuesto_estimado:
        partes_nota.append(f"Presupuesto declarado: {solicitud.presupuesto_estimado} {solicitud.moneda}")
    if contexto_conversacion and contexto_conversacion.get('ultima_consulta'):
        partes_nota.append(f"Última consulta en asistente: {contexto_conversacion['ultima_consulta']}")

    notas_consolidadas = ' | '.join(partes_nota) if partes_nota else 'Solicitud de contacto registrada desde Asistente Comercial IA (CU34).'

    resultado_crm = commercial_repos.registrar_lead_comercial_transaccional(
        id_empresa=id_empresa,
        nombre_completo=nombre,
        telefono=telefono,
        email=email,
        ci=ci,
        presupuesto_estimado=presupuesto_bob,
        notas=notas_consolidadas,
        unidades_interes=unidades_ids,
        resumen_interaccion=notas_consolidadas,
    )

    try:
        from app.services import notificaciones_services
        medio_str = telefono or email or ''
        cuerpo_notif = f"Prospecto {nombre} ({medio_str}) registrado en CRM (#CRM-{resultado_crm['id_cliente']})."
        if solicitud.notas:
            cuerpo_notif += f" Nota: {solicitud.notas.strip()}"
        notificaciones_services.emitir_notificacion_push_empresa(
            titulo=f"Nuevo prospecto comercial: {nombre}",
            cuerpo=cuerpo_notif,
            tipo_referencia="CRM_PROSPECTO",
            id_empresa=id_empresa,
            nro_referencia=resultado_crm['id_cliente'],
            roles_destino=[
                "ADMINISTRADOR",
                "ADMINISTRADOR_EMPRESA",
                "JEFE DE OBRA",
                "SUPERVISOR_OBRA",
                "CLIENTE",
            ],
            usuarios_especificos=[id_usuario_solicitante] if id_usuario_solicitante else None,
        )
    except Exception as exc:
        print(f"[WARN] Error al emitir push de prospecto CRM: {exc}")

    return {
        'registrado': True,
        'id_cliente_crm': resultado_crm['id_cliente'],
        'es_nuevo_prospecto': resultado_crm['es_nuevo_prospecto'],
        'estado_crm': resultado_crm['estado'],
        'asesor_asignado': resultado_crm['asesor_asignado'],
        'unidades_vinculadas': resultado_crm['unidades_vinculadas'],
        'id_interaccion': resultado_crm['id_interaccion'],
        'mensaje_confirmacion': (
            f"¡Solicitud registrada con éxito (#CRM-{resultado_crm['id_cliente']})! "
            f"Nuestro asesor comercial ({resultado_crm['asesor_asignado']}) se pondrá en contacto "
            f"contigo a la brevedad vía {'WhatsApp/teléfono ' + telefono if telefono else 'correo ' + email}."
        ),
    }
