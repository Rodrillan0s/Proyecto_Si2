import json
import time
import requests
from app.config import Config


class GeminiProviderError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class GeminiProvider:
    """
    Proveedor desacoplado para invocar la API de Google Gemini vía HTTPS REST.
    Permite ser reemplazado o extendido sin modificar la lógica del CRM ni de OBRATEC.
    """

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.model = model or Config.GEMINI_MODEL or "gemini-flash-latest"
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def generar_respuesta(self, system_instruction: str, user_prompt: str, context_data: dict = None) -> str:
        if not self.api_key:
            raise GeminiProviderError(
                "La API Key de Gemini no está configurada en el backend (GEMINI_API_KEY).", 500
            )

        context_str = json.dumps(context_data, ensure_ascii=False, indent=2) if context_data else "{}"

        prompt_combinado = f"""{system_instruction}

--- CONTEXTO DE DATOS AUTORIZADOS DE LA EMPRESA (VERIFICADO POR EL BACKEND) ---
{context_str}
--------------------------------------------------------------------------------

PREGUNTA DEL USUARIO:
{user_prompt}

INSTRUCCIÓN CRÍTICA DE RESPUESTA:
- Responde de forma precisa, ejecutiva, profesional y en lenguaje natural en español.
- Basa tu respuesta ÚNICAMENTE en la información autorizada provista en el contexto anterior.
- Si la información solicitada no está presente en el contexto, indica amablemente que no dispones de esos datos en el sistema.
- Jamás inventes clientes, números o unidades que no figuren en los datos provistos.
"""

        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key,
        }

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt_combinado}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.8,
                "maxOutputTokens": 800,
            }
        }

        for intento in range(3):
            try:
                resp = requests.post(self.endpoint, json=payload, headers=headers, timeout=15)
                if resp.status_code == 503 and intento < 2:
                    time.sleep(1.5 * (intento + 1))
                    continue

                if resp.status_code != 200:
                    error_detail = resp.text
                    try:
                        err_json = resp.json()
                        error_detail = err_json.get("error", {}).get("message", error_detail)
                    except Exception:
                        pass
                    raise GeminiProviderError(f"Error al consultar Gemini API ({resp.status_code}): {error_detail}")

                data = resp.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    return "No se pudo generar una respuesta a partir de los datos provistos."

                parts = candidates[0].get("content", {}).get("parts") or []
                if not parts:
                    return "Respuesta vacía recibida del asistente."

                return parts[0].get("text", "").strip()

            except requests.Timeout:
                if intento < 2:
                    time.sleep(1.0)
                    continue
                raise GeminiProviderError("Tiempo de espera agotado al comunicarse con el asistente de IA.", 504)
            except requests.RequestException as exc:
                if intento < 2:
                    time.sleep(1.0)
                    continue
                raise GeminiProviderError(f"Error de conexión con el servicio de IA: {str(exc)}", 502)

