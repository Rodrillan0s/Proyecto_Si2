import 'api_client.dart';
import 'token_storage.dart';

class PedidoService {
  static Future<PedidoResult> obtenerCatalogo() async {
    final idEmpresa = await TokenStorage.getEmpresaId();

    if (idEmpresa == null) {
      return PedidoResult(
        success: false,
        message: 'El usuario no tiene empresa asignada',
      );
    }

    final data = await ApiClient.get(
      '/insumos/catalogo?id_empresa=$idEmpresa',
      requiresAuth: true,
    );

    if (data['success'] != true) {
      return PedidoResult(
        success: false,
        message: data['message'] ?? 'No se pudo cargar el catálogo',
      );
    }

    final listado = data['catalogo'] as List<dynamic>? ?? [];

    return PedidoResult(
      success: true,
      message: 'Catálogo cargado correctamente',
      catalogo: listado.map((item) => Insumo.fromJson(item)).toList(),
    );
  }

  static Future<PedidoResult> crearPedido(List<CarritoItem> carrito) async {
    final idUsuario = await TokenStorage.getUserId();
    final idEmpresa = await TokenStorage.getEmpresaId();

    if (idUsuario == null || idEmpresa == null) {
      return PedidoResult(
        success: false,
        message: 'Faltan datos de sesión para crear el pedido',
      );
    }

    if (carrito.isEmpty) {
      return PedidoResult(
        success: false,
        message: 'El carrito está vacío',
      );
    }

    final body = {
      'id_cliente': idUsuario,
      'id_empresa': idEmpresa,
      'detalles': carrito.map((item) => item.toJson()).toList(),
    };

    final data = await ApiClient.post(
      '/pedidos/crear',
      body,
      requiresAuth: true,
    );

    if (data['success'] != true) {
      return PedidoResult(
        success: false,
        message: data['message'] ?? 'No se pudo registrar el pedido',
      );
    }

    final descuentoTotal = _toDouble(data['descuento_total']);
    final nivel = data['nivel_fidelizacion']?.toString() ?? 'SIN NIVEL';

    return PedidoResult(
      success: true,
      message: descuentoTotal > 0
          ? 'Pedido registrado. Descuento $nivel aplicado: Bs. ${descuentoTotal.toStringAsFixed(2)}'
          : data['message'] ?? 'Pedido registrado correctamente',
      nroTransaccion: _toInt(data['nro_transaccion']),
      montoTotal: _toDouble(data['monto_total']),
      subtotalOriginal: _toDouble(data['subtotal_original']),
      descuentoTotal: descuentoTotal,
      porcentajeDescuento: _toDouble(data['porcentaje_descuento']),
      nivelFidelizacion: nivel,
    );
  }

  static Future<PedidoResult> obtenerHistorial() async {
    final idUsuario = await TokenStorage.getUserId();

    if (idUsuario == null) {
      return PedidoResult(
        success: false,
        message: 'No se encontró el usuario de la sesión',
      );
    }

    final data = await ApiClient.get(
      '/pedidos/historial?id_usuario=$idUsuario',
      requiresAuth: true,
    );

    if (data['success'] != true) {
      return PedidoResult(
        success: false,
        message: data['message'] ?? 'No se pudo cargar el historial',
      );
    }

    final listado = data['listado'] as List<dynamic>? ?? [];

    return PedidoResult(
      success: true,
      message: 'Historial cargado correctamente',
      historial: listado.map((item) => PedidoResumen.fromJson(item)).toList(),
    );
  }

  static Future<PedidoResult> obtenerDetalle(int nroTransaccion) async {
    final data = await ApiClient.get(
      '/pedidos/detalle?nro_transaccion=$nroTransaccion',
      requiresAuth: true,
    );

    if (data['success'] != true) {
      return PedidoResult(
        success: false,
        message: data['message'] ?? 'No se pudo cargar el detalle',
      );
    }

    final listado = data['detalles'] as List<dynamic>? ?? [];

    return PedidoResult(
      success: true,
      message: 'Detalle cargado correctamente',
      detalles: listado.map((item) => PedidoDetalle.fromJson(item)).toList(),
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
    return double.tryParse(value.toString()) ?? 0.0;
  }
}

class PedidoResult {
  final bool success;
  final String message;
  final List<Insumo> catalogo;
  final List<PedidoResumen> historial;
  final List<PedidoDetalle> detalles;
  final int nroTransaccion;
  final double montoTotal;
  final double subtotalOriginal;
  final double descuentoTotal;
  final double porcentajeDescuento;
  final String nivelFidelizacion;

  PedidoResult({
    required this.success,
    required this.message,
    this.catalogo = const [],
    this.historial = const [],
    this.detalles = const [],
    this.nroTransaccion = 0,
    this.montoTotal = 0.0,
    this.subtotalOriginal = 0.0,
    this.descuentoTotal = 0.0,
    this.porcentajeDescuento = 0.0,
    this.nivelFidelizacion = 'SIN NIVEL',
  });
}

class Insumo {
  final int idProducto;
  final String nombreProducto;
  final String categoria;
  final String unidadMedida;
  final double precioUnitario;
  final double stockActual;

  Insumo({
    required this.idProducto,
    required this.nombreProducto,
    required this.categoria,
    required this.unidadMedida,
    required this.precioUnitario,
    required this.stockActual,
  });

  factory Insumo.fromJson(Map<String, dynamic> json) {
    return Insumo(
      idProducto: PedidoService._toInt(json['id_producto']),
      nombreProducto: json['nombre_producto']?.toString() ?? '',
      categoria: json['categoria']?.toString() ?? '',
      unidadMedida: json['unidad_medida']?.toString() ?? '',
      precioUnitario: PedidoService._toDouble(json['precio_unitario']),
      stockActual: PedidoService._toDouble(json['stock_actual']),
    );
  }
}

class CarritoItem {
  final Insumo insumo;
  double cantidad;

  CarritoItem({
    required this.insumo,
    required this.cantidad,
  });

  double get subtotal => cantidad * insumo.precioUnitario;

  Map<String, dynamic> toJson() {
    return {
      'id_producto': insumo.idProducto,
      'cantidad': cantidad,
      'precio_unitario': insumo.precioUnitario,
    };
  }
}

class PedidoResumen {
  final int nroTransaccion;
  final String fechaHora;
  final double montoTotal;
  final String estadoTransaccion;

  PedidoResumen({
    required this.nroTransaccion,
    required this.fechaHora,
    required this.montoTotal,
    required this.estadoTransaccion,
  });

  factory PedidoResumen.fromJson(Map<String, dynamic> json) {
    return PedidoResumen(
      nroTransaccion: PedidoService._toInt(json['nro_transaccion']),
      fechaHora: json['fecha_hora']?.toString() ?? '',
      montoTotal: PedidoService._toDouble(json['monto_total']),
      estadoTransaccion: json['estado_transaccion']?.toString() ?? '',
    );
  }
}

class PedidoDetalle {
  final String nombreProducto;
  final double cantidad;
  final double precioVenta;

  PedidoDetalle({
    required this.nombreProducto,
    required this.cantidad,
    required this.precioVenta,
  });

  double get subtotal => cantidad * precioVenta;

  factory PedidoDetalle.fromJson(Map<String, dynamic> json) {
    return PedidoDetalle(
      nombreProducto: json['nombre_producto']?.toString() ?? '',
      cantidad: PedidoService._toDouble(json['cantidad']),
      precioVenta: PedidoService._toDouble(json['precio_venta']),
    );
  }
}
