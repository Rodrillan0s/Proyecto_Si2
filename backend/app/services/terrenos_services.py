# app/services/terrenos_service.py
from app.repos import terrenos_repos
from app.classes.postgre import PostgreSQL

def get_terrenos_list():
    db = PostgreSQL()
    try:
        db.create_connection()
        res = terrenos_repos.get_all_terrenos_db(db)
        
        data = []
        if res is not None and db.cur.description:
            columns = [column[0] for column in db.cur.description]
            for row in res:
                data.append(dict(zip(columns, row)))
                
        return {'success': True, 'list_terrenos': data}, 200
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close_connection()


def add_new_terreno(data, id_admin):
    required = ['nombre_sector', 'tamano_hectareas', 'latitud', 'longitud']
    for f in required:
        if not data.get(f):
            return {'success': False, 'message': f'Falta el campo: {f}'}, 400

    nombre = data.get('nombre_sector').upper()
    db = PostgreSQL()
    
    try:
        db.create_connection()
        
        if terrenos_repos.check_duplicate_terreno(db, nombre, id_admin):
            return {'success': False, 'message': 'Terreno ya registrado en tu cuenta.'}, 409
        
        ra = terrenos_repos.insert_terreno_db(
            db, nombre, data.get('tamano_hectareas'), 
            data.get('latitud'), data.get('longitud'), id_admin
        )
        
        if ra and ra > 0:
            db.insert_log(accion="REGISTRO DE NUEVO TERRENO", id_user=id_admin)
            db.conn.commit() # Confirmamos inserción y log juntos
            return {'success': True, 'message': 'Terreno agregado exitosamente.'}, 201
            
        raise Exception('Error al insertar el terreno en la base de datos.')
    except Exception as e:
        if db.conn:
            db.conn.rollback()
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close_connection()


def update_existing_terreno(data):
    nro_lote = data.get('nro_lote')
    if not nro_lote:
        return {'success': False, 'message': 'nro_lote requerido.'}, 400

    fields, params = [], []
    mappings = {
        'nombre_sector': 'nombre_sector',
        'tamano_hectareas': 'tamano_hectareas',
        'latitud': 'latitud',
        'longitud': 'longitud',
        'estado': 'estado',
        'id_usuario': 'id_usuario'
    }

    for key, col in mappings.items():
        if data.get(key) is not None:
            fields.append(f"{col} = %s")
            val = data.get(key)
            params.append(val.upper() if isinstance(val, str) else val)

    if not fields:
        return {'success': False, 'message': 'No hay datos para actualizar.'}, 400

    db = PostgreSQL()
    try:
        db.create_connection()
        ra = terrenos_repos.update_terreno_dynamic_db(db, nro_lote, fields, params)
        
        if ra and ra > 0:
            db.conn.commit() # Confirmamos actualización
            return {'success': True, 'message': 'Terreno actualizado.'}, 200
            
        return {'success': False, 'message': 'Sin cambios o terreno no encontrado.'}, 404
    except Exception as e:
        if db.conn:
            db.conn.rollback()
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close_connection()


def delete_existing_terreno(nro_lote):
    if not nro_lote:
        return {'success': False, 'message': 'nro_lote requerido.'}, 400
        
    db = PostgreSQL()
    try:
        db.create_connection()
        ra = terrenos_repos.delete_terreno_db(db, nro_lote)
        
        if ra and ra > 0:
            db.conn.commit() # Confirmamos eliminación
            return {'success': True, 'message': 'Terreno eliminado.'}, 200
            
        return {'success': False, 'message': 'Terreno no encontrado.'}, 404
    except Exception as e:
        if db.conn:
            db.conn.rollback()
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close_connection()


# ========================================================
# NUEVO CÓDIGO: SERVICIO PARA IMPORTACIÓN MASIVA
# ========================================================
def import_terrenos_bulk(data_list, id_admin):
    """
    Procesa un listado de terrenos provenientes de una importación (Excel/CSV)
    y los inserta asegurando que no haya duplicados para el usuario actual.
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
                nombre = item.get('nombre_sector')
                
                if not nombre:
                    errores.append(f"Fila {idx+1}: Falta 'nombre_sector'.")
                    continue
                
                nombre = str(nombre).strip().upper()
                tamano = item.get('tamano_hectareas')
                lat = item.get('latitud')
                lon = item.get('longitud')
                
                # Si en el CSV no viene el id_usuario, por defecto se asigna al Admin que lo subió
                id_usuario = item.get('id_usuario', id_admin)

                # Validamos que los datos numéricos existan
                if tamano is None or lat is None or lon is None:
                    errores.append(f"Fila {idx+1} ({nombre}): Faltan datos numéricos (tamaño o coordenadas).")
                    continue

                # Evitamos duplicados
                if terrenos_repos.check_duplicate_terreno(db, nombre, id_usuario):
                    errores.append(f"Fila {idx+1} ({nombre}): El terreno ya existe para este usuario.")
                    continue

                # Inserción
                ra = terrenos_repos.insert_terreno_db(db, nombre, tamano, lat, lon, id_usuario)

                if ra and ra > 0:
                    importados += 1
                else:
                    errores.append(f"Fila {idx+1} ({nombre}): Fallo al insertar en la base de datos.")

            except Exception as e:
                errores.append(f"Fila {idx+1}: Error inesperado - {str(e)}")

        # Si insertó al menos 1, hace COMMIT en la base de datos
        if importados > 0:
            db.insert_log(f"IMPORTACIÓN MASIVA: Se registraron {importados} lotes/terrenos", id_admin)
            db.conn.commit()

        # Respuesta estructurada para el Frontend
        mensaje = f"Importación finalizada. {importados} terrenos agregados exitosamente."
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