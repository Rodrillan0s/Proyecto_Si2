import 'package:flutter/material.dart';
import 'package:socket_io_client/socket_io_client.dart' as IO;

import '../config/app_config.dart';
import 'token_storage.dart';

enum SocketConnectionStatus {
  disconnected,
  connecting,
  connected,
  reconnecting,
  error,
}

class NotificationSocketService extends ChangeNotifier {
  NotificationSocketService._internal();

  static final NotificationSocketService instance =
      NotificationSocketService._internal();

  IO.Socket? _socket;

  SocketConnectionStatus _status = SocketConnectionStatus.disconnected;

  String _lastMessage = '';
  String _lastError = '';

  int _unreadCount = 0;
  CrmNotification? _lastNotification;

  SocketConnectionStatus get status => _status;
  String get lastMessage => _lastMessage;
  String get lastError => _lastError;

  int get unreadCount => _unreadCount;
  CrmNotification? get lastNotification => _lastNotification;

  bool get isConnected => _status == SocketConnectionStatus.connected;
  bool get isConnecting => _status == SocketConnectionStatus.connecting;
  bool get hasError => _status == SocketConnectionStatus.error;

  String get statusLabel {
    switch (_status) {
      case SocketConnectionStatus.connected:
        return 'CONECTADO';
      case SocketConnectionStatus.connecting:
        return 'CONECTANDO';
      case SocketConnectionStatus.reconnecting:
        return 'RECONECTANDO';
      case SocketConnectionStatus.error:
        return 'ERROR';
      case SocketConnectionStatus.disconnected:
        return 'DESCONECTADO';
    }
  }

  Color get statusColor {
    switch (_status) {
      case SocketConnectionStatus.connected:
        return Colors.green;
      case SocketConnectionStatus.connecting:
        return Colors.blue;
      case SocketConnectionStatus.reconnecting:
        return Colors.orange;
      case SocketConnectionStatus.error:
        return Colors.red;
      case SocketConnectionStatus.disconnected:
        return Colors.grey;
    }
  }

  Future<void> connect() async {
    if (_status == SocketConnectionStatus.connected ||
        _status == SocketConnectionStatus.connecting) {
      return;
    }

    final token = await TokenStorage.getToken();

    if (token == null || token.isEmpty) {
      _setError('No hay token guardado. Inicia sesión nuevamente.');
      return;
    }

    _disposeCurrentSocket();

    _setStatus(SocketConnectionStatus.connecting);
    _lastError = '';
    _lastMessage = 'Intentando conectar con notificaciones...';

    try {
      _socket = IO.io(
        AppConfig.socketUrl,
        <String, dynamic>{
          'transports': ['websocket'],
          'autoConnect': false,
          'forceNew': true,
          'reconnection': true,
          'reconnectionAttempts': 5,
          'reconnectionDelay': 1500,

          // Tu backend acepta token por auth o por query.
          'auth': {
            'token': token,
          },
          'query': {
            'token': token,
          },
        },
      );

      _registerSocketEvents();

      _socket!.connect();
    } catch (e) {
      _setError('Error creando conexión socket: $e');
    }
  }

  Future<void> reconnect() async {
    disconnect();
    await Future.delayed(const Duration(milliseconds: 300));
    await connect();
  }

  void disconnect() {
    _lastMessage = 'Socket desconectado manualmente.';

    try {
      _socket?.disconnect();
      _socket?.dispose();
    } catch (_) {}

    _socket = null;
    _setStatus(SocketConnectionStatus.disconnected);
  }

  void markNotificationsAsRead() {
    _unreadCount = 0;
    notifyListeners();
  }

  void _registerSocketEvents() {
    final socket = _socket;

    if (socket == null) return;

    socket.onConnect((_) {
      _lastMessage = 'Canal de notificaciones conectado.';
      _lastError = '';
      _setStatus(SocketConnectionStatus.connected);
    });

    socket.onDisconnect((_) {
      _lastMessage = 'Canal de notificaciones desconectado.';
      _setStatus(SocketConnectionStatus.disconnected);
    });

    socket.onConnectError((data) {
      _setError('Error de conexión: ${data.toString()}');
    });

    socket.onError((data) {
      _setError('Error socket: ${data.toString()}');
    });

    socket.on('reconnect_attempt', (_) {
      _lastMessage = 'Intentando reconectar...';
      _setStatus(SocketConnectionStatus.reconnecting);
    });

    socket.on('reconnect_failed', (_) {
      _setError('No se pudo reconectar al canal de notificaciones.');
    });

    // Evento correcto del backend CRM.
    socket.on('nueva_notificacion', (data) {
      _handleCrmNotification(data);
    });

    // Fallback por si en algún lugar quedó mal escrito.
    socket.on('nueva_notifiacion', (data) {
      _handleCrmNotification(data);
    });

    // Otros eventos genéricos que ya tenías.
    socket.on('notificacion', (data) {
      _lastMessage = data.toString();
      notifyListeners();
    });

    socket.on('notification', (data) {
      _lastMessage = data.toString();
      notifyListeners();
    });

    socket.on('orden_actualizada', (data) {
      _lastMessage = data.toString();
      notifyListeners();
    });
  }

  void _handleCrmNotification(dynamic data) {
    final notification = CrmNotification.fromSocket(data);

    _lastNotification = notification;
    _unreadCount++;

    _lastMessage = '${notification.asunto}: ${notification.mensaje}';

    notifyListeners();
  }

  void _setStatus(SocketConnectionStatus newStatus) {
    _status = newStatus;
    notifyListeners();
  }

  void _setError(String error) {
    _lastError = error;
    _lastMessage = error;
    _setStatus(SocketConnectionStatus.error);
  }

  void _disposeCurrentSocket() {
    try {
      _socket?.disconnect();
      _socket?.dispose();
    } catch (_) {}

    _socket = null;
  }
}

class CrmNotification {
  final int localId;
  final String asunto;
  final String mensaje;
  final String canal;
  final String fecha;

  CrmNotification({
    required this.localId,
    required this.asunto,
    required this.mensaje,
    required this.canal,
    required this.fecha,
  });

  factory CrmNotification.fromSocket(dynamic data) {
    if (data is Map) {
      return CrmNotification(
        localId: DateTime.now().millisecondsSinceEpoch,
        asunto: data['asunto']?.toString() ?? 'Notificación',
        mensaje: data['mensaje']?.toString() ?? '',
        canal: data['canal']?.toString() ?? 'CRM',
        fecha: data['fecha']?.toString() ?? '',
      );
    }

    return CrmNotification(
      localId: DateTime.now().millisecondsSinceEpoch,
      asunto: 'Notificación',
      mensaje: data.toString(),
      canal: 'CRM',
      fecha: '',
    );
  }
}