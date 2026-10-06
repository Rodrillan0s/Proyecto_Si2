from fastapi import APIRouter, Depends, HTTPException, Request

from app.services import equipos_maquinaria_services

from app.utils.security import exigir_permiso


router = APIRouter(
    prefix="/api/equipos-maquinaria",
    tags=["Equipos y Maquinaria"]
)


@router.get("/")
def listar_equipos_maquinaria(
    tipo: str = '',
    estado: str = '',
    token_data: dict = Depends(
        exigir_permiso("Visualizar_equipos_maquinaria")
    )
):
    try:
        return equipos_maquinaria_services.listar_equipos_maquinaria(
            token_data=token_data,
            tipo=tipo,
            estado=estado
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/")
def registrar_equipo_maquinaria(
    data: dict,
    request: Request,
    token_data: dict = Depends(
        exigir_permiso("Modificar_equipos_maquinaria")
    )
):
    try:
        client_ip = (
            request.client.host
            if request.client
            else "unknown"
        )

        return equipos_maquinaria_services.registrar_equipo_maquinaria(
            data=data,
            token_data=token_data,
            client_ip=client_ip
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# ASIGNACIONES
# ============================================================

@router.get("/asignaciones/")
def listar_asignaciones_equipo_maquinaria(
    id_obra: int = None,
    id_equipo_maquinaria: int = None,
    estado: str = '',
    token_data: dict = Depends(
        exigir_permiso("Visualizar_equipos_maquinaria")
    )
):
    try:
        return equipos_maquinaria_services.listar_asignaciones_equipo_maquinaria(
            token_data=token_data,
            id_obra=id_obra,
            id_equipo_maquinaria=id_equipo_maquinaria,
            estado=estado
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/asignaciones/{id_asignacion}")
def obtener_asignacion_equipo_maquinaria(
    id_asignacion: int,
    token_data: dict = Depends(
        exigir_permiso("Visualizar_equipos_maquinaria")
    )
):
    try:
        return equipos_maquinaria_services.obtener_asignacion_equipo_maquinaria(
            id_asignacion=id_asignacion,
            token_data=token_data
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/asignaciones/")
def asignar_equipo_maquinaria(
    data: dict,
    request: Request,
    token_data: dict = Depends(
        exigir_permiso("Modificar_equipos_maquinaria")
    )
):
    try:
        client_ip = (
            request.client.host
            if request.client
            else "unknown"
        )

        return equipos_maquinaria_services.asignar_equipo_maquinaria(
            data=data,
            token_data=token_data,
            client_ip=client_ip
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.put("/asignaciones/{id_asignacion}/retirar")
def retirar_equipo_maquinaria(
    id_asignacion: int,
    data: dict,
    request: Request,
    token_data: dict = Depends(
        exigir_permiso("Modificar_equipos_maquinaria")
    )
):
    try:
        client_ip = (
            request.client.host
            if request.client
            else "unknown"
        )

        return equipos_maquinaria_services.retirar_equipo_maquinaria(
            id_asignacion=id_asignacion,
            data=data,
            token_data=token_data,
            client_ip=client_ip
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# EQUIPOS Y MAQUINARIA
# ============================================================

@router.get("/{id_equipo_maquinaria}")
def obtener_equipo_maquinaria(
    id_equipo_maquinaria: int,
    token_data: dict = Depends(
        exigir_permiso("Visualizar_equipos_maquinaria")
    )
):
    try:
        return equipos_maquinaria_services.obtener_equipo_maquinaria(
            id_equipo_maquinaria=id_equipo_maquinaria,
            token_data=token_data
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.put("/{id_equipo_maquinaria}")
def actualizar_equipo_maquinaria(
    id_equipo_maquinaria: int,
    data: dict,
    request: Request,
    token_data: dict = Depends(
        exigir_permiso("Modificar_equipos_maquinaria")
    )
):
    try:
        client_ip = (
            request.client.host
            if request.client
            else "unknown"
        )

        return equipos_maquinaria_services.actualizar_equipo_maquinaria(
            id_equipo_maquinaria=id_equipo_maquinaria,
            data=data,
            token_data=token_data,
            client_ip=client_ip
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.put("/{id_equipo_maquinaria}/estado")
def actualizar_estado_equipo_maquinaria(
    id_equipo_maquinaria: int,
    data: dict,
    request: Request,
    token_data: dict = Depends(
        exigir_permiso("Modificar_equipos_maquinaria")
    )
):
    try:
        client_ip = (
            request.client.host
            if request.client
            else "unknown"
        )

        return equipos_maquinaria_services.actualizar_estado_equipo_maquinaria(
            id_equipo_maquinaria=id_equipo_maquinaria,
            data=data,
            token_data=token_data,
            client_ip=client_ip
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )