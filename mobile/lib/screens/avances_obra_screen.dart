import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../services/avance_service.dart';
import '../theme/app_theme.dart';

/// CU18 – Pantalla de Avances de Obra (Bitácora de Órdenes de Trabajo)
/// El avance físico no es editable directamente; se calcula en base al
/// cumplimiento de las órdenes de trabajo programadas para la obra.
class AvancesObraScreen extends StatefulWidget {
  final int idObra;
  final String nombreObra;
  final String codigoObra;

  const AvancesObraScreen({
    super.key,
    required this.idObra,
    required this.nombreObra,
    required this.codigoObra,
  });

  @override
  State<AvancesObraScreen> createState() => _AvancesObraScreenState();
}

class _AvancesObraScreenState extends State<AvancesObraScreen>
    with SingleTickerProviderStateMixin {
  final AvanceService _avanceService = AvanceService();

  late TabController _tabController;
  final TextEditingController _searchCtrl = TextEditingController();

  bool _cargando = true;
  String? _error;

  // Datos
  List<Map<String, dynamic>> _todasLasOrdenes = [];
  List<Map<String, dynamic>> _ordenesFiltradas = [];

  double _porcentajeAvance = 0.0;
  int _totalOrdenes = 0;
  int _ordenesCumplidas = 0;
  int _ordenesPendientes = 0;
  List<dynamic> _cuadrillas = [];
  int? _cuadrillaSeleccionada;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _tabController.addListener(() {
      if (!_tabController.indexIsChanging) {
        _aplicarFiltros();
      }
    });
    _cargarDatos();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchCtrl.dispose();
    super.dispose();
  }

  Future<void> _cargarDatos() async {
    setState(() {
      _cargando = true;
      _error = null;
    });

    try {
      final res = await _avanceService.resumenAvances(widget.idObra);
      final list = await _avanceService.listarAvances(widget.idObra);

      if (mounted) {
        setState(() {
          _porcentajeAvance =
              double.tryParse((res['porcentaje_avance'] ?? 0).toString()) ??
                  0.0;
          _totalOrdenes = (res['total_ordenes'] as num?)?.toInt() ?? 0;
          _ordenesCumplidas = (res['ordenes_cumplidas'] as num?)?.toInt() ?? 0;
          _ordenesPendientes =
              (res['ordenes_pendientes'] as num?)?.toInt() ?? 0;
          _cuadrillas = (res['cuadrillas'] as List?) ?? [];

          _todasLasOrdenes = list;
          _aplicarFiltros();
          _cargando = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString().replaceFirst('Exception: ', '');
          _cargando = false;
        });
      }
    }
  }

  void _aplicarFiltros() {
    List<Map<String, dynamic>> filtradas = List.from(_todasLasOrdenes);

    // Filtro según tab: 0 = Todas, 1 = Cumplidas, 2 = Faltantes por cumplir
    if (_tabController.index == 1) {
      filtradas = filtradas.where((o) => o['es_cumplida'] == true).toList();
    } else if (_tabController.index == 2) {
      filtradas = filtradas.where((o) => o['es_cumplida'] != true).toList();
    }

    // Filtro por cuadrilla
    if (_cuadrillaSeleccionada != null) {
      filtradas = filtradas
          .where((o) => o['cuadrilla'] == _cuadrillaSeleccionada)
          .toList();
    }

    // Filtro por texto
    final query = _searchCtrl.text.trim().toLowerCase();
    if (query.isNotEmpty) {
      filtradas = filtradas.where((o) {
        final tipo = (o['tipo_trab'] ?? '').toString().toLowerCase();
        final obs = (o['observacion'] ?? '').toString().toLowerCase();
        final nro = (o['orden_nro'] ?? '').toString();
        final respList = (o['responsables'] as List?) ?? [];
        final respNombres = respList
            .map((r) => (r['nombre_completo'] ?? '').toString().toLowerCase())
            .join(' ');
        return tipo.contains(query) ||
            obs.contains(query) ||
            nro.contains(query) ||
            respNombres.contains(query);
      }).toList();
    }

    setState(() {
      _ordenesFiltradas = filtradas;
    });
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor:
          isDark ? AppTheme.darkBackground : AppTheme.background,
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Bitácora de Avances',
              style: GoogleFonts.inter(
                fontSize: 16,
                fontWeight: FontWeight.w700,
              ),
            ),
            Text(
              '${widget.codigoObra} – ${widget.nombreObra}',
              style: GoogleFonts.inter(
                fontSize: 11,
                color: isDark ? AppTheme.darkTextSecondary : AppTheme.textSecondary,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Actualizar',
            onPressed: _cargarDatos,
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppTheme.primary,
          labelColor: AppTheme.primary,
          unselectedLabelColor:
              isDark ? AppTheme.darkTextSecondary : AppTheme.textSecondary,
          labelStyle:
              GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w700),
          isScrollable: true,
          tabAlignment: TabAlignment.start,
          labelPadding: const EdgeInsets.symmetric(horizontal: 14),
          tabs: [
            Tab(text: 'Todas ($_totalOrdenes)'),
            Tab(text: 'Cumplidas ($_ordenesCumplidas)'),
            Tab(text: 'Faltantes ($_ordenesPendientes)'),
          ],
        ),
      ),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _buildErrorView(isDark)
              : RefreshIndicator(
                  onRefresh: _cargarDatos,
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
                    children: [
                      // 1. Tarjeta de Avance Global (Cálculo Automático)
                      _buildAvanceGlobalCard(isDark),
                      const SizedBox(height: 16),

                      // 2. Banner de Cuadrillas / Unidades Operativas
                      if (_cuadrillas.isNotEmpty) ...[
                        _buildCuadrillasSection(isDark),
                        const SizedBox(height: 16),
                      ],

                      // 3. Barra de búsqueda y conteo
                      _buildSearchBar(isDark),
                      const SizedBox(height: 14),

                      // 4. Lista de Órdenes
                      if (_ordenesFiltradas.isEmpty)
                        _buildEmptyList(isDark)
                      else
                        ..._ordenesFiltradas.map((o) => _buildOrdenCard(o, isDark)),
                    ],
                  ),
                ),
    );
  }

  // ── Tarjeta de Avance Global ──────────────────────────────────────────────
  Widget _buildAvanceGlobalCard(bool isDark) {
    final bool completado = _porcentajeAvance >= 100.0;
    final Color colorAcento =
        completado ? AppTheme.success : AppTheme.primary;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: isDark ? AppTheme.darkSurface : Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isDark ? AppTheme.darkBorder : AppTheme.border,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: isDark ? 0.2 : 0.04),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: colorAcento.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Icon(Icons.analytics_rounded,
                          color: colorAcento, size: 20),
                    ),
                    const SizedBox(width: 8),
                    Flexible(
                      child: Text(
                        'AVANCE FÍSICO',
                        style: GoogleFonts.inter(
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.8,
                          color: isDark
                              ? AppTheme.darkTextSecondary
                              : AppTheme.textSecondary,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
                decoration: BoxDecoration(
                  color: colorAcento.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  completado ? 'COMPLETADO' : 'CÁLCULO AUTO',
                  style: GoogleFonts.inter(
                    fontSize: 9.5,
                    fontWeight: FontWeight.w800,
                    color: colorAcento,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),

          // Número de Porcentaje
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                '${_porcentajeAvance.toStringAsFixed(1)}%',
                style: GoogleFonts.inter(
                  fontSize: 32,
                  fontWeight: FontWeight.w900,
                  color: colorAcento,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  '($_ordenesCumplidas de $_totalOrdenes cumplidas)',
                  style: GoogleFonts.inter(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w500,
                    color: isDark
                        ? AppTheme.darkTextSecondary
                        : AppTheme.textSecondary,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // Barra de progreso
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: (_porcentajeAvance / 100.0).clamp(0.0, 1.0),
              minHeight: 10,
              backgroundColor: isDark
                  ? AppTheme.darkBorder
                  : const Color(0xFFF1F5F9),
              valueColor: AlwaysStoppedAnimation<Color>(colorAcento),
            ),
          ),
          const SizedBox(height: 12),

          // Explicación
          Text(
            completado
                ? 'Todas las órdenes de trabajo programadas han sido cumplidas al 100%.'
                : 'Faltan $_ordenesPendientes órdenes por cumplir para alcanzar el 100% (${(100.0 - _porcentajeAvance).toStringAsFixed(1)}% restante).',
            style: GoogleFonts.inter(
              fontSize: 11.5,
              color: isDark
                  ? AppTheme.darkTextSecondary
                  : AppTheme.textSecondary,
            ),
          ),
        ],
      ),
    );
  }

  // ── Sección de Cuadrillas ────────────────────────────────────────────────
  Widget _buildCuadrillasSection(bool isDark) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'UNIDADES OPERATIVAS / CUADRILLAS',
          style: GoogleFonts.inter(
            fontSize: 11,
            fontWeight: FontWeight.w800,
            letterSpacing: 0.8,
            color: isDark ? AppTheme.darkTextSecondary : AppTheme.textSecondary,
          ),
        ),
        const SizedBox(height: 8),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: _cuadrillas.map((c) {
              final cuadrillaNro = c['cuadrilla'];
              final int tot = (c['total_ordenes'] as num?)?.toInt() ?? 0;
              final int cump = (c['cumplidas'] as num?)?.toInt() ?? 0;
              final bool isSelected = _cuadrillaSeleccionada == cuadrillaNro;

              return Padding(
                padding: const EdgeInsets.only(right: 8),
                child: FilterChip(
                  selected: isSelected,
                  selectedColor: AppTheme.primary.withValues(alpha: 0.15),
                  backgroundColor: isDark
                      ? AppTheme.darkSurface
                      : Colors.white,
                  side: BorderSide(
                    color: isSelected
                        ? AppTheme.primary
                        : (isDark ? AppTheme.darkBorder : AppTheme.border),
                  ),
                  label: Text(
                    'Cuadrilla $cuadrillaNro ($cump/$tot)',
                    style: GoogleFonts.inter(
                      fontSize: 11.5,
                      fontWeight: isSelected ? FontWeight.w800 : FontWeight.w600,
                      color: isSelected
                          ? AppTheme.primary
                          : (isDark ? Colors.white : AppTheme.textPrimary),
                    ),
                  ),
                  onSelected: (val) {
                    setState(() {
                      _cuadrillaSeleccionada = val ? cuadrillaNro : null;
                      _aplicarFiltros();
                    });
                  },
                ),
              );
            }).toList(),
          ),
        ),
      ],
    );
  }

  // ── Barra de Búsqueda ─────────────────────────────────────────────────────
  Widget _buildSearchBar(bool isDark) {
    return TextField(
      controller: _searchCtrl,
      onChanged: (_) => _aplicarFiltros(),
      style: GoogleFonts.inter(fontSize: 13),
      decoration: InputDecoration(
        hintText: 'Buscar por orden, trabajo o personal...',
        prefixIcon: const Icon(Icons.search_rounded, size: 18),
        suffixIcon: _searchCtrl.text.isNotEmpty
            ? IconButton(
                icon: const Icon(Icons.close_rounded, size: 16),
                onPressed: () {
                  _searchCtrl.clear();
                  _aplicarFiltros();
                },
              )
            : null,
      ),
    );
  }

  // ── Tarjeta de Orden de Trabajo ───────────────────────────────────────────
  Widget _buildOrdenCard(Map<String, dynamic> o, bool isDark) {
    final bool cumplida = o['es_cumplida'] == true;
    final int ordenNro = (o['orden_nro'] as num?)?.toInt() ?? 0;
    final String tipoTrab = o['tipo_trab'] ?? 'Trabajo general';
    final int? cuadrilla = o['cuadrilla'];
    final String? fInicio = o['fecha_inicio'];
    final String? fFin = o['fecha_fin'];
    final String? obs = o['observacion'];
    final double peso =
        double.tryParse((o['peso_porcentual'] ?? 0).toString()) ?? 0.0;
    final List<dynamic> responsables = (o['responsables'] as List?) ?? [];

    final Color badgeColor =
        cumplida ? AppTheme.success : AppTheme.warning;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark ? AppTheme.darkSurface : Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isDark ? AppTheme.darkBorder : AppTheme.border,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header de la tarjeta
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: badgeColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '#OT-$ordenNro',
                  style: GoogleFonts.inter(
                    fontSize: 11,
                    fontWeight: FontWeight.w900,
                    color: badgeColor,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  tipoTrab,
                  style: GoogleFonts.inter(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: isDark ? Colors.white : AppTheme.textPrimary,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: badgeColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  cumplida ? 'CUMPLIDA' : 'PENDIENTE',
                  style: GoogleFonts.inter(
                    fontSize: 9.5,
                    fontWeight: FontWeight.w800,
                    color: badgeColor,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // Aporte porcentual y Cuadrilla
          Wrap(
            crossAxisAlignment: WrapCrossAlignment.center,
            spacing: 6,
            runSpacing: 4,
            children: [
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.pie_chart_outline_rounded,
                      size: 14, color: badgeColor),
                  const SizedBox(width: 5),
                  Text(
                    cumplida
                        ? 'Aporte: +${peso.toStringAsFixed(1)}%'
                        : 'Aportará: +${peso.toStringAsFixed(1)}%',
                    style: GoogleFonts.inter(
                      fontSize: 11.5,
                      fontWeight: FontWeight.w700,
                      color: badgeColor,
                    ),
                  ),
                ],
              ),
              if (cuadrilla != null)
                Text(
                  '· Cuadrilla $cuadrilla',
                  style: GoogleFonts.inter(
                    fontSize: 11.5,
                    color: isDark
                        ? AppTheme.darkTextSecondary
                        : AppTheme.textSecondary,
                  ),
                ),
            ],
          ),

          // Fechas
          if (fInicio != null) ...[
            const SizedBox(height: 6),
            Row(
              children: [
                Icon(Icons.calendar_today_rounded,
                    size: 13,
                    color: isDark
                        ? AppTheme.darkTextSecondary
                        : AppTheme.textSecondary),
                const SizedBox(width: 6),
                Text(
                  fFin != null ? '$fInicio → $fFin' : 'Iniciado el $fInicio',
                  style: GoogleFonts.inter(
                    fontSize: 11,
                    color: isDark
                        ? AppTheme.darkTextSecondary
                        : AppTheme.textSecondary,
                  ),
                ),
              ],
            ),
          ],

          // Observaciones
          if (obs != null && obs.trim().isNotEmpty) ...[
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: isDark
                    ? AppTheme.darkBackground
                    : const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                obs,
                style: GoogleFonts.inter(
                  fontSize: 11.5,
                  color: isDark
                      ? AppTheme.darkTextSecondary
                      : AppTheme.textSecondary,
                ),
              ),
            ),
          ],

          // Personal asignado / Cuadrilla
          if (responsables.isNotEmpty) ...[
            const SizedBox(height: 10),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: responsables.map((r) {
                final String nombre = r['nombre_completo'] ?? 'Personal';
                return Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                  decoration: BoxDecoration(
                    color: isDark
                        ? AppTheme.darkBackground
                        : const Color(0xFFF1F5F9),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.person_rounded, size: 11),
                      const SizedBox(width: 4),
                      Text(
                        nombre,
                        style: GoogleFonts.inter(
                          fontSize: 10.5,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ],
        ],
      ),
    );
  }

  // ── Vista de Error ────────────────────────────────────────────────────────
  Widget _buildErrorView(bool isDark) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline_rounded,
                color: AppTheme.error, size: 48),
            const SizedBox(height: 12),
            Text(
              'No se pudo cargar la bitácora',
              style: GoogleFonts.inter(
                fontSize: 16,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              _error ?? 'Error desconocido',
              textAlign: TextAlign.center,
              style: GoogleFonts.inter(
                fontSize: 12,
                color: isDark
                    ? AppTheme.darkTextSecondary
                    : AppTheme.textSecondary,
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _cargarDatos,
              icon: const Icon(Icons.refresh_rounded, size: 18),
              label: const Text('Reintentar'),
            ),
          ],
        ),
      ),
    );
  }

  // ── Lista Vacía ───────────────────────────────────────────────────────────
  Widget _buildEmptyList(bool isDark) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 40),
        child: Column(
          children: [
            Icon(Icons.assignment_outlined,
                size: 48,
                color: isDark
                    ? AppTheme.darkTextSecondary
                    : AppTheme.textSecondary),
            const SizedBox(height: 12),
            Text(
              'No hay órdenes de trabajo',
              style: GoogleFonts.inter(
                fontSize: 14,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              _totalOrdenes == 0
                  ? 'Esta obra no cuenta con órdenes de trabajo programadas.'
                  : 'Ninguna orden coincide con los filtros aplicados.',
              style: GoogleFonts.inter(
                fontSize: 11.5,
                color: isDark
                    ? AppTheme.darkTextSecondary
                    : AppTheme.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
