import 'api_client.dart';
import 'token_storage.dart';

class AuthService {
  // Login contra /api/login.
  static Future<AuthResult> login({
    required String userInput,
    required String password,
  }) async {
    try {
      final data = await ApiClient.post('/login', {
        'user_input': userInput,
        'password': password,
      });

      if (data['success'] != true) {
        return AuthResult(
          success: false,
          message: data['message'] ?? 'Credenciales incorrectas',
        );
      }

      final token = data['access_token'];
      final user = data['user'];

      await TokenStorage.saveToken(token);
      await TokenStorage.saveUser(
        idUsuario: _toInt(user['id_usuario']),
        name: user['nombre_razon_social'] ?? '',
        mail: user['correo'] ?? '',
        role: _toInt(user['id_rol']),
        idEmpresa: user['id_empresa'] == null ? null : _toInt(user['id_empresa']),
      );

      return AuthResult(
        success: true,
        message: data['message'] ?? 'Inicio de sesión exitoso',
      );
    } catch (e) {
      return AuthResult(
        success: false,
        message: 'Error de conexión con el servidor',
      );
    }
  }

  static int _toInt(dynamic value) {
    if (value is int) return value;
    if (value is double) return value.toInt();
    return int.tryParse(value.toString()) ?? 0;
  }

  // Registro contra /api/register.
  static Future<AuthResult> register({
    required String user,
    required String doc,
    required String name,
    required String mail,
    required String number,
    required String password,
    String? dir,
  }) async {
    try {
      final body = {
        'user': user,
        'doc': doc,
        'name': name,
        'mail': mail,
        'number': number,
        'password': password,
        if (dir != null && dir.trim().isNotEmpty) 'dir': dir,
      };

      final data = await ApiClient.post('/register', body);

      if (data['success'] != true) {
        return AuthResult(
          success: false,
          message: data['message'] ?? 'No se pudo registrar el usuario',
        );
      }

      return AuthResult(
        success: true,
        message: data['message'] ?? 'Usuario registrado correctamente',
      );
    } catch (e) {
      return AuthResult(
        success: false,
        message: 'Error de conexión con el servidor',
      );
    }
  }

  static Future<void> logout() async {
    await TokenStorage.clearSession();
  }
}

class AuthResult {
  final bool success;
  final String message;

  AuthResult({
    required this.success,
    required this.message,
  });
}