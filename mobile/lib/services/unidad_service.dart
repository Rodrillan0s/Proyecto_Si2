import 'package:dio/dio.dart';
import 'api_client.dart';

class UnidadService {
  Future<List<Map<String, dynamic>>> listarUnidades(int idObra) async {
    try {
      final response = await ApiClient.dio.get('/api/proyectos/$idObra/unidades');
      final data = response.data;

      if (data is List) {
        return data.map((e) => Map<String, dynamic>.from(e as Map)).toList();
      }

      if (data is Map && data['data'] is List) {
        final list = data['data'] as List;
        return list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
      }

      return [];
    } on DioException catch (e) {
      throw Exception(_parsearErrorDio(e));
    }
  }

  Future<Map<String, dynamic>> obtenerDetalleUnidad(int idObra, int idUnidad) async {
    try {
      final response = await ApiClient.dio.get('/api/proyectos/$idObra/unidades/$idUnidad');
      final data = response.data;

      if (data is Map) {
        if (data['data'] is Map) {
          return Map<String, dynamic>.from(data['data'] as Map);
        }
        return Map<String, dynamic>.from(data);
      }

      throw Exception('Datos de unidad inválidos.');
    } on DioException catch (e) {
      throw Exception(_parsearErrorDio(e));
    }
  }

  Future<Map<String, dynamic>> cambiarEstadoUnidad({
    required int idObra,
    required int idUnidad,
    required String nuevoEstado,
    String observacion = '',
  }) async {
    try {
      final response = await ApiClient.dio.patch(
        '/api/proyectos/$idObra/unidades/$idUnidad/estado',
        data: {
          'estado': nuevoEstado,
          'observacion': observacion,
        },
      );

      final data = response.data;
      if (data is Map) {
        return Map<String, dynamic>.from(data);
      }
      return {'success': true};
    } on DioException catch (e) {
      throw Exception(_parsearErrorDio(e));
    }
  }

  String _parsearErrorDio(DioException e) {
    if (e.response?.data != null) {
      final data = e.response!.data;
      if (data is Map && data['detail'] is List) {
        final errores = data['detail'] as List;
        return errores.map((err) {
          if (err is Map && err['msg'] != null) return err['msg'].toString();
          return err.toString();
        }).join('\n');
      }
      if (data is Map && data['detail'] != null) {
        return data['detail'].toString();
      }
      if (data is Map && data['message'] != null) {
        return data['message'].toString();
      }
    }

    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.sendTimeout:
        return 'Tiempo de espera agotado. Verifique su conexión.';
      case DioExceptionType.connectionError:
        return 'No se pudo conectar al servidor.';
      default:
        break;
    }

    switch (e.response?.statusCode) {
      case 400:
        return 'Datos inválidos.';
      case 401:
        return 'Sesión expirada.';
      case 403:
        return 'No tiene permisos para esta acción.';
      case 404:
        return 'Unidad no encontrada.';
      case 500:
        return 'Error interno del servidor.';
      default:
        return 'Ocurrió un error inesperado.';
    }
  }
}
