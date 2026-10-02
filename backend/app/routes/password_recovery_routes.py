from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.services import password_recovery_services


router = APIRouter(tags=["Recuperación de contraseña"])


class SolicitarRecuperacionRequest(BaseModel):
    correo: EmailStr


class VerificarCodigoRequest(BaseModel):
    solicitud_id: str
    codigo: str


class RestablecerPasswordRequest(BaseModel):
    solicitud_id: str
    reset_token: str
    password_nueva: str
    confirmar_password: str


@router.post("/recuperar-password/solicitar")
def solicitar_recuperacion(data: SolicitarRecuperacionRequest):
    try:
        return password_recovery_services.solicitar_recuperacion(
            str(data.correo)
        )
    except password_recovery_services.PasswordRecoveryServiceUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                password_recovery_services.MENSAJE_SERVICIO_NO_DISPONIBLE
            ),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo procesar la solicitud.",
        )


@router.post("/recuperar-password/verificar")
def verificar_codigo(data: VerificarCodigoRequest):
    try:
        return password_recovery_services.verificar_codigo(
            data.solicitud_id,
            data.codigo,
        )
    except password_recovery_services.CodigoRecuperacionInvalidoError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_recovery_services.MENSAJE_CODIGO_INVALIDO,
        )
    except password_recovery_services.PasswordRecoveryServiceUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                password_recovery_services.MENSAJE_SERVICIO_NO_DISPONIBLE
            ),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo verificar el código de recuperación.",
        )


@router.post("/recuperar-password/restablecer")
def restablecer_password(data: RestablecerPasswordRequest):
    try:
        return password_recovery_services.restablecer_password(
            data.solicitud_id,
            data.reset_token,
            data.password_nueva,
            data.confirmar_password,
        )
    except password_recovery_services.PasswordRecuperacionInvalidoError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.public_message,
        )
    except password_recovery_services.ResetTokenInvalidoError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_recovery_services.MENSAJE_TOKEN_INVALIDO,
        )
    except password_recovery_services.PasswordRecoveryServiceUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                password_recovery_services.MENSAJE_SERVICIO_NO_DISPONIBLE
            ),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo restablecer la contraseña.",
        )
