import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../theme/app_theme.dart';

class _ChartDatum {
  final String label;
  final double value;
  final Color color;
  final double ratio;

  const _ChartDatum({
    required this.label,
    required this.value,
    required this.color,
    required this.ratio,
  });
}

class ChartSpecCard extends StatelessWidget {
  final Map<String, dynamic>? spec;
  final List<dynamic> rows;
  final Map<String, dynamic>? resumen;
  final bool compact;

  const ChartSpecCard({
    super.key,
    required this.spec,
    this.rows = const [],
    this.resumen,
    this.compact = false,
  });

  static const List<Color> _palette = [
    Color(0xFFD97706),
    Color(0xFF2563EB),
    Color(0xFF059669),
    Color(0xFF7C3AED),
    Color(0xFFE11D48),
    Color(0xFF0891B2),
    Color(0xFFEA580C),
    Color(0xFF4F46E5),
  ];

  String get _tipo => (spec?['tipo'] ?? 'none').toString().toLowerCase();

  String? _resolveLabelKey() {
    final ejeX = spec?['eje_x']?.toString();
    if (ejeX != null && ejeX.isNotEmpty) return ejeX;
    if (rows.isNotEmpty && rows.first is Map) {
      final map = rows.first as Map;
      if (map.isNotEmpty) return map.keys.first.toString();
    }
    return null;
  }

  String? _resolveMetricKey(String? labelKey) {
    final series = spec?['series'];
    if (series is List && series.isNotEmpty && series.first is Map) {
      final first = series.first as Map;
      final c = first['campo']?.toString() ?? first['field']?.toString();
      if (c != null && c.isNotEmpty) return c;
    }
    if (rows.isNotEmpty && rows.first is Map) {
      final map = rows.first as Map;
      for (final entry in map.entries) {
        if (entry.key.toString() == labelKey) continue;
        final v = entry.value;
        if (v is num) return entry.key.toString();
        if (v is String && double.tryParse(v.trim()) != null) {
          return entry.key.toString();
        }
      }
    }
    return null;
  }

  List<_ChartDatum> _extractPoints() {
    final labelKey = _resolveLabelKey();
    final metricKey = _resolveMetricKey(labelKey);
    if (labelKey == null || metricKey == null || rows.isEmpty) return [];

    final raw = <({String label, double value, Color color})>[];
    final limit = math.min(rows.length, 10);
    for (var i = 0; i < limit; i++) {
      final row = rows[i];
      if (row is! Map) continue;
      final lbl = (row[labelKey] ?? '#${i + 1}').toString();
      final valRaw = row[metricKey];
      final val = valRaw is num
          ? valRaw.toDouble()
          : (double.tryParse(valRaw?.toString() ?? '') ?? 0.0);
      raw.add((label: lbl, value: val, color: _palette[i % _palette.length]));
    }
    if (raw.isEmpty) return [];
    final maxAbs = raw.fold<double>(1.0, (m, e) => math.max(m, e.value.abs()));
    return raw
        .map(
          (e) => _ChartDatum(
            label: e.label,
            value: e.value,
            color: e.color,
            ratio: (e.value.abs() / maxAbs).clamp(0.02, 1.0),
          ),
        )
        .toList();
  }

  String _fmt(double v) {
    if (v == v.roundToDouble()) return v.toInt().toString();
    return v.toStringAsFixed(2);
  }

