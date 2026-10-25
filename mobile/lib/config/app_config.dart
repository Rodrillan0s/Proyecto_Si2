import 'package:flutter/foundation.dart';

class AppConfig {
<<<<<<< HEAD
  static const String defaultLocalUrl = 'http://192.168.0.7:5000';
=======
  static const String defaultLocalUrl =
      kIsWeb ? 'http://localhost:5000' : 'http://192.168.0.9:5000';
>>>>>>> 23ed517e922328483f60633df421d97f987059f4
  static const String defaultCloudUrl = 'https://obratec-66o2.onrender.com';

  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: defaultLocalUrl,
  );
}