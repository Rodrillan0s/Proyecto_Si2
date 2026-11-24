import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:emergencias_vehiculares/screens/cliente_unidad_detalle_screen.dart';
import 'package:emergencias_vehiculares/screens/cliente_unidades_screen.dart';
import 'package:emergencias_vehiculares/screens/home_screen.dart';
import 'package:emergencias_vehiculares/services/auth_provider.dart';
import 'package:emergencias_vehiculares/services/notificacion_service.dart';
import 'package:emergencias_vehiculares/theme/theme_provider.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('CU30 Etapa 1 & HU114 – Pruebas de Rol, Unidades y Avance Físico', () {
    test('AuthProvider determina correctamente el rol CLIENTE', () {
      final auth = AuthProvider();

      // Caso 1: Usuario con rol CLIENTE
      auth.loginExitoso({
        'nombre_completo': 'Fabricio Cliente',
        'nombre_rol': 'CLIENTE',
        'correo': 'fabricio@gmail.com',
        'ci': '9876543',
        'id_empresa': '1',
        'nombre_empresa': 'OBRATEC',
      });
      expect(auth.esCliente, isTrue);
      expect(auth.esAdminGlobal, isFalse);
      expect(auth.esJefeObra, isFalse);

      // Caso 2: Usuario con rol ADMINISTRADOR
      auth.loginExitoso({
        'nombre_completo': 'Admin General',
        'nombre_rol': 'ADMINISTRADOR',
        'correo': 'admin@obratec.com',
        'ci': '1234567',
        'id_empresa': '1',
        'nombre_empresa': 'OBRATEC',
      });
      expect(auth.esCliente, isFalse);
      expect(auth.esAdminGlobal, isTrue);

      // Caso 3: Usuario con rol JEFE DE OBRA
      auth.loginExitoso({
        'nombre_completo': 'Ing. Residente',
        'nombre_rol': 'JEFE DE OBRA',
        'correo': 'jefe@obratec.com',
        'ci': '5555555',
        'id_empresa': '1',
        'nombre_empresa': 'OBRATEC',
      });
      expect(auth.esCliente, isFalse);
      expect(auth.esJefeObra, isTrue);
    });

    testWidgets('HomeScreen muestra la opción "Mis Proyectos y Unidades" únicamente para el rol CLIENTE', (WidgetTester tester) async {
      final authCliente = AuthProvider();
      authCliente.loginExitoso({
        'nombre_completo': 'Ana Martínez',
        'nombre_rol': 'CLIENTE',
        'correo': 'ana@cliente.com',
        'ci': '6677889',
        'id_empresa': '1',
        'nombre_empresa': 'OBRATEC',
      });

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: authCliente),
            ChangeNotifierProvider.value(value: NotificacionService.instance),
            ChangeNotifierProvider.value(value: ThemeProvider()),
          ],
          child: const MaterialApp(
            home: HomeScreen(),
          ),
        ),
      );
      await tester.pump();

      // Debe encontrar la opción "Mis Proyectos y Unidades"
      expect(find.text('Mis Proyectos y Unidades'), findsWidgets);

      // Navegar a ClienteUnidadesScreen al pulsar la opción
      await tester.tap(find.text('Mis Proyectos y Unidades').first);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      // Comprobar que navegó exitosamente a ClienteUnidadesScreen
      expect(find.byType(ClienteUnidadesScreen), findsOneWidget);
      expect(find.text('PORTAL CLIENTE'), findsOneWidget);
    });

    testWidgets('HomeScreen NO muestra la opción "Mis Proyectos y Unidades" para ADMINISTRADOR', (WidgetTester tester) async {
      final authAdmin = AuthProvider();
      authAdmin.loginExitoso({
        'nombre_completo': 'Super Admin',
        'nombre_rol': 'ADMINISTRADOR',
        'correo': 'admin@obratec.com',
        'ci': '1111111',
        'id_empresa': '1',
        'nombre_empresa': 'OBRATEC',
      });

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: authAdmin),
            ChangeNotifierProvider.value(value: NotificacionService.instance),
            ChangeNotifierProvider.value(value: ThemeProvider()),
          ],
          child: const MaterialApp(
            home: HomeScreen(),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(seconds: 1));

      // NO debe encontrar ninguna opción ni tarjeta de "Mis Proyectos y Unidades"
      expect(find.text('Mis Proyectos y Unidades'), findsNothing);
      expect(find.text('PORTAL CLIENTE'), findsNothing);
    });

    testWidgets('ClienteUnidadesScreen muestra cabecera y estado offline controlado', (WidgetTester tester) async {
      final auth = AuthProvider();
      auth.loginExitoso({
        'nombre_completo': 'Carlos López',
        'nombre_rol': 'CLIENTE',
        'correo': 'carlos@cliente.com',
        'ci': '7788990',
        'id_empresa': '1',
        'nombre_empresa': 'Constructora Santa Cruz',
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

      // Cabecera con datos del cliente y empresa
      expect(find.text('Mis Proyectos y Unidades'), findsOneWidget);
      expect(find.text('PORTAL CLIENTE'), findsOneWidget);
      expect(find.text('Carlos López'), findsOneWidget);
      expect(find.text('Constructora Santa Cruz'), findsOneWidget);
      expect(find.text('Unidades inmobiliarias'), findsOneWidget);
    });

    testWidgets('ClienteUnidadDetalleScreen renderiza datos de unidad y sección HU114', (WidgetTester tester) async {
      final unidadDummy = {
        'id_cliente_unidad': 1,
        'id_cliente': 54,
        'id_unidad': 9,
        'estado_asociacion': 'COMPRADO',
        'monto_pactado': 85000.0,
        'fecha_asociacion': '2026-03-15T10:00:00',
        'observaciones': null,
        'codigo_unidad': 'DEP-302',
        'tipo_unidad': 'DEPARTAMENTO',
        'superficie': 78.5,
        'estado_unidad_actual': 'EN_CONSTRUCCION',
        'id_obra': 8,
        'nombre_obra': 'Edificio Los Sauces',
        'codigo_obra': 'OBR-008',
      };

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: ThemeProvider()),
          ],
          child: MaterialApp(
            home: ClienteUnidadDetalleScreen(unidad: unidadDummy),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(seconds: 1));

      // Validar datos de cabecera de unidad
      expect(find.text('Avance de Unidad'), findsOneWidget);
      expect(find.text('DEP-302'), findsOneWidget);
      expect(find.text('Edificio Los Sauces'), findsOneWidget);
      expect(find.text('OBR-008'), findsOneWidget);
      expect(find.text('DEPARTAMENTO'), findsOneWidget);
      expect(find.text('78.5 m²'), findsOneWidget);
      expect(find.text('COMPRADO'), findsOneWidget);

      // Validar sección de avance físico HU114
      expect(find.text('Avance físico reportado'), findsOneWidget);

      // Validar sección de fotografías HU115
      expect(find.text('Fotografías de la unidad'), findsOneWidget);
    });

    testWidgets('ClienteUnidadDetalleScreen muestra estados iniciales y secciones HU114 y HU115', (WidgetTester tester) async {
      final unidadDummy = {
        'id_cliente_unidad': 2,
        'id_cliente': 54,
        'id_unidad': 15,
        'codigo_unidad': 'CASA-12',
        'tipo_unidad': 'CASA',
        'superficie': 140.0,
        'estado_unidad_actual': 'EN_CONSTRUCCION',
        'id_obra': 8,
        'nombre_obra': 'Condominio Campestre',
        'codigo_obra': 'OBR-008',
      };

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: ThemeProvider()),
          ],
          child: MaterialApp(
            home: ClienteUnidadDetalleScreen(unidad: unidadDummy),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(seconds: 1));

      // Ambas secciones existen e integran la pantalla de detalle
      expect(find.text('Avance de Unidad'), findsOneWidget);
      expect(find.text('CASA-12'), findsOneWidget);
      expect(find.text('Avance físico reportado'), findsOneWidget);
      expect(find.text('Fotografías de la unidad'), findsOneWidget);
      expect(find.text('Cargando fotografías...'), findsOneWidget);
    });
  });
}
