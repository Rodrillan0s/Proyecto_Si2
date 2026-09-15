import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_provider.dart';
import '../services/orden_trabajo_service.dart';
import '../services/obra_service.dart';
import '../theme/app_theme.dart';

class OrdenesTrabajoScreen extends StatefulWidget {
  final int? idObraFiltro;
  final String? nombreObraFiltro;

  const OrdenesTrabajoScreen({
    super.key,
    this.idObraFiltro,
    this.nombreObraFiltro,
  });

  @override
  State<OrdenesTrabajoScreen> createState() => _OrdenesTrabajoScreenState();
}

class _OrdenesTrabajoScreenState extends State<OrdenesTrabajoScreen> {
  final OrdenTrabajoService _otService = OrdenTrabajoService();
  final ObraService _obraService = ObraService();
  final TextEditingController _searchCtrl = TextEditingController();

  List<Map<String, dynamic>> _ordenes = [];
  List<Map<String, dynamic>> _proyectos = [];
  bool _cargando = true;
  String _busqueda = '';
  String _filtroEstado = 'TODOS'; // TODOS, PENDIENTE, EN_PROCESO, FINALIZADO, CANCELADO

  @override
  void initState() {
    super.initState();
    _cargarDatos();
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  Future<void> _cargarDatos() async {
    setState(() => _cargando = true);
    final auth = Provider.of<AuthProvider>(context, listen: false);

    try {
      final int? idEmpresa = auth.esAdminGlobal ? auth.idEmpresaActiva : auth.empresaId;
      final int? idObra = widget.idObraFiltro;

      final results = await Future.wait([
        _otService.listarOrdenesTrabajo(idEmpresa: idEmpresa, idObra: idObra),
        _obraService.listarProyectos(),
      ]);

      if (!mounted) return;
      setState(() {
        _ordenes = results[0];
        _proyectos = results[1];
        _cargando = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _cargando = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error al cargar órdenes de trabajo: $e'),
          backgroundColor: AppTheme.error,
        ),
      );
    }
  }

  List<Map<String, dynamic>> get _ordenesFiltradas {
    return _ordenes.where((ot) {
      // Filtro de estado
      if (_filtroEstado != 'TODOS') {
        final estado = (ot['estado'] ?? '').toString().toUpperCase();
        if (estado != _filtroEstado) return false;
      }

      // Filtro de búsqueda
      if (_busqueda.isNotEmpty) {
        final query = _busqueda.toLowerCase();
        final tipo = (ot['tipo_trab'] ?? '').toString().toLowerCase();
        final ordenNro = (ot['orden_nro'] ?? '').toString();
        final nombreObra = (ot['nombre'] ?? '').toString().toLowerCase();
        final obs = (ot['observacion'] ?? '').toString().toLowerCase();
        final empresa = (ot['nombre_empresa'] ?? '').toString().toLowerCase();

        return tipo.contains(query) ||
            ordenNro.contains(query) ||
            nombreObra.contains(query) ||
            obs.contains(query) ||
            empresa.contains(query);
      }

      return true;
    }).toList();
  }

  bool _puedeModificar() {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    return auth.hasPermission('Modificar_ordenes_trabajo') ||
        auth.esAdminGlobal ||
        auth.esAdminEmpresa ||
        auth.esJefeDeObra;
  }

  Color _colorPorEstado(String? estado) {
    switch ((estado ?? '').toUpperCase()) {
      case 'PENDIENTE':
        return AppTheme.warning;
      case 'EN_PROCESO':
      case 'EN PROCESO':
        return AppTheme.info;
      case 'FINALIZADO':
        return AppTheme.success;
      case 'CANCELADO':
        return AppTheme.error;
      default:
        return AppTheme.textMuted;
    }
  }

  String _etiquetaEstado(String? estado) {
    switch ((estado ?? '').toUpperCase()) {
      case 'PENDIENTE':
        return 'Pendiente';
      case 'EN_PROCESO':
      case 'EN PROCESO':
        return 'En Proceso';
      case 'FINALIZADO':
        return 'Finalizado';
      case 'CANCELADO':
        return 'Cancelado';
      default:
        return estado ?? 'Sin estado';
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final cardBg = isDark ? const Color(0xFF1E293B) : Colors.white;
    final borderColor = isDark ? const Color(0xFF334155) : const Color(0xFFE2E8F0);

    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF0F172A) : AppTheme.background,
      appBar: AppBar(
        title: Text(
          widget.nombreObraFiltro != null
              ? 'OTs: ${widget.nombreObraFiltro}'
              : 'Órdenes de Trabajo',
        ),
        actions: [
          IconButton(
            tooltip: 'Actualizar',
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _cargando ? null : _cargarDatos,
          ),
        ],
      ),
      floatingActionButton: _puedeModificar()
          ? FloatingActionButton.extended(
              onPressed: () => _abrirModalCrearOrden(context),
              icon: const Icon(Icons.add_task_rounded),
              label: const Text('Nueva Orden'),
            )
          : null,
      body: SafeArea(
        child: Column(
          children: [
            // Banner de contexto multi-tenant para Administrador
            if (auth.esAdminGlobal)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                color: auth.esVistaGlobal
                    ? (isDark ? const Color(0xFF1E293B) : const Color(0xFFE0E7FF))
                    : (isDark ? const Color(0xFF14532D).withValues(alpha: 0.3) : const Color(0xFFDCFCE7)),
                child: Row(
                  children: [
                    Icon(
                      auth.esVistaGlobal ? Icons.public_rounded : Icons.business_rounded,
                      size: 18,
                      color: auth.esVistaGlobal ? AppTheme.primary : AppTheme.success,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        auth.esVistaGlobal
                            ? 'Vista Global: Todas las Empresas'
                            : 'Empresa Activa: ${auth.nombreEmpresaActiva ?? "Empresa"}',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: auth.esVistaGlobal ? AppTheme.primary : AppTheme.success,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),

            // Barra de búsqueda
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 6),
              child: TextField(
                controller: _searchCtrl,
                decoration: InputDecoration(
                  hintText: 'Buscar por orden, labor, obra...',
                  prefixIcon: const Icon(Icons.search_rounded, size: 20, color: AppTheme.textMuted),
                  suffixIcon: _busqueda.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear_rounded, size: 18),
                          onPressed: () {
                            _searchCtrl.clear();
                            setState(() => _busqueda = '');
                          },
                        )
                      : null,
                ),
                onChanged: (val) => setState(() => _busqueda = val.trim()),
              ),
            ),

            // Chips de filtro de estado
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              child: Row(
                children: [
                  _buildFiltroChip('TODOS', 'Todos (${_ordenes.length})'),
                  const SizedBox(width: 8),
                  _buildFiltroChip('PENDIENTE', 'Pendientes', color: AppTheme.warning),
                  const SizedBox(width: 8),
                  _buildFiltroChip('EN_PROCESO', 'En Proceso', color: AppTheme.info),
                  const SizedBox(width: 8),
                  _buildFiltroChip('FINALIZADO', 'Finalizadas', color: AppTheme.success),
                  const SizedBox(width: 8),
                  _buildFiltroChip('CANCELADO', 'Canceladas', color: AppTheme.error),
                ],
              ),
            ),

            const SizedBox(height: 6),

            // Listado de Órdenes
            Expanded(
              child: _cargando
                  ? const Center(child: CircularProgressIndicator())
                  : _ordenesFiltradas.isEmpty
                      ? _buildEmptyState(isDark)
                      : RefreshIndicator(
                          onRefresh: _cargarDatos,
                          child: ListView.separated(
                            padding: const EdgeInsets.fromLTRB(16, 8, 16, 80),
                            itemCount: _ordenesFiltradas.length,
                            separatorBuilder: (_, __) => const SizedBox(height: 12),
                            itemBuilder: (ctx, i) {
                              final ot = _ordenesFiltradas[i];
                              return _buildOrdenCard(ot, cardBg, borderColor, isDark);
                            },
                          ),
                        ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFiltroChip(String estadoKey, String label, {Color? color}) {
    final seleccionado = _filtroEstado == estadoKey;
    final activeColor = color ?? AppTheme.primary;

    return FilterChip(
      label: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          fontWeight: seleccionado ? FontWeight.w700 : FontWeight.w500,
          color: seleccionado ? Colors.white : AppTheme.textPrimary,
        ),
      ),
      selected: seleccionado,
      selectedColor: activeColor,
      checkmarkColor: Colors.white,
      backgroundColor: Colors.transparent,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: BorderSide(
          color: seleccionado ? activeColor : const Color(0xFFCBD5E1),
        ),
      ),
      onSelected: (_) => setState(() => _filtroEstado = estadoKey),
    );
  }

  Widget _buildOrdenCard(
    Map<String, dynamic> ot,
    Color cardBg,
    Color borderColor,
    bool isDark,
  ) {
    final ordenNro = ot['orden_nro'] ?? 0;
    final estado = (ot['estado'] ?? 'PENDIENTE').toString();
    final tipoTrab = (ot['tipo_trab'] ?? 'Trabajo general').toString();
    final cuadrilla = ot['cuadrilla'] ?? 1;
    final nombreObra = ot['nombre'] ?? 'Obra sin asignar';
    final nombreEmpresa = ot['nombre_empresa']?.toString();
    final fechaInicio = ot['fecha_inicio']?.toString();
    final fechaFin = ot['fecha_fin']?.toString();
    final observacion = ot['observacion']?.toString();

    final statusColor = _colorPorEstado(estado);

    return Container(
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderColor),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: isDark ? 0.2 : 0.04),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => _abrirDetalleOrden(ot),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Fila superior: ID y Estado
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppTheme.primary.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      '#OT-$ordenNro',
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.primary,
                      ),
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: statusColor.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: statusColor.withValues(alpha: 0.3)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 7,
                          height: 7,
                          decoration: BoxDecoration(
                            color: statusColor,
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 5),
                        Text(
                          _etiquetaEstado(estado),
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: statusColor,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),

