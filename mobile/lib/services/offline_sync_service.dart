import 'dart:async';
import 'dart:math';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';
import 'package:flutter/widgets.dart';

import 'api_client.dart';
import 'avance_service.dart';
import 'incidencia_service.dart';
import 'notificacion_service.dart';
import 'obra_service.dart';
import 'offline_db_service.dart';
import 'unidad_service.dart';

typedef ConnectivityCheck = Future<bool> Function();
typedef AvanceRemoteSender = Future<Map<String, dynamic>> Function({
  required int idObra,
  required Map<String, dynamic> payload,
  required String idempotencyKey,
  required String fechaOcurrenciaLocal,
});
typedef IncidenciaRemoteSender = Future<Map<String, dynamic>> Function({
  required Map<String, dynamic> payload,
  required String idempotencyKey,
  required String fechaOcurrenciaLocal,
});

class OfflineReadResult<T> {
  final T data;
  final bool esCopiaLocal;
  final DateTime? ultimaActualizacion;

  const OfflineReadResult({
    required this.data,
    required this.esCopiaLocal,
    this.ultimaActualizacion,
  });
}

class SyncSummary {
  final int procesados;
  final int errores;
  final int pendientesRestantes;
  final bool omitidoPorConcurrencia;

  const SyncSummary({
    required this.procesados,
    required this.errores,
    required this.pendientesRestantes,
    this.omitidoPorConcurrencia = false,
  });
}

/// CU41 – Motor offline-first y sincronización automática (HU90–HU94).
///
/// - Consulta primero SQLite para permitir apertura sin conexión usando la última copia descargada.
/// - Precarga obras y unidades mientras existe conectividad.
/// - Encola avances (HU91) e incidencias (HU92) con identificador único idempotente.
/// - Sincroniza al recuperar conexión y al reanudar la app (WidgetsBindingObserver),
///   protegido contra concurrencia y conservando datos hasta confirmación 2xx del backend.
class OfflineSyncService extends ChangeNotifier with WidgetsBindingObserver {
  static final OfflineSyncService instance = OfflineSyncService();

  final OfflineDbService _db;
  final ConnectivityCheck _checkConnectivity;
  final AvanceRemoteSender _sendAvance;
  final IncidenciaRemoteSender _sendIncidencia;
  final ObraService _obraService;
  final UnidadService _unidadService;

  StreamSubscription<List<ConnectivityResult>>? _connSub;
  bool _isOnline = true;
  bool _sincronizando = false;
  int? _activeEmpresaId;
  String? _activeUserKey;
  DateTime? _ultimaActualizacionCache;
  List<OfflineQueueItem> _items = [];

  OfflineSyncService({
    OfflineDbService? db,
    ConnectivityCheck? checkConnectivity,
    AvanceRemoteSender? sendAvance,
    IncidenciaRemoteSender? sendIncidencia,
    ObraService? obraService,
    UnidadService? unidadService,
  })  : _db = db ?? OfflineDbService(),
        _checkConnectivity = checkConnectivity ?? _defaultCheckConnectivity,
        _obraService = obraService ?? ObraService(),
        _unidadService = unidadService ?? UnidadService(),
        _sendAvance = sendAvance ?? _defaultSendAvance,
        _sendIncidencia = sendIncidencia ?? _defaultSendIncidencia;

  bool get isOnline => _isOnline;
  bool get sincronizando => _sincronizando;
  int? get activeEmpresaId => _activeEmpresaId;
  String? get activeUserKey => _activeUserKey;
  DateTime? get ultimaActualizacionCache => _ultimaActualizacionCache;
  List<OfflineQueueItem> get items => List.unmodifiable(_items);
  int get pendientesCount => _items.where((e) => e.estado == 'PENDIENTE').length;
  int get sincronizadosCount => _items.where((e) => e.estado == 'SINCRONIZADO').length;
  int get erroresCount => _items.where((e) => e.estado == 'ERROR').length;
  bool get tienePendientes => pendientesCount > 0;

  bool _precargandoTodo = false;

