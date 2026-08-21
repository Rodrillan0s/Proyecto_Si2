import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import 'token_storage.dart';

class ApiClient {
  static Future<Map<String, String>> _buildHeaders({
    bool requiresAuth = false,
  }) async {
    final token = await TokenStorage.getToken();

    return {
      'Content-Type': 'application/json',
      if (requiresAuth && token != null) 'Authorization': 'Bearer $token',
    };
  }

  static Future<Map<String, dynamic>> get(
    String path, {
    bool requiresAuth = false,
  }) async {
    try {
      final headers = await _buildHeaders(requiresAuth: requiresAuth);

      final response = await http.get(
        Uri.parse('${AppConfig.apiUrl}$path'),
        headers: headers,
      );

      final data = jsonDecode(response.body);

      if (data is Map<String, dynamic>) {
        return data;
      }

      return {
        'success': false,
        'message': 'Respuesta inválida del servidor',
      };
    } catch (e) {
      return {
        'success': false,
        'message': 'Error de conexión con el servidor',
      };
    }
  }

  static Future<Map<String, dynamic>> post(
    String path,
    Map<String, dynamic> body, {
    bool requiresAuth = false,
  }) async {
    try {
      final headers = await _buildHeaders(requiresAuth: requiresAuth);

      final response = await http.post(
        Uri.parse('${AppConfig.apiUrl}$path'),
        headers: headers,
        body: jsonEncode(body),
      );

      final data = jsonDecode(response.body);

      if (data is Map<String, dynamic>) {
        return data;
      }

      return {
        'success': false,
        'message': 'Respuesta inválida del servidor',
      };
    } catch (e) {
      return {
        'success': false,
        'message': 'Error de conexión con el servidor',
      };
    }
  }

  static Future<Map<String, dynamic>> put(
    String path,
    Map<String, dynamic> body, {
    bool requiresAuth = false,
  }) async {
    try {
      final headers = await _buildHeaders(requiresAuth: requiresAuth);

      final response = await http.put(
        Uri.parse('${AppConfig.apiUrl}$path'),
        headers: headers,
        body: jsonEncode(body),
      );

      final data = jsonDecode(response.body);

      if (data is Map<String, dynamic>) {
        return data;
      }

      return {
        'success': false,
        'message': 'Respuesta inválida del servidor',
      };
    } catch (e) {
      return {
        'success': false,
        'message': 'Error de conexión con el servidor',
      };
    }
  }
}