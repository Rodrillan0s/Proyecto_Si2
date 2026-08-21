import 'api_client.dart';

class ProfileService {
  static Future<ProfileResult> getProfile() async {
    final data = await ApiClient.get(
      '/profile',
      requiresAuth: true,
    );

    if (data['success'] != true) {
      return ProfileResult(
        success: false,
        message: data['message'] ?? 'No se pudo cargar el perfil',
      );
    }

    return ProfileResult(
      success: true,
      message: data['message'] ?? 'Perfil cargado correctamente',
      profile: ProfileData.fromJson(data['data'] ?? {}),
    );
  }

  static Future<ProfileResult> updateProfile({
    required String nombreRazonSocial,
    required String correo,
    required String telefono,
    required String direccion,
    String? newPassword,
    String? confirmPassword,
  }) async {
    final body = {
      'nombre_razon_social': nombreRazonSocial,
      'correo': correo,
      'telefono': telefono,
      'direccion': direccion,
      if (newPassword != null && newPassword.trim().isNotEmpty)
        'newPassword': newPassword,
      if (confirmPassword != null && confirmPassword.trim().isNotEmpty)
        'confirmPassword': confirmPassword,
    };

    final data = await ApiClient.put(
      '/update-profile',
      body,
      requiresAuth: true,
    );

    if (data['success'] != true) {
      return ProfileResult(
        success: false,
        message: data['message'] ?? 'No se pudo actualizar el perfil',
      );
    }

    return ProfileResult(
      success: true,
      message: data['message'] ?? 'Perfil actualizado correctamente',
    );
  }
}

class ProfileResult {
  final bool success;
  final String message;
  final ProfileData? profile;

  ProfileResult({
    required this.success,
    required this.message,
    this.profile,
  });
}

class ProfileData {
  final String userName;
  final String nombreRazonSocial;
  final String correo;
  final String documentoIdentidad;
  final String direccion;
  final String telefono;
  final String estadoCuenta;
  final String rol;
  final String fechaRegistro;

  ProfileData({
    required this.userName,
    required this.nombreRazonSocial,
    required this.correo,
    required this.documentoIdentidad,
    required this.direccion,
    required this.telefono,
    required this.estadoCuenta,
    required this.rol,
    required this.fechaRegistro,
  });

  factory ProfileData.fromJson(Map<String, dynamic> json) {
    return ProfileData(
      userName: json['user_name']?.toString() ?? '',
      nombreRazonSocial: json['nombre_razon_social']?.toString() ?? '',
      correo: json['correo']?.toString() ?? '',
      documentoIdentidad: json['documento_identidad']?.toString() ?? '',
      direccion: json['direccion']?.toString() ?? '',
      telefono: json['telefono']?.toString() ?? '',
      estadoCuenta: json['estado_cuenta']?.toString() ?? '',
      rol: json['rol']?.toString() ?? '',
      fechaRegistro: json['fecha_registro']?.toString() ?? '',
    );
  }
}