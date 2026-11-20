import 'package:flutter/foundation.dart';

class AppConfig {
  static const String defaultLocalUrl =
      kIsWeb ? 'http://localhost:5000' : 'http://127.0.0.1:5000';
  static const String defaultCloudUrl = 'https://obratech-y040.onrender.com';

  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: defaultCloudUrl,
  );

  static String get wsBaseUrl => wsBaseUrlFrom(apiBaseUrl);

  static String resolveBaseUrl(String? customUrl) {
    final trimmed = (customUrl ?? '').trim();
    if (trimmed.isEmpty ||
        trimmed.contains('127.0.0.1') ||
        trimmed.contains('localhost') ||
        trimmed.contains('obratec-66o2.onrender.com')) {
      return apiBaseUrl;
    }
    return trimmed.endsWith('/')
        ? trimmed.substring(0, trimmed.length - 1)
        : trimmed;
  }

  static String wsBaseUrlFrom(String httpUrl) {
    final normalized = resolveBaseUrl(httpUrl);
    if (normalized.startsWith('https://')) {
      return 'wss://${normalized.substring(8)}';
    }
    if (normalized.startsWith('http://')) {
      return 'ws://${normalized.substring(7)}';
    }
    return normalized;
  }
}
