import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../services/auth_provider.dart';
import '../services/obra_service.dart';
import '../theme/app_theme.dart';
import '../widgets/construction_widgets.dart';
import '../widgets/ev_widgets.dart';
import 'proyecto_detalle_screen.dart';

class ProyectosScreen extends StatefulWidget {
  const ProyectosScreen({super.key});

  @override
  State<ProyectosScreen> createState() => _ProyectosScreenState();
}

class _ProyectosScreenState extends State<ProyectosScreen> {
  final ObraService _obraService = ObraService();
  late Future<List<Map<String, dynamic>>> _futureProyectos;
  String _filtroEstado = 'TODOS';
  String _busqueda = '';
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _cargarProyectos();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _cargarProyectos() {
    _futureProyectos = _obraService.listarProyectos();
  }

  Future<void> _refrescar() async {
    setState(() {
      _cargarProyectos();
    });
    await _futureProyectos;
  }

  bool _puedeCrearObra() {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    return auth.hasPermission('Registrar_obras') ||
        auth.esAdminGlobal ||
        auth.esAdminEmpresa ||
        auth.esJefeObra;
  }

  void _mostrarModalNuevoProyecto() async {
    final nombreCtrl = TextEditingController();
    final codigoCtrl = TextEditingController();
    final ubicacionCtrl = TextEditingController();
    final presupuestoCtrl = TextEditingController();
    final descCtrl = TextEditingController();

    DateTime fechaInicio = DateTime.now();
    int? idTipoSeleccionado;
    List<Map<String, dynamic>> tiposDisponibles = [];
    bool guardando = false;

    try {
      tiposDisponibles = await _obraService.obtenerTiposProyecto();
      if (tiposDisponibles.isNotEmpty) {
        idTipoSeleccionado = int.tryParse(
          tiposDisponibles.first['id_tipo_obra']?.toString() ?? '',
        );
      }
    } catch (_) {}

    if (!mounted) return;

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
                      'Registrar Nueva Obra',
                      style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w800, color: titleColor),
                    ),
                    const SizedBox(height: 14),

                    Row(
                      children: [
                        Expanded(
                          flex: 3,
                          child: TextField(
                            controller: nombreCtrl,
                            decoration: const InputDecoration(
                              labelText: 'Nombre del Proyecto *',
                              hintText: 'Ej: Condominio Las Palmas',
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          flex: 2,
                          child: TextField(
                            controller: codigoCtrl,
                            decoration: const InputDecoration(
                              labelText: 'Código (Opcional)',
                              hintText: 'Auto',
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    if (tiposDisponibles.isNotEmpty)
                      DropdownButtonFormField<int>(
                        initialValue: idTipoSeleccionado,
                        decoration: const InputDecoration(labelText: 'Tipo de Obra *'),
                        items: tiposDisponibles.map((t) {
                          final id = int.tryParse(t['id_tipo_obra']?.toString() ?? '') ?? 0;
                          final nombre = t['nombre']?.toString() ?? 'Tipo';
                          return DropdownMenuItem(value: id, child: Text(nombre));
                        }).toList(),
                        onChanged: (v) => setModalState(() => idTipoSeleccionado = v),
                      ),
                    const SizedBox(height: 12),

                    TextField(
                      controller: ubicacionCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Ubicación / Dirección *',
                        hintText: 'Ej: Av. Banzer 4to Anillo',
                      ),
                    ),
                    const SizedBox(height: 12),

                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: presupuestoCtrl,
                            keyboardType: const TextInputType.numberWithOptions(decimal: true),
                            decoration: const InputDecoration(
                              labelText: 'Presupuesto Estimado (BOB)',
                              hintText: 'Ej: 1500000',
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: InkWell(
                            onTap: () async {
                              final picked = await showDatePicker(
                                context: context,
                                initialDate: fechaInicio,
                                firstDate: DateTime(2020),
                                lastDate: DateTime(2035),
                              );
                              if (picked != null) {
                                setModalState(() => fechaInicio = picked);
                              }
                            },
                            child: InputDecorator(
                              decoration: const InputDecoration(labelText: 'Fecha de Inicio'),
                              child: Text(
                                '${fechaInicio.year}-${fechaInicio.month.toString().padLeft(2, '0')}-${fechaInicio.day.toString().padLeft(2, '0')}',
                                style: const TextStyle(fontSize: 13),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    TextField(
                      controller: descCtrl,
                      maxLines: 2,
                      decoration: const InputDecoration(
                        labelText: 'Descripción del Proyecto',
                        hintText: 'Objetivo y alcance de la obra',
                      ),
                    ),
                    const SizedBox(height: 18),

                    ObratecPrimaryButton(
                      label: 'Registrar Proyecto',
                      loading: guardando,
                      onPressed: () async {
                        final nombre = nombreCtrl.text.trim();
                        final ubicacion = ubicacionCtrl.text.trim();
                        if (nombre.isEmpty || ubicacion.isEmpty) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Nombre y ubicación son obligatorios.')),
                          );
                          return;
                        }

                        setModalState(() => guardando = true);
                        try {
                          final payload = <String, dynamic>{
                            'nombre': nombre,
                            'ubicacion': ubicacion,
                            'descripcion': descCtrl.text.trim(),
                            'presupuesto_estimado': double.tryParse(presupuestoCtrl.text.trim()) ?? 0,
                            'fecha_inicio': '${fechaInicio.year}-${fechaInicio.month.toString().padLeft(2, '0')}-${fechaInicio.day.toString().padLeft(2, '0')}',
                          };
                          if (codigoCtrl.text.trim().isNotEmpty) {
                            payload['codigo'] = codigoCtrl.text.trim();
                          }
                          if (idTipoSeleccionado != null) {
                            payload['id_tipo_obra'] = idTipoSeleccionado;
                          }

                          await _obraService.crearProyecto(payload);

                          if (!ctx.mounted) return;
                          Navigator.pop(ctx);
                          _refrescar();

                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                              content: Text('Proyecto registrado exitosamente.'),
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

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final topBarBg = isDark ? const Color(0xFF0F172A) : Colors.white;
    final dividerColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);

    return Scaffold(
      appBar: AppBar(
        title: Text(
          'Catálogo de Proyectos',
          style: GoogleFonts.inter(fontWeight: FontWeight.w800, fontSize: 16.5),
        ),
        actions: [
          IconButton(
            tooltip: 'Recargar lista',
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _refrescar,
          ),
          const SizedBox(width: 4),
        ],
      ),
      floatingActionButton: _puedeCrearObra()
          ? FloatingActionButton.extended(
              backgroundColor: AppTheme.primary,
              icon: const Icon(Icons.add_business_rounded, color: Colors.white, size: 20),
              label: Text('Nuevo Proyecto', style: GoogleFonts.inter(fontWeight: FontWeight.w700, color: Colors.white)),
              onPressed: _mostrarModalNuevoProyecto,
            )
          : null,
      body: SafeArea(
        child: Column(
          children: [
            // Barra de Búsqueda y Filtros
            Container(
              color: topBarBg,
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 14),
              child: Column(
                children: [
                  TextField(
                    controller: _searchController,
                    onChanged: (val) => setState(() => _busqueda = val.trim().toLowerCase()),
                    style: GoogleFonts.inter(fontSize: 13),
                    decoration: InputDecoration(
                      hintText: 'Buscar por código, nombre o ubicación...',
                      prefixIcon: const Icon(Icons.search_rounded, size: 20, color: Color(0xFF94A3B8)),
                      suffixIcon: _busqueda.isNotEmpty
                          ? IconButton(
                              icon: const Icon(Icons.clear, size: 18),
                              onPressed: () {
                                _searchController.clear();
                                setState(() => _busqueda = '');
                              },
                            )
                          : null,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                    ),
                  ),
                  const SizedBox(height: 10),
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: [
                        _buildFilterChip('TODOS', 'Todos', isDark),
                        const SizedBox(width: 8),
                        _buildFilterChip('ACTIVO', 'En Ejecución', isDark),
                        const SizedBox(width: 8),
                        _buildFilterChip('PLANIFICACION', 'Planificación', isDark),
                        const SizedBox(width: 8),
                        _buildFilterChip('PAUSADO', 'Pausados', isDark),
                        const SizedBox(width: 8),
                        _buildFilterChip('FINALIZADO', 'Concluidos', isDark),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            Divider(height: 1, color: dividerColor),

            // Listado de Proyectos
            Expanded(
              child: RefreshIndicator(
                color: AppTheme.primary,
                onRefresh: _refrescar,
                child: FutureBuilder<List<Map<String, dynamic>>>(
                  future: _futureProyectos,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return const Center(child: CircularProgressIndicator(color: AppTheme.primary, strokeWidth: 2.5));
                    }

                    if (snapshot.hasError) {
                      return Center(
                        child: Padding(
                          padding: const EdgeInsets.all(24.0),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Icon(Icons.cloud_off_rounded, size: 44, color: AppTheme.error),
                              const SizedBox(height: 12),
                              Text(
                                snapshot.error.toString().replaceAll('Exception: ', ''),
                                textAlign: TextAlign.center,
                                style: GoogleFonts.inter(fontSize: 13, color: const Color(0xFF94A3B8)),
                              ),
                              const SizedBox(height: 16),
                              ElevatedButton.icon(
                                onPressed: _refrescar,
                                icon: const Icon(Icons.refresh, size: 18),
                                label: const Text('Reintentar'),
                              ),
                            ],
                          ),
                        ),
                      );
                    }

                    final listaTotal = snapshot.data ?? [];

                    final listaFiltrada = listaTotal.where((p) {
                      final estado = (p['estado_obra'] ?? '').toString().toUpperCase();
                      final nombre = (p['nombre'] ?? '').toString().toLowerCase();
                      final codigo = (p['codigo'] ?? '').toString().toLowerCase();
                      final ubicacion = (p['ubicacion'] ?? '').toString().toLowerCase();

                      final cumpleEstado = (_filtroEstado == 'TODOS') || (estado == _filtroEstado);
                      final cumpleBusqueda = _busqueda.isEmpty ||
                          nombre.contains(_busqueda) ||
                          codigo.contains(_busqueda) ||
                          ubicacion.contains(_busqueda);

                      return cumpleEstado && cumpleBusqueda;
                    }).toList();

                    if (listaFiltrada.isEmpty) {
                      return ListView(
                        padding: const EdgeInsets.all(24),
                        children: [
                          const SizedBox(height: 40),
                          Center(
                            child: Container(
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: isDark ? const Color(0xFF2E1C14) : const Color(0xFFFFF7ED),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(Icons.search_off_rounded, size: 40, color: AppTheme.primary),
                            ),
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'No se encontraron obras',
                            textAlign: TextAlign.center,
                            style: GoogleFonts.inter(fontSize: 15.5, fontWeight: FontWeight.w800),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            _busqueda.isNotEmpty
                                ? 'No hay resultados para "$_busqueda" con los filtros actuales.'
                                : 'No hay obras registradas en este estado.',
                            textAlign: TextAlign.center,
                            style: GoogleFonts.inter(fontSize: 12.5, color: const Color(0xFF94A3B8)),
                          ),
                          if (_busqueda.isNotEmpty || _filtroEstado != 'TODOS') ...[
                            const SizedBox(height: 16),
                            Center(
                              child: OutlinedButton(
                                onPressed: () {
                                  _searchController.clear();
                                  setState(() {
                                    _busqueda = '';
                                    _filtroEstado = 'TODOS';
                                  });
                                },
                                child: const Text('Limpiar Filtros'),
                              ),
                            ),
                          ],
                        ],
                      );
                    }

                    return ListView.builder(
                      padding: const EdgeInsets.fromLTRB(16, 16, 16, 80),
                      itemCount: listaFiltrada.length,
                      itemBuilder: (context, index) {
                        final p = listaFiltrada[index];
                        final idObra = int.tryParse(p['id_obra']?.toString() ?? '0') ?? 0;
                        final codigo = p['codigo']?.toString() ?? 'P-0000';
                        final nombre = p['nombre']?.toString() ?? 'Proyecto';
                        final tipoNombre = p['tipo_obra_nombre']?.toString() ?? 'Edificación';
                        final estado = (p['estado_obra']?.toString() ?? 'PLANIFICACION').toUpperCase();
                        final ubicacion = p['ubicacion']?.toString() ?? '';
                        final fechaInicio = p['fecha_inicio']?.toString() ?? '';

                        return CleanProjectCard(
                          idObra: idObra,
                          codigo: codigo,
                          nombre: nombre,
                          tipoNombre: tipoNombre,
                          estado: estado,
                          ubicacion: ubicacion,
                          fechaInicio: fechaInicio,
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => ProyectoDetalleScreen(
                                  idObra: idObra,
                                  codigo: codigo,
                                  nombre: nombre,
                                  tipoNombre: tipoNombre,
                                  estado: estado,
                                  ubicacion: ubicacion,
                                  fechaInicio: fechaInicio,
                                ),
                              ),
                            ).then((_) => _refrescar());
                          },
                        );
                      },
                    );
                  },
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFilterChip(String valor, String etiqueta, bool isDark) {
    final seleccionado = _filtroEstado == valor;

    final selectedBg = isDark ? const Color(0xFFF97316) : const Color(0xFF0F172A);
    final unselectedBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final unselectedBorder = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final unselectedTextColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);

    return InkWell(
      onTap: () => setState(() => _filtroEstado = valor),
      borderRadius: BorderRadius.circular(6),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: seleccionado ? selectedBg : unselectedBg,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: seleccionado ? selectedBg : unselectedBorder),
        ),
        child: Text(
          etiqueta,
          style: GoogleFonts.inter(
            fontSize: 12,
            fontWeight: seleccionado ? FontWeight.w700 : FontWeight.w500,
            color: seleccionado ? Colors.white : unselectedTextColor,
          ),
        ),
      ),
    );
  }
}
