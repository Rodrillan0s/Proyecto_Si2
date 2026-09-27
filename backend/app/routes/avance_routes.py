"""
Router CU18 – Avances de Obra
Endpoints REST para el registro y consulta de avances de obra.

Prefijo base: /api/proyectos/{id_obra}/avances
Permisos utilizados:
  - Visualizar_avances → GET
  - Registrar_avances  → POST / DELETE
"""
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request

from app.services import avance_services
from app.utils.security import exigir_permiso

router = APIRouter(
    prefix="/api/proyectos/{id_obra}/avances",
    tags=["Avances de Obra (CU18)"],
)


def _ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/proyectos/{id_obra}/avances/
#   Historial completo de avances. Filtrado opcional por ?id_unidad=N
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/")
def get_avances(
    id_obra: int,
    id_unidad: int = Query(default=None, description="Filtrar por unidad de construcción"),
    token_data: dict = Depends(exigir_permiso("Visualizar_avances")),
):
    try:
        return avance_services.listar_avances(id_obra, token_data, id_unidad)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/proyectos/{id_obra}/avances/resumen
#   Resumen de avance global del proyecto + último avance por unidad
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/resumen")
def get_resumen_avances(
    id_obra: int,
    token_data: dict = Depends(exigir_permiso("Visualizar_avances")),
):
    try:
        return avance_services.resumen_avances(id_obra, token_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/proyectos/{id_obra}/avances/
#   Registrar un nuevo avance de obra
#   Body: { id_unidad, porcentaje_avance, fecha_registro?, observacion? }
# ──────────────────────────────────────────────────────────────────────────────
@router.post("/")
def post_avance(
    id_obra: int,
    request: Request,
    data: dict = Body(...),
    token_data: dict = Depends(exigir_permiso("Registrar_avances")),
):
    if not data:
        raise HTTPException(status_code=400, detail="El cuerpo de la petición está vacío.")
    try:
        return avance_services.registrar_avance(id_obra, data, token_data, _ip(request))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ──────────────────────────────────────────────────────────────────────────────
# DELETE /api/proyectos/{id_obra}/avances/{id_avance}
#   Elimina un avance registrado (solo quien tenga Registrar_avances)
# ──────────────────────────────────────────────────────────────────────────────
@router.delete("/{id_avance}")
def delete_avance(
    id_obra: int,
    id_avance: int,
    request: Request,
    token_data: dict = Depends(exigir_permiso("Registrar_avances")),
):
    try:
        return avance_services.eliminar_avance(id_obra, id_avance, token_data, _ip(request))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
