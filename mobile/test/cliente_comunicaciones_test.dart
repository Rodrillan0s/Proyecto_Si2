import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:emergencias_vehiculares/screens/cliente_comunicaciones_screen.dart';
import 'package:emergencias_vehiculares/screens/cliente_unidades_screen.dart';
import 'package:emergencias_vehiculares/services/auth_provider.dart';
import 'package:emergencias_vehiculares/theme/theme_provider.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('CU30 / HU116 – Comunicaciones Oficiales de la Constructora para CLIENTE', () {
    testWidgets('ClienteUnidadesScreen contiene acceso directo a Comunicaciones (HU116)', (WidgetTester tester) async {
      final auth = AuthProvider();
      auth.loginExitoso({
        'nombre_completo': 'María González',
        'nombre_rol': 'CLIENTE',
        'correo': 'maria@cliente.com',
        'ci': '9988776',
        'id_empresa': '1',
        'nombre_empresa': 'Constructora Los Andes',
      });

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: auth),
            ChangeNotifierProvider.value(value: ThemeProvider()),
          ],
          child: const MaterialApp(
            home: ClienteUnidadesScreen(),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(seconds: 1));

      // Verificar que la tarjeta y acceso a comunicaciones existe en el Portal Cliente
      expect(find.text('Comunicaciones de la Constructora'), findsOneWidget);
      expect(find.text('HU116'), findsOneWidget);

      // Tocar la tarjeta de comunicaciones y verificar navegación a ClienteComunicacionesScreen
      await tester.tap(find.text('Comunicaciones de la Constructora'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      expect(find.byType(ClienteComunicacionesScreen), findsOneWidget);
      expect(find.text('Comunicaciones Oficiales'), findsOneWidget);
    });

    testWidgets('ClienteComunicacionesScreen muestra cabecera, badge HU116 y estados controlados', (WidgetTester tester) async {
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: ThemeProvider()),
          ],
          child: const MaterialApp(
            home: ClienteComunicacionesScreen(),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(seconds: 1));

      // Cabecera de pantalla
      expect(find.text('Comunicaciones Oficiales'), findsOneWidget);
      expect(find.text('HU116'), findsOneWidget);
      expect(find.text('Bandeja de comunicados'), findsOneWidget);

      // Al iniciar la pantalla, muestra el estado de consulta controlado
      expect(find.text('Consultando comunicaciones oficiales...'), findsOneWidget);
    });

    testWidgets('ClienteComunicacionesScreen no muestra campos de respuesta, input ni chat (Solo Lectura)', (WidgetTester tester) async {
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: ThemeProvider()),
          ],
          child: const MaterialApp(
            home: ClienteComunicacionesScreen(),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(seconds: 1));

      // Validar restricción estricta de HU116: solo consulta y lectura
      expect(find.byType(TextField), findsNothing);
      expect(find.byType(TextFormField), findsNothing);
      expect(find.text('Enviar'), findsNothing);
      expect(find.text('Responder'), findsNothing);
    });
  });
}
