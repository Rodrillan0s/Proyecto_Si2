import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:latlong2/latlong.dart';

import '../services/obra_service.dart';
import '../services/unidad_service.dart';
import '../theme/app_theme.dart';
import '../widgets/construction_widgets.dart';
import '../widgets/ev_widgets.dart';

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

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
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

  // ── MODAL DETALLE Y CAMBIO DE ESTADO DE UNIDAD (CU12) ──────────────────────
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

            final codigo = unidad['codigo']?.toString() ?? 'U-00';
            final tipo = unidad['tipo']?.toString() ?? 'DEPARTAMENTO';
            final area = unidad['area_m2']?.toString() ?? '0';
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

                    // Ficha de la unidad
                    Row(
                      children: [
                        Expanded(child: _buildInfoItem('Área Construida', '$area m²', subColor, titleColor)),
                        Expanded(child: _buildInfoItem('Precio', '$precio BOB', subColor, titleColor)),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // Cambiar Estado (CU12)
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
                        hintText: 'Ej: Inicio de tabiquería e instalaciones',
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

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final tabBg = isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC);
    final tabBoxBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final tabBorder = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final indicatorBg = isDark ? const Color(0xFFF97316) : const Color(0xFF0F172A);

    return Scaffold(
      body: SafeArea(
        child: NestedScrollView(
          headerSliverBuilder: (context, innerBoxIsScrolled) {
            return [
              // 1. HERO HEADER SÓLIDO
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
                              ConstructionStatusBadge(status: widget.estado, compact: true),
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

              // 2. SEGMENTED TAB SWITCHER (3 TABS)
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
                        dividerColor: Colors.transparent,
                        tabs: const [
                          Tab(
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.account_tree_outlined, size: 14),
                                SizedBox(width: 4),
                                Text('Estructura'),
                              ],
                            ),
                          ),
                          Tab(
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.meeting_room_outlined, size: 14),
                                SizedBox(width: 4),
                                Text('Unidades (CU12)'),
                              ],
                            ),
                          ),
                          Tab(
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.map_outlined, size: 14),
                                SizedBox(width: 4),
                                Text('Mapa & Ficha'),
                              ],
                            ),
                          ),
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
              _buildTabEstructura(isDark),
              _buildTabUnidades(isDark),
              _buildTabMapaYFicha(isDark),
            ],
          ),
        ),
      ),
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

          if (arbolCompleto.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.account_tree_outlined, size: 40, color: AppTheme.primary),
                    const SizedBox(height: 12),
                    Text(
                      'Sin estructura registrada',
                      style: GoogleFonts.inter(fontSize: 15, fontWeight: FontWeight.w800, color: titleColor),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Esta obra aún no tiene torres, bloques o niveles en el árbol WBS.',
                      textAlign: TextAlign.center,
                      style: GoogleFonts.inter(fontSize: 12, color: const Color(0xFF94A3B8)),
                    ),
                  ],
                ),
              ),
            );
          }

          final totalNiveles = _contarNodos(arbolCompleto, 'NIVEL');
          final totalSectores = _contarNodos(arbolCompleto, 'SECTOR');
          final totalAmbientes = _contarNodos(arbolCompleto, 'AMBIENTE');

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
                    _buildWbsMetricBadge('$totalNiveles', 'Niveles', isDark ? const Color(0xFF38BDF8) : AppTheme.info, titleColor),
                    Container(height: 20, width: 1, color: borderColor),
                    _buildWbsMetricBadge('$totalSectores', 'Sectores', isDark ? const Color(0xFF34D399) : AppTheme.success, titleColor),
                    Container(height: 20, width: 1, color: borderColor),
                    _buildWbsMetricBadge('$totalAmbientes', 'Ambientes', isDark ? const Color(0xFFA78BFA) : const Color(0xFF8B5CF6), titleColor),
                  ],
                ),
              ),
              const SizedBox(height: 10),

              TextField(
                controller: _searchCtrl,
                onChanged: (v) => setState(() => _filtroTexto = v.trim().toLowerCase()),
                style: GoogleFonts.inter(fontSize: 13),
                decoration: InputDecoration(
                  hintText: 'Filtrar elemento...',
                  prefixIcon: const Icon(Icons.search_rounded, size: 18, color: Color(0xFF94A3B8)),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                ),
              ),
              const SizedBox(height: 12),

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
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
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
            '${hijos.length} elemento${hijos.length == 1 ? '' : 's'}',
            style: GoogleFonts.inter(fontSize: 11, color: const Color(0xFF94A3B8), fontWeight: FontWeight.w500),
          ),
          trailing: Container(
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
          children: hijos.map((hijo) => _buildNodoJerarquico(hijo, profundidad + 1, isDark)).toList(),
        ),
      ),
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // TAB 2: UNIDADES DE CONSTRUCCIÓN (CU12)
  // ──────────────────────────────────────────────────────────────────────────
  Widget _buildTabUnidades(bool isDark) {
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
    final subColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);

    return RefreshIndicator(
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
            padding: const EdgeInsets.all(16),
            children: [
              // Filtro rápido de estados
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
                        Text('No hay unidades en este estado', style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w700, color: titleColor)),
                      ],
                    ),
                  ),
                )
              else
                ...filtradas.map((u) {
                  final cod = u['codigo']?.toString() ?? 'U-00';
                  final tipo = u['tipo']?.toString() ?? 'DEPARTAMENTO';
                  final est = (u['estado'] ?? 'PLANIFICADO').toString();
                  final area = u['area_m2']?.toString() ?? '0';
                  final precio = u['precio']?.toString() ?? '-';

                  return Container(
                    margin: const EdgeInsets.only(bottom: 10),
                    decoration: BoxDecoration(
                      color: cardBg,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: borderColor),
                    ),
                    child: ListTile(
                      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                      leading: Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: isDark ? const Color(0xFF2E1C14) : const Color(0xFFFFF7ED),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Icon(Icons.door_sliding_rounded, color: AppTheme.primary, size: 20),
                      ),
                      title: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(cod, style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w800, color: titleColor)),
                          ConstructionStatusBadge(status: est, compact: true),
                        ],
                      ),
                      subtitle: Padding(
                        padding: const EdgeInsets.only(top: 4.0),
                        child: Row(
                          children: [
                            Text(tipo, style: GoogleFonts.inter(fontSize: 11.5, color: subColor, fontWeight: FontWeight.w600)),
                            const SizedBox(width: 8),
                            Text('·', style: TextStyle(color: subColor)),
                            const SizedBox(width: 8),
                            Text('$area m²', style: GoogleFonts.inter(fontSize: 11.5, color: subColor)),
                            if (precio != '-') ...[
                              const SizedBox(width: 8),
                              Text('·', style: TextStyle(color: subColor)),
                              const SizedBox(width: 8),
                              Text('$precio BOB', style: GoogleFonts.inter(fontSize: 11.5, color: isDark ? const Color(0xFF34D399) : AppTheme.success, fontWeight: FontWeight.w700)),
                            ],
                          ],
                        ),
                      ),
                      trailing: const Icon(Icons.chevron_right_rounded, color: Color(0xFF94A3B8)),
                      onTap: () => _mostrarModalDetalleUnidad(u),
                    ),
                  );
                }),
            ],
          );
        },
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

  // ──────────────────────────────────────────────────────────────────────────
  // TAB 3: MAPA INTERACTIVO Y FICHA TÉCNICA
  // ──────────────────────────────────────────────────────────────────────────
  Widget _buildTabMapaYFicha(bool isDark) {
    return FutureBuilder<Map<String, dynamic>>(
      future: _futureDetalle,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator(color: AppTheme.primary, strokeWidth: 2.5));
        }

        final data = snapshot.data ?? {};
        final moneda = data['moneda']?.toString() ?? 'BOB';
        final valor = data['valor_estimado']?.toString() ?? 'No especificado';
        final descripcion = data['descripcion']?.toString() ?? 'Sin descripción registrada.';
        final zona = data['zona']?.toString() ?? '-';
        final distrito = data['distrito']?.toString() ?? '-';
        final uv = data['uv']?.toString() ?? '-';
        final manzana = data['manzana']?.toString() ?? '-';

        final lat = double.tryParse(data['latitud']?.toString() ?? '') ?? -17.7833;
        final lng = double.tryParse(data['longitud']?.toString() ?? '') ?? -63.1821;
        final puntoObra = LatLng(lat, lng);

        final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
        final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
        final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
        final labelColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);
        final dividerColor = isDark ? const Color(0xFF22304C) : const Color(0xFFF1F5F9);

        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // MAPA INTERACTIVO OPENSTREETMAP
            Container(
              height: 220,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: borderColor),
              ),
              clipBehavior: Clip.antiAlias,
              child: Stack(
                children: [
                  FlutterMap(
                    options: MapOptions(
                      initialCenter: puntoObra,
                      initialZoom: 15.0,
                    ),
                    children: [
                      TileLayer(
                        urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                        userAgentPackageName: 'com.obratec.app',
                      ),
                      MarkerLayer(
                        markers: [
                          Marker(
                            point: puntoObra,
                            width: 50,
                            height: 50,
                            child: Container(
                              decoration: BoxDecoration(
                                color: AppTheme.primary,
                                shape: BoxShape.circle,
                                boxShadow: [
                                  BoxShadow(
                                    color: AppTheme.primary.withValues(alpha: 0.4),
                                    blurRadius: 10,
                                    spreadRadius: 2,
                                  ),
                                ],
                              ),
                              child: const Icon(Icons.apartment_rounded, color: Colors.white, size: 28),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                  Positioned(
                    bottom: 10,
                    left: 10,
                    right: 10,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: (isDark ? const Color(0xFF0F172A) : Colors.white).withValues(alpha: 0.92),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: borderColor),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.location_on_rounded, size: 16, color: AppTheme.primary),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              widget.ubicacion.isNotEmpty ? widget.ubicacion : 'Coordenadas: $lat, $lng',
                              style: GoogleFonts.inter(fontSize: 11.5, fontWeight: FontWeight.w700, color: titleColor),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // Sección Especificaciones
            _buildSection(
              title: 'ESPECIFICACIONES DEL PROYECTO',
              cardBg: cardBg,
              borderColor: borderColor,
              children: [
                _buildInfoRow('Tipo de Obra', widget.tipoNombre, labelColor, titleColor),
                _buildInfoRow('Estado', widget.estado, labelColor, titleColor),
                _buildInfoRow('Moneda', moneda, labelColor, titleColor),
                _buildInfoRow('Presupuesto Inicial', valor, labelColor, titleColor),
                _buildInfoRow('Fecha de Inicio', widget.fechaInicio.isEmpty ? 'No definida' : widget.fechaInicio, labelColor, titleColor),
                Divider(height: 20, color: dividerColor),
                Text('DESCRIPCIÓN', style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w800, color: labelColor)),
                const SizedBox(height: 6),
                Text(
                  descripcion,
                  style: GoogleFonts.inter(fontSize: 13, color: titleColor, height: 1.4),
                ),
              ],
            ),
            const SizedBox(height: 14),

            // Sección Georreferenciación
            _buildSection(
              title: 'DETALLES DE UBICACIÓN',
              cardBg: cardBg,
              borderColor: borderColor,
              children: [
                _buildInfoRow('Dirección', widget.ubicacion.isEmpty ? 'No especificada' : widget.ubicacion, labelColor, titleColor),
                _buildInfoRow('Zona', zona, labelColor, titleColor),
                _buildInfoRow('Distrito', distrito, labelColor, titleColor),
                _buildInfoRow('Unidad Vecinal (UV)', uv, labelColor, titleColor),
                _buildInfoRow('Manzana', manzana, labelColor, titleColor),
              ],
            ),
          ],
        );
      },
    );
  }

  Widget _buildSection({
    required String title,
    required Color cardBg,
    required Color borderColor,
    required List<Widget> children,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderColor),
      ),
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: GoogleFonts.inter(
              fontSize: 11,
              fontWeight: FontWeight.w900,
              color: AppTheme.primary,
              letterSpacing: 0.6,
            ),
          ),
          const SizedBox(height: 14),
          ...children,
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value, Color labelColor, Color valueColor) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: GoogleFonts.inter(fontSize: 12, color: labelColor, fontWeight: FontWeight.w500)),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              value,
              textAlign: TextAlign.end,
              style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w700, color: valueColor),
            ),
          ),
        ],
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
