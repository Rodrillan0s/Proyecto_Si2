from fastapi import APIRouter, Body, HTTPException, Depends
from app.services import profile_services
from app.utils.security import verificar_token

router = APIRouter(tags=['Perfil'])

@router.get('/')
def get_profile(token_data: dict = Depends(verificar_token)):
    """
    CU09 - Consultar perfil del usuario autenticado.
    El ID del usuario se obtiene EXCLUSIVAMENTE del token JWT validado.
    No se acepta ningún parámetro de usuario desde el frontend.
    No se devuelve: contraseña, hash de contraseña, tokens ni información sensible.
    """
    try:
        nro_usuario = token_data.get('nro_usuario')
        if not nro_usuario:
            raise HTTPException(status_code=401, detail='No se pudo identificar al usuario autenticado.')
        return profile_services.obtener_perfil_usuario(nro_usuario)
    except HTTPException:
        raise
    except ValueError as e:
        error_msg = str(e)
        # Usuario no encontrado
        if 'no se encuentra' in error_msg.lower() or 'no encontrado' in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f'Error interno al consultar el perfil: {err}')


@router.put('/cambiar-password')
def change_password(token_data: dict = Depends(verificar_token), data: dict = Body(...)):
    try:
        nro_usuario = token_data['nro_usuario']
        return profile_services.cambiar_password_usuario(nro_usuario, data)
    except ValueError as e:
        status_code = 404 if str(e) == 'Usuario no encontrado' else 400
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f'Error interno en : {err}')


@router.put('/')
def update_profile(token_data: dict = Depends(verificar_token), data: dict = Body(...)):
    try:
        nro_usuario = token_data.get('nro_usuario')

        return profile_services.actualizar_perfil_usuario(nro_usuario, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error interno en : {err}")
