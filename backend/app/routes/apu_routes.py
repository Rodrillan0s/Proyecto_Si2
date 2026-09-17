from fastapi import APIRouter, Body, Depends, HTTPException, Request
from app.services import apu_services
from app.services.apu_services import ApuError
from app.utils.security import exigir_permiso

router = APIRouter(prefix="/api/apus", tags=["Análisis de Precios Unitarios (APU)"])


def _ip(request: Request):
    return request.client.host if request.client else "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# Categorías y Catálogo Base (OBRATEC)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/categorias")
def get_categorias(token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))):
    try:
        return apu_services.listar_categorias()
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/base")
def get_catalogo_base(
    id_categoria: int = None,
    q: str = None,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    try:
        return apu_services.listar_catalogo_base(id_categoria=id_categoria, q=q)
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/base/{id_apu_base}/copiar")
def post_copiar_apu_base(
    id_apu_base: int,
    request: Request,
    data: dict = Body(None),
    token_data: dict = Depends(exigir_permiso("Registrar_presupuesto"))
):
    try:
        return apu_services.copiar_apu_base(id_apu_base, token_data, _ip(request), data)
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# Mis APUs (Empresa)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/mis-apus")
def get_mis_apus(
    id_categoria: int = None,
    solo_vigentes: bool = False,
    q: str = None,
    id_obra: int = None,
    id_empresa: int = None,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    try:
        return apu_services.listar_mis_apus(
            token_data, id_categoria=id_categoria, solo_vigentes=solo_vigentes,
            q=q, id_obra=id_obra, id_empresa_req=id_empresa
        )
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# Compatibilidad con ruta previa GET /api/apus/
@router.get("/")
def get_apus_default(
    id_categoria: int = None,
    solo_vigentes: bool = False,
    q: str = None,
    id_obra: int = None,
    id_empresa: int = None,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    try:
        return apu_services.listar_mis_apus(
            token_data, id_categoria=id_categoria, solo_vigentes=solo_vigentes,
            q=q, id_obra=id_obra, id_empresa_req=id_empresa
        )
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/siguiente-codigo")
def get_siguiente_codigo(
    id_empresa: int = None,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    try:
        return apu_services.sugerir_codigo_apu(token_data, id_empresa)
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/recursos/materiales")
def get_recursos_materiales(
    q: str = None,
    id_empresa: int = None,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    try:
        return apu_services.listar_materiales_catalogo(token_data, q=q, id_empresa_req=id_empresa)
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/recursos/mano-obra")
def get_recursos_mano_obra(
    q: str = None,
    id_empresa: int = None,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    try:
        return apu_services.listar_mano_obra_catalogo(token_data, q=q, id_empresa_req=id_empresa)
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/recursos/equipos")
def get_recursos_equipos(
    q: str = None,
    id_empresa: int = None,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    try:
        return apu_services.listar_equipos_catalogo(token_data, q=q, id_empresa_req=id_empresa)
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/recursos/unidades-medida")
def get_unidades_medida(token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))):
    try:
        return apu_services.listar_unidades_medida()
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/")
def post_crear_apu(
    request: Request,
    data: dict = Body(...),
    token_data: dict = Depends(exigir_permiso("Registrar_presupuesto"))
):
    try:
        return apu_services.crear_apu_empresa(data, token_data, _ip(request))
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{id_apu}")
def get_detalle_apu(
    id_apu: int,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    try:
        return apu_services.obtener_detalle_apu(id_apu, token_data)
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.put("/{id_apu}")
def put_actualizar_apu(
    id_apu: int,
    request: Request,
    data: dict = Body(...),
    token_data: dict = Depends(exigir_permiso("Modificar_presupuesto"))
):
    try:
        return apu_services.actualizar_apu_empresa(id_apu, data, token_data, _ip(request))
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/{id_apu}/versionar")
def post_versionar_apu(
    id_apu: int,
    request: Request,
    token_data: dict = Depends(exigir_permiso("Modificar_presupuesto"))
):
    try:
        return apu_services.versionar_apu(id_apu, token_data, _ip(request))
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/{id_apu}/duplicar")
def post_duplicar_apu(
    id_apu: int,
    request: Request,
    data: dict = Body(None),
    token_data: dict = Depends(exigir_permiso("Registrar_presupuesto"))
):
    try:
        return apu_services.duplicar_apu(id_apu, token_data, _ip(request), data)
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.patch("/{id_apu}/estado")
def patch_estado_apu(
    id_apu: int,
    request: Request,
    data: dict = Body(...),
    token_data: dict = Depends(exigir_permiso("Modificar_presupuesto"))
):
    try:
        nuevo_estado = data.get("estado", "ACTIVO")
        return apu_services.cambiar_estado_apu(id_apu, nuevo_estado, token_data, _ip(request))
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# Componentes de APU
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{id_apu}/componentes")
def post_componente(
    id_apu: int,
    request: Request,
    data: dict = Body(...),
    token_data: dict = Depends(exigir_permiso("Modificar_presupuesto"))
):
    try:
        return apu_services.agregar_componente(id_apu, data, token_data, _ip(request))
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.put("/{id_apu}/componentes/{id_componente}")
def put_componente(
    id_apu: int,
    id_componente: int,
    request: Request,
    data: dict = Body(...),
    token_data: dict = Depends(exigir_permiso("Modificar_presupuesto"))
):
    try:
        return apu_services.actualizar_componente(id_apu, id_componente, data, token_data, _ip(request))
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.delete("/{id_apu}/componentes/{id_componente}")
def delete_componente(
    id_apu: int,
    id_componente: int,
    request: Request,
    token_data: dict = Depends(exigir_permiso("Modificar_presupuesto"))
):
    try:
        return apu_services.eliminar_componente(id_apu, id_componente, token_data, _ip(request))
    except ApuError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
