import 'dart:typed_data';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';

import 'api_client.dart';
import 'auth_provider.dart';
import 'token_storage.dart';

/// ─────────────────────────────────────────────────────────────────────────────
/// CU19 — Gestión de incidencias (HU69–HU74)
///
/// Consume exactamente los contratos de backend/app/routes/incidencia_routes.py.
/// Todas las llamadas usan [ApiClient.dio], que adjunta el Bearer token. Nunca
/// se envía id_empresa: el backend deriva la empresa por incidencia → obra →
/// empresa a partir del JWT. Tampoco se envían fechas de atención: las genera
/// el servidor al pasar a EN_PROCESO / PENDIENTE_VALIDACION.
/// ─────────────────────────────────────────────────────────────────────────────
class IncidenciaService {
  static const String _basePath = '/api/incidencias';

  static const List<String> estados = ['ABIERTA', 'ASIGNADA', 'EN_PROCESO', 'PENDIENTE_VALIDACION', 'RESUELTA', 'CERRADA'];
  static const List<String> prioridades = ['BAJA', 'MEDIA', 'ALTA', 'CRITICA'];

  /// Obras autorizadas por el servidor para registrar, con pertenencia activa.
  Future<List<Map<String, dynamic>>> obrasRegistro() async {
    final data = await _get('$_basePath/obras-registro');
    return _lista(data['data']);
  }

  // ── Listado / detalle ────────────────────────────────────────────────────
  /// GET /api/incidencias/ → {success, data: [...], pagination: {page, limit, total, total_pages}}
  Future<Map<String, dynamic>> listar({
    int? idObra,
    int? idResponsable,
    String? prioridad,
    String? estado,
    String? busqueda,
    int page = 1,
    int limit = 20,
  }) async {
    final params = <String, dynamic>{'page': page, 'limit': limit};
    if (idObra != null) params['id_obra'] = idObra;
    if (idResponsable != null) params['id_responsable'] = idResponsable;
    if (prioridad != null && prioridad.isNotEmpty) params['prioridad'] = prioridad;
    if (estado != null && estado.isNotEmpty) params['estado'] = estado;
    if (busqueda != null && busqueda.trim().isNotEmpty) params['busqueda'] = busqueda.trim();

    final data = await _get('$_basePath/', queryParameters: params);
    final paginacion = data['pagination'] is Map
        ? Map<String, dynamic>.from(data['pagination'] as Map)
        : <String, dynamic>{'page': page, 'limit': limit, 'total': 0, 'total_pages': 0};
    return {'data': _lista(data['data']), 'pagination': paginacion};
  }

  /// GET /api/incidencias/{id} → data incluye `ordenes_trabajo`.
  Future<Map<String, dynamic>> obtener(int id) async {
    final data = await _get('$_basePath/$id');
    return Map<String, dynamic>.from(data['data'] as Map);
  }

  // ── HU69 / HU70: registrar y editar ────────────────────────────────────────
  /// POST /api/incidencias/ → {success, id_incidencia, message}. Nace ABIERTA.
  Future<Map<String, dynamic>> registrar({
    required int idObra,
    int? idUnidad,
    required String titulo,
    required String descripcion,
    required String prioridad,
    String? ubicacion,
  }) {
    return _send('POST', '$_basePath/', data: {
      'id_obra': idObra,
      'id_unidad': idUnidad,
      'titulo': titulo.trim(),
      'descripcion': descripcion.trim(),
      'prioridad': prioridad,
      'ubicacion': _nulaSiVacia(ubicacion),
    });
  }

  /// PUT /api/incidencias/{id} (obra y unidad no se pueden cambiar).
  Future<Map<String, dynamic>> actualizar(
    int id, {
    required String titulo,
    required String descripcion,
    required String prioridad,
    String? ubicacion,
  }) {
    return _send('PUT', '$_basePath/$id', data: {
      'titulo': titulo.trim(),
      'descripcion': descripcion.trim(),
      'prioridad': prioridad,
      'ubicacion': _nulaSiVacia(ubicacion),
    });
  }

  // ── HU71: responsable ──────────────────────────────────────────────────────
  /// GET /{id}/responsables → [{nro_usuario, nombre_usuario, nombre_completo, nombre_rol}]
  Future<List<Map<String, dynamic>>> listarResponsables(int id) async {
    final data = await _get('$_basePath/$id/responsables');
    return _lista(data['data']);
  }

  /// PATCH /{id}/responsable → {success, message, estado}
  Future<Map<String, dynamic>> asignarResponsable(int id, int idResponsable) {
    return _send('PATCH', '$_basePath/$id/responsable', data: {'id_responsable': idResponsable});
  }

  // ── HU72 / HU74: estado ────────────────────────────────────────────────────
  /// PATCH /{id}/estado → {success, message, estado_anterior, estado_nuevo}
  Future<Map<String, dynamic>> cambiarEstado(int id, String estado, {String? observacion}) {
    final body = <String, dynamic>{'estado': estado};
    final obs = _nulaSiVacia(observacion);
    if (obs != null) body['observacion'] = obs;
    return _send('PATCH', '$_basePath/$id/estado', data: body);
  }

