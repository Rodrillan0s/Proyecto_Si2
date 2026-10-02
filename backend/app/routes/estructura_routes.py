from fastapi import APIRouter, Depends, HTTPException, Request
from app.services import estructura_services
from app.utils.security import exigir_permiso

router = APIRouter(prefix="/api/proyectos/{id_obra}/estructuras", tags=["Estructura de Obra"])

@router.get("/")
def get_estructura_obra(id_obra: int, token_data: dict = Depends(exigir_permiso("Visualizar_obras"))):
    try:
        return estructura_services.listar_estructura(id_obra, token_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/")
def post_elemento_estructura(id_obra: int, data: dict, request: Request, token_data: dict = Depends(exigir_permiso("Modificar_obras"))):
    try:
        client_ip = request.client.host if request.client else "unknown"
        return estructura_services.crear_elemento(id_obra, data, token_data, client_ip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.put("/{id_estructura}")
def put_elemento_estructura(id_obra: int, id_estructura: int, data: dict, request: Request, token_data: dict = Depends(exigir_permiso("Modificar_obras"))):
    try:
        client_ip = request.client.host if request.client else "unknown"
        return estructura_services.actualizar_elemento(id_obra, id_estructura, data, token_data, client_ip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.delete("/{id_estructura}")
def delete_elemento_estructura(id_obra: int, id_estructura: int, request: Request, token_data: dict = Depends(exigir_permiso("Modificar_obras"))):
    try:
        client_ip = request.client.host if request.client else "unknown"
        return estructura_services.eliminar_elemento(id_obra, id_estructura, token_data, client_ip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.put("/{id_estructura}/reordenar")
def reordenar_elemento_estructura(id_obra: int, id_estructura: int, data: dict, request: Request, token_data: dict = Depends(exigir_permiso("Modificar_obras"))):
    try:
        client_ip = request.client.host if request.client else "unknown"
        direccion = data.get("direccion", "UP")
        return estructura_services.reordenar_elemento(id_obra, id_estructura, direccion, token_data, client_ip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
