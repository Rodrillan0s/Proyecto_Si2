import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:emergencias_vehiculares/screens/home_screen.dart';
import 'package:emergencias_vehiculares/screens/perfil_screen.dart';
import 'package:emergencias_vehiculares/services/auth_provider.dart';
import 'package:emergencias_vehiculares/theme/theme_provider.dart';

void main() {
  testWidgets('PerfilScreen renders without exceptions in offline state', (WidgetTester tester) async {
    final authProvider = AuthProvider();
    final themeProvider = ThemeProvider();

    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider<AuthProvider>.value(value: authProvider),
          ChangeNotifierProvider<ThemeProvider>.value(value: themeProvider),
        ],
        child: const MaterialApp(
          home: Scaffold(
            body: PerfilScreen(),
          ),
        ),
      ),
    );

    await tester.pump();
    await tester.pump(const Duration(seconds: 5));

    expect(find.byType(PerfilScreen), findsOneWidget);
    expect(find.text('Ajustes y Cuenta'), findsOneWidget);
    expect(find.text('INFORMACIÓN DE CUENTA'), findsOneWidget);
  });

  testWidgets('HomeScreen switches to PerfilScreen (Más) without exceptions', (WidgetTester tester) async {
    final authProvider = AuthProvider();
    final themeProvider = ThemeProvider();

    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider<AuthProvider>.value(value: authProvider),
          ChangeNotifierProvider<ThemeProvider>.value(value: themeProvider),
        ],
        child: const MaterialApp(
          home: HomeScreen(),
        ),
      ),
    );

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    // Tap on 'Más' tab (index 4)
    final masTab = find.text('Más');
    expect(masTab, findsOneWidget);
    await tester.tap(masTab);
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));

    expect(find.byType(PerfilScreen), findsOneWidget);
    expect(find.text('INFORMACIÓN DE CUENTA'), findsOneWidget);
  });
}
