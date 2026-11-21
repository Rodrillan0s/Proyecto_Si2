import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:emergencias_vehiculares/config/app_config.dart';
import 'package:emergencias_vehiculares/main.dart';
import 'package:emergencias_vehiculares/screens/asistente_screen.dart';
import 'package:emergencias_vehiculares/screens/reportes_screen.dart';
import 'package:emergencias_vehiculares/services/ai_assistant_service.dart';
import 'package:emergencias_vehiculares/services/auth_provider.dart';
import 'package:emergencias_vehiculares/services/notificacion_service.dart';
import 'package:emergencias_vehiculares/services/reportes_service.dart';
import 'package:emergencias_vehiculares/theme/theme_provider.dart';

void main() {
  testWidgets('App basic smoke test', (WidgetTester tester) async {
    expect(const ConstructorApp(), isNotNull);
  });

  test('AppConfig uses https://obratech-y040.onrender.com and wss://obratech-y040.onrender.com', () {
    expect(AppConfig.defaultCloudUrl, 'https://obratech-y040.onrender.com');
    expect(AppConfig.apiBaseUrl, 'https://obratech-y040.onrender.com');
    expect(AppConfig.wsBaseUrl, 'wss://obratech-y040.onrender.com');
    // Legacy cloud URL must automatically normalize to the new Render domain
    expect(
      AppConfig.resolveBaseUrl('https://obratec-66o2.onrender.com'),
      'https://obratech-y040.onrender.com',
    );
  });

  test('NotificacionService emits real-time push notifications and tracks unread count', () async {
    final service = NotificacionService.instance;
    service.disconnect();
    expect(service.unreadCount, 0);

    Map<String, dynamic>? receivedPush;
    final sub = service.incomingPushStream.listen((event) {
      receivedPush = event;
    });

    service.simulateIncomingPush({
      'id_notificacion': 501,
      'titulo': 'Avance registrado en Residencial Las Palmas',
      'cuerpo': 'Se registró un avance del 85% en Torre A.',
      'tipo_alerta': 'AVANCE_OBRA',
      'leido': false,
      'fecha_creacion': '2026-11-05 14:30:00',
    });

    await Future<void>.delayed(Duration.zero);
    expect(service.unreadCount, 1);
    expect(service.notificaciones.length, 1);
    expect(receivedPush, isNotNull);
    expect(receivedPush!['titulo'], 'Avance registrado en Residencial Las Palmas');
    expect(receivedPush!['tipo_referencia'], 'AVANCE_OBRA');

    await sub.cancel();
    service.disconnect();
  });

  test('AiAssistantService isolates chat sessions per user and company', () {
    AiAssistantService.clearAllSessions();

    final s1 = AiAssistantService.obtenerSesionAdmin(
      userIdentity: 'u:admin1@obratec.com',
      idEmpresa: 1,
    );
    s1.mensajes.add(
      AdminChatMessage(
        author: 'user',
        text: 'Generame un reporte de las obras con mas deficit',
        fecha: DateTime.now(),
      ),
    );

    final s2OtherCompany = AiAssistantService.obtenerSesionAdmin(
      userIdentity: 'u:admin1@obratec.com',
      idEmpresa: 3,
    );
    expect(s2OtherCompany.mensajes, isEmpty);
    expect(s1.mensajes.length, 1);

    // Al cambiar de usuario se deben limpiar todas las sesiones anteriores
    final s3OtherUser = AiAssistantService.obtenerSesionAdmin(
      userIdentity: 'u:cliente2@obratec.com',
      idEmpresa: 1,
    );
    expect(s3OtherUser.mensajes, isEmpty);
  });

  test('ReportesService includes saldo_comercial and all report families', () {
    expect(reportFamilies['finanzas'], contains('saldo_comercial'));
    expect(reportFamilies['finanzas'], contains('costos_periodo'));
    expect(reportFamilies['finanzas'], contains('comparativo_costos'));
    expect(reportFamilies['inventario'], contains('stock'));
    expect(ReportesService.identity().length, 36);
  });

  testWidgets('AsistenteScreen renders unified selector for admin and comercial mode for client',
      (WidgetTester tester) async {
    final auth = AuthProvider();
    auth.loginExitoso({
      'nombre_completo': 'Carlos Admin',
      'nombre_rol': 'ADMINISTRADOR_EMPRESA',
      'correo': 'carlos@obratec.com',
      'ci': '4455667',
      'id_empresa': '1',
      'nombre_empresa': 'CONSTRUCTORA OBRATEC',
    });

    final sesion = AiAssistantService.obtenerSesionAdmin(
      userIdentity: auth.userIdentityKey,
      idEmpresa: auth.idEmpresaActiva,
    );
    sesion.catalog = {
      'reportes': [
        {'id': 'saldo_comercial', 'titulo': 'Saldo Comercial'},
      ],
      'obras': [],
      'acciones': ['Visualizar_reportes', 'Exportar_reportes', 'Usar_ia'],
    };

    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider<AuthProvider>.value(value: auth),
          ChangeNotifierProvider<ThemeProvider>(create: (_) => ThemeProvider()),
        ],
        child: const MaterialApp(
          home: AsistenteScreen(),
        ),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(seconds: 2));

    expect(find.text('Gestión / Admin'), findsOneWidget);
    expect(find.text('Comercial & Planos'), findsOneWidget);
    expect(
      find.text('Generame un reporte de las obras con mas deficit'),
      findsOneWidget,
    );
  });

  testWidgets('ReportesScreen prompts global admin to select company when none active',
      (WidgetTester tester) async {
    final auth = AuthProvider();
    auth.loginExitoso({
      'nombre_completo': 'Super Admin',
      'nombre_rol': 'ADMINISTRADOR',
      'correo': 'root@obratec.com',
      'ci': '112233',
      'id_empresa': '',
      'nombre_empresa': '',
    });

    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider<AuthProvider>.value(value: auth),
          ChangeNotifierProvider<ThemeProvider>(create: (_) => ThemeProvider()),
        ],
        child: const MaterialApp(
          home: ReportesScreen(),
        ),
      ),
    );
    await tester.pump();

    expect(find.text('Selecciona una empresa'), findsOneWidget);
  });
}
