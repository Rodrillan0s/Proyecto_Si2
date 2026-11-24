"""Catálogo Semántico declarativo de OBRATEC.

REGLA ARQUITECTÓNICA:
- Este módulo es 100% declarativo: define tablas, columnas, tipos, relaciones,
  estrategias de tenant/obra y requisitos de permiso.
- NO evalúa permisos RBAC ni autoriza usuarios: toda autorización efectiva se
  delega a app.services.reportes.authorization.
- Ninguna columna sensible (contrasena, correo, telefono, salario_diario, etc.)
  se expone en este catálogo.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FieldDef:
    name: str
    sql_expr: str
    data_type: str  # 'text' | 'number' | 'money' | 'quantity' | 'date' | 'datetime' | 'bool'
    label: str = ''
    filterable: bool = True
    groupable: bool = True
    aggregatable: bool = False


@dataclass(frozen=True)
class RelationDef:
    name: str
    target_entity: str
    join_sql: str  # JOIN seguro N:1 o 1:1 (nunca N:M para evitar fan-out)
    required_permission: str | None = None
    fields: tuple[FieldDef, ...] = ()


@dataclass(frozen=True)
class EntityDef:
    id: str
    title: str
    description: str
    table: str
    alias: str
    base_from: str
    required_permission: str | None
    plan_module: str | None = None
    tenant_clause: str = ''          # SQL con 1 placeholder %s para id_empresa
    work_column: str | None = None   # columna id_obra para scope_obras = ANY(%s)
    default_date_field: str | None = None
    allowed_roles_only: tuple[str, ...] = ()   # si no vacío, solo esos roles
    allow_cliente: bool = False
    allow_workers: bool = False
    cliente_row_clause: str | None = None      # filtro RLS para CLIENTE
    worker_row_clause: str | None = None       # filtro RLS para WORKERS
    money_requires_currency: bool = True
    has_currency_field: bool = False
    versioned_by_work: bool = False            # ej. estimaciones: no sumar versiones
    default_order: str = ''
    fields: tuple[FieldDef, ...] = ()
    relations: tuple[RelationDef, ...] = ()
    warnings: tuple[str, ...] = ()

    def field_map(self) -> dict[str, FieldDef]:
        return {f.name: f for f in self.fields}

    def relation_map(self) -> dict[str, RelationDef]:
        return {r.name: r for r in self.relations}


def _f(name: str, expr: str, dtype: str = 'text', agg: bool = False, grp: bool = True) -> FieldDef:
    return FieldDef(
        name=name,
        sql_expr=expr,
        data_type=dtype,
        label=name.replace('_', ' ').capitalize(),
        filterable=True,
        groupable=grp,
        aggregatable=agg or dtype in {'number', 'money', 'quantity'},
    )


ENTITIES: dict[str, EntityDef] = {e.id: e for e in (
    EntityDef(
        id='obras',
        title='Obras y proyectos',
        description='Proyectos de construcción registrados en la empresa.',
        table='t_obra',
        alias='o',
        base_from='obras.t_obra o',
        required_permission='Visualizar_obras',
        tenant_clause='o.id_empresa = %s',
        work_column='o.id_obra',
        default_date_field='fecha_inicio',
        allow_cliente=True,
        allow_workers=True,
        has_currency_field=True,
        default_order='o.id_obra DESC',
        fields=(
            _f('id_obra', 'o.id_obra', 'number'),
            _f('codigo', 'o.codigo', 'text'),
            _f('nombre', 'o.nombre', 'text'),
            _f('estado_obra', 'o.estado_obra', 'text'),
            _f('fecha_inicio', 'o.fecha_inicio', 'date'),
            _f('fecha_fin', 'o.fecha_fin', 'date'),
            _f('moneda', 'o.moneda', 'text'),
        ),
    ),
    EntityDef(
        id='unidades',
        title='Unidades inmobiliarias',
        description='Unidades constructivas vinculadas a la estructura de cada obra.',
        table='t_unidad_construccion',
        alias='u',
        base_from=(
            'obras.t_unidad_construccion u '
            'JOIN obras.t_estructura_obra s ON s.id_estructura = u.id_estructura '
            'JOIN obras.t_obra o ON o.id_obra = s.id_obra'
        ),
        required_permission='Visualizar_avances',
        tenant_clause='o.id_empresa = %s',
        work_column='o.id_obra',
        allow_cliente=True,
        allow_workers=True,
        default_order='o.id_obra, u.codigo',
        fields=(
            _f('id_unidad', 'u.id_unidad', 'number'),
            _f('id_obra', 'o.id_obra', 'number'),
            _f('obra', 'o.nombre', 'text'),
            _f('codigo', 'u.codigo', 'text'),
            _f('tipo_unidad', 'u.tipo_unidad', 'text'),
            _f('estado', 'u.estado', 'text'),
            _f('superficie', 'u.superficie', 'number', agg=True),
        ),
    ),
    EntityDef(
        id='avances',
        title='Avances físicos de obra',
        description='Registros de avance físico por obra y unidad.',
        table='t_avance_obra',
        alias='av',
        base_from=(
            'obras.t_avance_obra av '
            'JOIN obras.t_obra o ON o.id_obra = av.id_obra '
            'LEFT JOIN obras.t_unidad_construccion u ON u.id_unidad = av.id_unidad'
        ),
        required_permission='Visualizar_avances',
        tenant_clause='o.id_empresa = %s',
        work_column='av.id_obra',
        default_date_field='fecha_registro',
        allow_cliente=True,
        allow_workers=True,
        default_order='av.fecha_registro DESC, av.id_avance DESC',
        fields=(
            _f('id_avance', 'av.id_avance', 'number'),
            _f('id_obra', 'av.id_obra', 'number'),
            _f('obra', 'o.nombre', 'text'),
            _f('id_unidad', 'av.id_unidad', 'number'),
            _f('unidad_codigo', 'u.codigo', 'text'),
            _f('porcentaje_avance', 'av.porcentaje_avance', 'number', agg=True),
            _f('fecha_registro', 'av.fecha_registro', 'date'),
        ),
    ),
    EntityDef(
        id='cronogramas',
        title='Actividades de cronograma',
        description='Actividades e hitos planificados de las obras (fechas previstas, reales y avance).',
        table='t_cronograma_actividad',
        alias='ca',
        base_from=(
            'obras.t_cronograma_actividad ca '
            'JOIN obras.t_cronograma cr ON cr.id_cronograma = ca.id_cronograma '
            'JOIN obras.t_obra o ON o.id_obra = cr.id_obra'
        ),
        required_permission='Visualizar_cronograma',
        tenant_clause='o.id_empresa = %s',
        work_column='cr.id_obra',
        default_date_field='fecha_fin',
        allow_workers=True,
        default_order='ca.fecha_fin ASC',
        fields=(
            _f('id_cronograma', 'ca.id_cronograma', 'number'),
            _f('cronograma', 'cr.nombre', 'text'),
            _f('id_obra', 'cr.id_obra', 'number'),
            _f('obra', 'o.nombre', 'text'),
            _f('clave', 'ca.clave', 'text'),
            _f('nombre', 'ca.nombre', 'text'),
            _f('tipo', 'ca.tipo', 'text'),
            _f('fecha_inicio', 'ca.fecha_inicio', 'date'),
            _f('fecha_fin', 'ca.fecha_fin', 'date'),
            _f('inicio_real', 'ca.inicio_real', 'date'),
            _f('fin_real', 'ca.fin_real', 'date'),
            _f('avance', 'ca.avance', 'number', agg=True),
        ),
    ),
    EntityDef(
        id='estimaciones',
        title='Presupuestos y estimaciones',
        description='Versiones de presupuestos/estimaciones por obra y moneda.',
        table='t_estimacion',
        alias='e',
        base_from='obras.t_estimacion e JOIN obras.t_obra o ON o.id_obra = e.id_obra',
        required_permission='Visualizar_estimaciones',
        tenant_clause='o.id_empresa = %s AND e.id_empresa = o.id_empresa',
        work_column='e.id_obra',
        default_date_field='created_at',
        has_currency_field=True,
        versioned_by_work=True,
        default_order='e.id_obra, e.version DESC',
        warnings=('Cada fila representa una versión de estimación. No sumar versiones distintas.',),
        fields=(
            _f('id_estimacion', 'e.id_estimacion', 'number'),
            _f('id_obra', 'e.id_obra', 'number'),
            _f('obra', 'o.nombre', 'text'),
            _f('moneda', 'o.moneda', 'text'),
            _f('nombre', 'e.nombre', 'text'),
            _f('version', 'e.version', 'number'),
            _f('estado', 'e.estado', 'text'),
            _f('monto_total', 'e.monto_total', 'money', agg=True),
            _f('created_at', 'e.created_at', 'datetime'),
        ),
    ),
    EntityDef(
        id='costos_ejecutados',
        title='Costos ejecutados',
        description='Costos reales registrados sobre la línea base activa por obra y moneda.',
        table='t_costo_ejecutado',
        alias='ce',
        base_from=(
            'obras.t_costo_ejecutado ce '
            'JOIN obras.t_control_costo_obra cc ON cc.id_control_costo = ce.id_control_costo '
            'JOIN obras.t_obra o ON o.id_obra = ce.id_obra'
        ),
        required_permission='Visualizar_control_costos',
        tenant_clause=(
            "o.id_empresa = %s AND ce.id_empresa = o.id_empresa "
            "AND cc.id_empresa = o.id_empresa AND cc.estado = 'ACTIVO'"
        ),
        work_column='ce.id_obra',
        default_date_field='fecha',
        has_currency_field=True,
        default_order='ce.fecha DESC, ce.id_costo_ejecutado DESC',
        fields=(
            _f('id_costo_ejecutado', 'ce.id_costo_ejecutado', 'number'),
            _f('id_obra', 'ce.id_obra', 'number'),
            _f('obra', 'o.nombre', 'text'),
            _f('moneda', 'cc.moneda', 'text'),
            _f('fecha', 'ce.fecha', 'date'),
            _f('concepto', 'ce.concepto', 'text'),
            _f('categoria', 'ce.categoria', 'text'),
            _f('cantidad', 'ce.cantidad', 'number', agg=True),
            _f('costo_unitario', 'ce.costo_unitario', 'money', agg=True),
            _f('monto', 'ce.monto', 'money', agg=True),
            _f('estado', 'ce.estado', 'text'),
        ),
    ),
    EntityDef(
        id='ordenes_cambio',
        title='Órdenes de cambio',
        description='Órdenes de cambio presupuestario y de plazo por obra.',
        table='t_orden_cambio',
        alias='ocm',
        base_from='obras.t_orden_cambio ocm JOIN obras.t_obra o ON o.id_obra = ocm.id_obra',
        required_permission='Visualizar_control_costos',
        tenant_clause='o.id_empresa = %s',
        work_column='ocm.id_obra',
        default_date_field='fecha',
        has_currency_field=True,
        default_order='ocm.fecha DESC',
        fields=(
            _f('id_orden_cambio', 'ocm.id_orden_cambio', 'number'),
            _f('id_obra', 'ocm.id_obra', 'number'),
            _f('obra', 'o.nombre', 'text'),
            _f('moneda', 'o.moneda', 'text'),
            _f('codigo', 'ocm.codigo', 'text'),
            _f('titulo', 'ocm.titulo', 'text'),
            _f('fecha', 'ocm.fecha', 'date'),
            _f('impacto_costo', 'ocm.impacto_costo', 'money', agg=True),
            _f('impacto_plazo_dias', 'ocm.impacto_plazo_dias', 'number', agg=True),
            _f('estado', 'ocm.estado', 'text'),
        ),
    ),
    EntityDef(
        id='incidencias',
        title='Incidencias de obra',
        description='Problemas técnicos, fallas y alertas reportadas en campo.',
        table='t_incidencia',
        alias='i',
        base_from=(
            'obras.t_incidencia i '
            'JOIN obras.t_obra o ON o.id_obra = i.id_obra '
            'LEFT JOIN obras.t_usuario ur ON ur.id_usuario = i.id_responsable '
            'LEFT JOIN obras.t_persona pr ON pr.id_persona = ur.id_persona'
        ),
        required_permission='Visualizar_incidencias',
        tenant_clause='o.id_empresa = %s',
        work_column='i.id_obra',
        default_date_field='created_at',
        allow_workers=True,
        worker_row_clause='(i.id_usuario_registro = %s OR i.id_responsable = %s)',
        default_order='i.created_at DESC',
        fields=(
            _f('id_incidencia', 'i.id_incidencia', 'number'),
            _f('id_obra', 'i.id_obra', 'number'),
            _f('obra', 'o.nombre', 'text'),
            _f('id_unidad', 'i.id_unidad', 'number'),
            _f('id_responsable', 'i.id_responsable', 'number'),
            _f('responsable', "COALESCE(pr.nombre_completo, 'Sin asignar')", 'text'),
            _f('titulo', 'i.titulo', 'text'),
            _f('prioridad', 'i.prioridad', 'text'),
            _f('estado', 'i.estado', 'text'),
            _f('created_at', 'i.created_at', 'datetime'),
        ),
    ),
    EntityDef(
        id='ordenes_trabajo',
        title='Órdenes de trabajo',
        description='Órdenes de trabajo asignadas en obra.',
        table='t_orden_trabajo',
        alias='ot',
        base_from='obras.t_orden_trabajo ot JOIN obras.t_obra o ON o.id_obra = ot.id_obra',
        required_permission='Visualizar_obras',
        tenant_clause='o.id_empresa = %s',
        work_column='ot.id_obra',
        default_date_field='fecha_inicio',
        allow_workers=True,
        worker_row_clause=(
            'EXISTS(SELECT 1 FROM obras.t_orden_trabajo_usuario otu '
            'WHERE otu.id_orden_trabajo = ot.orden_nro AND otu.id_usuario = %s)'
        ),
        default_order='ot.fecha_fin ASC NULLS LAST, ot.orden_nro DESC',
        fields=(
            _f('orden_nro', 'ot.orden_nro', 'number'),
            _f('id_obra', 'ot.id_obra', 'number'),
            _f('obra', 'o.nombre', 'text'),
            _f('tipo_trab', 'ot.tipo_trab', 'text'),
            _f('estado', 'ot.estado', 'text'),
            _f('fecha_inicio', 'ot.fecha_inicio', 'date'),
            _f('fecha_fin', 'ot.fecha_fin', 'date'),
        ),
    ),
    EntityDef(
        id='consultas_tecnicas',
        title='Consultas técnicas',
        description='Consultas y aclaraciones técnicas de obra.',
        table='t_consulta_tecnica',
        alias='ct',
        base_from='obras.t_consulta_tecnica ct JOIN obras.t_obra o ON o.id_obra = ct.id_obra',
        required_permission='Visualizar_consultas_tecnicas',
        tenant_clause='ct.id_empresa = %s AND o.id_empresa = ct.id_empresa',
        work_column='ct.id_obra',
        default_date_field='created_at',
        default_order='ct.created_at DESC',
        fields=(
            _f('id_consulta_tecnica', 'ct.id_consulta_tecnica', 'number'),
            _f('id_obra', 'ct.id_obra', 'number'),
            _f('obra', 'o.nombre', 'text'),
            _f('codigo', 'ct.codigo', 'text'),
            _f('asunto', 'ct.asunto', 'text'),
            _f('estado', 'ct.estado', 'text'),
            _f('created_at', 'ct.created_at', 'datetime'),
        ),
    ),
    EntityDef(
        id='materiales',
        title='Materiales',
        description='Catálogo de materiales e insumos de la empresa.',
        table='t_material',
        alias='m',
        base_from='obras.t_material m',
        required_permission='Visualizar_materiales',
        tenant_clause='m.id_empresa = %s',
        default_order='m.nombre_material ASC',
        fields=(
            _f('id_material', 'm.id_material', 'number'),
            _f('codigo', 'm.codigo', 'text'),
            _f('nombre_material', 'm.nombre_material', 'text'),
            _f('precio', 'm.precio', 'money', agg=True),
            _f('id_proveedor', 'm.id_proveedor', 'number'),
            _f('id_categoria', 'm.id_categoria', 'number'),
            _f('id_unidad_medida', 'm.id_unidad_medida', 'number'),
            _f('estado', 'm.estado', 'text'),
        ),
    ),
    EntityDef(
        id='movimientos_almacen',
        title='Movimientos de almacén',
        description='Salidas y movimientos de materiales vinculados a órdenes de trabajo.',
        table='t_movimiento_almacen',
        alias='ma',
        base_from=(
            'obras.t_movimiento_almacen ma '
            'JOIN obras.t_material mat ON mat.id_material = ma.id_material '
            'JOIN obras.t_orden_trabajo ot ON ot.orden_nro = ma.orden_nro '
            'JOIN obras.t_obra o ON o.id_obra = ot.id_obra'
        ),
        required_permission='Visualizar_inventario',
        tenant_clause='o.id_empresa = %s AND mat.id_empresa = o.id_empresa',
        work_column='ot.id_obra',
        default_date_field='fecha_movimiento',
        default_order='ma.fecha_movimiento DESC',
        fields=(
            _f('id_movimiento', 'ma.id_movimiento', 'number'),
            _f('id_obra', 'ot.id_obra', 'number'),
            _f('obra', 'o.nombre', 'text'),
            _f('orden_nro', 'ot.orden_nro', 'number'),
            _f('id_material', 'ma.id_material', 'number'),
            _f('nombre_material', 'mat.nombre_material', 'text'),
            _f('tipo_movimiento', 'ma.tipo_movimiento', 'text'),
            _f('cantidad_asignada', 'ma.cantidad_asignada', 'quantity', agg=True),
            _f('fecha_movimiento', 'ma.fecha_movimiento', 'date'),
        ),
    ),
    EntityDef(
        id='proveedores',
        title='Proveedores',
        description='Directorio de proveedores de la empresa.',
        table='t_proveedor',
        alias='pv',
        base_from='obras.t_proveedor pv',
        required_permission='Visualizar_proveedores',
        tenant_clause='pv.id_empresa = %s',
        default_order='pv.nombre ASC',
        fields=(
            _f('id_proveedor', 'pv.id_proveedor', 'number'),
            _f('nombre', 'pv.nombre', 'text'),
            _f('estado', 'pv.estado', 'text'),
        ),
    ),
    EntityDef(
        id='compras',
        title='Órdenes de compra',
        description='Órdenes de compra emitidas a proveedores.',
        table='t_orden_compra',
        alias='oc',
        base_from=(
            'obras.t_orden_compra oc '
            'LEFT JOIN obras.t_proveedor pv ON pv.id_proveedor = oc.id_proveedor'
        ),
        required_permission='Visualizar_ordenes_compra',
        tenant_clause='oc.id_empresa = %s',
        default_date_field='fecha',
        default_order='oc.fecha DESC, oc.id_orden_compra DESC',
        warnings=('Los totales de órdenes de compra no registran moneda propia en tabla.',),
        fields=(
            _f('id_orden_compra', 'oc.id_orden_compra', 'number'),
            _f('numero_orden', 'oc.numero_orden', 'text'),
            _f('id_proveedor', 'oc.id_proveedor', 'number'),
            _f('proveedor', 'pv.nombre', 'text'),
            _f('fecha', 'oc.fecha', 'date'),
            _f('estado', 'oc.estado', 'text'),
            _f('subtotal', 'oc.subtotal', 'money', agg=True),
            _f('total', 'oc.total', 'money', agg=True),
        ),
    ),
    EntityDef(
        id='maquinaria',
        title='Equipos y maquinaria',
        description='Parque de equipos y maquinaria de la empresa.',
        table='t_equipo_maquinaria',
        alias='em',
        base_from='obras.t_equipo_maquinaria em',
        required_permission='Visualizar_materiales',
        tenant_clause='em.id_empresa = %s',
        default_order='em.nombre ASC',
        fields=(
            _f('id_equipo_maquinaria', 'em.id_equipo_maquinaria', 'number'),
            _f('codigo', 'em.codigo', 'text'),
            _f('nombre', 'em.nombre', 'text'),
            _f('tipo', 'em.tipo', 'text'),
            _f('marca', 'em.marca', 'text'),
            _f('modelo', 'em.modelo', 'text'),
            _f('estado', 'em.estado', 'text'),
        ),
    ),
    EntityDef(
        id='crm_clientes',
        title='Clientes y prospectos',
        description='Clientes comerciales y prospectos en seguimiento.',
        table='t_crm_cliente',
        alias='c',
        base_from=(
            'obras.t_crm_cliente c '
            'JOIN obras.t_persona p ON p.id_persona = c.id_persona '
            'LEFT JOIN obras.t_usuario ua ON ua.id_usuario = c.id_usuario_asignado '
            'LEFT JOIN obras.t_persona pa ON pa.id_persona = ua.id_persona'
        ),
        required_permission='Visualizar_clientes',
        tenant_clause='c.id_empresa = %s',
        default_date_field='created_at',
        default_order='c.created_at DESC',
        warnings=('El presupuesto estimado de CRM no registra moneda propia.',),
        fields=(
            _f('id_cliente', 'c.id_cliente', 'number'),
            _f('nombre_completo', 'p.nombre_completo', 'text'),
            _f('tipo_cliente', 'c.tipo_cliente', 'text'),
            _f('estado', 'c.estado', 'text'),
            _f('origen', 'c.origen', 'text'),
            _f('presupuesto_estimado', 'c.presupuesto_estimado', 'money', agg=True),
            _f('id_usuario_asignado', 'c.id_usuario_asignado', 'number'),
            _f('asesor', "COALESCE(pa.nombre_completo, 'Sin asignar')", 'text'),
            _f('created_at', 'c.created_at', 'datetime'),
        ),
    ),
    EntityDef(
        id='crm_interacciones',
        title='Interacciones comerciales',
        description='Historial de interacciones y seguimientos con clientes y prospectos.',
        table='t_crm_interaccion',
        alias='ci',
        base_from=(
            'obras.t_crm_interaccion ci '
            'JOIN obras.t_crm_cliente c ON c.id_cliente = ci.id_cliente '
            'JOIN obras.t_persona p ON p.id_persona = c.id_persona'
        ),
        required_permission='Visualizar_clientes',
        tenant_clause='c.id_empresa = %s',
        default_date_field='fecha_interaccion',
        default_order='ci.fecha_interaccion DESC',
        fields=(
            _f('id_interaccion', 'ci.id_interaccion', 'number'),
            _f('id_cliente', 'ci.id_cliente', 'number'),
            _f('cliente', 'p.nombre_completo', 'text'),
            _f('tipo', 'ci.tipo', 'text'),
            _f('asunto', 'ci.asunto', 'text'),
            _f('fecha_interaccion', 'ci.fecha_interaccion', 'datetime'),
            _f('fecha_proximo_contacto', 'ci.fecha_proximo_contacto', 'date'),
        ),
    ),
    EntityDef(
        id='crm_unidades',
        title='Reservas y ventas de unidades',
        description='Asociaciones comerciales entre clientes y unidades inmobiliarias.',
        table='t_crm_cliente_unidad',
        alias='cu',
        base_from=(
            'obras.t_crm_cliente_unidad cu '
            'JOIN obras.t_crm_cliente c ON c.id_cliente = cu.id_cliente '
            'JOIN obras.t_persona p ON p.id_persona = c.id_persona '
            'JOIN obras.t_unidad_construccion u ON u.id_unidad = cu.id_unidad '
            'JOIN obras.t_estructura_obra s ON s.id_estructura = u.id_estructura '
            'JOIN obras.t_obra o ON o.id_obra = s.id_obra'
        ),
        required_permission='Visualizar_clientes',
        tenant_clause='c.id_empresa = %s AND o.id_empresa = c.id_empresa',
        work_column='o.id_obra',
        default_date_field='fecha_asociacion',
        allow_cliente=True,
        cliente_row_clause='c.id_persona = %s',
        default_order='cu.fecha_asociacion DESC',
        warnings=('El monto pactado no tiene columna de moneda propia y no acredita cobros realizados.',),
        fields=(
            _f('id_cliente_unidad', 'cu.id_cliente_unidad', 'number'),
            _f('id_cliente', 'cu.id_cliente', 'number'),
            _f('cliente', 'p.nombre_completo', 'text'),
            _f('id_unidad', 'cu.id_unidad', 'number'),
            _f('unidad_codigo', 'u.codigo', 'text'),
            _f('id_obra', 'o.id_obra', 'number'),
            _f('obra', 'o.nombre', 'text'),
            _f('estado_asociacion', 'cu.estado_asociacion', 'text'),
            _f('monto_pactado', 'cu.monto_pactado', 'money', agg=True),
            _f('fecha_asociacion', 'cu.fecha_asociacion', 'datetime'),
        ),
    ),
    EntityDef(
        id='garantias',
        title='Garantías inmobiliarias',
        description='Garantías vigentes o vencidas asociadas a unidades inmobiliarias.',
        table='t_garantia_inmobiliaria',
        alias='g',
        base_from=(
            'obras.t_garantia_inmobiliaria g '
            'JOIN obras.t_unidad_construccion u ON u.id_unidad = g.id_unidad '
            'JOIN obras.t_estructura_obra s ON s.id_estructura = u.id_estructura '
            'JOIN obras.t_obra o ON o.id_obra = s.id_obra'
        ),
        required_permission=None,
        tenant_clause='g.id_empresa = %s AND o.id_empresa = g.id_empresa',
        work_column='o.id_obra',
        default_date_field='fecha_inicio',
        allow_cliente=True,
        cliente_row_clause=(
            'EXISTS(SELECT 1 FROM obras.t_crm_cliente_unidad cu '
            'JOIN obras.t_crm_cliente c ON c.id_cliente = cu.id_cliente '
            'WHERE cu.id_unidad = g.id_unidad AND c.id_empresa = g.id_empresa AND c.id_persona = %s)'
        ),
        default_order='g.creado_en DESC',
        fields=(
            _f('id_garantia', 'g.id_garantia', 'number'),
            _f('id_unidad', 'g.id_unidad', 'number'),
            _f('unidad_codigo', 'u.codigo', 'text'),
            _f('id_obra', 'o.id_obra', 'number'),
            _f('obra', 'o.nombre', 'text'),
            _f('codigo', 'g.codigo', 'text'),
            _f('tipo_garantia', 'g.tipo_garantia', 'text'),
            _f('fecha_inicio', 'g.fecha_inicio', 'date'),
            _f('fecha_fin', 'g.fecha_fin', 'date'),
            _f('creado_en', 'g.creado_en', 'datetime'),
        ),
    ),
    EntityDef(
        id='posventa',
        title='Solicitudes de posventa',
        description='Reclamos y atenciones de servicio posventa por unidad.',
        table='t_solicitud_posventa',
        alias='sp',
        base_from=(
            'obras.t_solicitud_posventa sp '
            'JOIN obras.t_unidad_construccion u ON u.id_unidad = sp.id_unidad '
            'JOIN obras.t_estructura_obra s ON s.id_estructura = u.id_estructura '
            'JOIN obras.t_obra o ON o.id_obra = s.id_obra '
            'JOIN obras.t_crm_cliente c ON c.id_cliente = sp.id_cliente '
            'LEFT JOIN obras.t_usuario ur ON ur.id_usuario = sp.id_responsable '
            'LEFT JOIN obras.t_persona pr ON pr.id_persona = ur.id_persona'
        ),
        required_permission=None,
        tenant_clause='sp.id_empresa = %s AND o.id_empresa = sp.id_empresa',
        work_column='o.id_obra',
        default_date_field='creado_en',
        allow_cliente=True,
        allow_workers=True,
        cliente_row_clause='c.id_persona = %s',
        worker_row_clause='sp.id_responsable = %s',
        default_order='sp.creado_en DESC',
        fields=(
            _f('id_solicitud_posventa', 'sp.id_solicitud_posventa', 'number'),
            _f('id_unidad', 'sp.id_unidad', 'number'),
            _f('unidad_codigo', 'u.codigo', 'text'),
            _f('id_obra', 'o.id_obra', 'number'),
            _f('obra', 'o.nombre', 'text'),
            _f('id_garantia', 'sp.id_garantia', 'number'),
            _f('titulo', 'sp.titulo', 'text'),
            _f('categoria', 'sp.categoria', 'text'),
            _f('estado', 'sp.estado', 'text'),
            _f('responsable', "COALESCE(pr.nombre_completo, 'Sin asignar')", 'text'),
            _f('creado_en', 'sp.creado_en', 'datetime'),
        ),
    ),
    EntityDef(
        id='personal_obra',
        title='Personal asignado a obras',
        description='Asignación de personal operativo y técnico a obras.',
        table='t_obra_usuario',
        alias='ou',
        base_from=(
            'obras.t_obra_usuario ou '
            'JOIN obras.t_obra o ON o.id_obra = ou.id_obra '
            'JOIN obras.t_usuario u ON u.id_usuario = ou.id_usuario '
            'LEFT JOIN obras.t_persona p ON p.id_persona = u.id_persona '
            'JOIN obras.t_rol r ON r.id_rol = u.id_rol'
        ),
        required_permission='Visualizar_obras',
        tenant_clause='o.id_empresa = %s AND u.id_empresa = o.id_empresa',
        work_column='ou.id_obra',
        default_date_field='fecha_asignacion',
        allow_workers=True,
        worker_row_clause='u.id_usuario = %s',
        default_order='ou.fecha_asignacion DESC',
        fields=(
            _f('id_obra', 'ou.id_obra', 'number'),
            _f('obra', 'o.nombre', 'text'),
            _f('id_usuario', 'u.id_usuario', 'number'),
            _f('nombre_completo', 'p.nombre_completo', 'text'),
            _f('nombre_rol', 'r.nombre_rol', 'text'),
            _f('fecha_asignacion', 'ou.fecha_asignacion', 'datetime'),
        ),
    ),
)}


def get_entity(entity_id: str) -> EntityDef | None:
    return ENTITIES.get(entity_id)


def list_entity_summaries(authorized_ids: list[str]) -> list[dict]:
    out = []
    for eid in authorized_ids:
        ent = ENTITIES.get(eid)
        if not ent:
            continue
        out.append({
            'entidad': ent.id,
            'titulo': ent.title,
            'descripcion': ent.description,
            'campos': [
                {'nombre': f.name, 'tipo': f.data_type, 'agregable': f.aggregatable}
                for f in ent.fields
            ],
            'campo_fecha_defecto': ent.default_date_field,
            'tiene_moneda': ent.has_currency_field,
        })
    return out
