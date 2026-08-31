from datetime import date
from decimal import Decimal, InvalidOperation

from app.repos import bitacora_repos, material_repos


ESTADOS = {"ACTIVO", "INACTIVO"}
PROHIBIDOS_EDICION = {"cantidad_actual", "cantidad_inicial", "id_material", "id_empresa", "estado"}


class MaterialError(ValueError):
    def __init__(self, message, status_code=400):
        super().__init__(message); self.status_code = status_code


def _empresa(token):
    value = token.get("id_empresa")
    if not value:
        raise MaterialError("El token no identifica una empresa.", 403)
    return value


def _numero(value, campo, obligatorio=True):
    if value is None and not obligatorio: return None
    if isinstance(value, bool): raise MaterialError(f"{campo} debe ser un número válido.")
    try: parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError): raise MaterialError(f"{campo} debe ser un número válido.")
    if not parsed.is_finite() or parsed < 0: raise MaterialError(f"{campo} no puede ser negativo.")
    return parsed


def _validar(data, creando):
    if not isinstance(data, dict): raise MaterialError("El cuerpo debe ser un objeto válido.")
    if not creando:
        invalidos = PROHIBIDOS_EDICION.intersection(data)
        if invalidos: raise MaterialError("No se permite modificar: " + ", ".join(sorted(invalidos)) + ".")
    result = dict(data)
    for key, label in (("codigo","El código"),("nombre_material","El nombre")):
        result[key] = str(data.get(key) or "").strip()
        if not result[key]: raise MaterialError(f"{label} es obligatorio.")
    result["descripcion"] = str(data.get("descripcion") or "").strip() or None
    for key, table, label in (("id_categoria","t_categoria_material","La categoría"),
                              ("id_unidad_medida","t_unidad_medida","La unidad de medida")):
        try: result[key] = int(data.get(key))
        except (TypeError, ValueError): raise MaterialError(f"{label} es obligatoria.")
        if result[key] <= 0 or not material_repos.referencia_activa(table, result[key]):
            raise MaterialError(f"{label} no existe o está inactiva.", 404)
    result["precio"] = _numero(data.get("precio"), "El precio", obligatorio=False)
    result["stock_minimo"] = _numero(data.get("stock_minimo"), "El stock mínimo")
    chars = data.get("caracteristicas", [])
    if not isinstance(chars, list): raise MaterialError("Las características deben ser una lista.")
    seen = set(); result["caracteristicas"] = []
    for item in chars:
        if not isinstance(item, dict): raise MaterialError("Cada característica debe ser un objeto.")
        nombre, valor = str(item.get("nombre") or "").strip(), str(item.get("valor") or "").strip()
        if not nombre or not valor: raise MaterialError("Cada característica debe tener nombre y valor.")
        if nombre.casefold() in seen: raise MaterialError(f"La característica '{nombre}' está duplicada.")
        seen.add(nombre.casefold()); result["caracteristicas"].append({"nombre":nombre,"valor":valor})
    if creando:
        result["cantidad_inicial"] = _numero(data.get("cantidad_inicial"), "La cantidad inicial")
        try: result["fecha_ingreso"] = date.fromisoformat(str(data.get("fecha_ingreso")))
        except (ValueError, TypeError): raise MaterialError("La fecha de ingreso debe tener formato YYYY-MM-DD.")
    return result


def _log(token, accion, descripcion, ip):
    bitacora_repos.registrar_bitacora(token.get("nro_usuario"), "MATERIALES", accion, descripcion, ip, "EXITOSO")


def registrar(data, token, ip="unknown"):
    clean = _validar(data, True)
    try: material_id = material_repos.crear(_empresa(token), clean)
    except material_repos.MaterialConflictError as exc: raise MaterialError(str(exc), 409)
    _log(token,"REGISTRAR_MATERIAL",f"Material {material_id} registrado.",ip)
    return {"success":True,"id_material":material_id,"message":"Material registrado exitosamente."}


def modificar(material_id, data, token, ip="unknown"):
    if not material_repos.obtener(_empresa(token), material_id): raise MaterialError("Material no encontrado.",404)
    clean = _validar(data, False)
    try: saved = material_repos.actualizar(_empresa(token), material_id, clean)
    except material_repos.MaterialConflictError as exc: raise MaterialError(str(exc),409)
    if not saved: raise MaterialError("Material no encontrado.",404)
    _log(token,"MODIFICAR_MATERIAL",f"Material {material_id} modificado.",ip)
    return {"success":True,"message":"Material actualizado exitosamente."}


def listar(token, q=None, id_categoria=None, estado=None, stock_bajo=None, page=1, limit=20):
    if estado:
        estado = estado.upper()
        if estado not in ESTADOS: raise MaterialError("Estado inválido.")
    if page < 1 or limit < 1 or limit > 100: raise MaterialError("Paginación inválida; limit debe estar entre 1 y 100.")
    rows,total = material_repos.listar(_empresa(token),q.strip() if q else None,id_categoria,estado,stock_bajo,page,limit)
    return {"success":True,"data":rows,"pagination":{"page":page,"limit":limit,"total":total,"total_pages":(total+limit-1)//limit}}


def detalle(material_id, token):
    data = material_repos.obtener(_empresa(token),material_id)
    if not data: raise MaterialError("Material no encontrado.",404)
    return {"success":True,"data":data}


def cambiar_estado(material_id, estado, token, ip="unknown"):
    estado = str(estado or "").strip().upper()
    if estado not in ESTADOS: raise MaterialError("Estado inválido.")
    if not material_repos.cambiar_estado(_empresa(token),material_id,estado): raise MaterialError("Material no encontrado.",404)
    accion = "DESACTIVAR_MATERIAL" if estado == "INACTIVO" else "REACTIVAR_MATERIAL"
    _log(token,accion,f"Material {material_id} cambiado a {estado}.",ip)
    return {"success":True,"message":"Estado actualizado exitosamente."}


def categorias(token):
    _empresa(token); return {"success":True,"data":material_repos.catalogo_activo("categorias")}


def unidades_medida(token):
    _empresa(token); return {"success":True,"data":material_repos.catalogo_activo("unidades")}
