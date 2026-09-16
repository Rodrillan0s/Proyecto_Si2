import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../services/auth_provider.dart';
import '../services/obra_service.dart';
import '../services/empresa_service.dart';
import '../theme/app_theme.dart';
import '../widgets/construction_widgets.dart';
import '../widgets/ev_widgets.dart';
import 'perfil_screen.dart';
import 'proyectos_screen.dart';
import 'proyecto_detalle_screen.dart';
import 'materiales_screen.dart';
import 'ordenes_trabajo_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ObraService _obraService = ObraService();
  final EmpresaService _empresaService = EmpresaService();

  List<Map<String, dynamic>> _proyectos = [];
  bool _cargando = true;
  int _conteoActivos = 0;
  int _conteoPlanificacion = 0;

  @override
  void initState() {
    super.initState();
    _cargarObras();
  }

  Future<void> _cargarObras() async {
    setState(() => _cargando = true);
    try {
      final lista = await _obraService.listarProyectos();
      if (!mounted) return;
      final auth = Provider.of<AuthProvider>(context, listen: false);

      // Si el Administrador Global tiene una empresa activa seleccionada, filtramos sus obras
      List<Map<String, dynamic>> listaFiltrada = lista;
      if (auth.esAdminGlobal && !auth.esVistaGlobal && auth.idEmpresaActiva != null) {
        listaFiltrada = lista.where((p) {
          final pEmpresaId = p['id_empresa'];
          return pEmpresaId == auth.idEmpresaActiva;
        }).toList();
      }

      int activos = 0;
      int planif = 0;

      for (var p in listaFiltrada) {
        final estado = (p['estado_obra'] ?? '').toString().toUpperCase();
        if (estado == 'ACTIVO' || estado == 'EN EJECUCION') activos++;
        if (estado == 'PLANIFICACION') planif++;
      }

      if (!mounted) return;
      setState(() {
        _proyectos = listaFiltrada;
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
    final auth = Provider.of<AuthProvider>(context);
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final nombreCompleto = auth.usuarioCompleto ?? 'Usuario';
    final primerNombre = nombreCompleto.split(' ').first;

    return Scaffold(
      appBar: AppBar(
        titleSpacing: 16,
        title: ObratecLogo(fontSize: 18, darkBackground: isDark),
        actions: [
          // Botón selector de empresa solo para Administrador Global
          if (auth.esAdminGlobal)
            IconButton(
              tooltip: 'Cambiar Empresa Activa',
              icon: Icon(
                auth.esVistaGlobal ? Icons.public_rounded : Icons.business_rounded,
                color: auth.esVistaGlobal ? AppTheme.primary : AppTheme.success,
              ),
              onPressed: () => _mostrarSelectorEmpresas(context),
            ),
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
          child: _seleccionarDashboardSegunRol(auth, primerNombre, nombreCompleto, isDark),
        ),
      ),
    );
  }

  Widget _seleccionarDashboardSegunRol(
    AuthProvider auth,
    String primerNombre,
    String nombreCompleto,
    bool isDark,
  ) {
    if (auth.esCliente) {
      return _buildClientPortalView(primerNombre, nombreCompleto, isDark);
    }

    if (auth.esTrabajadorCampo) {
      return _buildOperarioCampoView(auth, primerNombre, nombreCompleto, isDark);
    }

    if (auth.esSupervisor) {
      return _buildSupervisorView(auth, primerNombre, nombreCompleto, isDark);
    }

    if (auth.esJefeDeObra) {
      return _buildJefeObraView(auth, primerNombre, nombreCompleto, isDark);
    }

    if (auth.esAdminEmpresa) {
      return _buildAdminEmpresaView(auth, primerNombre, nombreCompleto, isDark);
    }

    // Por defecto o ADMINISTRADOR global
    return _buildAdminGlobalView(auth, primerNombre, nombreCompleto, isDark);
  }

  // ──────────────────────────────────────────────────────────────────────────
  // 1. DASHBOARD ADMINISTRADOR GLOBAL
  // ──────────────────────────────────────────────────────────────────────────
  Widget _buildAdminGlobalView(AuthProvider auth, String primerNombre, String nombreCompleto, bool isDark) {
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final dividerColor = isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        // Selector / Banner de Empresa Activa
        _buildBannerEmpresaActiva(auth, isDark),
        const SizedBox(height: 14),

        // Hero Panel Ejecutivo Global
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
                    'ADMINISTRACIÓN GLOBAL',
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
                      'ADMINISTRADOR',
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
                nombreCompleto,
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
                  const SizedBox(width: 10),
                  _buildMetricPill(
                    label: auth.esVistaGlobal ? 'Total Global' : 'En Empresa',
                    value: _proyectos.length.toString(),
                    color: const Color(0xFFF59E0B),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),

        // Directorio de Herramientas
        _buildSectionHeader('Herramientas de Plataforma', titleColor),
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
                icon: Icons.assignment_outlined,
                title: 'Órdenes de Trabajo',
                subtitle: 'Asignaciones de tareas y cuadrillas',
                iconColor: const Color(0xFF10B981),
                iconBg: isDark ? const Color(0xFF064E3B) : const Color(0xFFECFDF5),
                onTap: () {
                  Navigator.push(context, MaterialPageRoute(builder: (_) => const OrdenesTrabajoScreen()));
                },
              ),
              Divider(height: 1, color: dividerColor),
              _buildToolRow(
                icon: Icons.inventory_2_outlined,
                title: 'Catálogo de Materiales',
                subtitle: 'Insumos, existencias y costos',
                iconColor: const Color(0xFFF59E0B),
                iconBg: isDark ? const Color(0xFF451A03) : const Color(0xFFFFFBEB),
                onTap: () {
                  Navigator.push(context, MaterialPageRoute(builder: (_) => const MaterialesScreen()));
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

        // Listado de Proyectos
        _buildProyectosListSection(titleColor, cardBg, borderColor),
      ],
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // 2. DASHBOARD ADMINISTRADOR DE EMPRESA
  // ──────────────────────────────────────────────────────────────────────────
  Widget _buildAdminEmpresaView(AuthProvider auth, String primerNombre, String nombreCompleto, bool isDark) {
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final dividerColor = isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        // Banner de Empresa
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: isDark ? const Color(0xFF1E293B) : const Color(0xFFEFF6FF),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: AppTheme.primary.withValues(alpha: 0.3)),
          ),
          child: Row(
            children: [
              const Icon(Icons.business_rounded, color: AppTheme.primary, size: 22),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      auth.nombreEmpresa ?? 'Empresa Constructora',
                      style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13),
                    ),
                    const Text(
                      'Alcance Corporativo de Empresa',
                      style: TextStyle(fontSize: 11, color: AppTheme.textMuted),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),

        // Hero Card
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: const Color(0xFF0F172A),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'PANEL DE EMPRESA',
                style: GoogleFonts.inter(
                  fontSize: 10.5,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1.0,
                  color: AppTheme.primary,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                'Hola, $primerNombre',
                style: GoogleFonts.inter(fontSize: 21, fontWeight: FontWeight.w900, color: Colors.white),
              ),
              Text(nombreCompleto, style: GoogleFonts.inter(fontSize: 13, color: const Color(0xFF94A3B8))),
              const SizedBox(height: 16),
              const Divider(color: Colors.white12),
              const SizedBox(height: 12),
              Row(
                children: [
                  _buildMetricPill(label: 'Obras Activas', value: _conteoActivos.toString(), color: AppTheme.success),
                  const SizedBox(width: 10),
                  _buildMetricPill(label: 'Planificación', value: _conteoPlanificacion.toString(), color: AppTheme.info),
                  const SizedBox(width: 10),
                  _buildMetricPill(label: 'Total Obras', value: _proyectos.length.toString(), color: const Color(0xFFF59E0B)),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),

        // Herramientas de Empresa
        _buildSectionHeader('Módulos de Empresa', titleColor),
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
                title: 'Obras de la Empresa',
                subtitle: 'Supervisión y avance de obras',
                iconColor: AppTheme.primary,
                iconBg: isDark ? const Color(0xFF2E1C14) : const Color(0xFFFFF7ED),
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProyectosScreen())),
              ),
              Divider(height: 1, color: dividerColor),
              _buildToolRow(
                icon: Icons.assignment_outlined,
                title: 'Órdenes de Trabajo',
                subtitle: 'Órdenes operativas de la constructora',
                iconColor: const Color(0xFF10B981),
                iconBg: isDark ? const Color(0xFF064E3B) : const Color(0xFFECFDF5),
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const OrdenesTrabajoScreen())),
              ),
              Divider(height: 1, color: dividerColor),
              _buildToolRow(
                icon: Icons.inventory_2_outlined,
                title: 'Inventario de Materiales',
                subtitle: 'Existencias y pedidos en curso',
                iconColor: const Color(0xFFF59E0B),
                iconBg: isDark ? const Color(0xFF451A03) : const Color(0xFFFFFBEB),
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MaterialesScreen())),
              ),
            ],
          ),
        ),
        const SizedBox(height: 22),
        _buildProyectosListSection(titleColor, cardBg, borderColor),
      ],
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // 3. DASHBOARD JEFE DE OBRA
  // ──────────────────────────────────────────────────────────────────────────
  Widget _buildJefeObraView(AuthProvider auth, String primerNombre, String nombreCompleto, bool isDark) {
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final dividerColor = isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: const Color(0xFF0F172A),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'JEFATURA DE OBRA',
                    style: GoogleFonts.inter(fontSize: 10.5, fontWeight: FontWeight.w800, color: AppTheme.primary),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: const Color(0xFF10B981).withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: const Text('EJECUCIÓN', style: TextStyle(fontSize: 9.5, fontWeight: FontWeight.w800, color: Color(0xFF34D399))),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text('Hola, $primerNombre', style: GoogleFonts.inter(fontSize: 21, fontWeight: FontWeight.w900, color: Colors.white)),
              Text(nombreCompleto, style: GoogleFonts.inter(fontSize: 13, color: const Color(0xFF94A3B8))),
              const SizedBox(height: 16),
              const Divider(color: Colors.white12),
              const SizedBox(height: 12),
              Row(
                children: [
                  _buildMetricPill(label: 'En Ejecución', value: _conteoActivos.toString(), color: AppTheme.success),
                  const SizedBox(width: 10),
                  _buildMetricPill(label: 'Planificadas', value: _conteoPlanificacion.toString(), color: AppTheme.info),
                  const SizedBox(width: 10),
                  _buildMetricPill(label: 'Total Frentes', value: _proyectos.length.toString(), color: const Color(0xFFF59E0B)),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),

        _buildSectionHeader('Gestión Técnica y Operativa', titleColor),
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
                icon: Icons.assignment_outlined,
                title: 'Órdenes de Trabajo de Campo',
                subtitle: 'Emitir y coordinar labores de cuadrillas',
                iconColor: const Color(0xFF10B981),
                iconBg: isDark ? const Color(0xFF064E3B) : const Color(0xFFECFDF5),
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const OrdenesTrabajoScreen())),
              ),
              Divider(height: 1, color: dividerColor),
              _buildToolRow(
                icon: Icons.account_tree_outlined,
                title: 'Estructuras WBS y Unidades',
                subtitle: 'Sectores, niveles y ambientes de obra',
                iconColor: isDark ? const Color(0xFF38BDF8) : AppTheme.info,
                iconBg: isDark ? const Color(0xFF13283E) : const Color(0xFFF0F9FF),
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProyectosScreen())),
              ),
              Divider(height: 1, color: dividerColor),
              _buildToolRow(
                icon: Icons.inventory_2_outlined,
                title: 'Requerimientos de Materiales',
                subtitle: 'Consultar existencias para el frente de obra',
                iconColor: const Color(0xFFF59E0B),
                iconBg: isDark ? const Color(0xFF451A03) : const Color(0xFFFFFBEB),
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MaterialesScreen())),
              ),
            ],
          ),
        ),
        const SizedBox(height: 22),
        _buildProyectosListSection(titleColor, cardBg, borderColor),
      ],
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // 4. DASHBOARD SUPERVISOR DE OBRA
  // ──────────────────────────────────────────────────────────────────────────
  Widget _buildSupervisorView(AuthProvider auth, String primerNombre, String nombreCompleto, bool isDark) {
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final dividerColor = isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: const Color(0xFF0F172A),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'SUPERVISIÓN Y CONTROL',
                    style: GoogleFonts.inter(fontSize: 10.5, fontWeight: FontWeight.w800, color: AppTheme.primary),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: Colors.amber.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: const Text('CALIDAD', style: TextStyle(fontSize: 9.5, fontWeight: FontWeight.w800, color: Colors.amber)),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text('Hola, $primerNombre', style: GoogleFonts.inter(fontSize: 21, fontWeight: FontWeight.w900, color: Colors.white)),
              Text(nombreCompleto, style: GoogleFonts.inter(fontSize: 13, color: const Color(0xFF94A3B8))),
              const SizedBox(height: 16),
              const Divider(color: Colors.white12),
              const SizedBox(height: 12),
              Row(
                children: [
                  _buildMetricPill(label: 'Obras a Inspeccionar', value: _proyectos.length.toString(), color: AppTheme.primary),
                  const SizedBox(width: 10),
                  _buildMetricPill(label: 'En Ejecución', value: _conteoActivos.toString(), color: AppTheme.success),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),

        _buildSectionHeader('Herramientas de Inspección', titleColor),
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
                icon: Icons.checklist_rtl_rounded,
                title: 'Órdenes de Trabajo a Verificar',
                subtitle: 'Revisión y cambio de estado de tareas',
                iconColor: const Color(0xFF10B981),
                iconBg: isDark ? const Color(0xFF064E3B) : const Color(0xFFECFDF5),
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const OrdenesTrabajoScreen())),
              ),
              Divider(height: 1, color: dividerColor),
              _buildToolRow(
                icon: Icons.account_tree_outlined,
                title: 'Estructuras y Niveles',
                subtitle: 'Validación de sectores concluidos',
                iconColor: isDark ? const Color(0xFF38BDF8) : AppTheme.info,
                iconBg: isDark ? const Color(0xFF13283E) : const Color(0xFFF0F9FF),
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProyectosScreen())),
              ),
            ],
          ),
        ),
        const SizedBox(height: 22),
        _buildProyectosListSection(titleColor, cardBg, borderColor),
      ],
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // 5. DASHBOARD OPERARIOS DE CAMPO (ALBAÑIL, ELÉCTRICO, PLOMERO)
  // ──────────────────────────────────────────────────────────────────────────
  Widget _buildOperarioCampoView(AuthProvider auth, String primerNombre, String nombreCompleto, bool isDark) {
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        // Hero Operario
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: const Color(0xFF0F172A),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'MI JORNADA LABORAL',
                    style: GoogleFonts.inter(fontSize: 10.5, fontWeight: FontWeight.w800, color: AppTheme.primary),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppTheme.primary.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      auth.rolNormalizado,
                      style: const TextStyle(fontSize: 9.5, fontWeight: FontWeight.w800, color: AppTheme.primaryLight),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text('Hola, $primerNombre', style: GoogleFonts.inter(fontSize: 21, fontWeight: FontWeight.w900, color: Colors.white)),
              Text(nombreCompleto, style: GoogleFonts.inter(fontSize: 13, color: const Color(0xFF94A3B8))),
              const SizedBox(height: 14),
              const Divider(color: Colors.white12),
              const SizedBox(height: 8),
              Row(
                children: [
                  const Icon(Icons.handyman_rounded, size: 16, color: AppTheme.primaryLight),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Revisá tus órdenes asignadas para la jornada de hoy.',
                      style: GoogleFonts.inter(fontSize: 12, color: Colors.white70),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        // Acceso Destacado a Órdenes de Trabajo
        Container(
          decoration: BoxDecoration(
            color: isDark ? const Color(0xFF1E293B) : const Color(0xFFECFDF5),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: const Color(0xFF10B981).withValues(alpha: 0.4)),
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            leading: Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFF10B981).withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.assignment_turned_in_rounded, color: Color(0xFF10B981), size: 24),
            ),
            title: const Text(
              'Mis Órdenes de Trabajo',
              style: TextStyle(fontWeight: FontWeight.w800, fontSize: 14.5),
            ),
            subtitle: const Text(
              'Consultar tareas asignadas, avance y reportar estado',
              style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
            ),
            trailing: const Icon(Icons.chevron_right_rounded, color: Color(0xFF10B981)),
            onTap: () {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const OrdenesTrabajoScreen()));
            },
          ),
        ),
        const SizedBox(height: 16),

        // Recordatorio de Seguridad
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: isDark ? const Color(0xFF1E1F3D) : const Color(0xFFFEF3C7),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.amber.withValues(alpha: 0.5)),
          ),
          child: const Row(
            children: [
              Icon(Icons.shield_outlined, color: Colors.amber, size: 24),
              SizedBox(width: 12),
              Expanded(
                child: Text(
                  'Seguridad en obra: uso obligatorio de casco, botas de puntera de acero y arnés en altura.',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),

        // Frentes de Obra
        _buildSectionHeader('Frentes de Obra Asignados', titleColor),
        const SizedBox(height: 10),
        _buildProyectosListSection(titleColor, cardBg, borderColor),
      ],
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // 6. PORTAL DE CLIENTE / PROPIETARIO
  // ──────────────────────────────────────────────────────────────────────────
  Widget _buildClientPortalView(String primerNombre, String nombreCompleto, bool isDark) {
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        // Hero Propietario
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: const Color(0xFF0F172A),
            borderRadius: BorderRadius.circular(14),
            boxShadow: const [
              BoxShadow(color: Color(0x14000000), blurRadius: 12, offset: Offset(0, 4)),
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
                    style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w800, letterSpacing: 1.0, color: AppTheme.primary),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      'CLIENTE',
                      style: GoogleFonts.inter(fontSize: 10, fontWeight: FontWeight.w700, color: Colors.white),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text('Hola, $primerNombre', style: GoogleFonts.inter(fontSize: 21, fontWeight: FontWeight.w900, color: Colors.white)),
              Text(nombreCompleto, style: GoogleFonts.inter(fontSize: 13, color: const Color(0xFF94A3B8))),
              const SizedBox(height: 14),
              const Divider(color: Colors.white12),
              const SizedBox(height: 10),
              Row(
                children: [
                  const Icon(Icons.check_circle_outline_rounded, size: 15, color: AppTheme.primaryLight),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Seguimiento en tiempo real del progreso de tu inmueble.',
                      style: GoogleFonts.inter(fontSize: 11.5, color: Colors.white70),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),

        // Acceso directo a Perfil
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
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PerfilScreen())),
          ),
        ),
        const SizedBox(height: 20),

        _buildSectionHeader('Mis Inmuebles y Proyectos', titleColor),
        const SizedBox(height: 10),
        _buildProyectosListSection(titleColor, cardBg, borderColor),
      ],
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // COMPONENTES AUXILIARES
  // ──────────────────────────────────────────────────────────────────────────
  Widget _buildBannerEmpresaActiva(AuthProvider auth, bool isDark) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: auth.esVistaGlobal
            ? (isDark ? const Color(0xFF1E293B) : const Color(0xFFEFF6FF))
            : (isDark ? const Color(0xFF064E3B).withValues(alpha: 0.4) : const Color(0xFFDCFCE7)),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: auth.esVistaGlobal
              ? AppTheme.primary.withValues(alpha: 0.3)
              : AppTheme.success.withValues(alpha: 0.4),
        ),
      ),
      child: Row(
        children: [
          Icon(
            auth.esVistaGlobal ? Icons.public_rounded : Icons.business_rounded,
            size: 20,
            color: auth.esVistaGlobal ? AppTheme.primary : AppTheme.success,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  auth.esVistaGlobal ? 'Alcance: Plataforma Global' : 'Empresa Activa:',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: auth.esVistaGlobal ? AppTheme.primary : AppTheme.success,
                  ),
                ),
                Text(
                  auth.esVistaGlobal ? 'Todas las Empresas' : (auth.nombreEmpresaActiva ?? 'Empresa Activa'),
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w800,
                    color: isDark ? Colors.white : AppTheme.textPrimary,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          OutlinedButton(
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              minimumSize: Size.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              side: BorderSide(
                color: auth.esVistaGlobal ? AppTheme.primary : AppTheme.success,
              ),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
            ),
            onPressed: () => _mostrarSelectorEmpresas(context),
            child: Text(
              'Cambiar',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.bold,
                color: auth.esVistaGlobal ? AppTheme.primary : AppTheme.success,
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _mostrarSelectorEmpresas(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (bCtx) {
        return FutureBuilder<List<Map<String, dynamic>>>(
          future: _empresaService.listarEmpresas(),
          builder: (ctx, snapshot) {
            final auth = Provider.of<AuthProvider>(context, listen: false);

            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Padding(
                padding: EdgeInsets.all(40),
                child: Center(child: CircularProgressIndicator()),
              );
            }

            final empresas = snapshot.data ?? [];

            return Container(
              padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
              constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.7),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Seleccionar Empresa Activa',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close_rounded),
                        onPressed: () => Navigator.pop(ctx),
                      ),
                    ],
                  ),
                  const Text(
                    'Define el contexto operativo para consultar proyectos y órdenes.',
                    style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
                  ),
                  const Divider(height: 20),

                  // Opción Global
                  ListTile(
                    leading: Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: AppTheme.primary.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(Icons.public_rounded, color: AppTheme.primary),
                    ),
                    title: const Text('Vista Global (Todas las Empresas)', style: TextStyle(fontWeight: FontWeight.w700)),
                    subtitle: const Text('Muestra información consolidada de toda la plataforma', style: TextStyle(fontSize: 11)),
                    trailing: auth.esVistaGlobal ? const Icon(Icons.check_circle_rounded, color: AppTheme.primary) : null,
                    onTap: () async {
                      Navigator.pop(bCtx);
                      await auth.seleccionarEmpresa(null);
                      if (!mounted) return;
                      _cargarObras();
                    },
                  ),
                  const Divider(),

                  Expanded(
                    child: empresas.isEmpty
                        ? const Center(child: Text('No hay empresas registradas.'))
                        : ListView.separated(
                            shrinkWrap: true,
                            itemCount: empresas.length,
                            separatorBuilder: (_, __) => const Divider(height: 1),
                            itemBuilder: (lCtx, i) {
                              final emp = empresas[i];
                              final id = emp['id_empresa'];
                              final nombre = emp['razon_social'] ?? emp['nombre_comercial'] ?? 'Empresa #$id';
                              final esSeleccionada = auth.idEmpresaActiva == id;

                              return ListTile(
                                leading: Container(
                                  padding: const EdgeInsets.all(8),
                                  decoration: BoxDecoration(
                                    color: Colors.grey.withValues(alpha: 0.1),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: const Icon(Icons.business_rounded, color: AppTheme.textSecondary),
                                ),
                                title: Text(nombre, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13.5)),
                                subtitle: Text('ID: $id · NIT: ${emp['nit'] ?? 'S/N'}', style: const TextStyle(fontSize: 11)),
                                trailing: esSeleccionada ? const Icon(Icons.check_circle_rounded, color: AppTheme.success) : null,
                                onTap: () async {
                                  Navigator.pop(bCtx);
                                  await auth.seleccionarEmpresa(emp);
                                  if (!mounted) return;
                                  _cargarObras();
                                },
                              );
                            },
                          ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildSectionHeader(String title, Color titleColor) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          title,
          style: GoogleFonts.inter(fontSize: 15.5, fontWeight: FontWeight.w800, color: titleColor, letterSpacing: -0.2),
        ),
      ],
    );
  }

  Widget _buildProyectosListSection(Color titleColor, Color cardBg, Color borderColor) {
    if (_cargando) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(28.0),
          child: CircularProgressIndicator(color: AppTheme.primary, strokeWidth: 2.5),
        ),
      );
    }

    if (_proyectos.isEmpty) {
      return Container(
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
              Text('No hay proyectos registrados', style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w700, color: titleColor)),
              const SizedBox(height: 4),
              const Text('Crea obras desde la web o recarga la conexión.', textAlign: TextAlign.center, style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8))),
            ],
          ),
        ),
      );
    }

    return Column(
      children: _proyectos.map((p) {
        return CleanProjectCard(
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
        );
      }).toList(),
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