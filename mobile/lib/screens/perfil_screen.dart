import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../services/auth_provider.dart';
import '../services/profile_service.dart';
import '../theme/app_theme.dart';
import '../theme/theme_provider.dart';
import '../widgets/ev_widgets.dart';

class PerfilScreen extends StatefulWidget {
  const PerfilScreen({super.key});

  @override
  State<PerfilScreen> createState() => _PerfilScreenState();
}

class _PerfilScreenState extends State<PerfilScreen> {
  Map<String, dynamic>? _perfil;
  bool _cargando = true;

  @override
  void initState() {
    super.initState();
    _cargarPerfil();
  }

  Future<void> _cargarPerfil() async {
    setState(() => _cargando = true);

    try {
      final perfil = await ProfileService().obtenerPerfil();

      if (!mounted) return;

      setState(() {
        _perfil = perfil;
        _cargando = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() => _cargando = false);
      _mostrarError(e.toString().replaceAll('Exception: ', ''));
    }
  }

  // ── MODAL PARA EDITAR INFORMACIÓN DE CONTACTO ─────────────────────────────
  void _abrirModalEditarContacto() {
    if (_perfil == null) return;

    final formKey = GlobalKey<FormState>();
    final telCtrl = TextEditingController(text: _texto(_perfil!['telefono']));
    final emailCtrl = TextEditingController(text: _texto(_perfil!['correo']));
    final dirCtrl = TextEditingController(text: _texto(_perfil!['direccion']));
    bool guardando = false;
    String errorModal = '';

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            final isDark = Theme.of(context).brightness == Brightness.dark;
            final bottomInset = MediaQuery.of(context).viewInsets.bottom;
            final sheetBg = isDark ? const Color(0xFF131D31) : Colors.white;
            final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
            final subColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);
            final dividerColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);

