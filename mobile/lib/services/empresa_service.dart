import 'package:dio/dio.dart';
import 'api_client.dart';

class EmpresaService {
  static const String _basePath = '/api/empresas';

  /// Obtiene el listado de empresas registradas en OBRATEC
  Future<List<Map<String, dynamic>>> listarEmpresas() async {
    try {
      final response = await ApiClient.dio.get('$_basePath/');
      final data = response.data;

      if (data is! Map) {
        throw Exception('Formato de respuesta no válido.');
      }

      if (data['success'] != true) {
        throw Exception(data['message'] ?? 'Error al obtener empresas.');
      }

      final rawList = data['data'];
      if (rawList is! List) return [];

      return rawList.map((item) => Map<String, dynamic>.from(item as Map)).toList();
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
    if (e.type == DioExceptionType.connectionTimeout || e.type == DioExceptionType.connectionError) {
      return 'No se pudo conectar al servidor de empresas. Verificá tu conexión.';
    }
    return 'Error al comunicar con el servidor (${e.response?.statusCode ?? 'red'}).';
  }
}