  Future<void> guardarHttpCache(String cacheKey, Object payload) async {
    final emp = _activeEmpresaId ?? 0;
    final uKey = _activeUserKey ?? 'anon';
    await _safeGuardarCache(
      idEmpresa: emp,
      userKey: uKey,
      entidad: 'http_get',
      clave: cacheKey,
      payload: payload,
    );
  }

  Future<dynamic> leerHttpCache(String cacheKey) async {
    final emp = _activeEmpresaId ?? 0;
    final uKey = _activeUserKey ?? 'anon';
    final entry = await _safeObtenerCache(
      idEmpresa: emp,
      userKey: uKey,
      entidad: 'http_get',
      clave: cacheKey,
    );
    return entry?.payload;
  }

  /// Precarga en segundo plano todos los módulos operativos clave en SQLite
  /// para que la app muestre obras, incidencias, órdenes de trabajo, avances,
  /// materiales, notificaciones, CRM y reportes al quedar sin conexión.
  Future<void> precargarTodoOffline({
    required int idEmpresa,
    required String userKey,
    bool esCliente = false,
  }) async {
    if (_precargandoTodo) return;
    _activeEmpresaId = idEmpresa;
    _activeUserKey = userKey;
    final online = await _checkConnectivity();
    _isOnline = online;
    if (!online) return;

    _precargandoTodo = true;
    try {
      Future<void> warm(String path, {Map<String, dynamic>? query}) async {
        try {
          await ApiClient.dio.get(path, queryParameters: query);
        } catch (_) {}
      }

      // 1. Precargar obras y sus detalles/unidades/avances
      await precargarDatosObra(idEmpresa: idEmpresa, userKey: userKey);
      List<dynamic> obras = [];
      try {
        final r = await ApiClient.dio.get('/api/proyectos/');
        if (r.data is List) {
          obras = r.data as List;
        } else if (r.data is Map && r.data['data'] is List) {
          obras = r.data['data'] as List;
        }
      } catch (_) {}

      // 2. Módulos transversales (se guardan automáticamente vía interceptor SQLite de ApiClient)
      final endpointsGlobales = <String>[
        '/api/ws/historial',
        '/api/proyectos/tipos',
        '/api/reportes/catalogo',
        '/api/incidencias/',
        '/api/ordenes-trabajo/',
        '/api/materiales/',
        '/api/materiales/categorias',
        '/api/consultas-tecnicas/',
        if (esCliente) '/api/crm/cliente/unidades' else '/api/crm/clientes',
        if (!esCliente) '/api/usuarios/',
      ];
      for (final ep in endpointsGlobales) {
        await warm(ep);
      }

      // 3. Detalles por obra (top 10 obras activas para no saturar red móvil)
      for (final o in obras.take(10)) {
        if (o is! Map) continue;
        final idObra = int.tryParse(o['id_obra']?.toString() ?? '');
        if (idObra == null) continue;
        await warm('/api/proyectos/$idObra');
        await warm('/api/proyectos/$idObra/unidades');
        await warm('/api/proyectos/$idObra/estructuras');
        await warm('/api/proyectos/$idObra/avances');
        await warm('/api/proyectos/$idObra/avances/resumen');
        await warm('/api/incidencias/', query: {'id_obra': idObra});
        await warm('/api/ordenes-trabajo/', query: {'id_obra': idObra});
      }

      _ultimaActualizacionCache = DateTime.now().toUtc();
      notifyListeners();
    } finally {
      _precargandoTodo = false;
    }
  }

  static Future<bool> _defaultCheckConnectivity() async {
    try {
      final result = await Connectivity().checkConnectivity();
      if (result.isEmpty) return true;
      return result.any((r) => r != ConnectivityResult.none);
    } catch (_) {
      return true;
    }
  }

  Future<OfflineCacheEntry?> _safeObtenerCache({
    required int idEmpresa,
    required String userKey,
    required String entidad,
    required String clave,
  }) async {
    try {
      return await _db.obtenerCache(
        idEmpresa: idEmpresa,
        userKey: userKey,
        entidad: entidad,
        clave: clave,
      );
    } catch (_) {
      return null;
    }
  }

