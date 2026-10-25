import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:emergencias_vehiculares/screens/cronogramas_screen.dart';
import 'package:emergencias_vehiculares/services/auth_provider.dart';
import 'package:emergencias_vehiculares/services/cronograma_service.dart';

class _Supervisor extends AuthProvider {
  @override
  String get rolNormalizado => 'SUPERVISOR_OBRA';
}

void main() {
  testWidgets('El hito muestra una sola fecha prevista editable',
      (tester) async {
    await tester.pumpWidget(const MaterialApp(
        home: CronogramaEditorScreen(idObra: 10, puedeCabecera: true, plan: {
      'id_cronograma': 1,
      'version': 1,
      'nombre': 'Plan',
      'descripcion': '',
      'fecha_inicio': '2026-01-01',
      'fecha_fin': '2026-12-31',
      'actividades': [
        {
          'clave': 'h',
          'nombre': 'Entrega',
          'descripcion': '',
          'tipo': 'HITO',
          'fecha_inicio': '2026-01-10',
          'fecha_fin': '2026-01-10',
          'inicio_real': null,
          'fin_real': null,
          'avance': 0,
          'dependencias': []
        }
      ]
    })));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('1. Entrega'));
    await tester.tap(find.text('1. Entrega'));
    await tester.pumpAndSettle();
    final fecha = find.byWidgetPredicate(
        (w) => w is TextField && w.decoration?.labelText == 'Fecha prevista');
    expect(fecha, findsOneWidget);
    expect(
        find.byWidgetPredicate(
            (w) => w is TextField && w.decoration?.labelText == 'Fin previsto'),
        findsNothing);
    expect(
        find.byWidgetPredicate((w) =>
            w is TextField && w.decoration?.labelText == 'Inicio previsto'),
        findsNothing);
    await tester.ensureVisible(fecha);
    await tester.tap(fecha);
    await tester.pumpAndSettle();
    expect(find.byType(DatePickerDialog), findsOneWidget);
    await tester.tap(find.text('5'));
    await tester.tap(find.text('OK'));
    await tester.pumpAndSettle();
    expect(tester.widget<TextField>(fecha).controller!.text, '2026-01-05');
    await tester.ensureVisible(find.text('Aceptar actividad'));
    await tester.tap(find.text('Aceptar actividad'));
    await tester.pumpAndSettle();
    expect(find.text('HITO · 2026-01-05 → 2026-01-05'), findsOneWidget);
  });
  test('Supervisor consulta y planifica sin crear ni modificar cabecera', () {
    final auth = _Supervisor();
    expect(auth.hasPermission('Visualizar_cronograma'), isTrue);
    expect(auth.hasPermission('Planificar_cronograma'), isTrue);
    expect(auth.hasPermission('Registrar_cronograma'), isFalse);
    expect(auth.hasPermission('Modificar_cronograma'), isFalse);
  });
  test('Payload elimina campos derivados y normaliza fechas vacías', () {
    final payload = actividadPayload({
      'clave': 'a',
      'nombre': 'Obra',
      'descripcion': '',
      'tipo': 'HITO',
      'fecha_inicio': '2026-01-01',
      'fecha_fin': '2026-01-01',
      'inicio_real': '',
      'fin_real': null,
      'avance': 0,
      'dependencias': [],
      'dias_retraso': 30,
      'estado': 'PENDIENTE',
      'bloqueada': true
    });
    expect(payload['inicio_real'], isNull);
    expect(payload.containsKey('dias_retraso'), isFalse);
    expect(payload.containsKey('estado'), isFalse);
  });
  testWidgets('Supervisor ve cabecera de solo lectura y editor de actividades',
      (tester) async {
    await tester.pumpWidget(ChangeNotifierProvider<AuthProvider>.value(
        value: _Supervisor(),
        child: const MaterialApp(
            home:
                CronogramaEditorScreen(idObra: 10, puedeCabecera: false, plan: {
          'id_cronograma': 1,
          'version': 2,
          'nombre': 'Plan base',
          'descripcion': '',
          'fecha_inicio': '2026-01-01',
          'fecha_fin': '2026-12-31',
          'actividades': <dynamic>[]
        }))));
    await tester.pump();
    final nombre =
        tester.widget<TextFormField>(find.byType(TextFormField).first);
    expect(nombre.initialValue, 'Plan base');
    expect(find.text('+ Actividad'), findsOneWidget);
    expect(find.text('+ Hito'), findsOneWidget);
    expect(find.text('Guardar planificación'), findsOneWidget);
  });
}
