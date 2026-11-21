import 'package:dio/dio.dart';
import 'api_client.dart';

class AdminChatMessage {
  final String author; // 'user' | 'assistant'
  final String text;
  final DateTime fecha;
  final String? query;
  String? topic;
  Map<String, dynamic>? execution;
  List<Map<String, dynamic>> executions;
  List<String> choices;
  List<Map<String, dynamic>> works;
  Map<String, dynamic>? request;
  Map<String, dynamic>? operacionPropuesta;
  Map<String, dynamic>? resultadoAnalisis;
  List<String> sugerencias;
  List<String> referencias;
  bool ejecutandoAccion;

  AdminChatMessage({
    required this.author,
    required this.text,
    required this.fecha,
    this.query,
    this.topic,
    this.execution,
    this.executions = const [],
    this.choices = const [],
    this.works = const [],
    this.request,
    this.operacionPropuesta,
    this.resultadoAnalisis,
    this.sugerencias = const [],
    this.referencias = const [],
    this.ejecutandoAccion = false,
  });
}

class AdminChatSession {
  String? conversacionId;
  List<AdminChatMessage> mensajes = [];
  String draftInput = '';
  String historyFilter = 'todos';
  Map<String, dynamic>? catalog;
}

class CommercialChatMessage {
  final String id;
  final String rol; // 'user' | 'assistant'
  final String texto;
  final String fecha;
  final String? intencion;
  final String? planoPath;
  final String? planoNombre;
  final String? estiloPlano;
  List<Map<String, dynamic>> unidades;
  Map<String, dynamic>? comparativa;
  Map<String, dynamic>? estimacionCosto;
  Map<String, dynamic>? lecturaPlano;
  Map<String, dynamic>? registroCrm;
  bool requiereContacto;
  bool mostrarFormularioContacto;
  List<String> sugerencias;

  CommercialChatMessage({
    required this.id,
    required this.rol,
    required this.texto,
    required this.fecha,
    this.intencion,
    this.planoPath,
    this.planoNombre,
    this.estiloPlano,
    this.unidades = const [],
    this.comparativa,
    this.estimacionCosto,
    this.lecturaPlano,
    this.registroCrm,
    this.requiereContacto = false,
    this.mostrarFormularioContacto = false,
    this.sugerencias = const [],
  });
}

class CommercialChatSession {
  String? conversacionId;
  List<CommercialChatMessage> mensajes = [];
  String mensajeInput = '';
  String? archivoPlanoPath;
  String? archivoPlanoNombre;
  String estiloPlanoSeleccionado = 'MINIMALISTA';
  List<int> unidadesSeleccionadasComparar = [];
  List<int> unidadesInteresContacto = [];
  Map<String, dynamic>? catalogo;
  Map<String, dynamic> formContacto = {
    'nombre_completo': '',
    'telefono': '',
    'email': '',
    'ci': '',
    'presupuesto_estimado': null,
    'moneda': 'USD',
    'horario_preferido': 'Mañana (09:00 - 12:00)',
    'notas': '',
  };
}

class AiAssistantService {
  final Dio _dio = ApiClient.dio;

  static String? _activeUserIdentity;
  static final Map<String, AdminChatSession> _adminSessions = {};
  static final Map<String, CommercialChatSession> _commercialSessions = {};
  static List<Map<String, dynamic>> empresasComercialesCache = [];
  static dynamic empresaRefComercialActiva;

  /// Garantiza aislamiento estricto de historial cuando cambia el usuario autenticado
  static void syncUserIdentity(String? userIdentity) {
    final normalized = (userIdentity ?? 'anon').trim().toLowerCase();
    if (_activeUserIdentity != null && _activeUserIdentity != normalized) {
      clearAllSessions();
    }
    _activeUserIdentity = normalized;
  }

  /// Limpia todas las sesiones en memoria (al cerrar sesión o cambiar de usuario)
  static void clearAllSessions() {
    _adminSessions.clear();
    _commercialSessions.clear();
    empresaRefComercialActiva = null;
  }

  static AdminChatSession obtenerSesionAdmin({
    required String userIdentity,
    required int? idEmpresa,
    int? idObraContexto,
  }) {
    syncUserIdentity(userIdentity);
    final key = '${_activeUserIdentity ?? "anon"}:${idEmpresa ?? "global"}:${idObraContexto ?? 0}';
    return _adminSessions.putIfAbsent(key, () => AdminChatSession());
  }

