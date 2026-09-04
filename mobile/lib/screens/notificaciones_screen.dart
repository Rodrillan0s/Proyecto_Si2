import 'package:flutter/material.dart';
import '../services/notificacion_service.dart';
import '../theme/app_theme.dart';

class NotificacionesScreen extends StatefulWidget {
  const NotificacionesScreen({super.key});

  @override
  State<NotificacionesScreen> createState() => _NotificacionesScreenState();
}

class _NotificacionesScreenState extends State<NotificacionesScreen> {
  late Future<List<Map<String, dynamic>>> _futureNotificaciones;
  bool _marcandoTodo = false;
  String _filtroActivo = 'TODAS'; // TODAS, NO_LEIDAS, LEIDAS

  @override
  void initState() {
    super.initState();
    _futureNotificaciones = NotificacionService().listarMisNotificaciones();
  }

  Future<void> _refrescar() async {
    final nuevaCarga = NotificacionService().listarMisNotificaciones();
    setState(() {
      _futureNotificaciones = nuevaCarga;
    });
    await nuevaCarga;
  }

  bool _esLeido(dynamic value) {
    if (value is bool) return value;
    final texto = value?.toString().toLowerCase().trim();
    return texto == 'true' || texto == '1' || texto == 'si';
  }

  String _texto(dynamic value) {
    if (value == null) return '';
    return value.toString().trim();
  }

  Color _colorTipo(String tipo) {
    final t = tipo.toUpperCase();
    if (t.contains('OBRA') || t.contains('PROYECTO')) return AppTheme.primary;
    if (t.contains('ASIGNACION') || t.contains('ROL')) return AppTheme.info;
    if (t.contains('ALERTA') || t.contains('URGENTE')) return AppTheme.warning;
    if (t.contains('ERROR') || t.contains('FALLA')) return AppTheme.error;
    return AppTheme.textSecondary;
  }

  IconData _iconoTipo(String tipo) {
    final t = tipo.toUpperCase();
    if (t.contains('OBRA') || t.contains('PROYECTO')) return Icons.engineering_rounded;
    if (t.contains('ASIGNACION') || t.contains('ROL')) return Icons.badge_outlined;
    if (t.contains('ALERTA') || t.contains('URGENTE')) return Icons.warning_amber_rounded;
    if (t.contains('ERROR')) return Icons.error_outline_rounded;
    return Icons.notifications_none_rounded;
  }

