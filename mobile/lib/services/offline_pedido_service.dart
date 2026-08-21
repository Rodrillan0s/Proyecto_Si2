import 'dart:async';
import 'dart:convert';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'pedido_service.dart';

class OfflinePedidoService extends ChangeNotifier {
  OfflinePedidoService._internal();

  static final OfflinePedidoService instance = OfflinePedidoService._internal();

  static const String _pendingOrdersKey = 'pending_orders_offline';

  final Connectivity _connectivity = Connectivity();

  StreamSubscription<dynamic>? _connectivitySubscription;

  bool _isOnline = true;
  bool _syncing = false;
  int _pendingCount = 0;
  String _lastMessage = '';

  bool get isOnline => _isOnline;
  bool get syncing => _syncing;
  int get pendingCount => _pendingCount;
  String get lastMessage => _lastMessage;

  String get statusLabel {
    if (_syncing) return 'SINCRONIZANDO';
    if (!_isOnline) return 'SIN CONEXIÓN';
    if (_pendingCount > 0) return 'PENDIENTES';
    return 'SINCRONIZADO';
  }

  Color get statusColor {
    if (_syncing) return Colors.blue;
    if (!_isOnline) return Colors.orange;
    if (_pendingCount > 0) return Colors.amber;
    return Colors.green;
  }

  Future<void> init() async {
    await refreshPendingCount();
    await checkConnectivity();

    _connectivitySubscription?.cancel();

    _connectivitySubscription = _connectivity.onConnectivityChanged.listen(
      (dynamic result) async {
        final online = _hasConnectivity(result);

        _isOnline = online;
        notifyListeners();

        if (online) {
          await syncPendingOrders();
        } else {
          _lastMessage = 'Sin conexión. Los pedidos se guardarán localmente.';
          notifyListeners();
        }
      },
    );

    if (_isOnline) {
      await syncPendingOrders();
    }
  }

  Future<void> checkConnectivity() async {
    final result = await _connectivity.checkConnectivity();
    _isOnline = _hasConnectivity(result);
    notifyListeners();
  }

  Future<void> refreshPendingCount() async {
    final pending = await getPendingOrders();
    _pendingCount = pending.length;
    notifyListeners();
  }

  Future<PedidoResult> createPedidoOrSaveOffline(List<CarritoItem> carrito) async {
    await checkConnectivity();

    if (!_isOnline) {
      await savePendingOrder(carrito);

      return PedidoResult(
        success: true,
        message: 'Sin conexión. Pedido guardado y se enviará al reconectarse.',
      );
    }

    final result = await PedidoService.crearPedido(carrito);

    if (result.success) {
      _lastMessage = result.descuentoTotal > 0
          ? 'Pedido enviado. Descuento ${result.nivelFidelizacion}: Bs. ${result.descuentoTotal.toStringAsFixed(2)}.'
          : 'Pedido enviado correctamente.';
      await refreshPendingCount();
      return result;
    }

    final shouldSaveOffline = _looksLikeConnectionError(result.message);

    if (shouldSaveOffline) {
      await savePendingOrder(carrito);

      return PedidoResult(
        success: true,
        message: 'No se pudo contactar al servidor. Pedido guardado para envío automático.',
      );
    }

    return result;
  }

  Future<void> savePendingOrder(List<CarritoItem> carrito) async {
    final prefs = await SharedPreferences.getInstance();
    final pending = await getPendingOrders();

    final order = OfflinePedido(
      localId: DateTime.now().millisecondsSinceEpoch.toString(),
      createdAt: DateTime.now().toIso8601String(),
      detalles: carrito.map((item) {
        return OfflinePedidoDetalle(
          idProducto: item.insumo.idProducto,
          nombreProducto: item.insumo.nombreProducto,
          cantidad: item.cantidad,
          precioUnitario: item.insumo.precioUnitario,
        );
      }).toList(),
    );

    pending.add(order);

    final encoded = pending.map((item) => item.toJson()).toList();

    await prefs.setString(_pendingOrdersKey, jsonEncode(encoded));

    _pendingCount = pending.length;
    _lastMessage = 'Pedido guardado localmente.';
    notifyListeners();
  }

