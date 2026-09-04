import 'package:dio/dio.dart';
import 'api_client.dart';

class MaterialService {
  final Dio _dio = ApiClient.dio;

  Future<List<Map<String, dynamic>>> listarMateriales({String? q}) async {
    try {
      final response = await _dio.get(
        '/api/materiales',
        queryParameters: q != null && q.isNotEmpty ? {'q': q} : null,
      );

      final data = response.data;
      if (data == null || data['success'] != true) {
        return [];
      }

      final list = data['data'] as List<dynamic>?;
      return list?.map((e) => Map<String, dynamic>.from(e as Map)).toList() ?? [];
    } catch (_) {
      return [];
    }
  }

  Future<List<Map<String, dynamic>>> listarCategorias() async {
    try {
      final response = await _dio.get('/api/materiales/categorias');
      final data = response.data;
      if (data == null || data['success'] != true) return [];
      final list = data['data'] as List<dynamic>?;
      return list?.map((e) => Map<String, dynamic>.from(e as Map)).toList() ?? [];
    } catch (_) {
      return [];
    }
  }
}
