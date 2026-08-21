import 'package:flutter/material.dart';
import '../services/offline_pedido_service.dart';
import '../services/auth_service.dart';
import '../services/token_storage.dart';
import '../theme/app_theme.dart';
import '../services/notification_socket_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String name = '';
  String mail = '';
  int role = 0;
  int? empresaId;
  final socketService = NotificationSocketService.instance;
  int _lastShownNotificationId = 0;

  @override
  void initState() {
    super.initState();
    loadUser();

    socketService.addListener(_handleSocketNotification);
    socketService.connect();

    OfflinePedidoService.instance.init();
  }

  @override
  void dispose() {
    socketService.removeListener(_handleSocketNotification);
    super.dispose();
  }

  void _handleSocketNotification() {
    final notification = socketService.lastNotification;

    if (notification == null) return;

    if (notification.localId == _lastShownNotificationId) return;

    _lastShownNotificationId = notification.localId;

    if (!mounted) return;

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          backgroundColor: AppTheme.primaryGreen,
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 5),
          content: Row(
            children: [
              const Icon(
                Icons.notifications_active,
                color: Colors.white,
                size: 22,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  '${notification.asunto}: ${notification.mensaje}',
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    });
  }

  Future<void> loadUser() async {
    final userName = await TokenStorage.getUserName();
    final userMail = await TokenStorage.getUserMail();
    final userRole = await TokenStorage.getUserRole();
    final currentEmpresaId = await TokenStorage.getEmpresaId();

    if (!mounted) return;

    setState(() {
      name = userName ?? 'Usuario';
      mail = userMail ?? '';
      role = userRole ?? 0;
      empresaId = currentEmpresaId;
    });
  }

  Widget _buildCrmNotificationCard() {
    return AnimatedBuilder(
      animation: socketService,
      builder: (context, _) {
        final notification = socketService.lastNotification;

        return Container(
          width: double.infinity,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            border: Border.all(
              color: socketService.unreadCount > 0
                  ? Colors.green.shade300
                  : AppTheme.borderColor,
            ),
            borderRadius: BorderRadius.circular(10),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.03),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Row(
            children: [
              Stack(
                clipBehavior: Clip.none,
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryGreen.withOpacity(0.10),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(
                      Icons.notifications_active_outlined,
                      color: AppTheme.primaryGreen,
                      size: 23,
                    ),
                  ),
                  if (socketService.unreadCount > 0)
                    Positioned(
                      right: -5,
                      top: -5,
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 6,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.red,
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          socketService.unreadCount.toString(),
                          style: const TextStyle(
                            fontSize: 9,
                            fontWeight: FontWeight.w900,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ),
                ],
              ),
              const SizedBox(width: 12),
              Expanded(
                child: notification == null
                    ? const Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'NOTIFICACIONES CRM',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w900,
                              color: AppTheme.slateText,
                              letterSpacing: 0.8,
                            ),
                          ),
                          SizedBox(height: 3),
                          Text(
                            'Aún no recibiste notificaciones del servidor.',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w700,
                              color: AppTheme.mutedText,
                            ),
                          ),
                        ],
                      )
                    : Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            notification.asunto.toUpperCase(),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w900,
                              color: AppTheme.slateText,
                              letterSpacing: 0.8,
                            ),
                          ),
                          const SizedBox(height: 3),
                          Text(
                            notification.mensaje,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w700,
                              color: AppTheme.mutedText,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '${notification.canal}  •  ${notification.fecha}',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 8,
                              fontWeight: FontWeight.w900,
                              color: AppTheme.primaryGreen,
                              letterSpacing: 0.7,
                            ),
                          ),
                        ],
                      ),
              ),
              const SizedBox(width: 8),
              if (socketService.unreadCount > 0)
                IconButton(
                  onPressed: socketService.markNotificationsAsRead,
                  icon: const Icon(
                    Icons.done_all,
                    color: AppTheme.primaryGreen,
                  ),
                  tooltip: 'Marcar como leído',
                ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildOfflinePedidosCard() {
    final offlineService = OfflinePedidoService.instance;

    return AnimatedBuilder(
      animation: offlineService,
      builder: (context, _) {
        return Container(
          width: double.infinity,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            border: Border.all(
              color: offlineService.pendingCount > 0
                  ? Colors.amber.shade300
                  : AppTheme.borderColor,
            ),
            borderRadius: BorderRadius.circular(10),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.03),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Row(
            children: [
              Container(
                width: 11,
                height: 11,
                decoration: BoxDecoration(
                  color: offlineService.statusColor,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'MODO OFFLINE: ${offlineService.statusLabel}',
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w900,
                        color: AppTheme.slateText,
                        letterSpacing: 0.8,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      offlineService.pendingCount == 0
                          ? 'No tienes pedidos pendientes por enviar.'
                          : 'Pedidos pendientes por enviar: ${offlineService.pendingCount}',
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.mutedText,
                      ),
                    ),
                    if (offlineService.lastMessage.isNotEmpty) ...[
                      const SizedBox(height: 3),
                      Text(
                        offlineService.lastMessage,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.mutedText,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(width: 10),
              SizedBox(
                height: 34,
                child: OutlinedButton(
                  onPressed: offlineService.syncing
                      ? null
                      : () async {
                          await offlineService.syncPendingOrders();
                        },
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppTheme.primaryGreen,
                    side: const BorderSide(color: AppTheme.primaryGreen),
                    padding: const EdgeInsets.symmetric(horizontal: 10),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(7),
                    ),
                  ),
                  child: Text(
                    offlineService.syncing ? '...' : 'ENVIAR',
                    style: const TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 0.8,
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
  Widget _buildSocketStatusCard() {
    return AnimatedBuilder(
      animation: socketService,
      builder: (context, _) {
        final status = socketService.status;
        final connected = status == SocketConnectionStatus.connected;
        final connecting = status == SocketConnectionStatus.connecting ||
            status == SocketConnectionStatus.reconnecting;
        final error = status == SocketConnectionStatus.error;

        return Container(
          width: double.infinity,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            border: Border.all(
              color: error
                  ? Colors.red.shade200
                  : connected
                      ? Colors.green.shade200
                      : AppTheme.borderColor,
            ),
            borderRadius: BorderRadius.circular(10),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.03),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Row(
            children: [
              Container(
                width: 11,
                height: 11,
                decoration: BoxDecoration(
                  color: socketService.statusColor,
                  shape: BoxShape.circle,
                  boxShadow: [
                    if (connected)
                      BoxShadow(
                        color: Colors.green.withOpacity(0.35),
                        blurRadius: 8,
                        spreadRadius: 2,
                      ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'CANAL DE NOTIFICACIONES: ${socketService.statusLabel}',
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w900,
                        color: AppTheme.slateText,
                        letterSpacing: 0.8,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      socketService.lastMessage.isEmpty
                          ? 'Socket.IO listo para recibir eventos del servidor.'
                          : socketService.lastMessage,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.mutedText,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              SizedBox(
                height: 34,
                child: OutlinedButton(
                  onPressed: connecting
                      ? null
                      : connected
                          ? socketService.disconnect
                          : socketService.reconnect,
                  style: OutlinedButton.styleFrom(
                    foregroundColor:
                        connected ? Colors.red : AppTheme.primaryGreen,
                    side: BorderSide(
                      color: connected ? Colors.red : AppTheme.primaryGreen,
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 10),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(7),
                    ),
                  ),
                  child: Text(
                    connecting
                        ? '...'
                        : connected
                            ? 'CORTAR'
                            : 'RECONECTAR',
                    style: const TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 0.8,
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Future<void> logout() async {
    socketService.disconnect();
    await AuthService.logout();

    if (!mounted) return;

    Navigator.pushReplacementNamed(context, '/auth');
  }

  String getRoleName(int roleId) {
    switch (roleId) {
      case 1:
        return 'ADMINISTRADOR';
      case 2:
        return 'SUPERVISOR';
      case 3:
        return 'EMPLEADO';
      case 4:
        return 'CLIENTE';
      default:
        return 'SIN ROL';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundBlue,
      body: SafeArea(
        child: Column(
          children: [
            Container(
              height: 4,
              width: double.infinity,
              color: AppTheme.primaryGreen,
            ),
            Expanded(
              child: RefreshIndicator(
                onRefresh: loadUser,
                color: AppTheme.primaryGreen,
                child: ListView(
                  padding: const EdgeInsets.all(18),
                  children: [
                    _buildHeader(),
                    const SizedBox(height: 16),
                    _buildWelcomeCard(),
                    const SizedBox(height: 16),
                    _buildSocketStatusCard(),
                    const SizedBox(height: 16),
                    _buildOfflinePedidosCard(),
                    const SizedBox(height: 16),
                    _buildCrmNotificationCard(),
                    const SizedBox(height: 12),
                    _buildQuickStats(),
                    const SizedBox(height: 20),
                    _buildSectionTitle('MÓDULOS PRINCIPALES'),
                    const SizedBox(height: 10),
                    _buildModuleCard(
                      icon: Icons.storefront,
                      title: 'Productos agrícolas',
                      subtitle: 'Comprar semillas y fertilizantes disponibles',
                      tag: 'CATÁLOGO',
                      onTap: () {
                        Navigator.pushNamed(context, '/productos');
                      },
                    ),
                    _buildModuleCard(
                      icon: Icons.receipt_long,
                      title: 'Pedidos',
                      subtitle: 'Ver historial y detalle de tus compras',
                      tag: 'COMPRAS',
                      onTap: () {
                        Navigator.pushNamed(context, '/pedidos');
                      },
                    ),
                    _buildModuleCard(
                      icon: Icons.person,
                      title: 'Perfil',
                      subtitle: 'Actualizar tus datos personales',
                      tag: 'CUENTA',
                      onTap: () {
                        Navigator.pushNamed(context, '/perfil');
                      },
                    ),
                    _buildModuleCard(
                      icon: Icons.assignment,
                      title: 'Órdenes de trabajo',
                      subtitle: 'Ver actividades asignadas y cargar reportes',
                      tag: 'CAMPO',
                      onTap: () {
                        Navigator.pushNamed(context, '/ordenes');
                      },
                    ),
                    if (role == 3)
                      _buildModuleCard(
                        icon: Icons.local_shipping,
                        title: 'Entregas',
                        subtitle: 'Rutas de distribución y confirmación de entrega',
                        tag: 'LOGÍSTICA',
                        onTap: () {
                          Navigator.pushNamed(context, '/entregas');
                        },
                      ),
                    const SizedBox(height: 14),
                    _buildFooter(),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Row(
      children: [
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: AppTheme.primaryGreen,
            borderRadius: BorderRadius.circular(14),
          ),
          child: const Icon(
            Icons.eco,
            color: Colors.white,
            size: 28,
          ),
        ),
        const SizedBox(width: 12),
        const Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'AGROENLACE',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w900,
                  color: AppTheme.slateText,
                  letterSpacing: 1.3,
                ),
              ),
              SizedBox(height: 2),
              Text(
                'Aplicación móvil',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.mutedText,
                ),
              ),
            ],
          ),
        ),
        IconButton(
          onPressed: () {
            Navigator.pushNamed(context, '/perfil');
          },
          style: IconButton.styleFrom(
            backgroundColor: Colors.white,
            foregroundColor: AppTheme.primaryGreen,
            side: const BorderSide(color: AppTheme.borderColor),
          ),
          icon: const Icon(Icons.person_outline),
        ),
        const SizedBox(width: 6),
        IconButton(
          onPressed: logout,
          style: IconButton.styleFrom(
            backgroundColor: AppTheme.primaryGreen,
            foregroundColor: Colors.white,
          ),
          icon: const Icon(Icons.logout),
        ),
      ],
    );
  }

  Widget _buildWelcomeCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppTheme.primaryGreen,
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primaryGreen.withOpacity(0.22),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Stack(
        children: [
          Positioned(
            right: -20,
            top: -18,
            child: Icon(
              Icons.agriculture,
              size: 110,
              color: Colors.white.withOpacity(0.10),
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'BIENVENIDO',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w900,
                  color: Colors.white70,
                  letterSpacing: 1.5,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                name.toUpperCase(),
                style: const TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.w900,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                mail,
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: Colors.white70,
                ),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  _buildWhiteBadge(getRoleName(role)),
                  const SizedBox(width: 8),
                  _buildWhiteBadge(
                    empresaId == null ? 'SIN EMPRESA' : 'EMPRESA $empresaId',
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQuickStats() {
    return Row(
      children: [
        Expanded(
          child: _buildSmallCard(
            icon: Icons.verified_user,
            title: 'SESIÓN',
            value: 'ACTIVA',
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _buildSmallCard(
            icon: Icons.shopping_bag,
            title: 'MÓDULOS',
            value: role == 3 ? '5' : '4',
          ),
        ),
      ],
    );
  }

  Widget _buildSmallCard({
    required IconData icon,
    required String title,
    required String value,
  }) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.borderColor),
      ),
      child: Row(
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: AppTheme.primaryGreen.withOpacity(0.10),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(
              icon,
              color: AppTheme.primaryGreen,
              size: 20,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.w900,
                    color: AppTheme.mutedText,
                    letterSpacing: 1.1,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w900,
                    color: AppTheme.slateText,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildModuleCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required String tag,
    required VoidCallback onTap,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: Container(
            padding: const EdgeInsets.all(15),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppTheme.borderColor),
            ),
            child: Row(
              children: [
                Container(
                  width: 52,
                  height: 52,
                  decoration: BoxDecoration(
                    color: AppTheme.primaryGreen.withOpacity(0.10),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Icon(
                    icon,
                    color: AppTheme.primaryGreen,
                    size: 26,
                  ),
                ),
                const SizedBox(width: 13),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: AppTheme.primaryGreen.withOpacity(0.08),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          tag,
                          style: const TextStyle(
                            fontSize: 8,
                            fontWeight: FontWeight.w900,
                            color: AppTheme.primaryGreen,
                            letterSpacing: 1,
                          ),
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        title.toUpperCase(),
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w900,
                          color: AppTheme.slateText,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        subtitle,
                        style: const TextStyle(
                          fontSize: 11,
                          color: AppTheme.mutedText,
                          height: 1.3,
                        ),
                      ),
                    ],
                  ),
                ),
                const Icon(
                  Icons.arrow_forward_ios,
                  size: 16,
                  color: AppTheme.mutedText,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildWhiteBadge(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: 10,
        vertical: 6,
      ),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.14),
        borderRadius: BorderRadius.circular(30),
        border: Border.all(color: Colors.white24),
      ),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 9,
          fontWeight: FontWeight.w900,
          color: Colors.white,
          letterSpacing: 1,
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.w900,
        color: AppTheme.mutedText,
        letterSpacing: 1.5,
      ),
    );
  }

  Widget _buildFooter() {
    return const Center(
      child: Text(
        'UAGRM • 2026',
        style: TextStyle(
          fontSize: 9,
          fontWeight: FontWeight.w900,
          color: Colors.grey,
          letterSpacing: 2,
        ),
      ),
    );
  }
}