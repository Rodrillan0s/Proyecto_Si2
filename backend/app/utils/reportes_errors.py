"""Errores de instalación compartidos por persistencia y transporte HTTP."""

REPORT_TABLES = frozenset({
    't_reporte_programacion', 't_reporte_programacion_destinatario',
    't_reporte_ejecucion', 't_reporte_archivo', 't_reporte_envio',
    't_asistente_conversacion', 't_asistente_mensaje',
})


class ReportesSchemaMissing(RuntimeError):
    def __init__(self):
        super().__init__(
            'La base de datos requiere la migración de Reportes. '
            'Ejecuta python migrate_reportes.py --apply desde el backend.'
        )
