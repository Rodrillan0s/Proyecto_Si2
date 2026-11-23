import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../services/avance_service.dart';
import '../services/unidad_service.dart';
import '../theme/app_theme.dart';
import '../widgets/construction_widgets.dart';
import '../widgets/incidencia_widgets.dart';

/// CU30 / HU114 / HU115 – Detalle, Avance Físico y Fotografías de Unidad para CLIENTE
class ClienteUnidadDetalleScreen extends StatefulWidget {
  final Map<String, dynamic> unidad;

  const ClienteUnidadDetalleScreen({
    super.key,
    required this.unidad,
  });

  @override
  State<ClienteUnidadDetalleScreen> createState() => _ClienteUnidadDetalleScreenState();
}

class _ClienteUnidadDetalleScreenState extends State<ClienteUnidadDetalleScreen> {
  final AvanceService _avanceService = AvanceService();
  final UnidadService _unidadService = UnidadService();

  // Estado de Avance Físico (HU114)
  bool _cargandoAvance = true;
  String? _errorAvance;
  List<Map<String, dynamic>> _historialAvances = [];

  // Estado de Fotografías (HU115)
  bool _cargandoFotos = true;
  String? _errorFotos;
  List<Map<String, dynamic>> _fotografias = [];

  int get _idObra =>
      int.tryParse(widget.unidad['id_obra']?.toString() ?? '0') ?? 0;
  int get _idUnidad =>
      int.tryParse(widget.unidad['id_unidad']?.toString() ?? '0') ?? 0;

  String get _codigoUnidad =>
      (widget.unidad['codigo_unidad'] ?? widget.unidad['codigo'] ?? 'U-00').toString();
  String get _nombreObra =>
      (widget.unidad['nombre_obra'] ?? 'Obra').toString();
  String get _codigoObra =>
      (widget.unidad['codigo_obra'] ?? '').toString();
  String get _tipoUnidad =>
      (widget.unidad['tipo_unidad'] ?? 'DEPARTAMENTO').toString();
  String get _estadoUnidad =>
      (widget.unidad['estado_unidad_actual'] ?? widget.unidad['estado'] ?? 'EN_CONSTRUCCION').toString();
  String get _estadoAsociacion =>
      (widget.unidad['estado_asociacion'] ?? '').toString();
  String? get _superficie =>
      widget.unidad['superficie'] != null ? '${widget.unidad['superficie']} m²' : null;

  @override
  void initState() {
    super.initState();
    _cargarAvanceFisico();
    _cargarFotografias();
  }

  Future<void> _cargarAvanceFisico() async {
    setState(() {
      _cargandoAvance = true;
      _errorAvance = null;
    });

    try {
      final avances = await _avanceService.consultarAvanceFisicoUnidadCliente(
        idObra: _idObra,
        idUnidad: _idUnidad,
      );

      if (!mounted) return;
      setState(() {
        _historialAvances = avances;
        _cargandoAvance = false;
        _errorAvance = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorAvance = e.toString().replaceFirst('Exception: ', '');
        _cargandoAvance = false;
      });
    }
  }

