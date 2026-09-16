import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../services/auth_provider.dart';
import '../services/auth_service.dart';
import '../theme/app_theme.dart';
import '../widgets/ev_widgets.dart';
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
  bool _loading = false;

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
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(e.toString().replaceAll('Exception: ', '')),
        backgroundColor: AppTheme.error,
      ));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final isWide = MediaQuery.of(context).size.width > 640;
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
    final subColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);
    final outlineBorder = isDark ? const Color(0xFF334155) : const Color(0xFFCBD5E1);

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Row(
        children: [
          Expanded(
            child: SafeArea(
              child: Center(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 36),
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 420),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          ObratecLogo(fontSize: 22, darkBackground: isDark),
                          const SizedBox(height: 12),
                          const ObratecDivider(),
                          const SizedBox(height: 28),
                          Text(
                            'Acceso a OBRATEC',
                            style: GoogleFonts.inter(
                              fontSize: 24,
                              fontWeight: FontWeight.w900,
                              color: titleColor,
                              letterSpacing: -0.4,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            'Ingresa con tu Usuario, Correo o Carnet de Identidad.',
                            style: GoogleFonts.inter(
                              fontSize: 13,
                              color: subColor,
                            ),
                          ),
                          const SizedBox(height: 28),

                          // Campo Identificador (CI / Usuario / Correo)
                          ObratecTextField(
                            label: 'USUARIO, CORREO O CI *',
                            hint: 'Ej: admin, supervisor@obratec.com o 9781936',
                            controller: _identificadorController,
                            keyboardType: TextInputType.emailAddress,
                            autofocus: true,
                            validator: (v) => (v == null || v.trim().isEmpty)
                                ? 'Ingrese su usuario, correo o CI'
                                : null,
                          ),
                          const SizedBox(height: 18),

                          // Campo Contraseña
                          ObratecTextField(
                            label: 'CONTRASEÑA *',
                            hint: '••••••••',
                            controller: _passController,
                            obscure: _obscurePass,
                            suffixIcon: IconButton(
                              icon: Icon(
                                _obscurePass
                                    ? Icons.visibility_off_outlined
                                    : Icons.visibility_outlined,
                                size: 18,
                                color: const Color(0xFF94A3B8),
                              ),
                              onPressed: () =>
                                  setState(() => _obscurePass = !_obscurePass),
                            ),
                            validator: (v) => (v == null || v.isEmpty)
                                ? 'Ingrese su contraseña'
                                : null,
                          ),
                          const SizedBox(height: 8),

                          // Enlace Recuperar Contraseña (CU08)
                          Align(
                            alignment: Alignment.centerRight,
                            child: TextButton(
                              onPressed: () => RecuperarPasswordModal.show(context),
                              style: TextButton.styleFrom(
                                padding: EdgeInsets.zero,
                                minimumSize: const Size(50, 30),
                                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                              ),
                              child: Text(
                                '¿Olvidó su contraseña?',
                                style: GoogleFonts.inter(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w700,
                                  color: AppTheme.primary,
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(height: 24),

                          // Botón Iniciar Sesión
                          ObratecPrimaryButton(
                            label: 'Iniciar Sesión',
                            loading: _loading,
                            onPressed: _handleLogin,
                            icon: Icons.login_rounded,
                          ),
                          const SizedBox(height: 14),

                          // Botón Crear Usuario
                          OutlinedButton(
                            onPressed: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(builder: (_) => const RegistroScreen()),
                              );
                            },
                            style: OutlinedButton.styleFrom(
                              minimumSize: const Size(double.infinity, 48),
                              side: BorderSide(color: outlineBorder),
                            ),
                            child: Text(
                              'Crear usuario',
                              style: GoogleFonts.inter(
                                fontSize: 14,
                                fontWeight: FontWeight.w700,
                                color: titleColor,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),

          // Panel lateral para tablets / desktops
          if (isWide)
            Expanded(
              child: Container(
                color: isDark ? const Color(0xFF0F172A) : const Color(0xFFF1F5F9),
                child: Center(
                  child: Padding(
                    padding: const EdgeInsets.all(48),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        ObratecLogo(fontSize: 28, darkBackground: isDark),
                        const SizedBox(height: 18),
                        Text(
                          'Sistema Integral de Gestión de Obras',
                          style: GoogleFonts.inter(
                            fontSize: 22,
                            fontWeight: FontWeight.w900,
                            color: titleColor,
                          ),
                        ),
                        const SizedBox(height: 10),
                        Text(
                          'Control de avance físico, estructuras WBS, cuadrillas y materiales en tiempo real.',
                          style: GoogleFonts.inter(
                            fontSize: 14,
                            color: subColor,
                            height: 1.5,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}