  static AdminChatSession reiniciarSesionAdmin({
    required String userIdentity,
    required int? idEmpresa,
    int? idObraContexto,
  }) {
    syncUserIdentity(userIdentity);
    final key = '${_activeUserIdentity ?? "anon"}:${idEmpresa ?? "global"}:${idObraContexto ?? 0}';
    final prevCatalog = _adminSessions[key]?.catalog;
    final next = AdminChatSession()..catalog = prevCatalog;
    _adminSessions[key] = next;
    return next;
  }

  static CommercialChatSession obtenerSesionComercial({
    required String userIdentity,
    required dynamic empresaRef,
  }) {
    syncUserIdentity(userIdentity);
    final key = '${_activeUserIdentity ?? "anon"}:${empresaRef ?? "default"}';
    return _commercialSessions.putIfAbsent(key, () => CommercialChatSession());
  }

  static CommercialChatSession reiniciarSesionComercial({
    required String userIdentity,
    required dynamic empresaRef,
  }) {
    syncUserIdentity(userIdentity);
    final key = '${_activeUserIdentity ?? "anon"}:${empresaRef ?? "default"}';
    final prevCatalog = _commercialSessions[key]?.catalogo;
    final next = CommercialChatSession()..catalogo = prevCatalog;
    _commercialSessions[key] = next;
    return next;
  }

  // ── MODO GESTIÓN / ADMIN & REPORTES (/api/ai/*) ──────────────────────────

  /// Envía una consulta al Asistente Inteligente Administrativo, Operativo y de Reportes
  Future<Map<String, dynamic>> enviarConsulta({
    required String texto,
    String? conversacionId,
    int? idEmpresa,
    int? idObraContexto,
    Map<String, dynamic>? solicitud,
  }) async {
    try {
      final payload = <String, dynamic>{
        'texto': texto.trim(),
        'usar_ia': true,
      };
      if (conversacionId != null && conversacionId.isNotEmpty) {
        payload['conversacion'] = conversacionId;
      }
      if (idObraContexto != null && idObraContexto > 0) {
        payload['id_obra_contexto'] = idObraContexto;
      }
      if (solicitud != null && solicitud.isNotEmpty) {
        payload['solicitud'] = solicitud;
      }

      final queryParams = <String, dynamic>{};
      if (idEmpresa != null && idEmpresa > 0) {
        queryParams['id_empresa'] = idEmpresa;
      }

      final response = await _dio.post(
        '/api/ai/consulta',
        data: payload,
        queryParameters: queryParams,
      );

      if (response.data is Map<String, dynamic>) {
        return response.data as Map<String, dynamic>;
      }
      return {'success': false, 'mensaje': 'Respuesta con formato no esperado'};
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ??
          e.response?.data?['message'] ??
          'No se pudo conectar con el asistente.';
      throw Exception(msg);
    }
  }

  /// Confirma y ejecuta una propuesta de operación administrativa generada por el asistente
  Future<Map<String, dynamic>> confirmarOperacion({
    required String idPropuesta,
    int? idEmpresa,
    int? idObraContexto,
  }) async {
    try {
      final queryParams = <String, dynamic>{};
      if (idEmpresa != null && idEmpresa > 0) {
        queryParams['id_empresa'] = idEmpresa;
      }
      if (idObraContexto != null && idObraContexto > 0) {
        queryParams['id_obra_contexto'] = idObraContexto;
      }

      final response = await _dio.post(
        '/api/ai/operacion/confirmar',
        data: {'id_propuesta': idPropuesta},
        queryParameters: queryParams,
      );

      if (response.data is Map<String, dynamic>) {
        return response.data as Map<String, dynamic>;
      }
      return {'success': true, 'mensaje': 'Operación ejecutada exitosamente'};
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ??
          e.response?.data?['message'] ??
          'Error al confirmar la operación.';
      throw Exception(msg);
    }
  }

  /// Cancela una propuesta de operación administrativa en el servidor
  Future<Map<String, dynamic>> cancelarOperacion({
    required String idPropuesta,
    int? idEmpresa,
    int? idObraContexto,
  }) async {
    try {
      final queryParams = <String, dynamic>{};
      if (idEmpresa != null && idEmpresa > 0) {
        queryParams['id_empresa'] = idEmpresa;
      }
      if (idObraContexto != null && idObraContexto > 0) {
        queryParams['id_obra_contexto'] = idObraContexto;
      }

      final response = await _dio.post(
        '/api/ai/operacion/cancelar',
        data: {'id_propuesta': idPropuesta},
        queryParameters: queryParams,
      );

      if (response.data is Map<String, dynamic>) {
        return response.data as Map<String, dynamic>;
      }
      return {'success': true, 'mensaje': 'Operación cancelada'};
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ??
          e.response?.data?['message'] ??
          'Error al cancelar la operación.';
      throw Exception(msg);
    }
  }