  Future<void> _cargarFotografias() async {
    setState(() {
      _cargandoFotos = true;
      _errorFotos = null;
    });

    try {
      final fotos = await _unidadService.listarFotografiasUnidadCliente(_idUnidad);

      if (!mounted) return;
      setState(() {
        _fotografias = fotos;
        _cargandoFotos = false;
        _errorFotos = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorFotos = e.toString().replaceFirst('Exception: ', '');
        _cargandoFotos = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
    final subColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);

    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC),
      appBar: AppBar(
        titleSpacing: 0,
        backgroundColor: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
          color: titleColor,
          onPressed: () => Navigator.of(context).maybePop(),
        ),
        title: Text(
          'Avance de Unidad',
          style: GoogleFonts.inter(
            fontSize: 17,
            fontWeight: FontWeight.w800,
            color: titleColor,
          ),
        ),
      ),
      body: SafeArea(
        child: RefreshIndicator(
          color: AppTheme.primary,
          onRefresh: () async {
            await Future.wait([
              _cargarAvanceFisico(),
              _cargarFotografias(),
            ]);
          },
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            children: [
              // 1. Tarjeta Resumen del Inmueble
              _buildFichaInmueble(isDark, cardBg, borderColor, titleColor, subColor),
              const SizedBox(height: 20),

              // 2. Encabezado de la sección de Avance Físico (HU114)
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Avance físico reportado',
                    style: GoogleFonts.inter(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: titleColor,
                    ),
                  ),
                  if (!_cargandoAvance && _errorAvance == null)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppTheme.primary.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        'HU114',
                        style: GoogleFonts.inter(
                          fontSize: 10.5,
                          fontWeight: FontWeight.w800,
                          color: AppTheme.primary,
                        ),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 12),

              // 3. Contenido condicional según estado de carga / error / datos de Avance
              if (_cargandoAvance)
                _buildEstadoCarga(isDark, cardBg, borderColor, subColor)
              else if (_errorAvance != null)
                _buildEstadoError(isDark, cardBg, borderColor, titleColor, subColor)
              else if (_historialAvances.isEmpty)
                _buildEstadoVacio(isDark, cardBg, borderColor, titleColor, subColor)
              else
                ..._buildContenidoAvance(isDark, cardBg, borderColor, titleColor, subColor),

              const SizedBox(height: 28),

              // 4. Encabezado de la sección de Fotografías de la unidad (HU115)
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Fotografías de la unidad',
                    style: GoogleFonts.inter(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: titleColor,
                    ),
                  ),
                  if (!_cargandoFotos && _errorFotos == null)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppTheme.info.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        'HU115',
                        style: GoogleFonts.inter(
                          fontSize: 10.5,
                          fontWeight: FontWeight.w800,
                          color: AppTheme.info,
                        ),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 12),

