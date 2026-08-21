import 'package:flutter/material.dart';

import '../services/profile_service.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class PerfilScreen extends StatefulWidget {
  const PerfilScreen({super.key});

  @override
  State<PerfilScreen> createState() => _PerfilScreenState();
}

class _PerfilScreenState extends State<PerfilScreen> {
  bool loading = true;
  bool saving = false;

  String message = '';
  bool messageSuccess = false;

  ProfileData? profile;

  final nameController = TextEditingController();
  final mailController = TextEditingController();
  final phoneController = TextEditingController();
  final directionController = TextEditingController();
  final newPasswordController = TextEditingController();
  final confirmPasswordController = TextEditingController();

  @override
  void initState() {
    super.initState();
    loadProfile();
  }

  @override
  void dispose() {
    nameController.dispose();
    mailController.dispose();
    phoneController.dispose();
    directionController.dispose();
    newPasswordController.dispose();
    confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> loadProfile() async {
    setState(() {
      loading = true;
      message = '';
    });

    final result = await ProfileService.getProfile();

    if (!mounted) return;

    if (!result.success || result.profile == null) {
      setState(() {
        loading = false;
        message = result.message;
        messageSuccess = false;
      });
      return;
    }

    final data = result.profile!;

    setState(() {
      profile = data;
      nameController.text = data.nombreRazonSocial;
      mailController.text = data.correo;
      phoneController.text = data.telefono;
      directionController.text = data.direccion;
      loading = false;
    });
  }

  Future<void> saveProfile() async {
    final newPassword = newPasswordController.text.trim();
    final confirmPassword = confirmPasswordController.text.trim();

    if (nameController.text.trim().isEmpty ||
        mailController.text.trim().isEmpty ||
        phoneController.text.trim().isEmpty) {
      setState(() {
        message = 'Nombre, correo y teléfono son obligatorios';
        messageSuccess = false;
      });
      return;
    }

    if (newPassword.isNotEmpty && newPassword != confirmPassword) {
      setState(() {
        message = 'Las nuevas contraseñas no coinciden';
        messageSuccess = false;
      });
      return;
    }

    setState(() {
      saving = true;
      message = '';
    });

    final result = await ProfileService.updateProfile(
      nombreRazonSocial: nameController.text.trim(),
      correo: mailController.text.trim(),
      telefono: phoneController.text.trim(),
      direccion: directionController.text.trim(),
      newPassword: newPassword,
      confirmPassword: confirmPassword,
    );

    if (!mounted) return;

    setState(() {
      saving = false;
      message = result.message;
      messageSuccess = result.success;
    });

    if (result.success) {
      newPasswordController.clear();
      confirmPasswordController.clear();
      await loadProfile();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundBlue,
      body: SafeArea(
        child: Column(
          children: [
            _buildTopBar(),
            Expanded(
              child: loading
                  ? const Center(
                      child: CircularProgressIndicator(
                        color: AppTheme.primaryGreen,
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: loadProfile,
                      color: AppTheme.primaryGreen,
                      child: SingleChildScrollView(
                        physics: const AlwaysScrollableScrollPhysics(),
                        padding: const EdgeInsets.all(18),
                        child: Column(
                          children: [
                            if (profile != null) _buildProfileHero(),
                            const SizedBox(height: 14),
                            if (profile != null) _buildAccountInfo(),
                            const SizedBox(height: 14),
                            _buildEditCard(),
                          ],
                        ),
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTopBar() {
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 10, 14, 12),
      decoration: const BoxDecoration(
        color: AppTheme.primaryGreen,
      ),
      child: Row(
        children: [
          IconButton(
            onPressed: () {
              Navigator.pop(context);
            },
            style: IconButton.styleFrom(
              backgroundColor: Colors.white.withOpacity(0.14),
              foregroundColor: Colors.white,
            ),
            icon: const Icon(Icons.arrow_back),
          ),
          const SizedBox(width: 8),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'MI PERFIL',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 1,
                  ),
                ),
                SizedBox(height: 2),
                Text(
                  'Datos personales y seguridad',
                  style: TextStyle(
                    color: Colors.white70,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: loadProfile,
            style: IconButton.styleFrom(
              backgroundColor: Colors.white.withOpacity(0.14),
              foregroundColor: Colors.white,
            ),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
    );
  }

  Widget _buildProfileHero() {
    final data = profile!;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppTheme.primaryGreen,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primaryGreen.withOpacity(0.22),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Stack(
        children: [
          Positioned(
            right: -16,
            top: -18,
            child: Icon(
              Icons.person,
              size: 110,
              color: Colors.white.withOpacity(0.10),
            ),
          ),
          Row(
            children: [
              Container(
                width: 68,
                height: 68,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.16),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: Colors.white24),
                ),
                child: const Icon(
                  Icons.person,
                  color: Colors.white,
                  size: 38,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      data.nombreRazonSocial.toUpperCase(),
                      style: const TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w900,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      data.correo,
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: Colors.white70,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        _buildWhiteBadge(data.estadoCuenta),
                        const SizedBox(width: 8),
                        _buildWhiteBadge(data.rol),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildAccountInfo() {
    final data = profile!;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppTheme.borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle('DATOS DE CUENTA'),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _buildInfoTile(
                  icon: Icons.alternate_email,
                  label: 'Usuario',
                  value: data.userName,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _buildInfoTile(
                  icon: Icons.badge,
                  label: 'Documento',
                  value: data.documentoIdentidad,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          _buildInfoTile(
            icon: Icons.calendar_month,
            label: 'Fecha registro',
            value: data.fechaRegistro,
          ),
        ],
      ),
    );
  }

  Widget _buildEditCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppTheme.borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle('EDITAR INFORMACIÓN'),
          const SizedBox(height: 12),
          if (message.isNotEmpty) ...[
            AgroErrorBox(
              message: message,
              success: messageSuccess,
            ),
            const SizedBox(height: 14),
          ],
          AgroTextField(
            label: 'Nombre o razón social',
            hint: 'Nombre',
            controller: nameController,
          ),
          const SizedBox(height: 12),
          AgroTextField(
            label: 'Correo',
            hint: 'correo@agro.com',
            controller: mailController,
            keyboardType: TextInputType.emailAddress,
          ),
          const SizedBox(height: 12),
          AgroTextField(
            label: 'Teléfono',
            hint: '70000000',
            controller: phoneController,
            keyboardType: TextInputType.phone,
          ),
          const SizedBox(height: 12),
          AgroTextField(
            label: 'Dirección',
            hint: 'Dirección',
            controller: directionController,
          ),
          const SizedBox(height: 20),
          _buildPasswordBox(),
          const SizedBox(height: 18),
          AgroButton(
            text: 'Guardar cambios',
            loading: saving,
            onPressed: saveProfile,
          ),
        ],
      ),
    );
  }

  Widget _buildPasswordBox() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(
                Icons.lock_outline,
                color: AppTheme.primaryGreen,
                size: 20,
              ),
              SizedBox(width: 8),
              Text(
                'CAMBIAR CONTRASEÑA',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w900,
                  color: AppTheme.slateText,
                  letterSpacing: 1,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          const Text(
            'Deja estos campos vacíos si no quieres cambiar tu contraseña.',
            style: TextStyle(
              fontSize: 11,
              color: AppTheme.mutedText,
            ),
          ),
          const SizedBox(height: 12),
          AgroTextField(
            label: 'Nueva contraseña',
            hint: '••••••••',
            controller: newPasswordController,
            obscureText: true,
          ),
          const SizedBox(height: 12),
          AgroTextField(
            label: 'Confirmar contraseña',
            hint: '••••••••',
            controller: confirmPasswordController,
            obscureText: true,
          ),
        ],
      ),
    );
  }

  Widget _buildInfoTile({
    required IconData icon,
    required String label,
    required String value,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.borderColor),
      ),
      child: Row(
        children: [
          Icon(
            icon,
            color: AppTheme.primaryGreen,
            size: 20,
          ),
          const SizedBox(width: 9),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label.toUpperCase(),
                  style: const TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.w900,
                    color: AppTheme.mutedText,
                    letterSpacing: 1,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  value.isEmpty ? 'Sin datos' : value,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w900,
                    color: AppTheme.slateText,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWhiteBadge(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: 9,
        vertical: 5,
      ),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.14),
        borderRadius: BorderRadius.circular(30),
        border: Border.all(color: Colors.white24),
      ),
      child: Text(
        text.toUpperCase(),
        style: const TextStyle(
          fontSize: 8,
          fontWeight: FontWeight.w900,
          color: Colors.white,
          letterSpacing: 0.8,
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.w900,
        color: AppTheme.mutedText,
        letterSpacing: 1.4,
      ),
    );
  }
}