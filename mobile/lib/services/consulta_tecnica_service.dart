import 'package:dio/dio.dart';
import 'api_client.dart';

class ConsultaTecnicaService {
  final Dio _dio = ApiClient.dio;

  Future<Map<String, dynamic>> listarConsultas({
    int? idObra,
    String? estado,
    int? idResponsable,
    String? busqueda,
    int page = 1,
    int limit = 20,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'page': page,
        'limit': limit,
      };
      if (idObra != null && idObra > 0) queryParams['id_obra'] = idObra;
      if (estado != null && estado.isNotEmpty) queryParams['estado'] = estado;
      if (idResponsable != null) queryParams['id_responsable'] = idResponsable;
      if (busqueda != null && busqueda.trim().isNotEmpty) queryParams['busqueda'] = busqueda.trim();

      final url = (idObra != null && idObra > 0)
          ? '/api/proyectos/$idObra/consultas-tecnicas'
          : '/api/consultas-tecnicas';

      final response = await _dio.get(url, queryParameters: queryParams);
      if (response.data is Map<String, dynamic>) {
        return response.data as Map<String, dynamic>;
      }
      return {'items': [], 'total': 0, 'page': 1, 'pages': 1};
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'Error al cargar consultas técnicas';
      throw Exception(msg);
    }
  }

  Future<Map<String, dynamic>> obtenerDetalle(int idConsultaTecnica) async {
    try {
      final response = await _dio.get('/api/consultas-tecnicas/$idConsultaTecnica');
      return Map<String, dynamic>.from(response.data as Map);
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'Error al obtener detalle de la consulta';
      throw Exception(msg);
    }
  }

  Future<Map<String, dynamic>> crearConsulta({
    required int idObra,
    required String asunto,
    required String descripcion,
    String? referenciaTecnica,
    int? asignadoA,
  }) async {
    try {
      final payload = <String, dynamic>{
        'asunto': asunto.trim(),
        'descripcion': descripcion.trim(),
      };
      if (referenciaTecnica != null && referenciaTecnica.trim().isNotEmpty) {
        payload['referencia_tecnica'] = referenciaTecnica.trim();
      }
      if (asignadoA != null && asignadoA > 0) {
        payload['asignado_a'] = asignadoA;
      }

      final response = await _dio.post('/api/proyectos/$idObra/consultas-tecnicas', data: payload);
      return Map<String, dynamic>.from(response.data as Map);
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'Error al registrar consulta técnica';
      throw Exception(msg);
    }
  }

  Future<List<Map<String, dynamic>>> obtenerUsuariosAsignables(int idObra) async {
    try {
      final response = await _dio.get('/api/proyectos/$idObra/consultas-tecnicas/usuarios-asignables');
      if (response.data is List) {
        return (response.data as List).map((u) => Map<String, dynamic>.from(u as Map)).toList();
      }
      return [];
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'Error al obtener usuarios asignables';
      throw Exception(msg);
    }
  }

  Future<Map<String, dynamic>> responder({
    required int idConsultaTecnica,
    required String respuesta,
  }) async {
    try {
      final response = await _dio.post(
        '/api/consultas-tecnicas/$idConsultaTecnica/respuestas',
        data: {'respuesta': respuesta.trim()},
      );
      return Map<String, dynamic>.from(response.data as Map);
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'Error al registrar respuesta técnica';
      throw Exception(msg);
    }
  }

  Future<Map<String, dynamic>> asignarResponsable({
    required int idConsultaTecnica,
    required int idResponsable,
    String? motivo,
  }) async {
    try {
      final payload = <String, dynamic>{
        'id_responsable': idResponsable,
      };
      if (motivo != null && motivo.trim().isNotEmpty) {
        payload['motivo'] = motivo.trim();
      }
      final response = await _dio.patch(
        '/api/consultas-tecnicas/$idConsultaTecnica/asignacion',
        data: payload,
      );
      return Map<String, dynamic>.from(response.data as Map);
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'Error al asignar responsable';
      throw Exception(msg);
    }
  }

  Future<Map<String, dynamic>> cambiarEstado({
    required int idConsultaTecnica,
    required String estado,
    String? motivo,
  }) async {
    try {
      final payload = <String, dynamic>{
        'estado': estado,
      };
      if (motivo != null && motivo.trim().isNotEmpty) {
        payload['motivo'] = motivo.trim();
      }
      final response = await _dio.patch(
        '/api/consultas-tecnicas/$idConsultaTecnica/estado',
        data: payload,
      );
      return Map<String, dynamic>.from(response.data as Map);
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'Error al cambiar estado';
      throw Exception(msg);
    }
  }
}