  Future<void> _safeGuardarCache({
    required int idEmpresa,
    required String userKey,
    required String entidad,
    required String clave,
    required Object payload,
    DateTime? updatedAt,
  }) async {
    try {
      await _db.guardarCache(
        idEmpresa: idEmpresa,
        userKey: userKey,
        entidad: entidad,
        clave: clave,
        payload: payload,
        updatedAt: updatedAt,
      );
    } catch (_) {}
  }

  static Future<Map<String, dynamic>> _defaultSendAvance({
    required int idObra,
    required Map<String, dynamic> payload,
    required String idempotencyKey,
    required String fechaOcurrenciaLocal,
  }) {
    return AvanceService().registrarAvance(
      idObra: idObra,
      idUnidad: (payload['id_unidad'] as num).toInt(),
      porcentajeAvance: (payload['porcentaje_avance'] as num).toDouble(),
      observacion: payload['observacion']?.toString(),
      fechaRegistro: payload['fecha_registro']?.toString(),
      idempotencyKey: idempotencyKey,
      fechaOcurrenciaLocal: fechaOcurrenciaLocal,
    );
  }

  static Future<Map<String, dynamic>> _defaultSendIncidencia({
    required Map<String, dynamic> payload,
    required String idempotencyKey,
    required String fechaOcurrenciaLocal,
  }) {
    return IncidenciaService().registrar(
      idObra: (payload['id_obra'] as num).toInt(),
      idUnidad: payload['id_unidad'] != null ? (payload['id_unidad'] as num).toInt() : null,
      titulo: payload['titulo'].toString(),
      descripcion: payload['descripcion'].toString(),
      prioridad: payload['prioridad'].toString(),
      ubicacion: payload['ubicacion']?.toString(),
      idempotencyKey: idempotencyKey,
      fechaOcurrenciaLocal: fechaOcurrenciaLocal,
    );
  }

  Future<void> inicializarContexto({
    required int idEmpresa,
    required String userKey,
    bool activarObservadores = true,
  }) async {
    _activeEmpresaId = idEmpresa;
    _activeUserKey = userKey;
    _isOnline = await _checkConnectivity();
    await _refrescarEstadoLocal();

    if (activarObservadores && _connSub == null) {
      WidgetsBinding.instance.addObserver(this);
      _connSub = Connectivity().onConnectivityChanged.listen((results) async {
        final onlineAhora = results.any((r) => r != ConnectivityResult.none);
        final recuperoConexion = !_isOnline && onlineAhora;
        _isOnline = onlineAhora;
        notifyListeners();
        if (recuperoConexion && _activeEmpresaId != null && _activeUserKey != null) {
          await sincronizarPendientes();
        }
      });
    }
  }

