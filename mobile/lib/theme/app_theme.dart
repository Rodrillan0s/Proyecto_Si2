import 'package:flutter/material.dart';

class AppTheme {
  // Colores principales tomados del Login.jsx.
  static const Color primaryGreen = Color(0xFF1A5729);
  static const Color darkGreen = Color(0xFF144320);
  static const Color backgroundBlue = Color(0xFFEBF5FF);
  static const Color slateText = Color(0xFF1E293B);
  static const Color mutedText = Color(0xFF64748B);
  static const Color borderColor = Color(0xFFE2E8F0);

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: backgroundBlue,
      fontFamily: 'Arial',

      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryGreen,
        primary: primaryGreen,
        secondary: darkGreen,
        surface: Colors.white,
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFFF8FAFC),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 14,
          vertical: 12,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(6),
          borderSide: const BorderSide(color: borderColor),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(6),
          borderSide: const BorderSide(color: borderColor),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(6),
          borderSide: const BorderSide(
            color: primaryGreen,
            width: 1.4,
          ),
        ),
      ),
    );
  }
}