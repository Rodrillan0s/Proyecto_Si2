import 'package:flutter/material.dart';
import '../services/recovery_service.dart';
import '../theme/app_theme.dart';
import '../widgets/ev_widgets.dart';

class RecuperarPasswordModal extends StatefulWidget {
  const RecuperarPasswordModal({super.key});

  static Future<void> show(BuildContext context) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const RecuperarPasswordModal(),
    );
  }

  @override
  State<RecuperarPasswordModal> createState() => _RecuperarPasswordModalState();
}

class _RecuperarPasswordModalState extends State<RecuperarPasswordModal> {
  final RecoveryService _service = RecoveryService();

  int _paso = 1; // 1: Correo, 2: Código, 3: Nueva contraseña, 4: Éxito
  bool _loading = false;
  String _error = '';

  final _correoCtrl = TextEditingController();
  final _codigoCtrl = TextEditingController();
  final _passNuevaCtrl = TextEditingController();
  final _passConfirmCtrl = TextEditingController();

  bool _obscurePassNueva = true;
  bool _obscurePassConfirm = true;

  String? _solicitudId;
  String? _resetToken;

  @override
  void dispose() {
    _correoCtrl.dispose();
    _codigoCtrl.dispose();
    _passNuevaCtrl.dispose();
    _passConfirmCtrl.dispose();
    super.dispose();
  }

  Future<void> _solicitarCodigo() async {
    final correo = _correoCtrl.text.trim();
    if (correo.isEmpty || !correo.contains('@')) {
      setState(() => _error = 'Ingrese un correo electrónico válido');
      return;
    }

    setState(() {
      _loading = true;
      _error = '';
    });

    try {
      final res = await _service.solicitarRecuperacion(correo);
      if (!mounted) return;
      setState(() {
        _solicitudId = res['solicitud_id']?.toString();
        _paso = 2;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
        _loading = false;
      });
    }
  }

  Future<void> _verificarCodigo() async {
    final codigo = _codigoCtrl.text.trim();
    if (codigo.isEmpty || codigo.length < 4) {
      setState(() => _error = 'Ingrese el código recibido en su correo');
      return;
    }

    setState(() {
      _loading = true;
      _error = '';
    });

    try {
      final res = await _service.verificarCodigo(
        solicitudId: _solicitudId!,
        codigo: codigo,
      );
      if (!mounted) return;
      setState(() {
        _resetToken = res['reset_token']?.toString();
        _paso = 3;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
        _loading = false;
      });
    }
  }

