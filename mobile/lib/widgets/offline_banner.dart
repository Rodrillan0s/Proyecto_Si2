import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../screens/sync_status_screen.dart';
import '../services/offline_sync_service.dart';

/// Banner reutilizable CU41 (HU90 / HU94):
/// - Indica claramente cuando se muestra una copia local y su fecha de última actualización.
/// - Advierte que la información puede estar desactualizada si no hay conexión.
/// - Permite abrir el estado de sincronización cuando hay operaciones pendientes o con error.
class OfflineBanner extends StatelessWidget {
  final bool esCopiaLocal;
  final DateTime? ultimaActualizacion;

  const OfflineBanner({
    super.key,
    this.esCopiaLocal = false,
    this.ultimaActualizacion,
  });

  String _formatFecha(DateTime? dt) {
    if (dt == null) return 'Sin registro previo';
    final local = dt.toLocal();
    final d = local.day.toString().padLeft(2, '0');
    final m = local.month.toString().padLeft(2, '0');
    final h = local.hour.toString().padLeft(2, '0');
    final min = local.minute.toString().padLeft(2, '0');
    return '$d/$m/${local.year} $h:$min';
  }

  OfflineSyncService _resolverSync(BuildContext context) {
    try {
      return context.watch<OfflineSyncService>();
    } catch (_) {
      return OfflineSyncService.instance;
    }
  }

  @override
  Widget build(BuildContext context) {
    final sync = _resolverSync(context);
    final mostrarOffline = !sync.isOnline || esCopiaLocal;
    final pendientes = sync.pendientesCount;
    final errores = sync.erroresCount;

    if (!mostrarOffline && pendientes == 0 && errores == 0) {
      return const SizedBox.shrink();
    }

    final ts = ultimaActualizacion ?? sync.ultimaActualizacionCache;
    final bgColor = mostrarOffline
        ? const Color(0xFFFFFBEB)
        : (errores > 0 ? const Color(0xFFFEF2F2) : const Color(0xFFEFF6FF));
    final borderColor = mostrarOffline
        ? const Color(0xFFF59E0B)
        : (errores > 0 ? const Color(0xFFEF4444) : const Color(0xFF3B82F6));
    final textColor = mostrarOffline
        ? const Color(0xFF92400E)
        : (errores > 0 ? const Color(0xFF991B1B) : const Color(0xFF1E40AF));

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.fromLTRB(12, 8, 12, 4),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: borderColor.withValues(alpha: 0.6)),
      ),
      child: Row(
        children: [
          Icon(
            mostrarOffline ? Icons.cloud_off_rounded : Icons.sync_rounded,
            size: 20,
            color: textColor,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  mostrarOffline
                      ? 'Modo sin conexión · Copia local (puede estar desactualizada)'
                      : 'Sincronización: $pendientes pendientes · $errores con error',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: textColor,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  'Última actualización: ${_formatFecha(ts)}${pendientes > 0 ? ' · $pendientes en cola' : ''}',
                  style: TextStyle(fontSize: 11, color: textColor.withValues(alpha: 0.9)),
                ),
              ],
            ),
          ),
          TextButton(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const SyncStatusScreen()),
              );
            },
            style: TextButton.styleFrom(
              foregroundColor: textColor,
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              minimumSize: Size.zero,
            ),
            child: const Text('Ver estado', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
          ),
        ],
      ),
    );
  }
}
