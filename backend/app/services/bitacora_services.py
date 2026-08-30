from datetime import date

from app.repos import bitacora_repos


def registrar_evento_bitacora(id_usuario, modulo, accion, descripcion, ip, estado):
    return bitacora_repos.registrar_evento_bitacora(
        id_usuario=id_usuario,
        modulo=modulo,
        accion=accion,
        descripcion=descripcion,
        ip=ip,
        estado=estado,
    )


def consultar_bitacora(fecha=None, id_usuario=None, usuario=None, accion=None, page=1, limit=20, id_empresa=None, es_admin_sistema=False):
    if fecha is not None:
        try:
            date.fromisoformat(fecha)
        except ValueError as exc:
            raise ValueError("El filtro 'fecha' debe tener formato YYYY-MM-DD.") from exc

    if id_usuario is not None and id_usuario <= 0:
        raise ValueError("El filtro 'id_usuario' debe ser mayor que cero.")
    if page < 1:
        raise ValueError("El parámetro 'page' debe ser mayor que cero.")
    if limit < 1 or limit > 100:
        raise ValueError("El parámetro 'limit' debe estar entre 1 y 100.")
    if not es_admin_sistema and id_empresa is None:
        raise ValueError("No se pudo determinar la empresa del usuario autenticado.")

    resultado = bitacora_repos.obtener_bitacora(
        fecha=fecha,
        id_usuario=id_usuario,
        usuario=usuario.strip() if usuario else None,
        accion=accion.strip() if accion else None,
        page=page,
        limit=limit,
        id_empresa=id_empresa,
        es_admin_sistema=es_admin_sistema,
    )
    total = resultado["total"]

    return {
        "success": True,
        "data": resultado["rows"],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
        },
    }