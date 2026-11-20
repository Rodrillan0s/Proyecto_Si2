import 'dart:math';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'api_client.dart';
import 'notificacion_service.dart';

const Map<String, List<String>> reportFamilies = {
  'finanzas': ['presupuestario', 'comparativo_costos', 'costos_periodo', 'saldo_comercial'],
  'obras': ['avance_ejecutivo', 'estado_unidades'],
  'inventario': ['stock', 'consumo_materiales'],
  'personal': ['asignacion_personal', 'utilizacion_personal'],
  'incidencias': ['incidencias', 'incidencias_criticas'],
};

const Map<String, String> reportFamilyLabels = {
  '': 'Todos',
  'finanzas': 'Finanzas y Rentabilidad',
  'obras': 'Obras y Avance',
  'inventario': 'Inventario y Materiales',
  'personal': 'Personal',
  'incidencias': 'Incidencias',
};

class ReportesService {
  final String base = '/api/reportes';

  Map<String, dynamic> tenant(int? company) =>
      company == null ? {} : {'id_empresa': company};

  Future<dynamic> get(String path, [int? company]) async =>
      (await ApiClient.dio.get('$base/$path', queryParameters: tenant(company))).data;

  Future<dynamic> post(String path, Map<String, dynamic> body, [int? company]) async =>
      (await ApiClient.dio.post('$base/$path', data: body, queryParameters: tenant(company))).data;

  Future<Map<String, dynamic>> catalog(int? company) async =>
      Map<String, dynamic>.from(await get('catalogo', company));

  Future<Map<String, dynamic>> interpret(
    String text,
    int? company, [
    String? conversation,
    bool ai = false,
  ]) async =>
      Map<String, dynamic>.from(
        await post(
          'interpretar',
          {'texto': text, 'conversacion': conversation, 'usar_ia': ai},
          company,
        ),
      );

  Future<Map<String, dynamic>> create(
    Map<String, dynamic> request,
    int? company,
  ) async =>
      Map<String, dynamic>.from(await post('ejecuciones', request, company));

  Future<Map<String, dynamic>> execution(String id) async =>
      Map<String, dynamic>.from(await get('ejecuciones/$id'));

  Future<List<dynamic>> history(int? company) async =>
      List<dynamic>.from(await get('ejecuciones', company) ?? []);

  Future<List<dynamic>> recipients(int? company) async =>
      List<dynamic>.from(await get('destinatarios', company) ?? []);

  Future<List<dynamic>> schedules(int? company) async =>
      List<dynamic>.from(await get('programaciones', company) ?? []);

  Future<List<dynamic>> deliveries(String executionId) async =>
      List<dynamic>.from(await get('ejecuciones/$executionId/envios') ?? []);

  Future<({Uint8List bytes, String name})> download(
    String execution,
    String format,
  ) async {
    final file = (await ApiClient.dio.post(
      '$base/ejecuciones/$execution/exportaciones',
      queryParameters: {'formato': format},
    ))
        .data;
    final response = await ApiClient.dio.get<List<int>>(
      '$base/archivos/${file['id']}',
      options: Options(responseType: ResponseType.bytes),
    );
    return (
      bytes: Uint8List.fromList(response.data!),
      name: file['nombre'].toString(),
    );
  }

  Future<void> send(
    String execution,
    List<int> recipients,
    String format,
    String identity,
  ) async {
    await ApiClient.dio.post(
      '$base/ejecuciones/$execution/envios',
      data: {
        'destinatarios': recipients,
        'formatos': [format],
      },
      options: Options(headers: {'Idempotency-Key': identity}),
    );
    NotificacionService.instance.emitLocalPush(
      titulo: 'Reporte Enviado por Correo',
      cuerpo: 'El reporte en formato ${format.toUpperCase()} fue enviado a ${recipients.length} destinatario(s).',
      tipo: 'REPORTE',
    );
  }

  Future<void> pause(String id, bool enabled) async {
    await ApiClient.dio.patch(
      '$base/programaciones/$id',
      data: {'habilitada': enabled},
    );
    NotificacionService.instance.emitLocalPush(
      titulo: enabled ? 'Programación de Reporte Activada' : 'Programación de Reporte Pausada',
      cuerpo: 'La programación #$id fue ${enabled ? 'habilitada' : 'pausada'}.',
      tipo: 'REPORTE',
    );
  }

  Future<void> runScheduleNow(String id) async {
    await post('programaciones/$id/ejecutar', {});
    NotificacionService.instance.emitLocalPush(
      titulo: 'Reporte Programado Ejecutado',
      cuerpo: 'La programación #$id se ejecutó y despachó en este momento.',
      tipo: 'REPORTE',
    );
  }

  Future<String> transcribe(String path, int? company) async {
    final response = await ApiClient.dio.post(
      '/api/voz/transcribir',
      data: FormData.fromMap({'audio': await MultipartFile.fromFile(path)}),
      queryParameters: tenant(company),
    );
    return response.data['texto'].toString();
  }

  static String identity() {
    final random = Random.secure();
    final bytes = List.generate(16, (_) => random.nextInt(256));
    bytes[6] = (bytes[6] & 15) | 64;
    bytes[8] = (bytes[8] & 63) | 128;
    final hex = bytes.map((v) => v.toRadixString(16).padLeft(2, '0')).join();
    return '${hex.substring(0, 8)}-${hex.substring(8, 12)}-${hex.substring(12, 16)}-${hex.substring(16, 20)}-${hex.substring(20)}';
  }
}
