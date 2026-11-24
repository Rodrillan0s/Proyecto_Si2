import 'dart:convert';
import 'dart:io' show Platform;
import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

/// CU41 – Persistencia local SQLite transaccional (HU90–HU94).
///
/// Reglas de seguridad y aislamiento:
/// - Nunca almacena contraseñas ni tokens JWT.
/// - Todos los registros de caché y cola están particionados por (id_empresa, user_key).
/// - Todas las escrituras y transiciones de estado utilizan transacciones SQLite.
class OfflineDbService {
  static const String _dbName = 'obratec_cu41_offline.db';
  static const int _dbVersion = 1;

  final DatabaseFactory? _factoryOverride;
  final String? _pathOverride;
  Database? _db;

  OfflineDbService({DatabaseFactory? databaseFactory, String? dbPath})
      : _factoryOverride = databaseFactory,
        _pathOverride = dbPath;

  Future<Database> get database async {
    if (_db != null && _db!.isOpen) return _db!;
    if (_factoryOverride == null && (Platform.isWindows || Platform.isLinux || Platform.isMacOS)) {
      throw UnsupportedError('SQLite sin factory FFI no disponible en host de escritorio.');
    }
    final factory = _factoryOverride ?? databaseFactory;
    final dbPath = _pathOverride ?? p.join(await factory.getDatabasesPath(), _dbName);
    _db = await factory.openDatabase(
      dbPath,
      options: OpenDatabaseOptions(
        version: _dbVersion,
        onCreate: (db, version) async {
          await db.execute('''
            CREATE TABLE IF NOT EXISTS offline_cache (
              id_empresa INTEGER NOT NULL,
              user_key TEXT NOT NULL,
              entidad TEXT NOT NULL,
              clave TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              PRIMARY KEY (id_empresa, user_key, entidad, clave)
            );
          ''');
          await db.execute('''
            CREATE TABLE IF NOT EXISTS offline_queue (
              id_local INTEGER PRIMARY KEY AUTOINCREMENT,
              client_operation_id TEXT NOT NULL,
              id_empresa INTEGER NOT NULL,
              user_key TEXT NOT NULL,
              tipo_operacion TEXT NOT NULL,
              id_obra INTEGER NOT NULL,
              payload_json TEXT NOT NULL,
              fecha_ocurrencia_local TEXT NOT NULL,
              estado TEXT NOT NULL,
              intentos INTEGER NOT NULL DEFAULT 0,
              ultimo_error TEXT,
              id_recurso_remoto INTEGER,
              fecha_sincronizacion TEXT,
              UNIQUE (id_empresa, user_key, tipo_operacion, client_operation_id)
            );
          ''');
          await db.execute('''
            CREATE INDEX IF NOT EXISTS idx_offline_queue_scope
            ON offline_queue (id_empresa, user_key, estado, id_local);
          ''');
        },
      ),
    );
    return _db!;
  }

  Future<void> close() async {
    if (_db != null && _db!.isOpen) {
      await _db!.close();
    }
    _db = null;
  }

  // ── CACHÉ LOCAL PARTICIONADO (HU90) ───────────────────────────────────────

