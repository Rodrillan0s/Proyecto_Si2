import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../services/crm_service.dart';
import '../theme/app_theme.dart';
import '../widgets/ev_widgets.dart';
import 'crm_cliente_detalle_screen.dart';

class CrmScreen extends StatefulWidget {
  const CrmScreen({super.key});

  @override
  State<CrmScreen> createState() => _CrmScreenState();
}

class _CrmScreenState extends State<CrmScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final CrmService _crmService = CrmService();

  late Future<List<Map<String, dynamic>>> _futureProspectos;
  late Future<List<Map<String, dynamic>>> _futureClientes;
  late Future<Map<String, dynamic>> _futureMetricas;

  String _busqueda = '';
  String _filtroEstado = 'TODOS';
  final TextEditingController _searchCtrl = TextEditingController();

  final List<String> _estadosPipeline = [
    'TODOS',
    'NUEVO',
    'CONTACTADO',
    'INTERESADO',
    'NEGOCIACION',
    'RESERVADO',
    'VENDIDO',
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _tabController.addListener(() {
      if (!_tabController.indexIsChanging) {
        setState(() {});
      }
    });
    _cargarDatos();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchCtrl.dispose();
    super.dispose();
  }

  void _cargarDatos() {
    _futureProspectos = _crmService.listarClientes(tipoCliente: 'PROSPECTO');
    _futureClientes = _crmService.listarClientes(tipoCliente: 'CLIENTE');
    _futureMetricas = _crmService.obtenerMetricas();
  }

  Future<void> _refrescar() async {
    setState(() {
      _cargarDatos();
    });
    await Future.wait([_futureProspectos, _futureClientes, _futureMetricas]);
  }

  Color _colorEstado(String estado, bool isDark) {
    switch (estado.toUpperCase()) {
      case 'NUEVO':
        return isDark ? const Color(0xFF38BDF8) : const Color(0xFF0284C7);
      case 'CONTACTADO':
        return isDark ? const Color(0xFF2DD4BF) : const Color(0xFF0D9488);
      case 'INTERESADO':
        return isDark ? const Color(0xFFFBBF24) : const Color(0xFFD97706);
      case 'NEGOCIACION':
      case 'NEGOCIACIÓN':
        return isDark ? const Color(0xFFFB923C) : AppTheme.primary;
      case 'RESERVADO':
        return isDark ? const Color(0xFFA78BFA) : const Color(0xFF7C3AED);
      case 'VENDIDO':
      case 'CONVERTIDO':
        return isDark ? const Color(0xFF34D399) : AppTheme.success;
      case 'PERDIDO':
        return isDark ? const Color(0xFFF87171) : AppTheme.error;
      default:
        return isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);
    }
  }

  void _mostrarModalNuevoProspecto() async {
    final nombreCtrl = TextEditingController();
    final apellidoCtrl = TextEditingController();
    final ciCtrl = TextEditingController();
    final telCtrl = TextEditingController();
    final emailCtrl = TextEditingController();
    final presupuestoCtrl = TextEditingController();
    final notasCtrl = TextEditingController();

    String origenSeleccionado = 'Visita a Obra';
    final origenesDisponibles = [
      'Visita a Obra',
      'Feria Inmobiliaria',
      'Recomendación',
      'Redes Sociales',
      'Sitio Web',
      'Llamada Telefónica',
      'Otro',
    ];

    int? idAsesorSeleccionado;
    List<Map<String, dynamic>> asesoresDisponibles = [];
    bool guardando = false;

    try {
      asesoresDisponibles = await _crmService.listarAsesores();
      if (asesoresDisponibles.isNotEmpty) {
        idAsesorSeleccionado = int.tryParse(asesoresDisponibles.first['id_usuario']?.toString() ?? '');
      }
    } catch (_) {}

    if (!mounted) return;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            final isDark = Theme.of(context).brightness == Brightness.dark;
            final sheetBg = isDark ? const Color(0xFF131D31) : Colors.white;
            final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

            return Container(
              padding: EdgeInsets.fromLTRB(20, 16, 20, 24 + MediaQuery.of(context).viewInsets.bottom),
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
                    Text(
                      'Registrar Nuevo Prospecto',
                      style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w800, color: titleColor),
                    ),
                    const SizedBox(height: 14),

                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: nombreCtrl,
                            decoration: const InputDecoration(
                              labelText: 'Nombre *',
                              hintText: 'Ej: Carlos',
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: TextField(
                            controller: apellidoCtrl,
                            decoration: const InputDecoration(
                              labelText: 'Apellido',
                              hintText: 'Ej: Mendoza',
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: telCtrl,
                            keyboardType: TextInputType.phone,
                            decoration: const InputDecoration(
                              labelText: 'Teléfono / WhatsApp *',
                              hintText: 'Ej: 71234567',
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: TextField(
                            controller: ciCtrl,
                            decoration: const InputDecoration(
                              labelText: 'C.I. / Documento',
                              hintText: 'Ej: 8392102',
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    TextField(
                      controller: emailCtrl,
                      keyboardType: TextInputType.emailAddress,
                      decoration: const InputDecoration(
                        labelText: 'Correo Electrónico',
                        hintText: 'carlos.mendoza@email.com',
                      ),
                    ),
                    const SizedBox(height: 12),

                    Row(
                      children: [
                        Expanded(
                          child: DropdownButtonFormField<String>(
                            initialValue: origenSeleccionado,
                            decoration: const InputDecoration(labelText: 'Origen de Contacto'),
                            items: origenesDisponibles
                                .map((o) => DropdownMenuItem(value: o, child: Text(o, style: const TextStyle(fontSize: 12))))
                                .toList(),
                            onChanged: (v) => setModalState(() => origenSeleccionado = v ?? 'Visita a Obra'),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: TextField(
                            controller: presupuestoCtrl,
                            keyboardType: const TextInputType.numberWithOptions(decimal: true),
                            decoration: const InputDecoration(
                              labelText: 'Presupuesto (BOB)',
                              hintText: 'Ej: 450000',
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    if (asesoresDisponibles.isNotEmpty)
                      DropdownButtonFormField<int>(
                        initialValue: idAsesorSeleccionado,
                        decoration: const InputDecoration(labelText: 'Asesor Comercial Asignado'),
                        items: asesoresDisponibles.map((a) {
                          final id = int.tryParse(a['id_usuario']?.toString() ?? '') ?? 0;
                          final nombre = a['nombre_completo'] ?? a['nombre_usuario'] ?? 'Asesor';
                          return DropdownMenuItem(value: id, child: Text(nombre, style: const TextStyle(fontSize: 12.5)));
                        }).toList(),
                        onChanged: (v) => setModalState(() => idAsesorSeleccionado = v),
                      ),
                    const SizedBox(height: 12),

                    TextField(
                      controller: notasCtrl,
                      maxLines: 2,
                      decoration: const InputDecoration(
                        labelText: 'Interés inicial y notas',
                        hintText: 'Interesado en departamentos de 2 dormitorios',
                      ),
                    ),
                    const SizedBox(height: 18),

                    ObratecPrimaryButton(
                      label: 'Registrar Prospecto',
                      loading: guardando,
                      onPressed: () async {
                        final nombre = nombreCtrl.text.trim();
                        final tel = telCtrl.text.trim();
                        if (nombre.isEmpty || tel.isEmpty) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('El nombre y teléfono son obligatorios.')),
                          );
                          return;
                        }

                        setModalState(() => guardando = true);
                        try {
                          final payload = <String, dynamic>{
                            'tipo_cliente': 'PROSPECTO',
                            'nombre': nombre,
                            'apellido': apellidoCtrl.text.trim(),
                            'telefono': tel,
                            'ci': ciCtrl.text.trim(),
                            'email': emailCtrl.text.trim(),
                            'origen': origenSeleccionado,
                            'presupuesto_estimado': double.tryParse(presupuestoCtrl.text.trim()) ?? 0,
                            'notas': notasCtrl.text.trim(),
                          };
                          if (idAsesorSeleccionado != null) {
                            payload['id_usuario_asignado'] = idAsesorSeleccionado;
                          }

                          await _crmService.crearCliente(payload);

                          if (!ctx.mounted) return;
                          Navigator.pop(ctx);
                          _refrescar();

                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                              content: Text('Prospecto registrado exitosamente en el CRM.'),
                              backgroundColor: AppTheme.success,
                            ));
                          }
                        } catch (e) {
                          setModalState(() => guardando = false);
                          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                            content: Text(e.toString().replaceAll('Exception: ', '')),
                            backgroundColor: AppTheme.error,
                          ));
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

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final topBarBg = isDark ? const Color(0xFF0F172A) : Colors.white;
    final dividerColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final tabBoxBg = isDark ? const Color(0xFF131D31) : const Color(0xFFF1F5F9);
    final indicatorBg = isDark ? const Color(0xFFF97316) : const Color(0xFF0F172A);

    return Scaffold(
      appBar: AppBar(
        title: Text(
          'Clientes y CRM',
          style: GoogleFonts.inter(fontWeight: FontWeight.w800, fontSize: 16.5),
        ),
        actions: [
          IconButton(
            tooltip: 'Recargar',
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _refrescar,
          ),
          const SizedBox(width: 4),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: AppTheme.primary,
        icon: const Icon(Icons.person_add_alt_1_rounded, color: Colors.white, size: 20),
        label: Text('Nuevo Prospecto', style: GoogleFonts.inter(fontWeight: FontWeight.w700, color: Colors.white)),
        onPressed: _mostrarModalNuevoProspecto,
      ),
      body: SafeArea(
        child: Column(
          children: [
            // RESUMEN MÉTRICO DEL PIPELINE
            FutureBuilder<Map<String, dynamic>>(
              future: _futureMetricas,
              builder: (context, snapshot) {
                final metricas = snapshot.data ?? {};
                final totalProspectos = metricas['total_prospectos']?.toString() ?? '0';
                final totalClientes = metricas['total_clientes']?.toString() ?? '0';
                final unidadesAsociadas = metricas['unidades_asociadas']?.toString() ?? '0';

                return Container(
                  color: topBarBg,
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 10),
                  child: Row(
                    children: [
                      _buildMetricCard('Prospectos', totalProspectos, const Color(0xFF38BDF8), isDark),
                      const SizedBox(width: 8),
                      _buildMetricCard('Clientes', totalClientes, AppTheme.success, isDark),
                      const SizedBox(width: 8),
                      _buildMetricCard('Unidades Negociadas', unidadesAsociadas, AppTheme.primary, isDark),
                    ],
                  ),
                );
              },
            ),

            // BARRA DE BÚSQUEDA Y PESTAÑAS (PROSPECTOS / CLIENTES)
            Container(
              color: topBarBg,
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 12),
              child: Column(
                children: [
                  TextField(
                    controller: _searchCtrl,
                    onChanged: (val) => setState(() => _busqueda = val.trim().toLowerCase()),
                    style: GoogleFonts.inter(fontSize: 13),
                    decoration: InputDecoration(
                      hintText: 'Buscar por nombre, CI o teléfono...',
                      prefixIcon: const Icon(Icons.search_rounded, size: 20, color: Color(0xFF94A3B8)),
                      suffixIcon: _busqueda.isNotEmpty
                          ? IconButton(
                              icon: const Icon(Icons.clear, size: 18),
                              onPressed: () {
                                _searchCtrl.clear();
                                setState(() => _busqueda = '');
                              },
                            )
                          : null,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    ),
                  ),
                  const SizedBox(height: 10),

                  // TAB BAR CONVERTIDO
                  Container(
                    height: 38,
                    padding: const EdgeInsets.all(3),
                    decoration: BoxDecoration(
                      color: tabBoxBg,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: TabBar(
                      controller: _tabController,
                      indicator: BoxDecoration(
                        color: indicatorBg,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      labelColor: Colors.white,
                      unselectedLabelColor: isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B),
                      labelStyle: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w800),
                      unselectedLabelStyle: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w600),
                      dividerColor: Colors.transparent,
                      tabs: const [
                        Tab(text: 'Prospectos (Leads)'),
                        Tab(text: 'Clientes Comerciales'),
                      ],
                    ),
                  ),
                  const SizedBox(height: 10),

                  // FILTRO POR ESTADO EN PIPELINE
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: _estadosPipeline.map((e) {
                        final sel = _filtroEstado == e;
                        return Padding(
                          padding: const EdgeInsets.only(right: 6.0),
                          child: InkWell(
                            onTap: () => setState(() => _filtroEstado = e),
                            borderRadius: BorderRadius.circular(6),
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                              decoration: BoxDecoration(
                                color: sel
                                    ? (isDark ? const Color(0xFFF97316) : const Color(0xFF0F172A))
                                    : (isDark ? const Color(0xFF131D31) : Colors.white),
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(
                                  color: sel
                                      ? Colors.transparent
                                      : (isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0)),
                                ),
                              ),
                              child: Text(
                                e.replaceAll('_', ' '),
                                style: GoogleFonts.inter(
                                  fontSize: 11,
                                  fontWeight: sel ? FontWeight.w700 : FontWeight.w500,
                                  color: sel ? Colors.white : (isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B)),
                                ),
                              ),
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ],
              ),
            ),
            Divider(height: 1, color: dividerColor),

            // CONTENIDO DE LAS PESTAÑAS
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  _buildListaContactos(_futureProspectos, isDark, esProspecto: true),
                  _buildListaContactos(_futureClientes, isDark, esProspecto: false),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricCard(String label, String valor, Color color, bool isDark) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: color.withValues(alpha: isDark ? 0.12 : 0.08),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: color.withValues(alpha: 0.25)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(valor, style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w900, color: color)),
            Text(label, style: GoogleFonts.inter(fontSize: 10.5, fontWeight: FontWeight.w600, color: isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B)), maxLines: 1, overflow: TextOverflow.ellipsis),
          ],
        ),
      ),
    );
  }

  Widget _buildListaContactos(
    Future<List<Map<String, dynamic>>> future,
    bool isDark, {
    required bool esProspecto,
  }) {
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
    final subColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);

    return RefreshIndicator(
      color: AppTheme.primary,
      onRefresh: _refrescar,
      child: FutureBuilder<List<Map<String, dynamic>>>(
        future: future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator(color: AppTheme.primary, strokeWidth: 2.5));
          }

          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Text(
                  snapshot.error.toString().replaceAll('Exception: ', ''),
                  textAlign: TextAlign.center,
                  style: GoogleFonts.inter(fontSize: 13, color: subColor),
                ),
              ),
            );
          }

          final todos = snapshot.data ?? [];

          final filtrados = todos.where((c) {
            final estado = (c['estado'] ?? '').toString().toUpperCase();
            final nombreCompleto = '${c['nombre'] ?? ''} ${c['apellido'] ?? ''}'.toLowerCase();
            final ci = (c['ci'] ?? '').toString().toLowerCase();
            final tel = (c['telefono'] ?? '').toString().toLowerCase();

            final cumpleEstado = (_filtroEstado == 'TODOS') || (estado == _filtroEstado);
            final cumpleBusqueda = _busqueda.isEmpty ||
                nombreCompleto.contains(_busqueda) ||
                ci.contains(_busqueda) ||
                tel.contains(_busqueda);

            return cumpleEstado && cumpleBusqueda;
          }).toList();

          if (filtrados.isEmpty) {
            return ListView(
              padding: const EdgeInsets.all(32),
              children: [
                const SizedBox(height: 30),
                Center(
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: isDark ? const Color(0xFF2E1C14) : const Color(0xFFFFF7ED),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.people_outline_rounded, size: 36, color: AppTheme.primary),
                  ),
                ),
                const SizedBox(height: 14),
                Text(
                  esProspecto ? 'Sin prospectos comerciales' : 'Sin clientes registrados',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.inter(fontSize: 15, fontWeight: FontWeight.w800, color: titleColor),
                ),
                const SizedBox(height: 4),
                Text(
                  _busqueda.isNotEmpty
                      ? 'No hay registros que coincidan con "$_busqueda".'
                      : 'No hay contactos en esta etapa comercial.',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.inter(fontSize: 12.5, color: subColor),
                ),
              ],
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 80),
            itemCount: filtrados.length,
            itemBuilder: (context, index) {
              final c = filtrados[index];
              final idCliente = int.tryParse(c['id_cliente']?.toString() ?? '') ?? 0;
              final nombreCompleto = '${c['nombre'] ?? ''} ${c['apellido'] ?? ''}'.trim();
              final estado = (c['estado'] ?? 'NUEVO').toString().toUpperCase();
              final tel = c['telefono']?.toString() ?? '-';
              final asesor = c['asesor_nombre']?.toString() ?? 'Sin asesor';
              final presupuesto = c['presupuesto_estimado'] != null
                  ? '${c['presupuesto_estimado']} BOB'
                  : null;

              final colorEst = _colorEstado(estado, isDark);

              return Container(
                margin: const EdgeInsets.only(bottom: 10),
                decoration: BoxDecoration(
                  color: cardBg,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: borderColor),
                ),
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                  leading: CircleAvatar(
                    radius: 20,
                    backgroundColor: colorEst.withValues(alpha: 0.15),
                    child: Text(
                      nombreCompleto.isNotEmpty ? nombreCompleto[0].toUpperCase() : 'C',
                      style: GoogleFonts.inter(fontWeight: FontWeight.w900, color: colorEst, fontSize: 16),
                    ),
                  ),
                  title: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          nombreCompleto,
                          style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w800, color: titleColor),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                        decoration: BoxDecoration(
                          color: colorEst.withValues(alpha: isDark ? 0.2 : 0.1),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          estado.replaceAll('_', ' '),
                          style: GoogleFonts.inter(fontSize: 9.5, fontWeight: FontWeight.w800, color: colorEst),
                        ),
                      ),
                    ],
                  ),
                  subtitle: Padding(
                    padding: const EdgeInsets.only(top: 4.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.phone_outlined, size: 12, color: Color(0xFF94A3B8)),
                            const SizedBox(width: 4),
                            Text(tel, style: GoogleFonts.inter(fontSize: 11.5, color: subColor)),
                            if (presupuesto != null) ...[
                              const SizedBox(width: 10),
                              Text('·', style: TextStyle(color: subColor)),
                              const SizedBox(width: 10),
                              Text(presupuesto, style: GoogleFonts.inter(fontSize: 11.5, fontWeight: FontWeight.w700, color: isDark ? const Color(0xFF34D399) : AppTheme.success)),
                            ],
                          ],
                        ),
                        const SizedBox(height: 2),
                        Row(
                          children: [
                            const Icon(Icons.support_agent_rounded, size: 12, color: Color(0xFF94A3B8)),
                            const SizedBox(width: 4),
                            Text('Asesor: $asesor', style: GoogleFonts.inter(fontSize: 11, color: subColor)),
                          ],
                        ),
                      ],
                    ),
                  ),
                  trailing: const Icon(Icons.chevron_right_rounded, color: Color(0xFF94A3B8)),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => CrmClienteDetalleScreen(
                          idCliente: idCliente,
                          nombreCompleto: nombreCompleto,
                          tipoCliente: c['tipo_cliente']?.toString() ?? (esProspecto ? 'PROSPECTO' : 'CLIENTE'),
                        ),
                      ),
                    ).then((_) => _refrescar());
                  },
                ),
              );
            },
          );
        },
      ),
    );
  }
}
