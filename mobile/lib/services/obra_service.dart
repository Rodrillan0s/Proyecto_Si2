import 'package:dio/dio.dart';
import 'api_client.dart';

class ObraService {
  static const String _basePath = '/api/proyectos';

  /// Obtiene el listado completo de proyectos accesibles para el usuario
  Future<List<Map<String, dynamic>>> listarProyectos() async {
    try {
      final response = await ApiClient.dio.get('$_basePath/');
      final data = response.data;

      if (data is! Map) {
        throw Exception('Formato de respuesta no válido.');
      }

      if (data['success'] != true) {
        throw Exception(data['message'] ?? 'Error al obtener proyectos.');
      }

      final rawList = data['data'];
      if (rawList is! List) return [];

      return rawList.map((item) => Map<String, dynamic>.from(item as Map)).toList();
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Obtiene el detalle técnico y de ubicación de un proyecto
  Future<Map<String, dynamic>> obtenerDetalleProyecto(int idObra) async {
    try {
      final response = await ApiClient.dio.get('$_basePath/$idObra');
      final data = response.data;

      if (data is! Map || data['success'] != true) {
        throw Exception(data?['message'] ?? 'Error al obtener detalle del proyecto.');
      }

      return Map<String, dynamic>.from(data['data'] as Map);
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Obtiene el árbol jerárquico de la estructura WBS de una obra (HU35)
  Future<List<Map<String, dynamic>>> obtenerEstructura(int idObra) async {
    try {
      final response = await ApiClient.dio.get('$_basePath/$idObra/estructuras/');
      final data = response.data;

      if (data is! Map || data['success'] != true) {
        throw Exception(data?['message'] ?? 'Error al obtener la estructura.');
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
      return 'No se pudo conectar al servidor de obras. Verificá tu conexión.';
    }
    return 'Error al comunicar con el servidor (${e.response?.statusCode ?? 'red'}).';
  }
}
