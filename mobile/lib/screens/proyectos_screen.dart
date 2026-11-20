import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../services/auth_provider.dart';
import '../services/obra_service.dart';
import '../theme/app_theme.dart';
import 'proyecto_detalle_screen.dart';

class ProyectosScreen extends StatefulWidget {
  final bool showBackButton;

  const ProyectosScreen({
    super.key,
    this.showBackButton = false,
  });

  @override
  State<ProyectosScreen> createState() => _ProyectosScreenState();
}

class _ProyectosScreenState extends State<ProyectosScreen> {
  final ObraService _obraService = ObraService();
  late Future<List<Map<String, dynamic>>> _futureProyectos;
  List<Map<String, dynamic>> _tiposProyectoCache = [];
  String _filtroEstado = 'TODOS';
  String _busqueda = '';
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _cargarProyectos();
    _precargarTipos();
  }

  void _precargarTipos() async {
    try {
      final tipos = await _obraService.obtenerTiposProyecto();
      if (mounted) {
        setState(() => _tiposProyectoCache = tipos);
      }
    } catch (_) {}
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

  void _mostrarModalNuevoProyecto() {
    final nombreCtrl = TextEditingController();
    final codigoCtrl = TextEditingController();
    final ubicacionCtrl = TextEditingController();
    final presupuestoCtrl = TextEditingController();
    final descCtrl = TextEditingController();

    DateTime fechaInicio = DateTime.now();
    List<Map<String, dynamic>> tiposDisponibles = List.from(_tiposProyectoCache);
    int? idTipoSeleccionado = tiposDisponibles.isNotEmpty
        ? int.tryParse(tiposDisponibles.first['id_tipo_obra']?.toString() ?? '')
        : null;
    bool guardando = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            if (tiposDisponibles.isEmpty) {
              _obraService.obtenerTiposProyecto().then((tipos) {
                if (ctx.mounted && tipos.isNotEmpty) {
                  setModalState(() {
                    tiposDisponibles = tipos;
                    _tiposProyectoCache = tipos;
                    idTipoSeleccionado ??= int.tryParse(tipos.first['id_tipo_obra']?.toString() ?? '');
                  });
                }
              }).catchError((_) {});
            }
            final isDark = Theme.of(context).brightness == Brightness.dark;
            final sheetBg = isDark ? const Color(0xFF131D31) : Colors.white;
            final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
            final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);

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
                border: Border.all(color: borderColor),
              ),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Center(
                      child: Container(
                        width: 40,
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
                        Text(
                          'Nuevo Proyecto',
                          style: GoogleFonts.inter(
                            fontSize: 18,
                            fontWeight: FontWeight.w800,
                            color: titleColor,
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.close_rounded, size: 20),
                          onPressed: () => Navigator.pop(ctx),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: nombreCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Nombre del Proyecto *',
                        hintText: 'Ej: Edificio Sky Equipetrol',
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: codigoCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Código / Sigla',
                        hintText: 'Ej: SCZ-EQ-001 (o dejar en blanco para automático)',
                      ),
                    ),
                    const SizedBox(height: 12),
                    if (tiposDisponibles.isNotEmpty)
                      DropdownButtonFormField<int>(
                        initialValue: idTipoSeleccionado,
                        decoration: const InputDecoration(labelText: 'Tipo de Proyecto *'),
                        items: tiposDisponibles.map((t) {
                          return DropdownMenuItem<int>(
                            value: int.tryParse(t['id_tipo_obra']?.toString() ?? ''),
                            child: Text(t['nombre_obra']?.toString() ?? 'Obra'),
                          );
                        }).toList(),
                        onChanged: (val) => setModalState(() => idTipoSeleccionado = val),
                      ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: ubicacionCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Ubicación / Dirección',
                        hintText: 'Ej: Av. San Martín #450',
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: presupuestoCtrl,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: 'Cotización / Presupuesto Inicial (BOB)',
                        hintText: 'Ej: 1500000',
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: descCtrl,
                      maxLines: 2,
                      decoration: const InputDecoration(
                        labelText: 'Descripción',
                        hintText: 'Detalles u observaciones preliminares...',
                      ),
                    ),
                    const SizedBox(height: 20),
                    SizedBox(
                      width: double.infinity,
                      height: 48,
                      child: ElevatedButton(
                        onPressed: guardando
                            ? null
                            : () async {
                                final nombre = nombreCtrl.text.trim();
                                if (nombre.isEmpty) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text('El nombre es obligatorio.')),
                                  );
                                  return;
                                }
                                setModalState(() => guardando = true);
                                try {
                                  final auth = Provider.of<AuthProvider>(context, listen: false);
                                  await _obraService.crearProyecto({
                                    'nombre': nombre,
                                    'codigo': codigoCtrl.text.trim(),
                                    'id_tipo_obra': idTipoSeleccionado ?? 1,
                                    'id_empresa': auth.idEmpresaActiva,
                                    'ubicacion': ubicacionCtrl.text.trim(),
                                    'cotizacion_inicial': double.tryParse(presupuestoCtrl.text) ?? 0,
                                    'descripcion': descCtrl.text.trim(),
                                    'fecha_inicio': fechaInicio.toIso8601String().substring(0, 10),
                                  });
                                  if (!context.mounted) return;
                                  Navigator.pop(ctx);
                                  _refrescar();
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text('Proyecto registrado con éxito.'),
                                      backgroundColor: AppTheme.success,
                                    ),
                                  );
                                } catch (e) {
                                  setModalState(() => guardando = false);
                                  if (!context.mounted) return;
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(
                                      content: Text(e.toString().replaceAll('Exception: ', '')),
                                      backgroundColor: AppTheme.error,
                                    ),
                                  );
                                }
                              },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primary,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        child: guardando
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                              )
                            : Text('Crear Proyecto', style: GoogleFonts.inter(fontWeight: FontWeight.w800)),
                      ),
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
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC),
      appBar: AppBar(
        titleSpacing: widget.showBackButton ? 0 : 16,
        leading: widget.showBackButton
            ? IconButton(
                icon: const Icon(Icons.arrow_back_rounded),
                onPressed: () => Navigator.pop(context),
              )
            : null,
        title: Text(
          'Proyectos',
          style: GoogleFonts.inter(
            fontSize: 18,
            fontWeight: FontWeight.w800,
            color: titleColor,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded, size: 22),
            tooltip: 'Actualizar lista',
            onPressed: _refrescar,
          ),
          const SizedBox(width: 6),
        ],
      ),
      floatingActionButton: _puedeCrearObra()
          ? FloatingActionButton.extended(
              backgroundColor: AppTheme.primary,
              foregroundColor: Colors.white,
              elevation: 3,
              icon: const Icon(Icons.add_rounded, size: 20),
              label: Text(
                'Nuevo',
                style: GoogleFonts.inter(fontWeight: FontWeight.w800, fontSize: 13.5),
              ),
              onPressed: _mostrarModalNuevoProyecto,
            )
          : null,
      body: SafeArea(
        child: Column(
          children: [
            // Filtros horizontales y Barra de búsqueda (Prototipo Screens 3 y 9)
            Container(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 12),
              child: Column(
                children: [
                  // Chips de Estado
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: [
                        _buildFilterChip('TODOS', 'Todos', isDark),
                        const SizedBox(width: 8),
                        _buildFilterChip('PLANIFICACION', 'Planificación', isDark),
                        const SizedBox(width: 8),
                        _buildFilterChip('EJECUCION', 'Ejecución', isDark),
                        const SizedBox(width: 8),
                        _buildFilterChip('CONCLUIDO', 'Concluido', isDark),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),

                  // Buscador
                  TextField(
                    controller: _searchController,
                    onChanged: (val) => setState(() => _busqueda = val.trim().toLowerCase()),
                    style: GoogleFonts.inter(fontSize: 13.5),
                    decoration: InputDecoration(
                      hintText: 'Buscar proyecto...',
                      hintStyle: GoogleFonts.inter(fontSize: 13, color: const Color(0xFF94A3B8)),
                      prefixIcon: const Icon(Icons.search_rounded, size: 20, color: Color(0xFF94A3B8)),
                      suffixIcon: _busqueda.isNotEmpty
                          ? IconButton(
                              icon: const Icon(Icons.clear_rounded, size: 18),
                              onPressed: () {
                                _searchController.clear();
                                setState(() => _busqueda = '');
                              },
                            )
                          : const Icon(Icons.tune_rounded, size: 18, color: Color(0xFF94A3B8)),
                      filled: true,
                      fillColor: cardBg,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: BorderSide(color: borderColor),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: BorderSide(color: borderColor),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: const BorderSide(color: AppTheme.primary, width: 1.5),
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // Listado de Proyectos
            Expanded(
              child: RefreshIndicator(
                color: AppTheme.primary,
                onRefresh: _refrescar,
                child: FutureBuilder<List<Map<String, dynamic>>>(
                  future: _futureProyectos,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return const Center(
                        child: CircularProgressIndicator(color: AppTheme.primary, strokeWidth: 2.5),
                      );
                    }

                    if (snapshot.hasError) {
                      return Center(
                        child: Padding(
                          padding: const EdgeInsets.all(24.0),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Icon(Icons.cloud_off_rounded, size: 40, color: AppTheme.error),
                              const SizedBox(height: 12),
                              Text(
                                snapshot.error.toString().replaceAll('Exception: ', ''),
                                textAlign: TextAlign.center,
                                style: GoogleFonts.inter(fontSize: 13, color: const Color(0xFF94A3B8)),
                              ),
                              const SizedBox(height: 16),
                              ElevatedButton(
                                onPressed: _refrescar,
                                style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primary),
                                child: const Text('Reintentar'),
                              ),
                            ],
                          ),
                        ),
                      );
                    }

                    final listaTotal = snapshot.data ?? [];
                    final auth = Provider.of<AuthProvider>(context, listen: false);

                    // Filtrado multiempresa si aplica
                    List<Map<String, dynamic>> listaFiltradaEmpresa = listaTotal;
                    if (auth.esAdminGlobal && !auth.esVistaGlobal && auth.idEmpresaActiva != null) {
                      listaFiltradaEmpresa = listaTotal.where((p) {
                        return p['id_empresa'] == auth.idEmpresaActiva;
                      }).toList();
                    }

                    final listaFiltrada = listaFiltradaEmpresa.where((p) {
                      final rawEstado = (p['estado_obra'] ?? p['estado'] ?? '').toString().toUpperCase();
                      final nombre = (p['nombre'] ?? '').toString().toLowerCase();
                      final codigo = (p['codigo'] ?? '').toString().toLowerCase();

                      bool cumpleEstado = true;
                      if (_filtroEstado == 'PLANIFICACION') {
                        cumpleEstado = rawEstado.contains('PLANIF');
                      } else if (_filtroEstado == 'EJECUCION') {
                        cumpleEstado = rawEstado.contains('EJEC') || rawEstado.contains('PROCESO') || rawEstado == 'ACTIVO';
                      } else if (_filtroEstado == 'CONCLUIDO') {
                        cumpleEstado = rawEstado.contains('CONCLU') || rawEstado.contains('FINALIZ');
                      }

                      final cumpleBusqueda = _busqueda.isEmpty ||
                          nombre.contains(_busqueda) ||
                          codigo.contains(_busqueda);

                      return cumpleEstado && cumpleBusqueda;
                    }).toList();

                    if (listaFiltrada.isEmpty) {
                      return ListView(
                        padding: const EdgeInsets.all(32),
                        children: [
                          const SizedBox(height: 40),
                          Center(
                            child: Container(
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: isDark ? const Color(0xFF1E293B) : const Color(0xFFFFF7ED),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(Icons.search_off_rounded, size: 36, color: AppTheme.primary),
                            ),
                          ),
                          const SizedBox(height: 14),
                          Text(
                            'No se encontraron proyectos',
                            textAlign: TextAlign.center,
                            style: GoogleFonts.inter(
                              fontSize: 15,
                              fontWeight: FontWeight.w800,
                              color: titleColor,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            _busqueda.isNotEmpty
                                ? 'No hay resultados que coincidan con "$_busqueda".'
                                : 'No hay proyectos en el estado seleccionado.',
                            textAlign: TextAlign.center,
                            style: GoogleFonts.inter(fontSize: 12.5, color: const Color(0xFF94A3B8)),
                          ),
                        ],
                      );
                    }

                    return ListView.separated(
                      padding: const EdgeInsets.fromLTRB(16, 4, 16, 80),
                      itemCount: listaFiltrada.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 10),
                      itemBuilder: (context, index) {
                        final p = listaFiltrada[index];
                        final idObra = int.tryParse(p['id_obra']?.toString() ?? '0') ?? 0;
                        final codigo = p['codigo']?.toString() ?? 'P-0000';
                        final nombre = p['nombre']?.toString() ?? 'Proyecto';
                        final tipo = p['tipo_obra_nombre']?.toString() ?? 'Edificaciones';
                        final estado = (p['estado_obra'] ?? p['estado'] ?? 'PLANIFICACION').toString().toUpperCase();

                        return _buildProjectCard(
                          p: p,
                          idObra: idObra,
                          codigo: codigo,
                          nombre: nombre,
                          tipo: tipo,
                          estado: estado,
                          isDark: isDark,
                          cardBg: cardBg,
                          borderColor: borderColor,
                          titleColor: titleColor,
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

  Widget _buildFilterChip(String valor, String label, bool isDark) {
    final bool activo = _filtroEstado == valor;

    return GestureDetector(
      onTap: () => setState(() => _filtroEstado = valor),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
        decoration: BoxDecoration(
          color: activo
              ? AppTheme.primary
              : (isDark ? const Color(0xFF131D31) : Colors.white),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: activo
                ? AppTheme.primary
                : (isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0)),
          ),
        ),
        child: Text(
          label,
          style: GoogleFonts.inter(
            fontSize: 12.5,
            fontWeight: activo ? FontWeight.w800 : FontWeight.w600,
            color: activo
                ? Colors.white
                : (isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B)),
          ),
        ),
      ),
    );
  }

  Widget _buildProjectCard({
    required Map<String, dynamic> p,
    required int idObra,
    required String codigo,
    required String nombre,
    required String tipo,
    required String estado,
    required bool isDark,
    required Color cardBg,
    required Color borderColor,
    required Color titleColor,
  }) {
    Color pillColor = AppTheme.info;
    String estadoLegible = 'Planificación';

    if (estado.contains('EJEC') || estado.contains('ACTIVO') || estado.contains('PROCESO')) {
      pillColor = AppTheme.success;
      estadoLegible = 'En Ejecución';
    } else if (estado.contains('CONCLU') || estado.contains('FINALIZ')) {
      pillColor = const Color(0xFF818CF8);
      estadoLegible = 'Concluido';
    }

    return Container(
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: borderColor),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => ProyectoDetalleScreen(
                idObra: idObra,
                codigo: codigo,
                nombre: nombre,
                tipoNombre: tipo,
                estado: estado,
                ubicacion: p['ubicacion']?.toString() ?? '',
                fechaInicio: p['fecha_inicio']?.toString() ?? '',
              ),
            ),
          ).then((_) => _refrescar());
        },
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              // Miniatura del Proyecto
              Container(
                width: 52,
                height: 52,
                decoration: BoxDecoration(
                  color: isDark ? const Color(0xFF1E293B) : const Color(0xFFFFF7ED),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.apartment_rounded, color: AppTheme.primary, size: 26),
              ),
              const SizedBox(width: 12),

              // Información del Proyecto
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          codigo,
                          style: GoogleFonts.inter(
                            fontSize: 10.5,
                            fontWeight: FontWeight.w800,
                            color: const Color(0xFF94A3B8),
                          ),
                        ),
                        const SizedBox(width: 6),
                        Container(
                          width: 4,
                          height: 4,
                          decoration: const BoxDecoration(
                            color: Color(0xFF94A3B8),
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: pillColor.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            estadoLegible,
                            style: GoogleFonts.inter(
                              fontSize: 9.5,
                              fontWeight: FontWeight.w800,
                              color: pillColor,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 3),
                    Text(
                      nombre,
                      style: GoogleFonts.inter(
                        fontSize: 14,
                        fontWeight: FontWeight.w800,
                        color: titleColor,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      tipo,
                      style: GoogleFonts.inter(
                        fontSize: 11.5,
                        color: const Color(0xFF94A3B8),
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded, color: Color(0xFF94A3B8), size: 20),
            ],
          ),
        ),
      ),
    );
  }
}
