import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../services/auth_provider.dart';
import '../services/auth_service.dart';
import '../theme/app_theme.dart';
import 'recuperar_password_modal.dart';
import 'registro_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _identificadorController = TextEditingController();
  final _passController = TextEditingController();
  bool _obscurePass = true;
  bool _recordarCuenta = true;
  bool _loading = false;
  int _activeTab = 0; // 0: Iniciar sesión, 1: Crear cuenta

  @override
  void dispose() {
    _identificadorController.dispose();
    _passController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      final usuario = await AuthService().login(
        identificador: _identificadorController.text.trim(),
        password: _passController.text.trim(),
      );
      if (!mounted) return;
      Provider.of<AuthProvider>(context, listen: false).loginExitoso({
        'nombre_completo': usuario['nombre_completo']?.toString() ?? '',
        'nombre_rol': usuario['nombre_rol']?.toString() ?? '',
        'ci': usuario['ci']?.toString() ?? '',
        'correo': usuario['correo']?.toString() ?? '',
        'id_empresa': usuario['id_empresa']?.toString() ?? '',
        'nombre_empresa': usuario['nombre_empresa']?.toString() ?? '',
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(e.toString().replaceAll('Exception: ', '')),
        backgroundColor: AppTheme.error,
        behavior: SnackBarBehavior.floating,
      ));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final textMutedColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);
    final textColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Form(
                key: _formKey,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Banner ilustrativo con icono OBRATEC
                    _buildHeaderBanner(isDark),
                    const SizedBox(height: 24),

                    // Selector de Pestañas (Iniciar sesión / Crear cuenta)
                    _buildTabBar(isDark),
                    const SizedBox(height: 24),

                    // Campo 1: Identificador
                    _buildInputField(
                      controller: _identificadorController,
                      label: 'Correo, usuario o CI',
                      hint: 'admin@obratec.com',
                      icon: Icons.person_outline_rounded,
                      isDark: isDark,
                      cardBg: cardBg,
                      borderColor: borderColor,
                      textMutedColor: textMutedColor,
                      textColor: textColor,
                      validator: (v) => (v == null || v.trim().isEmpty)
                          ? 'Ingrese su usuario, correo o CI'
                          : null,
                    ),
                    const SizedBox(height: 16),

                    // Campo 2: Contraseña
                    _buildInputField(
                      controller: _passController,
                      label: 'Contraseña',
                      hint: '••••••••',
                      icon: Icons.lock_outline_rounded,
                      isDark: isDark,
                      cardBg: cardBg,
                      borderColor: borderColor,
                      textMutedColor: textMutedColor,
                      textColor: textColor,
                      obscure: _obscurePass,
                      suffixIcon: IconButton(
                        icon: Icon(
                          _obscurePass ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                          size: 20,
                          color: textMutedColor,
                        ),
                        onPressed: () => setState(() => _obscurePass = !_obscurePass),
                      ),
                      validator: (v) => (v == null || v.isEmpty)
                          ? 'Ingrese su contraseña'
                          : null,
                    ),
                    const SizedBox(height: 14),

                    // Fila: Recordar cuenta switch
                    Row(
                      children: [
                        Transform.scale(
                          scale: 0.8,
                          child: Switch(
                            value: _recordarCuenta,
                            activeThumbColor: AppTheme.primary,
                            activeTrackColor: AppTheme.primary.withValues(alpha: 0.35),
                            inactiveThumbColor: textMutedColor,
                            inactiveTrackColor: isDark ? const Color(0xFF1E293B) : const Color(0xFFE2E8F0),
                            onChanged: (val) => setState(() => _recordarCuenta = val),
                          ),
                        ),
                        Text(
                          'Recordar cuenta',
                          style: GoogleFonts.inter(
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                            color: textMutedColor,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 18),

                    // Botón Principal de Iniciar Sesión
                    SizedBox(
                      width: double.infinity,
                      height: 50,
                      child: ElevatedButton(
                        onPressed: _loading ? null : _handleLogin,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primary,
                          foregroundColor: Colors.white,
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        child: _loading
                            ? const SizedBox(
                                width: 22,
                                height: 22,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2.2,
                                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                ),
                              )
                            : Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  const Icon(Icons.arrow_forward_rounded, size: 20),
                                  const SizedBox(width: 8),
                                  Text(
                                    'Iniciar sesión',
                                    style: GoogleFonts.inter(
                                      fontSize: 15,
                                      fontWeight: FontWeight.w800,
                                      letterSpacing: 0.2,
                                    ),
                                  ),
                                ],
                              ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Enlace ¿Olvidó su contraseña?
                    TextButton(
                      onPressed: () => RecuperarPasswordModal.show(context),
                      style: TextButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      ),
                      child: Text(
                        '¿Olvidó su contraseña?',
                        style: GoogleFonts.inter(
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.primary,
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Términos y condiciones
                    Text(
                      'Al continuar, acepta nuestros',
                      style: GoogleFonts.inter(
                        fontSize: 11.5,
                        color: textMutedColor,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      'Términos y Condiciones',
                      style: GoogleFonts.inter(
                        fontSize: 11.5,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.primary,
                        decoration: TextDecoration.underline,
                        decorationColor: AppTheme.primary,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeaderBanner(bool isDark) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: isDark
              ? [
                  const Color(0xFF2A170A),
                  const Color(0xFF131D31),
                ]
              : [
                  const Color(0xFFFFF3E0),
                  const Color(0xFFFFF7ED),
                ],
        ),
        border: Border.all(
          color: isDark ? const Color(0xFF3B2412) : const Color(0xFFFFEDD5),
          width: 1,
        ),
      ),
      child: Column(
        children: [
          // Icono OBRATEC Naranja
          Container(
            width: 58,
            height: 58,
            decoration: BoxDecoration(
              color: AppTheme.primary,
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: AppTheme.primary.withValues(alpha: 0.35),
                  blurRadius: 14,
                  offset: const Offset(0, 6),
                ),
              ],
            ),
            child: const Icon(
              Icons.construction_rounded,
              color: Colors.white,
              size: 32,
            ),
          ),
          const SizedBox(height: 14),
          // Logo OBRATEC
          Text(
            'OBRATEC',
            style: GoogleFonts.inter(
              fontSize: 22,
              fontWeight: FontWeight.w900,
              letterSpacing: 1.5,
              color: isDark ? Colors.white : const Color(0xFF0F172A),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Gestión integral de obras civiles',
            style: GoogleFonts.inter(
              fontSize: 12.5,
              fontWeight: FontWeight.w500,
              color: isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTabBar(bool isDark) {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF131D31) : const Color(0xFFF1F5F9),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: GestureDetector(
              onTap: () => setState(() => _activeTab = 0),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(vertical: 10),
                decoration: BoxDecoration(
                  color: _activeTab == 0
                      ? (isDark ? const Color(0xFF1E293B) : Colors.white)
                      : Colors.transparent,
                  borderRadius: BorderRadius.circular(8),
                  boxShadow: _activeTab == 0
                      ? [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.05),
                            blurRadius: 4,
                            offset: const Offset(0, 2),
                          ),
                        ]
                      : null,
                ),
                child: Center(
                  child: Text(
                    'Iniciar sesión',
                    style: GoogleFonts.inter(
                      fontSize: 13.5,
                      fontWeight: _activeTab == 0 ? FontWeight.w800 : FontWeight.w600,
                      color: _activeTab == 0
                          ? AppTheme.primary
                          : (isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B)),
                    ),
                  ),
                ),
              ),
            ),
          ),
          Expanded(
            child: GestureDetector(
              onTap: () {
                setState(() => _activeTab = 1);
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const RegistroScreen()),
                ).then((_) {
                  if (mounted) setState(() => _activeTab = 0);
                });
              },
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(vertical: 10),
                decoration: BoxDecoration(
                  color: _activeTab == 1
                      ? (isDark ? const Color(0xFF1E293B) : Colors.white)
                      : Colors.transparent,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Center(
                  child: Text(
                    'Crear cuenta',
                    style: GoogleFonts.inter(
                      fontSize: 13.5,
                      fontWeight: _activeTab == 1 ? FontWeight.w800 : FontWeight.w600,
                      color: _activeTab == 1
                          ? AppTheme.primary
                          : (isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B)),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInputField({
    required TextEditingController controller,
    required String label,
    required String hint,
    required IconData icon,
    required bool isDark,
    required Color cardBg,
    required Color borderColor,
    required Color textMutedColor,
    required Color textColor,
    bool obscure = false,
    Widget? suffixIcon,
    String? Function(String?)? validator,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: GoogleFonts.inter(
            fontSize: 12,
            fontWeight: FontWeight.w700,
            color: textMutedColor,
          ),
        ),
        const SizedBox(height: 6),
        TextFormField(
          controller: controller,
          obscureText: obscure,
          style: GoogleFonts.inter(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: textColor,
          ),
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: GoogleFonts.inter(
              fontSize: 13.5,
              fontWeight: FontWeight.w400,
              color: isDark ? const Color(0xFF475569) : const Color(0xFF94A3B8),
            ),
            filled: true,
            fillColor: cardBg,
            prefixIcon: Icon(icon, size: 20, color: textMutedColor),
            suffixIcon: suffixIcon,
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: borderColor, width: 1),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: borderColor, width: 1),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: AppTheme.primary, width: 1.8),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: AppTheme.error, width: 1),
            ),
          ),
          validator: validator,
        ),
      ],
    );
  }
}