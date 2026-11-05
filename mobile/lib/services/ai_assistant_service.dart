import 'package:dio/dio.dart';
import 'api_client.dart';

class AiAssistantService {
  final Dio _dio = ApiClient.dio;

  /// Envía una consulta al Asistente Inteligente Administrativo y Operativo
  Future<Map<String, dynamic>> enviarConsulta({
    required String texto,
    String? conversacionId,
    int? idEmpresa,
    int? idObraContexto,
  }) async {
    try {
      final payload = <String, dynamic>{
        'texto': texto.trim(),
        'usar_ia': true,
      };
      if (conversacionId != null && conversacionId.isNotEmpty) {
        payload['conversacion'] = conversacionId;
      }
      if (idObraContexto != null && idObraContexto > 0) {
        payload['id_obra_contexto'] = idObraContexto;
      }

      final queryParams = <String, dynamic>{};
      if (idEmpresa != null && idEmpresa > 0) {
        queryParams['id_empresa'] = idEmpresa;
      }

      final response = await _dio.post(
        '/api/ai/consulta',
        data: payload,
        queryParameters: queryParams,
      );

      if (response.data is Map<String, dynamic>) {
        return response.data as Map<String, dynamic>;
      }
      return {'success': false, 'mensaje': 'Respuesta con formato no esperado'};
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ??
          e.response?.data?['message'] ??
          'No se pudo conectar con el asistente de IA.';
      throw Exception(msg);
    }
  }

  /// Confirma y ejecuta una propuesta de operación administrativa generada por la IA
  Future<Map<String, dynamic>> confirmarOperacion({
    required String idPropuesta,
    int? idEmpresa,
    int? idObraContexto,
  }) async {
    try {
      final queryParams = <String, dynamic>{};
      if (idEmpresa != null && idEmpresa > 0) {
        queryParams['id_empresa'] = idEmpresa;
      }
      if (idObraContexto != null && idObraContexto > 0) {
        queryParams['id_obra_contexto'] = idObraContexto;
      }

      final response = await _dio.post(
        '/api/ai/operacion/confirmar',
        data: {'id_propuesta': idPropuesta},
        queryParameters: queryParams,
      );

      if (response.data is Map<String, dynamic>) {
        return response.data as Map<String, dynamic>;
      }
      return {'success': true, 'mensaje': 'Operación ejecutada exitosamente'};
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ??
          e.response?.data?['message'] ??
          'Error al confirmar la operación.';
      throw Exception(msg);
    }
  }

  /// Cancela una propuesta de operación administrativa en el servidor
  Future<Map<String, dynamic>> cancelarOperacion({
    required String idPropuesta,
  }) async {
    try {
      final response = await _dio.post(
        '/api/ai/operacion/cancelar',
        data: {'id_propuesta': idPropuesta},
      );

      if (response.data is Map<String, dynamic>) {
        return response.data as Map<String, dynamic>;
      }
      return {'success': true, 'mensaje': 'Operación cancelada'};
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ??
          e.response?.data?['message'] ??
          'Error al cancelar la operación.';
      throw Exception(msg);
    }
  }
}
