import 'api_client.dart';

class OrdenService {
  static Future<OrdenResult> obtenerOrdenes() async {
    final data = await ApiClient.get(
      '/get-ordenes',
      requiresAuth: true,
    );

    if (data['success'] != true) {
      return OrdenResult(
        success: false,
        message: data['message'] ?? 'No se pudieron cargar las órdenes',
      );
    }

    final listado = data['list_ordenes'] as List<dynamic>? ?? [];

    return OrdenResult(
      success: true,
      message: data['message'] ?? 'Órdenes cargadas correctamente',
      ordenes: listado.map((item) {
        return OrdenTrabajo.fromJson(item as Map<String, dynamic>);
      }).toList(),
    );
  }

  static Future<OrdenResult> actualizarMiOrden({
    required int nroOrden,
    required String estado,
    required String reporteTexto,
    String? urlImagen,
    String? urlAudio,
  }) async {
    final body = {
      'nro_orden': nroOrden,
      'estado': estado,
      'reporte_texto': reporteTexto,
      'url_imagen': urlImagen,
      'url_audio': urlAudio,
    };

    final data = await ApiClient.post(
      '/update-mi-orden',
      body,
      requiresAuth: true,
    );

    if (data['success'] != true) {
      return OrdenResult(
        success: false,
        message: data['message'] ?? 'No se pudo actualizar la orden',
      );
    }

    return OrdenResult(
      success: true,
      message: data['message'] ?? 'Orden actualizada correctamente',
    );
  }

  static int _toInt(dynamic value) {
    if (value == null) return 0;
    if (value is int) return value;
    if (value is double) return value.toInt();

    return int.tryParse(value.toString()) ?? 0;
  }
}

class OrdenResult {
  final bool success;
  final String message;
  final List<OrdenTrabajo> ordenes;

  OrdenResult({
    required this.success,
    required this.message,
    this.ordenes = const [],
  });
}

class OrdenTrabajo {
  final int nroOrden;
  final String tipoTrabajo;
  final String fechaInicio;
  final String fechaFin;
  final String estado;
  final int idCampana;
  final int idSupervisor;
  final String supervisorUsername;
  final int idEmpleado;
  final String empleadoUsername;
  final String reporteTexto;
  final String urlImagen;
  final String urlAudio;

  OrdenTrabajo({
    required this.nroOrden,
    required this.tipoTrabajo,
    required this.fechaInicio,
    required this.fechaFin,
    required this.estado,
    required this.idCampana,
    required this.idSupervisor,
    required this.supervisorUsername,
    required this.idEmpleado,
    required this.empleadoUsername,
    required this.reporteTexto,
    required this.urlImagen,
    required this.urlAudio,
  });

  factory OrdenTrabajo.fromJson(Map<String, dynamic> json) {
    return OrdenTrabajo(
      nroOrden: OrdenService._toInt(json['nro_orden']),
      tipoTrabajo: json['tipo_trabajo']?.toString() ?? '',
      fechaInicio: json['fecha_inicio']?.toString() ?? '',
      fechaFin: json['fecha_fin']?.toString() ?? '',
      estado: json['estado']?.toString() ?? 'PENDIENTE',
      idCampana: OrdenService._toInt(json['id_campana']),
      idSupervisor: OrdenService._toInt(json['id_supervisor']),
      supervisorUsername: json['supervisor_username']?.toString() ?? '',
      idEmpleado: OrdenService._toInt(json['id_empleado']),
      empleadoUsername: json['empleado_username']?.toString() ?? '',
      reporteTexto: json['reporte_texto']?.toString() ?? '',
      urlImagen: json['url_imagen']?.toString() ?? '',
      urlAudio: json['url_audio']?.toString() ?? '',
    );
  }
}