import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../services/crm_service.dart';
import '../theme/app_theme.dart';
import '../widgets/incidencia_widgets.dart';

/// CU30 / HU117 – Detalle y Seguimiento de Solicitud para CLIENTE
/// Visualización exclusiva de estado, requerimiento y respuesta oficial de la constructora.
class ClienteSolicitudDetalleScreen extends StatefulWidget {
  final Map<String, dynamic> solicitud;

  const ClienteSolicitudDetalleScreen({
    super.key,
    required this.solicitud,
  });

  @override
  State<ClienteSolicitudDetalleScreen> createState() => _ClienteSolicitudDetalleScreenState();
}

class _ClienteSolicitudDetalleScreenState extends State<ClienteSolicitudDetalleScreen> {
  final CrmService _crmService = CrmService();

  late Map<String, dynamic> _solicitudActual;
  bool _cargando = true;
  String? _error;

  int get _idSolicitud =>
      int.tryParse(_solicitudActual['id_solicitud']?.toString() ?? '0') ?? 0;

  @override
  void initState() {
    super.initState();
    _solicitudActual = Map<String, dynamic>.from(widget.solicitud);
    _cargarDetalle();
  }

  Future<void> _cargarDetalle() async {
    if (_idSolicitud == 0) {
      setState(() => _cargando = false);
      return;
    }

    setState(() {
      _cargando = true;
      _error = null;
    });

    try {
      final detalle = await _crmService.obtenerDetalleSolicitudCliente(_idSolicitud);
      if (!mounted) return;
      setState(() {
        _solicitudActual = detalle;
        _cargando = false;
        _error = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString().replaceFirst('Exception: ', '');
        _cargando = false;
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

    final String titulo = (_solicitudActual['titulo'] ?? _solicitudActual['asunto'] ?? 'Solicitud').toString();
    final String descripcion = (_solicitudActual['descripcion'] ?? '').toString();
    final String estado = (_solicitudActual['estado'] ?? 'PENDIENTE').toString();
    final String nombreObra = (_solicitudActual['nombre_obra'] ?? 'Obra no especificada').toString();
    final String codigoObra = (_solicitudActual['codigo_obra'] ?? '').toString();
    final String? codigoUnidad = _solicitudActual['codigo_unidad']?.toString();
    final String? tipoUnidad = _solicitudActual['tipo_unidad']?.toString();
    final String? fechaCreacion = _solicitudActual['fecha_creacion']?.toString();
    final String? respuestaOficial = _solicitudActual['respuesta']?.toString();
    final String? fechaRespuesta = _solicitudActual['fecha_respuesta']?.toString();

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
          'Detalle de Solicitud',
          style: GoogleFonts.inter(
            fontSize: 17,
            fontWeight: FontWeight.w800,
            color: titleColor,
          ),
        ),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 16),
            padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 3),
            decoration: BoxDecoration(
              color: AppTheme.primary.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Center(
              child: Text(
                'HU117',
                style: GoogleFonts.inter(
                  fontSize: 10.5,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.primary,
                ),
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: RefreshIndicator(
          color: AppTheme.primary,
          onRefresh: _cargarDetalle,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            children: [
              if (_error != null) ...[
                Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: AppTheme.error.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppTheme.error.withValues(alpha: 0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.info_outline_rounded, size: 16, color: AppTheme.error),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'No se pudo sincronizar la última actualización: $_error',
                          style: GoogleFonts.inter(fontSize: 11.5, color: AppTheme.error),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
              if (_cargando && _solicitudActual.isEmpty)
                _buildEstadoCarga(isDark, cardBg, borderColor, subColor)
              else ...[
                // 1. Tarjeta principal: Título, estado y fechas
              Container(
                padding: const EdgeInsets.all(18),
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
                          child: Text(
                            titulo,
                            style: GoogleFonts.inter(
                              fontSize: 18,
                              fontWeight: FontWeight.w900,
                              color: titleColor,
                              letterSpacing: -0.3,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        _buildBadgeEstado(estado),
                      ],
                    ),
                    const SizedBox(height: 10),
                    if (fechaCreacion != null) ...[
                      Row(
                        children: [
                          Icon(Icons.calendar_today_rounded, size: 13, color: subColor),
                          const SizedBox(width: 6),
                          Text(
                            'Registrada el ${formatearFechaHora(fechaCreacion)}',
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
              const SizedBox(height: 16),

              // 2. Información del Inmueble Vinculado
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: cardBg,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: borderColor),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Inmueble y Proyecto',
                      style: GoogleFonts.inter(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: subColor,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        Container(
                          width: 38,
                          height: 38,
                          decoration: BoxDecoration(
                            color: AppTheme.primary.withValues(alpha: isDark ? 0.2 : 0.1),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: const Icon(
                            Icons.domain_rounded,
                            color: AppTheme.primary,
                            size: 20,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                nombreObra,
                                style: GoogleFonts.inter(
                                  fontSize: 14.5,
                                  fontWeight: FontWeight.w800,
                                  color: titleColor,
                                ),
                              ),
                              if (codigoObra.isNotEmpty) ...[
                                const SizedBox(height: 1),
                                Text(
                                  codigoObra,
                                  style: GoogleFonts.inter(fontSize: 11.5, color: subColor),
                                ),
                              ],
                            ],
                          ),
                        ),
                        if (codigoUnidad != null) ...[
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                            decoration: BoxDecoration(
                              color: isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: borderColor),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text(
                                  codigoUnidad,
                                  style: GoogleFonts.inter(
                                    fontSize: 12.5,
                                    fontWeight: FontWeight.w800,
                                    color: titleColor,
                                  ),
                                ),
                                if (tipoUnidad != null) ...[
                                  Text(
                                    tipoUnidad,
                                    style: GoogleFonts.inter(
                                      fontSize: 9.5,
                                      fontWeight: FontWeight.w600,
                                      color: subColor,
                                    ),
                                  ),
                                ],
                              ],
                            ),
                          ),
                        ],
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // 3. Descripción de la Solicitud
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: cardBg,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: borderColor),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Requerimiento del Cliente',
                      style: GoogleFonts.inter(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: subColor,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      descripcion.isNotEmpty ? descripcion : 'Sin descripción adicional.',
                      style: GoogleFonts.inter(
                        fontSize: 13.5,
                        color: titleColor,
                        height: 1.45,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // 4. Sección de Respuesta Oficial de la Constructora
              Text(
                'Respuesta de la constructora',
                style: GoogleFonts.inter(
                  fontSize: 15.5,
                  fontWeight: FontWeight.w800,
                  color: titleColor,
                ),
              ),
              const SizedBox(height: 10),

              if (respuestaOficial != null && respuestaOficial.trim().isNotEmpty)
                _buildTarjetaRespuestaOficial(
                  respuesta: respuestaOficial.trim(),
                  fechaRespuesta: fechaRespuesta,
                  isDark: isDark,
                  cardBg: cardBg,
                  borderColor: borderColor,
                  titleColor: titleColor,
                  subColor: subColor,
                )
              else
                _buildTarjetaSinRespuesta(isDark, cardBg, borderColor, titleColor, subColor),
              ],
            ],
          ),
        ),
      ),
    );
  }

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
              'Cargando detalle de solicitud...',
              style: GoogleFonts.inter(fontSize: 13, color: subColor),
            ),
          ],
        ),
      ),
    );
  }

  /// Tarjeta de Respuesta Oficial emitida por la constructora
  Widget _buildTarjetaRespuestaOficial({
    required String respuesta,
    required String? fechaRespuesta,
    required bool isDark,
    required Color cardBg,
    required Color borderColor,
    required Color titleColor,
    required Color subColor,
  }) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: const Color(0xFF10B981).withValues(alpha: isDark ? 0.4 : 0.5),
          width: 1.2,
        ),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF10B981).withValues(alpha: isDark ? 0.1 : 0.05),
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
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: const Color(0xFF10B981).withValues(alpha: 0.15),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.verified_rounded,
                  color: Color(0xFF10B981),
                  size: 18,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Respuesta oficial registrada',
                      style: GoogleFonts.inter(
                        fontSize: 13.5,
                        fontWeight: FontWeight.w800,
                        color: const Color(0xFF10B981),
                      ),
                    ),
                    if (fechaRespuesta != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        'Respondida el ${formatearFechaHora(fechaRespuesta)}',
                        style: GoogleFonts.inter(
                          fontSize: 11,
                          color: subColor,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          const Divider(height: 1),
          const SizedBox(height: 14),
          Text(
            respuesta,
            style: GoogleFonts.inter(
              fontSize: 13.5,
              color: titleColor,
              height: 1.45,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  /// Tarjeta cuando la solicitud todavía no tiene respuesta
  Widget _buildTarjetaSinRespuesta(
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 24),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: borderColor),
      ),
      child: Column(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF1E293B) : const Color(0xFFFFFBEB),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.pending_actions_rounded,
              color: Color(0xFFF59E0B),
              size: 24,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'Pendiente de respuesta oficial',
            style: GoogleFonts.inter(
              fontSize: 14,
              fontWeight: FontWeight.w800,
              color: titleColor,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'La constructora aún no ha registrado una respuesta a su solicitud. Le notificaremos en cuanto el equipo de obra o atención emita su dictamen.',
            textAlign: TextAlign.center,
            style: GoogleFonts.inter(
              fontSize: 12,
              color: subColor,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }

  /// Representación visual para los estados oficiales
  Widget _buildBadgeEstado(String estado) {
    Color color;
    Color bg;
    IconData icon;
    String label;

    switch (estado.toUpperCase()) {
      case 'PENDIENTE':
        color = const Color(0xFFF59E0B);
        bg = const Color(0xFFF59E0B).withValues(alpha: 0.12);
        icon = Icons.hourglass_top_rounded;
        label = 'PENDIENTE';
        break;
      case 'EN_PROCESO':
        color = const Color(0xFF0284C7);
        bg = const Color(0xFF0284C7).withValues(alpha: 0.12);
        icon = Icons.sync_rounded;
        label = 'EN PROCESO';
        break;
      case 'ATENDIDA':
        color = const Color(0xFF10B981);
        bg = const Color(0xFF10B981).withValues(alpha: 0.12);
        icon = Icons.check_circle_rounded;
        label = 'ATENDIDA';
        break;
      case 'RECHAZADA':
        color = const Color(0xFFEF4444);
        bg = const Color(0xFFEF4444).withValues(alpha: 0.12);
        icon = Icons.cancel_rounded;
        label = 'RECHAZADA';
        break;
      default:
        color = const Color(0xFF64748B);
        bg = const Color(0xFF64748B).withValues(alpha: 0.12);
        icon = Icons.info_outline_rounded;
        label = estado;
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: GoogleFonts.inter(
              fontSize: 10,
              fontWeight: FontWeight.w800,
              color: color,
              letterSpacing: 0.3,
            ),
          ),
        ],
      ),
    );
  }
}