              // Tipo de Trabajo
              Text(
                tipoTrab,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                  color: isDark ? Colors.white : AppTheme.textPrimary,
                ),
              ),
              const SizedBox(height: 6),

              // Proyecto / Obra
              Row(
                children: [
                  const Icon(Icons.apartment_rounded, size: 15, color: AppTheme.textMuted),
                  const SizedBox(width: 5),
                  Expanded(
                    child: Text(
                      nombreObra,
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.textSecondary,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  if (nombreEmpresa != null && nombreEmpresa.isNotEmpty) ...[
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: isDark ? const Color(0xFF334155) : const Color(0xFFF1F5F9),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        nombreEmpresa,
                        style: const TextStyle(fontSize: 10, color: AppTheme.textMuted),
                      ),
                    ),
                  ],
                ],
              ),
              const SizedBox(height: 10),

              // Fila inferior: Cuadrilla y Fechas
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.groups_rounded, size: 16, color: AppTheme.primary),
                      const SizedBox(width: 4),
                      Text(
                        '$cuadrilla operario${cuadrilla > 1 ? 's' : ''}',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                    ],
                  ),
                  if (fechaInicio != null)
                    Row(
                      children: [
                        const Icon(Icons.calendar_today_rounded, size: 13, color: AppTheme.textMuted),
                        const SizedBox(width: 4),
                        Text(
                          fechaFin != null ? '$fechaInicio → $fechaFin' : 'Inicia: $fechaInicio',
                          style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                        ),
                      ],
                    ),
                ],
              ),

              if (observacion != null && observacion.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(
                  observacion,
                  style: const TextStyle(fontSize: 12, fontStyle: FontStyle.italic, color: AppTheme.textMuted),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState(bool isDark) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.assignment_late_outlined, size: 64, color: AppTheme.textMuted.withValues(alpha: 0.5)),
            const SizedBox(height: 16),
            const Text(
              'No hay órdenes de trabajo',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              'No se encontraron órdenes con los filtros actuales.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
            ),
          ],
        ),
      ),
    );
  }

  // ==========================================
  // MODAL DETALLE DE ORDEN DE TRABAJO
  // ==========================================
  void _abrirDetalleOrden(Map<String, dynamic> ot) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (bCtx) => _DetalleOrdenModal(
        ot: ot,
        onCambioEstado: (nuevoEstado) async {
          Navigator.pop(bCtx);
          final ordenNro = ot['orden_nro'] as int;
          try {
            await _otService.actualizarEstado(ordenNro, nuevoEstado);
            if (!mounted) return;
            _cargarDatos();
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('Estado actualizado a $nuevoEstado'),
                backgroundColor: AppTheme.success,
              ),
            );
          } catch (e) {
            if (!mounted) return;
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Error: $e'), backgroundColor: AppTheme.error),
            );
          }
        },
        onEliminar: () async {
          final ordenNro = ot['orden_nro'] as int;
          final messenger = ScaffoldMessenger.of(context);
          final modalNav = Navigator.of(bCtx);
          final confirmar = await showDialog<bool>(
            context: context,
            builder: (dCtx) => AlertDialog(
              title: const Text('¿Eliminar Orden?'),
              content: Text('¿Estás seguro de cancelar/eliminar la orden #OT-$ordenNro?'),
              actions: [
                TextButton(onPressed: () => Navigator.pop(dCtx, false), child: const Text('Volver')),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error),
                  onPressed: () => Navigator.pop(dCtx, true),
                  child: const Text('Eliminar'),
                ),
              ],
            ),
          );

          if (confirmar == true) {
            modalNav.pop();
            try {
              await _otService.eliminarOrdenTrabajo(ordenNro);
              if (!mounted) return;
              _cargarDatos();
              messenger.showSnackBar(
                const SnackBar(content: Text('Orden eliminada exitosamente'), backgroundColor: AppTheme.success),
              );
            } catch (e) {
              messenger.showSnackBar(
                SnackBar(content: Text('Error al eliminar: $e'), backgroundColor: AppTheme.error),
              );
            }
          }
        },
      ),
    );
  }

  // ==========================================
  // MODAL CREAR NUEVA ORDEN DE TRABAJO
  // ==========================================
  void _abrirModalCrearOrden(BuildContext context) {
    int? selectedIdObra = widget.idObraFiltro ?? (_proyectos.isNotEmpty ? _proyectos.first['id_obra'] : null);
    final tipoCtrl = TextEditingController();
    final cuadrillaCtrl = TextEditingController(text: '1');
    final obsCtrl = TextEditingController();
    DateTime fechaInicio = DateTime.now();
    DateTime? fechaFin;
    bool guardando = false;

    final sugerenciasTipos = [
      'Albañilería y muros',
      'Instalación eléctrica',
      'Plomería y tuberías',
      'Estructura de hormigón',
      'Pintura y acabados',
      'Carpintería metálica',
    ];

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (bCtx) => StatefulBuilder(
        builder: (ctx, setModalState) {
          return Padding(
            padding: EdgeInsets.only(
              bottom: MediaQuery.of(ctx).viewInsets.bottom,
              left: 20,
              right: 20,
              top: 20,
            ),
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Nueva Orden de Trabajo',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close_rounded),
                        onPressed: () => Navigator.pop(ctx),
                      ),
                    ],
                  ),
                  const Divider(),
                  const SizedBox(height: 10),

                  // Selector de Obra
                  const Text('Obra / Proyecto *', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
                  const SizedBox(height: 6),
                  DropdownButtonFormField<int>(
                    initialValue: selectedIdObra,
                    isExpanded: true,
                    decoration: InputDecoration(
                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                    items: _proyectos.map((p) {
                      final id = p['id_obra'] as int;
                      final nombre = p['nombre']?.toString() ?? 'Obra #$id';
                      return DropdownMenuItem<int>(
                        value: id,
                        child: Text(nombre, maxLines: 1, overflow: TextOverflow.ellipsis),
                      );
                    }).toList(),
                    onChanged: (val) => setModalState(() => selectedIdObra = val),
                  ),
                  const SizedBox(height: 14),

                  // Tipo de Trabajo
                  const Text('Tipo de Trabajo *', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
                  const SizedBox(height: 6),
                  TextField(
                    controller: tipoCtrl,
                    decoration: InputDecoration(
                      hintText: 'Ej. Hormigonado de columnas...',
                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                  ),
                  const SizedBox(height: 6),
                  Wrap(
                    spacing: 6,
                    runSpacing: 4,
                    children: sugerenciasTipos.map((sug) {
                      return ActionChip(
                        label: Text(sug, style: const TextStyle(fontSize: 10)),
                        padding: EdgeInsets.zero,
                        onPressed: () => setModalState(() => tipoCtrl.text = sug),
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 14),

                  // Cuadrilla (operarios)
                  const Text('Cuadrilla (Cantidad de operarios) *', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
                  const SizedBox(height: 6),
                  TextField(
                    controller: cuadrillaCtrl,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      hintText: '1',
                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                  ),
                  const SizedBox(height: 14),

                  // Fechas
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Fecha Inicio *', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12)),
                            const SizedBox(height: 4),
                            OutlinedButton.icon(
                              icon: const Icon(Icons.calendar_today_rounded, size: 14),
                              label: Text('${fechaInicio.year}-${fechaInicio.month.toString().padLeft(2, '0')}-${fechaInicio.day.toString().padLeft(2, '0')}', style: const TextStyle(fontSize: 12)),
                              onPressed: () async {
                                final d = await showDatePicker(
                                  context: ctx,
                                  initialDate: fechaInicio,
                                  firstDate: DateTime(2020),
                                  lastDate: DateTime(2035),
                                );
                                if (d != null) setModalState(() => fechaInicio = d);
                              },
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Fecha Fin Estimada', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12)),
                            const SizedBox(height: 4),
                            OutlinedButton.icon(
                              icon: const Icon(Icons.calendar_today_rounded, size: 14),
                              label: Text(
                                fechaFin != null
                                    ? '${fechaFin!.year}-${fechaFin!.month.toString().padLeft(2, '0')}-${fechaFin!.day.toString().padLeft(2, '0')}'
                                    : 'Sin definir',
                                style: const TextStyle(fontSize: 12),
                              ),
                              onPressed: () async {
                                final d = await showDatePicker(
                                  context: ctx,
                                  initialDate: fechaFin ?? fechaInicio.add(const Duration(days: 7)),
                                  firstDate: DateTime(2020),
                                  lastDate: DateTime(2035),
                                );
                                if (d != null) setModalState(() => fechaFin = d);
                              },
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),

                  // Observaciones
                  const Text('Observaciones y detalles', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
                  const SizedBox(height: 6),
                  TextField(
                    controller: obsCtrl,
                    maxLines: 2,
                    decoration: InputDecoration(
                      hintText: 'Indicaciones especiales, herramientas necesarias...',
                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Botón Guardar
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: guardando
                          ? null
                          : () async {
                              if (selectedIdObra == null) {
                                ScaffoldMessenger.of(ctx).showSnackBar(
                                  const SnackBar(content: Text('Seleccione una obra.'), backgroundColor: AppTheme.error),
                                );
                                return;
                              }
                              if (tipoCtrl.text.trim().isEmpty) {
                                ScaffoldMessenger.of(ctx).showSnackBar(
                                  const SnackBar(content: Text('Especifique el tipo de trabajo.'), backgroundColor: AppTheme.error),
                                );
                                return;
                              }

                              final cuadrillaInt = int.tryParse(cuadrillaCtrl.text.trim()) ?? 1;

                              setModalState(() => guardando = true);

                              final payload = {
                                'id_obra': selectedIdObra,
                                'tipo_trab': tipoCtrl.text.trim(),
                                'cuadrilla': cuadrillaInt,
                                'estado': 'PENDIENTE',
                                'fecha_inicio': '${fechaInicio.year}-${fechaInicio.month.toString().padLeft(2, '0')}-${fechaInicio.day.toString().padLeft(2, '0')}',
                                if (fechaFin != null)
                                  'fecha_fin': '${fechaFin!.year}-${fechaFin!.month.toString().padLeft(2, '0')}-${fechaFin!.day.toString().padLeft(2, '0')}',
                                'observacion': obsCtrl.text.trim(),
                                'id_usuarios': [],
                              };

                              final messenger = ScaffoldMessenger.of(context);
                              Navigator.pop(ctx);
                              try {
                                await _otService.crearOrdenTrabajo(payload);
                                if (!mounted) return;
                                _cargarDatos();
                                messenger.showSnackBar(
                                  const SnackBar(
                                    content: Text('Orden de trabajo creada exitosamente'),
                                    backgroundColor: AppTheme.success,
                                  ),
                                );
                              } catch (e) {
                                messenger.showSnackBar(
                                  SnackBar(content: Text('Error: $e'), backgroundColor: AppTheme.error),
                                );
                              }
                            },
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      child: guardando
                          ? const SizedBox(
                              height: 18,
                              width: 18,
                              child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                            )
                          : const Text('Crear Orden de Trabajo', style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}

// ==========================================
// COMPONENTE: DETALLE ORDEN MODAL
// ==========================================
class _DetalleOrdenModal extends StatefulWidget {
  final Map<String, dynamic> ot;
  final Function(String nuevoEstado) onCambioEstado;
  final VoidCallback onEliminar;

  const _DetalleOrdenModal({
    required this.ot,
    required this.onCambioEstado,
    required this.onEliminar,
  });

  @override
  State<_DetalleOrdenModal> createState() => _DetalleOrdenModalState();
}

class _DetalleOrdenModalState extends State<_DetalleOrdenModal> {
  final OrdenTrabajoService _service = OrdenTrabajoService();
  List<Map<String, dynamic>> _responsables = [];
  bool _cargandoResponsables = true;

  @override
  void initState() {
    super.initState();
    _cargarResponsables();
  }

  Future<void> _cargarResponsables() async {
    final ordenNro = widget.ot['orden_nro'] as int;
    try {
      final list = await _service.listarResponsables(ordenNro);
      if (!mounted) return;
      setState(() {
        _responsables = list;
        _cargandoResponsables = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _cargandoResponsables = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final ot = widget.ot;
    final ordenNro = ot['orden_nro'] ?? 0;
    final estado = (ot['estado'] ?? 'PENDIENTE').toString();
    final tipoTrab = (ot['tipo_trab'] ?? '').toString();
    final cuadrilla = ot['cuadrilla'] ?? 1;
    final nombreObra = ot['nombre'] ?? '';
    final fechaInicio = ot['fecha_inicio']?.toString();
    final fechaFin = ot['fecha_fin']?.toString();
    final observacion = ot['observacion']?.toString();

    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF1E293B) : Colors.white;

    return Container(
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Drag handle
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey.withValues(alpha: 0.3),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Orden de Trabajo #$ordenNro',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              IconButton(
                icon: const Icon(Icons.delete_outline_rounded, color: AppTheme.error),
                tooltip: 'Eliminar / Cancelar',
                onPressed: widget.onEliminar,
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            tipoTrab,
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppTheme.primary),
          ),
          Text(
            'Obra: $nombreObra',
            style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
          ),
          const Divider(height: 24),

          // Cambiar Estado rápido
          const Text('Cambiar Estado:', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12)),
          const SizedBox(height: 8),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                if (estado != 'PENDIENTE')
                  _buildEstadoBtn('PENDIENTE', 'Pendiente', AppTheme.warning),
                if (estado != 'EN_PROCESO')
                  _buildEstadoBtn('EN_PROCESO', 'En Proceso', AppTheme.info),
                if (estado != 'FINALIZADO')
                  _buildEstadoBtn('FINALIZADO', 'Finalizar', AppTheme.success),
                if (estado != 'CANCELADO')
                  _buildEstadoBtn('CANCELADO', 'Cancelar', AppTheme.error),
              ],
            ),
          ),
          const Divider(height: 24),

          // Datos de la Orden
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Operarios requeridos: $cuadrilla', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
              Text('Inicio: ${fechaInicio ?? 'N/D'}', style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
            ],
          ),
          if (fechaFin != null) ...[
            const SizedBox(height: 4),
            Text('Fin estimado: $fechaFin', style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
          ],
          if (observacion != null && observacion.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text('Nota: $observacion', style: const TextStyle(fontSize: 12, fontStyle: FontStyle.italic)),
          ],

          const SizedBox(height: 16),
          // Responsables asignados
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Personal Asignado', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
              Text('${_responsables.length} asignados', style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
            ],
          ),
          const SizedBox(height: 8),
          if (_cargandoResponsables)
            const Center(child: Padding(padding: EdgeInsets.all(12), child: CircularProgressIndicator()))
          else if (_responsables.isEmpty)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.black.withValues(alpha: 0.03),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Text('Sin operarios asignados a esta orden.', style: TextStyle(fontSize: 12, color: AppTheme.textMuted)),
            )
          else
            ConstrainedBox(
              constraints: const BoxConstraints(maxHeight: 180),
              child: ListView.separated(
                shrinkWrap: true,
                itemCount: _responsables.length,
                separatorBuilder: (_, __) => const Divider(height: 1),
                itemBuilder: (ctx, i) {
                  final resp = _responsables[i];
                  final nombre = resp['nombre_completo'] ?? resp['username'] ?? 'Operario';
                  final rol = resp['nombre_rol'] ?? 'Operario';
                  return ListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    leading: CircleAvatar(
                      radius: 14,
                      backgroundColor: AppTheme.primary.withValues(alpha: 0.2),
                      child: Text(nombre[0].toUpperCase(), style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.primary)),
                    ),
                    title: Text(nombre, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                    subtitle: Text(rol, style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                  );
                },
              ),
            ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _buildEstadoBtn(String key, String label, Color color) {
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: OutlinedButton(
        style: OutlinedButton.styleFrom(
          foregroundColor: color,
          side: BorderSide(color: color),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        ),
        onPressed: () => widget.onCambioEstado(key),
        child: Text(label, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
      ),
    );
  }
}
