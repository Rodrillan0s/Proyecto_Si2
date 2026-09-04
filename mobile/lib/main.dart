import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'theme/app_theme.dart';
import 'theme/theme_provider.dart';
import 'services/auth_provider.dart';
import 'screens/auth_screens.dart';
import 'screens/home_screen.dart';

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
        ChangeNotifierProvider(create: (_) => ThemeProvider()),
      ],
      child: const ConstructorApp(),
    ),
  );
}

class ConstructorApp extends StatelessWidget {
  const ConstructorApp({super.key});

  @override
  Widget build(BuildContext context) {
    final themeProv = context.watch<ThemeProvider>();

    return MaterialApp(
      title: 'OBRATEC Mobile — Gestión de Obras',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: themeProv.themeMode,
      home: const _RootRouter(),
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