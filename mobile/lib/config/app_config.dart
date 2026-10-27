import 'package:flutter/foundation.dart';

class AppConfig {
  static const String defaultLocalUrl =
      kIsWeb ? 'http://localhost:5000' : 'http://127.0.0.1:5000';
  static const String defaultCloudUrl = 'https://obratec-66o2.onrender.com';

  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: defaultCloudUrl,
  );
}