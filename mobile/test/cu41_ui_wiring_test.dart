import 'dart:io';

import 'package:emergencias_vehiculares/screens/sync_status_screen.dart';
import 'package:emergencias_vehiculares/services/offline_db_service.dart';
import 'package:emergencias_vehiculares/services/offline_sync_service.dart';
import 'package:emergencias_vehiculares/widgets/offline_banner.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:provider/provider.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

void main() {
  sqfliteFfiInit();

  late Directory tempDir;
  late String dbPath;

  setUp(() async {
    tempDir = await Directory.systemTemp.createTemp('obratec_cu41_ui_test_');
    dbPath = p.join(tempDir.path, 'cu41_ui.db');
  });

  tearDown(() async {
    if (await tempDir.exists()) {
      await tempDir.delete(recursive: true);
    }
  });

  test('obtenerDetalleObraOfflineFirst y obtenerEstructuraOfflineFirst leen copia local tras cierre y reapertura sin red', () async {
    bool online = true;
    final db1 = OfflineDbService(databaseFactory: databaseFactoryFfi, dbPath: dbPath);
    final sync1 = OfflineSyncService(db: db1, checkConnectivity: () async => online);

    await sync1.inicializarContexto(idEmpresa: 3, userKey: 'u:jefe@laroca.bo', activarObservadores: false);
    final detOnline = await sync1.obtenerDetalleObraOfflineFirst(
      idEmpresa: 3,
      userKey: 'u:jefe@laroca.bo',
      idObra: 15,
      fetcherRemoto: (_) async => {'id_obra': 15, 'nombre': 'Edificio Central', 'ubicacion': 'Santa Cruz'},
    );
    expect(detOnline.esCopiaLocal, isFalse);

    final estOnline = await sync1.obtenerEstructuraOfflineFirst(
      idEmpresa: 3,
      userKey: 'u:jefe@laroca.bo',
      idObra: 15,
      fetcherRemoto: (_) async => [
        {'id_estructura': 1, 'nombre': 'Torre Norte', 'tipo': 'TORRE'},
      ],
    );
    expect(estOnline.esCopiaLocal, isFalse);

    // Simular cierre/reinicio y apertura sin red
    await db1.close();
    online = false;

    final db2 = OfflineDbService(databaseFactory: databaseFactoryFfi, dbPath: dbPath);
    final sync2 = OfflineSyncService(db: db2, checkConnectivity: () async => online);
    await sync2.inicializarContexto(idEmpresa: 3, userKey: 'u:jefe@laroca.bo', activarObservadores: false);

    final detOffline = await sync2.obtenerDetalleObraOfflineFirst(
      idEmpresa: 3,
      userKey: 'u:jefe@laroca.bo',
      idObra: 15,
      fetcherRemoto: (_) async => throw Exception('Sin internet'),
    );
    expect(detOffline.esCopiaLocal, isTrue);
    expect(detOffline.data['nombre'], 'Edificio Central');
    expect(detOffline.ultimaActualizacion, isNotNull);

    final estOffline = await sync2.obtenerEstructuraOfflineFirst(
      idEmpresa: 3,
      userKey: 'u:jefe@laroca.bo',
      idObra: 15,
      fetcherRemoto: (_) async => throw Exception('Sin internet'),
    );
    expect(estOffline.esCopiaLocal, isTrue);
    expect(estOffline.data.first['nombre'], 'Torre Norte');

    await db2.close();
  });

  testWidgets('OfflineBanner muestra advertencia de copia local y navega a SyncStatusScreen con conteos', (tester) async {
    final db = OfflineDbService(databaseFactory: databaseFactoryFfi, dbPath: dbPath);
    final sync = OfflineSyncService(db: db, checkConnectivity: () async => false);
    await tester.runAsync(() async {
      await sync.inicializarContexto(idEmpresa: 3, userKey: 'u:sup@laroca.bo', activarObservadores: false);
      await sync.registrarAvanceOffline(
        idEmpresa: 3,
        userKey: 'u:sup@laroca.bo',
        idObra: 15,
        idUnidad: 7,
        porcentajeAvance: 40,
        observacion: 'Avance offline UI test',
      );
    });

    await tester.pumpWidget(
      ChangeNotifierProvider<OfflineSyncService>.value(
        value: sync,
        child: MaterialApp(
          home: Scaffold(
            body: OfflineBanner(
              esCopiaLocal: true,
              ultimaActualizacion: DateTime.utc(2026, 11, 23, 18, 0),
            ),
          ),
        ),
      ),
    );

    expect(find.textContaining('Modo sin conexión'), findsOneWidget);
    expect(find.textContaining('1 en cola'), findsOneWidget);

    await tester.tap(find.text('Ver estado'));
    await tester.pumpAndSettle();

    expect(find.byType(SyncStatusScreen), findsOneWidget);
    expect(find.text('Estado de sincronización'), findsOneWidget);
    expect(find.textContaining('Avance de obra (40.0%)'), findsOneWidget);

    await tester.runAsync(() => db.close());
  });
}
