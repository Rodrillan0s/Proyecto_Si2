import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../services/crm_service.dart';
import '../theme/app_theme.dart';
import '../widgets/incidencia_widgets.dart';

/// CU30 / HU116 – Pantalla de Consulta y Recepción de Comunicaciones Oficiales
/// Exclusivamente para lectura/consulta de avisos de la constructora (sin respuestas ni chat).
class ClienteComunicacionesScreen extends StatefulWidget {
  const ClienteComunicacionesScreen({super.key});

  @override
  State<ClienteComunicacionesScreen> createState() => _ClienteComunicacionesScreenState();
}

class _ClienteComunicacionesScreenState extends State<ClienteComunicacionesScreen> {
  final CrmService _crmService = CrmService();

  bool _cargando = true;
  String? _error;
  List<Map<String, dynamic>> _comunicaciones = [];

  @override
  void initState() {
    super.initState();
    _cargarComunicaciones();
  }

  Future<void> _cargarComunicaciones() async {
    setState(() {
      _cargando = true;
      _error = null;
    });

    try {
      final lista = await _crmService.listarComunicacionesCliente();
      if (!mounted) return;
      setState(() {
        _comunicaciones = lista;
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

  int get _noLeidasCount =>
      _comunicaciones.where((c) => c['leido'] == false).length;

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
          'Comunicaciones Oficiales',
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
                'HU116',
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
          onRefresh: _cargarComunicaciones,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            children: [
              // 1. Cabecera resumen
              _buildCabeceraInformativa(isDark, cardBg, borderColor, titleColor, subColor),
              const SizedBox(height: 18),

              // 2. Encabezado de la lista con contador
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Bandeja de comunicados',
                    style: GoogleFonts.inter(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: titleColor,
                    ),
                  ),
                  if (!_cargando && _error == null)
                    Text(
                      '${_comunicaciones.length} ${_comunicaciones.length == 1 ? 'comunicado' : 'comunicados'}',
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
              else if (_comunicaciones.isEmpty)
                _buildEstadoVacio(isDark, cardBg, borderColor, titleColor, subColor)
              else
                ..._comunicaciones.map((comunicacion) => _buildTarjetaComunicacion(
                      comunicacion: comunicacion,
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

  /// Tarjeta descriptiva del buzón
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
              Icons.campaign_rounded,
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
                  'Comunicaciones de la Constructora',
                  style: GoogleFonts.inter(
                    fontSize: 14.5,
                    fontWeight: FontWeight.w800,
                    color: titleColor,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  'Canal oficial para recepción de circulares, avisos de avance e información de obras.',
                  style: GoogleFonts.inter(
                    fontSize: 11.5,
                    color: subColor,
                    height: 1.3,
                  ),
                ),
                if (!_cargando && _error == null && _noLeidasCount > 0) ...[
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2.5),
                    decoration: BoxDecoration(
                      color: AppTheme.primary.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      '$_noLeidasCount no ${_noLeidasCount == 1 ? 'leída' : 'leídas'}',
                      style: GoogleFonts.inter(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.primary,
                      ),
                    ),
                  ),
                ],
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
              'Consultando comunicaciones oficiales...',
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
            'Error al cargar comunicaciones',
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
            onPressed: _cargarComunicaciones,
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
            child: Icon(Icons.mark_email_read_outlined, size: 28, color: subColor),
          ),
          const SizedBox(height: 14),
          Text(
            'Sin comunicaciones registradas',
            style: GoogleFonts.inter(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: titleColor,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'La constructora aún no ha emitido comunicaciones directas para su cuenta.',
            textAlign: TextAlign.center,
            style: GoogleFonts.inter(fontSize: 12.5, color: subColor, height: 1.35),
          ),
        ],
      ),
    );
  }

  /// Tarjeta individual de una comunicación oficial
  Widget _buildTarjetaComunicacion({
    required Map<String, dynamic> comunicacion,
    required bool isDark,
    required Color cardBg,
    required Color borderColor,
    required Color titleColor,
    required Color subColor,
  }) {
    final String titulo = (comunicacion['titulo'] ?? 'Comunicado Oficial').toString();
    final String cuerpo = (comunicacion['cuerpo'] ?? comunicacion['mensaje'] ?? '').toString();
    final bool leido = comunicacion['leido'] == true;
    final String? fechaStr =
        comunicacion['fecha_creacion']?.toString() ?? comunicacion['created_at']?.toString();
    final String tipoReferencia =
        (comunicacion['tipo_referencia'] ?? comunicacion['tipo'] ?? 'COMUNICACION').toString();
    final int? nroEmergencia = int.tryParse(comunicacion['nro_emergencia']?.toString() ?? '');

    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: !leido ? AppTheme.primary.withValues(alpha: 0.5) : borderColor,
          width: !leido ? 1.3 : 1.0,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: isDark ? 0.2 : 0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Cabecera: Título y badge leído/no leído
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
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: !leido
                        ? AppTheme.primary.withValues(alpha: 0.15)
                        : (isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9)),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(
                      color: !leido
                          ? AppTheme.primary.withValues(alpha: 0.4)
                          : borderColor,
                    ),
                  ),
                  child: Text(
                    !leido ? 'NO LEÍDO' : 'LEÍDO',
                    style: GoogleFonts.inter(
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      color: !leido ? AppTheme.primary : subColor,
                      letterSpacing: 0.4,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),

            // Metadatos: Tipo y Fecha
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF1E293B) : const Color(0xFFF8FAFC),
                    borderRadius: BorderRadius.circular(5),
                    border: Border.all(color: borderColor),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.label_outline_rounded, size: 12, color: subColor),
                      const SizedBox(width: 4),
                      Text(
                        _formatearTipo(tipoReferencia),
                        style: GoogleFonts.inter(
                          fontSize: 10.5,
                          fontWeight: FontWeight.w600,
                          color: subColor,
                        ),
                      ),
                    ],
                  ),
                ),
                if (nroEmergencia != null) ...[
                  const SizedBox(width: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppTheme.error.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(5),
                    ),
                    child: Text(
                      'Incidencia #$nroEmergencia',
                      style: GoogleFonts.inter(
                        fontSize: 10.5,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.error,
                      ),
                    ),
                  ),
                ],
                const Spacer(),
                if (fechaStr != null) ...[
                  Icon(Icons.access_time_rounded, size: 13, color: subColor),
                  const SizedBox(width: 4),
                  Text(
                    formatearFechaHora(fechaStr),
                    style: GoogleFonts.inter(
                      fontSize: 11,
                      fontWeight: FontWeight.w500,
                      color: subColor,
                    ),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 12),
            const Divider(height: 1),
            const SizedBox(height: 12),

            // Contenido textual íntegro (Solo lectura)
            Text(
              cuerpo.isNotEmpty ? cuerpo : 'Sin contenido adicional.',
              style: GoogleFonts.inter(
                fontSize: 13,
                color: titleColor.withValues(alpha: isDark ? 0.9 : 0.85),
                height: 1.45,
                fontWeight: FontWeight.w400,
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatearTipo(String tipo) {
    switch (tipo.toUpperCase()) {
      case 'COMUNICACION_CLIENTE':
      case 'COMUNICACION':
        return 'Comunicado Oficial';
      case 'AVANCE':
        return 'Aviso de Avance';
      case 'GENERAL':
        return 'General';
      default:
        return tipo.replaceAll('_', ' ');
    }
  }
}
