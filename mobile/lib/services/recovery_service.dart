import 'package:dio/dio.dart';
import '../config/app_config.dart';
import 'token_storage.dart';

class RecoveryService {
  Future<Dio> _createDio() async {
    final customUrl = await TokenStorage.getValue('custom_api_url');
    final baseUrl = (customUrl != null && customUrl.trim().isNotEmpty)
        ? customUrl.trim()
        : AppConfig.apiBaseUrl;

    return Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );
  }

  Future<Map<String, dynamic>> solicitarRecuperacion(String correo) async {
    try {
      final dio = await _createDio();
      final response = await dio.post(
        '/api/auth/recuperar-password/solicitar',
        data: {'correo': correo.trim()},
      );
      final data = response.data;
      if (data == null || data['success'] != true) {
        throw Exception(data?['message'] ?? data?['detail'] ?? 'No se pudo enviar el código.');
      }
      return Map<String, dynamic>.from(data);
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  Future<Map<String, dynamic>> verificarCodigo({
    required String solicitudId,
    required String codigo,
  }) async {
    try {
      final dio = await _createDio();
      final response = await dio.post(
        '/api/auth/recuperar-password/verificar',
        data: {
          'solicitud_id': solicitudId,
          'codigo': codigo.trim(),
        },
      );
      final data = response.data;
      if (data == null || data['success'] != true) {
        throw Exception(data?['message'] ?? data?['detail'] ?? 'Código inválido o expirado.');
      }
      return Map<String, dynamic>.from(data);
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  Future<void> restablecerPassword({
    required String solicitudId,
    required String resetToken,
    required String passwordNueva,
    required String confirmarPassword,
  }) async {
    try {
      final dio = await _createDio();
      final response = await dio.post(
        '/api/auth/recuperar-password/restablecer',
        data: {
          'solicitud_id': solicitudId,
          'reset_token': resetToken,
          'password_nueva': passwordNueva,
          'confirmar_password': confirmarPassword,
        },
      );
      final data = response.data;
      if (data == null || data['success'] != true) {
        throw Exception(data?['message'] ?? data?['detail'] ?? 'No se pudo restablecer la contraseña.');
      }
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  String _parsearError(DioException e) {
    if (e.response?.data is Map) {
      final detail = e.response?.data['detail'] ?? e.response?.data['message'] ?? e.response?.data['error'];
      if (detail != null) return detail.toString();
    }
    if (e.type == DioExceptionType.connectionTimeout || e.type == DioExceptionType.receiveTimeout) {
      return 'Tiempo de espera agotado. Verifica tu conexión.';
    }
    if (e.type == DioExceptionType.connectionError) {
      return 'No se pudo conectar con el servidor.';
    }
    return 'Error al procesar la solicitud.';
  }
}
