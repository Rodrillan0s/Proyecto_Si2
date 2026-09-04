import 'package:flutter/material.dart';
import 'token_storage.dart';

class AuthProvider extends ChangeNotifier {
  bool _estaAutenticado = false;
  Map<String, String>? _datosUsuario;

  bool get estaAutenticado => _estaAutenticado;
  Map<String, String>? get datosUsuario => _datosUsuario;

  String? get usuarioCompleto => _datosUsuario?['nombre_completo'] ?? _datosUsuario?['nombre'];
  String? get rol => _datosUsuario?['nombre_rol'] ?? _datosUsuario?['rol'];
  String? get correo => _datosUsuario?['correo'];
  String? get ci => _datosUsuario?['ci'];
  String? get idEmpresa => _datosUsuario?['id_empresa'];

  Future<void> verificarSesion() async {
    final token = await TokenStorage.getToken();
    if (token != null && token.isNotEmpty) {
      _estaAutenticado = true;
      final nombre = await TokenStorage.getValue('nombre_completo') ?? '';
      final rol = await TokenStorage.getValue('nombre_rol') ?? '';
      final correo = await TokenStorage.getValue('correo') ?? '';
      final ci = await TokenStorage.getValue('ci') ?? '';
      final idEmpresa = await TokenStorage.getValue('id_empresa') ?? '';

      _datosUsuario = {
        'nombre_completo': nombre,
        'nombre_rol': rol,
        'correo': correo,
        'ci': ci,
        'id_empresa': idEmpresa,
      };
      notifyListeners();
    }
  }

  void loginExitoso(Map<String, String> datos) {
    _estaAutenticado = true;
    _datosUsuario = datos;
    notifyListeners();
  }

  Future<void> cerrarSesion() async {
    _estaAutenticado = false;
    _datosUsuario = null;
    await TokenStorage.clearToken();
    notifyListeners();
  }

  void logout() {
    cerrarSesion();
  }
}