import 'package:dio/dio.dart';
import 'api_client.dart';

class SuscripcionService {
  static const String _basePath = '/api/suscripciones';

  /// Obtiene los detalles de la suscripción SaaS de la empresa actual
  Future<Map<String, dynamic>?> obtenerSuscripcionEmpresa({int? idEmpresa}) async {
    try {
      final queryParams = <String, dynamic>{};
      if (idEmpresa != null && idEmpresa > 0) {
        queryParams['id_empresa'] = idEmpresa;
      }

      final response = await ApiClient.dio.get(
        '$_basePath/mi-empresa',
        queryParameters: queryParams.isNotEmpty ? queryParams : null,
      );

      final data = response.data;
      if (data is Map && data['data'] is Map) {
        return Map<String, dynamic>.from(data['data'] as Map);
      }
      return null;
    } on DioException catch (e) {
      if (e.response?.statusCode == 404 || e.response?.statusCode == 403) {
        return null;
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  /// Para administradores globales: lista el estado de todas las suscripciones
  Future<List<Map<String, dynamic>>> listarSuscripcionesEmpresas() async {
    try {
      final response = await ApiClient.dio.get('$_basePath/empresas');
      final data = response.data;
      if (data is Map && data['data'] is List) {
        return List<Map<String, dynamic>>.from(
          (data['data'] as List).map((x) => Map<String, dynamic>.from(x as Map)),
        );
      }
      return [];
    } catch (_) {
      return [];
    }
  }
}