  @override
  Widget build(BuildContext context) {
    if (spec == null || _tipo == 'none') return const SizedBox.shrink();

    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF111827) : Colors.white;
    final borderColor = isDark ? const Color(0xFF1F2937) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? Colors.white : const Color(0xFF0F172A);
    final subColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);

    final points = _extractPoints();
    final kpiMap = (resumen != null && resumen!.isNotEmpty)
        ? resumen!
        : (rows.isNotEmpty && rows.first is Map
            ? Map<String, dynamic>.from(rows.first as Map)
            : <String, dynamic>{});

    if (_tipo == 'kpi' && kpiMap.isEmpty) return const SizedBox.shrink();
    if (_tipo == 'line' && points.length < 2) return const SizedBox.shrink();
    if ((_tipo == 'bar' || _tipo == 'stacked_bar' || _tipo == 'pie') && points.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
      width: double.infinity,
      margin: EdgeInsets.symmetric(vertical: compact ? 6 : 10),
      padding: EdgeInsets.all(compact ? 10 : 14),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'VISUALIZACIÓN',
            style: GoogleFonts.inter(
              fontSize: 9.5,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.7,
              color: AppTheme.primary,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            spec?['titulo']?.toString() ?? 'Resumen gráfico',
            style: GoogleFonts.inter(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: titleColor,
            ),
          ),
          const SizedBox(height: 10),
          if (_tipo == 'kpi')
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: kpiMap.entries.take(6).map((e) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: borderColor),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        e.key.replaceAll('_', ' ').toUpperCase(),
                        style: GoogleFonts.inter(fontSize: 9.5, color: subColor, fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '${e.value ?? "—"}',
                        style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w800, color: titleColor),
                      ),
                    ],
                  ),
                );
              }).toList(),
            )
          else if (_tipo == 'bar' || _tipo == 'stacked_bar')
            Column(
              children: points.map((p) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Text(
                              p.label,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: GoogleFonts.inter(fontSize: 11.5, color: titleColor),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            _fmt(p.value),
                            style: GoogleFonts.inter(
                              fontSize: 11.5,
                              fontWeight: FontWeight.w700,
                              color: titleColor,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(999),
                        child: LinearProgressIndicator(
                          value: p.ratio,
                          minHeight: 7,
                          backgroundColor: borderColor,
                          valueColor: AlwaysStoppedAnimation<Color>(p.color),
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            )
          else if (_tipo == 'line')
            Column(
              children: [
                SizedBox(
                  height: 110,
                  width: double.infinity,
                  child: CustomPaint(
                    painter: _LineChartPainter(points: points, gridColor: borderColor),
                  ),
                ),
                const SizedBox(height: 4),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(points.first.label, style: GoogleFonts.inter(fontSize: 10, color: subColor)),
                    Text(points.last.label, style: GoogleFonts.inter(fontSize: 10, color: subColor)),
                  ],
                ),
              ],
            )
          else if (_tipo == 'pie')
            Row(
              children: [
                SizedBox(
                  width: 92,
                  height: 92,
                  child: CustomPaint(painter: _DonutChartPainter(points: points)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: _buildPieLegend(points, titleColor, subColor),
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }

  List<Widget> _buildPieLegend(List<_ChartDatum> points, Color titleColor, Color subColor) {
    final positive = points.where((p) => p.value > 0).toList();
    final total = positive.fold<double>(0.0, (s, p) => s + p.value);
    if (total <= 0) return [];
    return positive.take(6).map((p) {
      final pct = (p.value / total * 100).toStringAsFixed(1);
      return Padding(
        padding: const EdgeInsets.only(bottom: 4),
        child: Row(
          children: [
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(color: p.color, shape: BoxShape.circle),
            ),
            const SizedBox(width: 6),
            Expanded(
              child: Text(
                p.label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: GoogleFonts.inter(fontSize: 11, color: titleColor),
              ),
            ),
            Text(
              '$pct%',
              style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w700, color: subColor),
            ),
          ],
        ),
      );
    }).toList();
  }
}

class _LineChartPainter extends CustomPainter {
  final List<_ChartDatum> points;
  final Color gridColor;

  _LineChartPainter({required this.points, required this.gridColor});

  @override
  void paint(Canvas canvas, Size size) {
    if (points.length < 2) return;
    final gridPaint = Paint()
      ..color = gridColor
      ..strokeWidth = 1;
    for (final y in [12.0, size.height / 2, size.height - 12.0]) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), gridPaint);
    }

    final minVal = points.map((p) => p.value).reduce(math.min);
    final maxVal = points.map((p) => p.value).reduce(math.max);
    final span = (maxVal - minVal) == 0 ? 1.0 : (maxVal - minVal);
    final stepX = size.width / (points.length - 1);

    final path = Path();
    final linePaint = Paint()
      ..color = const Color(0xFFD97706)
      ..strokeWidth = 2.4
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    final dotPaint = Paint()..color = const Color(0xFFD97706);

    for (var i = 0; i < points.length; i++) {
      final x = i * stepX;
      final y = (size.height - 14) - ((points[i].value - minVal) / span) * (size.height - 28);
      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
      canvas.drawCircle(Offset(x, y), 3.2, dotPaint);
    }
    canvas.drawPath(path, linePaint);
  }

  @override
  bool shouldRepaint(covariant _LineChartPainter oldDelegate) => oldDelegate.points != points;
}

class _DonutChartPainter extends CustomPainter {
  final List<_ChartDatum> points;

  _DonutChartPainter({required this.points});

  @override
  void paint(Canvas canvas, Size size) {
    final positive = points.where((p) => p.value > 0).toList();
    final total = positive.fold<double>(0.0, (s, p) => s + p.value);
    if (total <= 0) return;

    final rect = Rect.fromLTWH(10, 10, size.width - 20, size.height - 20);
    var startAngle = -math.pi / 2;
    for (final p in positive) {
      final sweep = (p.value / total) * 2 * math.pi;
      final paint = Paint()
        ..color = p.color
        ..style = PaintingStyle.stroke
        ..strokeWidth = 14;
      canvas.drawArc(rect, startAngle, sweep, false, paint);
      startAngle += sweep;
    }
  }

  @override
  bool shouldRepaint(covariant _DonutChartPainter oldDelegate) => oldDelegate.points != points;
}
