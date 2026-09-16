import 'package:dio/dio.dart';
import '../config/app_config.dart';
import 'token_storage.dart';

class AuthService {
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

  // ── LOGIN (CU02) ──────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> login({
    required String identificador,
    required String password,
  }) async {
    try {
      final dio = await _createDio();
      final response = await dio.post(
        '/api/auth/login',
        data: {
          'ci': identificador.trim(),
          'identificador': identificador.trim(),
          'password': password,
        },
      );

      final data = response.data;

      if (data == null || data['success'] != true) {
        throw Exception(data?['message'] ?? 'Error al iniciar sesión.');
      }

      final token = data['token'] as String;
      final usuario = data['usuario'] as Map<String, dynamic>;

      await TokenStorage.saveToken(token);
      await TokenStorage.saveUserData(
        nroUsuario: usuario['nro_usuario']?.toString() ?? '',
        ci: usuario['ci']?.toString() ?? '',
        nombreCompleto: usuario['nombre_completo']?.toString() ?? '',
        correo: usuario['correo']?.toString() ?? '',
        nombreRol: usuario['nombre_rol']?.toString() ?? '',
        telefono: usuario['telefono']?.toString() ?? '',
        idEmpresa: usuario['id_empresa']?.toString() ?? '',
      );

      return usuario;
    } on DioException catch (e) {
      throw Exception(_parsearErrorDio(e));
    }
  }

  // ── REGISTER (CU01) ───────────────────────────────────────────────────────
  Future<void> register({
    required String ci,
    required String nombreCompleto,
    required String nombreUsuario,
    required String correo,
    required String password,
    String? telefono,
    String? direccion,
    String? nombreEmpresa,
  }) async {
    try {
      final dio = await _createDio();
      final response = await dio.post(
        '/api/auth/register',
        data: {
          'ci': ci.trim(),
          'nombre_completo': nombreCompleto.trim(),
          'nombre_usuario': nombreUsuario.trim(),
          'correo': correo.trim(),
          'password': password,
          'telefono': telefono?.trim() ?? '',
          'direccion': direccion?.trim() ?? '',
          'nombre_empresa': nombreEmpresa?.trim() ?? '',
        },
      );

      final data = response.data;

      if (data == null || data['success'] != true) {
        throw Exception(data?['message'] ?? 'Error al registrar usuario.');
      }
    } on DioException catch (e) {
      throw Exception(_parsearErrorDio(e));
    }
  }

  // ── LOGOUT (CU03) ────────────────────────────────────────────────────────
  Future<void> logout() async {
    await TokenStorage.clearToken();
  }

  // ── PARSEAR ERRORES DIO ────────────────────────────────────────────────
  String _parsearErrorDio(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return 'Tiempo de espera agotado. Verifica tu conexión a internet o el estado del servidor.';
      case DioExceptionType.badResponse:
        final statusCode = e.response?.statusCode;
        final responseData = e.response?.data;

        if (responseData is Map) {
          final detail = responseData['detail'] ?? responseData['error'] ?? responseData['message'];
          if (detail != null) return detail.toString();
        }

        if (statusCode == 400) return 'Datos inválidos. Verifica la información ingresada.';
        if (statusCode == 401) return 'Credenciales incorrectas o usuario no encontrado.';
        if (statusCode == 403) return 'Acceso denegado. No tienes permisos para realizar esta acción.';
        if (statusCode == 404) return 'Recurso no encontrado (404).';
        if (statusCode == 500) return 'Error interno del servidor. Intenta de nuevo más tarde.';

        return 'Error del servidor: $statusCode';
      case DioExceptionType.connectionError:
        return 'No se pudo conectar con el servidor. Revisa tu conexión de red o la IP del servidor.';
      case DioExceptionType.cancel:
        return 'La petición fue cancelada.';
      default:
        return 'Ocurrió un error inesperado. Intenta de nuevo.';
    }
  }
}