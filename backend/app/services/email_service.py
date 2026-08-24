import requests

from app.config import Config


BREVO_EMAIL_URL = "https://api.brevo.com/v3/smtp/email"


def _enviar_mensaje(destinatario: str, asunto: str, contenido: str):
    if not Config.BREVO_API_KEY:
        raise RuntimeError("Falta configurar la API key de Brevo")

    if not Config.BREVO_SENDER_EMAIL:
        raise RuntimeError("Falta configurar el email remitente de Brevo")

    headers = {
        "api-key": Config.BREVO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "sender": {
            "name": Config.BREVO_SENDER_NAME,
            "email": Config.BREVO_SENDER_EMAIL,
        },
        "to": [{"email": destinatario}],
        "subject": asunto,
        "textContent": contenido,
    }

    try:
        respuesta = requests.post(
            BREVO_EMAIL_URL,
            headers=headers,
            json=payload,
            timeout=Config.BREVO_TIMEOUT_SECONDS,
        )
    except requests.exceptions.Timeout as exc:
        raise RuntimeError("Timeout al conectar con Brevo") from exc
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError("Error de conexión con Brevo") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError("Error al enviar el correo mediante Brevo") from exc

    if respuesta.status_code == 201:
        return

    if 200 <= respuesta.status_code < 300:
        try:
            respuesta_json = respuesta.json()
        except ValueError as exc:
            raise RuntimeError(
                f"Brevo respondió HTTP {respuesta.status_code} sin confirmar el envío"
            ) from exc

        if isinstance(respuesta_json, dict) and respuesta_json.get("messageId"):
            return

        raise RuntimeError(
            f"Brevo respondió HTTP {respuesta.status_code} sin confirmar el envío"
        )

    if respuesta.status_code == 429:
        raise RuntimeError("Brevo alcanzó temporalmente el límite de solicitudes")

    if respuesta.status_code in {400, 401, 403, 422}:
        raise RuntimeError(f"Brevo rechazó la solicitud con HTTP {respuesta.status_code}")

    if 500 <= respuesta.status_code < 600:
        raise RuntimeError(
            f"El servicio de Brevo no está disponible (HTTP {respuesta.status_code})"
        )

    raise RuntimeError(f"Respuesta inesperada de Brevo: HTTP {respuesta.status_code}")


def enviar_correo_prueba(destinatario: str):
    contenido = (
        "Hola.\n\n"
        "Este es un correo de prueba enviado desde OBRATEC.\n\n"
        "Si recibiste este mensaje, la configuración de Brevo funciona correctamente."
    )

    _enviar_mensaje(destinatario, "Prueba de correo - OBRATEC", contenido)


def enviar_codigo_recuperacion(destinatario: str, codigo: str):
    contenido = (
        "Solicitaste recuperar tu contraseña de OBRATEC.\n\n"
        "Tu código de recuperación es:\n\n"
        f"{codigo}\n\n"
        "Este código vence en 10 minutos.\n\n"
        "Si no solicitaste este cambio, puedes ignorar este mensaje."
    )

    _enviar_mensaje(
        destinatario,
        "Código de recuperación - OBRATEC",
        contenido,
    )
