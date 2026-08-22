import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/auth_provider.dart';
import '../services/notificacion_ws_service.dart';
import '../theme/app_theme.dart';
import 'notificaciones_screen.dart';
import 'perfil_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String _nombreUsuario = '';
  String _rolUsuario = '';

  final NotificacionWsService _wsService = NotificacionWsService();
  bool _wsActivo = false;
  bool _estaConectadoRed = true;

  StreamSubscription? _conexionSub;

  @override
  void initState() {
    super.initState();
    _cargarDatosUsuario();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      _iniciarWebSocket();
      _escucharConexion();
    });
  }

  @override
  void dispose() {
    _conexionSub?.cancel();
    _wsService.desconectar();
    super.dispose();
  }

  void _cargarDatosUsuario() {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    setState(() {
      _nombreUsuario = auth.usuarioCompleto ?? 'Usuario';
      _rolUsuario = auth.rol ?? 'SIN ROL';
    });
  }

  void _iniciarWebSocket() {
    _wsService.conectar(
      onEstado: (activo) {
        if (!mounted) return;
        setState(() {
          _wsActivo = activo;
        });
      },
      onMensaje: (mensaje) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              '${mensaje['titulo'] ?? 'Nueva Notificación'}: ${mensaje['cuerpo'] ?? ''}',
            ),
            backgroundColor: AppTheme.primary,
          ),
        );
      },
      onError: (error) {
        debugPrint('Error de WebSocket: $error');
      },
    );
  }

  void _escucharConexion() {
    _conexionSub = Connectivity().onConnectivityChanged.listen((event) {
      final conectado = _hayConexionDesdeEvento(event);
      if (!mounted) return;

      setState(() {
        _estaConectadoRed = conectado;
      });

      if (conectado) {
        _wsService.reconectar(
          onEstado: (activo) {
            if (mounted) setState(() => _wsActivo = activo);
          },
          onMensaje: (mensaje) {},
          onError: (_) {},
        );
      }
    });
  }

  bool _hayConexionDesdeEvento(dynamic event) {
    if (event is List<ConnectivityResult>) {
      return !event.contains(ConnectivityResult.none);
    }
    if (event is ConnectivityResult) {
      return event != ConnectivityResult.none;
    }
    return false;
  }

  void _cerrarSesion() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Cerrar Sesión'),
        content: const Text('¿Estás seguro de que deseas salir del sistema?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              Provider.of<AuthProvider>(context, listen: false).cerrarSesion();
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error),
            child: const Text('Salir'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text(
          'BASE GESTIÓN',
          style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1.2),
        ),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const NotificacionesScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: _cerrarSesion,
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Barra de estado de conexión
            if (!_estaConectadoRed)
              Container(
                color: AppTheme.error,
                padding: const EdgeInsets.symmetric(vertical: 4),
                width: double.infinity,
                child: const Text(
                  'Sin conexión a Internet',
                  style: TextStyle(color: Colors.white, fontSize: 12),
                  textAlign: TextAlign.center,
                ),
              )
            else if (!_wsActivo)
              Container(
                color: Colors.amber,
                padding: const EdgeInsets.symmetric(vertical: 4),
                width: double.infinity,
                child: const Text(
                  'Sincronizando tiempo real...',
                  style: TextStyle(color: Colors.black87, fontSize: 12),
                  textAlign: TextAlign.center,
                ),
              ),

            // Encabezado del usuario
            Container(
              padding: const EdgeInsets.all(20),
              width: double.infinity,
              decoration: BoxDecoration(
                color: AppTheme.primary,
                borderRadius: const BorderRadius.only(
                  bottomLeft: Radius.circular(24),
                  bottomRight: Radius.circular(24),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Bienvenido,',
                    style: TextStyle(color: Colors.white70, fontSize: 16),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _nombreUsuario,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.white24,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      _rolUsuario,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 1.0,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // Módulos base y plantillas
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: GridView.count(
                  crossAxisCount: 2,
                  crossAxisSpacing: 14,
                  mainAxisSpacing: 14,
                  children: [
                    _buildMenuCard(
                      icon: Icons.person,
                      title: 'Mi Perfil',
                      subtitle: 'Gestionar mi cuenta',
                      color: Colors.blue,
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => const PerfilScreen()),
                        );
                      },
                    ),
                    _buildMenuCard(
                      icon: Icons.notifications_active,
                      title: 'Notificaciones',
                      subtitle: 'Alertas del sistema',
                      color: Colors.teal,
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => const NotificacionesScreen(),
                          ),
                        );
                      },
                    ),
                    _buildMenuCard(
                      icon: Icons.engineering_outlined,
                      title: 'Obras Civiles',
                      subtitle: 'Módulo Esqueleto',
                      color: Colors.amber[800]!,
                      onTap: () => _mostrarSnackbarEsqueleto('Obras Civiles'),
                    ),
                    _buildMenuCard(
                      icon: Icons.assignment_outlined,
                      title: 'Proyectos',
                      subtitle: 'Módulo Esqueleto',
                      color: Colors.purple,
                      onTap: () => _mostrarSnackbarEsqueleto('Proyectos'),
                    ),
                    _buildMenuCard(
                      icon: Icons.home_repair_service_outlined,
                      title: 'Remodelaciones',
                      subtitle: 'Módulo Esqueleto',
                      color: Colors.indigo,
                      onTap: () => _mostrarSnackbarEsqueleto('Remodelaciones'),
                    ),
                    _buildMenuCard(
                      icon: Icons.build_circle_outlined,
                      title: 'Órdenes de Trabajo',
                      subtitle: 'Módulo Esqueleto',
                      color: Colors.deepOrange,
                      onTap: () =>
                          _mostrarSnackbarEsqueleto('Órdenes de Trabajo'),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMenuCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  shape: BoxShape.circle,
                ),
                child: Icon(icon, color: color, size: 28),
              ),
              const SizedBox(height: 12),
              Text(
                title,
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 15,
                  color: Colors.black87,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: const TextStyle(fontSize: 11, color: Colors.black45),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _mostrarSnackbarEsqueleto(String modulo) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          'Esqueleto del módulo "$modulo" listo para desarrollo incremental.',
        ),
        duration: const Duration(seconds: 2),
      ),
    );
  }
}