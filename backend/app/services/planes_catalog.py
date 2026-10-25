"""Módulos implementados configurables por plan; no concede permisos RBAC."""
MODULOS = {
    'obras':'Proyectos, estructura y unidades', 'avances':'Avances de obra',
    'ordenes_trabajo':'Órdenes de trabajo', 'incidencias':'Incidencias y evidencias',
    'presupuestos':'Presupuestos y APU', 'control_costos':'Control de costos y órdenes de cambio',
    'compras':'Compras y recepciones', 'inventario':'Inventario y ajustes',
    'materiales':'Materiales y catálogo', 'proveedores':'Proveedores',
    'equipos':'Equipos y maquinaria', 'crm':'CRM y clientes',
    'usuarios':'Usuarios y roles', 'reportes':'Reportes', 'ia':'Asistente IA y voz',
}


def modulo_ruta(ruta):
    partes = ruta.strip('/').split('/')
    if partes and partes[0]=='api': partes=partes[1:]
    if not partes: return None
    raiz=partes[0]
    if raiz=='obras': return 'obras'
    if raiz=='proyectos':
        sub=partes[2] if len(partes)>2 else None
        return {'presupuestos':'presupuestos','costos-ejecutados':'control_costos','avances':'avances'}.get(sub,'obras')
    return {'estimaciones':'presupuestos','apus':'presupuestos','control-costos':'control_costos',
        'ordenes-trabajo':'ordenes_trabajo','incidencias':'incidencias','compras':'compras',
        'inventario':'inventario','materiales':'materiales','proveedores':'proveedores',
        'equipos-maquinaria':'equipos','crm':'crm','usuarios':'usuarios','roles':'usuarios',
        'reportes':'reportes','ai':'ia','voz':'ia'}.get(raiz)
