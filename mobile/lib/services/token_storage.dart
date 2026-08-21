import 'package:shared_preferences/shared_preferences.dart';

class TokenStorage {
  static const String _tokenKey = 'access_token';
  static const String _userIdKey = 'user_id';
  static const String _empresaIdKey = 'empresa_id';
  static const String _userNameKey = 'user_name';
  static const String _userMailKey = 'user_mail';
  static const String _userRoleKey = 'user_role';

  static Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
  }

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  static Future<void> saveUser({
    required int idUsuario,
    required String name,
    required String mail,
    required int role,
    int? idEmpresa,
  }) async {
    final prefs = await SharedPreferences.getInstance();

    await prefs.setInt(_userIdKey, idUsuario);
    await prefs.setString(_userNameKey, name);
    await prefs.setString(_userMailKey, mail);
    await prefs.setInt(_userRoleKey, role);

    if (idEmpresa != null) {
      await prefs.setInt(_empresaIdKey, idEmpresa);
    } else {
      await prefs.remove(_empresaIdKey);
    }
  }

  static Future<int?> getUserId() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt(_userIdKey);
  }

  static Future<int?> getEmpresaId() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt(_empresaIdKey);
  }

  static Future<String?> getUserName() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_userNameKey);
  }

  static Future<String?> getUserMail() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_userMailKey);
  }

  static Future<int?> getUserRole() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt(_userRoleKey);
  }

  static Future<void> clearSession() async {
    final prefs = await SharedPreferences.getInstance();

    await prefs.remove(_tokenKey);
    await prefs.remove(_userIdKey);
    await prefs.remove(_empresaIdKey);
    await prefs.remove(_userNameKey);
    await prefs.remove(_userMailKey);
    await prefs.remove(_userRoleKey);
  }
}