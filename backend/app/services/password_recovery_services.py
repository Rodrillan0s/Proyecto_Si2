from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import re
import secrets
from threading import RLock
from uuid import UUID, uuid4

from werkzeug.security import generate_password_hash

from app.config import Config
from app.repos import password_recovery_repos
from app.services import email_service
from app.utils import security


MENSAJE_SOLICITUD_GENERICO = (
    "Si el correo está registrado, recibirás un código de recuperación."
)
MENSAJE_CODIGO_INVALIDO = "El código es inválido o ha expirado."
MENSAJE_TOKEN_INVALIDO = (
    "La solicitud de restablecimiento es inválida o ha expirado."
)
MENSAJE_SERVICIO_NO_DISPONIBLE = (
    "No se pudo procesar la solicitud en este momento."
)

_DURACION_CODIGO = timedelta(minutes=10)
_DURACION_RESET_TOKEN = timedelta(minutes=15)
_MAXIMO_INTENTOS = 5

_recuperaciones = {}
_recuperaciones_lock = RLock()


class CodigoRecuperacionInvalidoError(Exception):
    pass


class ResetTokenInvalidoError(Exception):
    pass


class PasswordRecuperacionInvalidoError(Exception):
    def __init__(self, public_message: str):
        super().__init__()
        self.public_message = public_message


class PasswordRecoveryServiceUnavailableError(Exception):
    pass


def _ahora_utc():
    return datetime.now(timezone.utc)


def _obtener_secreto_hmac():
    secreto = Config.RECOVERY_CODE_SECRET
    if not isinstance(secreto, str) or not secreto:
        raise PasswordRecoveryServiceUnavailableError()
    return secreto.encode("utf-8")


def _normalizar_solicitud_id(solicitud_id: str):
    try:
        return str(UUID(str(solicitud_id)))
    except (TypeError, ValueError, AttributeError):
        return None