              // 5. Contenido condicional de Fotografías
              if (_cargandoFotos)
                _buildFotosCarga(isDark, cardBg, borderColor, subColor)
              else if (_errorFotos != null)
                _buildFotosError(isDark, cardBg, borderColor, titleColor, subColor)
              else if (_fotografias.isEmpty)
                _buildFotosVacio(isDark, cardBg, borderColor, titleColor, subColor)
              else
                _buildFotosGaleria(isDark, cardBg, borderColor, titleColor, subColor),
            ],
          ),
        ),
      ),
    );
  }

  /// Tarjeta de datos principales del inmueble
  Widget _buildFichaInmueble(
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Flexible(
                          child: Text(
                            _nombreObra,
                            style: GoogleFonts.inter(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: subColor,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        if (_codigoObra.isNotEmpty) ...[
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1.5),
                            decoration: BoxDecoration(
                              color: isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9),
                              borderRadius: BorderRadius.circular(4),
                              border: Border.all(color: borderColor),
                            ),
                            child: Text(
                              _codigoObra,
                              style: GoogleFonts.inter(
                                fontSize: 10,
                                fontWeight: FontWeight.w700,
                                color: subColor,
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      _codigoUnidad,
                      style: GoogleFonts.inter(
                        fontSize: 22,
                        fontWeight: FontWeight.w900,
                        color: titleColor,
                        letterSpacing: -0.5,
                      ),
                    ),
                  ],
                ),
              ),
              ConstructionStatusBadge(status: _estadoUnidad, compact: false),
            ],
          ),
          const SizedBox(height: 14),
          const Divider(height: 1),
          const SizedBox(height: 12),
          Wrap(
            spacing: 12,
            runSpacing: 8,
            children: [
              _buildPillMeta(
                icon: Icons.category_outlined,
                texto: _tipoUnidad,
                isDark: isDark,
                borderColor: borderColor,
                subColor: subColor,
              ),
              if (_superficie != null)
                _buildPillMeta(
                  icon: Icons.square_foot_rounded,
                  texto: _superficie!,
                  isDark: isDark,
                  borderColor: borderColor,
                  subColor: subColor,
                ),
              if (_estadoAsociacion.isNotEmpty)
                _buildPillMeta(
                  icon: Icons.verified_user_outlined,
                  texto: _estadoAsociacion,
                  isDark: isDark,
                  borderColor: borderColor,
                  subColor: subColor,
                ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPillMeta({
    required IconData icon,
    required String texto,
    required bool isDark,
    required Color borderColor,
    required Color subColor,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1E293B) : const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: borderColor),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: subColor),
          const SizedBox(width: 5),
          Text(
            texto,
            style: GoogleFonts.inter(
              fontSize: 11.5,
              fontWeight: FontWeight.w600,
              color: subColor,
            ),
          ),
        ],
      ),
    );
  }

  // ── HU114: Widgets de Estado de Avance ──────────────────────────────────────

  Widget _buildEstadoCarga(
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color subColor,
  ) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 48),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: borderColor),
      ),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(
              width: 32,
              height: 32,
              child: CircularProgressIndicator(
                strokeWidth: 2.8,
                color: AppTheme.primary,
              ),
            ),
            const SizedBox(height: 14),
            Text(
              'Consultando avance físico...',
              style: GoogleFonts.inter(fontSize: 13, color: subColor),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEstadoError(
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.error.withValues(alpha: 0.4)),
      ),
      child: Column(
        children: [
          const Icon(Icons.error_outline_rounded, color: AppTheme.error, size: 38),
          const SizedBox(height: 12),
          Text(
            'Error al cargar avance físico',
            style: GoogleFonts.inter(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: titleColor,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            _errorAvance ?? 'No se pudo conectar con el servidor.',
            textAlign: TextAlign.center,
            style: GoogleFonts.inter(fontSize: 12.5, color: subColor),
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primary,
              minimumSize: const Size(140, 40),
            ),
            onPressed: _cargarAvanceFisico,
            icon: const Icon(Icons.refresh_rounded, size: 18),
            label: Text('Reintentar', style: GoogleFonts.inter(fontWeight: FontWeight.w700)),
          ),
        ],
      ),
    );
  }

  Widget _buildEstadoVacio(
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 36),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: borderColor),
      ),
      child: Column(
        children: [
          Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9),
              shape: BoxShape.circle,
            ),
            child: Icon(Icons.history_toggle_off_rounded, size: 28, color: subColor),
          ),
          const SizedBox(height: 14),
          Text(
            'Sin registros de avance físico',
            style: GoogleFonts.inter(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: titleColor,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'La constructora aún no ha reportado avances físicos para esta unidad.',
            textAlign: TextAlign.center,
            style: GoogleFonts.inter(fontSize: 12.5, color: subColor, height: 1.35),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildContenidoAvance(
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    final ultimoAvance = _historialAvances.first;
    final double porcentajeActual =
        double.tryParse(ultimoAvance['porcentaje_avance']?.toString() ?? '0') ?? 0.0;
    final String? fechaUltima = ultimoAvance['fecha_registro']?.toString();
    final String estadoReportado = (ultimoAvance['estado_unidad'] ?? _estadoUnidad).toString();

    return [
      // Tarjeta Destacada de Avance Global de la Unidad
      Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: cardBg,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: AppTheme.primary.withValues(alpha: isDark ? 0.35 : 0.45),
            width: 1.2,
          ),
          boxShadow: [
            BoxShadow(
              color: AppTheme.primary.withValues(alpha: isDark ? 0.12 : 0.06),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Porcentaje actual',
                  style: GoogleFonts.inter(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: subColor,
                  ),
                ),
                ConstructionStatusBadge(status: estadoReportado, compact: true),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              crossAxisAlignment: CrossAxisAlignment.baseline,
              textBaseline: TextBaseline.alphabetic,
              children: [
                Text(
                  '${porcentajeActual.toStringAsFixed(porcentajeActual.truncateToDouble() == porcentajeActual ? 0 : 1)}%',
                  style: GoogleFonts.inter(
                    fontSize: 36,
                    fontWeight: FontWeight.w900,
                    color: AppTheme.primary,
                    letterSpacing: -1,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  'completado',
                  style: GoogleFonts.inter(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: subColor,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: LinearProgressIndicator(
                value: (porcentajeActual / 100.0).clamp(0.0, 1.0),
                minHeight: 10,
                backgroundColor: isDark ? const Color(0xFF1E293B) : const Color(0xFFFFEDD5),
                valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.primary),
              ),
            ),
            if (fechaUltima != null) ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  Icon(Icons.event_available_rounded, size: 14, color: subColor),
                  const SizedBox(width: 6),
                  Text(
                    'Última actualización: ${formatearFechaHora(fechaUltima)}',
                    style: GoogleFonts.inter(
                      fontSize: 11.5,
                      color: subColor,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
      const SizedBox(height: 24),

      // Historial Cronológico de Avances
      Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            'Historial de reportes (${_historialAvances.length})',
            style: GoogleFonts.inter(
              fontSize: 15,
              fontWeight: FontWeight.w800,
              color: titleColor,
            ),
          ),
        ],
      ),
      const SizedBox(height: 12),

      ..._historialAvances.map((avance) {
        final double pct = double.tryParse(avance['porcentaje_avance']?.toString() ?? '0') ?? 0.0;
        final String fecha = formatearFechaHora(avance['fecha_registro']);
        final String est = (avance['estado_unidad'] ?? '').toString();
        final String observacion = (avance['observacion'] ?? '').toString().trim();

        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: cardBg,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: borderColor),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: AppTheme.primary.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          '${pct.toStringAsFixed(pct.truncateToDouble() == pct ? 0 : 1)}%',
                          style: GoogleFonts.inter(
                            fontSize: 13,
                            fontWeight: FontWeight.w800,
                            color: AppTheme.primary,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        fecha,
                        style: GoogleFonts.inter(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: subColor,
                        ),
                      ),
                    ],
                  ),
                  if (est.isNotEmpty)
                    ConstructionStatusBadge(status: est, compact: true),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                observacion.isNotEmpty ? observacion : 'Sin observación técnica registrada.',
                style: GoogleFonts.inter(
                  fontSize: 13,
                  color: observacion.isNotEmpty ? titleColor : subColor,
                  fontStyle: observacion.isNotEmpty ? FontStyle.normal : FontStyle.italic,
                  height: 1.35,
                ),
              ),
            ],
          ),
        );
      }),
    ];
  }

  // ── HU115: Widgets de Fotografías de Unidad ────────────────────────────────

  Widget _buildFotosCarga(
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color subColor,
  ) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 36),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: borderColor),
      ),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(
              width: 30,
              height: 30,
              child: CircularProgressIndicator(
                strokeWidth: 2.8,
                color: AppTheme.primary,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              'Cargando fotografías...',
              style: GoogleFonts.inter(fontSize: 13, color: subColor),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFotosError(
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.error.withValues(alpha: 0.4)),
      ),
      child: Column(
        children: [
          const Icon(Icons.broken_image_rounded, color: AppTheme.error, size: 34),
          const SizedBox(height: 10),
          Text(
            'Error al cargar fotografías',
            style: GoogleFonts.inter(
              fontSize: 14.5,
              fontWeight: FontWeight.w700,
              color: titleColor,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            _errorFotos ?? 'No se pudo conectar con el servidor.',
            textAlign: TextAlign.center,
            style: GoogleFonts.inter(fontSize: 12.5, color: subColor),
          ),
          const SizedBox(height: 14),
          ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primary,
              minimumSize: const Size(130, 38),
            ),
            onPressed: _cargarFotografias,
            icon: const Icon(Icons.refresh_rounded, size: 18),
            label: Text('Reintentar', style: GoogleFonts.inter(fontWeight: FontWeight.w700)),
          ),
        ],
      ),
    );
  }

  Widget _buildFotosVacio(
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 32),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: borderColor),
      ),
      child: Column(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9),
              shape: BoxShape.circle,
            ),
            child: Icon(Icons.photo_library_outlined, size: 26, color: subColor),
          ),
          const SizedBox(height: 12),
          Text(
            'Sin fotografías registradas',
            style: GoogleFonts.inter(
              fontSize: 14.5,
              fontWeight: FontWeight.w700,
              color: titleColor,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Aún no se han publicado fotografías actualizadas para esta unidad.',
            textAlign: TextAlign.center,
            style: GoogleFonts.inter(fontSize: 12.5, color: subColor, height: 1.35),
          ),
        ],
      ),
    );
  }

  Widget _buildFotosGaleria(
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: _fotografias.length,
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        childAspectRatio: 0.82,
      ),
      itemBuilder: (context, index) {
        final foto = _fotografias[index];
        final String nombreArchivo = (foto['nombre_archivo'] ?? 'Foto ${index + 1}').toString();
        final String urlArchivo = (foto['url_archivo'] ?? '').toString();
        final bool esPrincipal = foto['es_principal'] == true;
        final String? fechaStr = foto['created_at']?.toString();

        return InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: () => _mostrarFotoAmpliada(context, foto),
          child: Container(
            decoration: BoxDecoration(
              color: cardBg,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: esPrincipal ? const Color(0xFFF59E0B).withValues(alpha: 0.6) : borderColor,
                width: esPrincipal ? 1.4 : 1.0,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: isDark ? 0.2 : 0.04),
                  blurRadius: 6,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Imagen miniatura
                  Expanded(
                    child: Stack(
                      fit: StackFit.expand,
                      children: [
                        _ImagenAutenticada(
                          urlArchivo: urlArchivo,
                          unidadService: _unidadService,
                          fit: BoxFit.cover,
                        ),
                        if (esPrincipal)
                          Positioned(
                            top: 8,
                            left: 8,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                              decoration: BoxDecoration(
                                color: const Color(0xFFF59E0B),
                                borderRadius: BorderRadius.circular(6),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withValues(alpha: 0.3),
                                    blurRadius: 4,
                                  ),
                                ],
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(Icons.star_rounded, size: 12, color: Colors.white),
                                  const SizedBox(width: 3),
                                  Text(
                                    'Principal',
                                    style: GoogleFonts.inter(
                                      fontSize: 10,
                                      fontWeight: FontWeight.w800,
                                      color: Colors.white,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                  // Pie de foto con metadatos
                  Padding(
                    padding: const EdgeInsets.all(10),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          nombreArchivo,
                          style: GoogleFonts.inter(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: titleColor,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        if (fechaStr != null) ...[
                          const SizedBox(height: 3),
                          Text(
                            formatearFechaHora(fechaStr),
                            style: GoogleFonts.inter(
                              fontSize: 10.5,
                              fontWeight: FontWeight.w500,
                              color: subColor,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  void _mostrarFotoAmpliada(BuildContext context, Map<String, dynamic> foto) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
    final subColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);
    final nombreArchivo = (foto['nombre_archivo'] ?? 'Fotografía de unidad').toString();
    final urlArchivo = (foto['url_archivo'] ?? '').toString();
    final esPrincipal = foto['es_principal'] == true;
    final String? createdAt = foto['created_at']?.toString();
    final tamanoBytes = int.tryParse(foto['tamano_bytes']?.toString() ?? '');
    String? tamanoStr;
    if (tamanoBytes != null && tamanoBytes > 0) {
      if (tamanoBytes > 1024 * 1024) {
        tamanoStr = '${(tamanoBytes / (1024 * 1024)).toStringAsFixed(1)} MB';
      } else {
        tamanoStr = '${(tamanoBytes / 1024).toStringAsFixed(1)} KB';
      }
    }

    showDialog(
      context: context,
      builder: (ctx) => Dialog(
        insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
        backgroundColor: cardBg,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        clipBehavior: Clip.antiAlias,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Cabecera del diálogo
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 8, 8),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Flexible(
                              child: Text(
                                nombreArchivo,
                                style: GoogleFonts.inter(
                                  fontSize: 14,
                                  fontWeight: FontWeight.w700,
                                  color: titleColor,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            if (esPrincipal) ...[
                              const SizedBox(width: 8),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: const Color(0xFFF59E0B),
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: Text(
                                  'Principal',
                                  style: GoogleFonts.inter(
                                    fontSize: 10,
                                    fontWeight: FontWeight.w800,
                                    color: Colors.white,
                                  ),
                                ),
                              ),
                            ],
                          ],
                        ),
                        if (createdAt != null) ...[
                          const SizedBox(height: 2),
                          Text(
                            formatearFechaHora(createdAt),
                            style: GoogleFonts.inter(fontSize: 11, color: subColor),
                          ),
                        ],
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close_rounded),
                    color: subColor,
                    onPressed: () => Navigator.of(ctx).pop(),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            // Visor de imagen con zoom interactivo
            Flexible(
              child: Container(
                constraints: BoxConstraints(
                  maxHeight: MediaQuery.of(context).size.height * 0.55,
                ),
                color: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF1F5F9),
                child: InteractiveViewer(
                  minScale: 0.8,
                  maxScale: 4.0,
                  child: Center(
                    child: _ImagenAutenticada(
                      urlArchivo: urlArchivo,
                      unidadService: _unidadService,
                      fit: BoxFit.contain,
                    ),
                  ),
                ),
              ),
            ),
            if (tamanoStr != null) ...[
              const Divider(height: 1),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Tamaño de archivo',
                      style: GoogleFonts.inter(fontSize: 11.5, color: subColor),
                    ),
                    Text(
                      tamanoStr,
                      style: GoogleFonts.inter(
                        fontSize: 11.5,
                        fontWeight: FontWeight.w600,
                        color: titleColor,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Widget auxiliar para descargar y visualizar imágenes privadas mediante autenticación Bearer
class _ImagenAutenticada extends StatefulWidget {
  final String urlArchivo;
  final UnidadService unidadService;
  final BoxFit fit;

  const _ImagenAutenticada({
    required this.urlArchivo,
    required this.unidadService,
    this.fit = BoxFit.cover,
  });

  static final Map<String, Uint8List> _cacheEnMemoria = {};

  @override
  State<_ImagenAutenticada> createState() => _ImagenAutenticadaState();
}

class _ImagenAutenticadaState extends State<_ImagenAutenticada> {
  Uint8List? _bytes;
  bool _cargando = true;
  bool _error = false;

  @override
  void initState() {
    super.initState();
    _cargarImagen();
  }

  @override
  void didUpdateWidget(covariant _ImagenAutenticada oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.urlArchivo != widget.urlArchivo) {
      _cargarImagen();
    }
  }

  Future<void> _cargarImagen() async {
    if (widget.urlArchivo.isEmpty) {
      if (mounted) {
        setState(() {
          _cargando = false;
          _error = true;
        });
      }
      return;
    }

    if (_ImagenAutenticada._cacheEnMemoria.containsKey(widget.urlArchivo)) {
      if (mounted) {
        setState(() {
          _bytes = _ImagenAutenticada._cacheEnMemoria[widget.urlArchivo];
          _cargando = false;
          _error = false;
        });
      }
      return;
    }

    try {
      final bytes = await widget.unidadService.descargarArchivoFotografia(widget.urlArchivo);
      _ImagenAutenticada._cacheEnMemoria[widget.urlArchivo] = bytes;
      if (!mounted) return;
      setState(() {
        _bytes = bytes;
        _cargando = false;
        _error = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _cargando = false;
        _error = true;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_cargando) {
      return const Center(
        child: SizedBox(
          width: 24,
          height: 24,
          child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primary),
        ),
      );
    }

    if (_error || _bytes == null) {
      return Container(
        color: Theme.of(context).brightness == Brightness.dark
            ? const Color(0xFF1E293B)
            : const Color(0xFFF1F5F9),
        child: const Center(
          child: Icon(Icons.image_not_supported_outlined, size: 28, color: Color(0xFF94A3B8)),
        ),
      );
    }

    return Image.memory(
      _bytes!,
      fit: widget.fit,
      width: double.infinity,
      height: double.infinity,
      errorBuilder: (_, __, ___) => Container(
        color: const Color(0xFF1E293B),
        child: const Center(
          child: Icon(Icons.broken_image_outlined, size: 28, color: Color(0xFF94A3B8)),
        ),
      ),
    );
  }
}
