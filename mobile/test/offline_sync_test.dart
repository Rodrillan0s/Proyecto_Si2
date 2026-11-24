import 'dart:io';

import 'package:emergencias_vehiculares/services/offline_db_service.dart';
import 'package:emergencias_vehiculares/services/offline_sync_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

void main() {
  sqfliteFfiInit();

  late Directory tempDir;
  late String dbPath;

  setUp(() async {
    tempDir = await Directory.systemTemp.createTemp('obratec_cu41_test_');
    dbPath = p.join(tempDir.path, 'cu41_offline.db');
  });

  tearDown(() async {
    if (await tempDir.exists()) {
      await tempDir.delete(recursive: true);
    }
  });

  test('Día 1 precarga con red -> Día 2 abre sin conexión (tras cerrar/reiniciar) -> consulta obras y unidades y registra offline -> Día 3 sincroniza automáticamente', () async {
    bool online = true;
    final serverAvances = <String, Map<String, dynamic>>{};
    final serverIncidencias = <String, Map<String, dynamic>>{};
    int avanceSeq = 100;
    int incSeq = 500;

    OfflineSyncService crearSync(OfflineDbService db) {
      return OfflineSyncService(
        db: db,
        checkConnectivity: () async => online,
        sendAvance: ({
          required int idObra,
          required Map<String, dynamic> payload,
          required String idempotencyKey,
          required String fechaOcurrenciaLocal,
        }) async {
          if (serverAvances.containsKey(idempotencyKey)) {
            return serverAvances[idempotencyKey]!;
          }
          avanceSeq++;
          final resp = {
            'success': true,
            'id_avance': avanceSeq,
            'fecha_ocurrencia_local': fechaOcurrenciaLocal,
            'fecha_sincronizacion': '2026-11-26T10:00:00Z',
          };
          serverAvances[idempotencyKey] = resp;
          return resp;
        },
        sendIncidencia: ({
          required Map<String, dynamic> payload,
          required String idempotencyKey,
          required String fechaOcurrenciaLocal,
        }) async {
          if (serverIncidencias.containsKey(idempotencyKey)) {
            return serverIncidencias[idempotencyKey]!;
          }
          incSeq++;
          final resp = {
            'success': true,
            'id_incidencia': incSeq,
            'fecha_ocurrencia_local': fechaOcurrenciaLocal,
            'fecha_sincronizacion': '2026-11-26T10:01:00Z',
          };
          serverIncidencias[idempotencyKey] = resp;
          return resp;
        },
      );
    }

    // ── DÍA 1: App abierta con conexión, precarga obras y unidades ───────────
    final dbDia1 = OfflineDbService(databaseFactory: databaseFactoryFfi, dbPath: dbPath);
    final syncDia1 = crearSync(dbDia1);
    await syncDia1.inicializarContexto(idEmpresa: 3, userKey: 'u:jefe@laroca.bo', activarObservadores: false);
    await syncDia1.precargarDatosObra(
      idEmpresa: 3,
      userKey: 'u:jefe@laroca.bo',
      fetcherObras: () async => [
        {'id_obra': 10, 'codigo': 'OB-010', 'nombre': 'Torre Sky'},
      ],
      fetcherUnidades: (idObra) async => [
        {'id_unidad': 77, 'codigo': 'U-101', 'nombre': 'Dpto 101', 'id_obra': idObra},
      ],
    );
    // Simular cierre completo de app / reinicio de dispositivo
    await dbDia1.close();

    // ── DÍA 2: Abrir la app SIN CONEXIÓN usando la copia local descargada ────
    online = false;
    final dbDia2 = OfflineDbService(databaseFactory: databaseFactoryFfi, dbPath: dbPath);
    final syncDia2 = crearSync(dbDia2);
    await syncDia2.inicializarContexto(idEmpresa: 3, userKey: 'u:jefe@laroca.bo', activarObservadores: false);

    final obrasOffline = await syncDia2.obtenerObrasOfflineFirst(
      idEmpresa: 3,
      userKey: 'u:jefe@laroca.bo',
      fetcherRemoto: () async => throw Exception('No debe llamar red estando offline'),
    );
    expect(obrasOffline.esCopiaLocal, isTrue);
    expect(obrasOffline.ultimaActualizacion, isNotNull);
    expect(obrasOffline.data.length, 1);
    expect(obrasOffline.data.first['nombre'], 'Torre Sky');

    final unidadesOffline = await syncDia2.obtenerUnidadesOfflineFirst(
      idEmpresa: 3,
      userKey: 'u:jefe@laroca.bo',
      idObra: 10,
      fetcherRemoto: (_) async => throw Exception('Sin red'),
    );
    expect(unidadesOffline.esCopiaLocal, isTrue);
    expect(unidadesOffline.data.first['id_unidad'], 77);

    // Registrar avance e incidencia sin conexión
    final opAvance = await syncDia2.registrarAvanceOffline(
      idEmpresa: 3,
      userKey: 'u:jefe@laroca.bo',
      idObra: 10,
      idUnidad: 77,
      porcentajeAvance: 55.0,
      observacion: 'Losa vaciada sin señal',
      fechaOcurrenciaLocal: DateTime.utc(2026, 11, 25, 14, 30),
    );
    final opInc = await syncDia2.registrarIncidenciaOffline(
      idEmpresa: 3,
      userKey: 'u:jefe@laroca.bo',
      idObra: 10,
      idUnidad: 77,
      titulo: 'Humedad en ducto',
      descripcion: 'Se observa filtración menor en piso 2',
      prioridad: 'ALTA',
      fechaOcurrenciaLocal: DateTime.utc(2026, 11, 25, 15, 0),
    );
    expect(opAvance.estado, 'PENDIENTE');
    expect(opInc.estado, 'PENDIENTE');
    expect(syncDia2.pendientesCount, 2);

    // Cerrar y volver a abrir la app SIN CONEXIÓN (persistencia tras reinicio)
    await dbDia2.close();
    final dbDia2Reopen = OfflineDbService(databaseFactory: databaseFactoryFfi, dbPath: dbPath);
    final syncDia2Reopen = crearSync(dbDia2Reopen);
    await syncDia2Reopen.inicializarContexto(idEmpresa: 3, userKey: 'u:jefe@laroca.bo', activarObservadores: false);
    expect(syncDia2Reopen.pendientesCount, 2);
    expect(syncDia2Reopen.sincronizadosCount, 0);

    // ── DÍA 3: Recuperar conexión y sincronizar automáticamente ──────────────
    online = true;
    final resumen = await syncDia2Reopen.sincronizarPendientes();
    expect(resumen.procesados, 2);
    expect(resumen.errores, 0);
    expect(syncDia2Reopen.pendientesCount, 0);
    expect(syncDia2Reopen.sincronizadosCount, 2);
    expect(serverAvances.length, 1);
    expect(serverIncidencias.length, 1);

    // Repetir sincronización no crea duplicados
    final resumenRepetido = await syncDia2Reopen.sincronizarPendientes();
    expect(resumenRepetido.procesados, 0);
    expect(serverAvances.length, 1);
    expect(serverIncidencias.length, 1);

    await dbDia2Reopen.close();
  });

  test('Interrupción durante sincronización conserva registros pendientes y reintenta sin pérdida ni duplicados', () async {
    bool online = true;
    int llamadas = 0;
    final db = OfflineDbService(databaseFactory: databaseFactoryFfi, dbPath: dbPath);
    final sync = OfflineSyncService(
      db: db,
      checkConnectivity: () async => online,
      sendAvance: ({
        required int idObra,
        required Map<String, dynamic> payload,
        required String idempotencyKey,
        required String fechaOcurrenciaLocal,
      }) async {
        llamadas++;
        if (llamadas == 2) {
          throw Exception('Corte de red a mitad de sincronización');
        }
        return {'success': true, 'id_avance': 800 + llamadas};
      },
      sendIncidencia: ({
        required Map<String, dynamic> payload,
        required String idempotencyKey,
        required String fechaOcurrenciaLocal,
      }) async =>
          {'success': true, 'id_incidencia': 900},
    );

    await sync.inicializarContexto(idEmpresa: 3, userKey: 'u:sup@laroca.bo', activarObservadores: false);
    await sync.registrarAvanceOffline(
      idEmpresa: 3,
      userKey: 'u:sup@laroca.bo',
      idObra: 10,
      idUnidad: 1,
      porcentajeAvance: 20,
    );
    await sync.registrarAvanceOffline(
      idEmpresa: 3,
      userKey: 'u:sup@laroca.bo',
      idObra: 10,
      idUnidad: 2,
      porcentajeAvance: 30,
    );

    // Primera sincronización: 1ro pasa, 2do sufre corte de red
    final r1 = await sync.sincronizarPendientes();
    expect(r1.procesados, 1);
    expect(r1.errores, 1);
    expect(sync.sincronizadosCount, 1);
    expect(sync.pendientesCount, 1);

    // Segunda sincronización: completa el pendiente sin duplicar el 1ro
    final r2 = await sync.sincronizarPendientes();
    expect(r2.procesados, 1);
    expect(r2.errores, 0);
    expect(sync.sincronizadosCount, 2);
    expect(sync.pendientesCount, 0);

    await db.close();
  });

  test('Aislamiento estricto multi-tenant y por usuario: cambiar de empresa o usuario no expone datos ajenos', () async {
    final db = OfflineDbService(databaseFactory: databaseFactoryFfi, dbPath: dbPath);
    final sync = OfflineSyncService(db: db, checkConnectivity: () async => false);

    // Usuario A de Empresa 3 guarda caché y encola operación
    await db.guardarCache(
      idEmpresa: 3,
      userKey: 'u:a@empresa3.bo',
      entidad: 'obras',
      clave: 'listado',
      payload: [
        {'id_obra': 30, 'nombre': 'Obra Privada Empresa 3'},
      ],
    );
    await sync.registrarIncidenciaOffline(
      idEmpresa: 3,
      userKey: 'u:a@empresa3.bo',
      idObra: 30,
      titulo: 'Incidencia secreta E3',
      descripcion: 'Solo empresa 3',
      prioridad: 'MEDIA',
    );

    // Cambiar a Usuario B de Empresa 4
    await sync.inicializarContexto(idEmpresa: 4, userKey: 'u:b@empresa4.bo', activarObservadores: false);
    final obrasE4 = await sync.obtenerObrasOfflineFirst(
      idEmpresa: 4,
      userKey: 'u:b@empresa4.bo',
    );
    expect(obrasE4.data, isEmpty);
    expect(sync.items, isEmpty);

    // Cambiar a otro usuario de la misma Empresa 3
    await sync.inicializarContexto(idEmpresa: 3, userKey: 'u:otro@empresa3.bo', activarObservadores: false);
    final obrasOtroU = await sync.obtenerObrasOfflineFirst(
      idEmpresa: 3,
      userKey: 'u:otro@empresa3.bo',
    );
    expect(obrasOtroU.data, isEmpty);
    expect(sync.items, isEmpty);

    await db.close();
  });
}