  // ── Seguimiento ────────────────────────────────────────────────────────────
  Future<List<Map<String, dynamic>>> listarSeguimiento(int id) async {
    final data = await _get('$_basePath/$id/seguimiento');
    return _lista(data['data']);
  }

  Future<Map<String, dynamic>> registrarSeguimiento(int id, String observacion) {
    return _send('POST', '$_basePath/$id/seguimiento', data: {'observacion': observacion.trim()});
  }

  // ── HU73: evidencias fotográficas ─────────────────────────────────────────
  Future<List<Map<String, dynamic>>> listarEvidencias(int id) async {
    final data = await _get('$_basePath/$id/evidencias');
    return _lista(data['data']);
  }

  /// POST /{id}/evidencias (multipart, campo `archivo`). El backend solo
  /// acepta image/jpeg, image/png, image/webp o image/gif de hasta 10 MB.
  Future<Map<String, dynamic>> subirEvidencia(
    int id, {
    required Uint8List bytes,
    required String nombreArchivo,
    void Function(int enviados, int total)? onProgreso,
  }) {
    final formData = FormData.fromMap({
      'archivo': MultipartFile.fromBytes(
        bytes,
        filename: nombreArchivo,
        contentType: DioMediaType.parse(tipoMimeImagen(nombreArchivo)),
      ),
    });
    return _send(
      'POST',
      '$_basePath/$id/evidencias',
      data: formData,
      onSendProgress: onProgreso,
      timeout: const Duration(seconds: 120),
    );
  }

  /// GET /{id}/evidencias/{id_evidencia}/archivo — endpoint autenticado; nunca
  /// se construye una URL pública hacia la carpeta uploads del backend.
  Future<Uint8List> descargarEvidencia(int id, int idEvidencia) async {
    try {
      final response = await ApiClient.dio.get<List<int>>(
        '$_basePath/$id/evidencias/$idEvidencia/archivo',
        options: Options(responseType: ResponseType.bytes, receiveTimeout: const Duration(seconds: 120)),
      );
      return Uint8List.fromList(response.data ?? const []);
    } on DioException catch (e) {
      throw IncidenciaException(await mensajeError(e, recurso: 'La fotografía'), e.response?.statusCode);
    }
  }

  // ── Órdenes de trabajo afectadas (relación M:N) ────────────────────────────
  Future<List<Map<String, dynamic>>> listarOrdenesTrabajo(int id) async {
    final data = await _get('$_basePath/$id/ordenes-trabajo');
    return _lista(data['data']);
  }

  /// Solo OT de la MISMA obra de la incidencia (el backend las filtra), con
  /// el indicador `afectada`.
  Future<List<Map<String, dynamic>>> listarOrdenesTrabajoDisponibles(int id) async {
    final data = await _get('$_basePath/$id/ordenes-trabajo/disponibles');
    return _lista(data['data']);
  }

  /// PUT /{id}/ordenes-trabajo {ordenes: [...]} — reemplaza el conjunto
  /// (lista vacía = ninguna). → {success, message, agregadas, quitadas}
  Future<Map<String, dynamic>> actualizarOrdenesTrabajo(int id, List<int> ordenes) {
    return _send('PUT', '$_basePath/$id/ordenes-trabajo', data: {'ordenes': ordenes});
  }

  // ── Utilidades públicas ────────────────────────────────────────────────────
  static String etiquetaOrden(dynamic ordenNro) {
    final n = int.tryParse(ordenNro?.toString() ?? '');
    return n == null ? 'OT-?' : 'OT-${n.toString().padLeft(3, '0')}';
  }

  static String tipoMimeImagen(String nombreArchivo) {
    final ext = nombreArchivo.split('.').last.toLowerCase();
    switch (ext) {
      case 'png':
        return 'image/png';
      case 'webp':
        return 'image/webp';
      case 'gif':
        return 'image/gif';
      default:
        return 'image/jpeg';
    }
  }

  /// Mensaje comprensible para cada error HTTP / de red.
  static Future<String> mensajeError(DioException e, {String recurso = 'La incidencia'}) async {
    final status = e.response?.statusCode;
    final data = e.response?.data;
    String? detalle;
    if (data is Map && data['detail'] is String) detalle = data['detail'] as String;

    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return 'Tiempo de espera agotado. Verifica tu conexión o el estado del servidor.';
      case DioExceptionType.connectionError:
        return await _hayConexion()
            ? 'No se pudo conectar con el servidor de OBRATEC. Intenta nuevamente.'
            : 'Sin conexión a internet. Revisa tu red e intenta nuevamente.';
      case DioExceptionType.cancel:
        return 'La operación fue cancelada.';
      default:
        break;
    }

