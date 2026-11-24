import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/offline_db_service.dart';
import '../services/offline_sync_service.dart';

/// CU41 – HU94: Consultar estado de sincronización.
/// Diferencia registros PENDIENTE, SINCRONIZADO y ERROR con detalle e intento manual.
class SyncStatusScreen extends StatefulWidget {
  const SyncStatusScreen({super.key});

  @override
  State<SyncStatusScreen> createState() => _SyncStatusScreenState();
}

class _SyncStatusScreenState extends State<SyncStatusScreen> {
  String _filtro = 'TODOS';

  @override
  Widget build(BuildContext context) {
    final sync = context.watch<OfflineSyncService>();
    final items = _filtro == 'TODOS'
        ? sync.items
        : sync.items.where((i) => i.estado == _filtro).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Estado de sincronización'),
        actions: [
          IconButton(
            tooltip: 'Sincronizar ahora',
            onPressed: sync.sincronizando ? null : () => sync.sincronizarPendientes(),
            icon: sync.sincronizando
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.sync_rounded),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                _metricCard('Pendientes', sync.pendientesCount, const Color(0xFFD97706)),
                const SizedBox(width: 8),
                _metricCard('Sincronizados', sync.sincronizadosCount, const Color(0xFF059669)),
                const SizedBox(width: 8),
                _metricCard('Con error', sync.erroresCount, const Color(0xFFDC2626)),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Wrap(
              spacing: 8,
              children: [
                for (final f in const ['TODOS', 'PENDIENTE', 'SINCRONIZADO', 'ERROR'])
                  ChoiceChip(
                    label: Text(f),
                    selected: _filtro == f,
                    onSelected: (_) => setState(() => _filtro = f),
                  ),
              ],
            ),
          ),
          if (sync.erroresCount > 0)
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
              child: SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: sync.sincronizando ? null : () => sync.reintentarErrores(),
                  icon: const Icon(Icons.refresh_rounded, size: 18),
                  label: const Text('Reintentar registros con error'),
                ),
              ),
            ),
          const SizedBox(height: 8),
          Expanded(
            child: items.isEmpty
                ? const Center(
                    child: Text(
                      'No hay registros en esta vista de sincronización.',
                      style: TextStyle(color: Colors.grey),
                    ),
                  )
                : ListView.separated(
                    padding: const EdgeInsets.all(12),
                    itemCount: items.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 8),
                    itemBuilder: (_, idx) => _buildItemTile(items[idx]),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _metricCard(String label, int value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: color.withValues(alpha: 0.35)),
          color: color.withValues(alpha: 0.08),
        ),
        child: Column(
          children: [
            Text('$value', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: color)),
            const SizedBox(height: 2),
            Text(label, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: color)),
          ],
        ),
      ),
    );
  }

  Widget _buildItemTile(OfflineQueueItem item) {
    final color = item.estado == 'SINCRONIZADO'
        ? const Color(0xFF059669)
        : (item.estado == 'ERROR' ? const Color(0xFFDC2626) : const Color(0xFFD97706));
    final titulo = item.tipoOperacion == 'AVANCE_OBRA'
        ? 'Avance de obra (${item.payload['porcentaje_avance']}%) · Unidad #${item.payload['id_unidad']}'
        : 'Incidencia: ${item.payload['titulo'] ?? 'Sin título'}';

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(titulo, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(item.estado, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: color)),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text('Obra #${item.idObra} · Ocurrencia local: ${item.fechaOcurrenciaLocal}',
                style: const TextStyle(fontSize: 11, color: Colors.black54)),
            if (item.fechaSincronizacion != null)
              Text('Sincronizado: ${item.fechaSincronizacion} (ID remoto #${item.idRecursoRemoto ?? '-'})',
                  style: const TextStyle(fontSize: 11, color: Color(0xFF059669))),
            if (item.ultimoError != null && item.ultimoError!.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text('Detalle: ${item.ultimoError}',
                    style: const TextStyle(fontSize: 11, color: Color(0xFFDC2626))),
              ),
          ],
        ),
      ),
    );
  }
}
