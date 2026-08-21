import 'package:flutter/material.dart';

import '../config/app_config.dart';
import '../services/auth_service.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  bool isLogin = true;
  bool loading = false;

  String message = '';
  bool messageSuccess = false;

  final userController = TextEditingController();
  final passwordController = TextEditingController();

  final docController = TextEditingController();
  final nameController = TextEditingController();
  final mailController = TextEditingController();
  final numberController = TextEditingController();
  final dirController = TextEditingController();

  @override
  void dispose() {
    userController.dispose();
    passwordController.dispose();
    docController.dispose();
    nameController.dispose();
    mailController.dispose();
    numberController.dispose();
    dirController.dispose();
    super.dispose();
  }

  void showMessage(String text, {bool success = false}) {
    setState(() {
      message = text;
      messageSuccess = success;
    });
  }

  Future<void> handleLogin() async {
    setState(() {
      loading = true;
      message = '';
    });

    final result = await AuthService.login(
      userInput: userController.text.trim(),
      password: passwordController.text.trim(),
    );

    setState(() {
      loading = false;
    });

    if (!mounted) return;

    if (!result.success) {
      showMessage(result.message);
      return;
    }

    Navigator.pushReplacementNamed(context, '/home');
  }

  Future<void> handleRegister() async {
    setState(() {
      loading = true;
      message = '';
    });

    final result = await AuthService.register(
      user: userController.text.trim(),
      doc: docController.text.trim(),
      name: nameController.text.trim(),
      mail: mailController.text.trim(),
      number: numberController.text.trim(),
      password: passwordController.text.trim(),
      dir: dirController.text.trim(),
    );

    setState(() {
      loading = false;
    });

    if (!result.success) {
      showMessage(result.message);
      return;
    }

    showMessage(result.message, success: true);

    // Después de registrar, dejamos activo el modo login.
    setState(() {
      isLogin = true;
      passwordController.clear();
    });
  }

  void loadDemoUser() {
    setState(() {
      userController.text = AppConfig.demoUser;
      passwordController.text = AppConfig.demoPassword;
      message = '';
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Línea decorativa superior como en React.
            Container(
              height: 4,
              width: double.infinity,
              color: AppTheme.primaryGreen,
            ),

            Expanded(
              child: Center(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(18),
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 420),
                    child: Column(
                      children: [
                        _buildAuthCard(),
                        const SizedBox(height: 14),
                        if (isLogin) _buildDemoBanner(),
                        const SizedBox(height: 18),
                        const Text(
                          'UAGRM • 2026',
                          style: TextStyle(
                            fontSize: 9,
                            fontWeight: FontWeight.w900,
                            color: Colors.grey,
                            letterSpacing: 2,
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
      ),
    );
  }

  Widget _buildAuthCard() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(10),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        children: [
          _buildHeader(),
          Padding(
            padding: const EdgeInsets.all(22),
            child: Column(
              children: [
                if (message.isNotEmpty) ...[
                  AgroErrorBox(
                    message: message,
                    success: messageSuccess,
                  ),
                  const SizedBox(height: 16),
                ],

                // Selector Login o Registro.
                Row(
                  children: [
                    Expanded(
                      child: _buildModeButton(
                        text: 'Login',
                        selected: isLogin,
                        onTap: () {
                          setState(() {
                            isLogin = true;
                            message = '';
                          });
                        },
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _buildModeButton(
                        text: 'Registro',
                        selected: !isLogin,
                        onTap: () {
                          setState(() {
                            isLogin = false;
                            message = '';
                          });
                        },
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 20),

                if (isLogin) _buildLoginForm() else _buildRegisterForm(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(
        horizontal: 24,
        vertical: 24,
      ),
      decoration: const BoxDecoration(
        color: Color(0xFFF8FAFC),
        border: Border(
          bottom: BorderSide(color: Color(0xFFF1F5F9)),
        ),
      ),
      child: Column(
        children: [
          // Por ahora usamos un ícono. Luego lo cambiamos por el logo real.
          Container(
            width: 74,
            height: 74,
            decoration: BoxDecoration(
              color: AppTheme.primaryGreen.withOpacity(0.10),
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Icon(
              Icons.eco,
              color: AppTheme.primaryGreen,
              size: 42,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            isLogin ? 'ACCESO AL SISTEMA' : 'CREAR CUENTA',
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w900,
              color: AppTheme.slateText,
              letterSpacing: 2,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLoginForm() {
    return Column(
      children: [
        AgroTextField(
          label: 'Usuario',
          hint: 'emple@agroenlace.com',
          controller: userController,
          keyboardType: TextInputType.emailAddress,
        ),
        const SizedBox(height: 14),
        AgroTextField(
          label: 'Contraseña',
          hint: '••••••••',
          controller: passwordController,
          obscureText: true,
        ),
        const SizedBox(height: 20),
        AgroButton(
          text: 'Ingresar',
          loading: loading,
          onPressed: handleLogin,
        ),
      ],
    );
  }

  Widget _buildRegisterForm() {
    return Column(
      children: [
        AgroTextField(
          label: 'Usuario',
          hint: 'nombre_usuario',
          controller: userController,
        ),
        const SizedBox(height: 12),
        AgroTextField(
          label: 'Documento',
          hint: '12345678',
          controller: docController,
          keyboardType: TextInputType.number,
        ),
        const SizedBox(height: 12),
        AgroTextField(
          label: 'Nombre o razón social',
          hint: 'Agro Productor SRL',
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
          controller: numberController,
          keyboardType: TextInputType.phone,
        ),
        const SizedBox(height: 12),
        AgroTextField(
          label: 'Dirección',
          hint: 'Opcional',
          controller: dirController,
        ),
        const SizedBox(height: 12),
        AgroTextField(
          label: 'Contraseña',
          hint: '••••••••',
          controller: passwordController,
          obscureText: true,
        ),
        const SizedBox(height: 20),
        AgroButton(
          text: 'Registrarme',
          loading: loading,
          onPressed: handleRegister,
        ),
      ],
    );
  }

  Widget _buildModeButton({
    required String text,
    required bool selected,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: loading ? null : onTap,
      borderRadius: BorderRadius.circular(6),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: selected ? AppTheme.primaryGreen : const Color(0xFFF8FAFC),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(
            color: selected ? AppTheme.primaryGreen : AppTheme.borderColor,
          ),
        ),
        child: Text(
          text.toUpperCase(),
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w900,
            letterSpacing: 1.4,
            color: selected ? Colors.white : AppTheme.mutedText,
          ),
        ),
      ),
    );
  }

  Widget _buildDemoBanner() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.blue.withOpacity(0.08),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.blue.shade100),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.blue.shade600,
              borderRadius: BorderRadius.circular(6),
            ),
            child: const Icon(
              Icons.notifications,
              color: Colors.white,
              size: 16,
            ),
          ),
          const SizedBox(width: 12),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'USUARIO DEMO',
                  style: TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.w900,
                    color: Colors.blue,
                    letterSpacing: 0.5,
                  ),
                ),
                SizedBox(height: 2),
                Text(
                  'emple@agroenlace.com / 12345678',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.slateText,
                  ),
                ),
              ],
            ),
          ),
          TextButton(
            onPressed: loadDemoUser,
            style: TextButton.styleFrom(
              backgroundColor: Colors.blue.shade600,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(
                horizontal: 14,
                vertical: 8,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(6),
              ),
            ),
            child: const Text(
              'CARGAR',
              style: TextStyle(
                fontSize: 9,
                fontWeight: FontWeight.w900,
              ),
            ),
          ),
        ],
      ),
    );
  }
}