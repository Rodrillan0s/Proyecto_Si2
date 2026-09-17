import 'package:dio/dio.dart';
import 'api_client.dart';

class CrmService {
  static const String _basePath = '/crm';

  /// Obtiene la lista de clientes o prospectos comerciales con filtros
  Future<List<Map<String, dynamic>>> listarClientes({
    String? tipoCliente,
    String? estado,
    String? query,
    int? idUsuarioAsignado,
    int page = 1,
    int limit = 50,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'page': page,
        'limit': limit,
      };
      if (tipoCliente != null && tipoCliente.isNotEmpty) {
        queryParams['tipo_cliente'] = tipoCliente;
      }
      if (estado != null && estado.isNotEmpty && estado != 'TODOS') {
        queryParams['estado'] = estado;
      }
      if (query != null && query.isNotEmpty) {
        queryParams['q'] = query;
      }
      if (idUsuarioAsignado != null) {
        queryParams['id_usuario_asignado'] = idUsuarioAsignado;
      }

      final response = await ApiClient.dio.get(
        '$_basePath/clientes',
        queryParameters: queryParams,
      );
      final data = response.data;

      if (data is Map && data['data'] is List) {
        final list = data['data'] as List;
        return list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
      }
      if (data is List) {
        return data.map((e) => Map<String, dynamic>.from(e as Map)).toList();
      }

      return [];
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Obtiene la ficha completa de un cliente con sus interacciones y unidades
  Future<Map<String, dynamic>> obtenerDetalleCliente(int idCliente) async {
    try {
      final response = await ApiClient.dio.get('$_basePath/clientes/$idCliente');
      final data = response.data;

      if (data is Map && data['data'] is Map) {
        return Map<String, dynamic>.from(data['data'] as Map);
      }
      if (data is Map) {
        return Map<String, dynamic>.from(data);
      }

      throw Exception('Formato de datos de cliente no válido.');
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Obtiene las métricas cuantitativas del embudo comercial
  Future<Map<String, dynamic>> obtenerMetricas() async {
    try {
      final response = await ApiClient.dio.get('$_basePath/clientes/metricas');
      final data = response.data;

      if (data is Map && data['data'] is Map) {
        return Map<String, dynamic>.from(data['data'] as Map);
      }
      return {};
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Obtiene la lista de asesores comerciales de la empresa
  Future<List<Map<String, dynamic>>> listarAsesores() async {
    try {
      final response = await ApiClient.dio.get('$_basePath/asesores');
      final data = response.data;

      if (data is Map && data['data'] is List) {
        final list = data['data'] as List;
        return list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
      }
      return [];
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Registra un nuevo prospecto o cliente en el CRM
  Future<Map<String, dynamic>> crearCliente(Map<String, dynamic> datos) async {
    try {
      final response = await ApiClient.dio.post(
        '$_basePath/clientes',
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

  /// Actualiza los datos de contacto y asesor de un prospecto/cliente
  Future<Map<String, dynamic>> actualizarCliente(
    int idCliente,
    Map<String, dynamic> datos,
  ) async {
    try {
      final response = await ApiClient.dio.put(
        '$_basePath/clientes/$idCliente',
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

  /// Avanza la etapa comercial en el pipeline con registro automático de nota
  Future<Map<String, dynamic>> avanzarEtapaComercial({
    required int idCliente,
    required String nuevoEstado,
    String? nota,
  }) async {
    try {
      final payload = <String, dynamic>{'nuevo_estado': nuevoEstado};
      if (nota != null && nota.trim().isNotEmpty) {
        payload['nota'] = nota.trim();
      }

      final response = await ApiClient.dio.patch(
        '$_basePath/clientes/$idCliente/clasificacion',
        data: payload,
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

  /// Asienta una nueva interacción comercial (llamada, visita, reunión, minuta)
  Future<Map<String, dynamic>> registrarInteraccion({
    required int idCliente,
    required String tipoInteraccion,
    required String observaciones,
    String? fechaContacto,
  }) async {
    try {
      final payload = <String, dynamic>{
        'tipo_interaccion': tipoInteraccion,
        'observaciones': observaciones,
      };
      if (fechaContacto != null) {
        payload['fecha_contacto'] = fechaContacto;
      }

      final response = await ApiClient.dio.post(
        '$_basePath/clientes/$idCliente/interacciones',
        data: payload,
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

  /// Consulta unidades disponibles para cotización y reserva
  Future<List<Map<String, dynamic>>> listarUnidadesDisponibles({int? idObra}) async {
    try {
      final queryParams = <String, dynamic>{};
      if (idObra != null) queryParams['id_obra'] = idObra;

      final response = await ApiClient.dio.get(
        '$_basePath/clientes/unidades-disponibles',
        queryParameters: queryParams,
      );
      final data = response.data;

      if (data is Map && data['data'] is List) {
        final list = data['data'] as List;
        return list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
      }
      return [];
    } on DioException catch (e) {
      throw Exception(_parsearError(e));
    }
  }

  /// Asocia una unidad inmobiliaria al prospecto/cliente (interés, reserva o venta)
  Future<Map<String, dynamic>> asociarUnidad({
    required int idCliente,
    required int idUnidad,
    required String estadoAsociacion,
    double? precioPactado,
    String? observaciones,
  }) async {
    try {
      final payload = <String, dynamic>{
        'id_unidad': idUnidad,
        'estado_asociacion': estadoAsociacion,
        'precio_pactado': precioPactado,
        'observaciones': observaciones ?? '',
      };

      final response = await ApiClient.dio.post(
        '$_basePath/clientes/$idCliente/unidades',
        data: payload,
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

  String _parsearError(DioException e) {
    if (e.response?.data != null && e.response!.data is Map) {
      final data = e.response!.data as Map;
      if (data['detail'] != null) return data['detail'].toString();
      if (data['message'] != null) return data['message'].toString();
    }
    if (e.type == DioExceptionType.connectionTimeout || e.type == DioExceptionType.connectionError) {
      return 'No se pudo conectar al servidor de CRM. Verifique su conexión.';
    }
    return 'Error en el servicio comercial (${e.response?.statusCode ?? 'red'}).';
  }
}