  Future<void> guardarCache({
    required int idEmpresa,
    required String userKey,
    required String entidad,
    required String clave,
    required Object payload,
    DateTime? updatedAt,
  }) async {
    final db = await database;
    final stamp = (updatedAt ?? DateTime.now()).toUtc().toIso8601String();
    await db.transaction((txn) async {
      await txn.insert(
        'offline_cache',
        {
          'id_empresa': idEmpresa,
          'user_key': userKey,
          'entidad': entidad,
          'clave': clave,
          'payload_json': jsonEncode(payload),
          'updated_at': stamp,
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    });
  }

  Future<OfflineCacheEntry?> obtenerCache({
    required int idEmpresa,
    required String userKey,
    required String entidad,
    required String clave,
  }) async {
    final db = await database;
    final rows = await db.query(
      'offline_cache',
      where: 'id_empresa = ? AND user_key = ? AND entidad = ? AND clave = ?',
      whereArgs: [idEmpresa, userKey, entidad, clave],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    final row = rows.first;
    return OfflineCacheEntry(
      payload: jsonDecode(row['payload_json'] as String),
      updatedAt: DateTime.tryParse(row['updated_at'] as String) ?? DateTime.now().toUtc(),
    );
  }

  Future<DateTime?> obtenerUltimaActualizacion({
    required int idEmpresa,
    required String userKey,
  }) async {
    final db = await database;
    final rows = await db.rawQuery(
      'SELECT MAX(updated_at) AS max_ts FROM offline_cache WHERE id_empresa = ? AND user_key = ?',
      [idEmpresa, userKey],
    );
    final raw = rows.isNotEmpty ? rows.first['max_ts'] as String? : null;
    return raw != null ? DateTime.tryParse(raw) : null;
  }

  // ── COLA TRANSACCIONAL OFFLINE (HU91, HU92, HU93, HU94) ───────────────────

  Future<OfflineQueueItem> encolarOperacion({
    required String clientOperationId,
    required int idEmpresa,
    required String userKey,
    required String tipoOperacion,
    required int idObra,
    required Map<String, dynamic> payload,
    required DateTime fechaOcurrenciaLocal,
  }) async {
    final db = await database;
    final fechaIso = fechaOcurrenciaLocal.toUtc().toIso8601String();
    return db.transaction((txn) async {
      await txn.insert(
        'offline_queue',
        {
          'client_operation_id': clientOperationId,
          'id_empresa': idEmpresa,
          'user_key': userKey,
          'tipo_operacion': tipoOperacion,
          'id_obra': idObra,
          'payload_json': jsonEncode(payload),
          'fecha_ocurrencia_local': fechaIso,
          'estado': 'PENDIENTE',
          'intentos': 0,
        },
        conflictAlgorithm: ConflictAlgorithm.ignore,
      );
      final rows = await txn.query(
        'offline_queue',
        where: 'id_empresa = ? AND user_key = ? AND tipo_operacion = ? AND client_operation_id = ?',
        whereArgs: [idEmpresa, userKey, tipoOperacion, clientOperationId],
        limit: 1,
      );
      return OfflineQueueItem.fromRow(rows.first);
    });
  }

  Future<List<OfflineQueueItem>> listarCola({
    required int idEmpresa,
    required String userKey,
    String? estado,
  }) async {
    final db = await database;
    final where = estado != null
        ? 'id_empresa = ? AND user_key = ? AND estado = ?'
        : 'id_empresa = ? AND user_key = ?';
    final args = estado != null
        ? [idEmpresa, userKey, estado]
        : [idEmpresa, userKey];
    final rows = await db.query(
      'offline_queue',
      where: where,
      whereArgs: args,
      orderBy: 'id_local ASC',
    );
    return rows.map(OfflineQueueItem.fromRow).toList();
  }

  Future<void> marcarSincronizado({
    required int idLocal,
    required int idEmpresa,
    required String userKey,
    int? idRecursoRemoto,
    String? fechaSincronizacion,
  }) async {
    final db = await database;
    final syncTs = fechaSincronizacion ?? DateTime.now().toUtc().toIso8601String();
    await db.transaction((txn) async {
      await txn.update(
        'offline_queue',
        {
          'estado': 'SINCRONIZADO',
          'ultimo_error': null,
          'id_recurso_remoto': idRecursoRemoto,
          'fecha_sincronizacion': syncTs,
        },
        where: 'id_local = ? AND id_empresa = ? AND user_key = ?',
        whereArgs: [idLocal, idEmpresa, userKey],
      );
    });
  }

  Future<void> registrarIntentoFallido({
    required int idLocal,
    required int idEmpresa,
    required String userKey,
    required String error,
    required bool esErrorPermanente,
  }) async {
    final db = await database;
    await db.transaction((txn) async {
      final rows = await txn.query(
        'offline_queue',
        columns: ['intentos'],
        where: 'id_local = ? AND id_empresa = ? AND user_key = ?',
        whereArgs: [idLocal, idEmpresa, userKey],
        limit: 1,
      );
      if (rows.isEmpty) return;
      final intentos = ((rows.first['intentos'] as int?) ?? 0) + 1;
      await txn.update(
        'offline_queue',
        {
          'estado': esErrorPermanente ? 'ERROR' : 'PENDIENTE',
          'intentos': intentos,
          'ultimo_error': error,
        },
        where: 'id_local = ? AND id_empresa = ? AND user_key = ?',
        whereArgs: [idLocal, idEmpresa, userKey],
      );
    });
  }

  Future<void> reencolarErrores({
    required int idEmpresa,
    required String userKey,
  }) async {
    final db = await database;
    await db.transaction((txn) async {
      await txn.update(
        'offline_queue',
        {'estado': 'PENDIENTE', 'ultimo_error': null},
        where: "id_empresa = ? AND user_key = ? AND estado = 'ERROR'",
        whereArgs: [idEmpresa, userKey],
      );
    });
  }
}

class OfflineCacheEntry {
  final dynamic payload;
  final DateTime updatedAt;

  const OfflineCacheEntry({required this.payload, required this.updatedAt});
}

class OfflineQueueItem {
  final int idLocal;
  final String clientOperationId;
  final int idEmpresa;
  final String userKey;
  final String tipoOperacion;
  final int idObra;
  final Map<String, dynamic> payload;
  final String fechaOcurrenciaLocal;
  final String estado; // PENDIENTE | SINCRONIZADO | ERROR
  final int intentos;
  final String? ultimoError;
  final int? idRecursoRemoto;
  final String? fechaSincronizacion;

  const OfflineQueueItem({
    required this.idLocal,
    required this.clientOperationId,
    required this.idEmpresa,
    required this.userKey,
    required this.tipoOperacion,
    required this.idObra,
    required this.payload,
    required this.fechaOcurrenciaLocal,
    required this.estado,
    required this.intentos,
    this.ultimoError,
    this.idRecursoRemoto,
    this.fechaSincronizacion,
  });

  factory OfflineQueueItem.fromRow(Map<String, Object?> row) {
    return OfflineQueueItem(
      idLocal: row['id_local'] as int,
      clientOperationId: row['client_operation_id'] as String,
      idEmpresa: row['id_empresa'] as int,
      userKey: row['user_key'] as String,
      tipoOperacion: row['tipo_operacion'] as String,
      idObra: row['id_obra'] as int,
      payload: Map<String, dynamic>.from(
        jsonDecode(row['payload_json'] as String) as Map,
      ),
      fechaOcurrenciaLocal: row['fecha_ocurrencia_local'] as String,
      estado: row['estado'] as String,
      intentos: (row['intentos'] as int?) ?? 0,
      ultimoError: row['ultimo_error'] as String?,
      idRecursoRemoto: row['id_recurso_remoto'] as int?,
      fechaSincronizacion: row['fecha_sincronizacion'] as String?,
    );
  }
}
