import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class TokenStorage {
    static const FlutterSecureStorage _storage = FlutterSecureStorage();

    static Future<void> saveToken(String token) async {
        await _storage.write(key: 'auth_token', value: token);
    }

    static Future<String?> getToken() async {
        return _storage.read(key: 'auth_token');
    }

    static Future<void> clearToken() async {
        await _storage.delete(key: 'auth_token');
    }

    static Future<void> saveUserData({
        required String nroUsuario,
        required String ci,
        required String nombreCompleto,
        required String correo,
        required String nombreRol,
        required String telefono,
        required String idEmpresa,
    }) async {
        await _storage.write(key: 'nro_usuario', value: nroUsuario);
        await _storage.write(key: 'ci', value: ci);
        await _storage.write(key: 'nombre_completo', value: nombreCompleto);
        await _storage.write(key: 'correo', value: correo);
        await _storage.write(key: 'nombre_rol', value: nombreRol);
        await _storage.write(key: 'telefono', value: telefono);
        await _storage.write(key: 'id_empresa', value: idEmpresa);
    }

    static Future<void> setBiometriaHabilitada(bool habilitado) async {
        await _storage.write(key: 'biometria_habilitada', value: habilitado ? '1' : '0');
    }

    static Future<bool> isBiometriaHabilitada() async {
        final val = await _storage.read(key: 'biometria_habilitada');
        return val == '1';
    }

    static Future<void> setCustomApiUrl(String url) async {
        await _storage.write(key: 'custom_api_url', value: url.trim());
    }

    static Future<String?> getCustomApiUrl() async {
        return _storage.read(key: 'custom_api_url');
    }

    static Future<String?> getValue(String key) async {
       return _storage.read(key: key);
    }
}