  Future<void> _marcarTodo() async {
    setState(() => _marcandoTodo = true);
    try {
      await NotificacionService().marcarTodasComoLeidas();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Todas las notificaciones fueron marcadas como leídas.'),
          backgroundColor: AppTheme.success,
        ),
      );
      await _refrescar();
    } catch (e) {
      if (!mounted) return;
      _mostrarError(e.toString().replaceAll('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _marcandoTodo = false);
    }
  }

  Future<void> _abrirNotificacion(Map<String, dynamic> notificacion) async {
    final id = int.tryParse(_texto(notificacion['id_notificacion']));
    try {
      if (id != null && !_esLeido(notificacion['leido'])) {
        await NotificacionService().marcarComoLeida(idNotificacion: id);
      }
      if (!mounted) return;
      _mostrarDetalleModal(notificacion);
      _refrescar();
    } catch (e) {
      if (!mounted) return;
      _mostrarError(e.toString().replaceAll('Exception: ', ''));
    }
  }

  void _mostrarDetalleModal(Map<String, dynamic> notificacion) {
    final titulo = _texto(notificacion['titulo']).isEmpty ? 'Notificación' : _texto(notificacion['titulo']);
    final cuerpo = _texto(notificacion['cuerpo']).isEmpty ? _texto(notificacion['mensaje']) : _texto(notificacion['cuerpo']);
    final tipo = _texto(notificacion['tipo']).isEmpty ? 'GENERAL' : _texto(notificacion['tipo']);
    final fecha = _texto(notificacion['created_at']);

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(AppTheme.radiusXLarge)),
      ),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: _colorTipo(tipo).withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                  ),
                  child: Icon(_iconoTipo(tipo), color: _colorTipo(tipo), size: 22),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    tipo.toUpperCase(),
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                      color: _colorTipo(tipo),
                      letterSpacing: 0.8,
                    ),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 20),
                  onPressed: () => Navigator.pop(ctx),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text(
              titulo,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w800,
                color: AppTheme.textPrimary,
              ),
            ),
            if (fecha.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                fecha,
                style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
              ),
            ],
            const SizedBox(height: 16),
            const Divider(),
            const SizedBox(height: 16),
            Text(
              cuerpo.isNotEmpty ? cuerpo : 'Sin detalles adicionales.',
              style: const TextStyle(
                fontSize: 14,
                color: AppTheme.textSecondary,
                height: 1.5,
              ),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => Navigator.pop(ctx),
                style: ElevatedButton.styleFrom(backgroundColor: AppTheme.secondary),
                child: const Text('Entendido'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _mostrarError(String mensaje) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(mensaje),
        backgroundColor: AppTheme.error,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Centro de Notificaciones'),
        actions: [
          IconButton(
            tooltip: 'Marcar todas como leídas',
            icon: _marcandoTodo
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.done_all_rounded),
            onPressed: _marcandoTodo ? null : _marcarTodo,
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Barra de filtros
            Container(
              color: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              child: Row(
                children: [
                  _buildFilterChip('TODAS', 'Todas'),
                  const SizedBox(width: 8),
                  _buildFilterChip('NO_LEIDAS', 'No leídas'),
                  const SizedBox(width: 8),
                  _buildFilterChip('LEIDAS', 'Leídas'),
                ],
              ),
            ),
            const Divider(),

            // Lista de notificaciones
            Expanded(
              child: RefreshIndicator(
                color: AppTheme.primary,
                onRefresh: _refrescar,
                child: FutureBuilder<List<Map<String, dynamic>>>(
                  future: _futureNotificaciones,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return const Center(
                        child: CircularProgressIndicator(
                          strokeWidth: 2.5,
                          color: AppTheme.primary,
                        ),
                      );
                    }

                    if (snapshot.hasError) {
                      return Center(
                        child: Padding(
                          padding: const EdgeInsets.all(24.0),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Icon(Icons.error_outline_rounded, size: 48, color: AppTheme.error),
                              const SizedBox(height: 12),
                              Text(
                                snapshot.error.toString().replaceAll('Exception: ', ''),
                                textAlign: TextAlign.center,
                                style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                              ),
                              const SizedBox(height: 16),
                              OutlinedButton.icon(
                                onPressed: _refrescar,
                                icon: const Icon(Icons.refresh, size: 18),
                                label: const Text('Reintentar'),
                              ),
                            ],
                          ),
                        ),
                      );
                    }

                    final todas = snapshot.data ?? [];
                    final lista = todas.where((n) {
                      final leido = _esLeido(n['leido']);
                      if (_filtroActivo == 'NO_LEIDAS') return !leido;
                      if (_filtroActivo == 'LEIDAS') return leido;
                      return true;
                    }).toList();

                    if (lista.isEmpty) {
                      return ListView(
                        children: [
                          SizedBox(height: MediaQuery.of(context).size.height * 0.2),
                          Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Container(
                                  padding: const EdgeInsets.all(16),
                                  decoration: BoxDecoration(
                                    color: AppTheme.primaryLight,
                                    shape: BoxShape.circle,
                                  ),
                                  child: const Icon(
                                    Icons.notifications_off_outlined,
                                    size: 40,
                                    color: AppTheme.primary,
                                  ),
                                ),
                                const SizedBox(height: 16),
                                const Text(
                                  'Sin notificaciones',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                    color: AppTheme.textPrimary,
                                  ),
                                ),
                                const SizedBox(height: 6),
                                const Text(
                                  'Te avisaremos cuando haya novedades en la obra.',
                                  style: TextStyle(
                                    fontSize: 13,
                                    color: AppTheme.textSecondary,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      );
                    }

                    return ListView.separated(
                      padding: const EdgeInsets.all(16),
                      itemCount: lista.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 10),
                      itemBuilder: (context, index) {
                        final item = lista[index];
                        final leido = _esLeido(item['leido']);
                        final tipo = _texto(item['tipo']).isEmpty ? 'GENERAL' : _texto(item['tipo']);
                        final titulo = _texto(item['titulo']).isEmpty ? 'Alerta de Obra' : _texto(item['titulo']);
                        final cuerpo = _texto(item['cuerpo']).isEmpty ? _texto(item['mensaje']) : _texto(item['cuerpo']);
                        final fecha = _texto(item['created_at']);

                        return Card(
                          color: leido ? Colors.white : AppTheme.primaryLight.withValues(alpha: 0.5),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
                            side: BorderSide(
                              color: leido ? AppTheme.border : AppTheme.primary.withValues(alpha: 0.3),
                              width: leido ? 1 : 1.2,
                            ),
                          ),
                          child: InkWell(
                            onTap: () => _abrirNotificacion(item),
                            borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
                            child: Padding(
                              padding: const EdgeInsets.all(14.0),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Container(
                                    padding: const EdgeInsets.all(8),
                                    decoration: BoxDecoration(
                                      color: _colorTipo(tipo).withValues(alpha: 0.12),
                                      borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                                    ),
                                    child: Icon(_iconoTipo(tipo), color: _colorTipo(tipo), size: 20),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                          children: [
                                            Text(
                                              tipo.toUpperCase(),
                                              style: TextStyle(
                                                fontSize: 10,
                                                fontWeight: FontWeight.w800,
                                                color: _colorTipo(tipo),
                                                letterSpacing: 0.5,
                                              ),
                                            ),
                                            if (fecha.isNotEmpty)
                                              Text(
                                                fecha,
                                                style: const TextStyle(
                                                  fontSize: 10,
                                                  color: AppTheme.textMuted,
                                                ),
                                              ),
                                          ],
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          titulo,
                                          style: TextStyle(
                                            fontSize: 14,
                                            fontWeight: leido ? FontWeight.w600 : FontWeight.w800,
                                            color: AppTheme.textPrimary,
                                          ),
                                        ),
                                        if (cuerpo.isNotEmpty) ...[
                                          const SizedBox(height: 4),
                                          Text(
                                            cuerpo,
                                            maxLines: 2,
                                            overflow: TextOverflow.ellipsis,
                                            style: const TextStyle(
                                              fontSize: 12,
                                              color: AppTheme.textSecondary,
                                              height: 1.35,
                                            ),
                                          ),
                                        ],
                                      ],
                                    ),
                                  ),
                                  if (!leido) ...[
                                    const SizedBox(width: 8),
                                    Container(
                                      width: 8,
                                      height: 8,
                                      margin: const EdgeInsets.only(top: 6),
                                      decoration: const BoxDecoration(
                                        color: AppTheme.primary,
                                        shape: BoxShape.circle,
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                            ),
                          ),
                        );
                      },
                    );
                  },
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFilterChip(String valor, String label) {
    final seleccionado = _filtroActivo == valor;
    return GestureDetector(
      onTap: () => setState(() => _filtroActivo = valor),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
        decoration: BoxDecoration(
          color: seleccionado ? AppTheme.secondary : Colors.transparent,
          borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
          border: Border.all(
            color: seleccionado ? AppTheme.secondary : AppTheme.border,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: seleccionado ? FontWeight.w700 : FontWeight.w500,
            color: seleccionado ? Colors.white : AppTheme.textSecondary,
          ),
        ),
      ),
    );
  }
}