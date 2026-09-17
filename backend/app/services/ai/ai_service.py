from app.services import crm_services
from app.services.ai.context_builder import ContextBuilder
from app.services.ai.gemini_provider import GeminiProvider, GeminiProviderError


SYSTEM_INSTRUCTION_CRM = """Eres el Asistente Inteligente de CRM de OBRATEC, la plataforma de gestión integral de obras civiles y proyectos inmobiliarios.
Tu función es responder preguntas del usuario (Responsable de Proyecto o Administrador) acerca de los prospectos comerciales, clientes, negociaciones, unidades asociadas e interacciones comerciales de su empresa.
Debes ser conciso, profesional, analítico y redactar en español claro. Si se te pregunta una cantidad o porcentaje, preséntala de forma destacada."""


class AIService:
    def __init__(self, provider=None):
        self.provider = provider or GeminiProvider()

    def consultar_crm(self, pregunta: str, token: dict, id_empresa_solicitada=None, ip: str = "unknown") -> dict:
        if not pregunta or not pregunta.strip():
            raise ValueError("La pregunta o consulta no puede estar vacía.")

        # 1. Validar empresa autorizada mediante la misma seguridad multitenant de CRM
        id_empresa = crm_services._empresa(token, id_empresa_solicitada, obligatorio=True)

        # 2. Construir contexto autorizado (HU109)
        contexto = ContextBuilder.construir_contexto_crm(id_empresa)

        # 3. Invocar al proveedor de IA desacoplado
        try:
            respuesta = self.provider.generar_respuesta(
                system_instruction=SYSTEM_INSTRUCTION_CRM,
                user_prompt=pregunta.strip(),
                context_data=contexto
            )
        except GeminiProviderError as exc:
            raise crm_services.CrmError(f"Asistente IA no disponible: {str(exc)}", exc.status_code)

        # 4. Registrar auditoría (Bitácora) de forma segura sin volcar prompts completos
        crm_services._log(
            token=token,
            accion="CONSULTA_IA_CRM",
            descripcion=f"Consulta de IA CRM realizada para empresa ID {id_empresa}.",
            ip=ip,
            estado="EXITOSO"
        )

        return {
            "success": True,
            "pregunta": pregunta.strip(),
            "respuesta": respuesta,
            "empresa_autorizada": contexto.get("empresa_autorizada"),
            "metricas": contexto.get("metricas_crm")
        }


# Instancia singleton lista para usar
ai_service = AIService()
