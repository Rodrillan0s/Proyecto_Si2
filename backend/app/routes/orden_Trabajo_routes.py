from fastapi import APIRouter, Depends, HTTPException, Request

from app.services import orden_Trabajo_services

from app.utils.security import exigir_permiso

router = APIRouter(
    prefix="/api/ordenes-trabajo",
    tags=["Órdenes de Trabajo"]
)


@router.get("/")
def get_ordenes_trabajo(
    id_empresa: int = None,
    id_obra: int = None,
    token_data: dict = Depends(exigir_permiso("Visualizar_ordenes_trabajo"))
):
    try:
        return orden_Trabajo_services.listar_ordenes_trabajo(
            token_data,
            id_empresa=id_empresa,
            id_obra=id_obra
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )


@router.get("/{orden_nro}")
def get_orden_trabajo(
    orden_nro: int,
    token_data: dict = Depends(exigir_permiso("Visualizar_ordenes_trabajo"))
):
    try:
        return orden_Trabajo_services.obtener_orden_trabajo(
            orden_nro,
            token_data
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )


@router.post("/")
def post_orden_trabajo(
    data: dict,
    request: Request,
    token_data: dict = Depends(exigir_permiso("Modificar_ordenes_trabajo"))
):
    try:
        client_ip = request.client.host if request.client else "unknown"

        return orden_Trabajo_services.crear_orden_trabajo(
            data,
            token_data,
            client_ip
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )


@router.put("/{orden_nro}")
def put_orden_trabajo(
    orden_nro: int,
    data: dict,
    request: Request,
    token_data: dict = Depends(exigir_permiso("Modificar_ordenes_trabajo"))
):
    try:
        client_ip = request.client.host if request.client else "unknown"

        return orden_Trabajo_services.actualizar_orden_trabajo(
            orden_nro,
            data,
            token_data,
            client_ip
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )


@router.delete("/{orden_nro}")
def delete_orden_trabajo(
    orden_nro: int,
    request: Request,
    token_data: dict = Depends(exigir_permiso("Modificar_ordenes_trabajo"))
):
    try:
        client_ip = request.client.host if request.client else "unknown"

        return orden_Trabajo_services.eliminar_orden_trabajo(
            orden_nro,
            token_data,
            client_ip
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )


@router.put("/{orden_nro}/estado")
def put_estado_orden_trabajo(
    orden_nro: int,
    data: dict,
    request: Request,
    token_data: dict = Depends(exigir_permiso("Modificar_ordenes_trabajo"))
):
    try:
        client_ip = request.client.host if request.client else "unknown"

        return orden_Trabajo_services.actualizar_estado_orden_trabajo(
            orden_nro,
            data,
            token_data,
            client_ip
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )


@router.get("/{orden_nro}/historial")
def get_historial_orden_trabajo(
    orden_nro: int,
    token_data: dict = Depends(exigir_permiso("Visualizar_ordenes_trabajo"))
):
    try:
        return orden_Trabajo_services.listar_historial_orden_trabajo(
            orden_nro,
            token_data
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

@router.get("/{orden_nro}/responsables")
def get_responsables_orden_trabajo(
    orden_nro: int,
    token_data: dict = Depends(
        exigir_permiso("Visualizar_ordenes_trabajo")
    )
):
    try:
        return orden_Trabajo_services.listar_responsables_orden_trabajo(
            orden_nro,
            token_data
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )


@router.post("/{orden_nro}/responsables")
def post_responsable_orden_trabajo(
    orden_nro: int,
    data: dict,
    request: Request,
    token_data: dict = Depends(
        exigir_permiso("Modificar_ordenes_trabajo")
    )
):
    try:
        client_ip = request.client.host if request.client else "unknown"

        return orden_Trabajo_services.asignar_responsable_orden_trabajo(
            orden_nro,
            data,
            token_data,
            client_ip
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )


@router.delete("/{orden_nro}/responsables/{id_usuario}")
def delete_responsable_orden_trabajo(
    orden_nro: int,
    id_usuario: int,
    request: Request,
    token_data: dict = Depends(
        exigir_permiso("Modificar_ordenes_trabajo")
    )
):
    try:
        client_ip = request.client.host if request.client else "unknown"

        return orden_Trabajo_services.eliminar_responsable_orden_trabajo(
            orden_nro,
            id_usuario,
            token_data,
            client_ip
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )    