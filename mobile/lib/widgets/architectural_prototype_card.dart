import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../theme/app_theme.dart';

/// Renderiza un prototipo arquitectónico conceptual (fachada + planta esquemática)
/// directamente desde los parámetros estructurados de `propuesta_proyecto`.
class ArchitecturalPrototypeCard extends StatelessWidget {
  final Map<String, dynamic> prototipo;

  const ArchitecturalPrototypeCard({super.key, required this.prototipo});

  @override
  Widget build(BuildContext context) {
    final titulo = prototipo['titulo']?.toString() ?? 'Prototipo conceptual';
    final estilo = prototipo['estilo']?.toString() ?? 'MINIMALISTA';
    final dorms = int.tryParse(prototipo['dormitorios']?.toString() ?? '2') ?? 2;
    final banos = int.tryParse(prototipo['banos']?.toString() ?? '2') ?? 2;
    final plantas = int.tryParse(prototipo['plantas']?.toString() ?? '1') ?? 1;

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppTheme.primary.withValues(alpha: 0.5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            titulo.toUpperCase(),
            style: GoogleFonts.inter(
              fontSize: 10.5,
              fontWeight: FontWeight.w800,
              color: AppTheme.primary,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            'Estilo $estilo · $dorms Dorm. · $banos Baño(s) · $plantas planta(s)',
            style: GoogleFonts.inter(fontSize: 10, color: const Color(0xFF94A3B8)),
          ),
          const SizedBox(height: 8),
          SizedBox(
            height: 112,
            width: double.infinity,
            child: CustomPaint(
              painter: _HousePrototypePainter(
                estilo: estilo,
                dormitorios: dorms,
                banos: banos,
                plantas: plantas,
              ),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            prototipo['nota']?.toString() ??
                'Prototipo visual conceptual preliminar; no equivale a plano aprobado.',
            style: GoogleFonts.inter(
              fontSize: 9.5,
              fontStyle: FontStyle.italic,
              color: const Color(0xFF94A3B8),
            ),
          ),
        ],
      ),
    );
  }
}

class _HousePrototypePainter extends CustomPainter {
  final String estilo;
  final int dormitorios;
  final int banos;
  final int plantas;

  _HousePrototypePainter({
    required this.estilo,
    required this.dormitorios,
    required this.banos,
    required this.plantas,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final halfW = size.width * 0.48;
    final h = size.height;

    // Fondo fachada
    final facadeRect = RRect.fromRectAndRadius(
      Rect.fromLTWH(0, 0, halfW, h),
      const Radius.circular(8),
    );
    canvas.drawRRect(facadeRect, Paint()..color = const Color(0xFF1E293B));

    final wallPaint = Paint()..color = const Color(0xFFF8FAFC);
    final roofColor = estilo == 'LUJO'
        ? const Color(0xFF020617)
        : (estilo == 'ESTANDAR' ? const Color(0xFFB45309) : const Color(0xFF334155));
    final roofPaint = Paint()..color = roofColor;
    final glassPaint = Paint()..color = const Color(0xFF7DD3FC);
    final doorPaint = Paint()..color = const Color(0xFFD97706);

    // Planta baja
    final baseLeft = halfW * 0.12;
    final baseW = halfW * 0.76;
    canvas.drawRect(Rect.fromLTWH(baseLeft, h * 0.50, baseW, h * 0.40), wallPaint);
    canvas.drawRect(Rect.fromLTWH(baseLeft + baseW * 0.10, h * 0.62, baseW * 0.16, h * 0.28), doorPaint);
    canvas.drawRect(Rect.fromLTWH(baseLeft + baseW * 0.36, h * 0.58, baseW * 0.22, h * 0.18), glassPaint);
    canvas.drawRect(Rect.fromLTWH(baseLeft + baseW * 0.66, h * 0.58, baseW * 0.22, h * 0.18), glassPaint);

    if (plantas >= 2) {
      canvas.drawRect(Rect.fromLTWH(baseLeft, h * 0.18, baseW, h * 0.32), wallPaint);
      canvas.drawRect(Rect.fromLTWH(baseLeft + baseW * 0.12, h * 0.25, baseW * 0.28, h * 0.16), glassPaint);
      canvas.drawRect(Rect.fromLTWH(baseLeft + baseW * 0.56, h * 0.25, baseW * 0.28, h * 0.16), glassPaint);
      canvas.drawRect(Rect.fromLTWH(baseLeft - 4, h * 0.12, baseW + 8, h * 0.06), roofPaint);
    } else {
      final roof = Path()
        ..moveTo(baseLeft - 6, h * 0.50)
        ..lineTo(halfW * 0.5, h * 0.18)
        ..lineTo(baseLeft + baseW + 6, h * 0.50)
        ..close();
      canvas.drawPath(roof, roofPaint);
    }

    // Planta esquemática derecha
    final planLeft = size.width * 0.52;
    final planW = size.width * 0.48;
    canvas.drawRRect(
      RRect.fromRectAndRadius(Rect.fromLTWH(planLeft, 0, planW, h), const Radius.circular(8)),
      Paint()..color = Colors.white,
    );

    const pad = 6.0;
    final innerW = planW - pad * 2;
    final dormCount = dormitorios.clamp(1, 4);
    final dormW = innerW / dormCount;
    final dormFill = Paint()..color = const Color(0xFFFEF3C7);
    final dormBorder = Paint()
      ..color = const Color(0xFFB45309)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    for (var i = 0; i < dormCount; i++) {
      final r = Rect.fromLTWH(planLeft + pad + i * dormW + 1, pad, dormW - 2, h * 0.42);
      canvas.drawRect(r, dormFill);
      canvas.drawRect(r, dormBorder);
    }

    // Sala-Comedor
    final salaRect = Rect.fromLTWH(planLeft + pad, h * 0.50, innerW * 0.62, h * 0.43);
    canvas.drawRect(salaRect, Paint()..color = const Color(0xFFE0F2FE));
    canvas.drawRect(
      salaRect,
      Paint()
        ..color = const Color(0xFF0284C7)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1,
    );

    // Cocina + Baños
    final cocRect = Rect.fromLTWH(planLeft + pad + innerW * 0.65, h * 0.50, innerW * 0.35, h * 0.20);
    canvas.drawRect(cocRect, Paint()..color = const Color(0xFFDCFCE7));
    final banoRect = Rect.fromLTWH(planLeft + pad + innerW * 0.65, h * 0.73, innerW * 0.35, h * 0.20);
    canvas.drawRect(banoRect, Paint()..color = const Color(0xFFE2E8F0));
  }

  @override
  bool shouldRepaint(covariant _HousePrototypePainter oldDelegate) =>
      oldDelegate.estilo != estilo ||
      oldDelegate.dormitorios != dormitorios ||
      oldDelegate.banos != banos ||
      oldDelegate.plantas != plantas;
}
