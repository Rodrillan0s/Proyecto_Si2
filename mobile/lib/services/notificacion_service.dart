import 'dart:async';
import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../config/app_config.dart';
import 'api_client.dart';
import 'token_storage.dart';

class NotificacionService extends ChangeNotifier {
  static const String _basePath = '/api/ws';

  /// Singleton reactivo para conexión Push en tiempo real (WebSocket + Sondeo).
  static final NotificacionService instance = NotificacionService._internal();

  NotificacionService._internal();

  factory NotificacionService() => instance;

  WebSocketChannel? _channel;
  StreamSubscription? _wsSubscription;
  Timer? _reconnectTimer;
  Timer? _pingTimer;
  Timer? _pollTimer;

  bool _isConnected = false;
  bool _isConnecting = false;
  bool _manualDisconnect = false;
  List<Map<String, dynamic>> _notificaciones = [];
  final Set<int> _notifiedIds = <int>{};
  bool _initialLoadCompleted = false;

  final StreamController<Map<String, dynamic>> _incomingPushController =
      StreamController<Map<String, dynamic>>.broadcast();

  bool get isConnected => _isConnected;
  List<Map<String, dynamic>> get notificaciones =>
      List.unmodifiable(_notificaciones);
  Stream<Map<String, dynamic>> get incomingPushStream =>
      _incomingPushController.stream;

  int get unreadCount {
    int count = 0;
    for (final n in _notificaciones) {
      if (!esLeidoValor(n['leido'])) count++;
    }
    return count;
  }

  static bool esLeidoValor(dynamic value) {
    if (value is bool) return value;
    final texto = value?.toString().toLowerCase().trim();
    return texto == 'true' || texto == '1' || texto == 'si';
  }

  /// Inicia la sincronización del historial y abre el canal WebSocket Push.
  Future<void> connectAndSync() async {
    _manualDisconnect = false;
    final token = await TokenStorage.getToken();
    if (token == null || token.trim().isEmpty) return;
    await sincronizarSilencioso();
    await _connectWebSocket();
    _startPollingFallback();
  }

  /// Cierra la conexión WebSocket y limpia el estado al cerrar sesión.
  void disconnect() {
    _manualDisconnect = true;
    _isConnected = false;
    _isConnecting = false;
    _reconnectTimer?.cancel();
    _reconnectTimer = null;
    _pingTimer?.cancel();
    _pingTimer = null;
    _pollTimer?.cancel();
    _pollTimer = null;
    _wsSubscription?.cancel();
    _wsSubscription = null;
    try {
      _channel?.sink.close();
    } catch (_) {}
    _channel = null;
    _notificaciones = [];
    _notifiedIds.clear();
    _initialLoadCompleted = false;
    notifyListeners();
  }

  Future<void> _connectWebSocket() async {
    if (_isConnected || _isConnecting || _manualDisconnect) return;
    _isConnecting = true;

    try {
      final token = await TokenStorage.getToken();
      if (token == null || token.trim().isEmpty) {
        _isConnecting = false;
        return;
      }

      final customUrl = await TokenStorage.getValue('custom_api_url');
      final httpBase = AppConfig.resolveBaseUrl(customUrl);
      final wsBase = AppConfig.wsBaseUrlFrom(httpBase);
      final uri = Uri.parse(
        '$wsBase$_basePath/notificaciones?token=${Uri.encodeQueryComponent(token.trim())}',
      );

      final channel = WebSocketChannel.connect(uri);
      _channel = channel;

      _wsSubscription?.cancel();
      _wsSubscription = channel.stream.listen(
        (dynamic rawMessage) {
          _isConnected = true;
          _isConnecting = false;
          _handleIncomingWebSocketPayload(rawMessage);
        },
        onError: (_) {
          _isConnected = false;
          _isConnecting = false;
          notifyListeners();
          _scheduleReconnect();
        },
        onDone: () {
          _isConnected = false;
          _isConnecting = false;
          notifyListeners();
          if (!_manualDisconnect) {
            _scheduleReconnect();
          }
        },
        cancelOnError: true,
      );

      _isConnected = true;
      _isConnecting = false;
      _startPingKeepAlive();
      notifyListeners();
    } catch (_) {
      _isConnected = false;
      _isConnecting = false;
      notifyListeners();
      _scheduleReconnect();
    }
  }

  void _startPingKeepAlive() {
    _pingTimer?.cancel();
    _pingTimer = Timer.periodic(const Duration(seconds: 25), (_) {
      if (_isConnected && _channel != null) {
        try {
          _channel!.sink.add('ping');
        } catch (_) {}
      }
    });
  }