def _crear_codigo_hmac(
    solicitud_id: str,
    id_usuario: int,
    codigo: str,
    secreto: bytes,
):
    mensaje = (
        f"OBRATEC|CU08|codigo|v1|{solicitud_id}|{id_usuario}|{codigo}"
    )
    return hmac.new(
        secreto,
        mensaje.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _eliminar_expiradas_bajo_lock(ahora: datetime):
    for solicitud_id, recuperacion in list(_recuperaciones.items()):
        if not recuperacion["verificado"]:
            expirada = recuperacion["fecha_expiracion"] <= ahora
        else:
            token_expiracion = recuperacion.get("reset_token_expiracion")
            expirada = token_expiracion is None or token_expiracion <= ahora

        if expirada:
            _recuperaciones.pop(solicitud_id, None)


def _invalidar_recuperaciones_usuario_bajo_lock(id_usuario: int):
    for solicitud_id, recuperacion in list(_recuperaciones.items()):
        if recuperacion["id_usuario"] == id_usuario:
            _recuperaciones.pop(solicitud_id, None)


def _usuario_valido(usuario: dict):
    estado = str(usuario.get("estado") or "").strip().upper()
    correo = usuario.get("correo")
    return (
        isinstance(usuario.get("id_usuario"), int)
        and isinstance(correo, str)
        and bool(correo.strip())
        and estado == "ACTIVO"
    )


def _respuesta_solicitud(solicitud_id: str):
    return {
        "success": True,
        "message": MENSAJE_SOLICITUD_GENERICO,
        "solicitud_id": solicitud_id,
    }


def solicitar_recuperacion(correo: str):
    solicitud_id = str(uuid4())
    correo_normalizado = correo.strip().lower()
    secreto = _obtener_secreto_hmac()

    try:
        usuarios = password_recovery_repos.buscar_usuarios_por_correo(
            correo_normalizado
        )
    except password_recovery_repos.PasswordRecoveryRepositoryError as exc:
        raise PasswordRecoveryServiceUnavailableError() from exc

    if len(usuarios) != 1 or not _usuario_valido(usuarios[0]):
        return _respuesta_solicitud(solicitud_id)

    usuario = usuarios[0]
    id_usuario = usuario["id_usuario"]
    codigo = f"{secrets.randbelow(1_000_000):06d}"
    codigo_hmac = _crear_codigo_hmac(
        solicitud_id,
        id_usuario,
        codigo,
        secreto,
    )

    ahora = _ahora_utc()
    with _recuperaciones_lock:
        _eliminar_expiradas_bajo_lock(ahora)
        _invalidar_recuperaciones_usuario_bajo_lock(id_usuario)
        _recuperaciones[solicitud_id] = {
            "solicitud_id": solicitud_id,
            "id_usuario": id_usuario,
            "codigo_hmac": codigo_hmac,
            "fecha_expiracion": ahora + _DURACION_CODIGO,
            "intentos_fallidos": 0,
            "verificado": False,
            "reset_token_hash": None,
            "reset_token_expiracion": None,
        }

    try:
        email_service.enviar_codigo_recuperacion(
            usuario["correo"].strip(),
            codigo,
        )
    except Exception:
        with _recuperaciones_lock:
            _recuperaciones.pop(solicitud_id, None)

    return _respuesta_solicitud(solicitud_id)


def _registrar_intento_fallido_bajo_lock(
    solicitud_id: str,
    recuperacion: dict,
):
    recuperacion["intentos_fallidos"] += 1
    if recuperacion["intentos_fallidos"] >= _MAXIMO_INTENTOS:
        _recuperaciones.pop(solicitud_id, None)


def verificar_codigo(solicitud_id: str, codigo: str):
    solicitud_id_normalizado = _normalizar_solicitud_id(solicitud_id)
    secreto = _obtener_secreto_hmac()
    ahora = _ahora_utc()

    with _recuperaciones_lock:
        _eliminar_expiradas_bajo_lock(ahora)
        recuperacion = _recuperaciones.get(solicitud_id_normalizado)

        if recuperacion is None or recuperacion["verificado"]:
            raise CodigoRecuperacionInvalidoError()

        if recuperacion["intentos_fallidos"] >= _MAXIMO_INTENTOS:
            _recuperaciones.pop(solicitud_id_normalizado, None)
            raise CodigoRecuperacionInvalidoError()

        codigo_valido = isinstance(codigo, str) and bool(
            re.fullmatch(r"\d{6}", codigo)
        )

        if codigo_valido:
            codigo_hmac_esperado = _crear_codigo_hmac(
                solicitud_id_normalizado,
                recuperacion["id_usuario"],
                codigo,
                secreto,
            )
            codigo_valido = hmac.compare_digest(
                codigo_hmac_esperado,
                recuperacion["codigo_hmac"],
            )

        if not codigo_valido:
            _registrar_intento_fallido_bajo_lock(
                solicitud_id_normalizado,
                recuperacion,
            )
            raise CodigoRecuperacionInvalidoError()

        reset_token = secrets.token_urlsafe(32)
        recuperacion["verificado"] = True
        recuperacion["codigo_hmac"] = None
        recuperacion["reset_token_hash"] = hashlib.sha256(
            reset_token.encode("utf-8")
        ).hexdigest()
        recuperacion["reset_token_expiracion"] = (
            ahora + _DURACION_RESET_TOKEN
        )

    return {
        "success": True,
        "reset_token": reset_token,
    }


def _validar_password_cu04(
    password_nueva: str,
    confirmar_password: str,
):
    passwords = (password_nueva, confirmar_password)
    if any(
        not isinstance(password, str) or not password
        for password in passwords
    ):
        raise PasswordRecuperacionInvalidoError(
            "La nueva contraseña y su confirmación son obligatorias."
        )

    if password_nueva != confirmar_password:
        raise PasswordRecuperacionInvalidoError(
            "Las contraseñas no coinciden."
        )

    if not security.password_cumple_requisitos(password_nueva):
        raise PasswordRecuperacionInvalidoError(
            "La nueva contraseña no cumple los requisitos de seguridad."
        )


def restablecer_password(
    solicitud_id: str,
    reset_token: str,
    password_nueva: str,
    confirmar_password: str,
):
    _validar_password_cu04(password_nueva, confirmar_password)

    solicitud_id_normalizado = _normalizar_solicitud_id(solicitud_id)
    ahora = _ahora_utc()

    with _recuperaciones_lock:
        _eliminar_expiradas_bajo_lock(ahora)
        recuperacion = _recuperaciones.get(solicitud_id_normalizado)

        if (
            recuperacion is None
            or not recuperacion["verificado"]
            or recuperacion["reset_token_hash"] is None
            or recuperacion["reset_token_expiracion"] is None
            or recuperacion["reset_token_expiracion"] <= ahora
            or not isinstance(reset_token, str)
            or not reset_token
        ):
            raise ResetTokenInvalidoError()

        reset_token_hash = hashlib.sha256(
            reset_token.encode("utf-8")
        ).hexdigest()
        if not hmac.compare_digest(
            reset_token_hash,
            recuperacion["reset_token_hash"],
        ):
            raise ResetTokenInvalidoError()

        password_hash = generate_password_hash(password_nueva)
        try:
            password_actualizado = password_recovery_repos.actualizar_password(
                recuperacion["id_usuario"],
                password_hash,
            )
        except password_recovery_repos.PasswordRecoveryRepositoryError as exc:
            raise PasswordRecoveryServiceUnavailableError() from exc

        if not password_actualizado:
            raise PasswordRecoveryServiceUnavailableError()

        _recuperaciones.pop(solicitud_id_normalizado, None)

    return {
        "success": True,
        "message": "Contraseña restablecida correctamente.",
    }
