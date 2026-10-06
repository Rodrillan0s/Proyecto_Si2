import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../theme/app_theme.dart';

/// Componentes visuales de CU19 (incidencias), con la misma estética que
/// ConstructionStatusBadge / tarjetas de OBRATEC.

String etiquetaEstadoIncidencia(String? estado) {
  switch ((estado ?? '').toUpperCase()) {
    case 'ABIERTA':
      return 'Abierta';
    case 'ASIGNADA':
      return 'Asignada';
    case 'EN_PROCESO':
      return 'En proceso';
    case 'PENDIENTE_VALIDACION':
      return 'Pendiente de validación';
    case 'RESUELTA':
      return 'Resuelta';
    case 'CERRADA':
      return 'Cerrada';
    default:
      return estado ?? '—';
  }
}

String etiquetaPrioridad(String? prioridad) {
  switch ((prioridad ?? '').toUpperCase()) {
    case 'BAJA':
      return 'Baja';
    case 'MEDIA':
      return 'Media';
    case 'ALTA':
      return 'Alta';
    case 'CRITICA':
      return 'Crítica';
    default:
      return prioridad ?? '—';
  }
}

Color colorEstadoIncidencia(String? estado) {
  switch ((estado ?? '').toUpperCase()) {
    case 'ABIERTA':
      return AppTheme.warning;
    case 'ASIGNADA':
      return const Color(0xFF6366F1);
    case 'EN_PROCESO':
      return AppTheme.info;
    case 'RESUELTA':
      return AppTheme.success;
    case 'CERRADA':
      return AppTheme.textSecondary;
    default:
      return AppTheme.textMuted;
  }
}

Color colorPrioridad(String? prioridad) {
  switch ((prioridad ?? '').toUpperCase()) {
    case 'BAJA':
      return AppTheme.success;
    case 'MEDIA':
      return AppTheme.info;
    case 'ALTA':
      return AppTheme.warning;
    case 'CRITICA':
      return AppTheme.error;
    default:
      return AppTheme.textMuted;
  }
}

/// Fecha ISO del backend (TIMESTAMPTZ / DATE) → "dd/MM/yyyy HH:mm" en hora local.
String formatearFechaHora(dynamic valor, {bool conHora = true, String vacio = '—'}) {
  if (valor == null) return vacio;
  final fecha = DateTime.tryParse(valor.toString());
  if (fecha == null) return valor.toString();
  // DateTime.parse devuelve UTC cuando el texto trae zona (TIMESTAMPTZ).
  final f = fecha.isUtc ? fecha.toLocal() : fecha;
  String dos(int n) => n.toString().padLeft(2, '0');
  final d = '${dos(f.day)}/${dos(f.month)}/${f.year}';
  return conHora ? '$d ${dos(f.hour)}:${dos(f.minute)}' : d;
}

class IncidenciaChip extends StatelessWidget {
  final String texto;
  final Color color;
  final bool compact;
  final IconData? icon;

  const IncidenciaChip({super.key, required this.texto, required this.color, this.compact = false, this.icon});

  factory IncidenciaChip.estado(String? estado, {bool compact = false}) =>
      IncidenciaChip(texto: etiquetaEstadoIncidencia(estado), color: colorEstadoIncidencia(estado), compact: compact);

  factory IncidenciaChip.prioridad(String? prioridad, {bool compact = false}) => IncidenciaChip(
        texto: etiquetaPrioridad(prioridad),
        color: colorPrioridad(prioridad),
        compact: compact,
        icon: Icons.flag_rounded,
      );

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      padding: EdgeInsets.symmetric(horizontal: compact ? 8 : 10, vertical: compact ? 3 : 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: isDark ? 0.16 : 0.10),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null)
            Icon(icon, size: compact ? 11 : 12, color: color)
          else
            Container(width: 5.5, height: 5.5, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
          const SizedBox(width: 5),
          Text(
            texto,
            style: GoogleFonts.inter(fontSize: compact ? 10 : 11, fontWeight: FontWeight.w700, color: color),
          ),
        ],
      ),
    );
  }
}

/// Tarjeta de sección con título (mismo estilo de tarjetas de HomeScreen).
class IncidenciaSeccion extends StatelessWidget {
  final String titulo;
  final IconData icon;
  final Widget child;
  final Widget? accion;

  const IncidenciaSeccion({super.key, required this.titulo, required this.icon, required this.child, this.accion});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark ? AppTheme.darkSurface : Colors.white,
        borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
        border: Border.all(color: isDark ? AppTheme.darkBorder : AppTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 18, color: AppTheme.primary),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  titulo.toUpperCase(),
                  style: GoogleFonts.inter(
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.6,
                    color: isDark ? AppTheme.darkTextSecondary : AppTheme.textSecondary,
                  ),
                ),
              ),
              if (accion != null) accion!,
            ],
          ),
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }
}

/// Par etiqueta/valor para fichas de detalle.
class IncidenciaDato extends StatelessWidget {
  final String etiqueta;
  final String valor;

  const IncidenciaDato({super.key, required this.etiqueta, required this.valor});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          etiqueta.toUpperCase(),
          style: GoogleFonts.inter(fontSize: 9.5, fontWeight: FontWeight.w800, letterSpacing: 0.5, color: AppTheme.textMuted),
        ),
        const SizedBox(height: 3),
        Text(
          valor,
          style: GoogleFonts.inter(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: isDark ? AppTheme.darkTextPrimary : AppTheme.textPrimary,
          ),
        ),
      ],
    );
  }
}

/// Estado vacío / error con acción de reintento.
class IncidenciaMensaje extends StatelessWidget {
  final IconData icon;
  final String titulo;
  final String? detalle;
  final String? textoAccion;
  final VoidCallback? onAccion;
  final bool esError;

  const IncidenciaMensaje({
    super.key,
    required this.icon,
    required this.titulo,
    this.detalle,
    this.textoAccion,
    this.onAccion,
    this.esError = false,
  });

  @override
  Widget build(BuildContext context) {
    final color = esError ? AppTheme.error : AppTheme.textMuted;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 40),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 48, color: color),
          const SizedBox(height: 12),
          Text(titulo, textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
          if (detalle != null) ...[
            const SizedBox(height: 6),
            Text(detalle!, textAlign: TextAlign.center, style: const TextStyle(fontSize: 12.5, color: AppTheme.textSecondary)),
          ],
          if (onAccion != null) ...[
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: onAccion,
              icon: const Icon(Icons.refresh_rounded, size: 18),
              label: Text(textoAccion ?? 'Reintentar'),
            ),
          ],
        ],
      ),
    );
  }
}

void mostrarMensajeIncidencia(BuildContext context, String mensaje, {bool error = false}) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(
      content: Text(mensaje),
      backgroundColor: error ? AppTheme.error : AppTheme.success,
    ));
}