            return Container(
              padding: EdgeInsets.fromLTRB(20, 16, 20, 24 + bottomInset),
              decoration: BoxDecoration(
                color: sheetBg,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
              ),
              child: SingleChildScrollView(
                child: Form(
                  key: formKey,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Center(
                        child: Container(
                          width: 36,
                          height: 4,
                          decoration: BoxDecoration(
                            color: isDark ? const Color(0xFF334155) : const Color(0xFFCBD5E1),
                            borderRadius: BorderRadius.circular(2),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: isDark ? const Color(0xFF2E1C14) : const Color(0xFFFFF7ED),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: const Icon(Icons.edit_note_rounded, color: AppTheme.primary, size: 22),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Editar Información de Contacto',
                                  style: GoogleFonts.inter(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w900,
                                    color: titleColor,
                                  ),
                                ),
                                Text(
                                  'Actualiza tu teléfono, correo y dirección.',
                                  style: GoogleFonts.inter(fontSize: 11.5, color: subColor),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      Divider(color: dividerColor),
                      const SizedBox(height: 14),

                      if (errorModal.isNotEmpty) ...[
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: AppTheme.errorBg,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: AppTheme.error.withValues(alpha: 0.3)),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.error_outline, size: 16, color: AppTheme.error),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(errorModal, style: GoogleFonts.inter(fontSize: 12, color: AppTheme.error, fontWeight: FontWeight.w600)),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 14),
                      ],

                      ObratecTextField(
                        label: 'TELÉFONO *',
                        hint: 'Ej: 77012345',
                        controller: telCtrl,
                        keyboardType: TextInputType.phone,
                        validator: (v) => (v == null || v.trim().isEmpty) ? 'Ingrese su teléfono' : null,
                      ),
                      const SizedBox(height: 12),

                      ObratecTextField(
                        label: 'CORREO ELECTRÓNICO *',
                        hint: 'usuario@obratec.com',
                        controller: emailCtrl,
                        keyboardType: TextInputType.emailAddress,
                        validator: (v) {
                          if (v == null || v.trim().isEmpty) return 'Ingrese su correo';
                          if (!v.contains('@')) return 'Correo inválido';
                          return null;
                        },
                      ),
                      const SizedBox(height: 12),

                      ObratecTextField(
                        label: 'DIRECCIÓN *',
                        hint: 'Ej: Av. Cristo Redentor, Santa Cruz',
                        controller: dirCtrl,
                        keyboardType: TextInputType.streetAddress,
                        validator: (v) => (v == null || v.trim().isEmpty) ? 'Ingrese su dirección' : null,
                      ),
                      const SizedBox(height: 20),

                      ObratecPrimaryButton(
                        label: 'Guardar Cambios',
                        loading: guardando,
                        icon: Icons.check_circle_outline_rounded,
                        onPressed: () async {
                          if (!formKey.currentState!.validate()) return;

                          setModalState(() {
                            guardando = true;
                            errorModal = '';
                          });

                          try {
                            await ProfileService().actualizarPerfil(
                              ci: _texto(_perfil!['ci']),
                              telefono: telCtrl.text.trim(),
                              correo: emailCtrl.text.trim(),
                              direccion: dirCtrl.text.trim(),
                            );

                            if (!ctx.mounted) return;
                            Navigator.pop(ctx);

                            if (mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('Datos de contacto actualizados correctamente.'),
                                  backgroundColor: AppTheme.success,
                                ),
                              );
                              _cargarPerfil();
                            }
                          } catch (e) {
                            setModalState(() {
                              errorModal = e.toString().replaceAll('Exception: ', '');
                              guardando = false;
                            });
                          }
                        },
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        );
      },
    );
  }

  // ── MODAL PARA CAMBIAR CONTRASEÑA ─────────────────────────────────────────
  void _abrirModalCambiarPassword() {
    final actualCtrl = TextEditingController();
    final nuevaCtrl = TextEditingController();
    final confirmCtrl = TextEditingController();

    bool obscureActual = true;
    bool obscureNueva = true;
    bool obscureConfirm = true;
    bool guardandoPass = false;
    String errorModal = '';

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            final isDark = Theme.of(context).brightness == Brightness.dark;
            final bottomInset = MediaQuery.of(context).viewInsets.bottom;
            final sheetBg = isDark ? const Color(0xFF131D31) : Colors.white;
            final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
            final subColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);
            final dividerColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);

            return Container(
              padding: EdgeInsets.fromLTRB(20, 16, 20, 24 + bottomInset),
              decoration: BoxDecoration(
                color: sheetBg,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
              ),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Center(
                      child: Container(
                        width: 36,
                        height: 4,
                        decoration: BoxDecoration(
                          color: isDark ? const Color(0xFF334155) : const Color(0xFFCBD5E1),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: isDark ? const Color(0xFF2E1C14) : const Color(0xFFFFF7ED),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Icon(Icons.lock_reset_rounded, color: AppTheme.primary, size: 20),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Cambiar Contraseña',
                                style: GoogleFonts.inter(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w900,
                                  color: titleColor,
                                ),
                              ),
                              Text(
                                'Ingresa tu clave actual y define tu nueva contraseña.',
                                style: GoogleFonts.inter(fontSize: 11.5, color: subColor),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Divider(color: dividerColor),
                    const SizedBox(height: 14),

                    if (errorModal.isNotEmpty) ...[
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: AppTheme.errorBg,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: AppTheme.error.withValues(alpha: 0.3)),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.error_outline, size: 16, color: AppTheme.error),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(errorModal, style: GoogleFonts.inter(fontSize: 12, color: AppTheme.error, fontWeight: FontWeight.w600)),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 14),
                    ],

                    ObratecTextField(
                      label: 'CONTRASEÑA ACTUAL *',
                      hint: '••••••••',
                      controller: actualCtrl,
                      obscure: obscureActual,
                      suffixIcon: IconButton(
                        icon: Icon(obscureActual ? Icons.visibility_off_outlined : Icons.visibility_outlined, size: 18, color: const Color(0xFF94A3B8)),
                        onPressed: () => setModalState(() => obscureActual = !obscureActual),
                      ),
                    ),
                    const SizedBox(height: 14),

                    ObratecTextField(
                      label: 'NUEVA CONTRASEÑA *',
                      hint: 'Mínimo 8 caracteres (A-Z, a-z, 0-9, símbolo)',
                      controller: nuevaCtrl,
                      obscure: obscureNueva,
                      suffixIcon: IconButton(
                        icon: Icon(obscureNueva ? Icons.visibility_off_outlined : Icons.visibility_outlined, size: 18, color: const Color(0xFF94A3B8)),
                        onPressed: () => setModalState(() => obscureNueva = !obscureNueva),
                      ),
                    ),
                    const SizedBox(height: 14),

                    ObratecTextField(
                      label: 'CONFIRMAR NUEVA CONTRASEÑA *',
                      hint: 'Repita la nueva contraseña',
                      controller: confirmCtrl,
                      obscure: obscureConfirm,
                      suffixIcon: IconButton(
                        icon: Icon(obscureConfirm ? Icons.visibility_off_outlined : Icons.visibility_outlined, size: 18, color: const Color(0xFF94A3B8)),
                        onPressed: () => setModalState(() => obscureConfirm = !obscureConfirm),
                      ),
                    ),
                    const SizedBox(height: 20),

                    ObratecPrimaryButton(
                      label: 'Actualizar Contraseña',
                      loading: guardandoPass,
                      icon: Icons.check_circle_outline_rounded,
                      onPressed: () async {
                        final act = actualCtrl.text.trim();
                        final nva = nuevaCtrl.text.trim();
                        final cnf = confirmCtrl.text.trim();

                        if (act.isEmpty || nva.isEmpty || cnf.isEmpty) {
                          setModalState(() => errorModal = 'Todos los campos son obligatorios.');
                          return;
                        }
                        if (nva.length < 8) {
                          setModalState(() => errorModal = 'La nueva contraseña debe tener al menos 8 caracteres.');
                          return;
                        }
                        if (!RegExp(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\/`~;]').hasMatch(nva)) {
                          setModalState(() => errorModal = 'Debe incluir al menos 1 símbolo especial (ej. @, #, \$, %).');
                          return;
                        }
                        if (nva != cnf) {
                          setModalState(() => errorModal = 'Las contraseñas no coinciden.');
                          return;
                        }

                        setModalState(() {
                          guardandoPass = true;
                          errorModal = '';
                        });

                        try {
                          await ProfileService().cambiarPassword(
                            passwordActual: act,
                            passwordNueva: nva,
                            confirmarPassword: cnf,
                          );

                          if (!ctx.mounted) return;
                          Navigator.pop(ctx);

                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('¡Contraseña actualizada exitosamente!'),
                                backgroundColor: AppTheme.success,
                              ),
                            );
                          }
                        } catch (e) {
                          setModalState(() {
                            errorModal = e.toString().replaceAll('Exception: ', '');
                            guardandoPass = false;
                          });
                        }
                      },
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  void _confirmarCerrarSesion() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Row(
          children: [
            Icon(Icons.logout_rounded, color: AppTheme.error, size: 22),
            SizedBox(width: 10),
            Text('Cerrar Sesión', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
          ],
        ),
        content: const Text(
          '¿Estás seguro de que deseas salir de la plataforma OBRATEC?',
          style: TextStyle(fontSize: 13, color: Color(0xFF64748B)),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancelar', style: TextStyle(fontWeight: FontWeight.w600)),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              Navigator.pop(context);
              Provider.of<AuthProvider>(context, listen: false).cerrarSesion();
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error),
            child: const Text('Salir'),
          ),
        ],
      ),
    );
  }

  String _texto(dynamic value) {
    if (value == null) return '';
    return value.toString().trim();
  }

  String _iniciales(String nombre) {
    final partes = nombre.trim().split(RegExp(r'\s+'));
    if (partes.isEmpty || partes.first.isEmpty) return 'U';
    if (partes.length == 1) return partes.first[0].toUpperCase();
    return '${partes[0][0]}${partes[1][0]}'.toUpperCase();
  }

  void _mostrarError(String mensaje) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(mensaje),
        backgroundColor: AppTheme.error,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final themeProv = context.watch<ThemeProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;

    final usernameVal = _perfil != null
        ? _texto(_perfil!['username'] ?? _perfil!['nombre_usuario']).toLowerCase()
        : '';

    final telefonoVal = _perfil != null ? _texto(_perfil!['telefono']) : '';
    final correoVal = _perfil != null ? _texto(_perfil!['correo']) : '';
    final direccionVal = _perfil != null ? _texto(_perfil!['direccion']) : '';

    return Scaffold(
      appBar: AppBar(
        title: Text('Ajustes y Cuenta', style: GoogleFonts.inter(fontWeight: FontWeight.w800, fontSize: 16.5)),
        actions: [
          IconButton(
            tooltip: 'Recargar perfil',
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _cargando ? null : _cargarPerfil,
          ),
        ],
      ),
      body: _cargando
          ? const Center(child: CircularProgressIndicator(color: AppTheme.primary, strokeWidth: 2.5))
          : _perfil == null
              ? _ErrorState(onRetry: _cargarPerfil)
              : SafeArea(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Header del Perfil
                        _PerfilExecutiveHeader(
                          iniciales: _iniciales(_texto(_perfil!['nombre_completo'])),
                          nombreCompleto: _texto(_perfil!['nombre_completo']),
                          username: usernameVal,
                          rol: _texto(_perfil!['nombre_rol']),
                          empresa: _texto(_perfil!['nombre_empresa']),
                        ),
                        const SizedBox(height: 16),

                        // Sección: Información de Cuenta
                        _FormalSectionGroup(
                          title: 'INFORMACIÓN DE CUENTA',
                          icon: Icons.badge_outlined,
                          children: [
                            _FormalInfoRow(
                              label: 'Carnet (CI)',
                              value: _texto(_perfil!['ci']),
                            ),
                            Divider(height: 18, color: isDark ? const Color(0xFF22304C) : const Color(0xFFF1F5F9)),
                            _FormalInfoRow(
                              label: 'Usuario',
                              value: usernameVal.isEmpty ? 'No registrado' : usernameVal,
                            ),
                            Divider(height: 18, color: isDark ? const Color(0xFF22304C) : const Color(0xFFF1F5F9)),
                            _FormalInfoRow(
                              label: 'Empresa',
                              value: _texto(_perfil!['nombre_empresa']).isEmpty
                                  ? 'Sin empresa asignada'
                                  : _texto(_perfil!['nombre_empresa']),
                            ),
                            Divider(height: 18, color: isDark ? const Color(0xFF22304C) : const Color(0xFFF1F5F9)),
                            _FormalInfoRow(
                              label: 'Rol del Sistema',
                              value: _texto(_perfil!['nombre_rol']).isEmpty
                                  ? 'Usuario'
                                  : _texto(_perfil!['nombre_rol']),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),

                        // Sección: Datos de Contacto (MODO LECTURA + BOTÓN EDITAR)
                        _FormalSectionGroup(
                          title: 'DATOS DE CONTACTO',
                          icon: Icons.contact_mail_outlined,
                          action: TextButton.icon(
                            onPressed: _abrirModalEditarContacto,
                            icon: const Icon(Icons.edit_outlined, size: 14, color: AppTheme.primary),
                            label: Text(
                              'Editar',
                              style: GoogleFonts.inter(
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                                color: AppTheme.primary,
                              ),
                            ),
                            style: TextButton.styleFrom(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              minimumSize: Size.zero,
                              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                            ),
                          ),
                          children: [
                            _FormalInfoRow(
                              label: 'Teléfono',
                              value: telefonoVal.isEmpty ? 'No registrado' : telefonoVal,
                            ),
                            Divider(height: 18, color: isDark ? const Color(0xFF22304C) : const Color(0xFFF1F5F9)),
                            _FormalInfoRow(
                              label: 'Correo',
                              value: correoVal.isEmpty ? 'No registrado' : correoVal,
                            ),
                            Divider(height: 18, color: isDark ? const Color(0xFF22304C) : const Color(0xFFF1F5F9)),
                            _FormalInfoRow(
                              label: 'Dirección',
                              value: direccionVal.isEmpty ? 'No registrada' : direccionVal,
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),

                        // Sección: Seguridad (Cambio de Contraseña)
                        _FormalSectionGroup(
                          title: 'SEGURIDAD DE LA CUENTA',
                          icon: Icons.security_rounded,
                          children: [
                            ListTile(
                              contentPadding: EdgeInsets.zero,
                              leading: Container(
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(
                                  color: isDark ? const Color(0xFF2E1C14) : const Color(0xFFFFF7ED),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: const Icon(Icons.lock_outline_rounded, color: AppTheme.primary, size: 20),
                              ),
                              title: Text('Cambiar Contraseña', style: GoogleFonts.inter(fontWeight: FontWeight.w700, fontSize: 13.5)),
                              subtitle: Text('Requiere clave actual y confirmación', style: GoogleFonts.inter(fontSize: 11.5, color: isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B))),
                              trailing: OutlinedButton(
                                onPressed: _abrirModalCambiarPassword,
                                style: OutlinedButton.styleFrom(
                                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                                  minimumSize: Size.zero,
                                ),
                                child: Text('Modificar', style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w700)),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),

                        // Preferencias de Apariencia (Modo Oscuro / Claro)
                        _FormalSectionGroup(
                          title: 'PREFERENCIAS DE LA APLICACIÓN',
                          icon: Icons.palette_outlined,
                          children: [
                            ListTile(
                              contentPadding: EdgeInsets.zero,
                              leading: Container(
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(
                                  color: isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Icon(
                                  themeProv.isDarkMode ? Icons.dark_mode_rounded : Icons.light_mode_rounded,
                                  color: isDark ? const Color(0xFF38BDF8) : const Color(0xFFF59E0B),
                                  size: 20,
                                ),
                              ),
                              title: Text(
                                'Modo Oscuro',
                                style: GoogleFonts.inter(fontWeight: FontWeight.w700, fontSize: 13.5),
                              ),
                              subtitle: Text(
                                themeProv.isDarkMode ? 'Tema oscuro activado' : 'Tema claro activado',
                                style: GoogleFonts.inter(fontSize: 11.5, color: isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B)),
                              ),
                              trailing: Switch.adaptive(
                                value: themeProv.isDarkMode,
                                activeTrackColor: AppTheme.primary,
                                onChanged: (_) => themeProv.toggleTheme(),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 24),

                        // Botón Cerrar Sesión
                        Container(
                          width: double.infinity,
                          decoration: BoxDecoration(
                            color: isDark ? const Color(0xFF131D31) : Colors.white,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: AppTheme.error.withValues(alpha: 0.35)),
                          ),
                          child: Material(
                            color: Colors.transparent,
                            child: InkWell(
                              onTap: _confirmarCerrarSesion,
                              borderRadius: BorderRadius.circular(12),
                              child: Padding(
                                padding: const EdgeInsets.symmetric(vertical: 14),
                                child: Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    const Icon(Icons.logout_rounded, color: AppTheme.error, size: 18),
                                    const SizedBox(width: 8),
                                    Text(
                                      'Cerrar Sesión',
                                      style: GoogleFonts.inter(
                                        fontSize: 14,
                                        fontWeight: FontWeight.w800,
                                        color: AppTheme.error,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 32),
                      ],
                    ),
                  ),
                ),
    );
  }
}

class _PerfilExecutiveHeader extends StatelessWidget {
  final String iniciales;
  final String nombreCompleto;
  final String username;
  final String rol;
  final String empresa;

  const _PerfilExecutiveHeader({
    required this.iniciales,
    required this.nombreCompleto,
    required this.username,
    required this.rol,
    required this.empresa,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(14),
        boxShadow: const [
          BoxShadow(
            color: Color(0x14000000),
            blurRadius: 12,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              color: AppTheme.primary,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Center(
              child: Text(
                iniciales,
                style: GoogleFonts.inter(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  nombreCompleto,
                  style: GoogleFonts.inter(
                    color: Colors.white,
                    fontSize: 16.5,
                    fontWeight: FontWeight.w900,
                    letterSpacing: -0.3,
                    height: 1.25,
                  ),
                ),
                if (username.isNotEmpty) ...[
                  const SizedBox(height: 2),
                  Text(
                    '@$username',
                    style: GoogleFonts.inter(
                      fontSize: 12.5,
                      color: const Color(0xFF94A3B8),
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
                const SizedBox(height: 6),
                Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        rol.toUpperCase(),
                        style: GoogleFonts.inter(
                          color: Colors.white,
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.5,
                        ),
                      ),
                    ),
                    if (empresa.isNotEmpty)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: AppTheme.primary.withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          empresa.toUpperCase(),
                          style: GoogleFonts.inter(
                            color: AppTheme.primaryLight,
                            fontSize: 10,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 0.5,
                          ),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _FormalSectionGroup extends StatelessWidget {
  final String title;
  final IconData icon;
  final Widget? action;
  final List<Widget> children;

  const _FormalSectionGroup({
    required this.title,
    required this.icon,
    this.action,
    required this.children,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);

    return Container(
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderColor),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(icon, size: 16, color: AppTheme.primary),
                  const SizedBox(width: 8),
                  Text(
                    title,
                    style: GoogleFonts.inter(
                      fontSize: 11,
                      fontWeight: FontWeight.w900,
                      color: AppTheme.primary,
                      letterSpacing: 0.6,
                    ),
                  ),
                ],
              ),
              if (action != null) action!,
            ],
          ),
          const SizedBox(height: 14),
          ...children,
        ],
      ),
    );
  }
}

class _FormalInfoRow extends StatelessWidget {
  final String label;
  final String value;

  const _FormalInfoRow({
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final labelColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);
    final valueColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        SizedBox(
          width: 110,
          child: Text(
            label,
            style: GoogleFonts.inter(fontSize: 12, color: labelColor, fontWeight: FontWeight.w600),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            value,
            textAlign: TextAlign.end,
            style: GoogleFonts.inter(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: valueColor,
              height: 1.3,
            ),
          ),
        ),
      ],
    );
  }
}

class _ErrorState extends StatelessWidget {
  final VoidCallback onRetry;
  const _ErrorState({required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline_rounded, size: 48, color: AppTheme.error),
            const SizedBox(height: 12),
            Text('No se pudo cargar el perfil', style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
            ),
          ],
        ),
      ),
    );
  }
}