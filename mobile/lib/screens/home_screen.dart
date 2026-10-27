import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../services/auth_provider.dart';
import '../services/obra_service.dart';
import '../services/empresa_service.dart';
import '../theme/app_theme.dart';
import 'asistente_screen.dart';
import 'consultas_tecnicas_screen.dart';
import 'incidencias_screen.dart';
import 'materiales_screen.dart';
import 'notificaciones_screen.dart';
import 'ordenes_trabajo_screen.dart';
import 'perfil_screen.dart';
import 'proyectos_screen.dart';
import 'proyecto_detalle_screen.dart';
import 'avances_obra_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  final ObraService _obraService = ObraService();
  final EmpresaService _empresaService = EmpresaService();

  List<Map<String, dynamic>> _proyectos = [];
  bool _cargando = true;
  int _conteoTotal = 0;
  int _conteoEnEjecucion = 0;
  int _conteoPlanificacion = 0;
  int _conteoConcluidas = 0;
  int? _empresaCargada;

  @override
  void initState() {
    super.initState();
    _cargarObras();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final auth = Provider.of<AuthProvider>(context, listen: false);
    if (_empresaCargada != auth.idEmpresaActiva) {
      _empresaCargada = auth.idEmpresaActiva;
      _cargarObras();
    }
  }

  Future<void> _cargarObras() async {
    setState(() => _cargando = true);
    try {
      final lista = await _obraService.listarProyectos();
      if (!mounted) return;
      final auth = Provider.of<AuthProvider>(context, listen: false);

      List<Map<String, dynamic>> listaFiltrada = lista;
      if (auth.esAdminGlobal && !auth.esVistaGlobal && auth.idEmpresaActiva != null) {
        listaFiltrada = lista.where((p) {
          final pEmpresaId = p['id_empresa'];
          return pEmpresaId == auth.idEmpresaActiva;
        }).toList();
      }

      int total = listaFiltrada.length;
      int ejecucion = 0;
      int planif = 0;
      int concluidas = 0;

      for (var p in listaFiltrada) {
        final rawEstado = (p['estado_obra'] ?? p['estado'] ?? '').toString().trim().toUpperCase();
        if (rawEstado.contains('EJECUCION') || rawEstado.contains('PROCESO') || rawEstado == 'ACTIVO') {
          ejecucion++;
        } else if (rawEstado.contains('PLANIF')) {
          planif++;
        } else if (rawEstado.contains('CONCLU') || rawEstado.contains('FINALIZ')) {
          concluidas++;
        }
      }

      if (!mounted) return;
      setState(() {
        _proyectos = listaFiltrada;
        _conteoTotal = total;
        _conteoEnEjecucion = ejecucion;
        _conteoPlanificacion = planif;
        _conteoConcluidas = concluidas;
        _cargando = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _cargando = false);
    }
  }

  void _mostrarSelectorEmpresas(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    if (!auth.esAdminGlobal) return;

    final futureEmpresas = _empresaService.listarEmpresas();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        final isDark = Theme.of(ctx).brightness == Brightness.dark;
        final sheetBg = isDark ? const Color(0xFF131D31) : Colors.white;
        final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
        final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);

        return Container(
          constraints: BoxConstraints(
            maxHeight: MediaQuery.of(ctx).size.height * 0.75,
          ),
          decoration: BoxDecoration(
            color: sheetBg,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
            border: Border.all(color: borderColor),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF334155) : const Color(0xFFCBD5E1),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'Seleccionar Empresa',
                style: GoogleFonts.inter(
                  fontSize: 17,
                  fontWeight: FontWeight.w800,
                  color: titleColor,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Filtra los datos del dashboard y proyectos según el alcance deseado.',
                style: GoogleFonts.inter(fontSize: 12.5, color: const Color(0xFF94A3B8)),
              ),
              const SizedBox(height: 16),
              ListTile(
                contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                  side: BorderSide(
                    color: auth.esVistaGlobal ? AppTheme.primary : borderColor,
                    width: auth.esVistaGlobal ? 1.5 : 1,
                  ),
                ),
                leading: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: auth.esVistaGlobal
                        ? AppTheme.primary.withValues(alpha: 0.15)
                        : (isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9)),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(
                    Icons.public_rounded,
                    color: auth.esVistaGlobal ? AppTheme.primary : const Color(0xFF64748B),
                    size: 20,
                  ),
                ),
                title: Text(
                  'Todas las empresas',
                  style: GoogleFonts.inter(
                    fontSize: 13.5,
                    fontWeight: auth.esVistaGlobal ? FontWeight.w800 : FontWeight.w600,
                  ),
                ),
                subtitle: const Text(
                  'Vista global consolidada',
                  style: TextStyle(fontSize: 11.5, color: Color(0xFF94A3B8)),
                ),
                trailing: auth.esVistaGlobal
                    ? const Icon(Icons.check_circle_rounded, color: AppTheme.primary, size: 20)
                    : null,
                onTap: () {
                  Navigator.pop(ctx);
                  auth.cambiarEmpresaActiva(null, null);
                  _cargarObras();
                },
              ),
              const SizedBox(height: 10),
              Flexible(
                child: FutureBuilder<List<Map<String, dynamic>>>(
                  future: futureEmpresas,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return const Padding(
                        padding: EdgeInsets.all(24.0),
                        child: Center(
                          child: CircularProgressIndicator(color: AppTheme.primary, strokeWidth: 2.5),
                        ),
                      );
                    }

                    final empresas = snapshot.data ?? [];
                    if (empresas.isEmpty) {
                      return Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Center(
                          child: Text(
                            'No se encontraron empresas registradas.',
                            style: GoogleFonts.inter(fontSize: 12.5, color: const Color(0xFF94A3B8)),
                          ),
                        ),
                      );
                    }

                    return ListView.separated(
                      shrinkWrap: true,
                      itemCount: empresas.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 8),
                      itemBuilder: (_, i) {
                        final emp = empresas[i];
                        final idEmp = int.tryParse(emp['id_empresa']?.toString() ?? '');
                        final nombreEmp = emp['nombre_empresa']?.toString() ??
                            emp['nombre']?.toString() ??
                            emp['razon_social']?.toString() ??
                            'Empresa #${emp['id_empresa']}';
                        final nitEmp = emp['nit']?.toString() ??
                            emp['codigo']?.toString() ??
                            emp['ruc']?.toString() ??
                            '';
                        final esActiva = (!auth.esVistaGlobal) && (auth.idEmpresaActiva == idEmp);

                        return ListTile(
                          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                            side: BorderSide(
                              color: esActiva ? AppTheme.primary : borderColor,
                              width: esActiva ? 1.5 : 1,
                            ),
                          ),
                          leading: Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: esActiva
                                  ? AppTheme.primary.withValues(alpha: 0.15)
                                  : (isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9)),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Icon(
                              Icons.business_rounded,
                              color: esActiva ? AppTheme.primary : const Color(0xFF64748B),
                              size: 20,
                            ),
                          ),
                          title: Text(
                            nombreEmp,
                            style: GoogleFonts.inter(
                              fontSize: 13.5,
                              fontWeight: esActiva ? FontWeight.w800 : FontWeight.w600,
                            ),
                          ),
                          subtitle: Text(
                            nitEmp.isNotEmpty ? 'NIT: $nitEmp' : 'ID: ${emp['id_empresa']}',
                            style: const TextStyle(fontSize: 11.5, color: Color(0xFF94A3B8)),
                          ),
                          trailing: esActiva
                              ? const Icon(Icons.check_circle_rounded, color: AppTheme.primary, size: 20)
                              : null,
                          onTap: () {
                            Navigator.pop(ctx);
                            if (idEmp != null) {
                              auth.cambiarEmpresaActiva(idEmp, nombreEmp);
                              _cargarObras();
                            }
                          },
                        );
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
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    // Vistas principales según el BottomNavigationBar
    final List<Widget> pantallas = [
      _buildDashboardView(isDark),
      const ProyectosScreen(),
      const AsistenteScreen(),
      const NotificacionesScreen(),
      const PerfilScreen(),
    ];

    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC),
      body: IndexedStack(
        index: _currentIndex,
        children: pantallas,
      ),
      bottomNavigationBar: _buildBottomNav(isDark),
    );
  }

  Widget _buildDashboardView(bool isDark) {
    final auth = Provider.of<AuthProvider>(context);
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        titleSpacing: 16,
        backgroundColor: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC),
        elevation: 0,
        title: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: AppTheme.primary,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.construction_rounded, color: Colors.white, size: 18),
            ),
            const SizedBox(width: 8),
            Text(
              'OBRATEC',
              style: GoogleFonts.inter(
                fontSize: 18,
                fontWeight: FontWeight.w900,
                letterSpacing: 1.0,
                color: isDark ? Colors.white : const Color(0xFF0F172A),
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.search_rounded, size: 22),
            tooltip: 'Buscar proyectos',
            onPressed: () => setState(() => _currentIndex = 1),
          ),
          IconButton(
            icon: const Icon(Icons.notifications_none_rounded, size: 22),
            tooltip: 'Notificaciones',
            onPressed: () => setState(() => _currentIndex = 3),
          ),
          GestureDetector(
            onTap: () => setState(() => _currentIndex = 4),
            child: Container(
              margin: const EdgeInsets.only(right: 16, left: 4),
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                color: AppTheme.primary.withValues(alpha: 0.2),
                shape: BoxShape.circle,
                border: Border.all(color: AppTheme.primary, width: 1.5),
              ),
              child: Center(
                child: Text(
                  (auth.usuarioCompleto ?? 'U').substring(0, 1).toUpperCase(),
                  style: GoogleFonts.inter(
                    fontWeight: FontWeight.w800,
                    fontSize: 14,
                    color: AppTheme.primary,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: RefreshIndicator(
          color: AppTheme.primary,
          onRefresh: _cargarObras,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            children: [
              // 1. Tarjeta Selector de Empresa (Prototipo Screen 2 y 8)
              _buildCompanySelectorCard(auth, isDark, cardBg, borderColor, titleColor),
              const SizedBox(height: 20),

              // 2. Resumen General (Métricas 2x2)
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Resumen general',
                    style: GoogleFonts.inter(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: titleColor,
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: borderColor),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          'Activo',
                          style: GoogleFonts.inter(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: const Color(0xFF94A3B8),
                          ),
                        ),
                        const SizedBox(width: 4),
                        const Icon(Icons.keyboard_arrow_down_rounded, size: 14, color: Color(0xFF94A3B8)),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              _buildMetricsGrid2x2(isDark, cardBg, borderColor, titleColor),
              const SizedBox(height: 24),

              // 3. Accesos Rápidos
              Text(
                'Accesos rápidos',
                style: GoogleFonts.inter(
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                  color: titleColor,
                ),
              ),
              const SizedBox(height: 12),
              _buildQuickAccessGrid(isDark, cardBg, borderColor, titleColor),
              const SizedBox(height: 24),

              // 4. Proyectos Recientes
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Proyectos recientes',
                    style: GoogleFonts.inter(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: titleColor,
                    ),
                  ),
                  TextButton(
                    onPressed: () => setState(() => _currentIndex = 1),
                    child: Text(
                      'Ver todos',
                      style: GoogleFonts.inter(
                        fontSize: 12.5,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.primary,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              _buildRecentProjectsList(isDark, cardBg, borderColor, titleColor),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCompanySelectorCard(
    AuthProvider auth,
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
  ) {
    final String nombreEmpresa = auth.esVistaGlobal
        ? 'Todas las empresas'
        : (auth.empresaActivaNombre ?? auth.nombreEmpresa ?? 'Constructora Obratec');
    final String subtitulo = auth.esVistaGlobal
        ? 'Vista global de la plataforma'
        : 'Empresa activa seleccionada';

    return GestureDetector(
      onTap: auth.esAdminGlobal ? () => _mostrarSelectorEmpresas(context) : null,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: cardBg,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: borderColor),
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: isDark ? const Color(0xFF1E293B) : const Color(0xFFFFF7ED),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: isDark ? const Color(0xFF334155) : const Color(0xFFFFEDD5),
                ),
              ),
              child: Icon(
                auth.esVistaGlobal ? Icons.public_rounded : Icons.apartment_rounded,
                color: AppTheme.primary,
                size: 22,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    nombreEmpresa,
                    style: GoogleFonts.inter(
                      fontSize: 14.5,
                      fontWeight: FontWeight.w800,
                      color: titleColor,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitulo,
                    style: GoogleFonts.inter(
                      fontSize: 11.5,
                      color: const Color(0xFF94A3B8),
                    ),
                  ),
                ],
              ),
            ),
            if (auth.esAdminGlobal)
              const Icon(Icons.chevron_right_rounded, color: Color(0xFF94A3B8), size: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricsGrid2x2(
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
  ) {
    if (_cargando) {
      return GridView.count(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        crossAxisCount: 2,
        mainAxisSpacing: 10,
        crossAxisSpacing: 10,
        childAspectRatio: 1.8,
        children: List.generate(4, (_) => Container(
          decoration: BoxDecoration(
            color: cardBg,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: borderColor),
          ),
          child: const Center(
            child: SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primary),
            ),
          ),
        )),
      );
    }

    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      mainAxisSpacing: 10,
      crossAxisSpacing: 10,
      childAspectRatio: 1.8,
      children: [
        _buildKpiCard(
          icon: Icons.apartment_rounded,
          iconColor: const Color(0xFF38BDF8),
          iconBg: isDark ? const Color(0xFF13283E) : const Color(0xFFF0F9FF),
          value: _conteoTotal.toString(),
          label: 'Obras activas',
          cardBg: cardBg,
          borderColor: borderColor,
          titleColor: titleColor,
        ),
        _buildKpiCard(
          icon: Icons.trending_up_rounded,
          iconColor: const Color(0xFF10B981),
          iconBg: isDark ? const Color(0xFF064E3B) : const Color(0xFFECFDF5),
          value: _conteoEnEjecucion.toString(),
          label: 'En ejecución',
          cardBg: cardBg,
          borderColor: borderColor,
          titleColor: titleColor,
        ),
        _buildKpiCard(
          icon: Icons.calendar_today_rounded,
          iconColor: const Color(0xFF818CF8),
          iconBg: isDark ? const Color(0xFF1E1F3D) : const Color(0xFFEEF2FF),
          value: _conteoPlanificacion.toString(),
          label: 'Planificación',
          cardBg: cardBg,
          borderColor: borderColor,
          titleColor: titleColor,
        ),
        _buildKpiCard(
          icon: Icons.check_circle_outline_rounded,
          iconColor: const Color(0xFF10B981),
          iconBg: isDark ? const Color(0xFF064E3B) : const Color(0xFFECFDF5),
          value: _conteoConcluidas.toString(),
          label: 'Concluidas',
          cardBg: cardBg,
          borderColor: borderColor,
          titleColor: titleColor,
        ),
      ],
    );
  }

  Widget _buildKpiCard({
    required IconData icon,
    required Color iconColor,
    required Color iconBg,
    required String value,
    required String label,
    required Color cardBg,
    required Color borderColor,
    required Color titleColor,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderColor),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: iconBg,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: iconColor, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  value,
                  style: GoogleFonts.inter(
                    fontSize: 20,
                    fontWeight: FontWeight.w900,
                    color: titleColor,
                    letterSpacing: -0.5,
                  ),
                ),
                Text(
                  label,
                  style: GoogleFonts.inter(
                    fontSize: 11,
                    fontWeight: FontWeight.w500,
                    color: const Color(0xFF94A3B8),
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickAccessGrid(
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
  ) {
    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 3,
      mainAxisSpacing: 10,
      crossAxisSpacing: 10,
      childAspectRatio: 1.05,
      children: [
        _buildQuickAccessItem(
          icon: Icons.apartment_rounded,
          iconColor: AppTheme.primary,
          label: 'Proyectos',
          onTap: () => setState(() => _currentIndex = 1),
          isDark: isDark,
          cardBg: cardBg,
          borderColor: borderColor,
          titleColor: titleColor,
        ),
        _buildQuickAccessItem(
          icon: Icons.assignment_outlined,
          iconColor: const Color(0xFF10B981),
          label: 'Órdenes de trabajo',
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const OrdenesTrabajoScreen())),
          isDark: isDark,
          cardBg: cardBg,
          borderColor: borderColor,
          titleColor: titleColor,
        ),
        _buildQuickAccessItem(
          icon: Icons.warning_amber_rounded,
          iconColor: AppTheme.error,
          label: 'Incidencias',
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const IncidenciasScreen())),
          isDark: isDark,
          cardBg: cardBg,
          borderColor: borderColor,
          titleColor: titleColor,
        ),
        _buildQuickAccessItem(
          icon: Icons.inventory_2_outlined,
          iconColor: const Color(0xFF0284C7),
          label: 'Materiales',
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MaterialesScreen())),
          isDark: isDark,
          cardBg: cardBg,
          borderColor: borderColor,
          titleColor: titleColor,
        ),
        _buildQuickAccessItem(
          icon: Icons.help_outline_rounded,
          iconColor: const Color(0xFFF59E0B),
          label: 'Consultas técnicas',
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ConsultasTecnicasScreen())),
          isDark: isDark,
          cardBg: cardBg,
          borderColor: borderColor,
          titleColor: titleColor,
        ),
        _buildQuickAccessItem(
          icon: Icons.timeline_rounded,
          iconColor: const Color(0xFF8B5CF6),
          label: 'Avances',
          onTap: () {
            if (_proyectos.isNotEmpty) {
              final primerObraId = int.tryParse(_proyectos.first['id_obra']?.toString() ?? '0') ?? 0;
              final primerObraNombre = _proyectos.first['nombre']?.toString() ?? 'Obra';
              final primerObraCodigo = _proyectos.first['codigo']?.toString() ?? 'P-0000';
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => AvancesObraScreen(
                    idObra: primerObraId,
                    nombreObra: primerObraNombre,
                    codigoObra: primerObraCodigo,
                  ),
                ),
              );
            } else {
              setState(() => _currentIndex = 1);
            }
          },
          isDark: isDark,
          cardBg: cardBg,
          borderColor: borderColor,
          titleColor: titleColor,
        ),
      ],
    );
  }

  Widget _buildQuickAccessItem({
    required IconData icon,
    required Color iconColor,
    required String label,
    required VoidCallback onTap,
    required bool isDark,
    required Color cardBg,
    required Color borderColor,
    required Color titleColor,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 10),
        decoration: BoxDecoration(
          color: cardBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: borderColor),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(9),
              decoration: BoxDecoration(
                color: iconColor.withValues(alpha: isDark ? 0.18 : 0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: iconColor, size: 22),
            ),
            const SizedBox(height: 8),
            Text(
              label,
              textAlign: TextAlign.center,
              style: GoogleFonts.inter(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: titleColor,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecentProjectsList(
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
  ) {
    if (_cargando) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(20),
          child: CircularProgressIndicator(color: AppTheme.primary, strokeWidth: 2),
        ),
      );
    }

    if (_proyectos.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: cardBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: borderColor),
        ),
        child: Center(
          child: Column(
            children: [
              const Icon(Icons.folder_open_rounded, size: 36, color: Color(0xFF94A3B8)),
              const SizedBox(height: 8),
              Text(
                'No hay proyectos disponibles',
                style: GoogleFonts.inter(fontSize: 13.5, fontWeight: FontWeight.w700, color: titleColor),
              ),
            ],
          ),
        ),
      );
    }

    final topProyectos = _proyectos.take(3).toList();

    return Column(
      children: topProyectos.map((p) {
        final idObra = int.tryParse(p['id_obra']?.toString() ?? '0') ?? 0;
        final codigo = p['codigo']?.toString() ?? 'P-0000';
        final nombre = p['nombre']?.toString() ?? 'Proyecto';
        final tipo = p['tipo_obra_nombre']?.toString() ?? 'Edificaciones';
        final estado = (p['estado_obra'] ?? p['estado'] ?? 'PLANIFICACION').toString().toUpperCase();

        Color pillColor = AppTheme.info;
        if (estado.contains('EJEC') || estado.contains('ACTIVO')) pillColor = AppTheme.success;
        if (estado.contains('CONCLU') || estado.contains('FINALIZ')) pillColor = const Color(0xFF818CF8);

        return Container(
          margin: const EdgeInsets.only(bottom: 10),
          decoration: BoxDecoration(
            color: cardBg,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: borderColor),
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
            leading: Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: isDark ? const Color(0xFF1E293B) : const Color(0xFFFFF7ED),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.apartment_rounded, color: AppTheme.primary, size: 24),
            ),
            title: Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    codigo,
                    style: GoogleFonts.inter(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w800,
                      color: AppTheme.primary,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: pillColor.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    estado,
                    style: GoogleFonts.inter(
                      fontSize: 9.5,
                      fontWeight: FontWeight.w800,
                      color: pillColor,
                    ),
                  ),
                ),
              ],
            ),
            subtitle: Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    nombre,
                    style: GoogleFonts.inter(
                      fontSize: 13.5,
                      fontWeight: FontWeight.w800,
                      color: titleColor,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    tipo,
                    style: GoogleFonts.inter(fontSize: 11.5, color: const Color(0xFF94A3B8)),
                  ),
                ],
              ),
            ),
            trailing: const Icon(Icons.chevron_right_rounded, color: Color(0xFF94A3B8), size: 20),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => ProyectoDetalleScreen(
                    idObra: idObra,
                    codigo: codigo,
                    nombre: nombre,
                    tipoNombre: tipo,
                    estado: estado,
                    ubicacion: p['ubicacion']?.toString() ?? '',
                    fechaInicio: p['fecha_inicio']?.toString() ?? '',
                  ),
                ),
              );
            },
          ),
        );
      }).toList(),
    );
  }

  Widget _buildBottomNav(bool isDark) {
    return Container(
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF0F172A) : Colors.white,
        border: Border(
          top: BorderSide(
            color: isDark ? const Color(0xFF1E293B) : const Color(0xFFE2E8F0),
            width: 1,
          ),
        ),
      ),
      child: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
        type: BottomNavigationBarType.fixed,
        backgroundColor: Colors.transparent,
        elevation: 0,
        selectedItemColor: AppTheme.primary,
        unselectedItemColor: isDark ? const Color(0xFF64748B) : const Color(0xFF94A3B8),
        selectedLabelStyle: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w800),
        unselectedLabelStyle: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w500),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_filled),
            label: 'Inicio',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.apartment_rounded),
            label: 'Proyectos',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.auto_awesome_rounded),
            label: 'Asistente',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.notifications_none_rounded),
            label: 'Notificaciones',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.more_horiz_rounded),
            label: 'Más',
          ),
        ],
      ),
    );
  }
}
