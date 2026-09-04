import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // ── Paleta principal OBRATEC (Construcción & Obras) ──────────────────────
  static const Color primary = Color(0xFFEA580C);       // Orange-600
  static const Color primaryDark = Color(0xFFC2410C);   // Orange-700
  static const Color primaryLight = Color(0xFFFFF7ED);  // Orange-50
  static const Color primaryBorder = Color(0xFFFFEDD5); // Orange-100

  static const Color secondary = Color(0xFF0F172A);     // Slate-900
  static const Color secondaryLight = Color(0xFF1E293B);// Slate-800
  static const Color surface = Color(0xFFFFFFFF);
  static const Color surfaceElevated = Color(0xFFFFFFFF);
  static const Color background = Color(0xFFF8FAFC);    // Slate-50

  // ── Dark Mode Colors ──────────────────────────────────────────────────────
  static const Color darkBackground = Color(0xFF0B0F19); // Obsidian / Deep Slate
  static const Color darkSurface = Color(0xFF131D31);    // Elevated Slate Card
  static const Color darkSurfaceCard = Color(0xFF18233C);// Highlight Card
  static const Color darkBorder = Color(0xFF22304C);     // Hairline Border Dark
  static const Color darkTextPrimary = Color(0xFFF8FAFC);
  static const Color darkTextSecondary = Color(0xFF94A3B8);
  static const Color darkTextMuted = Color(0xFF64748B);

  // ── Neutros y textos (Light) ──────────────────────────────────────────────
  static const Color textPrimary = Color(0xFF0F172A);   // Slate-900
  static const Color textSecondary = Color(0xFF64748B); // Slate-500
  static const Color textMuted = Color(0xFF94A3B8);     // Slate-400
  static const Color border = Color(0xFFE2E8F0);        // Slate-200
  static const Color borderLight = Color(0xFFF1F5F9);   // Slate-100
  static const Color surfaceSubtle = Color(0xFFF1F5F9); // Slate-100 subtle surface

  // ── Estados semánticos de obra ────────────────────────────────────────────
  static const Color success = Color(0xFF10B981);       // Emerald-500
  static const Color successBg = Color(0xFFECFDF5);     // Emerald-50
  static const Color info = Color(0xFF0284C7);          // Sky-600
  static const Color infoBg = Color(0xFFF0F9FF);        // Sky-50
  static const Color warning = Color(0xFFF59E0B);       // Amber-500
  static const Color warningBg = Color(0xFFFFFBEB);     // Amber-50
  static const Color error = Color(0xFFEF4444);         // Red-500
  static const Color errorBg = Color(0xFFFEF2F2);       // Red-50

  static const double radiusSmall = 8.0;
  static const double radiusMedium = 12.0;
  static const double radiusLarge = 16.0;
  static const double radiusXLarge = 24.0;

  // ── TEMA CLARO (LIGHT THEME) ──────────────────────────────────────────────
  static ThemeData get lightTheme {
    final baseTextTheme = GoogleFonts.interTextTheme();

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: background,
      colorScheme: const ColorScheme.light(
        primary: primary,
        onPrimary: Colors.white,
        primaryContainer: primaryLight,
        onPrimaryContainer: primaryDark,
        secondary: secondary,
        onSecondary: Colors.white,
        surface: surface,
        onSurface: textPrimary,
        error: error,
        onError: Colors.white,
        outline: border,
        outlineVariant: borderLight,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.white,
        foregroundColor: textPrimary,
        elevation: 0,
        scrolledUnderElevation: 0.5,
        surfaceTintColor: Colors.transparent,
        systemOverlayStyle: const SystemUiOverlayStyle(
          statusBarColor: Colors.transparent,
          statusBarIconBrightness: Brightness.dark,
        ),
        titleTextStyle: GoogleFonts.inter(
          fontSize: 16.5,
          fontWeight: FontWeight.w800,
          color: textPrimary,
          letterSpacing: -0.3,
        ),
        iconTheme: const IconThemeData(color: textPrimary, size: 22),
      ),
      cardTheme: CardThemeData(
        color: surface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radiusMedium),
          side: const BorderSide(color: border, width: 1.1),
        ),
        margin: EdgeInsets.zero,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          minimumSize: const Size(double.infinity, 48),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radiusMedium),
          ),
          elevation: 0,
          textStyle: GoogleFonts.inter(
            fontSize: 14,
            fontWeight: FontWeight.w800,
            letterSpacing: 0.2,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surface,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        hintStyle: GoogleFonts.inter(
          fontSize: 13.5,
          color: textMuted,
          fontWeight: FontWeight.w400,
        ),
        labelStyle: GoogleFonts.inter(
          fontSize: 12.5,
          fontWeight: FontWeight.w700,
          color: textSecondary,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusMedium),
          borderSide: const BorderSide(color: border, width: 1),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusMedium),
          borderSide: const BorderSide(color: border, width: 1),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusMedium),
          borderSide: const BorderSide(color: primary, width: 1.8),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusMedium),
          borderSide: const BorderSide(color: error, width: 1),
        ),
      ),
      dividerTheme: const DividerThemeData(color: border, thickness: 1, space: 1),
      textTheme: baseTextTheme.copyWith(
        displayLarge: GoogleFonts.inter(fontSize: 28, fontWeight: FontWeight.w900, color: textPrimary),
        displayMedium: GoogleFonts.inter(fontSize: 22, fontWeight: FontWeight.w900, color: textPrimary),
        titleLarge: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w800, color: textPrimary),
        titleMedium: GoogleFonts.inter(fontSize: 15, fontWeight: FontWeight.w800, color: textPrimary),
        titleSmall: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w700, color: textPrimary),
        bodyLarge: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w400, color: textPrimary),
        bodyMedium: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w400, color: textSecondary),
        bodySmall: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w400, color: textMuted),
      ),
    );
  }

  // ── TEMA OSCURO (DARK THEME) ──────────────────────────────────────────────
  static ThemeData get darkTheme {
    final baseTextTheme = GoogleFonts.interTextTheme();

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: darkBackground,
      colorScheme: const ColorScheme.dark(
        primary: Color(0xFFF97316), // Vivid Orange
        onPrimary: Colors.white,
        primaryContainer: Color(0xFF431407),
        onPrimaryContainer: Color(0xFFFFEDD5),
        secondary: Color(0xFFE2E8F0),
        onSecondary: Color(0xFF0F172A),
        surface: darkSurface,
        onSurface: darkTextPrimary,
        error: Color(0xFFF87171),
        onError: Colors.white,
        outline: darkBorder,
        outlineVariant: Color(0xFF1E293B),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: const Color(0xFF0F172A),
        foregroundColor: darkTextPrimary,
        elevation: 0,
        scrolledUnderElevation: 0.5,
        surfaceTintColor: Colors.transparent,
        systemOverlayStyle: const SystemUiOverlayStyle(
          statusBarColor: Colors.transparent,
          statusBarIconBrightness: Brightness.light,
        ),
        titleTextStyle: GoogleFonts.inter(
          fontSize: 16.5,
          fontWeight: FontWeight.w800,
          color: darkTextPrimary,
          letterSpacing: -0.3,
        ),
        iconTheme: const IconThemeData(color: darkTextPrimary, size: 22),
      ),
      cardTheme: CardThemeData(
        color: darkSurface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radiusMedium),
          side: const BorderSide(color: darkBorder, width: 1.1),
        ),
        margin: EdgeInsets.zero,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFFEA580C),
          foregroundColor: Colors.white,
          minimumSize: const Size(double.infinity, 48),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radiusMedium),
          ),
          elevation: 0,
          textStyle: GoogleFonts.inter(
            fontSize: 14,
            fontWeight: FontWeight.w800,
            letterSpacing: 0.2,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: darkSurface,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        hintStyle: GoogleFonts.inter(
          fontSize: 13.5,
          color: darkTextMuted,
          fontWeight: FontWeight.w400,
        ),
        labelStyle: GoogleFonts.inter(
          fontSize: 12.5,
          fontWeight: FontWeight.w700,
          color: darkTextSecondary,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusMedium),
          borderSide: const BorderSide(color: darkBorder, width: 1),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusMedium),
          borderSide: const BorderSide(color: darkBorder, width: 1),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusMedium),
          borderSide: const BorderSide(color: Color(0xFFF97316), width: 1.8),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusMedium),
          borderSide: const BorderSide(color: Color(0xFFF87171), width: 1),
        ),
      ),
      dividerTheme: const DividerThemeData(color: darkBorder, thickness: 1, space: 1),
      textTheme: baseTextTheme.copyWith(
        displayLarge: GoogleFonts.inter(fontSize: 28, fontWeight: FontWeight.w900, color: darkTextPrimary),
        displayMedium: GoogleFonts.inter(fontSize: 22, fontWeight: FontWeight.w900, color: darkTextPrimary),
        titleLarge: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w800, color: darkTextPrimary),
        titleMedium: GoogleFonts.inter(fontSize: 15, fontWeight: FontWeight.w800, color: darkTextPrimary),
        titleSmall: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w700, color: darkTextPrimary),
        bodyLarge: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w400, color: darkTextPrimary),
        bodyMedium: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w400, color: darkTextSecondary),
        bodySmall: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w400, color: darkTextMuted),
      ),
    );
  }

  // Alias retrocompatible
  static ThemeData get theme => lightTheme;
}