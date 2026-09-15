import 'package:dio/dio.dart';
import 'api_client.dart';

class OrdenTrabajoService {
  static const String _basePath = '/api/ordenes-trabajo';

  /// Lista órdenes de trabajo con filtros opcionales de empresa y obra
  Future<List<Map<String, dynamic>>> listarOrdenesTrabajo({
    int? idEmpresa,
    int? idObra,
  }) async {
    try {
      final queryParams = <String, dynamic>{};
      if (idEmpresa != null) queryParams['id_empresa'] = idEmpresa;
      if (idObra != null) queryParams['id_obra'] = idObra;

      final response = await ApiClient.dio.get(
        '$_basePath/',
        queryParameters: queryParams.isNotEmpty ? queryParams : null,
      );

      final data = response.data;
      if (data is! Map) {
        throw Exception('Formato de respuesta no válido.');
      }

      if (data['success'] != true) {
        throw Exception(data['message'] ?? 'Error al obtener órdenes de trabajo.');
      }

      final rawList = data['data'];
      if (rawList is! List) return [];

      return rawList.map((item) => Map<String, dynamic>.from(item as Map)).toList();
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Obtiene el detalle de una orden de trabajo por su número
  Future<Map<String, dynamic>> obtenerOrdenTrabajo(int ordenNro) async {
    try {
      final response = await ApiClient.dio.get('$_basePath/$ordenNro');
      final data = response.data;

      if (data is Map && data.containsKey('data')) {
        return Map<String, dynamic>.from(data['data'] as Map);
      }
      if (data is Map) {
        return Map<String, dynamic>.from(data);
      }
      throw Exception('Formato de datos no reconocido.');
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Crea una nueva orden de trabajo
  Future<Map<String, dynamic>> crearOrdenTrabajo(Map<String, dynamic> datos) async {
    try {
      final response = await ApiClient.dio.post(
        '$_basePath/',
        data: datos,
      );

      final data = response.data;
      if (data is! Map) {
        throw Exception('Respuesta inesperada al crear orden de trabajo.');
      }
      return Map<String, dynamic>.from(data);
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Actualiza una orden de trabajo existente
  Future<Map<String, dynamic>> actualizarOrdenTrabajo(
    int ordenNro,
    Map<String, dynamic> datos,
  ) async {
    try {
      final response = await ApiClient.dio.put(
        '$_basePath/$ordenNro',
        data: datos,
      );

      final data = response.data;
      if (data is! Map) {
        throw Exception('Respuesta inesperada al actualizar orden de trabajo.');
      }
      return Map<String, dynamic>.from(data);
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Actualiza el estado de una orden de trabajo ('PENDIENTE', 'EN_PROCESO', 'FINALIZADO', 'CANCELADO')
  Future<Map<String, dynamic>> actualizarEstado(
    int ordenNro,
    String nuevoEstado,
  ) async {
    try {
      final response = await ApiClient.dio.put(
        '$_basePath/$ordenNro/estado',
        data: {'estado': nuevoEstado},
      );

      final data = response.data;
      if (data is! Map) {
        throw Exception('Respuesta inesperada al actualizar estado.');
      }
      return Map<String, dynamic>.from(data);
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Elimina una orden de trabajo
  Future<void> eliminarOrdenTrabajo(int ordenNro) async {
    try {
      await ApiClient.dio.delete('$_basePath/$ordenNro');
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Obtiene los responsables asignados a la orden
  Future<List<Map<String, dynamic>>> listarResponsables(int ordenNro) async {
    try {
      final response = await ApiClient.dio.get('$_basePath/$ordenNro/responsables');
      final data = response.data;

      if (data is! Map) return [];
      final rawList = data['data'];
      if (rawList is! List) return [];

      return rawList.map((item) => Map<String, dynamic>.from(item as Map)).toList();
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Asigna un nuevo responsable a la orden
  Future<Map<String, dynamic>> asignarResponsable(int ordenNro, int idUsuario) async {
    try {
      final response = await ApiClient.dio.post(
        '$_basePath/$ordenNro/responsables',
        data: {'id_usuario': idUsuario},
      );
      return Map<String, dynamic>.from(response.data as Map);
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Elimina un responsable de la orden
  Future<void> eliminarResponsable(int ordenNro, int idUsuario) async {
    try {
      await ApiClient.dio.delete('$_basePath/$ordenNro/responsables/$idUsuario');
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Historial de estados de la orden
  Future<List<Map<String, dynamic>>> listarHistorial(int ordenNro) async {
    try {
      final response = await ApiClient.dio.get('$_basePath/$ordenNro/historial');
      final data = response.data;

      if (data is List) {
        return data.map((item) => Map<String, dynamic>.from(item as Map)).toList();
      }
      if (data is Map && data['data'] is List) {
        return (data['data'] as List)
            .map((item) => Map<String, dynamic>.from(item as Map))
            .toList();
      }
      return [];
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  String _parsearError(DioException e) {
    if (e.response?.data != null && e.response!.data is Map) {
      final data = e.response!.data as Map;
      if (data['detail'] != null) return data['detail'].toString();
      if (data['message'] != null) return data['message'].toString();
    }
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.connectionError) {
      return 'No se pudo conectar con el servidor. Verificá tu red.';
    }
    return 'Error del servidor (${e.response?.statusCode ?? 'red'}).';
  }
}
