import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../services/notificacion_service.dart';
import '../theme/app_theme.dart';

class NotificacionesScreen extends StatefulWidget {
  const NotificacionesScreen({super.key});

  @override
  State<NotificacionesScreen> createState() => _NotificacionesScreenState();
}

class _NotificacionesScreenState extends State<NotificacionesScreen> {
  final NotificacionService _service = NotificacionService.instance;
  bool _cargandoInicial = false;
  bool _marcandoTodo = false;
  bool _enviandoPrueba = false;
  String? _errorCarga;
  String _filtroActivo = 'TODAS'; // TODAS, NO_LEIDAS, LEIDAS

  @override
  void initState() {
    super.initState();
    _service.addListener(_onServiceUpdated);
    _cargarInicial();
  }

  @override
  void dispose() {
    _service.removeListener(_onServiceUpdated);
    super.dispose();
  }

  void _onServiceUpdated() {
    if (mounted) {
      setState(() {});
    }
  }

  Future<void> _cargarInicial() async {
    if (_service.notificaciones.isEmpty) {
      setState(() {
        _cargandoInicial = true;
        _errorCarga = null;
      });
    }
    try {
      await _service.listarMisNotificaciones();
      if (!mounted) return;
      setState(() {
        _cargandoInicial = false;
        _errorCarga = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _cargandoInicial = false;
        _errorCarga = e.toString().replaceAll('Exception: ', '');
      });
    }
  }

  Future<void> _refrescar() async {
    setState(() => _errorCarga = null);
    try {
      await _service.listarMisNotificaciones();
    } catch (e) {
      if (!mounted) return;
      _mostrarError(e.toString().replaceAll('Exception: ', ''));
    }
  }

  bool _esLeido(dynamic value) => NotificacionService.esLeidoValor(value);

  String _texto(dynamic value) {
    if (value == null) return '';
    return value.toString().trim();
  }

  Color _colorTipo(String tipo) {
    final t = tipo.toUpperCase();
    if (t.contains('INCIDENCIA') || t.contains('ALERTA') || t.contains('URGENTE') || t.contains('EMERGENCIA')) {
      return AppTheme.warning;
    }
    if (t.contains('ORDEN') || t.contains('ASIGNACION') || t.contains('ROL')) {
      return AppTheme.info;
    }
    if (t.contains('ERROR') || t.contains('FALLA') || t.contains('RECHAZ')) {
      return AppTheme.error;
    }
    if (t.contains('AVANCE') || t.contains('ACEPTAD') || t.contains('EXITO')) {
      return AppTheme.success;
    }
    return AppTheme.primary;
  }

  IconData _iconoTipo(String tipo) {
    final t = tipo.toUpperCase();
    if (t.contains('INCIDENCIA') || t.contains('ALERTA') || t.contains('EMERGENCIA')) {
      return Icons.warning_amber_rounded;
    }
    if (t.contains('ORDEN') || t.contains('ASIGNACION')) {
      return Icons.assignment_outlined;
    }
    if (t.contains('AVANCE')) {
      return Icons.timeline_rounded;
    }
    if (t.contains('CRM') || t.contains('OFERTA') || t.contains('COMERCIAL')) {
      return Icons.people_alt_outlined;
    }
    if (t.contains('ERROR')) {
      return Icons.error_outline_rounded;
    }
    return Icons.notifications_active_outlined;
  }

