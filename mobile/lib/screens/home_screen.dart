import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../services/auth_provider.dart';
import '../services/obra_service.dart';
import '../theme/app_theme.dart';
import '../widgets/construction_widgets.dart';
import '../widgets/ev_widgets.dart';
import 'perfil_screen.dart';
import 'proyectos_screen.dart';
import 'proyecto_detalle_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String _nombreUsuario = '';
  String _rolUsuario = '';

  final ObraService _obraService = ObraService();

  List<Map<String, dynamic>> _proyectos = [];
  bool _cargando = true;
  int _conteoActivos = 0;
  int _conteoPlanificacion = 0;

  @override
  void initState() {
    super.initState();
    _cargarDatosUsuario();
    _cargarObras();
  }

  void _cargarDatosUsuario() {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    setState(() {
      _nombreUsuario = auth.usuarioCompleto ?? 'Usuario';
      _rolUsuario = (auth.rol ?? 'CLIENTE').toUpperCase().trim();
    });
  }

  bool get _esAdmin =>
      _rolUsuario.contains('ADMIN') || _rolUsuario == 'ADMINISTRADOR' || _rolUsuario == 'ADMINISTRADOR_EMPRESA';
  bool get _esCliente => _rolUsuario == 'CLIENTE' || _rolUsuario.contains('CLIENTE');

  Future<void> _cargarObras() async {
    setState(() => _cargando = true);
    try {
      final lista = await _obraService.listarProyectos();
      int activos = 0;
      int planif = 0;

      for (var p in lista) {
        final estado = (p['estado_obra'] ?? '').toString().toUpperCase();
        if (estado == 'ACTIVO') activos++;
        if (estado == 'PLANIFICACION') planif++;
      }

      if (!mounted) return;
      setState(() {
        _proyectos = lista;
        _conteoActivos = activos;
        _conteoPlanificacion = planif;
        _cargando = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _cargando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final primerNombre = _nombreUsuario.split(' ').first;

    return Scaffold(
      appBar: AppBar(
        titleSpacing: 16,
        title: ObratecLogo(fontSize: 18, darkBackground: isDark),
        actions: [
          IconButton(
            tooltip: 'Recargar datos',
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _cargando ? null : _cargarObras,
          ),
          IconButton(
            tooltip: 'Ajustes y Perfil',
            icon: const Icon(Icons.settings_outlined),
            onPressed: () {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const PerfilScreen()));
            },
          ),
          const SizedBox(width: 6),
        ],
      ),
      body: SafeArea(
        child: RefreshIndicator(
          color: AppTheme.primary,
          onRefresh: _cargarObras,
          child: _esCliente
              ? _buildClientPortalView(primerNombre)
              : _buildAdminJefeView(primerNombre),
        ),
      ),
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // 1. PORTAL DE CLIENTE / PROPIETARIO
  // ──────────────────────────────────────────────────────────────────────────
  Widget _buildClientPortalView(String primerNombre) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        // Hero Card Limpia de Propietario
        Container(
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
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'PORTAL DE PROPIETARIO',
                    style: GoogleFonts.inter(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 1.0,
                      color: AppTheme.primary,
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      'CLIENTE',
                      style: GoogleFonts.inter(
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        color: Colors.white,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                'Hola, $primerNombre',
                style: GoogleFonts.inter(
                  fontSize: 21,
                  fontWeight: FontWeight.w900,
                  color: Colors.white,
                  letterSpacing: -0.4,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                _nombreUsuario,
                style: GoogleFonts.inter(
                  fontSize: 13,
                  color: const Color(0xFF94A3B8),
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: 14),
              const Divider(color: Colors.white12),
              const SizedBox(height: 10),
              Row(
                children: [
                  const Icon(Icons.check_circle_outline_rounded, size: 15, color: AppTheme.primaryLight),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Seguimiento en tiempo real de tu proyecto e inmueble.',
                      style: GoogleFonts.inter(fontSize: 11.5, color: Colors.white70),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),

        // Acceso directo a Ajustes y Perfil
        Container(
          decoration: BoxDecoration(
            color: cardBg,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: borderColor),
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            leading: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: isDark ? const Color(0xFF2E1C14) : const Color(0xFFFFF7ED),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.settings_outlined, color: AppTheme.primary, size: 20),
            ),
            title: Text('Ajustes y Seguridad', style: GoogleFonts.inter(fontWeight: FontWeight.w700, fontSize: 13.5, color: titleColor)),
            subtitle: Text('Gestionar datos de contacto, contraseña y tema', style: GoogleFonts.inter(fontSize: 11.5, color: isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B))),
            trailing: const Icon(Icons.chevron_right_rounded, color: Color(0xFF94A3B8)),
            onTap: () {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const PerfilScreen()));
            },
          ),
        ),
        const SizedBox(height: 20),

        // Mis Obras
        Text(
          'Mis Inmuebles y Proyectos',
          style: GoogleFonts.inter(
            fontSize: 15.5,
            fontWeight: FontWeight.w800,
            color: titleColor,
            letterSpacing: -0.2,
          ),
        ),
        const SizedBox(height: 10),

        if (_cargando) ...[
          const Center(
            child: Padding(
              padding: EdgeInsets.all(28.0),
              child: CircularProgressIndicator(color: AppTheme.primary, strokeWidth: 2.5),
            ),
          ),
        ] else if (_proyectos.isEmpty) ...[
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 36),
            decoration: BoxDecoration(
              color: cardBg,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: borderColor),
            ),
            child: Center(
              child: Column(
                children: [
                  const Icon(Icons.apartment_rounded, size: 36, color: Color(0xFF94A3B8)),
                  const SizedBox(height: 12),
                  Text(
                    'Sin obras vinculadas',
                    style: GoogleFonts.inter(fontSize: 14.5, fontWeight: FontWeight.w700, color: titleColor),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Cuando la constructora asigne tu inmueble o proyecto, podrás revisarlo aquí.',
                    textAlign: TextAlign.center,
                    style: GoogleFonts.inter(fontSize: 12, color: const Color(0xFF64748B), height: 1.4),
                  ),
                ],
              ),
            ),
          ),
        ] else ...[
          ..._proyectos.map((p) => CleanProjectCard(
                idObra: int.tryParse(p['id_obra']?.toString() ?? '0') ?? 0,
                codigo: p['codigo']?.toString() ?? 'P-0000',
                nombre: p['nombre']?.toString() ?? 'Proyecto',
                tipoNombre: p['tipo_obra_nombre']?.toString() ?? 'Edificación',
                estado: (p['estado_obra']?.toString() ?? 'PLANIFICACION').toUpperCase(),
                ubicacion: p['ubicacion']?.toString() ?? '',
                fechaInicio: p['fecha_inicio']?.toString() ?? '',
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ProyectoDetalleScreen(
                        idObra: int.tryParse(p['id_obra']?.toString() ?? '0') ?? 0,
                        codigo: p['codigo']?.toString() ?? 'P-0000',
                        nombre: p['nombre']?.toString() ?? 'Proyecto',
                        tipoNombre: p['tipo_obra_nombre']?.toString() ?? 'Edificación',
                        estado: (p['estado_obra']?.toString() ?? 'PLANIFICACION').toUpperCase(),
                        ubicacion: p['ubicacion']?.toString() ?? '',
                        fechaInicio: p['fecha_inicio']?.toString() ?? '',
                      ),
                    ),
                  );
                },
              )),
        ],
      ],
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // 2. DASHBOARD DE ADMINISTRACIÓN Y SUPERVISIÓN
  // ──────────────────────────────────────────────────────────────────────────
  Widget _buildAdminJefeView(String primerNombre) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final dividerColor = isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        // Hero Panel Ejecutivo Sólido
        Container(
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
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    _esAdmin ? 'PANEL DE CONTROL' : 'SUPERVISIÓN DE CAMPO',
                    style: GoogleFonts.inter(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 1.0,
                      color: AppTheme.primary,
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppTheme.primary.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: AppTheme.primary.withValues(alpha: 0.4)),
                    ),
                    child: Text(
                      _rolUsuario,
                      style: GoogleFonts.inter(
                        fontSize: 9.5,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.primaryLight,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                'Hola, $primerNombre',
                style: GoogleFonts.inter(
                  fontSize: 21,
                  fontWeight: FontWeight.w900,
                  color: Colors.white,
                  letterSpacing: -0.4,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                _nombreUsuario,
                style: GoogleFonts.inter(
                  fontSize: 13,
                  color: const Color(0xFF94A3B8),
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: 16),
              const Divider(color: Colors.white12),
              const SizedBox(height: 12),

              // Métricas
              Row(
                children: [
                  _buildMetricPill(
                    label: 'Obras Activas',
                    value: _conteoActivos.toString(),
                    color: AppTheme.success,
                  ),
                  const SizedBox(width: 10),
                  _buildMetricPill(
                    label: 'Planificación',
                    value: _conteoPlanificacion.toString(),
                    color: AppTheme.info,
                  ),
                  if (_esAdmin) ...[
                    const SizedBox(width: 10),
                    _buildMetricPill(
                      label: 'Total Obras',
                      value: _proyectos.length.toString(),
                      color: const Color(0xFFF59E0B),
                    ),
                  ],
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),

        // Directorio de Herramientas (Estilo Procore Tools List)
        Text(
          'Herramientas de Gestión',
          style: GoogleFonts.inter(
            fontSize: 15.5,
            fontWeight: FontWeight.w800,
            color: titleColor,
            letterSpacing: -0.2,
          ),
        ),
        const SizedBox(height: 10),

        Container(
          decoration: BoxDecoration(
            color: cardBg,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: borderColor),
          ),
          child: Column(
            children: [
              _buildToolRow(
                icon: Icons.apartment_rounded,
                title: 'Catálogo de Proyectos',
                subtitle: 'Fichas técnicas y estado de obras',
                iconColor: AppTheme.primary,
                iconBg: isDark ? const Color(0xFF2E1C14) : const Color(0xFFFFF7ED),
                onTap: () {
                  Navigator.push(context, MaterialPageRoute(builder: (_) => const ProyectosScreen()));
                },
              ),
              Divider(height: 1, color: dividerColor),
              _buildToolRow(
                icon: Icons.account_tree_outlined,
                title: 'Estructuras WBS',
                subtitle: 'Árbol jerárquico y sectores por nivel',
                iconColor: isDark ? const Color(0xFF38BDF8) : AppTheme.info,
                iconBg: isDark ? const Color(0xFF13283E) : const Color(0xFFF0F9FF),
                onTap: () {
                  Navigator.push(context, MaterialPageRoute(builder: (_) => const ProyectosScreen()));
                },
              ),
              Divider(height: 1, color: dividerColor),
              _buildToolRow(
                icon: Icons.settings_outlined,
                title: 'Ajustes y Seguridad',
                subtitle: 'Datos de perfil, contraseña y tema',
                iconColor: const Color(0xFF818CF8),
                iconBg: isDark ? const Color(0xFF1E1F3D) : const Color(0xFFEEF2FF),
                onTap: () {
                  Navigator.push(context, MaterialPageRoute(builder: (_) => const PerfilScreen()));
                },
              ),
            ],
          ),
        ),
        const SizedBox(height: 22),

        // Proyectos en Curso
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Proyectos en Curso',
              style: GoogleFonts.inter(
                fontSize: 15.5,
                fontWeight: FontWeight.w800,
                color: titleColor,
                letterSpacing: -0.2,
              ),
            ),
            if (_proyectos.isNotEmpty)
              Text(
                '${_proyectos.length} registradas',
                style: GoogleFonts.inter(fontSize: 12, color: const Color(0xFF94A3B8), fontWeight: FontWeight.w600),
              ),
          ],
        ),
        const SizedBox(height: 10),

        if (_cargando) ...[
          const Center(
            child: Padding(
              padding: EdgeInsets.all(28.0),
              child: CircularProgressIndicator(color: AppTheme.primary, strokeWidth: 2.5),
            ),
          ),
        ] else if (_proyectos.isEmpty) ...[
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 32),
            decoration: BoxDecoration(
              color: cardBg,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: borderColor),
            ),
            child: Center(
              child: Column(
                children: [
                  const Icon(Icons.folder_open_rounded, size: 36, color: Color(0xFF94A3B8)),
                  const SizedBox(height: 10),
                  Text(
                    'No hay proyectos registrados',
                    style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w700, color: titleColor),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Crea obras desde la web o recarga la conexión.',
                    textAlign: TextAlign.center,
                    style: GoogleFonts.inter(fontSize: 12, color: const Color(0xFF94A3B8)),
                  ),
                ],
              ),
            ),
          ),
        ] else ...[
          ..._proyectos.map((p) => CleanProjectCard(
                idObra: int.tryParse(p['id_obra']?.toString() ?? '0') ?? 0,
                codigo: p['codigo']?.toString() ?? 'P-0000',
                nombre: p['nombre']?.toString() ?? 'Proyecto',
                tipoNombre: p['tipo_obra_nombre']?.toString() ?? 'Edificación',
                estado: (p['estado_obra']?.toString() ?? 'PLANIFICACION').toUpperCase(),
                ubicacion: p['ubicacion']?.toString() ?? '',
                fechaInicio: p['fecha_inicio']?.toString() ?? '',
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ProyectoDetalleScreen(
                        idObra: int.tryParse(p['id_obra']?.toString() ?? '0') ?? 0,
                        codigo: p['codigo']?.toString() ?? 'P-0000',
                        nombre: p['nombre']?.toString() ?? 'Proyecto',
                        tipoNombre: p['tipo_obra_nombre']?.toString() ?? 'Edificación',
                        estado: (p['estado_obra']?.toString() ?? 'PLANIFICACION').toUpperCase(),
                        ubicacion: p['ubicacion']?.toString() ?? '',
                        fechaInicio: p['fecha_inicio']?.toString() ?? '',
                      ),
                    ),
                  );
                },
              )),
        ],
      ],
    );
  }

  Widget _buildMetricPill({
    required String label,
    required String value,
    required Color color,
  }) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              value,
              style: GoogleFonts.inter(fontSize: 17, fontWeight: FontWeight.w900, color: Colors.white),
            ),
            const SizedBox(height: 1),
            Text(
              label,
              style: GoogleFonts.inter(fontSize: 10, color: const Color(0xFF94A3B8), fontWeight: FontWeight.w600),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildToolRow({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color iconColor,
    required Color iconBg,
    required VoidCallback onTap,
  }) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: iconBg,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Icon(icon, color: iconColor, size: 20),
      ),
      title: Text(
        title,
        style: GoogleFonts.inter(fontSize: 13.5, fontWeight: FontWeight.w700, color: isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A)),
      ),
      subtitle: Text(
        subtitle,
        style: GoogleFonts.inter(fontSize: 11.5, color: isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B)),
      ),
      trailing: const Icon(Icons.chevron_right_rounded, color: Color(0xFF94A3B8), size: 20),
      onTap: onTap,
    );
  }
}