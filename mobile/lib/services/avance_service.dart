import 'package:dio/dio.dart';
import 'api_client.dart';

/// Servicio CU18 – Avances de Obra (Bitácora de Órdenes de Trabajo)
/// Los avances se derivan automáticamente de las órdenes cumplidas / finalizadas.
class AvanceService {
  static const String _base = '/api/proyectos';

  // ── Listar órdenes de trabajo (Bitácora de avance) ─────────────────────────
  Future<List<Map<String, dynamic>>> listarAvances(
    int idObra, {
    String? estado, // 'FINALIZADO' o 'PENDIENTE'
  }) async {
    try {
      final url = estado != null && estado.isNotEmpty
          ? '$_base/$idObra/avances/?estado=$estado'
          : '$_base/$idObra/avances/';
      final response = await ApiClient.dio.get(url);
      final data = response.data;
      if (data is! Map || data['success'] != true) {
        throw Exception(data?['detail'] ?? 'Error al obtener la bitácora de órdenes.');
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

  // ── Resumen de avance global derivado de órdenes de trabajo ────────────────
  Future<Map<String, dynamic>> resumenAvances(int idObra) async {
    try {
      final response =
          await ApiClient.dio.get('$_base/$idObra/avances/resumen');
      final data = response.data;
      if (data is! Map || data['success'] != true) {
        throw Exception(data?['detail'] ?? 'Error al obtener resumen de avance.');
      }
      return Map<String, dynamic>.from(data);
    } on DioException catch (e) {
      throw Exception(_parseError(e));
    }
  }

  // ── Helper de errores ──────────────────────────────────────────────────────
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
