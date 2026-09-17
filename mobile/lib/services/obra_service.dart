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

  /// Obtiene el catálogo de tipos de obra disponibles
  Future<List<Map<String, dynamic>>> obtenerTiposProyecto() async {
    try {
      final response = await ApiClient.dio.get('$_basePath/tipos');
      final data = response.data;

      if (data is List) {
        return data.map((item) => Map<String, dynamic>.from(item as Map)).toList();
      }
      if (data is Map && data['data'] is List) {
        final list = data['data'] as List;
        return list.map((item) => Map<String, dynamic>.from(item as Map)).toList();
      }
      return [];
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

  /// Registra un nuevo proyecto en la plataforma
  Future<Map<String, dynamic>> crearProyecto(Map<String, dynamic> datos) async {
    try {
      final response = await ApiClient.dio.post(
        '$_basePath/',
        data: datos,
      );
      final data = response.data;
      if (data is Map) {
        return Map<String, dynamic>.from(data);
      }
      return {'success': true};
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Actualiza la información técnica y económica de un proyecto existente
  Future<Map<String, dynamic>> actualizarProyecto(
    int idObra,
    Map<String, dynamic> datos,
  ) async {
    try {
      final response = await ApiClient.dio.put(
        '$_basePath/$idObra',
        data: datos,
      );
      final data = response.data;
      if (data is Map) {
        return Map<String, dynamic>.from(data);
      }
      return {'success': true};
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Actualiza el estado operativo de una obra
  Future<Map<String, dynamic>> actualizarEstadoObra(
    int idObra,
    String nuevoEstado,
  ) async {
    try {
      final response = await ApiClient.dio.patch(
        '$_basePath/$idObra/estado',
        data: {'estado_obra': nuevoEstado},
      );
      final data = response.data;
      if (data is Map) {
        return Map<String, dynamic>.from(data);
      }
      return {'success': true};
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Asigna un Jefe de Obra / Supervisor responsable al proyecto
  Future<Map<String, dynamic>> asignarResponsable(
    int idObra,
    int idUsuario,
  ) async {
    try {
      final response = await ApiClient.dio.post(
        '$_basePath/$idObra/responsables',
        data: {'id_usuario': idUsuario},
      );
      final data = response.data;
      if (data is Map) {
        return Map<String, dynamic>.from(data);
      }
      return {'success': true};
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Retira la asignación de un responsable del proyecto
  Future<void> retirarResponsable(int idObra, int idUsuario) async {
    try {
      await ApiClient.dio.delete('$_basePath/$idObra/responsables/$idUsuario');
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Lista usuarios disponibles con rol 'JEFE DE OBRA' para asignación
  Future<List<Map<String, dynamic>>> listarJefesObraDisponibles() async {
    try {
      final response = await ApiClient.dio.get('/api/usuarios/');
      final data = response.data;

      if (data is Map && data['data'] is List) {
        final list = data['data'] as List;
        return list
            .map((u) => Map<String, dynamic>.from(u as Map))
            .where((u) => (u['nombre_rol'] ?? '').toString().toUpperCase() == 'JEFE DE OBRA')
            .toList();
      }
      return [];
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Obtiene el árbol jerárquico de la estructura WBS de una obra
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

  /// Crea un nuevo elemento en la estructura de la obra (raíz o hijo con id_padre)
  Future<Map<String, dynamic>> crearElementoEstructura(
    int idObra,
    Map<String, dynamic> datos,
  ) async {
    try {
      final response = await ApiClient.dio.post(
        '$_basePath/$idObra/estructuras/',
        data: datos,
      );
      final data = response.data;

      if (data is! Map || data['success'] != true) {
        throw Exception(data?['message'] ?? 'Error al crear el elemento.');
      }

      return Map<String, dynamic>.from(data);
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Actualiza un elemento existente de la estructura
  Future<Map<String, dynamic>> actualizarElementoEstructura(
    int idObra,
    int idEstructura,
    Map<String, dynamic> datos,
  ) async {
    try {
      final response = await ApiClient.dio.put(
        '$_basePath/$idObra/estructuras/$idEstructura',
        data: datos,
      );
      final data = response.data;

      if (data is! Map || data['success'] != true) {
        throw Exception(data?['message'] ?? 'Error al actualizar el elemento.');
      }

      return Map<String, dynamic>.from(data);
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Elimina un elemento de la estructura
  Future<void> eliminarElementoEstructura(int idObra, int idEstructura) async {
    try {
      final response = await ApiClient.dio.delete(
        '$_basePath/$idObra/estructuras/$idEstructura',
      );
      final data = response.data;

      if (data is! Map || data['success'] != true) {
        throw Exception(data?['message'] ?? 'Error al eliminar el elemento.');
      }
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
      return 'No se pudo conectar al servidor de obras. Verifique su conexión.';
    }
    return 'Error al comunicar con el servidor (${e.response?.statusCode ?? 'red'}).';
  }
}