  Future<void> _restablecerPassword() async {
    final p1 = _passNuevaCtrl.text.trim();
    final p2 = _passConfirmCtrl.text.trim();

    if (p1.length < 6) {
      setState(() => _error = 'La contraseña debe tener al menos 6 caracteres');
      return;
    }
    if (p1 != p2) {
      setState(() => _error = 'Las contraseñas no coinciden');
      return;
    }

    setState(() {
      _loading = true;
      _error = '';
    });

    try {
      await _service.restablecerPassword(
        solicitudId: _solicitudId!,
        resetToken: _resetToken!,
        passwordNueva: p1,
        confirmarPassword: p2,
      );
      if (!mounted) return;
      setState(() {
        _paso = 4;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;

    return Container(
      padding: EdgeInsets.fromLTRB(24, 20, 24, 24 + bottomInset),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF131D31) : Colors.white,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(AppTheme.radiusLarge)),
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Handle bar
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: AppTheme.border,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 18),

            // Header con Paso
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'RECUPERACIÓN DE CONTRASEÑA',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1,
                        color: AppTheme.primary,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      _paso == 1
                          ? 'Ingresa tu Correo'
                          : _paso == 2
                              ? 'Verifica el Código'
                              : _paso == 3
                                  ? 'Nueva Contraseña'
                                  : '¡Listo!',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900),
                    ),
                  ],
                ),
                if (_paso <= 3)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryLight,
                      borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                    ),
                    child: Text(
                      'Paso $_paso / 3',
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.primaryDark),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 16),

            // Error banner
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

            // PASO 1: CORREO
            if (_paso == 1) ...[
              const Text(
                'Te enviaremos un código de seguridad de un solo uso para verificar tu identidad.',
                style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
              ),
              const SizedBox(height: 18),
              ObratecTextField(
                label: 'CORREO ELECTRÓNICO *',
                hint: 'usuario@obratec.com',
                controller: _correoCtrl,
                keyboardType: TextInputType.emailAddress,
                autofocus: true,
              ),
              const SizedBox(height: 24),
              ObratecPrimaryButton(
                label: 'Enviar Código de Seguridad',
                loading: _loading,
                icon: Icons.send_rounded,
                onPressed: _solicitarCodigo,
              ),
            ],

            // PASO 2: CÓDIGO
            if (_paso == 2) ...[
              Text(
                'Hemos enviado un código a ${_correoCtrl.text}. Ingrésalo a continuación:',
                style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
              ),
              const SizedBox(height: 18),
              ObratecTextField(
                label: 'CÓDIGO DE VERIFICACIÓN *',
                hint: 'Ej: 123456',
                controller: _codigoCtrl,
                keyboardType: TextInputType.number,
                autofocus: true,
              ),
              const SizedBox(height: 24),
              ObratecPrimaryButton(
                label: 'Validar Código',
                loading: _loading,
                icon: Icons.check_circle_outline_rounded,
                onPressed: _verificarCodigo,
              ),
              const SizedBox(height: 10),
              Center(
                child: TextButton(
                  onPressed: _loading ? null : () => setState(() => _paso = 1),
                  child: const Text('← Cambiar correo', style: TextStyle(fontSize: 12)),
                ),
              ),
            ],

            // PASO 3: NUEVA CONTRASEÑA
            if (_paso == 3) ...[
              const Text(
                'Crea una contraseña segura con al menos 6 caracteres.',
                style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
              ),
              const SizedBox(height: 18),
              ObratecTextField(
                label: 'NUEVA CONTRASEÑA *',
                hint: 'Mínimo 6 caracteres',
                controller: _passNuevaCtrl,
                obscure: _obscurePassNueva,
                suffixIcon: IconButton(
                  icon: Icon(
                    _obscurePassNueva ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                    size: 18,
                    color: AppTheme.textMuted,
                  ),
                  onPressed: () => setState(() => _obscurePassNueva = !_obscurePassNueva),
                ),
              ),
              const SizedBox(height: 14),
              ObratecTextField(
                label: 'CONFIRMAR CONTRASEÑA *',
                hint: 'Repite tu nueva contraseña',
                controller: _passConfirmCtrl,
                obscure: _obscurePassConfirm,
                suffixIcon: IconButton(
                  icon: Icon(
                    _obscurePassConfirm ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                    size: 18,
                    color: AppTheme.textMuted,
                  ),
                  onPressed: () => setState(() => _obscurePassConfirm = !_obscurePassConfirm),
                ),
              ),
              const SizedBox(height: 24),
              ObratecPrimaryButton(
                label: 'Guardar Nueva Contraseña',
                loading: _loading,
                icon: Icons.lock_reset_rounded,
                onPressed: _restablecerPassword,
              ),
            ],

            // PASO 4: ÉXITO
            if (_paso == 4) ...[
              Center(
                child: Column(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppTheme.successBg,
                        shape: BoxShape.circle,
                        border: Border.all(color: AppTheme.success.withValues(alpha: 0.3)),
                      ),
                      child: const Icon(Icons.check_circle_rounded, color: AppTheme.success, size: 42),
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      '¡Contraseña Actualizada!',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: AppTheme.textPrimary),
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'Ya puedes iniciar sesión con tus nuevas credenciales.',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                    ),
                    const SizedBox(height: 24),
                    ObratecPrimaryButton(
                      label: 'Entendido, volver al Login',
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
