import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../services/auth_provider.dart';
import '../services/obra_service.dart';
import '../services/unidad_service.dart';
import '../theme/app_theme.dart';
import '../widgets/construction_widgets.dart';
import '../widgets/ev_widgets.dart';
import 'avances_obra_screen.dart';
import 'consultas_tecnicas_screen.dart';
import 'ordenes_trabajo_screen.dart';
import 'incidencias_screen.dart';

class ProyectoDetalleScreen extends StatefulWidget {
  final int idObra;
  final String codigo;
  final String nombre;
  final String tipoNombre;
  final String estado;
  final String ubicacion;
  final String fechaInicio;

  const ProyectoDetalleScreen({
    super.key,
    required this.idObra,
    required this.codigo,
    required this.nombre,
    required this.tipoNombre,
    required this.estado,
    required this.ubicacion,
    required this.fechaInicio,
  });

  @override
  State<ProyectoDetalleScreen> createState() => _ProyectoDetalleScreenState();
}

class _ProyectoDetalleScreenState extends State<ProyectoDetalleScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final ObraService _obraService = ObraService();
  final UnidadService _unidadService = UnidadService();

  late Future<List<Map<String, dynamic>>> _futureEstructura;
  late Future<List<Map<String, dynamic>>> _futureUnidades;
  late Future<Map<String, dynamic>> _futureDetalle;

  String _filtroTexto = '';
  final TextEditingController _searchCtrl = TextEditingController();
  String _filtroEstadoUnidad = 'TODOS';

  String _estadoObraActual = '';

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _estadoObraActual = widget.estado;
    _cargarDatos();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchCtrl.dispose();
    super.dispose();
  }

  void _cargarDatos() {
    _futureEstructura = _obraService.obtenerEstructura(widget.idObra);
    _futureUnidades = _unidadService.listarUnidades(widget.idObra);
    _futureDetalle = _obraService.obtenerDetalleProyecto(widget.idObra);
  }

  Color _colorTipoElemento(String tipo, bool isDark) {
    switch (tipo.toUpperCase()) {
      case 'TORRE':
      case 'BLOQUE':
        return isDark ? const Color(0xFFFB923C) : AppTheme.primary;
      case 'NIVEL':
        return isDark ? const Color(0xFF38BDF8) : AppTheme.info;
      case 'SECTOR':
      case 'ÁREA':
      case 'AREA':
        return isDark ? const Color(0xFF34D399) : AppTheme.success;
      case 'ETAPA':
      case 'AMBIENTE':
        return isDark ? const Color(0xFFA78BFA) : const Color(0xFF8B5CF6);
      default:
        return isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);
    }
  }

  IconData _iconoTipoElemento(String tipo) {
    switch (tipo.toUpperCase()) {
      case 'TORRE':
        return Icons.apartment_rounded;
      case 'BLOQUE':
        return Icons.domain_rounded;
      case 'NIVEL':
        return Icons.layers_rounded;
      case 'SECTOR':
        return Icons.grid_view_rounded;
      case 'ÁREA':
      case 'AREA':
        return Icons.straighten_rounded;
      case 'ETAPA':
        return Icons.flag_rounded;
      case 'AMBIENTE':
        return Icons.meeting_room_rounded;
      default:
        return Icons.folder_open_rounded;
    }
  }

  int _contarNodos(List<Map<String, dynamic>> nodos, String tipo) {
    int total = 0;
    for (var n in nodos) {
      if ((n['tipo'] ?? '').toString().toUpperCase() == tipo.toUpperCase()) {
        total++;
      }
      final rawHijos = n['hijos'];
      if (rawHijos is List && rawHijos.isNotEmpty) {
        final List<Map<String, dynamic>> hijos =
            rawHijos.map((h) => Map<String, dynamic>.from(h as Map)).toList();
        total += _contarNodos(hijos, tipo);
      }
    }
    return total;
  }

  bool _nodoCoincide(Map<String, dynamic> nodo, String query) {
    if (query.isEmpty) return true;
    final nombre = (nodo['nombre'] ?? '').toString().toLowerCase();
    final tipo = (nodo['tipo'] ?? '').toString().toLowerCase();
    if (nombre.contains(query) || tipo.contains(query)) return true;

    final rawHijos = nodo['hijos'];
    if (rawHijos is List && rawHijos.isNotEmpty) {
      for (var h in rawHijos) {
        if (_nodoCoincide(Map<String, dynamic>.from(h as Map), query)) {
          return true;
        }
      }
    }
    return false;
  }

  bool _puedeModificarObra() {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    return auth.hasPermission('Modificar_obras') ||
        auth.esAdminGlobal ||
        auth.esAdminEmpresa ||
        auth.esJefeObra;
  }

  // Lista plana de nodos de estructura para desplegables
  List<Map<String, dynamic>> _aplanarNodos(List<Map<String, dynamic>> nodos, [int nivel = 0]) {
    final List<Map<String, dynamic>> result = [];
    for (var n in nodos) {
      final prefix = '  ' * nivel + (nivel > 0 ? '└ ' : '');
      result.add({
        'id': n['id_estructura'],
        'nombre': '$prefix${n['nombre']} (${n['tipo']})',
        'raw_nombre': n['nombre'],
      });
      final rawHijos = n['hijos'];
      if (rawHijos is List && rawHijos.isNotEmpty) {
        final List<Map<String, dynamic>> hijos =
            rawHijos.map((h) => Map<String, dynamic>.from(h as Map)).toList();
        result.addAll(_aplanarNodos(hijos, nivel + 1));
      }
    }
    return result;
  }

  // ── GESTIÓN DE ELEMENTOS DE ESTRUCTURA ────────────────────────────────────
  void _mostrarModalElementoEstructura({
    int? idEstructura,
    int? idPadre,
    String? nombrePadre,
    Map<String, dynamic>? elementoExistente,
  }) {
    final esEdicion = elementoExistente != null;
    final nombreCtrl = TextEditingController(
      text: elementoExistente?['nombre']?.toString() ?? '',
    );
    final descCtrl = TextEditingController(
      text: elementoExistente?['descripcion']?.toString() ?? '',
    );
    final ordenCtrl = TextEditingController(
      text: elementoExistente?['orden']?.toString() ?? '0',
    );
    String tipoSeleccionado = (elementoExistente?['tipo'] ?? 'NIVEL')
        .toString()
        .toUpperCase();

    // 9 tipos oficiales del sistema
    final tiposDisponibles = [
      'SECTOR',
      'ETAPA',
      'BLOQUE',
      'TORRE',
      'NIVEL',
      'LOTE',
      'ÁREA',
      'AMBIENTE',
      'OTRO',
    ];
    if (!tiposDisponibles.contains(tipoSeleccionado)) {
      tiposDisponibles.add(tipoSeleccionado);
    }
    bool guardando = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            final isDark = Theme.of(context).brightness == Brightness.dark;
            final sheetBg = isDark ? const Color(0xFF131D31) : Colors.white;
            final titleColor =
                isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

            return Container(
              padding: EdgeInsets.fromLTRB(
                20,
                16,
                20,
                24 + MediaQuery.of(context).viewInsets.bottom,
              ),
              decoration: BoxDecoration(
                color: sheetBg,
                borderRadius:
                    const BorderRadius.vertical(top: Radius.circular(20)),
              ),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Center(
                      child: Container(
                        width: 36,
                        height: 4,
                        decoration: BoxDecoration(
                          color: isDark
                              ? const Color(0xFF334155)
                              : const Color(0xFFCBD5E1),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      esEdicion
                          ? 'Editar Elemento de Estructura'
                          : (nombrePadre != null
                              ? 'Agregar Sub-elemento en "$nombrePadre"'
                              : 'Nuevo Elemento Principal'),
                      style: GoogleFonts.inter(
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                        color: titleColor,
                      ),
                    ),
                    const SizedBox(height: 14),
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: [
                          _buildQuickTypeSelector('TORRE', 'Torre / Bloque', tipoSeleccionado == 'TORRE' || tipoSeleccionado == 'BLOQUE', () {
                            setModalState(() => tipoSeleccionado = 'TORRE');
                          }, isDark),
                          const SizedBox(width: 8),
                          _buildQuickTypeSelector('NIVEL', 'Nivel / Piso', tipoSeleccionado == 'NIVEL', () {
                            setModalState(() => tipoSeleccionado = 'NIVEL');
                          }, isDark),
                          const SizedBox(width: 8),
                          _buildQuickTypeSelector('SECTOR', 'Sector', tipoSeleccionado == 'SECTOR', () {
                            setModalState(() => tipoSeleccionado = 'SECTOR');
                          }, isDark),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),
                    TextField(
                      controller: nombreCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Nombre del elemento *',
                        hintText: 'Ej: Torre A, Piso 2, Sector Este',
                      ),
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      initialValue: tipoSeleccionado,
                      decoration:
                          const InputDecoration(labelText: 'Tipo de elemento *'),
                      items: tiposDisponibles
                          .map((t) =>
                              DropdownMenuItem(value: t, child: Text(t)))
                          .toList(),
                      onChanged: (v) =>
                          setModalState(() => tipoSeleccionado = v ?? 'NIVEL'),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: descCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Descripción (Opcional)',
                        hintText: 'Detalles adicionales del sector o nivel',
                      ),
                    ),
                    const SizedBox(height: 16),
                    ObratecPrimaryButton(
                      label:
                          esEdicion ? 'Actualizar Elemento' : 'Guardar Elemento',
                      loading: guardando,
                      onPressed: () async {
                        final nombre = nombreCtrl.text.trim();
                        if (nombre.isEmpty) return;
                        setModalState(() => guardando = true);
                        try {
                          final payload = <String, dynamic>{
                            'id_obra': widget.idObra,
                            'nombre': nombre,
                            'tipo': tipoSeleccionado,
                            'descripcion': descCtrl.text.trim(),
                            'orden': int.tryParse(ordenCtrl.text.trim()) ?? 0,
                          };
                          if (esEdicion) {
                            await _obraService.actualizarElementoEstructura(
                              widget.idObra,
                              idEstructura!,
                              payload,
                            );
                          } else {
                            if (idPadre != null) payload['id_padre'] = idPadre;
                            await _obraService.crearElementoEstructura(
                              widget.idObra,
                              payload,
                            );
                          }
                          if (!ctx.mounted) return;
                          Navigator.pop(ctx);
                          setState(() {
                            _futureEstructura =
                                _obraService.obtenerEstructura(widget.idObra);
                          });
                        } catch (e) {
                          setModalState(() => guardando = false);
                          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                            content: Text(
                                e.toString().replaceAll('Exception: ', '')),
                            backgroundColor: AppTheme.error,
                          ));
                        }
                      },
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  Future<void> _confirmarEliminarElemento(Map<String, dynamic> nodo) async {
    final idEstructura =
        int.tryParse(nodo['id_estructura']?.toString() ?? '');
    if (idEstructura == null) return;
    final nombre = nodo['nombre'] ?? 'Elemento';

    final conf = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar Elemento'),
        content: Text(
          '¿Está seguro de eliminar "$nombre"? Los sub-elementos interiores también serán eliminados.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Eliminar', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (conf == true) {
      try {
        await _obraService.eliminarElementoEstructura(
            widget.idObra, idEstructura);
        setState(() {
          _futureEstructura = _obraService.obtenerEstructura(widget.idObra);
        });
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Elemento eliminado correctamente.'),
            backgroundColor: AppTheme.success,
          ));
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e.toString().replaceAll('Exception: ', '')),
            backgroundColor: AppTheme.error,
          ));
        }
      }
    }
  }

  // ── GESTIÓN DE UNIDADES DE CONSTRUCCIÓN (CREAR / EDITAR) ───────────────────
  void _mostrarModalUnidad({
    Map<String, dynamic>? unidadExistente,
    int? preIdEstructura,
  }) async {
    final esEdicion = unidadExistente != null;
    final idUnidad = int.tryParse(unidadExistente?['id_unidad']?.toString() ?? '0') ?? 0;

    final nombreCtrl = TextEditingController(
      text: unidadExistente?['nombre']?.toString() ?? '',
    );
    final descCtrl = TextEditingController(
      text: unidadExistente?['descripcion']?.toString() ?? '',
    );
    final supCtrl = TextEditingController(
      text: unidadExistente?['superficie']?.toString() ??
          unidadExistente?['area_m2']?.toString() ??
          '',
    );
    final plantasCtrl = TextEditingController(
      text: unidadExistente?['cantidad_plantas']?.toString() ?? '1',
    );

    String tipoUnidad = (unidadExistente?['tipo_unidad'] ??
            unidadExistente?['tipo'] ??
            'DEPARTAMENTO')
        .toString()
        .toUpperCase();
    final tiposUnidadDisponibles = [
      'VIVIENDA',
      'DEPARTAMENTO',
      'LOCAL',
      'LOTE',
      'OFICINA',
      'OTRO',
    ];
    if (!tiposUnidadDisponibles.contains(tipoUnidad)) {
      tiposUnidadDisponibles.add(tipoUnidad);
    }

    String estadoUnidad = (unidadExistente?['estado'] ?? 'PLANIFICADO')
        .toString()
        .toUpperCase();

    int? idEstructuraPadre = preIdEstructura ??
        int.tryParse(unidadExistente?['id_padre']?.toString() ??
            unidadExistente?['id_estructura']?.toString() ??
            '');

    // Cargar nodos de estructura para seleccionar padre
    List<Map<String, dynamic>> nodosDisponibles = [];
    try {
      final estructura = await _futureEstructura;
      nodosDisponibles = _aplanarNodos(estructura);
    } catch (_) {}

    if (!mounted) return;
    bool guardando = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            final isDark = Theme.of(context).brightness == Brightness.dark;
            final sheetBg = isDark ? const Color(0xFF131D31) : Colors.white;
            final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

            return Container(
              padding: EdgeInsets.fromLTRB(
                20,
                16,
                20,
                24 + MediaQuery.of(context).viewInsets.bottom,
              ),
              decoration: BoxDecoration(
                color: sheetBg,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
              ),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Center(
                      child: Container(
                        width: 36,
                        height: 4,
                        decoration: BoxDecoration(
                          color: isDark ? const Color(0xFF334155) : const Color(0xFFCBD5E1),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      esEdicion ? 'Editar Unidad de Construcción' : 'Registrar Nueva Unidad',
                      style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w800, color: titleColor),
                    ),
                    const SizedBox(height: 14),

                    TextField(
                      controller: nombreCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Nombre / Código de Unidad *',
                        hintText: 'Ej: Dpto 201, Local 4, Casa Lote 12',
                      ),
                    ),
                    const SizedBox(height: 12),

                    DropdownButtonFormField<String>(
                      initialValue: tipoUnidad,
                      decoration: const InputDecoration(labelText: 'Tipo de Unidad *'),
                      items: tiposUnidadDisponibles
                          .map((t) => DropdownMenuItem(value: t, child: Text(t.replaceAll('_', ' '))))
                          .toList(),
                      onChanged: (v) => setModalState(() => tipoUnidad = v ?? 'DEPARTAMENTO'),
                    ),
                    const SizedBox(height: 12),

                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: supCtrl,
                            keyboardType: const TextInputType.numberWithOptions(decimal: true),
                            decoration: const InputDecoration(
                              labelText: 'Superficie (m²)',
                              hintText: 'Ej: 85.5',
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: TextField(
                            controller: plantasCtrl,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(
                              labelText: 'Plantas / Pisos',
                              hintText: 'Ej: 1',
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // Selector de nivel / sector de la estructura
                    DropdownButtonFormField<int?>(
                      initialValue: nodosDisponibles.any((n) => n['id'] == idEstructuraPadre)
                          ? idEstructuraPadre
                          : null,
                      decoration: const InputDecoration(
                        labelText: 'Asignar a Nivel / Sector (Estructura)',
                        hintText: 'Seleccione nivel o bloque',
                      ),
                      isExpanded: true,
                      items: [
                        const DropdownMenuItem<int?>(
                          value: null,
                          child: Text('Sin asignación directa'),
                        ),
                        ...nodosDisponibles.map((n) {
                          return DropdownMenuItem<int?>(
                            value: n['id'] as int?,
                            child: Text(
                              n['nombre']?.toString() ?? '',
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(fontSize: 12),
                            ),
                          );
                        }),
                      ],
                      onChanged: (v) => setModalState(() => idEstructuraPadre = v),
                    ),
                    const SizedBox(height: 12),

                    if (!esEdicion) ...[
                      DropdownButtonFormField<String>(
                        initialValue: estadoUnidad,
                        decoration: const InputDecoration(labelText: 'Estado Inicial'),
                        items: ['PLANIFICADO', 'EN_CONSTRUCCION', 'FINALIZADO', 'SUSPENDIDO']
                            .map((e) => DropdownMenuItem(value: e, child: Text(e.replaceAll('_', ' '))))
                            .toList(),
                        onChanged: (v) => setModalState(() => estadoUnidad = v ?? 'PLANIFICADO'),
                      ),
                      const SizedBox(height: 12),
                    ],

                    TextField(
                      controller: descCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Descripción / Acabados (Opcional)',
                        hintText: 'Ej: Vista a la avenida, piso flotante',
                      ),
                    ),
                    const SizedBox(height: 18),

                    ObratecPrimaryButton(
                      label: esEdicion ? 'Guardar Cambios' : 'Registrar Unidad',
                      loading: guardando,
                      onPressed: () async {
                        final nombre = nombreCtrl.text.trim();
                        if (nombre.isEmpty) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('El nombre de la unidad es obligatorio.')),
                          );
                          return;
                        }
                        setModalState(() => guardando = true);
                        try {
                          final payload = <String, dynamic>{
                            'nombre': nombre,
                            'tipo_unidad': tipoUnidad,
                            'descripcion': descCtrl.text.trim(),
                            'superficie': double.tryParse(supCtrl.text.trim()) ?? 0,
                            'cantidad_plantas': int.tryParse(plantasCtrl.text.trim()) ?? 1,
                          };
                          if (idEstructuraPadre != null) {
                            payload['id_padre'] = idEstructuraPadre;
                          }

                          if (esEdicion) {
                            await _unidadService.actualizarUnidad(widget.idObra, idUnidad, payload);
                          } else {
                            payload['estado'] = estadoUnidad;
                            await _unidadService.crearUnidad(widget.idObra, payload);
                          }

                          if (!ctx.mounted) return;
                          Navigator.pop(ctx);
                          setState(() {
                            _futureUnidades = _unidadService.listarUnidades(widget.idObra);
                          });
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                              content: Text(esEdicion
                                  ? 'Unidad actualizada correctamente.'
                                  : 'Unidad registrada exitosamente.'),
                              backgroundColor: AppTheme.success,
                            ));
                          }
                        } catch (e) {
                          setModalState(() => guardando = false);
                          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                            content: Text(e.toString().replaceAll('Exception: ', '')),
                            backgroundColor: AppTheme.error,
                          ));
                        }
                      },
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  Future<void> _confirmarEliminarUnidad(Map<String, dynamic> unidad) async {
    final idUnidad = int.tryParse(unidad['id_unidad']?.toString() ?? '0') ?? 0;
    final nombre = unidad['nombre'] ?? unidad['codigo'] ?? 'Unidad';

    final conf = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar Unidad'),
        content: Text('¿Está seguro de eliminar la unidad "$nombre"? Esta acción no se puede deshacer.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Eliminar', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (conf == true) {
      try {
        await _unidadService.eliminarUnidad(widget.idObra, idUnidad);
        setState(() {
          _futureUnidades = _unidadService.listarUnidades(widget.idObra);
        });
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Unidad eliminada correctamente.'),
            backgroundColor: AppTheme.success,
          ));
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e.toString().replaceAll('Exception: ', '')),
            backgroundColor: AppTheme.error,
          ));
        }
      }
    }
  }

  // ── MODAL CAMBIO DE ESTADO DE UNIDAD ──────────────────────────────────────
  void _mostrarModalDetalleUnidad(Map<String, dynamic> unidad) {
    final idUnidad = int.tryParse(unidad['id_unidad']?.toString() ?? '0') ?? 0;
    String estadoActual = (unidad['estado'] ?? 'PLANIFICADO').toString().toUpperCase();
    final obsCtrl = TextEditingController();
    bool guardando = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            final isDark = Theme.of(context).brightness == Brightness.dark;
            final sheetBg = isDark ? const Color(0xFF131D31) : Colors.white;
            final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
            final subColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);
            final dividerColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);

            final codigo = unidad['codigo']?.toString() ?? unidad['nombre']?.toString() ?? 'U-00';
            final tipo = (unidad['tipo_unidad'] ?? unidad['tipo'] ?? 'DEPARTAMENTO').toString();
            final area = (unidad['superficie'] ?? unidad['area_m2'] ?? '0').toString();
            final precio = unidad['precio']?.toString() ?? '-';

            return Container(
              padding: EdgeInsets.fromLTRB(20, 16, 20, 24 + MediaQuery.of(context).viewInsets.bottom),
              decoration: BoxDecoration(
                color: sheetBg,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
              ),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Center(
                      child: Container(
                        width: 36,
                        height: 4,
                        decoration: BoxDecoration(
                          color: isDark ? const Color(0xFF334155) : const Color(0xFFCBD5E1),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: isDark ? const Color(0xFF2E1C14) : const Color(0xFFFFF7ED),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: const Icon(Icons.meeting_room_rounded, color: AppTheme.primary, size: 20),
                            ),
                            const SizedBox(width: 10),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  codigo,
                                  style: GoogleFonts.inter(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w900,
                                    color: titleColor,
                                  ),
                                ),
                                Text(
                                  tipo,
                                  style: GoogleFonts.inter(fontSize: 11.5, color: subColor),
                                ),
                              ],
                            ),
                          ],
                        ),
                        ConstructionStatusBadge(status: estadoActual, compact: true),
                      ],
                    ),
                    const SizedBox(height: 14),
                    Divider(color: dividerColor),
                    const SizedBox(height: 12),

                    Row(
                      children: [
                        Expanded(child: _buildInfoItem('Área Construida', '$area m²', subColor, titleColor)),
                        Expanded(child: _buildInfoItem('Precio', '$precio BOB', subColor, titleColor)),
                      ],
                    ),
                    const SizedBox(height: 16),

                    if (_puedeModificarObra())
                      Text(
                        'ACTUALIZAR ESTADO DE CONSTRUCCIÓN',
                        style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.primary),
                      ),
                    const SizedBox(height: 8),

                    Wrap(
                      spacing: 8,
                      runSpacing: 6,
                      children: ['PLANIFICADO', 'EN_CONSTRUCCION', 'FINALIZADO', 'SUSPENDIDO'].map((est) {
                        final sel = estadoActual == est;
                        return ChoiceChip(
                          label: Text(est.replaceAll('_', ' ')),
                          selected: sel,
                          selectedColor: AppTheme.primary,
                          labelStyle: TextStyle(
                            color: sel ? Colors.white : subColor,
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                          ),
                          onSelected: (selected) {
                            if (selected) {
                              setModalState(() => estadoActual = est);
                            }
                          },
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 12),

                    TextField(
                      controller: obsCtrl,
                      style: GoogleFonts.inter(fontSize: 13, color: titleColor),
                      decoration: const InputDecoration(
                        labelText: 'Observación del cambio de estado',
                        hintText: 'Ej: Inicio de obras de acabado e instalaciones',
                      ),
                    ),
                    const SizedBox(height: 18),

                    ObratecPrimaryButton(
                      label: 'Guardar Estado',
                      loading: guardando,
                      icon: Icons.check_circle_outline_rounded,
                      onPressed: () async {
                        setModalState(() => guardando = true);
                        try {
                          await _unidadService.cambiarEstadoUnidad(
                            idObra: widget.idObra,
                            idUnidad: idUnidad,
                            nuevoEstado: estadoActual,
                            observacion: obsCtrl.text.trim(),
                          );

                          if (!ctx.mounted) return;
                          Navigator.pop(ctx);

                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('Estado de la unidad actualizado exitosamente.'),
                                backgroundColor: AppTheme.success,
                              ),
                            );
                            setState(() {
                              _futureUnidades = _unidadService.listarUnidades(widget.idObra);
                            });
                          }
                        } catch (e) {
                          setModalState(() => guardando = false);
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text(e.toString().replaceAll('Exception: ', '')), backgroundColor: AppTheme.error),
                            );
                          }
                        }
                      },
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  // ── GESTIÓN DE LA OBRA Y JEFES DE OBRA ─────────────────────────────────────
  void _mostrarModalCambiarEstadoObra() {
    String nuevoEstado = _estadoObraActual;
    bool guardando = false;

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            final isDark = Theme.of(context).brightness == Brightness.dark;
            final sheetBg = isDark ? const Color(0xFF131D31) : Colors.white;
            final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

            return Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: sheetBg,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Actualizar Estado de la Obra',
                      style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w800, color: titleColor)),
                  const SizedBox(height: 14),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: ['PLANIFICACION', 'ACTIVO', 'PAUSADO', 'FINALIZADO'].map((e) {
                      final sel = nuevoEstado == e;
                      return ChoiceChip(
                        label: Text(e == 'ACTIVO' ? 'EN EJECUCIÓN' : e),
                        selected: sel,
                        selectedColor: AppTheme.primary,
                        labelStyle: TextStyle(
                          color: sel ? Colors.white : (isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B)),
                          fontWeight: FontWeight.w700,
                          fontSize: 12,
                        ),
                        onSelected: (selected) {
                          if (selected) setModalState(() => nuevoEstado = e);
                        },
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 20),
                  ObratecPrimaryButton(
                    label: 'Confirmar Estado',
                    loading: guardando,
                    onPressed: () async {
                      setModalState(() => guardando = true);
                      try {
                        await _obraService.actualizarEstadoObra(widget.idObra, nuevoEstado);
                        if (!ctx.mounted) return;
                        Navigator.pop(ctx);
                        setState(() {
                          _estadoObraActual = nuevoEstado;
                          _futureDetalle = _obraService.obtenerDetalleProyecto(widget.idObra);
                        });
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                            content: Text('Estado de la obra actualizado exitosamente.'),
                            backgroundColor: AppTheme.success,
                          ));
                        }
                      } catch (e) {
                        setModalState(() => guardando = false);
                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                          content: Text(e.toString().replaceAll('Exception: ', '')),
                          backgroundColor: AppTheme.error,
                        ));
                      }
                    },
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  void _mostrarModalAsignarJefeObra(List<dynamic> yaAsignados) {
    bool cargando = true;
    List<Map<String, dynamic>> jefesDisponibles = [];
    int? idSeleccionado;
    bool guardando = false;

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            if (cargando) {
              _obraService.listarJefesObraDisponibles().then((todos) {
                if (ctx.mounted) {
                  final idsAsignados = yaAsignados.map((r) => int.tryParse(r['id_usuario']?.toString() ?? '')).toSet();
                  setModalState(() {
                    jefesDisponibles = todos.where((u) {
                      final id = int.tryParse(u['nro_usuario']?.toString() ?? '');
                      return id != null && !idsAsignados.contains(id);
                    }).toList();
                    cargando = false;
                  });
                }
              }).catchError((_) {
                if (ctx.mounted) {
                  setModalState(() => cargando = false);
                }
              });
            }
            final isDark = Theme.of(context).brightness == Brightness.dark;
            final sheetBg = isDark ? const Color(0xFF131D31) : Colors.white;
            final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

            return Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: sheetBg,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Asignar Jefe de Obra',
                      style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w800, color: titleColor)),
                  const SizedBox(height: 6),
                  Text('Seleccione un profesional con rol Jefe de Obra para asignar a este proyecto:',
                      style: GoogleFonts.inter(fontSize: 12, color: const Color(0xFF94A3B8))),
                  const SizedBox(height: 14),

                  if (cargando)
                    const Center(child: CircularProgressIndicator(color: AppTheme.primary))
                  else if (jefesDisponibles.isEmpty)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 12.0),
                      child: Text('No hay más usuarios con rol Jefe de Obra disponibles para asignar.'),
                    )
                  else
                    DropdownButtonFormField<int>(
                      initialValue: idSeleccionado,
                      decoration: const InputDecoration(labelText: 'Jefe de Obra'),
                      items: jefesDisponibles.map((j) {
                        final id = int.parse(j['nro_usuario'].toString());
                        final nombre = j['nombre_completo'] ?? j['nombre_usuario'] ?? 'Usuario';
                        return DropdownMenuItem(value: id, child: Text(nombre));
                      }).toList(),
                      onChanged: (v) => setModalState(() => idSeleccionado = v),
                    ),

                  const SizedBox(height: 20),
                  ObratecPrimaryButton(
                    label: 'Asignar a la Obra',
                    loading: guardando,
                    onPressed: idSeleccionado == null ? null : () async {
                      if (idSeleccionado == null) return;
                      setModalState(() => guardando = true);
                      try {
                        await _obraService.asignarResponsable(widget.idObra, idSeleccionado!);
                        if (!ctx.mounted) return;
                        Navigator.pop(ctx);
                        setState(() {
                          _futureDetalle = _obraService.obtenerDetalleProyecto(widget.idObra);
                        });
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                            content: Text('Jefe de Obra asignado exitosamente.'),
                            backgroundColor: AppTheme.success,
                          ));
                        }
                      } catch (e) {
                        setModalState(() => guardando = false);
                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                          content: Text(e.toString().replaceAll('Exception: ', '')),
                          backgroundColor: AppTheme.error,
                        ));
                      }
                    },
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  Future<void> _retirarResponsable(int idUsuario, String nombre) async {
    final conf = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Retirar Responsable'),
        content: Text('¿Está seguro de retirar a "$nombre" como responsable de esta obra?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Retirar', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (conf == true) {
      try {
        await _obraService.retirarResponsable(widget.idObra, idUsuario);
        setState(() {
          _futureDetalle = _obraService.obtenerDetalleProyecto(widget.idObra);
        });
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Responsable retirado del proyecto.'),
            backgroundColor: AppTheme.success,
          ));
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e.toString().replaceAll('Exception: ', '')),
            backgroundColor: AppTheme.error,
          ));
        }
      }
    }
  }

  Widget _buildInfoItem(String label, String val, Color subColor, Color titleColor) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: GoogleFonts.inter(fontSize: 11, color: subColor, fontWeight: FontWeight.w500)),
        const SizedBox(height: 2),
        Text(val, style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w800, color: titleColor)),
      ],
    );
  }

  void _mostrarMenuAcciones() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        final isDark = Theme.of(ctx).brightness == Brightness.dark;
        final sheetBg = isDark ? const Color(0xFF131D31) : Colors.white;
        final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

        return Container(
          decoration: BoxDecoration(
            color: sheetBg,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 36,
                height: 4,
                decoration: BoxDecoration(
                  color: isDark ? const Color(0xFF334155) : const Color(0xFFCBD5E1),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'Acciones de Proyecto',
                style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w800, color: titleColor),
              ),
              const SizedBox(height: 12),
              if (_puedeModificarObra())
                ListTile(
                  leading: const Icon(Icons.published_with_changes_rounded, color: AppTheme.primary),
                  title: const Text('Cambiar Estado de Obra'),
                  onTap: () {
                    Navigator.pop(ctx);
                    _mostrarModalCambiarEstadoObra();
                  },
                ),
              ListTile(
                leading: const Icon(Icons.help_outline_rounded, color: Color(0xFF10B981)),
                title: const Text('Consultas Técnicas'),
                onTap: () {
                  Navigator.pop(ctx);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ConsultasTecnicasScreen(
                        idObraFiltro: widget.idObra,
                        nombreObraFiltro: widget.nombre,
                      ),
                    ),
                  );
                },
              ),
              ListTile(
                leading: const Icon(Icons.timeline_rounded, color: Color(0xFF38BDF8)),
                title: const Text('Ver Avances Físicos'),
                onTap: () {
                  Navigator.pop(ctx);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => AvancesObraScreen(
                        idObra: widget.idObra,
                        nombreObra: widget.nombre,
                        codigoObra: widget.codigo,
                      ),
                    ),
                  );
                },
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final tabBg = isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC);
    final tabBoxBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final tabBorder = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final indicatorBg = isDark ? const Color(0xFFF97316) : const Color(0xFF0F172A);

    return Scaffold(
      bottomNavigationBar: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: isDark ? const Color(0xFF0F172A) : Colors.white,
          border: Border(top: BorderSide(color: tabBorder)),
        ),
        child: Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => AvancesObraScreen(
                      idObra: widget.idObra,
                      nombreObra: widget.nombre,
                      codigoObra: widget.codigo,
                    ),
                  ),
                ),
                icon: const Icon(Icons.show_chart_rounded, size: 18),
                label: Text('Ver avances', style: GoogleFonts.inter(fontWeight: FontWeight.w700, fontSize: 13)),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  side: BorderSide(color: tabBorder),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: ElevatedButton(
                onPressed: _mostrarMenuAcciones,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                child: Text('Más acciones', style: GoogleFonts.inter(fontWeight: FontWeight.w800, fontSize: 13)),
              ),
            ),
          ],
        ),
      ),
      body: SafeArea(
        child: NestedScrollView(
          headerSliverBuilder: (context, innerBoxIsScrolled) {
            return [
              // HERO HEADER SÓLIDO
              SliverToBoxAdapter(
                child: Container(
                  color: const Color(0xFF0F172A),
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          InkWell(
                            onTap: () => Navigator.pop(context),
                            borderRadius: BorderRadius.circular(8),
                            child: Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: Colors.white.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: const Icon(Icons.arrow_back_rounded, color: Colors.white, size: 20),
                            ),
                          ),
                          Row(
                            children: [
                              IconButton(
                                constraints: const BoxConstraints(),
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                                icon: const Icon(Icons.contact_support_outlined, color: Colors.white, size: 20),
                                tooltip: 'Consultas Técnicas',
                                onPressed: () => Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => ConsultasTecnicasScreen(
                                      idObraFiltro: widget.idObra,
                                      nombreObraFiltro: widget.nombre,
                                    ),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 4),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(alpha: 0.1),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text(
                                  widget.codigo,
                                  style: GoogleFonts.jetBrainsMono(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w700,
                                    color: const Color(0xFFFFF7ED),
                                    letterSpacing: 0.5,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 8),
                              InkWell(
                                onTap: _puedeModificarObra() ? _mostrarModalCambiarEstadoObra : null,
                                child: ConstructionStatusBadge(
                                  status: _estadoObraActual.isNotEmpty ? _estadoObraActual : widget.estado,
                                  compact: true,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),

                      Text(
                        widget.nombre,
                        style: GoogleFonts.inter(
                          fontSize: 20,
                          fontWeight: FontWeight.w900,
                          color: Colors.white,
                          letterSpacing: -0.3,
                          height: 1.25,
                        ),
                      ),
                      const SizedBox(height: 8),

                      Wrap(
                        spacing: 8,
                        runSpacing: 6,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              widget.tipoNombre,
                              style: GoogleFonts.inter(fontSize: 11, color: Colors.white, fontWeight: FontWeight.w600),
                            ),
                          ),
                          if (widget.ubicacion.isNotEmpty)
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(Icons.location_on_outlined, size: 13, color: AppTheme.primaryLight),
                                const SizedBox(width: 4),
                                Text(
                                  widget.ubicacion,
                                  style: GoogleFonts.inter(fontSize: 11.5, color: const Color(0xFF94A3B8), fontWeight: FontWeight.w500),
                                ),
                              ],
                            ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),

              // SEGMENTED TAB SWITCHER (4 TABS)
              SliverPersistentHeader(
                pinned: true,
                delegate: _SegmentedTabHeaderDelegate(
                  child: Container(
                    color: tabBg,
                    padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),
                    child: Container(
                      height: 42,
                      padding: const EdgeInsets.all(3),
                      decoration: BoxDecoration(
                        color: tabBoxBg,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: tabBorder),
                      ),
                      child: TabBar(
                        controller: _tabController,
                        indicator: BoxDecoration(
                          color: indicatorBg,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        labelColor: Colors.white,
                        unselectedLabelColor: isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B),
                        labelStyle: GoogleFonts.inter(fontSize: 11.5, fontWeight: FontWeight.w800),
                        unselectedLabelStyle: GoogleFonts.inter(fontSize: 11.5, fontWeight: FontWeight.w600),
                        labelPadding: const EdgeInsets.symmetric(horizontal: 4),
                        dividerColor: Colors.transparent,
                        tabs: const [
                          Tab(text: 'Resumen'),
                          Tab(text: 'Estructura'),
                          Tab(text: 'Unidades'),
                          Tab(text: 'Equipo'),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ];
          },
          body: TabBarView(
            controller: _tabController,
            children: [
              _buildTabResumen(isDark),
              _buildTabEstructura(isDark),
              _buildTabUnidades(isDark),
              _buildTabEquipoYModulos(isDark),
            ],
          ),
        ),
      ),
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // TAB 0: RESUMEN DEL PROYECTO (Prototipo Screens 4 y 10)
  // ──────────────────────────────────────────────────────────────────────────
  Widget _buildTabResumen(bool isDark) {
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
    final subColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);

    return FutureBuilder<List<dynamic>>(
      future: Future.wait([_futureEstructura, _futureDetalle]),
      builder: (context, snapshot) {
        final List<Map<String, dynamic>> estructura = (snapshot.data != null && snapshot.data!.isNotEmpty)
            ? List<Map<String, dynamic>>.from(snapshot.data![0] as List)
            : [];
        final Map<String, dynamic> detalle = (snapshot.data != null && snapshot.data!.length > 1)
            ? Map<String, dynamic>.from(snapshot.data![1] as Map)
            : {};

        final totalTorres = _contarNodos(estructura, 'TORRE') + _contarNodos(estructura, 'BLOQUE');
        final totalNiveles = _contarNodos(estructura, 'NIVEL');
        final totalSectores = _contarNodos(estructura, 'SECTOR');

        final fechaFin = detalle['fecha_fin']?.toString() ?? '-';
        final empresaNombre = detalle['empresa_nombre']?.toString() ??
            detalle['nombre_empresa']?.toString() ??
            'Constructora Obratec';
        final supervisor = detalle['supervisor_nombre']?.toString() ??
            detalle['nombre_supervisor']?.toString() ??
            'No asignado';
        final cliente = detalle['cliente_nombre']?.toString() ?? '-';

        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Contadores (Torres/Bloques, Niveles, Sectores)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              decoration: BoxDecoration(
                color: cardBg,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: borderColor),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildWbsMetricBadge('$totalTorres', 'Torres/Bloques', AppTheme.primary, titleColor),
                  Container(height: 24, width: 1, color: borderColor),
                  _buildWbsMetricBadge('$totalNiveles', 'Niveles', const Color(0xFF38BDF8), titleColor),
                  Container(height: 24, width: 1, color: borderColor),
                  _buildWbsMetricBadge('$totalSectores', 'Sectores', const Color(0xFF10B981), titleColor),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Información General
            Text(
              'Información general',
              style: GoogleFonts.inter(
                fontSize: 15,
                fontWeight: FontWeight.w800,
                color: titleColor,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: cardBg,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: borderColor),
              ),
              child: Column(
                children: [
                  _buildInfoDetailRow('Código', widget.codigo, subColor, titleColor),
                  Divider(height: 18, color: borderColor),
                  _buildInfoDetailRow('Estado', _estadoObraActual.isNotEmpty ? _estadoObraActual : widget.estado, subColor, titleColor, isBadge: true),
                  Divider(height: 18, color: borderColor),
                  _buildInfoDetailRow('Tipo', widget.tipoNombre, subColor, titleColor),
                  Divider(height: 18, color: borderColor),
                  _buildInfoDetailRow('Fecha inicio', widget.fechaInicio.isEmpty ? '-' : widget.fechaInicio, subColor, titleColor),
                  Divider(height: 18, color: borderColor),
                  _buildInfoDetailRow('Fecha fin', fechaFin, subColor, titleColor),
                  Divider(height: 18, color: borderColor),
                  _buildInfoDetailRow('Empresa', empresaNombre, subColor, titleColor),
                  if (supervisor != 'No asignado') ...[
                    Divider(height: 18, color: borderColor),
                    _buildInfoDetailRow('Supervisor', supervisor, subColor, titleColor),
                  ],
                  if (cliente != '-') ...[
                    Divider(height: 18, color: borderColor),
                    _buildInfoDetailRow('Cliente', cliente, subColor, titleColor),
                  ],
                ],
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildInfoDetailRow(String label, String val, Color subColor, Color titleColor, {bool isBadge = false}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: GoogleFonts.inter(fontSize: 12.5, color: subColor, fontWeight: FontWeight.w500),
        ),
        if (isBadge)
          ConstructionStatusBadge(status: val, compact: true)
        else
          Text(
            val,
            style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w700, color: titleColor),
          ),
      ],
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // TAB 3: MÓDULOS DEL PROYECTO Y EQUIPO (Prototipo Screen 11)
  // ──────────────────────────────────────────────────────────────────────────
  Widget _buildTabEquipoYModulos(bool isDark) {
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(
          'Módulos del Proyecto',
          style: GoogleFonts.inter(
            fontSize: 15,
            fontWeight: FontWeight.w800,
            color: titleColor,
          ),
        ),
        const SizedBox(height: 10),

        _buildModuleCard(
          icon: Icons.assignment_outlined,
          iconColor: const Color(0xFF6366F1),
          title: 'Órdenes de trabajo',
          subtitle: 'Asignaciones y tareas',
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const OrdenesTrabajoScreen())),
          isDark: isDark,
          cardBg: cardBg,
          borderColor: borderColor,
          titleColor: titleColor,
        ),
        const SizedBox(height: 10),

        _buildModuleCard(
          icon: Icons.warning_amber_rounded,
          iconColor: AppTheme.error,
          title: 'Incidencias',
          subtitle: 'Registro y seguimiento',
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const IncidenciasScreen())),
          isDark: isDark,
          cardBg: cardBg,
          borderColor: borderColor,
          titleColor: titleColor,
        ),
        const SizedBox(height: 10),

        _buildModuleCard(
          icon: Icons.help_outline_rounded,
          iconColor: const Color(0xFF10B981),
          title: 'Consultas técnicas',
          subtitle: 'Preguntas y respuestas',
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => ConsultasTecnicasScreen(
                idObraFiltro: widget.idObra,
                nombreObraFiltro: widget.nombre,
              ),
            ),
          ),
          isDark: isDark,
          cardBg: cardBg,
          borderColor: borderColor,
          titleColor: titleColor,
        ),
        const SizedBox(height: 10),

        _buildModuleCard(
          icon: Icons.timeline_rounded,
          iconColor: const Color(0xFF38BDF8),
          title: 'Avances',
          subtitle: 'Seguimiento de obra',
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => AvancesObraScreen(
                idObra: widget.idObra,
                nombreObra: widget.nombre,
                codigoObra: widget.codigo,
              ),
            ),
          ),
          isDark: isDark,
          cardBg: cardBg,
          borderColor: borderColor,
          titleColor: titleColor,
        ),
        const SizedBox(height: 24),

        // Personal Asignado
        _buildPersonalSection(isDark, cardBg, borderColor, titleColor),
      ],
    );
  }

  Widget _buildModuleCard({
    required IconData icon,
    required Color iconColor,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
    required bool isDark,
    required Color cardBg,
    required Color borderColor,
    required Color titleColor,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderColor),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
        leading: Container(
          padding: const EdgeInsets.all(9),
          decoration: BoxDecoration(
            color: iconColor.withValues(alpha: isDark ? 0.18 : 0.1),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, color: iconColor, size: 22),
        ),
        title: Text(
          title,
          style: GoogleFonts.inter(fontSize: 13.5, fontWeight: FontWeight.w700, color: titleColor),
        ),
        subtitle: Text(
          subtitle,
          style: GoogleFonts.inter(fontSize: 11.5, color: const Color(0xFF94A3B8)),
        ),
        trailing: const Icon(Icons.chevron_right_rounded, color: Color(0xFF94A3B8), size: 20),
        onTap: onTap,
      ),
    );
  }

  Widget _buildPersonalSection(bool isDark, Color cardBg, Color borderColor, Color titleColor) {
    return FutureBuilder<Map<String, dynamic>>(
      future: _futureDetalle,
      builder: (context, snapshot) {
        final data = snapshot.data ?? {};
        final rawResponsables = data['responsables'];
        final List<dynamic> responsables = (rawResponsables is List) ? rawResponsables : [];

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Personal y Responsables',
                  style: GoogleFonts.inter(fontSize: 15, fontWeight: FontWeight.w800, color: titleColor),
                ),
                if (_puedeModificarObra())
                  TextButton.icon(
                    onPressed: () => _mostrarModalAsignarJefeObra(responsables),
                    icon: const Icon(Icons.person_add_outlined, size: 16),
                    label: const Text('Asignar', style: TextStyle(fontSize: 12)),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            if (responsables.isEmpty)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: cardBg,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: borderColor),
                ),
                child: const Center(
                  child: Text('No hay personal asignado a esta obra.', style: TextStyle(fontSize: 12.5, color: Color(0xFF94A3B8))),
                ),
              )
            else
              ...responsables.map((r) {
                final idUsuario = int.tryParse(r['id_usuario']?.toString() ?? '0') ?? 0;
                final nombre = r['nombre_completo']?.toString() ?? r['username']?.toString() ?? 'Usuario';
                final fechaAsig = r['fecha_asignacion']?.toString() ?? '';

                return Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    color: cardBg,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: borderColor),
                  ),
                  child: Row(
                    children: [
                      CircleAvatar(
                        radius: 16,
                        backgroundColor: AppTheme.primary.withValues(alpha: 0.15),
                        child: Text(
                          nombre.isNotEmpty ? nombre[0].toUpperCase() : 'U',
                          style: const TextStyle(color: AppTheme.primary, fontWeight: FontWeight.w800, fontSize: 13),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(nombre, style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w700, color: titleColor)),
                            if (fechaAsig.isNotEmpty)
                              Text('Asignado: $fechaAsig', style: const TextStyle(fontSize: 11, color: Color(0xFF94A3B8))),
                          ],
                        ),
                      ),
                      if (_puedeModificarObra())
                        IconButton(
                          icon: const Icon(Icons.remove_circle_outline_rounded, color: AppTheme.error, size: 18),
                          onPressed: () => _retirarResponsable(idUsuario, nombre),
                        ),
                    ],
                  ),
                );
              }),
          ],
        );
      },
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // TAB 1: ESTRUCTURA WBS
  // ──────────────────────────────────────────────────────────────────────────
  Widget _buildTabEstructura(bool isDark) {
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

    return RefreshIndicator(
      color: AppTheme.primary,
      onRefresh: () async {
        setState(() {
          _futureEstructura = _obraService.obtenerEstructura(widget.idObra);
        });
        await _futureEstructura;
      },
      child: FutureBuilder<List<Map<String, dynamic>>>(
        future: _futureEstructura,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator(color: AppTheme.primary, strokeWidth: 2.5));
          }

          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Text(
                  snapshot.error.toString().replaceAll('Exception: ', ''),
                  textAlign: TextAlign.center,
                  style: GoogleFonts.inter(fontSize: 13, color: const Color(0xFF94A3B8)),
                ),
              ),
            );
          }

          final arbolCompleto = snapshot.data ?? [];

          final totalNiveles = _contarNodos(arbolCompleto, 'NIVEL');
          final totalSectores = _contarNodos(arbolCompleto, 'SECTOR');
          final totalTorres = _contarNodos(arbolCompleto, 'TORRE') + _contarNodos(arbolCompleto, 'BLOQUE');

          final arbolFiltrado = _filtroTexto.isEmpty
              ? arbolCompleto
              : arbolCompleto.where((n) => _nodoCoincide(n, _filtroTexto)).toList();

          return ListView(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: cardBg,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: borderColor),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _buildWbsMetricBadge('$totalTorres', 'Torres/Bloques', isDark ? const Color(0xFFFB923C) : AppTheme.primary, titleColor),
                    Container(height: 20, width: 1, color: borderColor),
                    _buildWbsMetricBadge('$totalNiveles', 'Niveles', isDark ? const Color(0xFF38BDF8) : AppTheme.info, titleColor),
                    Container(height: 20, width: 1, color: borderColor),
                    _buildWbsMetricBadge('$totalSectores', 'Sectores', isDark ? const Color(0xFF34D399) : AppTheme.success, titleColor),
                  ],
                ),
              ),
              const SizedBox(height: 10),

              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _searchCtrl,
                      onChanged: (v) => setState(() => _filtroTexto = v.trim().toLowerCase()),
                      style: GoogleFonts.inter(fontSize: 13),
                      decoration: const InputDecoration(
                        hintText: 'Filtrar elemento en el árbol...',
                        prefixIcon: Icon(Icons.search_rounded, size: 18, color: Color(0xFF94A3B8)),
                        contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      ),
                    ),
                  ),
                  if (_puedeModificarObra()) ...[
                    const SizedBox(width: 8),
                    IconButton.filled(
                      tooltip: 'Nuevo Elemento Principal',
                      icon: const Icon(Icons.add_rounded, size: 20),
                      style: IconButton.styleFrom(backgroundColor: AppTheme.primary),
                      onPressed: () => _mostrarModalElementoEstructura(),
                    ),
                  ],
                ],
              ),
              const SizedBox(height: 12),

              if (arbolFiltrado.isEmpty)
                Container(
                  margin: const EdgeInsets.symmetric(vertical: 24),
                  padding: const EdgeInsets.all(28),
                  decoration: BoxDecoration(
                    color: cardBg,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: borderColor),
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 76,
                        height: 76,
                        decoration: BoxDecoration(
                          color: AppTheme.primary.withValues(alpha: isDark ? 0.16 : 0.08),
                          shape: BoxShape.circle,
                        ),
                        child: const Center(
                          child: Icon(
                            Icons.view_in_ar_rounded,
                            size: 40,
                            color: AppTheme.primary,
                          ),
                        ),
                      ),
                      const SizedBox(height: 18),
                      Text(
                        'Estructura no definida',
                        style: GoogleFonts.inter(
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                          color: titleColor,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Comienza creando la primera torre, bloque o nivel de la obra para organizar unidades y avances.',
                        textAlign: TextAlign.center,
                        style: GoogleFonts.inter(
                          fontSize: 12.5,
                          color: const Color(0xFF94A3B8),
                          height: 1.4,
                        ),
                      ),
                      if (_puedeModificarObra()) ...[
                        const SizedBox(height: 20),
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppTheme.primary,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                            ),
                            icon: const Icon(Icons.add_rounded, size: 18),
                            label: Text(
                              'Crear Elemento',
                              style: GoogleFonts.inter(fontWeight: FontWeight.w700, fontSize: 13),
                            ),
                            onPressed: () => _mostrarModalElementoEstructura(),
                          ),
                        ),
                      ],
                    ],
                  ),
                )
              else
                ...arbolFiltrado.map((nodo) => _buildNodoJerarquico(nodo, 0, isDark)),
            ],
          );
        },
      ),
    );
  }

  Widget _buildWbsMetricBadge(String valor, String label, Color color, Color titleColor) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(valor, style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w900, color: titleColor)),
        Text(label, style: GoogleFonts.inter(fontSize: 10.5, color: const Color(0xFF94A3B8), fontWeight: FontWeight.w600)),
      ],
    );
  }

  Widget _buildNodoActions(Map<String, dynamic> nodo, bool isDark) {
    if (!_puedeModificarObra()) return const SizedBox.shrink();
    final nombre = (nodo['nombre'] ?? 'Elemento').toString();
    final idEstructura = int.tryParse(nodo['id_estructura']?.toString() ?? '');

    return PopupMenuButton<String>(
      icon: const Icon(Icons.more_vert_rounded, size: 18, color: Color(0xFF94A3B8)),
      padding: EdgeInsets.zero,
      tooltip: 'Opciones de Estructura',
      onSelected: (value) {
        if (value == 'sub') {
          _mostrarModalElementoEstructura(idPadre: idEstructura, nombrePadre: nombre);
        } else if (value == 'unidad') {
          _mostrarModalUnidad(preIdEstructura: idEstructura);
        } else if (value == 'edit') {
          _mostrarModalElementoEstructura(idEstructura: idEstructura, elementoExistente: nodo);
        } else if (value == 'delete') {
          _confirmarEliminarElemento(nodo);
        }
      },
      itemBuilder: (ctx) => [
        const PopupMenuItem(
          value: 'sub',
          child: Row(
            children: [
              Icon(Icons.subdirectory_arrow_right_rounded, size: 18, color: AppTheme.primary),
              SizedBox(width: 8),
              Text('Agregar Sub-elemento', style: TextStyle(fontSize: 12.5)),
            ],
          ),
        ),
        const PopupMenuItem(
          value: 'unidad',
          child: Row(
            children: [
              Icon(Icons.add_home_work_outlined, size: 18, color: Color(0xFF10B981)),
              SizedBox(width: 8),
              Text('Crear Unidad aquí', style: TextStyle(fontSize: 12.5)),
            ],
          ),
        ),
        const PopupMenuItem(
          value: 'edit',
          child: Row(
            children: [
              Icon(Icons.edit_outlined, size: 18, color: Color(0xFF64748B)),
              SizedBox(width: 8),
              Text('Editar Elemento', style: TextStyle(fontSize: 12.5)),
            ],
          ),
        ),
        const PopupMenuItem(
          value: 'delete',
          child: Row(
            children: [
              Icon(Icons.delete_outline_rounded, size: 18, color: AppTheme.error),
              SizedBox(width: 8),
              Text('Eliminar', style: TextStyle(fontSize: 12.5, color: AppTheme.error)),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildNodoJerarquico(Map<String, dynamic> nodo, int profundidad, bool isDark) {
    final nombre = (nodo['nombre'] ?? 'Elemento').toString();
    final tipo = (nodo['tipo'] ?? 'SECTOR').toString();
    final rawHijos = nodo['hijos'];
    final List<Map<String, dynamic>> hijos = (rawHijos is List)
        ? rawHijos.map((h) => Map<String, dynamic>.from(h as Map)).toList()
        : [];

    final colorTipo = _colorTipoElemento(tipo, isDark);
    final iconTipo = _iconoTipoElemento(tipo);

    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

    final leftMargin = profundidad * 12.0;

    if (hijos.isEmpty) {
      return Container(
        margin: EdgeInsets.only(left: leftMargin, bottom: 6),
        decoration: BoxDecoration(
          color: cardBg,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: borderColor),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Row(
            children: [
              Icon(iconTipo, size: 16, color: colorTipo),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  nombre,
                  style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w700, color: titleColor),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: colorTipo.withValues(alpha: isDark ? 0.15 : 0.08),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  tipo.toUpperCase(),
                  style: GoogleFonts.inter(fontSize: 9, fontWeight: FontWeight.w800, color: colorTipo),
                ),
              ),
              _buildNodoActions(nodo, isDark),
            ],
          ),
        ),
      );
    }

    return Container(
      margin: EdgeInsets.only(left: leftMargin, bottom: 6),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: profundidad == 0 ? (isDark ? const Color(0xFF334155) : const Color(0xFFCBD5E1)) : borderColor),
      ),
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          initiallyExpanded: profundidad < 2,
          tilePadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 0),
          childrenPadding: const EdgeInsets.only(bottom: 6, right: 6),
          leading: Icon(iconTipo, size: 18, color: colorTipo),
          title: Text(
            nombre,
            style: GoogleFonts.inter(fontSize: 13.5, fontWeight: FontWeight.w800, color: titleColor),
          ),
          subtitle: Text(
            '${hijos.length} sub-elemento${hijos.length == 1 ? '' : 's'}',
            style: GoogleFonts.inter(fontSize: 11, color: const Color(0xFF94A3B8), fontWeight: FontWeight.w500),
          ),
          trailing: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: colorTipo.withValues(alpha: isDark ? 0.15 : 0.08),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  tipo.toUpperCase(),
                  style: GoogleFonts.inter(fontSize: 9, fontWeight: FontWeight.w800, color: colorTipo),
                ),
              ),
              _buildNodoActions(nodo, isDark),
            ],
          ),
          children: hijos.map((hijo) => _buildNodoJerarquico(hijo, profundidad + 1, isDark)).toList(),
        ),
      ),
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // TAB 2: UNIDADES DE CONSTRUCCIÓN
  // ──────────────────────────────────────────────────────────────────────────
  Widget _buildTabUnidades(bool isDark) {
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
    final subColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);

    return Scaffold(
      backgroundColor: Colors.transparent,
      floatingActionButton: _puedeModificarObra()
          ? FloatingActionButton.extended(
              backgroundColor: AppTheme.primary,
              icon: const Icon(Icons.add_home_work_rounded, color: Colors.white, size: 20),
              label: Text('Nueva Unidad', style: GoogleFonts.inter(fontWeight: FontWeight.w700, color: Colors.white)),
              onPressed: () => _mostrarModalUnidad(),
            )
          : null,
      body: RefreshIndicator(
        color: AppTheme.primary,
        onRefresh: () async {
          setState(() {
            _futureUnidades = _unidadService.listarUnidades(widget.idObra);
          });
          await _futureUnidades;
        },
        child: FutureBuilder<List<Map<String, dynamic>>>(
          future: _futureUnidades,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator(color: AppTheme.primary, strokeWidth: 2.5));
            }

            if (snapshot.hasError) {
              return Center(
                child: Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Text(
                    snapshot.error.toString().replaceAll('Exception: ', ''),
                    textAlign: TextAlign.center,
                    style: GoogleFonts.inter(fontSize: 13, color: subColor),
                  ),
                ),
              );
            }

            final todas = snapshot.data ?? [];

            final filtradas = todas.where((u) {
              final est = (u['estado'] ?? '').toString().toUpperCase();
              return _filtroEstadoUnidad == 'TODOS' || est == _filtroEstadoUnidad;
            }).toList();

            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 80),
              children: [
                // Filtro de estados
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      _buildChipFiltroUnidad('TODOS', 'Todos (${todas.length})', isDark),
                      const SizedBox(width: 8),
                      _buildChipFiltroUnidad('PLANIFICADO', 'Planificados', isDark),
                      const SizedBox(width: 8),
                      _buildChipFiltroUnidad('EN_CONSTRUCCION', 'En Construcción', isDark),
                      const SizedBox(width: 8),
                      _buildChipFiltroUnidad('FINALIZADO', 'Concluidos', isDark),
                    ],
                  ),
                ),
                const SizedBox(height: 14),

                if (filtradas.isEmpty)
                  Center(
                    child: Padding(
                      padding: const EdgeInsets.all(32.0),
                      child: Column(
                        children: [
                          const Icon(Icons.meeting_room_outlined, size: 40, color: Color(0xFF94A3B8)),
                          const SizedBox(height: 10),
                          Text('No hay unidades registradas',
                              style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w700, color: titleColor)),
                          const SizedBox(height: 4),
                          const Text('Utilice el botón "Nueva Unidad" para agregar la primera.',
                              textAlign: TextAlign.center, style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8))),
                        ],
                      ),
                    ),
                  )
                else
                  ...filtradas.map((u) {
                    final cod = u['codigo']?.toString() ?? u['nombre']?.toString() ?? 'U-00';
                    final nombre = u['nombre']?.toString() ?? '';
                    final tipo = (u['tipo_unidad'] ?? u['tipo'] ?? 'DEPARTAMENTO').toString();
                    final est = (u['estado'] ?? 'PLANIFICADO').toString();
                    final area = (u['superficie'] ?? u['area_m2'] ?? '0').toString();
                    final plantas = u['cantidad_plantas']?.toString() ?? '1';

                    return Container(
                      margin: const EdgeInsets.only(bottom: 10),
                      decoration: BoxDecoration(
                        color: cardBg,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: borderColor),
                      ),
                      child: InkWell(
                        borderRadius: BorderRadius.circular(12),
                        onTap: () => _mostrarModalDetalleUnidad(u),
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Row(
                                    children: [
                                      Container(
                                        padding: const EdgeInsets.all(8),
                                        decoration: BoxDecoration(
                                          color: isDark ? const Color(0xFF2E1C14) : const Color(0xFFFFF7ED),
                                          borderRadius: BorderRadius.circular(8),
                                        ),
                                        child: const Icon(Icons.door_sliding_rounded, color: AppTheme.primary, size: 20),
                                      ),
                                      const SizedBox(width: 10),
                                      Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Text(cod, style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w800, color: titleColor)),
                                          if (nombre.isNotEmpty && nombre != cod)
                                            Text(nombre, style: GoogleFonts.inter(fontSize: 12, color: subColor)),
                                        ],
                                      ),
                                    ],
                                  ),
                                  Row(
                                    children: [
                                      ConstructionStatusBadge(status: est, compact: true),
                                      if (_puedeModificarObra())
                                        PopupMenuButton<String>(
                                          icon: const Icon(Icons.more_vert_rounded, size: 18, color: Color(0xFF94A3B8)),
                                          padding: EdgeInsets.zero,
                                          onSelected: (action) {
                                            if (action == 'edit') {
                                              _mostrarModalUnidad(unidadExistente: u);
                                            } else if (action == 'estado') {
                                              _mostrarModalDetalleUnidad(u);
                                            } else if (action == 'delete') {
                                              _confirmarEliminarUnidad(u);
                                            }
                                          },
                                          itemBuilder: (ctx) => [
                                            const PopupMenuItem(
                                              value: 'estado',
                                              child: Row(
                                                children: [
                                                  Icon(Icons.published_with_changes_rounded, size: 16, color: AppTheme.primary),
                                                  SizedBox(width: 8),
                                                  Text('Cambiar Estado', style: TextStyle(fontSize: 12.5)),
                                                ],
                                              ),
                                            ),
                                            const PopupMenuItem(
                                              value: 'edit',
                                              child: Row(
                                                children: [
                                                  Icon(Icons.edit_outlined, size: 16, color: Color(0xFF64748B)),
                                                  SizedBox(width: 8),
                                                  Text('Editar Unidad', style: TextStyle(fontSize: 12.5)),
                                                ],
                                              ),
                                            ),
                                            const PopupMenuItem(
                                              value: 'delete',
                                              child: Row(
                                                children: [
                                                  Icon(Icons.delete_outline_rounded, size: 16, color: AppTheme.error),
                                                  SizedBox(width: 8),
                                                  Text('Eliminar', style: TextStyle(fontSize: 12.5, color: AppTheme.error)),
                                                ],
                                              ),
                                            ),
                                          ],
                                        ),
                                    ],
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Divider(height: 1, color: borderColor),
                              const SizedBox(height: 8),
                              Row(
                                children: [
                                  Text(tipo.replaceAll('_', ' '), style: GoogleFonts.inter(fontSize: 11.5, color: subColor, fontWeight: FontWeight.w600)),
                                  const SizedBox(width: 8),
                                  Text('·', style: TextStyle(color: subColor)),
                                  const SizedBox(width: 8),
                                  Text('$area m²', style: GoogleFonts.inter(fontSize: 11.5, color: subColor)),
                                  const SizedBox(width: 8),
                                  Text('·', style: TextStyle(color: subColor)),
                                  const SizedBox(width: 8),
                                  Text('$plantas ${plantas == '1' ? 'planta' : 'plantas'}', style: GoogleFonts.inter(fontSize: 11.5, color: subColor)),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  }),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildChipFiltroUnidad(String valor, String label, bool isDark) {
    final sel = _filtroEstadoUnidad == valor;
    return InkWell(
      onTap: () => setState(() => _filtroEstadoUnidad = valor),
      borderRadius: BorderRadius.circular(6),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: sel ? (isDark ? const Color(0xFFF97316) : const Color(0xFF0F172A)) : (isDark ? const Color(0xFF131D31) : Colors.white),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: sel ? Colors.transparent : (isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0))),
        ),
        child: Text(
          label,
          style: GoogleFonts.inter(
            fontSize: 11.5,
            fontWeight: sel ? FontWeight.w700 : FontWeight.w500,
            color: sel ? Colors.white : (isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B)),
          ),
        ),
      ),
    );
  }

  Widget _buildQuickTypeSelector(String valor, String label, bool sel, VoidCallback onTap, bool isDark) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
        decoration: BoxDecoration(
          color: sel ? (isDark ? const Color(0xFFF97316) : const Color(0xFF0F172A)) : (isDark ? const Color(0xFF131D31) : const Color(0xFFF1F5F9)),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: sel ? Colors.transparent : (isDark ? const Color(0xFF22304C) : const Color(0xFFCBD5E1)),
          ),
        ),
        child: Text(
          label,
          style: GoogleFonts.inter(
            fontSize: 12,
            fontWeight: sel ? FontWeight.w700 : FontWeight.w500,
            color: sel ? Colors.white : (isDark ? const Color(0xFF94A3B8) : const Color(0xFF475569)),
          ),
        ),
      ),
    );
  }
}

class _SegmentedTabHeaderDelegate extends SliverPersistentHeaderDelegate {
  final Widget child;
  _SegmentedTabHeaderDelegate({required this.child});

  @override
  Widget build(BuildContext context, double shrinkOffset, bool overlapsContent) {
    return child;
  }

  @override
  double get maxExtent => 62.0;

  @override
  double get minExtent => 62.0;

  @override
  bool shouldRebuild(covariant SliverPersistentHeaderDelegate oldDelegate) => false;
}
