import 'dart:async';
import 'package:dio/dio.dart';
import '../config/app_config.dart';
import 'offline_sync_service.dart';
import 'token_storage.dart';

class ApiClient {
  static String _cacheKeyFor(RequestOptions options) {
    final path = options.path.startsWith('http')
        ? Uri.tryParse(options.path)?.path ?? options.path
        : options.path;
    final qp = Map<String, dynamic>.from(options.queryParameters);
    if (qp.isEmpty) return path;
    final sortedKeys = qp.keys.toList()..sort();
    final qs = sortedKeys.map((k) => '$k=${qp[k]}').join('&');
    return '$path?$qs';
  }

  static bool _isCacheableGet(RequestOptions options) {
    if (options.method.toUpperCase() != 'GET') return false;
    if (options.responseType == ResponseType.bytes ||
        options.responseType == ResponseType.stream) {
      return false;
    }
    final p = options.path.toLowerCase();
    if (p.contains('/auth') ||
        p.contains('/login') ||
        p.contains('/archivos/') ||
        p.contains('/exportaciones')) {
      return false;
    }
    return true;
  }

  static bool _isNetworkError(DioException e) {
    return e.type == DioExceptionType.connectionError ||
        e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout ||
        e.type == DioExceptionType.sendTimeout ||
        (e.type == DioExceptionType.unknown && e.response == null);
  }

  static final Dio dio = Dio(
    BaseOptions(
      baseUrl: AppConfig.apiBaseUrl,
      connectTimeout: const Duration(seconds: 20),
      receiveTimeout: const Duration(seconds: 25),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ),
  )..interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final customUrl = await TokenStorage.getValue('custom_api_url');
          options.baseUrl = AppConfig.resolveBaseUrl(customUrl);

          final token = await TokenStorage.getToken();
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }

          // Respuesta inmediata desde SQLite si el dispositivo está sin conexión
          if (_isCacheableGet(options) && !OfflineSyncService.instance.isOnline) {
            final cached = await OfflineSyncService.instance.leerHttpCache(_cacheKeyFor(options));
            if (cached != null) {
              return handler.resolve(
                Response(
                  requestOptions: options,
                  statusCode: 200,
                  data: cached,
                  extra: {'from_offline_cache': true},
                ),
              );
            }
          }
          return handler.next(options);
        },
        onResponse: (response, handler) async {
          if (_isCacheableGet(response.requestOptions) &&
              response.statusCode != null &&
              response.statusCode! >= 200 &&
              response.statusCode! < 300 &&
              response.data != null &&
              response.extra['from_offline_cache'] != true) {
            final data = response.data;
            if (data is Map || data is List) {
              unawaited(
                OfflineSyncService.instance.guardarHttpCache(
                  _cacheKeyFor(response.requestOptions),
                  data,
                ),
              );
            }
          }
          return handler.next(response);
        },
        onError: (DioException e, handler) async {
          if (e.response?.statusCode == 401) {
            await TokenStorage.clearToken();
            return handler.next(e);
          }

          // Fallback transparente a SQLite ante caída de red o timeout en cualquier GET
          if (_isCacheableGet(e.requestOptions) && _isNetworkError(e)) {
            final cached = await OfflineSyncService.instance.leerHttpCache(
              _cacheKeyFor(e.requestOptions),
            );
            if (cached != null) {
              return handler.resolve(
                Response(
                  requestOptions: e.requestOptions,
                  statusCode: 200,
                  data: cached,
                  extra: {'from_offline_cache': true},
                ),
              );
            }
          }
          return handler.next(e);
        },
      ),
    );
}