  // ── MODO COMERCIAL & TASADOR DE PLANOS (/api/public/comercial/*) ─────────

  Future<List<Map<String, dynamic>>> listarEmpresasComerciales() async {
    try {
      final response = await _dio.get('/api/public/comercial/empresas');
      final data = response.data;
      if (data is Map && data['data'] is List) {
        final list = (data['data'] as List)
            .whereType<Map>()
            .map((e) => Map<String, dynamic>.from(e))
            .toList();
        empresasComercialesCache = list;
        return list;
      }
      return [];
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'No se pudo cargar el listado de constructoras.';
      throw Exception(msg);
    }
  }

  Future<Map<String, dynamic>> obtenerCatalogoComercial(dynamic empresaRef) async {
    try {
      final ref = Uri.encodeComponent(empresaRef.toString());
      final response = await _dio.get('/api/public/comercial/$ref/catalogo');
      final data = response.data;
      if (data is Map) {
        if (data['data'] is Map) {
          return Map<String, dynamic>.from(data['data'] as Map);
        }
        return Map<String, dynamic>.from(data);
      }
      return {};
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'No se pudo cargar el portafolio inmobiliario.';
      throw Exception(msg);
    }
  }

  Future<Map<String, dynamic>> enviarChatComercial(
    dynamic empresaRef,
    Map<String, dynamic> payload,
  ) async {
    try {
      final ref = Uri.encodeComponent(empresaRef.toString());
      final response = await _dio.post(
        '/api/public/comercial/$ref/chat',
        data: payload,
      );
      if (response.data is Map) {
        return Map<String, dynamic>.from(response.data as Map);
      }
      return {};
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'Ocurrió un error al consultar el asistente comercial.';
      throw Exception(msg);
    }
  }

  Future<Map<String, dynamic>> estimarCostoComercial(
    dynamic empresaRef,
    Map<String, dynamic> payload,
  ) async {
    try {
      final ref = Uri.encodeComponent(empresaRef.toString());
      final response = await _dio.post(
        '/api/public/comercial/$ref/estimar-costo',
        data: payload,
      );
      if (response.data is Map) {
        return Map<String, dynamic>.from(response.data as Map);
      }
      return {};
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'No se pudo recalcular la estimación de costos.';
      throw Exception(msg);
    }
  }

  Future<Map<String, dynamic>> analizarPlanoComercial(
    dynamic empresaRef, {
    required String filePath,
    required String fileName,
    String? mensaje,
    double? presupuestoMax,
    String moneda = 'USD',
    String? estiloPreferido,
    String? conversacionId,
  }) async {
    try {
      final ref = Uri.encodeComponent(empresaRef.toString());
      final formMap = <String, dynamic>{
        'archivo': await MultipartFile.fromFile(filePath, filename: fileName),
        'moneda': moneda,
      };
      if (mensaje != null && mensaje.trim().isNotEmpty) {
        formMap['mensaje'] = mensaje.trim();
      }
      if (presupuestoMax != null && presupuestoMax > 0) {
        formMap['presupuesto_max'] = presupuestoMax.toString();
      }
      if (estiloPreferido != null && estiloPreferido.isNotEmpty) {
        formMap['estilo_preferido'] = estiloPreferido;
      }
      if (conversacionId != null && conversacionId.isNotEmpty) {
        formMap['conversacion_id'] = conversacionId;
      }

      final response = await _dio.post(
        '/api/public/comercial/$ref/analizar-plano',
        data: FormData.fromMap(formMap),
      );
      if (response.data is Map) {
        return Map<String, dynamic>.from(response.data as Map);
      }
      return {};
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ??
          'No se pudo procesar la imagen del plano. Usa formato PNG, JPG o WEBP.';
      throw Exception(msg);
    }
  }

  Future<Map<String, dynamic>> solicitarContactoComercial(
    dynamic empresaRef,
    Map<String, dynamic> payload,
  ) async {
    try {
      final ref = Uri.encodeComponent(empresaRef.toString());
      final response = await _dio.post(
        '/api/public/comercial/$ref/solicitar-contacto',
        data: payload,
      );
      if (response.data is Map) {
        return Map<String, dynamic>.from(response.data as Map);
      }
      return {};
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'No se pudo registrar la solicitud de contacto.';
      throw Exception(msg);
    }
  }
}
