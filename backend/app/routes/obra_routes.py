from fastapi import APIRouter, Body, HTTPException, Depends, Request
from app.services import obra_services
from app.utils.security import exigir_permiso

router = APIRouter(tags=["Proyectos"])

@router.get('/')
def get_proyectos(token_data: dict = Depends(exigir_permiso('Visualizar_obras'))):
    try:
        return obra_services.listar_obras(token_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get('/tipos')
def get_tipos_proyecto(token_data: dict = Depends(exigir_permiso('Visualizar_obras'))):
    try:
        return obra_services.obtener_tipos_proyecto()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get('/siguiente-codigo')
def get_siguiente_codigo(token_data: dict = Depends(exigir_permiso('Registrar_obras'))):
    try:
        id_empresa = token_data.get('id_empresa')
        return {"success": True, "codigo": obra_services.generar_siguiente_codigo(id_empresa)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get('/{id_obra}')
def get_proyecto_detalle(id_obra: int, token_data: dict = Depends(exigir_permiso('Visualizar_obras'))):
    try:
        return obra_services.obtener_obra_detalle(id_obra, token_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post('/')
def create_proyecto(request: Request, data: dict = Body(...), token_data: dict = Depends(exigir_permiso('Registrar_obras'))):
    if not data:
        raise HTTPException(status_code=400, detail='El cuerpo de la petición está vacío.')
    
    try:
        client_ip = request.client.host if request.client else "unknown"
        return obra_services.registrar_obra(data, token_data, client_ip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno en BD: {str(e)}")

@router.put('/{id_obra}')
def update_proyecto(id_obra: int, request: Request, data: dict = Body(...), token_data: dict = Depends(exigir_permiso('Modificar_obras'))):
    if not data:
        raise HTTPException(status_code=400, detail='El cuerpo de la petición está vacío.')
        
    try:
        client_ip = request.client.host if request.client else "unknown"
        return obra_services.actualizar_obra(id_obra, data, token_data, client_ip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno en BD: {str(e)}")

@router.patch('/{id_obra}/estado')
def update_proyecto_estado(id_obra: int, request: Request, data: dict = Body(...), token_data: dict = Depends(exigir_permiso('Modificar_obras'))):
    nuevo_estado = data.get('estado_obra')
    if not nuevo_estado:
        raise HTTPException(status_code=400, detail="El campo 'estado_obra' es obligatorio.")
        
    try:
        client_ip = request.client.host if request.client else "unknown"
        return obra_services.actualizar_estado_obra(id_obra, nuevo_estado, token_data, client_ip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno en BD: {str(e)}")

@router.post('/{id_obra}/responsables')
def assign_proyecto_responsable(id_obra: int, request: Request, data: dict = Body(...), token_data: dict = Depends(exigir_permiso('Modificar_obras'))):
    id_usuario = data.get('id_usuario')
    if not id_usuario:
        raise HTTPException(status_code=400, detail="El campo 'id_usuario' es obligatorio.")
        
    try:
        client_ip = request.client.host if request.client else "unknown"
        return obra_services.asignar_responsable(id_obra, id_usuario, token_data, client_ip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno en BD: {str(e)}")

@router.delete('/{id_obra}/responsables/{id_usuario}')
def remove_proyecto_responsable(id_obra: int, id_usuario: int, request: Request, token_data: dict = Depends(exigir_permiso('Modificar_obras'))):
    try:
        client_ip = request.client.host if request.client else "unknown"
        return obra_services.retirar_responsable(id_obra, id_usuario, token_data, client_ip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno en BD: {str(e)}")
