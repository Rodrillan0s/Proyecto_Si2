import 'package:dio/dio.dart';
import 'api_client.dart';

Map<String, dynamic> actividadPayload(Map<String, dynamic> a) => {
      for (final key in [
        'clave',
        'nombre',
        'descripcion',
        'tipo',
        'fecha_inicio',
        'fecha_fin',
        'avance',
        'dependencias'
      ])
        key: a[key],
      'inicio_real':
          (a['inicio_real'] ?? '').toString().isEmpty ? null : a['inicio_real'],
      'fin_real':
          (a['fin_real'] ?? '').toString().isEmpty ? null : a['fin_real'],
    };

class CronogramaService {
  String _url(int obra) => '/api/obras/$obra/cronogramas';
  Future<dynamic> _request(Future<Response<dynamic>> Function() send) async {
    try {
      return (await send()).data;
    } on DioException catch (e) {
      final body = e.response?.data;
      final detail = body is Map ? body['detail'] : null;
      final message =
          detail is List ? detail.map((x) => x['msg']).join(' · ') : detail;
      throw Exception(
          message ?? 'No se pudo conectar con el servicio de cronogramas.');
    }
  }

  Future<List<Map<String, dynamic>>> listar(int obra) async {
    final r = await _request(() => ApiClient.dio.get('${_url(obra)}/'));
    return (r['data'] as List)
        .map((x) => Map<String, dynamic>.from(x))
        .toList();
  }

  Future<Map<String, dynamic>> obtener(
      int obra, int id, Map<String, String> filtros) async {
    final r = await _request(
        () => ApiClient.dio.get('${_url(obra)}/$id', queryParameters: filtros));
    return Map<String, dynamic>.from(r['data']);
  }

  Future<int> guardar(int obra, Map<String, dynamic> plan,
      {bool soloPlanificacion = false}) async {
    final actividades = (plan['actividades'] as List)
        .map((a) => actividadPayload(Map<String, dynamic>.from(a)))
        .toList();
    final id = plan['id_cronograma'];
    final payload = <String, dynamic>{'actividades': actividades};
    if (id != null) payload['version'] = plan['version'];
    if (!soloPlanificacion || id == null) {
      for (final key in [
        'nombre',
        'descripcion',
        'fecha_inicio',
        'fecha_fin'
      ]) {
        payload[key] = plan[key];
      }
    }
    final result = await _request(() => id == null
        ? ApiClient.dio.post('${_url(obra)}/', data: payload)
        : ApiClient.dio.put(
            '${_url(obra)}/$id${soloPlanificacion ? '/planificacion' : ''}',
            data: payload));
    return result['data']['id_cronograma'] as int;
  }

  Future<void> eliminar(int obra, Map<String, dynamic> plan) async {
    await _request(() => ApiClient.dio.delete(
        '${_url(obra)}/${plan['id_cronograma']}',
        queryParameters: {'version': plan['version']}));
  }
}
