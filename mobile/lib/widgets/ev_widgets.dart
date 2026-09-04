import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../theme/app_theme.dart';

/// Logo oficial OBRATEC para la app móvil
class ObratecLogo extends StatelessWidget {
  final double fontSize;
  final bool darkBackground;

  const ObratecLogo({
    super.key,
    this.fontSize = 22,
    this.darkBackground = false,
  });

  @override
  Widget build(BuildContext context) {
    final primaryColor = darkBackground ? Colors.white : const Color(0xFF0F172A);
    const accentColor = AppTheme.primary;

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          padding: const EdgeInsets.all(5),
          decoration: BoxDecoration(
            color: AppTheme.primary,
            borderRadius: BorderRadius.circular(6),
          ),
          child: const Icon(
            Icons.construction_rounded,
            color: Colors.white,
            size: 17,
          ),
        ),
        const SizedBox(width: 8),
        RichText(
          text: TextSpan(
            children: [
              TextSpan(
                text: 'OBRA',
                style: GoogleFonts.inter(
                  fontSize: fontSize,
                  fontWeight: FontWeight.w900,
                  color: primaryColor,
                  letterSpacing: 0.5,
                ),
              ),
              TextSpan(
                text: 'TEC',
                style: GoogleFonts.inter(
                  fontSize: fontSize,
                  fontWeight: FontWeight.w900,
                  color: accentColor,
                  letterSpacing: 0.5,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

// Alias para compatibilidad
typedef EvLogo = ObratecLogo;

/// Separador decorativo naranja para encabezados
class ObratecDivider extends StatelessWidget {
  const ObratecDivider({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 40,
      height: 3.5,
      decoration: BoxDecoration(
        color: AppTheme.primary,
        borderRadius: BorderRadius.circular(2),
      ),
    );
  }
}

typedef EvLogoDivider = ObratecDivider;

/// Campo de texto estilizado para formularios de obra
class ObratecTextField extends StatelessWidget {
  final String label;
  final String? hint;
  final bool obscure;
  final TextEditingController? controller;
  final String? Function(String?)? validator;
  final TextInputType? keyboardType;
  final Widget? suffixIcon;
  final bool autofocus;
  final TextCapitalization textCapitalization;

  const ObratecTextField({
    super.key,
    required this.label,
    this.hint,
    this.obscure = false,
    this.controller,
    this.validator,
    this.keyboardType,
    this.suffixIcon,
    this.autofocus = false,
    this.textCapitalization = TextCapitalization.none,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: GoogleFonts.inter(
            fontSize: 11.5,
            fontWeight: FontWeight.w800,
            color: const Color(0xFF64748B),
            letterSpacing: 0.3,
          ),
        ),
        const SizedBox(height: 6),
        TextFormField(
          controller: controller,
          obscureText: obscure,
          keyboardType: keyboardType,
          validator: validator,
          autofocus: autofocus,
          textCapitalization: textCapitalization,
          style: GoogleFonts.inter(
            fontSize: 13.5,
            color: const Color(0xFF0F172A),
            fontWeight: FontWeight.w600,
          ),
          decoration: InputDecoration(
            hintText: hint,
            suffixIcon: suffixIcon,
          ),
        ),
      ],
    );
  }
}

typedef EvTextField = ObratecTextField;

/// Botón primario de acción de obra con estado de carga
class ObratecPrimaryButton extends StatelessWidget {
  final String label;
  final bool loading;
  final VoidCallback? onPressed;
  final IconData? icon;

  const ObratecPrimaryButton({
    super.key,
    required this.label,
    this.loading = false,
    this.onPressed,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 48,
      child: ElevatedButton(
        onPressed: loading ? null : onPressed,
        child: loading
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: Colors.white,
                ),
              )
            : Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (icon != null) ...[
                    Icon(icon, size: 18),
                    const SizedBox(width: 8),
                  ],
                  Text(label),
                ],
              ),
      ),
    );
  }
}

typedef EvPrimaryButton = ObratecPrimaryButton;