from fastapi import APIRouter, Body, Depends, HTTPException, Request
from app.services.ai.ai_service import ai_service
from app.services import crm_services
from app.utils.security import exigir_permiso


router = APIRouter(tags=["Inteligencia Artificial"])


def _ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/ai/crm/consulta
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/crm/consulta")
def post_consulta_crm(
    request: Request,
    data: dict = Body(...),
    id_empresa: int = None,
    token=Depends(exigir_permiso("Visualizar_clientes")),
):
    pregunta = data.get("pregunta")
    if not pregunta or not str(pregunta).strip():
        raise HTTPException(status_code=400, detail="La pregunta es obligatoria.")

    try:
        return ai_service.consultar_crm(
            pregunta=str(pregunta).strip(),
            token=token,
            id_empresa_solicitada=id_empresa,
            ip=_ip(request)
        )
    except crm_services.CrmError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al procesar la consulta con IA: {str(exc)}")


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/ai/crm/sugerencias
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/crm/sugerencias")
def get_sugerencias(
    token=Depends(exigir_permiso("Visualizar_clientes")),
):
    return {
        "success": True,
        "sugerencias": [
            "¿Cuántos clientes potenciales tenemos registrados actualmente?",
            "¿Cuántos prospectos están en fase de negociación?",
            "¿Cuáles son nuestros clientes o prospectos con mayor presupuesto?",
            "¿Qué unidades inmobiliarias están reservadas o en negociación?",
            "¿Cuál fue la última interacción comercial registrada?",
            "¿Cuántos prospectos se han convertido a clientes comerciales?"
        ]
    }
