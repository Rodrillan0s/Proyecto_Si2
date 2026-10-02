import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../theme/app_theme.dart';

/// ── BADGE DE ESTADO MODERNO Y ELEGANTE ─────────────────────────────────────
class ConstructionStatusBadge extends StatelessWidget {
  final String status;
  final bool compact;

  const ConstructionStatusBadge({
    super.key,
    required this.status,
    this.compact = false,
  });

  Color _getTextColor(String s, bool isDark) {
    switch (s.toUpperCase()) {
      case 'ACTIVO':
      case 'EN EJECUCION':
        return isDark ? const Color(0xFF34D399) : const Color(0xFF059669);
      case 'PLANIFICACION':
      case 'DISENO':
        return isDark ? const Color(0xFF38BDF8) : const Color(0xFF0284C7);
      case 'PAUSADO':
        return isDark ? const Color(0xFFFBBF24) : const Color(0xFFD97706);
      case 'FINALIZADO':
      case 'ENTREGADO':
        return isDark ? const Color(0xFF818CF8) : const Color(0xFF4F46E5);
      case 'CANCELADO':
        return isDark ? const Color(0xFFF87171) : const Color(0xFFDC2626);
      default:
        return isDark ? const Color(0xFF94A3B8) : const Color(0xFF475569);
    }
  }

  Color _getBgColor(String s, bool isDark) {
    switch (s.toUpperCase()) {
      case 'ACTIVO':
      case 'EN EJECUCION':
        return isDark ? const Color(0x2210B981) : const Color(0xFFECFDF5);
      case 'PLANIFICACION':
      case 'DISENO':
        return isDark ? const Color(0x220284C7) : const Color(0xFFF0F9FF);
      case 'PAUSADO':
        return isDark ? const Color(0x22F59E0B) : const Color(0xFFFFFBEB);
      case 'FINALIZADO':
      case 'ENTREGADO':
        return isDark ? const Color(0x226366F1) : const Color(0xFFEEF2FF);
      case 'CANCELADO':
        return isDark ? const Color(0x22EF4444) : const Color(0xFFFEF2F2);
      default:
        return isDark ? const Color(0x2264748B) : const Color(0xFFF1F5F9);
    }
  }

  Color _getBorderColor(String s, bool isDark) {
    switch (s.toUpperCase()) {
      case 'ACTIVO':
      case 'EN EJECUCION':
        return isDark ? const Color(0x4410B981) : const Color(0xFFA7F3D0);
      case 'PLANIFICACION':
      case 'DISENO':
        return isDark ? const Color(0x440284C7) : const Color(0xFFBAE6FD);
      case 'PAUSADO':
        return isDark ? const Color(0x44F59E0B) : const Color(0xFFFDE68A);
      case 'FINALIZADO':
      case 'ENTREGADO':
        return isDark ? const Color(0x446366F1) : const Color(0xFFC7D2FE);
      case 'CANCELADO':
        return isDark ? const Color(0x44EF4444) : const Color(0xFFFECACA);
      default:
        return isDark ? const Color(0x4464748B) : const Color(0xFFE2E8F0);
    }
  }

  String _getLabel(String s) {
    switch (s.toUpperCase()) {
      case 'ACTIVO':
        return 'En Ejecución';
      case 'PLANIFICACION':
        return 'Planificación';
      case 'PAUSADO':
        return 'Pausado';
      case 'FINALIZADO':
        return 'Concluido';
      case 'CANCELADO':
        return 'Cancelado';
      default:
        return s;
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = _getTextColor(status, isDark);
    final bgColor = _getBgColor(status, isDark);
    final borderColor = _getBorderColor(status, isDark);
    final label = _getLabel(status);

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: compact ? 8 : 10,
        vertical: compact ? 3 : 4,
      ),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: borderColor, width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 5.5,
            height: 5.5,
            decoration: BoxDecoration(
              color: textColor,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 5),
          Text(
            label,
            style: GoogleFonts.inter(
              fontSize: compact ? 10 : 11,
              fontWeight: FontWeight.w700,
              color: textColor,
              letterSpacing: 0.1,
            ),
          ),
        ],
      ),
    );
  }
}

/// ── TARJETA DE PROYECTO ESTILO SKYSCANNER / AIRBNB HORIZONTAL ──────────────
class CleanProjectCard extends StatelessWidget {
  final int idObra;
  final String codigo;
  final String nombre;
  final String tipoNombre;
  final String estado;
  final String ubicacion;
  final String fechaInicio;
  final VoidCallback onTap;

  const CleanProjectCard({
    super.key,
    required this.idObra,
    required this.codigo,
    required this.nombre,
    required this.tipoNombre,
    required this.estado,
    required this.ubicacion,
    required this.fechaInicio,
    required this.onTap,
  });

