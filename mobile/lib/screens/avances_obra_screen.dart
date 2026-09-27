import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../services/auth_provider.dart';
import '../services/avance_service.dart';
import '../services/unidad_service.dart';
import '../theme/app_theme.dart';

/// CU18 – Pantalla de Avances de Obra
/// Permite registrar y consultar avances de las unidades de construcción.
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
  final UnidadService _unidadService = UnidadService();
  late TabController _tabController;

  late Future<Map<String, dynamic>> _futureResumen;
  late Future<List<Map<String, dynamic>>> _futureHistorial;
  late Future<List<Map<String, dynamic>>> _futureUnidades;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _recargar();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _recargar() {
    setState(() {
      _futureResumen = _avanceService.resumenAvances(widget.idObra);
      _futureHistorial = _avanceService.listarAvances(widget.idObra);
      _futureUnidades = _unidadService.listarUnidades(widget.idObra);
    });
  }

  bool _puedeRegistrar() {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    return auth.hasPermission('Registrar_avances') ||
        auth.esAdminGlobal ||
        auth.esAdminEmpresa ||
        auth.esJefeObra;
  }

  // ── Colors ────────────────────────────────────────────────────────────────

  Color _colorPorcentaje(double pct, bool isDark) {
    if (pct >= 100) return isDark ? const Color(0xFF34D399) : AppTheme.success;
    if (pct >= 60) return isDark ? const Color(0xFFFBBF24) : AppTheme.warning;
    if (pct > 0) return isDark ? const Color(0xFFFB923C) : AppTheme.primary;
    return isDark ? const Color(0xFF94A3B8) : AppTheme.textMuted;
  }

  Color _colorEstado(String estado, bool isDark) {
    switch (estado.toUpperCase()) {
      case 'FINALIZADO':
        return isDark ? const Color(0xFF34D399) : AppTheme.success;
      case 'EN_CONSTRUCCION':
        return isDark ? const Color(0xFFFBBF24) : AppTheme.warning;
      case 'SUSPENDIDO':
        return isDark ? const Color(0xFFF87171) : AppTheme.error;
      default:
        return isDark ? const Color(0xFF94A3B8) : AppTheme.textMuted;
    }
  }

  // ── Modal de registro de avance ────────────────────────────────────────────

  void _mostrarModalRegistro(List<Map<String, dynamic>> unidades) {
    if (unidades.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('No hay unidades de construcción en este proyecto.'),
      ));
      return;
    }

    int? idUnidadSel = unidades.first['id_unidad'] as int?;
    double porcentaje = 0;
    DateTime fechaSel = DateTime.now();
    final obsCtrl = TextEditingController();
    bool guardando = false;
    final formKey = GlobalKey<FormState>();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setModal) {
          final isDark = Theme.of(context).brightness == Brightness.dark;
          final sheetBg = isDark ? AppTheme.darkSurface : Colors.white;

          return Padding(
            padding: EdgeInsets.only(
              bottom: MediaQuery.of(context).viewInsets.bottom,
            ),
            child: Container(
              decoration: BoxDecoration(
                color: sheetBg,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
                border: Border.all(
                  color: isDark ? AppTheme.darkBorder : AppTheme.border,
                ),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Handle
                  Container(
                    margin: const EdgeInsets.only(top: 12),
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: isDark ? AppTheme.darkBorder : AppTheme.border,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
                    child: Form(
                      key: formKey,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Título
                          Row(
                            children: [
                              const Icon(Icons.trending_up_rounded,
                                  color: AppTheme.primary, size: 22),
                              const SizedBox(width: 8),
                              Text(
                                'Registrar Avance',
                                style: GoogleFonts.inter(
                                  fontSize: 17,
                                  fontWeight: FontWeight.w800,
                                  color: isDark
                                      ? AppTheme.darkTextPrimary
                                      : AppTheme.textPrimary,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 20),

                          // Dropdown de unidad
                          Text('Unidad de Construcción *',
                              style: GoogleFonts.inter(
                                fontSize: 11.5,
                                fontWeight: FontWeight.w700,
                                color: AppTheme.textSecondary,
                              )),
                          const SizedBox(height: 6),
                          DropdownButtonFormField<int>(
                            initialValue: idUnidadSel,
                            isExpanded: true,
                            decoration: const InputDecoration(),
                            validator: (v) =>
                                v == null ? 'Seleccione una unidad.' : null,
                            items: unidades
                                .map((u) => DropdownMenuItem<int>(
                                      value: u['id_unidad'] as int,
                                      child: Text(
                                        '${u['codigo'] ?? ''} – ${u['nombre'] ?? ''}',
                                        overflow: TextOverflow.ellipsis,
                                        style: GoogleFonts.inter(fontSize: 13),
                                      ),
                                    ))
                                .toList(),
                            onChanged: (v) =>
                                setModal(() => idUnidadSel = v),
                          ),
                          const SizedBox(height: 16),

                          // Porcentaje slider
                          Row(
                            children: [
                              Text('Porcentaje de Avance *',
                                  style: GoogleFonts.inter(
                                    fontSize: 11.5,
                                    fontWeight: FontWeight.w700,
                                    color: AppTheme.textSecondary,
                                  )),
                              const Spacer(),
                              Text(
                                '${porcentaje.round()}%',
                                style: GoogleFonts.inter(
                                  fontSize: 18,
                                  fontWeight: FontWeight.w900,
                                  color: _colorPorcentaje(porcentaje, isDark),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          SliderTheme(
                            data: SliderThemeData(
                              activeTrackColor: AppTheme.primary,
                              inactiveTrackColor: isDark
                                  ? AppTheme.darkBorder
                                  : AppTheme.border,
                              thumbColor: AppTheme.primary,
                              overlayColor:
                                  AppTheme.primary.withValues(alpha: 0.12),
                            ),
                            child: Slider(
                              value: porcentaje,
                              min: 0,
                              max: 100,
                              divisions: 100,
                              onChanged: (v) =>
                                  setModal(() => porcentaje = v),
                            ),
                          ),
                          // Barra de preview
                          ClipRRect(
                            borderRadius: BorderRadius.circular(4),
                            child: LinearProgressIndicator(
                              value: porcentaje / 100,
                              minHeight: 6,
                              backgroundColor:
                                  isDark ? AppTheme.darkBorder : AppTheme.border,
                              valueColor: AlwaysStoppedAnimation(
                                  _colorPorcentaje(porcentaje, isDark)),
                            ),
                          ),
                          const SizedBox(height: 16),

                          // Fecha
                          Text('Fecha de Registro *',
                              style: GoogleFonts.inter(
                                fontSize: 11.5,
                                fontWeight: FontWeight.w700,
                                color: AppTheme.textSecondary,
                              )),
                          const SizedBox(height: 6),
                          InkWell(
                            onTap: () async {
                              final picked = await showDatePicker(
                                context: context,
                                initialDate: fechaSel,
                                firstDate: DateTime(2020),
                                lastDate: DateTime.now().add(
                                    const Duration(days: 1)),
                              );
                              if (picked != null) {
                                setModal(() => fechaSel = picked);
                              }
                            },
                            borderRadius: BorderRadius.circular(12),
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 14, vertical: 14),
                              decoration: BoxDecoration(
                                border: Border.all(
                                    color: isDark
                                        ? AppTheme.darkBorder
                                        : AppTheme.border),
                                borderRadius: BorderRadius.circular(12),
                                color: isDark
                                    ? AppTheme.darkBackground
                                    : Colors.white,
                              ),
                              child: Row(
                                children: [
                                  const Icon(Icons.calendar_today_rounded,
                                      size: 16, color: AppTheme.primary),
                                  const SizedBox(width: 10),
                                  Text(
                                    '${fechaSel.day.toString().padLeft(2, '0')}/${fechaSel.month.toString().padLeft(2, '0')}/${fechaSel.year}',
                                    style: GoogleFonts.inter(
                                      fontSize: 13.5,
                                      fontWeight: FontWeight.w600,
                                      color: isDark
                                          ? AppTheme.darkTextPrimary
                                          : AppTheme.textPrimary,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(height: 16),

                          // Observaciones
                          Text('Observaciones',
                              style: GoogleFonts.inter(
                                fontSize: 11.5,
                                fontWeight: FontWeight.w700,
                                color: AppTheme.textSecondary,
                              )),
                          const SizedBox(height: 6),
                          TextFormField(
                            controller: obsCtrl,
                            maxLines: 3,
                            decoration: const InputDecoration(
                              hintText:
                                  'Descripción del trabajo realizado, observaciones...',
                            ),
                            style: GoogleFonts.inter(fontSize: 13.5),
                          ),
                          const SizedBox(height: 24),

                          // Botones
                          Row(
                            children: [
                              Expanded(
                                child: OutlinedButton(
                                  onPressed: guardando
                                      ? null
                                      : () => Navigator.pop(context),
                                  child: const Text('Cancelar'),
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: ElevatedButton(
                                  onPressed: guardando
                                      ? null
                                      : () async {
                                          if (!formKey.currentState!.validate()) {
                                            return;
                                          }
                                          final scaffoldMessenger =
                                              ScaffoldMessenger.of(context);
                                          setModal(() => guardando = true);
                                          try {
                                            final fStr =
                                                '${fechaSel.year}-${fechaSel.month.toString().padLeft(2, '0')}-${fechaSel.day.toString().padLeft(2, '0')}';
                                            await _avanceService
                                                .registrarAvance(
                                              idObra: widget.idObra,
                                              idUnidad: idUnidadSel!,
                                              porcentaje: porcentaje,
                                              fechaRegistro: fStr,
                                              observacion:
                                                  obsCtrl.text.trim(),
                                            );
                                            if (ctx.mounted) {
                                              Navigator.pop(ctx);
                                            }
                                            _recargar();
                                            if (mounted) {
                                              scaffoldMessenger.showSnackBar(
                                                const SnackBar(
                                                  content: Text(
                                                    'Avance registrado exitosamente.',
                                                  ),
                                                  backgroundColor:
                                                      AppTheme.success,
                                                ),
                                              );
                                            }
                                          } catch (e) {
                                            setModal(
                                                () => guardando = false);
                                            if (mounted) {
                                              scaffoldMessenger.showSnackBar(
                                                SnackBar(
                                                  content: Text(e
                                                      .toString()
                                                      .replaceFirst(
                                                          'Exception: ',
                                                          '')),
                                                  backgroundColor:
                                                      AppTheme.error,
                                                ),
                                              );
                                            }
                                          }
                                        },
                                  child: guardando
                                      ? const SizedBox(
                                          height: 20,
                                          width: 20,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                            color: Colors.white,
                                          ),
                                        )
                                      : const Text('Guardar'),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  // ── Build ──────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: isDark ? AppTheme.darkBackground : AppTheme.background,
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Avances de Obra',
              style: GoogleFonts.inter(
                fontSize: 15,
                fontWeight: FontWeight.w800,
              ),
            ),
            Text(
              widget.codigoObra,
              style: GoogleFonts.inter(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: AppTheme.primary,
              ),
            ),
          ],
        ),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppTheme.primary,
          labelColor: AppTheme.primary,
          unselectedLabelColor:
              isDark ? AppTheme.darkTextSecondary : AppTheme.textSecondary,
          labelStyle: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w700),
          tabs: const [
            Tab(text: 'Resumen'),
            Tab(text: 'Historial'),
          ],
        ),
        actions: [
          FutureBuilder<List<Map<String, dynamic>>>(
            future: _futureUnidades,
            builder: (context, snap) {
              final unidades = snap.data ?? [];
              return _puedeRegistrar()
                  ? IconButton(
                      icon: const Icon(Icons.add_circle_rounded),
                      color: AppTheme.primary,
                      tooltip: 'Registrar avance',
                      onPressed: () => _mostrarModalRegistro(unidades),
                    )
                  : const SizedBox.shrink();
            },
          ),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildTabResumen(isDark),
          _buildTabHistorial(isDark),
        ],
      ),
    );
  }

  // ── Tab: Resumen ──────────────────────────────────────────────────────────

  Widget _buildTabResumen(bool isDark) {
    return FutureBuilder<Map<String, dynamic>>(
      future: _futureResumen,
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snap.hasError) {
          return _errorWidget(snap.error.toString(), isDark);
        }
        final avanceGlobal =
            double.tryParse(snap.data?['avance_global']?.toString() ?? '0') ??
                0.0;
        final unidades =
            (snap.data?['unidades'] as List<dynamic>? ?? [])
                .map((e) => Map<String, dynamic>.from(e as Map))
                .toList();

        return RefreshIndicator(
          onRefresh: () async => _recargar(),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Barra global
              _buildCardAvanceGlobal(avanceGlobal, isDark),
              const SizedBox(height: 16),
              if (unidades.isEmpty)
                _emptyWidget(
                  'No hay unidades de construcción.',
                  'Registra unidades en la sección Estructura.',
                  isDark,
                )
              else
                ...unidades.map((u) => _buildCardUnidad(u, isDark)),
            ],
          ),
        );
      },
    );
  }

  Widget _buildCardAvanceGlobal(double avanceGlobal, bool isDark) {
    final cardBg = isDark ? AppTheme.darkSurface : Colors.white;
    final textColor =
        isDark ? AppTheme.darkTextPrimary : AppTheme.textPrimary;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
            color: isDark ? AppTheme.darkBorder : AppTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Avance Global del Proyecto',
                style: GoogleFonts.inter(
                    fontSize: 13, fontWeight: FontWeight.w700, color: textColor),
              ),
              Text(
                '${avanceGlobal.toStringAsFixed(1)}%',
                style: GoogleFonts.inter(
                  fontSize: 26,
                  fontWeight: FontWeight.w900,
                  color: _colorPorcentaje(avanceGlobal, isDark),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: avanceGlobal / 100,
              minHeight: 10,
              backgroundColor:
                  isDark ? AppTheme.darkBorder : AppTheme.borderLight,
              valueColor: AlwaysStoppedAnimation(
                  _colorPorcentaje(avanceGlobal, isDark)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCardUnidad(Map<String, dynamic> u, bool isDark) {
    final cardBg = isDark ? AppTheme.darkSurface : Colors.white;
    final pct =
        double.tryParse(u['ultimo_avance']?.toString() ?? '0') ?? 0.0;
    final estado = (u['estado_unidad'] ?? '').toString();
    final fecha = u['fecha_ultimo']?.toString();

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
            color: isDark ? AppTheme.darkBorder : AppTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      u['codigo_unidad']?.toString() ?? '',
                      style: GoogleFonts.inter(
                        fontSize: 10.5,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.primary,
                        letterSpacing: 0.3,
                      ),
                    ),
                    Text(
                      u['nombre_unidad']?.toString() ?? '',
                      style: GoogleFonts.inter(
                        fontSize: 13.5,
                        fontWeight: FontWeight.w700,
                        color: isDark
                            ? AppTheme.darkTextPrimary
                            : AppTheme.textPrimary,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: _colorEstado(estado, isDark).withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  estado.replaceAll('_', ' '),
                  style: GoogleFonts.inter(
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    color: _colorEstado(estado, isDark),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Avance',
                  style: GoogleFonts.inter(
                      fontSize: 11.5, color: AppTheme.textSecondary)),
              Text(
                '${pct.toStringAsFixed(0)}%',
                style: GoogleFonts.inter(
                  fontSize: 15,
                  fontWeight: FontWeight.w900,
                  color: _colorPorcentaje(pct, isDark),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: pct / 100,
              minHeight: 6,
              backgroundColor:
                  isDark ? AppTheme.darkBorder : AppTheme.borderLight,
              valueColor:
                  AlwaysStoppedAnimation(_colorPorcentaje(pct, isDark)),
            ),
          ),
          if (fecha != null) ...[
            const SizedBox(height: 6),
            Text(
              'Último registro: $fecha',
              style: GoogleFonts.inter(
                  fontSize: 10.5, color: AppTheme.textMuted),
            ),
          ],
        ],
      ),
    );
  }

  // ── Tab: Historial ────────────────────────────────────────────────────────

  Widget _buildTabHistorial(bool isDark) {
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: _futureHistorial,
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snap.hasError) {
          return _errorWidget(snap.error.toString(), isDark);
        }
        final avances = snap.data ?? [];

        if (avances.isEmpty) {
          return _emptyWidget(
            'Sin registros de avance',
            'Registra el primer avance con el botón + arriba.',
            isDark,
          );
        }

        return RefreshIndicator(
          onRefresh: () async => _recargar(),
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: avances.length,
            itemBuilder: (ctx, i) => _buildCardAvance(avances[i], isDark),
          ),
        );
      },
    );
  }

  Widget _buildCardAvance(Map<String, dynamic> a, bool isDark) {
    final cardBg = isDark ? AppTheme.darkSurface : Colors.white;
    final pct =
        double.tryParse(a['porcentaje_avance']?.toString() ?? '0') ?? 0.0;
    final puede = _puedeRegistrar();

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
            color: isDark ? AppTheme.darkBorder : AppTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      a['codigo_unidad']?.toString() ?? '',
                      style: GoogleFonts.inter(
                        fontSize: 10,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.primary,
                      ),
                    ),
                    Text(
                      a['nombre_unidad']?.toString() ?? '',
                      style: GoogleFonts.inter(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: isDark
                            ? AppTheme.darkTextPrimary
                            : AppTheme.textPrimary,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              Row(
                children: [
                  Text(
                    '${pct.toStringAsFixed(0)}%',
                    style: GoogleFonts.inter(
                      fontSize: 20,
                      fontWeight: FontWeight.w900,
                      color: _colorPorcentaje(pct, isDark),
                    ),
                  ),
                  if (puede) ...[
                    const SizedBox(width: 8),
                    GestureDetector(
                      onTap: () async {
                        final confirm = await showDialog<bool>(
                          context: context,
                          builder: (d) => AlertDialog(
                            title: const Text('Eliminar avance'),
                            content: const Text(
                                '¿Está seguro de que desea eliminar este avance?'),
                            actions: [
                              TextButton(
                                  onPressed: () =>
                                      Navigator.pop(d, false),
                                  child: const Text('Cancelar')),
                              TextButton(
                                  onPressed: () =>
                                      Navigator.pop(d, true),
                                  child: const Text('Eliminar',
                                      style: TextStyle(
                                          color: AppTheme.error))),
                            ],
                          ),
                        );
                        if (confirm == true) {
                          try {
                            await _avanceService.eliminarAvance(
                              widget.idObra,
                              a['id_avance'] as int,
                            );
                            _recargar();
                            if (mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('Avance eliminado.'),
                                ),
                              );
                            }
                          } catch (e) {
                            if (mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                    content: Text(e
                                        .toString()
                                        .replaceFirst('Exception: ', ''))),
                              );
                            }
                          }
                        }
                      },
                      child: const Icon(Icons.delete_outline_rounded,
                          color: AppTheme.error, size: 20),
                    ),
                  ],
                ],
              ),
            ],
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: pct / 100,
              minHeight: 5,
              backgroundColor:
                  isDark ? AppTheme.darkBorder : AppTheme.borderLight,
              valueColor:
                  AlwaysStoppedAnimation(_colorPorcentaje(pct, isDark)),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              const Icon(Icons.calendar_today_rounded,
                  size: 12, color: AppTheme.textMuted),
              const SizedBox(width: 4),
              Text(
                a['fecha_registro']?.toString() ?? '',
                style: GoogleFonts.inter(
                    fontSize: 11, color: AppTheme.textSecondary),
              ),
              const SizedBox(width: 12),
              const Icon(Icons.person_outline_rounded,
                  size: 12, color: AppTheme.textMuted),
              const SizedBox(width: 4),
              Expanded(
                child: Text(
                  a['usuario_nombre']?.toString() ?? '',
                  style: GoogleFonts.inter(
                      fontSize: 11, color: AppTheme.textSecondary),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          if ((a['observacion']?.toString() ?? '').isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(
              a['observacion'].toString(),
              style: GoogleFonts.inter(
                fontSize: 11.5,
                color: isDark
                    ? AppTheme.darkTextSecondary
                    : AppTheme.textSecondary,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ],
      ),
    );
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  Widget _errorWidget(String msg, bool isDark) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline_rounded,
                color: AppTheme.error, size: 40),
            const SizedBox(height: 12),
            Text(
              msg.replaceFirst('Exception: ', ''),
              textAlign: TextAlign.center,
              style: GoogleFonts.inter(
                  fontSize: 13,
                  color: isDark
                      ? AppTheme.darkTextSecondary
                      : AppTheme.textSecondary),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _recargar,
              child: const Text('Reintentar'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _emptyWidget(String title, String subtitle, bool isDark) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('📊', style: TextStyle(fontSize: 48)),
            const SizedBox(height: 16),
            Text(
              title,
              style: GoogleFonts.inter(
                fontSize: 15,
                fontWeight: FontWeight.w700,
                color: isDark
                    ? AppTheme.darkTextPrimary
                    : AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              subtitle,
              textAlign: TextAlign.center,
              style: GoogleFonts.inter(
                fontSize: 12.5,
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
