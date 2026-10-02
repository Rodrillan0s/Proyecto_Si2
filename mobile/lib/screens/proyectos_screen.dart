import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../services/obra_service.dart';
import '../theme/app_theme.dart';
import '../widgets/construction_widgets.dart';
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
                      padding: const EdgeInsets.all(16),
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
                            );
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
