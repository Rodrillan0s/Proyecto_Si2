import 'package:flutter/material.dart';
import 'services/offline_pedido_service.dart';

//SCREENS
import 'screens/auth_screen.dart';
import 'screens/home_screen.dart';
import 'services/token_storage.dart';
import 'theme/app_theme.dart';
import 'screens/perfil_screen.dart';
import 'screens/productos_screen.dart';
import 'screens/pedidos_screen.dart';
import 'screens/ordenes_screen.dart';
import 'screens/entregas_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final token = await TokenStorage.getToken();

  runApp(AgroEnlaceApp(isLoggedIn: token != null));
}

class AgroEnlaceApp extends StatelessWidget {
  final bool isLoggedIn;

  const AgroEnlaceApp({
    super.key,
    required this.isLoggedIn,
  });

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AgroEnlace Mobile',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,

      // Si ya inició sesión antes, entra al home.
      initialRoute: isLoggedIn ? '/home' : '/auth',

      //await OfflinePedidoService.instance.init();
      routes: {
        '/auth': (context) => const AuthScreen(),
        '/home': (context) => const HomeScreen(),
        '/perfil': (context) => const PerfilScreen(),
        '/productos': (context) => const ProductosScreen(),
        '/pedidos': (context) => const PedidosScreen(),
        '/ordenes': (context) => const OrdenesScreen(),
        '/entregas': (context) => const EntregasScreen(),
      },
    );
  }
}