  Future<List<OfflinePedido>> getPendingOrders() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_pendingOrdersKey);

    if (raw == null || raw.trim().isEmpty) return [];

    try {
      final decoded = jsonDecode(raw);

      if (decoded is! List) return [];

      return decoded.map((item) {
        return OfflinePedido.fromJson(item as Map<String, dynamic>);
      }).toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> _savePendingOrders(List<OfflinePedido> orders) async {
    final prefs = await SharedPreferences.getInstance();
    final encoded = orders.map((item) => item.toJson()).toList();

    await prefs.setString(_pendingOrdersKey, jsonEncode(encoded));

    _pendingCount = orders.length;
    notifyListeners();
  }

  Future<void> syncPendingOrders() async {
    if (_syncing) return;

    final pending = await getPendingOrders();

    if (pending.isEmpty) {
      _pendingCount = 0;
      _lastMessage = 'No hay pedidos pendientes.';
      notifyListeners();
      return;
    }

    await checkConnectivity();

    if (!_isOnline) {
      _lastMessage = 'No hay conexión para sincronizar.';
      notifyListeners();
      return;
    }

    _syncing = true;
    _lastMessage = 'Enviando pedidos pendientes...';
    notifyListeners();

    final remaining = <OfflinePedido>[];

    for (final order in pending) {
      final carrito = order.detalles.map((detalle) {
        return CarritoItem(
          insumo: Insumo(
            idProducto: detalle.idProducto,
            nombreProducto: detalle.nombreProducto,
            categoria: 'OFFLINE',
            unidadMedida: 'UND',
            precioUnitario: detalle.precioUnitario,
            stockActual: 999999,
          ),
          cantidad: detalle.cantidad,
        );
      }).toList();

      final result = await PedidoService.crearPedido(carrito);

      if (!result.success) {
        remaining.add(order);
      }
    }

    await _savePendingOrders(remaining);

    _syncing = false;

    if (remaining.isEmpty) {
      _lastMessage = 'Pedidos pendientes enviados correctamente.';
    } else {
      _lastMessage = 'Algunos pedidos no pudieron enviarse.';
    }

    notifyListeners();
  }

  bool _looksLikeConnectionError(String message) {
    final text = message.toLowerCase();

    return text.contains('conexión') ||
        text.contains('conexion') ||
        text.contains('servidor') ||
        text.contains('network') ||
        text.contains('socket') ||
        text.contains('timeout');
  }

  bool _hasConnectivity(dynamic result) {
    if (result is ConnectivityResult) {
      return result != ConnectivityResult.none;
    }

    if (result is List<ConnectivityResult>) {
      return result.any((item) => item != ConnectivityResult.none);
    }

    return false;
  }

  @override
  void dispose() {
    _connectivitySubscription?.cancel();
    super.dispose();
  }
}

class OfflinePedido {
  final String localId;
  final String createdAt;
  final List<OfflinePedidoDetalle> detalles;

  OfflinePedido({
    required this.localId,
    required this.createdAt,
    required this.detalles,
  });

  double get total {
    return detalles.fold(
      0.0,
      (sum, item) => sum + item.subtotal,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'local_id': localId,
      'created_at': createdAt,
      'detalles': detalles.map((item) => item.toJson()).toList(),
    };
  }

  factory OfflinePedido.fromJson(Map<String, dynamic> json) {
    final rawDetalles = json['detalles'] as List<dynamic>? ?? [];

    return OfflinePedido(
      localId: json['local_id']?.toString() ?? '',
      createdAt: json['created_at']?.toString() ?? '',
      detalles: rawDetalles.map((item) {
        return OfflinePedidoDetalle.fromJson(item as Map<String, dynamic>);
      }).toList(),
    );
  }
}

class OfflinePedidoDetalle {
  final int idProducto;
  final String nombreProducto;
  final double cantidad;
  final double precioUnitario;

  OfflinePedidoDetalle({
    required this.idProducto,
    required this.nombreProducto,
    required this.cantidad,
    required this.precioUnitario,
  });

  double get subtotal => cantidad * precioUnitario;

  Map<String, dynamic> toJson() {
    return {
      'id_producto': idProducto,
      'nombre_producto': nombreProducto,
      'cantidad': cantidad,
      'precio_unitario': precioUnitario,
    };
  }

  factory OfflinePedidoDetalle.fromJson(Map<String, dynamic> json) {
    return OfflinePedidoDetalle(
      idProducto: _toInt(json['id_producto']),
      nombreProducto: json['nombre_producto']?.toString() ?? '',
      cantidad: _toDouble(json['cantidad']),
      precioUnitario: _toDouble(json['precio_unitario']),
    );
  }

  static int _toInt(dynamic value) {
    if (value is int) return value;
    if (value is double) return value.toInt();

    return int.tryParse(value.toString()) ?? 0;
  }

  static double _toDouble(dynamic value) {
    if (value is double) return value;
    if (value is int) return value.toDouble();

    return double.tryParse(value.toString()) ?? 0;
  }
}
