import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../theme/app_theme.dart';
import '../widgets/ev_widgets.dart';

class RegistroScreen extends StatefulWidget {
  const RegistroScreen({super.key});

  @override
  State<RegistroScreen> createState() => _RegistroScreenState();
}

class _RegistroScreenState extends State<RegistroScreen> {
  final _formKey = GlobalKey<FormState>();

  final _ciCtrl = TextEditingController();
  final _nombreCtrl = TextEditingController();
  final _usuarioCtrl = TextEditingController();
  final _correoCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  final _passConfirmCtrl = TextEditingController();
  final _telefonoCtrl = TextEditingController();
  final _direccionCtrl = TextEditingController();
  final _empresaCtrl = TextEditingController();

  bool _obscurePass = true;
  bool _obscureConfirm = true;
  bool _loading = false;
  String _error = '';

  @override
  void dispose() {
    _ciCtrl.dispose();
    _nombreCtrl.dispose();
    _usuarioCtrl.dispose();
    _correoCtrl.dispose();
    _passCtrl.dispose();
    _passConfirmCtrl.dispose();
    _telefonoCtrl.dispose();
    _direccionCtrl.dispose();
    _empresaCtrl.dispose();
    super.dispose();
  }

  Future<void> _handleRegister() async {
    if (!_formKey.currentState!.validate()) return;

    final pass = _passCtrl.text.trim();
    if (pass.length < 8) {
      setState(() => _error = 'La contraseña debe tener al menos 8 caracteres.');
      return;
    }
    if (!RegExp(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\/`~;]').hasMatch(pass)) {
      setState(() => _error = r'La contraseña debe contener al menos 1 símbolo especial (ej: @, #, $, %, *, !).');
      return;
    }

    if (pass != _passConfirmCtrl.text.trim()) {
      setState(() => _error = 'Las contraseñas no coinciden.');
      return;
    }

    setState(() {
      _loading = true;
      _error = '';
    });

    try {
      await AuthService().register(
        ci: _ciCtrl.text.trim(),
        nombreCompleto: _nombreCtrl.text.trim(),
        nombreUsuario: _usuarioCtrl.text.trim(),
        correo: _correoCtrl.text.trim(),
        password: pass,
        telefono: _telefonoCtrl.text.trim(),
        direccion: _direccionCtrl.text.trim(),
        nombreEmpresa: _empresaCtrl.text.trim(),
      );

      if (!mounted) return;

      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (ctx) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppTheme.radiusLarge)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppTheme.successBg,
                  shape: BoxShape.circle,
                  border: Border.all(color: AppTheme.success.withValues(alpha: 0.3)),
                ),
                child: const Icon(Icons.check_circle_rounded, color: AppTheme.success, size: 38),
              ),
              const SizedBox(height: 16),
              const Text(
                '¡Cuenta Creada!',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: AppTheme.textPrimary),
              ),
              const SizedBox(height: 6),
              const Text(
                'Tu usuario ha sido registrado exitosamente. Ya puedes iniciar sesión con tus credenciales.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
              ),
              const SizedBox(height: 20),
              ObratecPrimaryButton(
                label: 'Ir al Inicio de Sesión',
                onPressed: () {
                  Navigator.pop(ctx);
                  Navigator.pop(context);
                },
              ),
            ],
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
      });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: const Text('Crear Cuenta'),
        elevation: 0,
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const ObratecLogo(fontSize: 20),
                    const SizedBox(height: 12),
                    const ObratecDivider(),
                    const SizedBox(height: 24),

                    Text(
                      'Registro de Usuario',
                      style: Theme.of(context).textTheme.displayMedium,
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Ingresa tus datos para registrarte en la plataforma OBRATEC.',
                      style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                    ),
                    const SizedBox(height: 20),

                    if (_error.isNotEmpty) ...[
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppTheme.errorBg,
                          borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                          border: Border.all(color: AppTheme.error.withValues(alpha: 0.3)),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.error_outline, size: 18, color: AppTheme.error),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(_error, style: const TextStyle(fontSize: 12, color: AppTheme.error, fontWeight: FontWeight.w600)),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],

                    // CI
                    ObratecTextField(
                      label: 'CARNET DE IDENTIDAD (CI) *',
                      hint: 'Ej: 9781936',
                      controller: _ciCtrl,
                      keyboardType: TextInputType.text,
                      validator: (v) => (v == null || v.trim().isEmpty) ? 'Ingrese su carnet de identidad' : null,
                    ),
                    const SizedBox(height: 14),

                    // Nombre Completo
                    ObratecTextField(
                      label: 'NOMBRE COMPLETO *',
                      hint: 'Ej: Carlos Pérez Mendoza',
                      controller: _nombreCtrl,
                      keyboardType: TextInputType.name,
                      validator: (v) => (v == null || v.trim().isEmpty) ? 'Ingrese su nombre completo' : null,
                    ),
                    const SizedBox(height: 14),

                    // Nombre de Usuario
                    ObratecTextField(
                      label: 'NOMBRE DE USUARIO *',
                      hint: 'Ej: carlosperez',
                      controller: _usuarioCtrl,
                      keyboardType: TextInputType.text,
                      validator: (v) => (v == null || v.trim().isEmpty) ? 'Ingrese un nombre de usuario' : null,
                    ),
                    const SizedBox(height: 14),

                    // Correo Electrónico
                    ObratecTextField(
                      label: 'CORREO ELECTRÓNICO *',
                      hint: 'carlos@obratec.com',
                      controller: _correoCtrl,
                      keyboardType: TextInputType.emailAddress,
                      validator: (v) {
                        if (v == null || v.trim().isEmpty) return 'Ingrese su correo';
                        if (!v.contains('@')) return 'Correo electrónico inválido';
                        return null;
                      },
                    ),
                    const SizedBox(height: 14),

                    // Contraseña
                    ObratecTextField(
                      label: 'CONTRASEÑA *',
                      hint: 'Mínimo 8 caracteres y 1 símbolo',
                      controller: _passCtrl,
                      obscure: _obscurePass,
                      suffixIcon: IconButton(
                        icon: Icon(_obscurePass ? Icons.visibility_off_outlined : Icons.visibility_outlined, size: 18, color: AppTheme.textMuted),
                        onPressed: () => setState(() => _obscurePass = !_obscurePass),
                      ),
                      validator: (v) {
                        if (v == null || v.trim().isEmpty) return 'Ingrese una contraseña';
                        if (v.trim().length < 8) return 'Mínimo 8 caracteres';
                        if (!RegExp(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\/`~;]').hasMatch(v)) {
                          return 'Debe incluir al menos 1 símbolo especial (@, #, \$, etc.)';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 14),

                    // Confirmar Contraseña
                    ObratecTextField(
                      label: 'CONFIRMAR CONTRASEÑA *',
                      hint: 'Repita su contraseña',
                      controller: _passConfirmCtrl,
                      obscure: _obscureConfirm,
                      suffixIcon: IconButton(
                        icon: Icon(_obscureConfirm ? Icons.visibility_off_outlined : Icons.visibility_outlined, size: 18, color: AppTheme.textMuted),
                        onPressed: () => setState(() => _obscureConfirm = !_obscureConfirm),
                      ),
                      validator: (v) => (v == null || v.trim().isEmpty) ? 'Confirme su contraseña' : null,
                    ),
                    const SizedBox(height: 14),

                    // Teléfono
                    ObratecTextField(
                      label: 'TELÉFONO (OPCIONAL)',
                      hint: 'Ej: 77012345',
                      controller: _telefonoCtrl,
                      keyboardType: TextInputType.phone,
                    ),
                    const SizedBox(height: 14),

                    // Dirección
                    ObratecTextField(
                      label: 'DIRECCIÓN (OPCIONAL)',
                      hint: 'Ej: Av. Cristo Redentor, Santa Cruz',
                      controller: _direccionCtrl,
                      keyboardType: TextInputType.streetAddress,
                    ),
                    const SizedBox(height: 14),

                    // Nombre Empresa (Opcional)
                    ObratecTextField(
                      label: 'EMPRESA / CONSTRUCTORA (OPCIONAL)',
                      hint: 'Dejar en blanco si es cliente particular',
                      controller: _empresaCtrl,
                      keyboardType: TextInputType.text,
                    ),
                    const SizedBox(height: 24),

                    // Botón Registrar
                    ObratecPrimaryButton(
                      label: 'Crear Cuenta',
                      loading: _loading,
                      icon: Icons.person_add_rounded,
                      onPressed: _handleRegister,
                    ),
                    const SizedBox(height: 18),

                    // Enlace Iniciar Sesión
                    Center(
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Text('¿Ya tienes una cuenta?', style: TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
                          TextButton(
                            onPressed: () => Navigator.pop(context),
                            child: const Text('Iniciar Sesión', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: AppTheme.primary)),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
