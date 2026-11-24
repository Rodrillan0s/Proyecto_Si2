import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'theme/app_theme.dart';
import 'theme/theme_provider.dart';
import 'services/auth_provider.dart';
import 'services/notificacion_service.dart';
import 'services/offline_sync_service.dart';
import 'screens/auth_screens.dart';
import 'screens/home_screen.dart';
import 'screens/notificaciones_screen.dart';

final GlobalKey<NavigatorState> appNavigatorKey = GlobalKey<NavigatorState>();

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
  ]);

  final authProvider = AuthProvider();
  await authProvider.verificarSesion();

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider.value(value: authProvider),
        ChangeNotifierProvider.value(value: NotificacionService.instance),
        ChangeNotifierProvider.value(value: OfflineSyncService.instance),
        ChangeNotifierProvider(create: (_) => ThemeProvider()),
      ],
      child: const ConstructorApp(),
    ),
  );
}

class ConstructorApp extends StatefulWidget {
  const ConstructorApp({super.key});

  @override
  State<ConstructorApp> createState() => _ConstructorAppState();
}

class _ConstructorAppState extends State<ConstructorApp> with WidgetsBindingObserver {
  StreamSubscription<Map<String, dynamic>>? _pushSub;
  Map<String, dynamic>? _activePush;
  Timer? _dismissTimer;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _pushSub = NotificacionService.instance.incomingPushStream.listen(_onGlobalPush);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _pushSub?.cancel();
    _dismissTimer?.cancel();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      unawaited(NotificacionService.instance.onAppResumed());
    }
  }

  void _onGlobalPush(Map<String, dynamic> alert) {
    if (!mounted) return;
    try {
      HapticFeedback.mediumImpact();
    } catch (_) {}
    _dismissTimer?.cancel();
    setState(() => _activePush = alert);
    _dismissTimer = Timer(const Duration(seconds: 5), () {
      if (mounted) {
        setState(() => _activePush = null);
      }
    });
  }

  void _openNotificationsFromBanner() {
    _dismissTimer?.cancel();
    setState(() => _activePush = null);
    appNavigatorKey.currentState?.push(
      MaterialPageRoute(builder: (_) => const NotificacionesScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final themeProv = context.watch<ThemeProvider>();

    return MaterialApp(
      navigatorKey: appNavigatorKey,
      title: 'OBRATEC Mobile — Gestión de Obras',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: themeProv.themeMode,
      home: const _RootRouter(),
      builder: (context, child) {
        return Stack(
          children: [
            if (child != null) child,
            if (_activePush != null)
              Positioned(
                top: MediaQuery.of(context).padding.top + 8,
                left: 12,
                right: 12,
                child: Material(
                  color: Colors.transparent,
                  child: GestureDetector(
                    onTap: _openNotificationsFromBanner,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0F172A),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: AppTheme.primary.withValues(alpha: 0.7), width: 1.2),
                        boxShadow: const [
                          BoxShadow(
                            color: Color(0x44000000),
                            blurRadius: 14,
                            offset: Offset(0, 6),
                          ),
                        ],
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: AppTheme.primary.withValues(alpha: 0.18),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(
                              Icons.notifications_active_rounded,
                              color: AppTheme.primary,
                              size: 18,
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(
                                  _activePush!['titulo']?.toString() ?? 'Nueva notificación',
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 13,
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                                if ((_activePush!['cuerpo']?.toString() ?? '').isNotEmpty) ...[
                                  const SizedBox(height: 2),
                                  Text(
                                    _activePush!['cuerpo'].toString(),
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(
                                      color: Color(0xFFCBD5E1),
                                      fontSize: 11.5,
                                    ),
                                  ),
                                ],
                              ],
                            ),
                          ),
                          IconButton(
                            onPressed: () {
                              _dismissTimer?.cancel();
                              setState(() => _activePush = null);
                            },
                            icon: const Icon(Icons.close_rounded, color: Color(0xFF94A3B8), size: 18),
                            padding: EdgeInsets.zero,
                            constraints: const BoxConstraints(),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
          ],
        );
      },
    );
  }
}

/// Escucha AuthProvider y decide qué pantalla mostrar.
class _RootRouter extends StatelessWidget {
  const _RootRouter();

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 300),
      child: auth.estaAutenticado
          ? const HomeScreen(key: ValueKey('home'))
          : const LoginScreen(key: ValueKey('login')),
    );
  }
}
