import 'dart:convert';
import 'package:flutter/material.dart';
import 'token_storage.dart';

/// 23 Permisos Oficiales de OBRATEC
const List<String> permisosOficiales = [
  'Visualizar_usuarios', 'Registrar_usuarios', 'Modificar_usuarios', 'Eliminar_usuarios',
  'Visualizar_obras', 'Registrar_obras', 'Modificar_obras', 'Eliminar_obras',
  'Visualizar_empresa', 'Registrar_empresa', 'Modificar_empresa', 'Eliminar_empresa',
  'Visualizar_inventario', 'Registrar_inventario', 'Modificar_inventario', 'Eliminar_inventario',
  'Visualizar_materiales', 'Registrar_materiales', 'Modificar_materiales', 'Desactivar_materiales',
  'Visualizar_proveedores', 'Registrar_proveedores', 'Modificar_proveedores',
];

/// Mapa de permisos por rol oficial
const Map<String, List<String>> mapaPermisosPorRol = {
  'ADMINISTRADOR': permisosOficiales,
  'ADMINISTRADOR_EMPRESA': [
    'Visualizar_usuarios', 'Registrar_usuarios', 'Modificar_usuarios', 'Eliminar_usuarios',
    'Visualizar_obras', 'Registrar_obras', 'Modificar_obras', 'Eliminar_obras',
    'Visualizar_empresa', 'Registrar_empresa', 'Modificar_empresa',
    'Visualizar_inventario', 'Registrar_inventario', 'Modificar_inventario', 'Eliminar_inventario',
    'Visualizar_materiales', 'Registrar_materiales', 'Modificar_materiales', 'Desactivar_materiales',
    'Visualizar_proveedores', 'Registrar_proveedores', 'Modificar_proveedores',
  ],
  'JEFE_DE_OBRA': [
    'Visualizar_obras', 'Registrar_obras', 'Modificar_obras',
    'Visualizar_inventario', 'Modificar_inventario',
    'Visualizar_materiales',
    'Visualizar_proveedores',
  ],
  'SUPERVISOR_OBRA': [
    'Visualizar_obras', 'Modificar_obras',
    'Visualizar_inventario',
    'Visualizar_materiales',
  ],
  'CLIENTE': [
    'Visualizar_obras',
  ],
  'ELECTRICO': [
    'Visualizar_obras',
    'Visualizar_inventario',
    'Visualizar_materiales',
  ],
  'PLOMERO': [
    'Visualizar_obras',
    'Visualizar_inventario',
    'Visualizar_materiales',
  ],
  'MAESTRO_ALBANIL': [
    'Visualizar_obras',
    'Visualizar_inventario',
    'Visualizar_materiales',
  ],
  'ALBANIL': [
    'Visualizar_obras',
    'Visualizar_inventario',
    'Visualizar_materiales',
  ],
};

class AuthProvider extends ChangeNotifier {
  bool _estaAutenticado = false;
  Map<String, String>? _datosUsuario;
  Map<String, dynamic>? _empresaActiva;

  bool get estaAutenticado => _estaAutenticado;
  Map<String, String>? get datosUsuario => _datosUsuario;
  Map<String, dynamic>? get empresaActiva => _empresaActiva;

  String? get usuarioCompleto => _datosUsuario?['nombre_completo'] ?? _datosUsuario?['nombre'];
  String? get rol => _datosUsuario?['nombre_rol'] ?? _datosUsuario?['rol'];
  String? get correo => _datosUsuario?['correo'];
  String? get ci => _datosUsuario?['ci'];
  String? get idEmpresa => _datosUsuario?['id_empresa'];
  String? get nombreEmpresa => _datosUsuario?['nombre_empresa'];

  // ── NORMALIZACIÓN DE ROL ──────────────────────────────────────────────────
  String get rolNormalizado {
    final raw = (rol ?? '').trim().toUpperCase().replaceAll(' ', '_').replaceAll('Ñ', 'N');
    if (raw.contains('ADMINISTRADOR_EMPRESA') || raw.contains('ADMIN_EMPRESA')) {
      return 'ADMINISTRADOR_EMPRESA';
    }
    if (raw == 'ADMINISTRADOR' || raw == 'ADMIN') {
      return 'ADMINISTRADOR';
    }
    if (raw.contains('JEFE')) return 'JEFE_DE_OBRA';
    if (raw.contains('SUPERVISOR')) return 'SUPERVISOR_OBRA';
    if (raw.contains('CLIENTE')) return 'CLIENTE';
    if (raw.contains('ELECTRICO')) return 'ELECTRICO';
    if (raw.contains('PLOMERO')) return 'PLOMERO';
    if (raw.contains('MAESTRO')) return 'MAESTRO_ALBANIL';
    if (raw.contains('ALBANIL')) return 'ALBANIL';
    return raw;
  }

