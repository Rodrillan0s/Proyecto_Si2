from fastapi import APIRouter, Body, Depends, HTTPException, Request, Query
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from app.services.ai.ai_service import ai_service
from app.services import crm_services
from app.utils.security import exigir_permiso
from app.utils.security import verificar_token
from app.services.reportes.contracts import AssistantRequest
from app.services import reportes_services


router = APIRouter(tags=["Inteligencia Artificial"])


class OperationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id_propuesta: UUID


@router.post('/consulta')
def consulta(data: AssistantRequest, id_empresa: int = None, token=Depends(verificar_token)):
    return reportes_services.assistant(token, data, id_empresa)


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
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo completar la consulta. Intente nuevamente.")


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


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/ai/operacion/confirmar
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/operacion/confirmar")
def post_confirmar_operacion(
    request: Request,
    data: OperationRequest,
    id_empresa: int | None = Query(None, gt=0),
    id_obra_contexto: int | None = Query(None, gt=0),
    token=Depends(verificar_token),
):
    from app.services.ai.assistant_operations import ejecutar_propuesta
    return ejecutar_propuesta(token, str(data.id_propuesta), ip=_ip(request), empresa=id_empresa,
                               id_obra_contexto=id_obra_contexto)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/ai/operacion/cancelar (M4)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/operacion/cancelar")
def post_cancelar_operacion(
    request: Request,
    data: OperationRequest,
    id_empresa: int | None = Query(None, gt=0),
    id_obra_contexto: int | None = Query(None, gt=0),
    token=Depends(verificar_token),
):
    from app.services.ai.assistant_operations import cancelar_propuesta
    return cancelar_propuesta(token, str(data.id_propuesta), ip=_ip(request), empresa=id_empresa,
                              id_obra_contexto=id_obra_contexto)
