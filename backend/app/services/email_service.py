import smtplib
import ssl
from email.message import EmailMessage

from app.config import Config


def _crear_contexto_ssl():
    contexto = ssl.create_default_context()
    if hasattr(ssl, "VERIFY_X509_STRICT"):
        contexto.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return contexto


def _enviar_mensaje(mensaje: EmailMessage):
    if Config.SMTP_USE_SSL:
        with smtplib.SMTP_SSL(
            Config.SMTP_HOST,
            Config.SMTP_PORT,
            timeout=Config.SMTP_TIMEOUT_SECONDS,
            context=_crear_contexto_ssl()
        ) as servidor:
            servidor.login(
                Config.SMTP_USER,
                Config.SMTP_PASSWORD
            )
            servidor.send_message(mensaje)

    else:
        with smtplib.SMTP(
            Config.SMTP_HOST,
            Config.SMTP_PORT,
            timeout=Config.SMTP_TIMEOUT_SECONDS
        ) as servidor:

            if Config.SMTP_USE_TLS:
                servidor.starttls(context=_crear_contexto_ssl())

            servidor.login(
                Config.SMTP_USER,
                Config.SMTP_PASSWORD
            )

            servidor.send_message(mensaje)


def enviar_correo_prueba(destinatario: str):
    mensaje = EmailMessage()

    mensaje["Subject"] = "Prueba SMTP - OBRATEC"
    mensaje["From"] = f"{Config.SMTP_FROM_NAME} <{Config.SMTP_FROM}>"
    mensaje["To"] = destinatario

    mensaje.set_content(
        "Hola.\n\n"
        "Este es un correo de prueba enviado desde OBRATEC.\n\n"
        "Si recibiste este mensaje, la configuración SMTP funciona correctamente."
    )

    _enviar_mensaje(mensaje)


def enviar_codigo_recuperacion(destinatario: str, codigo: str):
    mensaje = EmailMessage()

    mensaje["Subject"] = "Código de recuperación - OBRATEC"
    mensaje["From"] = f"{Config.SMTP_FROM_NAME} <{Config.SMTP_FROM}>"
    mensaje["To"] = destinatario

    mensaje.set_content(
        "Solicitaste recuperar tu contraseña.\n\n"
        "Tu código de recuperación es:\n\n"
        f"{codigo}\n\n"
        "Este código vence en 10 minutos.\n\n"
        "Si no solicitaste este cambio, puedes ignorar este mensaje."
    )

    _enviar_mensaje(mensaje)
