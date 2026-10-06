"""Expresión de lectura compartida; requiere la OT externa con alias ot.

La misma obra implica la misma empresa. No persiste afectaciones ni modifica
el estado operativo o los responsables. EXISTS evalúa todos los vínculos
en una única instantánea de la consulta, también ante cambios concurrentes.
"""

AFECTADA_POR_INCIDENCIA_SQL = """
    EXISTS (
        SELECT 1
        FROM obras.t_incidencia_orden_trabajo afectacion
        JOIN obras.t_incidencia incidencia_activa
          ON incidencia_activa.id_incidencia = afectacion.id_incidencia
        WHERE afectacion.orden_nro = ot.orden_nro
          AND incidencia_activa.id_obra = ot.id_obra
          AND incidencia_activa.estado IN (
              'ABIERTA', 'ASIGNADA', 'EN_PROCESO', 'PENDIENTE_VALIDACION'
          )
    )
"""