  void limpiarContextoEnMemoria() {
    _activeEmpresaId = null;
    _activeUserKey = null;
    _items = [];
    _ultimaActualizacionCache = null;
    notifyListeners();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed && _activeEmpresaId != null && _activeUserKey != null) {
      _checkConnectivity().then((online) async {
        _isOnline = online;
        notifyListeners();
        if (online) {
          await sincronizarPendientes();
        }
      });
    }
  }

  @override
  void dispose() {
    _connSub?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  Future<void> _refrescarEstadoLocal() async {
    if (_activeEmpresaId == null || _activeUserKey == null) return;
    _items = await _db.listarCola(
      idEmpresa: _activeEmpresaId!,
      userKey: _activeUserKey!,
    );
    _ultimaActualizacionCache = await _db.obtenerUltimaActualizacion(
      idEmpresa: _activeEmpresaId!,
      userKey: _activeUserKey!,
    );
    notifyListeners();
  }

  String _generarOperationId(String prefijo) {
    final rnd = Random.secure();
    final bytes = List<int>.generate(8, (_) => rnd.nextInt(256));
    final hex = bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
    return '$prefijo-${DateTime.now().toUtc().microsecondsSinceEpoch}-$hex';
  }

  // ── HU90: PRECARGA Y LECTURA OFFLINE-FIRST ────────────────────────────────

  /// Precarga obras y sus unidades en SQLite mientras hay conectividad (escenario Día 1).
  Future<void> precargarDatosObra({
    required int idEmpresa,
    required String userKey,
    Future<List<Map<String, dynamic>>> Function()? fetcherObras,
    Future<List<Map<String, dynamic>>> Function(int idObra)? fetcherUnidades,
  }) async {
    final online = await _checkConnectivity();
    _isOnline = online;
    if (!online) return;

    final obras = await (fetcherObras ?? _obraService.listarProyectos)();
    await _db.guardarCache(
      idEmpresa: idEmpresa,
      userKey: userKey,
      entidad: 'obras',
      clave: 'listado',
      payload: obras,
    );

    for (final obra in obras) {
      final idObra = int.tryParse(obra['id_obra']?.toString() ?? '');
      if (idObra == null) continue;
      await _db.guardarCache(
        idEmpresa: idEmpresa,
        userKey: userKey,
        entidad: 'obra_detalle',
        clave: 'obra_$idObra',
        payload: obra,
      );
      try {
        final unidades = await (fetcherUnidades ?? _unidadService.listarUnidades)(idObra);
        await _db.guardarCache(
          idEmpresa: idEmpresa,
          userKey: userKey,
          entidad: 'unidades',
          clave: 'obra_$idObra',
          payload: unidades,
        );
      } catch (_) {
        // No abortar precarga completa si una obra individual falla
      }
    }
    await _refrescarEstadoLocal();
  }

  /// Consulta obras en modo offline-first: si no hay red (o falla), devuelve la última copia SQLite.
  Future<OfflineReadResult<List<Map<String, dynamic>>>> obtenerObrasOfflineFirst({
    required int idEmpresa,
    required String userKey,
    Future<List<Map<String, dynamic>>> Function()? fetcherRemoto,
    bool forzarRefresco = false,
  }) async {
    final cached = await _safeObtenerCache(
      idEmpresa: idEmpresa,
      userKey: userKey,
      entidad: 'obras',
      clave: 'listado',
    );
    final online = await _checkConnectivity();
    _isOnline = online;

    if (!online) {
      final lista = _toListOfMaps(cached?.payload);
      return OfflineReadResult(
        data: lista,
        esCopiaLocal: true,
        ultimaActualizacion: cached?.updatedAt,
      );
    }

    // Actualización incremental: si tenemos caché reciente (< 2 min) y no se fuerza, retornar local
    if (!forzarRefresco &&
        cached != null &&
        DateTime.now().toUtc().difference(cached.updatedAt).inMinutes < 2) {
      return OfflineReadResult(
        data: _toListOfMaps(cached.payload),
        esCopiaLocal: false,
        ultimaActualizacion: cached.updatedAt,
      );
    }

    try {
      final remotas = await (fetcherRemoto ?? _obraService.listarProyectos)();
      final ahora = DateTime.now().toUtc();
      await _safeGuardarCache(
        idEmpresa: idEmpresa,
        userKey: userKey,
        entidad: 'obras',
        clave: 'listado',
        payload: remotas,
        updatedAt: ahora,
      );
      _ultimaActualizacionCache = ahora;
      notifyListeners();
      return OfflineReadResult(
        data: remotas,
        esCopiaLocal: false,
        ultimaActualizacion: ahora,
      );
    } catch (_) {
      if (cached != null || !online) {
        return OfflineReadResult(
          data: _toListOfMaps(cached?.payload),
          esCopiaLocal: true,
          ultimaActualizacion: cached?.updatedAt,
        );
      }
      rethrow;
    }
  }

  Future<OfflineReadResult<List<Map<String, dynamic>>>> obtenerUnidadesOfflineFirst({
    required int idEmpresa,
    required String userKey,
    required int idObra,
    Future<List<Map<String, dynamic>>> Function(int idObra)? fetcherRemoto,
  }) async {
    final cached = await _safeObtenerCache(
      idEmpresa: idEmpresa,
      userKey: userKey,
      entidad: 'unidades',
      clave: 'obra_$idObra',
    );
    final online = await _checkConnectivity();
    _isOnline = online;

    if (!online) {
      return OfflineReadResult(
        data: _toListOfMaps(cached?.payload),
        esCopiaLocal: true,
        ultimaActualizacion: cached?.updatedAt,
      );
    }

    try {
      final remotas = await (fetcherRemoto ?? _unidadService.listarUnidades)(idObra);
      final ahora = DateTime.now().toUtc();
      await _safeGuardarCache(
        idEmpresa: idEmpresa,
        userKey: userKey,
        entidad: 'unidades',
        clave: 'obra_$idObra',
        payload: remotas,
        updatedAt: ahora,
      );
      return OfflineReadResult(
        data: remotas,
        esCopiaLocal: false,
        ultimaActualizacion: ahora,
      );
    } catch (_) {
      if (cached != null || !online) {
        return OfflineReadResult(
          data: _toListOfMaps(cached?.payload),
          esCopiaLocal: true,
          ultimaActualizacion: cached?.updatedAt,
        );
      }
      rethrow;
    }
  }

  Future<OfflineReadResult<Map<String, dynamic>>> obtenerDetalleObraOfflineFirst({
    required int idEmpresa,
    required String userKey,
    required int idObra,
    Future<Map<String, dynamic>> Function(int idObra)? fetcherRemoto,
    Map<String, dynamic>? fallbackLocal,
  }) async {
    final cached = await _db.obtenerCache(
      idEmpresa: idEmpresa,
      userKey: userKey,
      entidad: 'obra_detalle',
      clave: 'obra_$idObra',
    );
    final online = await _checkConnectivity();
    _isOnline = online;

    if (!online) {
      if (cached != null && cached.payload is Map) {
        return OfflineReadResult(
          data: Map<String, dynamic>.from(cached.payload as Map),
          esCopiaLocal: true,
          ultimaActualizacion: cached.updatedAt,
        );
      }
      return OfflineReadResult(
        data: fallbackLocal ?? <String, dynamic>{},
        esCopiaLocal: true,
        ultimaActualizacion: cached?.updatedAt,
      );
    }

    try {
      final remoto = await (fetcherRemoto ?? _obraService.obtenerDetalleProyecto)(idObra);
      final ahora = DateTime.now().toUtc();
      await _db.guardarCache(
        idEmpresa: idEmpresa,
        userKey: userKey,
        entidad: 'obra_detalle',
        clave: 'obra_$idObra',
        payload: remoto,
        updatedAt: ahora,
      );
      return OfflineReadResult(
        data: remoto,
        esCopiaLocal: false,
        ultimaActualizacion: ahora,
      );
    } catch (_) {
      if (cached != null && cached.payload is Map) {
        return OfflineReadResult(
          data: Map<String, dynamic>.from(cached.payload as Map),
          esCopiaLocal: true,
          ultimaActualizacion: cached.updatedAt,
        );
      }
      if (fallbackLocal != null) {
        return OfflineReadResult(
          data: fallbackLocal,
          esCopiaLocal: true,
          ultimaActualizacion: cached?.updatedAt,
        );
      }
      rethrow;
    }
  }

  Future<OfflineReadResult<List<Map<String, dynamic>>>> obtenerEstructuraOfflineFirst({
    required int idEmpresa,
    required String userKey,
    required int idObra,
    Future<List<Map<String, dynamic>>> Function(int idObra)? fetcherRemoto,
  }) async {
    final cached = await _db.obtenerCache(
      idEmpresa: idEmpresa,
      userKey: userKey,
      entidad: 'estructura',
      clave: 'obra_$idObra',
    );
    final online = await _checkConnectivity();
    _isOnline = online;

    if (!online) {
      return OfflineReadResult(
        data: _toListOfMaps(cached?.payload),
        esCopiaLocal: true,
        ultimaActualizacion: cached?.updatedAt,
      );
    }

    try {
      final remota = await (fetcherRemoto ?? _obraService.obtenerEstructura)(idObra);
      final ahora = DateTime.now().toUtc();
      await _db.guardarCache(
        idEmpresa: idEmpresa,
        userKey: userKey,
        entidad: 'estructura',
        clave: 'obra_$idObra',
        payload: remota,
        updatedAt: ahora,
      );
      return OfflineReadResult(
        data: remota,
        esCopiaLocal: false,
        ultimaActualizacion: ahora,
      );
    } catch (_) {
      if (cached != null) {
        return OfflineReadResult(
          data: _toListOfMaps(cached.payload),
          esCopiaLocal: true,
          ultimaActualizacion: cached.updatedAt,
        );
      }
      rethrow;
    }
  }

  // ── HU91: REGISTRAR AVANCE OFFLINE-FIRST ──────────────────────────────────

  Future<OfflineQueueItem> registrarAvanceOffline({
    required int idEmpresa,
    required String userKey,
    required int idObra,
    required int idUnidad,
    required double porcentajeAvance,
    String? observacion,
    String? fechaRegistro,
    String? clientOperationId,
    DateTime? fechaOcurrenciaLocal,
  }) async {
    final opId = clientOperationId ?? _generarOperationId('cu41-av');
    final ocurrencia = fechaOcurrenciaLocal ?? DateTime.now().toUtc();
    final item = await _db.encolarOperacion(
      clientOperationId: opId,
      idEmpresa: idEmpresa,
      userKey: userKey,
      tipoOperacion: 'AVANCE_OBRA',
      idObra: idObra,
      payload: {
        'id_obra': idObra,
        'id_unidad': idUnidad,
        'porcentaje_avance': porcentajeAvance,
        'observacion': (observacion ?? '').trim(),
        'fecha_registro': fechaRegistro ?? ocurrencia.toIso8601String().substring(0, 10),
      },
      fechaOcurrenciaLocal: ocurrencia,
    );
    await _refrescarEstadoLocal();
    return item;
  }

  // ── HU92: REGISTRAR INCIDENCIA OFFLINE-FIRST ──────────────────────────────

  Future<OfflineQueueItem> registrarIncidenciaOffline({
    required int idEmpresa,
    required String userKey,
    required int idObra,
    int? idUnidad,
    required String titulo,
    required String descripcion,
    required String prioridad,
    String? ubicacion,
    String? clientOperationId,
    DateTime? fechaOcurrenciaLocal,
  }) async {
    final opId = clientOperationId ?? _generarOperationId('cu41-inc');
    final ocurrencia = fechaOcurrenciaLocal ?? DateTime.now().toUtc();
    final item = await _db.encolarOperacion(
      clientOperationId: opId,
      idEmpresa: idEmpresa,
      userKey: userKey,
      tipoOperacion: 'INCIDENCIA',
      idObra: idObra,
      payload: {
        'id_obra': idObra,
        'id_unidad': idUnidad,
        'titulo': titulo.trim(),
        'descripcion': descripcion.trim(),
        'prioridad': prioridad.trim().toUpperCase(),
        'ubicacion': ubicacion?.trim().isEmpty == true ? null : ubicacion?.trim(),
      },
      fechaOcurrenciaLocal: ocurrencia,
    );
    await _refrescarEstadoLocal();
    return item;
  }

  // ── HU93: SINCRONIZACIÓN AUTOMÁTICA CON LOCK E IDEMPOTENCIA ───────────────

  Future<SyncSummary> sincronizarPendientes({
    int? idEmpresa,
    String? userKey,
  }) async {
    final empId = idEmpresa ?? _activeEmpresaId;
    final uKey = userKey ?? _activeUserKey;
    if (empId == null || uKey == null) {
      return const SyncSummary(procesados: 0, errores: 0, pendientesRestantes: 0);
    }
    if (_sincronizando) {
      return SyncSummary(
        procesados: 0,
        errores: 0,
        pendientesRestantes: pendientesCount,
        omitidoPorConcurrencia: true,
      );
    }

    final online = await _checkConnectivity();
    _isOnline = online;
    if (!online) {
      await _refrescarEstadoLocal();
      return SyncSummary(
        procesados: 0,
        errores: 0,
        pendientesRestantes: pendientesCount,
      );
    }

    _sincronizando = true;
    notifyListeners();
    int procesados = 0;
    int errores = 0;

    try {
      final pendientes = await _db.listarCola(
        idEmpresa: empId,
        userKey: uKey,
        estado: 'PENDIENTE',
      );
      for (final op in pendientes) {
        if (!await _checkConnectivity()) {
          _isOnline = false;
          break;
        }
        try {
          Map<String, dynamic> resp;
          if (op.tipoOperacion == 'AVANCE_OBRA') {
            resp = await _sendAvance(
              idObra: op.idObra,
              payload: op.payload,
              idempotencyKey: op.clientOperationId,
              fechaOcurrenciaLocal: op.fechaOcurrenciaLocal,
            );
          } else if (op.tipoOperacion == 'INCIDENCIA') {
            resp = await _sendIncidencia(
              payload: op.payload,
              idempotencyKey: op.clientOperationId,
              fechaOcurrenciaLocal: op.fechaOcurrenciaLocal,
            );
          } else {
            continue;
          }

          if (resp['success'] == true) {
            final idRemoto = (resp['id_avance'] ?? resp['id_incidencia']) as num?;
            await _db.marcarSincronizado(
              idLocal: op.idLocal,
              idEmpresa: empId,
              userKey: uKey,
              idRecursoRemoto: idRemoto?.toInt(),
              fechaSincronizacion: resp['fecha_sincronizacion']?.toString(),
            );
            procesados++;
          } else {
            await _db.registrarIntentoFallido(
              idLocal: op.idLocal,
              idEmpresa: empId,
              userKey: uKey,
              error: resp['error']?.toString() ?? 'Respuesta no confirmada por el servidor.',
              esErrorPermanente: false,
            );
            errores++;
          }
        } on DioException catch (e) {
          final status = e.response?.statusCode;
          final permanente = status != null && status >= 400 && status < 500 && status != 408 && status != 409 && status != 429;
          await _db.registrarIntentoFallido(
            idLocal: op.idLocal,
            idEmpresa: empId,
            userKey: uKey,
            error: e.response?.data is Map
                ? (e.response!.data['detail']?.toString() ?? e.message ?? 'Error HTTP $status')
                : (e.message ?? 'Error de conexión'),
            esErrorPermanente: permanente,
          );
          errores++;
          if (!permanente) break;
        } catch (e) {
          await _db.registrarIntentoFallido(
            idLocal: op.idLocal,
            idEmpresa: empId,
            userKey: uKey,
            error: e.toString().replaceFirst('Exception: ', ''),
            esErrorPermanente: false,
          );
          errores++;
          break;
        }
      }
    } finally {
      _sincronizando = false;
      await _refrescarEstadoLocal();
    }

    if (procesados > 0) {
      NotificacionService.instance.emitLocalPush(
        titulo: 'Sincronización Offline Completada',
        cuerpo: '$procesados operación(es) en cola fueron enviadas al servidor correctamente.',
        tipo: 'OFFLINE_SYNC',
      );
    } else if (errores > 0) {
      NotificacionService.instance.emitLocalPush(
        titulo: 'Pendientes de Sincronización',
        cuerpo: '$errores operación(es) no pudieron sincronizarse. Revisa el estado de sincronización.',
        tipo: 'OFFLINE_SYNC',
      );
    }

    return SyncSummary(
      procesados: procesados,
      errores: errores,
      pendientesRestantes: pendientesCount,
    );
  }

  Future<SyncSummary> reintentarErrores() async {
    if (_activeEmpresaId == null || _activeUserKey == null) {
      return const SyncSummary(procesados: 0, errores: 0, pendientesRestantes: 0);
    }
    await _db.reencolarErrores(
      idEmpresa: _activeEmpresaId!,
      userKey: _activeUserKey!,
    );
    await _refrescarEstadoLocal();
    return sincronizarPendientes();
  }

  List<Map<String, dynamic>> _toListOfMaps(dynamic raw) {
    if (raw is! List) return [];
    return raw.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }
}