  void _startPollingFallback() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 25), (_) {
      if (!_manualDisconnect) {
        sincronizarSilencioso();
      }
    });
  }

  void _scheduleReconnect() {
    if (_manualDisconnect) return;
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 6), () {
      if (!_manualDisconnect && !_isConnected) {
        _connectWebSocket();
      }
    });
  }

  void _handleIncomingWebSocketPayload(dynamic rawMessage) {
    if (rawMessage == null) return;
    try {
      final decoded = rawMessage is String
          ? jsonDecode(rawMessage)
          : rawMessage;
      if (decoded is! Map) return;
      final map = Map<String, dynamic>.from(decoded);
      if (map['type'] == 'pong') return;

      final normalized = _normalizarItem(map);
      final idNotif = int.tryParse(
        normalized['id_notificacion']?.toString() ?? '',
      );

      if (idNotif != null && idNotif > 0) {
        _notifiedIds.add(idNotif);
        _notificaciones.removeWhere(
          (item) =>
              int.tryParse(item['id_notificacion']?.toString() ?? '') ==
              idNotif,
        );
      }

      _notificaciones = [normalized, ..._notificaciones];
      notifyListeners();
      _incomingPushController.add(normalized);
    } catch (_) {}
  }

  /// Permite inyectar una notificación push en memoria (útil para tests y eventos locales).
  void simulateIncomingPush(Map<String, dynamic> rawAlert) {
    final normalized = _normalizarItem(rawAlert);
    final idNotif = int.tryParse(
      normalized['id_notificacion']?.toString() ?? '',
    );
    if (idNotif != null && idNotif > 0) {
      _notifiedIds.add(idNotif);
      _notificaciones.removeWhere(
        (item) =>
            int.tryParse(item['id_notificacion']?.toString() ?? '') == idNotif,
      );
    }
    _notificaciones = [normalized, ..._notificaciones];
    notifyListeners();
    _incomingPushController.add(normalized);
  }

  /// Emite una notificación push inmediata tras una acción operativa en cualquier módulo.
  void emitLocalPush({
    required String titulo,
    required String cuerpo,
    String tipo = 'OBRA',
  }) {
    final now = DateTime.now();
    String two(int n) => n.toString().padLeft(2, '0');
    final fechaStr =
        '${now.year}-${two(now.month)}-${two(now.day)} ${two(now.hour)}:${two(now.minute)}:${two(now.second)}';
    simulateIncomingPush({
      'id_notificacion': now.microsecondsSinceEpoch % 1000000000,
      'titulo': titulo,
      'cuerpo': cuerpo,
      'tipo_referencia': tipo,
      'leido': false,
      'fecha_creacion': fechaStr,
    });
  }

  Map<String, dynamic> _normalizarItem(Map<String, dynamic> raw) {
    final tipo = (raw['tipo_referencia'] ??
            raw['tipo_alerta'] ??
            raw['tipo'] ??
            'OBRA')
        .toString()
        .trim();
    final fecha = (raw['fecha_creacion'] ?? raw['created_at'] ?? '')
        .toString()
        .trim();
    final cuerpo = (raw['cuerpo'] ?? raw['mensaje'] ?? '').toString().trim();
    final titulo = (raw['titulo'] ?? 'Notificación OBRATEC').toString().trim();

    return {
      ...raw,
      'id_notificacion': raw['id_notificacion'],
      'titulo': titulo.isEmpty ? 'Notificación OBRATEC' : titulo,
      'cuerpo': cuerpo,
      'mensaje': cuerpo,
      'tipo_referencia': tipo.isEmpty ? 'OBRA' : tipo,
      'tipo': tipo.isEmpty ? 'OBRA' : tipo,
      'leido': esLeidoValor(raw['leido']),
      'fecha_creacion': fecha,
      'created_at': fecha,
    };
  }

  Future<void> sincronizarSilencioso() async {
    try {
      final token = await TokenStorage.getToken();
      if (token == null || token.trim().isEmpty) return;
      await listarMisNotificaciones();
    } catch (_) {}
  }

  Future<List<Map<String, dynamic>>> listarMisNotificaciones() async {
    try {
      final response = await ApiClient.dio.get('$_basePath/historial');
      final data = response.data;

      if (data is! Map) {
        throw Exception('Respuesta inválida del servidor.');
      }

      if (data['success'] != true) {
        throw Exception(
          data['message'] ?? 'No se pudieron cargar las notificaciones.',
        );
      }

      final lista = data['data'] as List? ?? [];
      final normalizadas = lista
          .whereType<Map>()
          .map((item) => _normalizarItem(Map<String, dynamic>.from(item)))
          .toList();

      // Si ya se completó la carga inicial y aparecen alertas no leídas nuevas
      // por polling (p. ej. tras reconexión móvil), disparar el banner push.
      if (_initialLoadCompleted) {
        for (final item in normalizadas.reversed) {
          final id = int.tryParse(item['id_notificacion']?.toString() ?? '');
          if (id != null &&
              id > 0 &&
              !_notifiedIds.contains(id) &&
              !esLeidoValor(item['leido'])) {
            _notifiedIds.add(id);
            _incomingPushController.add(item);
          }
        }
      } else {
        for (final item in normalizadas) {
          final id = int.tryParse(item['id_notificacion']?.toString() ?? '');
          if (id != null && id > 0) {
            _notifiedIds.add(id);
          }
        }
        _initialLoadCompleted = true;
      }

      _notificaciones = normalizadas;
      notifyListeners();
      return normalizadas;
    } on DioException catch (e) {
      throw Exception(_parsearErrorDio(e));
    }
  }

  Future<Map<String, dynamic>> marcarComoLeida({
    required int idNotificacion,
  }) async {
    try {
      final response = await ApiClient.dio.put(
        '$_basePath/leer',
        data: {
          'id_notificacion': idNotificacion,
          'marcar_todo': false,
        },
      );

      final data = response.data;

      if (data is! Map) {
        throw Exception('Respuesta inválida del servidor.');
      }

      if (data['success'] != true) {
        throw Exception(
          data['message'] ?? 'No se pudo marcar la notificación como leída.',
        );
      }

      _notificaciones = _notificaciones.map((item) {
        final id = int.tryParse(item['id_notificacion']?.toString() ?? '');
        if (id == idNotificacion) {
          return {...item, 'leido': true};
        }
        return item;
      }).toList();
      notifyListeners();

      return Map<String, dynamic>.from(data);
    } on DioException catch (e) {
      throw Exception(_parsearErrorDio(e));
    }
  }

  Future<Map<String, dynamic>> marcarTodasComoLeidas() async {
    try {
      final response = await ApiClient.dio.put(
        '$_basePath/leer',
        data: {
          'marcar_todo': true,
        },
      );

      final data = response.data;

      if (data is! Map) {
        throw Exception('Respuesta inválida del servidor.');
      }

      if (data['success'] != true) {
        throw Exception(
          data['message'] ?? 'No se pudieron marcar las notificaciones.',
        );
      }

      _notificaciones = _notificaciones
          .map((item) => {...item, 'leido': true})
          .toList();
      notifyListeners();

      return Map<String, dynamic>.from(data);
    } on DioException catch (e) {
      throw Exception(_parsearErrorDio(e));
    }
  }

  Future<Map<String, dynamic>> enviarNotificacionPrueba({
    String? titulo,
    String? cuerpo,
    String tipo = 'OBRA',
  }) async {
    try {
      final response = await ApiClient.dio.post(
        '$_basePath/prueba',
        data: {
          if (titulo != null && titulo.trim().isNotEmpty)
            'titulo': titulo.trim(),
          if (cuerpo != null && cuerpo.trim().isNotEmpty)
            'cuerpo': cuerpo.trim(),
          'tipo': tipo,
        },
      );
      final data = response.data;
      if (data is Map) {
        await sincronizarSilencioso();
        return Map<String, dynamic>.from(data);
      }
      return {'success': true};
    } on DioException catch (e) {
      throw Exception(_parsearErrorDio(e));
    }
  }

  String _parsearErrorDio(DioException e) {
    if (e.response?.data != null) {
      final data = e.response!.data;

      if (data is Map && data['detail'] is List) {
        final errores = data['detail'] as List;

        return errores.map((err) {
          if (err is Map && err['msg'] != null) {
            return err['msg'].toString();
          }

          return err.toString();
        }).join('\n');
      }

      if (data is Map && data['detail'] != null) {
        return data['detail'].toString();
      }

      if (data is Map && data['message'] != null) {
        return data['message'].toString();
      }
    }

    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.sendTimeout:
        return 'Tiempo de espera agotado. Verificá tu conexión.';
      case DioExceptionType.connectionError:
        return 'No se pudo conectar al servidor.';
      default:
        break;
    }

    switch (e.response?.statusCode) {
      case 400:
        return 'Datos inválidos.';
      case 401:
        return 'Tu sesión expiró. Iniciá sesión nuevamente.';
      case 403:
        return 'No tienes permiso para esta acción.';
      case 404:
        return 'Servicio no encontrado.';
      case 500:
        return 'Error interno del servidor.';
      default:
        return 'Ocurrió un error inesperado.';
    }
  }
}
