import 'package:dio/dio.dart';
import 'api_client.dart';

class PosventaService {
  final Dio _dio = ApiClient.dio;

  /// HU162: Listar garantías del cliente o empresa
  Future<List<Map<String, dynamic>>> listarGarantias({int? idUnidad}) async {
    try {
      final queryParams = <String, dynamic>{};
      if (idUnidad != null) queryParams['id_unidad'] = idUnidad;

      final res = await _dio.get('/api/posventa/garantias', queryParameters: queryParams);
      if (res.data is List) {
        return List<Map<String, dynamic>>.from(res.data as List);
      }
      return [];
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'Error al cargar garantías';
      throw Exception(msg);
    }
  }

  /// HU167: Listar solicitudes de posventa
  Future<List<Map<String, dynamic>>> listarSolicitudes({String? estado}) async {
    try {
      final queryParams = <String, dynamic>{};
      if (estado != null && estado.isNotEmpty) queryParams['estado'] = estado;

      final res = await _dio.get('/api/posventa/solicitudes', queryParameters: queryParams);
      if (res.data is List) {
        return List<Map<String, dynamic>>.from(res.data as List);
      }
      return [];
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'Error al cargar solicitudes de posventa';
      throw Exception(msg);
    }
  }

  /// HU167: Obtener detalle de solicitud con timeline
  Future<Map<String, dynamic>> obtenerDetalle(int idSolicitud) async {
    try {
      final res = await _dio.get('/api/posventa/solicitudes/$idSolicitud');
      return Map<String, dynamic>.from(res.data as Map);
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'Error al obtener detalle';
      throw Exception(msg);
    }
  }

  /// HU163: Registrar solicitud de posventa (Cliente)
  Future<Map<String, dynamic>> registrarSolicitud({
    required int idUnidad,
    required String titulo,
    required String descripcionDefecto,
    int? idGarantia,
  }) async {
    try {
      final payload = {
        'id_unidad': idUnidad,
        'titulo': titulo.trim(),
        'descripcion_defecto': descripcionDefecto.trim(),
        if (idGarantia != null) 'id_garantia': idGarantia,
      };

      final res = await _dio.post('/api/posventa/solicitudes', data: payload);
      return Map<String, dynamic>.from(res.data as Map);
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'Error al registrar solicitud';
      throw Exception(msg);
    }
  }

  /// HU166: Atender y registrar bitácora (Supervisor)
  Future<Map<String, dynamic>> atenderSolicitud({
    required int idSolicitud,
    required String nuevoEstado,
    required String accionesRealizadas,
    String? materialesUtilizados,
    String? motivoCierre,
  }) async {
    try {
      final payload = {
        'nuevo_estado': nuevoEstado,
        'acciones_realizadas': accionesRealizadas.trim(),
        if (materialesUtilizados != null) 'materiales_utilizados': materialesUtilizados.trim(),
        if (motivoCierre != null) 'motivo_cierre': motivoCierre.trim(),
      };

      final res = await _dio.post('/api/posventa/solicitudes/$idSolicitud/atender', data: payload);
      return Map<String, dynamic>.from(res.data as Map);
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'Error al registrar atención técnica';
      throw Exception(msg);
    }
  }
}
