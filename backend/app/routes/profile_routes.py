from fastapi import APIRouter,Body,HTTPException,Depends
from app.services import profile_services
from app.utils.security import verificar_token

router=APIRouter(tags=['Perfil'])

@router.get('/')
def get_profile(token_data:dict = Depends(verificar_token)):
    try:
        nro_usuario=token_data.get('nro_usuario')
        return profile_services.obtener_perfil_usuario(nro_usuario)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error interno en : {err}")

@router.put('/cambiar-password')
def change_password(token_data:dict = Depends(verificar_token), data:dict = Body(...)):
    try:
        nro_usuario=token_data['nro_usuario']
        return profile_services.cambiar_password_usuario(nro_usuario, data)
    except ValueError as e:
        status_code = 404 if str(e) == 'Usuario no encontrado' else 400
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error interno en : {err}")
    

@router.put('/')
def update_profile(token_data:dict=Depends(verificar_token),data:dict=Body(...)):
    try:
        nro_usuario=token_data.get('nro_usuario')

        return profile_services.actualizar_perfil_usuario(nro_usuario,data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error interno en : {err}")