    switch (status) {
      case 401:
        return 'Tu sesión expiró o el token no es válido. Inicia sesión nuevamente.';
      case 403:
        return detalle ?? 'No tienes permisos para realizar esta acción.';
      case 404:
        return detalle ?? '$recurso no existe o no pertenece a tu empresa.';
      case 409:
        return detalle ?? 'La incidencia cambió de estado mientras operabas. Actualiza e intenta nuevamente.';
      case 400:
      case 422:
        return detalle ?? 'Datos inválidos. Revisa la información ingresada.';
    }
    if (status != null && status >= 500) {
      return 'Error interno del servidor. Intenta nuevamente más tarde.';
    }
    return detalle ?? 'Ocurrió un error inesperado. Intenta nuevamente.';
  }

  static Future<bool> _hayConexion() async {
    try {
      final resultado = await Connectivity().checkConnectivity();
      return !resultado.contains(ConnectivityResult.none);
    } catch (_) {
      return true; // Si no se puede determinar, no se afirma que no haya red.
    }
  }

  // ── Internos ───────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> _get(String path, {Map<String, dynamic>? queryParameters}) async {
    try {
      final response = await ApiClient.dio.get(path, queryParameters: queryParameters);
      return _validar(response.data);
    } on DioException catch (e) {
      throw IncidenciaException(await mensajeError(e), e.response?.statusCode);
    }
  }

  Future<Map<String, dynamic>> _send(
    String method,
    String path, {
    Object? data,
    void Function(int, int)? onSendProgress,
    Duration? timeout,
  }) async {
    try {
      final response = await ApiClient.dio.request(
        path,
        data: data,
        onSendProgress: onSendProgress,
        options: Options(method: method, sendTimeout: timeout, receiveTimeout: timeout),
      );
      return _validar(response.data);
    } on DioException catch (e) {
      throw IncidenciaException(await mensajeError(e), e.response?.statusCode);
    }
  }

  Map<String, dynamic> _validar(dynamic data) {
    if (data is! Map) throw const IncidenciaException('Formato de respuesta no válido.');
    if (data['success'] != true) {
      throw IncidenciaException((data['message'] ?? data['detail'] ?? 'La operación no se completó.').toString());
    }
    return Map<String, dynamic>.from(data);
  }

  static List<Map<String, dynamic>> _lista(dynamic raw) {
    if (raw is! List) return [];
    return raw.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  static String? _nulaSiVacia(String? valor) {
    final v = valor?.trim() ?? '';
    return v.isEmpty ? null : v;
  }
}

class IncidenciaException implements Exception {
  final String mensaje;
  final int? statusCode;

  const IncidenciaException(this.mensaje, [this.statusCode]);

  @override
  String toString() => mensaje;
}

/// ─────────────────────────────────────────────────────────────────────────────
/// Permisos CU19 por rol.
///
/// El backend no expone los permisos del rol al cliente; igual que el resto de
/// la app (ver [mapaPermisosPorRol]) y la web (MAPA_PERMISOS_POR_ROL en
/// frontend/src/app/services/auth.ts), se usa un mapa estático que replica las
/// filas reales de obras.t_rol_permiso (migration_cu19_incidencias.sql). Solo
/// sirve para mostrar/ocultar acciones: el backend (exigir_permiso + reglas de
/// responsable) es siempre la autoridad final.
/// ─────────────────────────────────────────────────────────────────────────────
class PermisosIncidencia {
  static bool puedeRegistrar(AuthProvider auth) =>
      auth.esTrabajadorCampo || tiene(auth, registrar);
  static const String visualizar = 'Visualizar_incidencias';
  static const String registrar = 'Registrar_incidencias';
  static const String modificar = 'Modificar_incidencias';
  static const String asignar = 'Asignar_incidencias';
  static const String cerrar = 'Cerrar_incidencias';

  static const Map<String, List<String>> porRol = {
    'ADMINISTRADOR_EMPRESA': [visualizar, registrar, modificar, asignar, cerrar],
    'JEFE_DE_OBRA': [visualizar, registrar, modificar, asignar],
    'SUPERVISOR_OBRA': [visualizar, modificar, cerrar],
  };

  static bool tiene(AuthProvider auth, String permiso) {
    if (auth.esAdminGlobal) return true; // exigir_permiso: bypass de ADMINISTRADOR
    return porRol[auth.rolNormalizado]?.contains(permiso) ?? false;
  }

  /// Usuario autenticado (nro_usuario guardado al iniciar sesión).
  static Future<int?> usuarioActual() async {
    return int.tryParse(await TokenStorage.getValue('nro_usuario') ?? '');
  }

  static bool esResponsable(Map<String, dynamic> incidencia, int? nroUsuario) {
    final idResponsable = int.tryParse(incidencia['id_responsable']?.toString() ?? '');
    return nroUsuario != null && idResponsable != null && idResponsable == nroUsuario;
  }
}
