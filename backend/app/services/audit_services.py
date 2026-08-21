from app.repos import audit_repos
from app.classes.postgre import PostgreSQL

def fetch_audit_logs() -> tuple[dict, int]:
    db = PostgreSQL()
    try:
        db.create_connection()

        result = audit_repos.get_last_30_days_logs(db)

        data = []
        if result is not None and db.cur.description:
            columns = [column[0] for column in db.cur.description]
            for row in result:
                row_dict = dict(zip(columns, row))
                
                # Formateamos la fecha a string para evitar errores de serialización JSON
                if 'fecha_hora' in row_dict and row_dict['fecha_hora']:
                    row_dict['fecha_hora'] = str(row_dict['fecha_hora'])
                    
                data.append(row_dict)

        return {
            'success': True,
            'message': 'Bitácora de los últimos 30 días obtenida correctamente.',
            'bitacora': data
        }, 200

    except Exception as e:
        print(f"Error en fetch_audit_logs: {e}")
        return {
            'success': False,
            'message': f'Error al obtener la bitácora: {str(e)}'
        }, 500
    finally:
        db.close_connection()