  Future<void> _marcarTodo() async {
    setState(() => _marcandoTodo = true);
    try {
      await _service.marcarTodasComoLeidas();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Todas las notificaciones fueron marcadas como leídas.'),
          backgroundColor: AppTheme.success,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      _mostrarError(e.toString().replaceAll('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _marcandoTodo = false);
    }
  }

  Future<void> _probarPushTiempoReal() async {
    setState(() => _enviandoPrueba = true);
    try {
      await _service.enviarNotificacionPrueba(
        titulo: 'Alerta Push OBRATEC en Tiempo Real',
        cuerpo: 'Canal de notificaciones push activo y sincronizado con el servidor.',
        tipo: 'OBRA',
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Notificación push emitida en tiempo real.'),
          backgroundColor: AppTheme.primary,
          duration: Duration(seconds: 2),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      _mostrarError(e.toString().replaceAll('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _enviandoPrueba = false);
    }
  }

  Future<void> _abrirNotificacion(Map<String, dynamic> notificacion) async {
    final id = int.tryParse(_texto(notificacion['id_notificacion']));
    try {
      if (id != null && !_esLeido(notificacion['leido'])) {
        await _service.marcarComoLeida(idNotificacion: id);
      }
      if (!mounted) return;
      _mostrarDetalleModal(notificacion);
    } catch (e) {
      if (!mounted) return;
      _mostrarError(e.toString().replaceAll('Exception: ', ''));
    }
  }

  void _mostrarDetalleModal(Map<String, dynamic> notificacion) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final sheetBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
    final subColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);

    final titulo = _texto(notificacion['titulo']).isEmpty
        ? 'Notificación'
        : _texto(notificacion['titulo']);
    final cuerpo = _texto(notificacion['cuerpo']).isEmpty
        ? _texto(notificacion['mensaje'])
        : _texto(notificacion['cuerpo']);
    final tipo = _texto(notificacion['tipo_referencia']).isEmpty
        ? (_texto(notificacion['tipo']).isEmpty ? 'OBRA' : _texto(notificacion['tipo']))
        : _texto(notificacion['tipo_referencia']);
    final fecha = _texto(notificacion['fecha_creacion']).isEmpty
        ? _texto(notificacion['created_at'])
        : _texto(notificacion['fecha_creacion']);

    showModalBottomSheet(
      context: context,
      backgroundColor: sheetBg,
      shape: RoundedRectangleBorder(
        borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        side: BorderSide(color: borderColor),
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
                    color: _colorTipo(tipo).withValues(alpha: 0.14),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(_iconoTipo(tipo), color: _colorTipo(tipo), size: 22),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    tipo.toUpperCase(),
                    style: GoogleFonts.inter(
                      fontSize: 11.5,
                      fontWeight: FontWeight.w800,
                      color: _colorTipo(tipo),
                      letterSpacing: 0.7,
                    ),
                  ),
                ),
                IconButton(
                  icon: Icon(Icons.close_rounded, size: 20, color: subColor),
                  onPressed: () => Navigator.pop(ctx),
                ),
              ],
            ),
            const SizedBox(height: 14),
            Text(
              titulo,
              style: GoogleFonts.inter(
                fontSize: 17,
                fontWeight: FontWeight.w800,
                color: titleColor,
              ),
            ),
            if (fecha.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                fecha,
                style: GoogleFonts.inter(fontSize: 11.5, color: subColor),
              ),
            ],
            const SizedBox(height: 14),
            Divider(color: borderColor),
            const SizedBox(height: 14),
            Text(
              cuerpo.isNotEmpty ? cuerpo : 'Sin detalles adicionales.',
              style: GoogleFonts.inter(
                fontSize: 13.5,
                color: isDark ? const Color(0xFFCBD5E1) : const Color(0xFF334155),
                height: 1.5,
              ),
            ),
            const SizedBox(height: 22),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => Navigator.pop(ctx),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: Text(
                  'Entendido',
                  style: GoogleFonts.inter(fontWeight: FontWeight.w700),
                ),
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
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC);
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
    final subColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);

    final todas = _service.notificaciones;
    final noLeidas = _service.unreadCount;
    final lista = todas.where((n) {
      final leido = _esLeido(n['leido']);
      if (_filtroActivo == 'NO_LEIDAS') return !leido;
      if (_filtroActivo == 'LEIDAS') return leido;
      return true;
    }).toList();

    return Scaffold(
      backgroundColor: bg,
      appBar: AppBar(
        backgroundColor: cardBg,
        elevation: 0,
        titleSpacing: 16,
        title: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Notificaciones Push',
                    style: GoogleFonts.inter(
                      fontSize: 16.5,
                      fontWeight: FontWeight.w800,
                      color: titleColor,
                    ),
                  ),
                  Row(
                    children: [
                      Container(
                        width: 7,
                        height: 7,
                        decoration: BoxDecoration(
                          color: _service.isConnected
                              ? AppTheme.success
                              : const Color(0xFFF59E0B),
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 5),
                      Flexible(
                        child: Text(
                          _service.isConnected
                              ? 'Canal Push en tiempo real activo'
                              : 'Sincronización automática activa',
                          style: GoogleFonts.inter(
                            fontSize: 10.5,
                            fontWeight: FontWeight.w600,
                            color: subColor,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'Enviar notificación push de prueba',
            icon: _enviandoPrueba
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primary),
                  )
                : const Icon(Icons.notifications_active_outlined, size: 21),
            onPressed: _enviandoPrueba ? null : _probarPushTiempoReal,
          ),
          IconButton(
            tooltip: 'Marcar todas como leídas',
            icon: _marcandoTodo
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primary),
                  )
                : const Icon(Icons.done_all_rounded, size: 21),
            onPressed: (_marcandoTodo || noLeidas == 0) ? null : _marcarTodo,
          ),
          const SizedBox(width: 6),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Container(
              color: cardBg,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              child: Row(
                children: [
                  _buildFilterChip('TODAS', 'Todas (${todas.length})', isDark, borderColor, subColor),
                  const SizedBox(width: 8),
                  _buildFilterChip('NO_LEIDAS', 'No leídas ($noLeidas)', isDark, borderColor, subColor),
                  const SizedBox(width: 8),
                  _buildFilterChip('LEIDAS', 'Leídas', isDark, borderColor, subColor),
                ],
              ),
            ),
            Divider(height: 1, color: borderColor),
            Expanded(
              child: RefreshIndicator(
                color: AppTheme.primary,
                onRefresh: _refrescar,
                child: _buildBody(
                  isDark: isDark,
                  cardBg: cardBg,
                  borderColor: borderColor,
                  titleColor: titleColor,
                  subColor: subColor,
                  lista: lista,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBody({
    required bool isDark,
    required Color cardBg,
    required Color borderColor,
    required Color titleColor,
    required Color subColor,
    required List<Map<String, dynamic>> lista,
  }) {
    if (_cargandoInicial && lista.isEmpty) {
      return const Center(
        child: CircularProgressIndicator(
          strokeWidth: 2.5,
          color: AppTheme.primary,
        ),
      );
    }

    if (_errorCarga != null && lista.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline_rounded, size: 48, color: AppTheme.error),
              const SizedBox(height: 12),
              Text(
                _errorCarga!,
                textAlign: TextAlign.center,
                style: GoogleFonts.inter(color: subColor, fontSize: 13),
              ),
              const SizedBox(height: 16),
              OutlinedButton.icon(
                onPressed: _cargarInicial,
                icon: const Icon(Icons.refresh, size: 18),
                label: const Text('Reintentar'),
              ),
            ],
          ),
        ),
      );
    }

    if (lista.isEmpty) {
      return ListView(
        children: [
          SizedBox(height: MediaQuery.of(context).size.height * 0.18),
          Center(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppTheme.primary.withValues(alpha: 0.14),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.notifications_off_outlined,
                      size: 38,
                      color: AppTheme.primary,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Sin notificaciones',
                    style: GoogleFonts.inter(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: titleColor,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Recibirás alertas push en tiempo real cuando se registren avances, incidencias u órdenes de trabajo.',
                    textAlign: TextAlign.center,
                    style: GoogleFonts.inter(
                      fontSize: 12.5,
                      color: subColor,
                    ),
                  ),
                  const SizedBox(height: 16),
                  OutlinedButton.icon(
                    onPressed: _enviandoPrueba ? null : _probarPushTiempoReal,
                    icon: const Icon(Icons.bolt_rounded, size: 18, color: AppTheme.primary),
                    label: Text(
                      'Enviar alerta push de prueba',
                      style: GoogleFonts.inter(
                        fontSize: 12.5,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.primary,
                      ),
                    ),
                  ),
                ],
              ),
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
        final tipo = _texto(item['tipo_referencia']).isEmpty
            ? (_texto(item['tipo']).isEmpty ? 'OBRA' : _texto(item['tipo']))
            : _texto(item['tipo_referencia']);
        final titulo = _texto(item['titulo']).isEmpty
            ? 'Alerta de Obra'
            : _texto(item['titulo']);
        final cuerpo = _texto(item['cuerpo']).isEmpty
            ? _texto(item['mensaje'])
            : _texto(item['cuerpo']);
        final fecha = _texto(item['fecha_creacion']).isEmpty
            ? _texto(item['created_at'])
            : _texto(item['fecha_creacion']);

        final unreadBg = isDark
            ? AppTheme.primary.withValues(alpha: 0.12)
            : AppTheme.primaryLight.withValues(alpha: 0.55);

        return Material(
          color: leido ? cardBg : unreadBg,
          borderRadius: BorderRadius.circular(14),
          child: InkWell(
            onTap: () => _abrirNotificacion(item),
            borderRadius: BorderRadius.circular(14),
            child: Container(
              padding: const EdgeInsets.all(14.0),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                  color: leido
                      ? borderColor
                      : AppTheme.primary.withValues(alpha: 0.45),
                  width: leido ? 1 : 1.3,
                ),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    padding: const EdgeInsets.all(9),
                    decoration: BoxDecoration(
                      color: _colorTipo(tipo).withValues(alpha: 0.14),
                      borderRadius: BorderRadius.circular(10),
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
                            Flexible(
                              child: Text(
                                tipo.toUpperCase(),
                                style: GoogleFonts.inter(
                                  fontSize: 10,
                                  fontWeight: FontWeight.w800,
                                  color: _colorTipo(tipo),
                                  letterSpacing: 0.5,
                                ),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            if (fecha.isNotEmpty) ...[
                              const SizedBox(width: 8),
                              Text(
                                fecha,
                                style: GoogleFonts.inter(
                                  fontSize: 10,
                                  color: subColor,
                                ),
                              ),
                            ],
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          titulo,
                          style: GoogleFonts.inter(
                            fontSize: 13.5,
                            fontWeight: leido ? FontWeight.w600 : FontWeight.w800,
                            color: titleColor,
                          ),
                        ),
                        if (cuerpo.isNotEmpty) ...[
                          const SizedBox(height: 4),
                          Text(
                            cuerpo,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: GoogleFonts.inter(
                              fontSize: 12,
                              color: subColor,
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
  }

  Widget _buildFilterChip(
    String valor,
    String label,
    bool isDark,
    Color borderColor,
    Color subColor,
  ) {
    final seleccionado = _filtroActivo == valor;
    return GestureDetector(
      onTap: () => setState(() => _filtroActivo = valor),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: seleccionado ? AppTheme.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: seleccionado ? AppTheme.primary : borderColor,
          ),
        ),
        child: Text(
          label,
          style: GoogleFonts.inter(
            fontSize: 11.5,
            fontWeight: seleccionado ? FontWeight.w700 : FontWeight.w600,
            color: seleccionado ? Colors.white : subColor,
          ),
        ),
      ),
    );
  }
}
