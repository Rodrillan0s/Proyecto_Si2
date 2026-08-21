import 'api_client.dart';
import 'token_storage.dart';

class RutaService {
  static Future<RutaResult> obtenerMisRutas({String? estado}) async {
    final idChofer = await TokenStorage.getUserId();

    if (idChofer == null) {
      return RutaResult(
        success: false,
        message: 'No se encontró el usuario de la sesión',
      );
    }

    String path = '/logistica/mis-rutas';
    if (estado != null && estado.isNotEmpty) {
      path += '?estado=$estado';
    }

    final data = await ApiClient.get(path, requiresAuth: true);

    if (data['success'] != true) {
      return RutaResult(
        success: false,
        message: data['message'] ?? 'No se pudieron cargar las rutas',
      );
    }

    final listado = data['rutas'] as List<dynamic>? ?? [];

    return RutaResult(
      success: true,
      message: data['message'] ?? 'Rutas cargadas correctamente',
      rutas: listado.map((item) {
        return RutaLogistica.fromJson(item as Map<String, dynamic>);
      }).toList(),
    );
  }

  static Future<RutaResult> confirmarEntrega({
    required int idRuta,
    String? observaciones,
    String? urlEvidenciaImagen,
    String? urlEvidenciaAudio,
  }) async {
    final body = <String, dynamic>{
      'observaciones': observaciones ?? '',
      'url_evidencia_imagen': urlEvidenciaImagen,
      'url_evidencia_audio': urlEvidenciaAudio,
    };

    final data = await ApiClient.post(
      '/logistica/rutas/$idRuta/confirmar-entrega',
      body,
      requiresAuth: true,
    );

    if (data['success'] != true) {
      return RutaResult(
        success: false,
        message: data['message'] ?? 'No se pudo confirmar la entrega',
      );
    }

    return RutaResult(
      success: true,
      message: data['message'] ?? 'Entrega confirmada correctamente',
    );
  }

  static int _toInt(dynamic value) {
    if (value == null) return 0;
    if (value is int) return value;
    if (value is double) return value.toInt();
    return int.tryParse(value.toString()) ?? 0;
  }

  static double _toDouble(dynamic value) {
    if (value == null) return 0.0;
    if (value is double) return value;
    if (value is int) return value.toDouble();
    return double.tryParse(value.toString()) ?? 0.0;
  }
}

class RutaResult {
  final bool success;
  final String message;
  final List<RutaLogistica> rutas;

  RutaResult({
    required this.success,
    required this.message,
    this.rutas = const [],
  });
}

class RutaLogistica {
  final int idRuta;
  final int idTransaccion;
  final int idChofer;
  final int idEmpresa;
  final String origen;
  final String destino;
  final String fechaAsignacion;
  final String fechaEntregaEstimada;
  final String fechaEntregaReal;
  final String estado;
  final String observaciones;
  final String urlEvidenciaImagen;
  final String urlEvidenciaAudio;
  final int nroTransaccion;
  final double montoTotal;
  final String clienteNombre;
  final String clienteDireccion;
  final String clienteTelefono;

  RutaLogistica({
    required this.idRuta,
    required this.idTransaccion,
    required this.idChofer,
    required this.idEmpresa,
    required this.origen,
    required this.destino,
    required this.fechaAsignacion,
    required this.fechaEntregaEstimada,
    required this.fechaEntregaReal,
    required this.estado,
    required this.observaciones,
    required this.urlEvidenciaImagen,
    required this.urlEvidenciaAudio,
    required this.nroTransaccion,
    required this.montoTotal,
    required this.clienteNombre,
    required this.clienteDireccion,
    required this.clienteTelefono,
  });

  factory RutaLogistica.fromJson(Map<String, dynamic> json) {
    return RutaLogistica(
      idRuta: RutaService._toInt(json['id_ruta']),
      idTransaccion: RutaService._toInt(json['id_transaccion']),
      idChofer: RutaService._toInt(json['id_chofer']),
      idEmpresa: RutaService._toInt(json['id_empresa']),
      origen: json['origen']?.toString() ?? '',
      destino: json['destino']?.toString() ?? '',
      fechaAsignacion: json['fecha_asignacion']?.toString() ?? '',
      fechaEntregaEstimada: json['fecha_entrega_estimada']?.toString() ?? '',
      fechaEntregaReal: json['fecha_entrega_real']?.toString() ?? '',
      estado: json['estado']?.toString() ?? 'ASIGNADA',
      observaciones: json['observaciones']?.toString() ?? '',
      urlEvidenciaImagen: json['url_evidencia_imagen']?.toString() ?? '',
      urlEvidenciaAudio: json['url_evidencia_audio']?.toString() ?? '',
      nroTransaccion: RutaService._toInt(json['nro_transaccion']),
      montoTotal: RutaService._toDouble(json['monto_total']),
      clienteNombre: json['cliente_nombre']?.toString() ?? '',
      clienteDireccion: json['cliente_direccion']?.toString() ?? '',
      clienteTelefono: json['cliente_telefono']?.toString() ?? '',
    );
  }
}
