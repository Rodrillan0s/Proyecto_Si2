# app/services/cultivos_services.py
from decimal import Decimal, InvalidOperation
from app.repos import cultivos_repos
from app.classes.postgre import PostgreSQL

def _to_decimal(value, field_name, default=None):
    if value is None or value == "":
        return default, None

    try:
        value = Decimal(str(value))
        if value < 0:
            return None, f"El campo {field_name} no puede ser negativo."
        return value, None

    except (InvalidOperation, ValueError):
        return None, f"El campo {field_name} debe ser numérico."


def get_cultivos_list():
    db = PostgreSQL()
    try:
        db.create_connection()
        result = cultivos_repos.get_all_cultivos(db)

        data = []
        if result is not None and db.cur.description:
            columns = [column[0] for column in db.cur.description]
            for row in result:
                data.append(dict(zip(columns, row)))

        return {
            "success": True,
            "message": "Bodega de cultivos obtenida exitosamente.",
            "data": data
        }, 200
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}, 500
    finally:
        db.close_connection()


def create_cultivo(data, user_id):
    if not data:
        return {"success": False, "message": "No se enviaron datos."}, 400

    required_fields = ["nombre_producto", "categoria"]
    for field in required_fields:
        if field not in data or not data[field]:
            return {"success": False, "message": f"Falta el campo: {field}"}, 400

    nombre_producto = data.get("nombre_producto").strip().upper()
    categoria = data.get("categoria").strip().upper()

    unidad_medida = data.get("unidad_medida")
    unidad_medida = unidad_medida.strip().upper() if unidad_medida else None

    precio_unitario, error = _to_decimal(data.get("precio_unitario"), "precio_unitario", default=None)
    if error: return {"success": False, "message": error}, 400

    stock_actual, error = _to_decimal(data.get("stock_actual"), "stock_actual", default=0)
    if error: return {"success": False, "message": error}, 400

    stock_minimo, error = _to_decimal(data.get("stock_minimo"), "stock_minimo", default=0)
    if error: return {"success": False, "message": error}, 400

    db = PostgreSQL()
    try:
        db.create_connection()
        ra = cultivos_repos.insert_cultivo(
            db, nombre_producto, categoria, unidad_medida, 
            precio_unitario, stock_actual, stock_minimo
        )

        if ra and ra > 0:
            db.insert_log(f"REGISTRO DE PRODUCTO EN BODEGA: {nombre_producto}", user_id)
            db.conn.commit() # Confirmar inserción y log
            return {"success": True, "message": "Cultivo registrado exitosamente."}, 201

        raise Exception("Error al registrar el cultivo en la base de datos.")
    except Exception as e:
        if db.conn:
            db.conn.rollback()
        return {"success": False, "message": str(e)}, 500
    finally:
        db.close_connection()


def modify_cultivo(data, user_id):
    if not data:
        return {"success": False, "message": "No se enviaron datos."}, 400

    id_producto = data.get("id_producto")
    if not id_producto:
        return {"success": False, "message": "id_producto requerido."}, 400

    try:
        id_producto = int(id_producto)
    except ValueError:
        return {"success": False, "message": "El id_producto debe ser un número entero."}, 400

    fields, params = [], []
    string_mappings = {"nombre_producto": "nombre_producto", "categoria": "categoria", "unidad_medida": "unidad_medida"}
    numeric_mappings = {"precio_unitario": "precio_unitario", "stock_actual": "stock_actual", "stock_minimo": "stock_minimo"}

    for key, column in string_mappings.items():
        if key in data and data.get(key) not in [None, ""]:
            value = data.get(key).strip().upper()
            fields.append(f"{column} = %s")
            params.append(value)

    for key, column in numeric_mappings.items():
        if key in data and data.get(key) not in [None, ""]:
            value, error = _to_decimal(data.get(key), key)
            if error:
                return {"success": False, "message": error}, 400
            fields.append(f"{column} = %s")
            params.append(value)

    if not fields:
        return {"success": False, "message": "No hay datos para actualizar."}, 400

    db = PostgreSQL()
    try:
        db.create_connection()
        ra = cultivos_repos.update_cultivo_dynamic(db, id_producto, fields, params)

        if ra and ra > 0:
            db.insert_log(f"ACTUALIZÓ PRODUCTO ID: {id_producto} EN BODEGA", user_id)
            db.conn.commit()
            return {"success": True, "message": "Cultivo actualizado exitosamente."}, 200

        return {"success": False, "message": "Sin cambios o cultivo no encontrado."}, 404
    except Exception as e:
        if db.conn:
            db.conn.rollback()
        return {"success": False, "message": str(e)}, 500
    finally:
        db.close_connection()


