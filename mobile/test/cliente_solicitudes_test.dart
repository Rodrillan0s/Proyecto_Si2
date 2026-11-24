import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:emergencias_vehiculares/screens/cliente_solicitud_detalle_screen.dart';
import 'package:emergencias_vehiculares/screens/cliente_solicitudes_screen.dart';
import 'package:emergencias_vehiculares/screens/cliente_unidades_screen.dart';
import 'package:emergencias_vehiculares/services/auth_provider.dart';
import 'package:emergencias_vehiculares/theme/theme_provider.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('CU30 / HU117 – Consultar Estado de Solicitudes Enviadas para CLIENTE', () {
    testWidgets('ClienteUnidadesScreen contiene acceso a "Mis Solicitudes" (HU117)', (WidgetTester tester) async {
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

      // Verificar que la tarjeta y acceso a "Mis Solicitudes" existe en el Portal Cliente
      expect(find.text('Mis Solicitudes'), findsOneWidget);
      expect(find.text('HU117'), findsOneWidget);

      // Tocar la tarjeta de solicitudes y verificar navegación a ClienteSolicitudesScreen
      await tester.tap(find.text('Mis Solicitudes'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      expect(find.byType(ClienteSolicitudesScreen), findsOneWidget);
      expect(find.text('Mis Solicitudes'), findsWidgets);
    });

    testWidgets('ClienteSolicitudesScreen muestra cabecera, badge HU117 y estado inicial controlado', (WidgetTester tester) async {
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: ThemeProvider()),
          ],
          child: const MaterialApp(
            home: ClienteSolicitudesScreen(),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(seconds: 1));

      // Cabecera de pantalla
      expect(find.text('Mis Solicitudes'), findsWidgets);
      expect(find.text('HU117'), findsOneWidget);
      expect(find.text('Historial de solicitudes'), findsOneWidget);

      // Estado de consulta controlado
      expect(find.text('Consultando solicitudes...'), findsOneWidget);
    });

    testWidgets('ClienteSolicitudDetalleScreen renderiza datos, estado y respuesta oficial de constructora', (WidgetTester tester) async {
      final solicitudConRespuesta = {
        'id_solicitud': 10,
        'id_cliente': 5,
        'id_usuario': 12,
        'id_empresa': 1,
        'id_obra': 8,
        'nombre_obra': 'Torre Mirador',
        'codigo_obra': 'OBR-TM',
        'id_unidad': 9,
        'codigo_unidad': 'DP-401',
        'tipo_unidad': 'DEPARTAMENTO',
        'titulo': 'Consulta sobre instalación de gas',
        'descripcion': 'Deseo saber cuándo iniciará la instalación de medidores de gas en mi piso.',
        'estado': 'ATENDIDA',
        'respuesta': 'Estimado cliente, los medidores serán colocados el próximo 15 de diciembre por la empresa instaladora.',
        'fecha_creacion': '2026-11-20T09:00:00',
        'fecha_respuesta': '2026-11-22T14:30:00',
      };

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: ThemeProvider()),
          ],
          child: MaterialApp(
            home: ClienteSolicitudDetalleScreen(solicitud: solicitudConRespuesta),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(seconds: 1));

      // Validar datos principales
      expect(find.text('Detalle de Solicitud'), findsOneWidget);
      expect(find.text('Consulta sobre instalación de gas'), findsOneWidget);
      expect(find.text('ATENDIDA'), findsOneWidget);
      expect(find.text('Torre Mirador'), findsOneWidget);
      expect(find.text('DP-401'), findsOneWidget);
      expect(find.text('Deseo saber cuándo iniciará la instalación de medidores de gas en mi piso.'), findsOneWidget);

      // Validar respuesta oficial de la constructora
      expect(find.text('Respuesta de la constructora'), findsOneWidget);
      expect(find.text('Respuesta oficial registrada'), findsOneWidget);
      expect(find.text('Estimado cliente, los medidores serán colocados el próximo 15 de diciembre por la empresa instaladora.'), findsOneWidget);

      // Validar restricción estricta de HU117: Solo consulta y seguimiento (sin inputs ni respuestas)
      expect(find.byType(TextField), findsNothing);
      expect(find.byType(TextFormField), findsNothing);
      expect(find.text('Responder'), findsNothing);
      expect(find.text('Enviar'), findsNothing);
    });

    testWidgets('ClienteSolicitudDetalleScreen muestra claramente solicitud pendiente sin respuesta', (WidgetTester tester) async {
      final solicitudPendiente = {
        'id_solicitud': 11,
        'id_cliente': 5,
        'id_usuario': 12,
        'id_empresa': 1,
        'id_obra': 8,
        'nombre_obra': 'Torre Mirador',
        'codigo_obra': 'OBR-TM',
        'id_unidad': 9,
        'codigo_unidad': 'DP-401',
        'tipo_unidad': 'DEPARTAMENTO',
        'titulo': 'Solicitud de copia de planos sanitarios',
        'descripcion': 'Requiero copia digital de los planos sanitarios de la unidad.',
        'estado': 'PENDIENTE',
        'respuesta': null,
        'fecha_creacion': '2026-11-23T08:00:00',
        'fecha_respuesta': null,
      };

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: ThemeProvider()),
          ],
          child: MaterialApp(
            home: ClienteSolicitudDetalleScreen(solicitud: solicitudPendiente),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(seconds: 1));

      expect(find.text('Solicitud de copia de planos sanitarios'), findsOneWidget);
      expect(find.text('PENDIENTE'), findsOneWidget);
      expect(find.text('Pendiente de respuesta oficial'), findsOneWidget);
      expect(find.text('La constructora aún no ha registrado una respuesta a su solicitud. Le notificaremos en cuanto el equipo de obra o atención emita su dictamen.'), findsOneWidget);
    });
  });
}
