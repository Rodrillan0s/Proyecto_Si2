import 'package:dio/dio.dart';
import 'api_client.dart';

/// Servicio CU18 – Avances de Obra
/// Gestiona el registro y consulta de avances de unidades de construcción.
class AvanceService {
  static const String _base = '/api/proyectos';

  // ── Listar historial de avances ────────────────────────────────────────────
  Future<List<Map<String, dynamic>>> listarAvances(
    int idObra, {
    int? idUnidad,
  }) async {
    try {
      final url = idUnidad != null
          ? '$_base/$idObra/avances/?id_unidad=$idUnidad'
          : '$_base/$idObra/avances/';
      final response = await ApiClient.dio.get(url);
      final data = response.data;
      if (data is! Map || data['success'] != true) {
        throw Exception(data?['detail'] ?? 'Error al obtener avances.');
      }
      final rawList = data['data'];
      if (rawList is! List) return [];
      return rawList
          .map((e) => Map<String, dynamic>.from(e as Map))
          .toList();
    } on DioException catch (e) {
      throw Exception(_parseError(e));
    }
  }

  // ── Resumen de avance global + último avance por unidad ──────────────────
  Future<Map<String, dynamic>> resumenAvances(int idObra) async {
    try {
      final response =
          await ApiClient.dio.get('$_base/$idObra/avances/resumen');
      final data = response.data;
      if (data is! Map || data['success'] != true) {
        throw Exception(data?['detail'] ?? 'Error al obtener resumen.');
      }
      return Map<String, dynamic>.from(data);
    } on DioException catch (e) {
      throw Exception(_parseError(e));
    }
  }

  // ── Registrar nuevo avance ────────────────────────────────────────────────
  Future<Map<String, dynamic>> registrarAvance({
    required int idObra,
    required int idUnidad,
    required double porcentaje,
    required String fechaRegistro, // YYYY-MM-DD
    String observacion = '',
  }) async {
    try {
      final response = await ApiClient.dio.post(
        '$_base/$idObra/avances/',
        data: {
          'id_unidad': idUnidad,
          'porcentaje_avance': porcentaje,
          'fecha_registro': fechaRegistro,
          'observacion': observacion,
        },
      );
      final data = response.data;
      if (data is! Map || data['success'] != true) {
        throw Exception(data?['detail'] ?? data?['message'] ?? 'Error al registrar avance.');
      }
      return Map<String, dynamic>.from(data);
    } on DioException catch (e) {
      throw Exception(_parseError(e));
    }
  }

  // ── Eliminar avance ──────────────────────────────────────────────────────
  Future<void> eliminarAvance(int idObra, int idAvance) async {
    try {
      final response =
          await ApiClient.dio.delete('$_base/$idObra/avances/$idAvance');
      final data = response.data;
      if (data is Map && data['success'] == false) {
        throw Exception(data['detail'] ?? data['error'] ?? 'Error al eliminar.');
      }
    } on DioException catch (e) {
      throw Exception(_parseError(e));
    }
  }

  // ── Helper ────────────────────────────────────────────────────────────────
  String _parseError(DioException e) {
    if (e.response?.data != null && e.response!.data is Map) {
      final d = e.response!.data as Map;
      if (d['detail'] != null) return d['detail'].toString();
      if (d['message'] != null) return d['message'].toString();
      if (d['error'] != null) return d['error'].toString();
    }
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.connectionError:
        return 'No se pudo conectar al servidor. Verifica tu conexión.';
      default:
        break;
    }
    switch (e.response?.statusCode) {
      case 400:
        return 'Datos inválidos.';
      case 401:
        return 'Sesión expirada. Inicia sesión nuevamente.';
      case 403:
        return 'No tienes permisos para realizar esta acción.';
      case 404:
        return 'Recurso no encontrado.';
      case 500:
        return 'Error interno del servidor.';
      default:
        return 'Ocurrió un error inesperado (${e.response?.statusCode ?? 'red'}).';
    }
  }
}
