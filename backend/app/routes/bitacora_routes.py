from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.services import bitacora_services
from app.utils.security import exigir_rol

router = APIRouter(tags=["Bitácora"])


@router.get("")
def get_bitacora(
    fecha: Optional[str] = Query(default=None, description="Fecha en formato YYYY-MM-DD"),
    id_usuario: Optional[int] = Query(default=None, description="ID del usuario"),
    usuario: Optional[str] = Query(default=None, description="Nombre de usuario o nombre completo"),
    accion: Optional[str] = Query(default=None, description="Tipo o texto de la acción"),
    page: int = Query(default=1, description="Número de página"),
    limit: int = Query(default=20, description="Registros por página; máximo 100"),
    token_data: dict = Depends(exigir_rol("ADMINISTRADOR")),
):
    try:
        return bitacora_services.consultar_bitacora(
            fecha=fecha,
            id_usuario=id_usuario,
            usuario=usuario,
            accion=accion,
            page=page,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        print(f"ERROR CONSULTANDO BITÁCORA: {exc}")
        raise HTTPException(status_code=500, detail="No se pudo consultar la bitácora.") from exc