def remove_cultivo(id_producto, user_id):
    if not id_producto:
        return {"success": False, "message": "Debe seleccionar un cultivo."}, 400

    try:
        id_producto = int(id_producto)
    except ValueError:
        return {"success": False, "message": "El id_producto debe ser un número entero."}, 400

    db = PostgreSQL()
    try:
        db.create_connection()
        ra = cultivos_repos.delete_cultivo_by_id(db, id_producto)

        if ra and ra > 0:
            db.insert_log(f"ELIMINÓ PRODUCTO ID: {id_producto} DE BODEGA", user_id)
            db.conn.commit()
            return {"success": True, "message": "Cultivo eliminado exitosamente.", "filas": ra}, 200

        return {"success": False, "message": "Cultivo no encontrado."}, 404
    except Exception as e:
        if db.conn:
            db.conn.rollback()
        if "violates foreign key constraint" in str(e).lower() or "foreign key" in str(e).lower():
            return {"success": False, "message": "No se puede eliminar el producto porque está siendo utilizado en campañas u órdenes."}, 409
        return {"success": False, "message": str(e)}, 500
    finally:
        db.close_connection()


# ========================================================
# NUEVO CÓDIGO: SERVICIO PARA IMPORTACIÓN MASIVA
# ========================================================
def import_cultivos(data_list, user_id):
    """
    Recibe una lista de diccionarios (datos parseados de CSV/Excel en el frontend)
    e inserta los registros válidos masivamente.
    """
    if not data_list or not isinstance(data_list, list):
        return {"success": False, "message": "El formato enviado debe ser una lista de registros."}, 400

    db = PostgreSQL()
    importados = 0
    errores = []

    try:
        db.create_connection()

        for idx, item in enumerate(data_list):
            try:
                # Validar campos obligatorios de la fila
                nombre_producto = item.get("nombre_producto", "")
                categoria = item.get("categoria", "")

                if not nombre_producto or not categoria:
                    errores.append(f"Fila {idx+1}: Falta 'nombre_producto' o 'categoria'.")
                    continue

                nombre_producto = str(nombre_producto).strip().upper()
                categoria = str(categoria).strip().upper()

                unidad_medida = item.get("unidad_medida", "")
                unidad_medida = str(unidad_medida).strip().upper() if unidad_medida else None

                # Conversión de numéricos
                precio_unitario, err1 = _to_decimal(item.get("precio_unitario"), "precio_unitario", default=0)
                stock_actual, err2 = _to_decimal(item.get("stock_actual"), "stock_actual", default=0)
                stock_minimo, err3 = _to_decimal(item.get("stock_minimo"), "stock_minimo", default=0)

                if err1 or err2 or err3:
                    errores.append(f"Fila {idx+1} ({nombre_producto}): Valores numéricos inválidos.")
                    continue

                # Insertar en base de datos
                ra = cultivos_repos.insert_cultivo(
                    db, nombre_producto, categoria, unidad_medida, 
                    precio_unitario, stock_actual, stock_minimo
                )

                if ra and ra > 0:
                    importados += 1
                else:
                    errores.append(f"Fila {idx+1} ({nombre_producto}): Fallo al insertar.")

            except Exception as e:
                errores.append(f"Fila {idx+1}: Error inesperado - {str(e)}")

        # Si al menos un registro se importó, hacemos commit y bitácora
        if importados > 0:
            db.insert_log(f"IMPORTACIÓN MASIVA: Se registraron {importados} productos en BODEGA", user_id)
            db.conn.commit()

        # Construir mensaje de respuesta
        mensaje = f"Importación finalizada. {importados} productos agregados exitosamente."
        if errores:
            mensaje += f" Se omitieron {len(errores)} filas con errores."

        return {
            "success": True if importados > 0 else False,
            "message": mensaje,
            "importados": importados,
            "errores": errores
        }, 201 if importados > 0 else 400

    except Exception as e:
        if db.conn:
            db.conn.rollback()
        return {"success": False, "message": f"Error crítico en importación: {str(e)}"}, 500
    finally:
        db.close_connection()