import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../services/crm_service.dart';
import '../theme/app_theme.dart';
import '../widgets/incidencia_widgets.dart';
import 'cliente_solicitud_detalle_screen.dart';

/// CU30 / HU117 – Listado de Solicitudes Registradas para CLIENTE
/// Permite consultar y dar seguimiento a las solicitudes y respuestas oficiales de la constructora.
class ClienteSolicitudesScreen extends StatefulWidget {
  const ClienteSolicitudesScreen({super.key});

  @override
  State<ClienteSolicitudesScreen> createState() => _ClienteSolicitudesScreenState();
}

class _ClienteSolicitudesScreenState extends State<ClienteSolicitudesScreen> {
  final CrmService _crmService = CrmService();

  bool _cargando = true;
  String? _error;
  List<Map<String, dynamic>> _solicitudes = [];

  @override
  void initState() {
    super.initState();
    _cargarSolicitudes();
  }

  Future<void> _cargarSolicitudes() async {
    setState(() {
      _cargando = true;
      _error = null;
    });

    try {
      final lista = await _crmService.listarSolicitudesCliente();
      if (!mounted) return;
      setState(() {
        _solicitudes = lista;
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
          'Mis Solicitudes',
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
          onRefresh: _cargarSolicitudes,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            children: [
              // 1. Cabecera informativa
              _buildCabeceraInformativa(isDark, cardBg, borderColor, titleColor, subColor),
              const SizedBox(height: 18),

              // 2. Encabezado de la lista con contador
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Historial de solicitudes',
                    style: GoogleFonts.inter(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: titleColor,
                    ),
                  ),
                  if (!_cargando && _error == null)
                    Text(
                      '${_solicitudes.length} ${_solicitudes.length == 1 ? 'solicitud' : 'solicitudes'}',
                      style: GoogleFonts.inter(
                        fontSize: 12.5,
                        fontWeight: FontWeight.w600,
                        color: subColor,
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 12),

              // 3. Estados condicionales
              if (_cargando)
                _buildEstadoCarga(isDark, cardBg, borderColor, subColor)
              else if (_error != null)
                _buildEstadoError(isDark, cardBg, borderColor, titleColor, subColor)
              else if (_solicitudes.isEmpty)
                _buildEstadoVacio(isDark, cardBg, borderColor, titleColor, subColor)
              else
                ..._solicitudes.map((solicitud) => _buildTarjetaSolicitud(
                      solicitud: solicitud,
                      isDark: isDark,
                      cardBg: cardBg,
                      borderColor: borderColor,
                      titleColor: titleColor,
                      subColor: subColor,
                    )),
            ],
          ),
        ),
      ),
    );
  }

  /// Tarjeta informativa de la pantalla
  Widget _buildCabeceraInformativa(
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
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: AppTheme.primary.withValues(alpha: isDark ? 0.2 : 0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: AppTheme.primary.withValues(alpha: 0.3),
              ),
            ),
            child: const Icon(
              Icons.assignment_outlined,
              color: AppTheme.primary,
              size: 24,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Seguimiento de Solicitudes y PQRS',
                  style: GoogleFonts.inter(
                    fontSize: 14.5,
                    fontWeight: FontWeight.w800,
                    color: titleColor,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  'Consulte el estado de atención y las respuestas oficiales emitidas por la constructora.',
                  style: GoogleFonts.inter(
                    fontSize: 11.5,
                    color: subColor,
                    height: 1.3,
                  ),
                ),
              ],
            ),
          ),
        ],
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
              'Consultando solicitudes...',
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
            'Error al cargar solicitudes',
            style: GoogleFonts.inter(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: titleColor,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            _error ?? 'No se pudo conectar con el servidor.',
            textAlign: TextAlign.center,
            style: GoogleFonts.inter(fontSize: 12.5, color: subColor),
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primary,
              minimumSize: const Size(140, 40),
            ),
            onPressed: _cargarSolicitudes,
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
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 40),
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
            child: Icon(Icons.inventory_2_outlined, size: 28, color: subColor),
          ),
          const SizedBox(height: 14),
          Text(
            'Sin solicitudes registradas',
            style: GoogleFonts.inter(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: titleColor,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'No tiene solicitudes o requerimientos registrados en el sistema.',
            textAlign: TextAlign.center,
            style: GoogleFonts.inter(fontSize: 12.5, color: subColor, height: 1.35),
          ),
        ],
      ),
    );
  }

  /// Tarjeta de solicitud individual en el listado
  Widget _buildTarjetaSolicitud({
    required Map<String, dynamic> solicitud,
    required bool isDark,
    required Color cardBg,
    required Color borderColor,
    required Color titleColor,
    required Color subColor,
  }) {
    final String titulo = (solicitud['titulo'] ?? solicitud['asunto'] ?? 'Solicitud').toString();
    final String estado = (solicitud['estado'] ?? 'PENDIENTE').toString();
    final String nombreObra = (solicitud['nombre_obra'] ?? 'Obra').toString();
    final String? codigoUnidad = solicitud['codigo_unidad']?.toString();
    final String? fechaCreacion = solicitud['fecha_creacion']?.toString();
    final bool tieneRespuesta =
        solicitud['respuesta'] != null && solicitud['respuesta'].toString().trim().isNotEmpty;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: borderColor),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: isDark ? 0.2 : 0.04),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(14),
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => ClienteSolicitudDetalleScreen(solicitud: solicitud),
            ),
          ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Fila 1: Título y Badge de Estado Oficial
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Text(
                        titulo,
                        style: GoogleFonts.inter(
                          fontSize: 15,
                          fontWeight: FontWeight.w800,
                          color: titleColor,
                          height: 1.25,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    _buildBadgeEstado(estado),
                  ],
                ),
                const SizedBox(height: 10),

                // Fila 2: Obra y Unidad
                Row(
                  children: [
                    Icon(Icons.domain_rounded, size: 14, color: subColor),
                    const SizedBox(width: 5),
                    Flexible(
                      child: Text(
                        nombreObra,
                        style: GoogleFonts.inter(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: subColor,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    if (codigoUnidad != null) ...[
                      const SizedBox(width: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1.5),
                        decoration: BoxDecoration(
                          color: isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9),
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(color: borderColor),
                        ),
                        child: Text(
                          codigoUnidad,
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
                const SizedBox(height: 10),
                const Divider(height: 1),
                const SizedBox(height: 10),

                // Fila 3: Fecha e indicador de respuesta
                Row(
                  children: [
                    if (fechaCreacion != null) ...[
                      Icon(Icons.calendar_today_rounded, size: 12, color: subColor),
                      const SizedBox(width: 4),
                      Text(
                        formatearFechaHora(fechaCreacion),
                        style: GoogleFonts.inter(
                          fontSize: 11,
                          color: subColor,
                        ),
                      ),
                    ],
                    const Spacer(),
                    if (tieneRespuesta)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                        decoration: BoxDecoration(
                          color: const Color(0xFF10B981).withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(5),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(Icons.check_circle_rounded, size: 11, color: Color(0xFF10B981)),
                            const SizedBox(width: 4),
                            Text(
                              'Con respuesta',
                              style: GoogleFonts.inter(
                                fontSize: 10,
                                fontWeight: FontWeight.w700,
                                color: const Color(0xFF10B981),
                              ),
                            ),
                          ],
                        ),
                      )
                    else
                      Text(
                        'En espera',
                        style: GoogleFonts.inter(
                          fontSize: 10.5,
                          fontWeight: FontWeight.w500,
                          color: subColor,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    const SizedBox(width: 6),
                    Icon(Icons.arrow_forward_ios_rounded, size: 12, color: subColor),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  /// Badge para los 4 estados oficiales: PENDIENTE, EN_PROCESO, ATENDIDA, RECHAZADA
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
      padding: const EdgeInsets.symmetric(horizontal: 7.5, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 11, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: GoogleFonts.inter(
              fontSize: 9.5,
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