  Color _getGradientStart(String s, bool isDark) {
    switch (s.toUpperCase()) {
      case 'ACTIVO':
      case 'EN EJECUCION':
        return isDark ? const Color(0xFFC2410C) : const Color(0xFFEA580C);
      case 'PLANIFICACION':
      case 'DISENO':
        return isDark ? const Color(0xFF0369A1) : const Color(0xFF0284C7);
      case 'PAUSADO':
        return isDark ? const Color(0xFFB45309) : const Color(0xFFD97706);
      case 'FINALIZADO':
        return isDark ? const Color(0xFF4338CA) : const Color(0xFF6366F1);
      default:
        return isDark ? const Color(0xFF334155) : const Color(0xFF475569);
    }
  }

  Color _getGradientEnd(String s, bool isDark) {
    switch (s.toUpperCase()) {
      case 'ACTIVO':
      case 'EN EJECUCION':
        return isDark ? const Color(0xFF7C2D12) : const Color(0xFF9A3412);
      case 'PLANIFICACION':
      case 'DISENO':
        return isDark ? const Color(0xFF0C4A6E) : const Color(0xFF075985);
      case 'PAUSADO':
        return isDark ? const Color(0xFF78350F) : const Color(0xFF92400E);
      case 'FINALIZADO':
        return isDark ? const Color(0xFF312E81) : const Color(0xFF4338CA);
      default:
        return isDark ? const Color(0xFF0F172A) : const Color(0xFF1E293B);
    }
  }

  IconData _getIconForType(String tipo) {
    switch (tipo.toUpperCase()) {
      case 'EDIFICACIÓN':
      case 'EDIFICACION':
      case 'TORRE':
        return Icons.apartment_rounded;
      case 'VIVIENDA':
      case 'CONDOMINIO':
        return Icons.home_work_rounded;
      case 'COMERCIAL':
        return Icons.storefront_rounded;
      case 'INFRAESTRUCTURA':
        return Icons.engineering_rounded;
      default:
        return Icons.domain_rounded;
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
    final subColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);
    final codeTagBg = isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9);
    final codeTagText = isDark ? const Color(0xFFCBD5E1) : const Color(0xFF475569);

    final gradStart = _getGradientStart(estado, isDark);
    final gradEnd = _getGradientEnd(estado, isDark);
    final iconData = _getIconForType(tipoNombre);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: borderColor, width: 1),
        boxShadow: [
          BoxShadow(
            color: isDark ? Colors.black.withValues(alpha: 0.3) : const Color(0x06000000),
            blurRadius: 10,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // 1. Bloque Visual Izquierdo (Estilo Skyscanner Thumbnail)
              Container(
                width: 82,
                height: 96,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [gradStart, gradEnd],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: const BorderRadius.horizontal(left: Radius.circular(13)),
                ),
                child: Center(
                  child: Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.15),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(iconData, color: Colors.white, size: 26),
                  ),
                ),
              ),

              // 2. Bloque Central y Derecho de Contenido
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // Fila Superior: Código & Estado
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: codeTagBg,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              codigo,
                              style: GoogleFonts.jetBrainsMono(
                                fontSize: 10.5,
                                fontWeight: FontWeight.w700,
                                color: codeTagText,
                              ),
                            ),
                          ),
                          ConstructionStatusBadge(status: estado, compact: true),
                        ],
                      ),
                      const SizedBox(height: 6),

                      // Título del Proyecto
                      Text(
                        nombre,
                        style: GoogleFonts.inter(
                          fontSize: 14.5,
                          fontWeight: FontWeight.w800,
                          color: titleColor,
                          letterSpacing: -0.2,
                          height: 1.25,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 4),

                      // Subtítulo: Tipo y Ubicación
                      Row(
                        children: [
                          Text(
                            tipoNombre,
                            style: GoogleFonts.inter(
                              fontSize: 11.5,
                              color: isDark ? const Color(0xFFFB923C) : AppTheme.primary,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          if (ubicacion.isNotEmpty) ...[
                            const SizedBox(width: 4),
                            Text('·', style: TextStyle(color: subColor, fontWeight: FontWeight.bold)),
                            const SizedBox(width: 4),
                            Expanded(
                              child: Text(
                                ubicacion,
                                style: GoogleFonts.inter(
                                  fontSize: 11.5,
                                  color: subColor,
                                  fontWeight: FontWeight.w500,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ],
                      ),
                    ],
                  ),
                ),
              ),

              // 3. Chevron Indicador
              Padding(
                padding: const EdgeInsets.only(right: 12.0),
                child: Icon(
                  Icons.chevron_right_rounded,
                  color: isDark ? const Color(0xFF64748B) : const Color(0xFF94A3B8),
                  size: 22,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

typedef BuildertrendProjectCard = CleanProjectCard;