  int? get empresaId => int.tryParse(idEmpresa ?? '');
  bool get esAdminGlobal => rolNormalizado == 'ADMINISTRADOR';
  bool get esAdminEmpresa => rolNormalizado == 'ADMINISTRADOR_EMPRESA';
  bool get esJefeObra => rolNormalizado == 'JEFE_DE_OBRA';
  bool get esJefeDeObra => esJefeObra;
  bool get esSupervisor => rolNormalizado == 'SUPERVISOR_OBRA';
  bool get esCliente => rolNormalizado == 'CLIENTE';
  bool get esOperarioCampo => [
        'ELECTRICO',
        'PLOMERO',
        'MAESTRO_ALBANIL',
        'ALBANIL',
      ].contains(rolNormalizado);
  bool get esTrabajadorCampo => esOperarioCampo;

  // ── PERMISOS ─────────────────────────────────────────────────────────────
  List<String> get permisos => mapaPermisosPorRol[rolNormalizado] ?? [];

  bool hasPermission(String permiso) => permisos.contains(permiso);

  bool hasAnyPermission(List<String> lista) =>
      lista.any((p) => permisos.contains(p));

  bool hasAllPermissions(List<String> lista) =>
      lista.every((p) => permisos.contains(p));

  // ── MULTI-TENANT & EMPRESA ACTIVA ────────────────────────────────────────
  bool get esVistaGlobal => _empresaActiva == null && esAdminGlobal;

  int? get idEmpresaActiva {
    if (esAdminGlobal) {
      if (_empresaActiva != null) {
        return int.tryParse(_empresaActiva!['id_empresa']?.toString() ?? '');
      }
      return null;
    }
    return int.tryParse(idEmpresa ?? '');
  }

  String? get nombreEmpresaActiva {
    if (esAdminGlobal) {
      return _empresaActiva?['nombre_empresa'];
    }
    return nombreEmpresa;
  }

  Future<void> seleccionarEmpresa(Map<String, dynamic>? empresa) async {
    _empresaActiva = empresa;
    if (empresa != null) {
      await TokenStorage.saveEmpresaActiva(jsonEncode(empresa));
    } else {
      await TokenStorage.saveEmpresaActiva(null);
    }
    notifyListeners();
  }

  // ── VERIFICACIÓN Y RESTAURACIÓN DE SESIÓN ────────────────────────────────
  Future<void> verificarSesion() async {
    final token = await TokenStorage.getToken();
    if (token != null && token.isNotEmpty) {
      _estaAutenticado = true;
      final nombre = await TokenStorage.getValue('nombre_completo') ?? '';
      final rol = await TokenStorage.getValue('nombre_rol') ?? '';
      final correo = await TokenStorage.getValue('correo') ?? '';
      final ci = await TokenStorage.getValue('ci') ?? '';
      final idEmpresa = await TokenStorage.getValue('id_empresa') ?? '';
      final nombreEmpresa = await TokenStorage.getValue('nombre_empresa') ?? '';

      _datosUsuario = {
        'nombre_completo': nombre,
        'nombre_rol': rol,
        'correo': correo,
        'ci': ci,
        'id_empresa': idEmpresa,
        'nombre_empresa': nombreEmpresa,
      };

      final rawEmpresaActiva = await TokenStorage.getEmpresaActiva();
      if (rawEmpresaActiva != null && rawEmpresaActiva.isNotEmpty) {
        try {
          _empresaActiva = jsonDecode(rawEmpresaActiva) as Map<String, dynamic>;
        } catch (_) {
          _empresaActiva = null;
        }
      }

      notifyListeners();
    }
  }

  void loginExitoso(Map<String, String> datos) {
    _estaAutenticado = true;
    _datosUsuario = datos;
    _empresaActiva = null;
    notifyListeners();
  }

  Future<void> cerrarSesion() async {
    _estaAutenticado = false;
    _datosUsuario = null;
    _empresaActiva = null;
    await TokenStorage.clearToken();
    await TokenStorage.saveEmpresaActiva(null);
    notifyListeners();
  }

  void logout() {
    cerrarSesion();
  }
}