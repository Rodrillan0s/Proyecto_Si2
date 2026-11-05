import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../services/auth_provider.dart';
import '../services/consulta_tecnica_service.dart';
import '../services/obra_service.dart';
import '../theme/app_theme.dart';
import 'consulta_tecnica_detalle_screen.dart';

class ConsultasTecnicasScreen extends StatefulWidget {
  final int? idObraFiltro;
  final String? nombreObraFiltro;

  const ConsultasTecnicasScreen({super.key, this.idObraFiltro, this.nombreObraFiltro});

  @override
  State<ConsultasTecnicasScreen> createState() => _ConsultasTecnicasScreenState();
}

class _ConsultasTecnicasScreenState extends State<ConsultasTecnicasScreen> {
  final ConsultaTecnicaService _service = ConsultaTecnicaService();
  final ObraService _obraService = ObraService();
  final TextEditingController _searchCtrl = TextEditingController();

  List<Map<String, dynamic>> _consultas = [];
  bool _cargando = true;
  String? _error;

  String _filtroEstado = '';
  int _pagina = 1;
  int _total = 0;
  Timer? _debounce;

  @override
  void initState() {
    super.initState();
    _cargarConsultas();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _searchCtrl.dispose();
    super.dispose();
  }

  void _onSearchChanged(String query) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 350), () {
      _pagina = 1;
      _cargarConsultas();
    });
  }

  Future<void> _cargarConsultas() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final res = await _service.listarConsultas(
        idObra: widget.idObraFiltro,
        estado: _filtroEstado.isNotEmpty ? _filtroEstado : null,
        busqueda: _searchCtrl.text.trim().isNotEmpty ? _searchCtrl.text.trim() : null,
        page: _pagina,
        limit: 30,
      );
      if (!mounted) return;
      final items = List<Map<String, dynamic>>.from(res['items'] ?? []);
      setState(() {
        _consultas = items;
        _total = (res['total'] as num?)?.toInt() ?? items.length;
        _cargando = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
        _cargando = false;
      });
    }
  }

  Color _colorEstado(String estado) {
    switch (estado.toUpperCase()) {
      case 'ABIERTA':
        return const Color(0xFFF59E0B);
      case 'ASIGNADA':
        return const Color(0xFF6366F1);
      case 'RESPONDIDA':
        return const Color(0xFF0D9488);
      case 'CERRADA':
        return const Color(0xFF64748B);
      default:
        return const Color(0xFF94A3B8);
    }
  }

  void _abrirModalCrear() async {
    int idObraSeleccionada = widget.idObraFiltro ?? 0;
    List<Map<String, dynamic>> obras = [];

    if (idObraSeleccionada == 0) {
      try {
        obras = await _obraService.listarProyectos();
        if (obras.isNotEmpty) {
          idObraSeleccionada = obras.first['id_obra'] as int;
        }
      } catch (_) {}
    }

    if (!mounted) return;

    final asuntoCtrl = TextEditingController();
    final descCtrl = TextEditingController();
    final refCtrl = TextEditingController();
    int? asignadoA;
    List<Map<String, dynamic>> usuariosAsignables = [];
    bool cargandoUsuarios = false;

    Future<void> cargarUsuarios(int idObra, void Function(void Function()) setModalState) async {
      setModalState(() => cargandoUsuarios = true);
      try {
        final list = await _service.obtenerUsuariosAsignables(idObra);
        setModalState(() {
          usuariosAsignables = list;
          cargandoUsuarios = false;
        });
      } catch (_) {
        setModalState(() => cargandoUsuarios = false);
      }
    }

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

            if (usuariosAsignables.isEmpty && idObraSeleccionada > 0 && !cargandoUsuarios) {
              cargarUsuarios(idObraSeleccionada, setModalState);
            }

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
                          color: Colors.grey.withValues(alpha: 0.3),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Nueva Consulta Técnica (RFI)',
                      style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w800, color: titleColor),
                    ),
                    const SizedBox(height: 14),

                    // Selector de obra si no está fijada
                    if (widget.idObraFiltro == null) ...[
                      DropdownButtonFormField<int>(
                        initialValue: idObraSeleccionada > 0 ? idObraSeleccionada : null,
                        decoration: const InputDecoration(labelText: 'Obra / Proyecto *'),
                        items: obras.map((o) {
                          return DropdownMenuItem<int>(
                            value: o['id_obra'] as int,
                            child: Text(o['nombre'] ?? 'Obra', style: const TextStyle(fontSize: 12)),
                          );
                        }).toList(),
                        onChanged: (val) {
                          if (val != null) {
                            setModalState(() {
                              idObraSeleccionada = val;
                              asignadoA = null;
                            });
                            cargarUsuarios(val, setModalState);
                          }
                        },
                      ),
                      const SizedBox(height: 12),
                    ],

                    // Asunto
                    TextField(
                      controller: asuntoCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Asunto de la consulta *',
                        hintText: 'Ej. Discrepancia en armadura eje 4',
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Referencia
                    TextField(
                      controller: refCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Referencia Técnica (Plano, Eje o Detalle)',
                        hintText: 'Ej. Plano E-04 / Detalle D-2',
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Descripción
                    TextField(
                      controller: descCtrl,
                      maxLines: 4,
                      decoration: const InputDecoration(
                        labelText: 'Descripción técnica detallada *',
                        hintText: 'Detalle claramente la consulta, inconsistencia o aclaración técnica requerida...',
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Asignación inicial opcional
                    DropdownButtonFormField<int>(
                      initialValue: asignadoA,
                      decoration: const InputDecoration(labelText: 'Asignar a responsable (opcional)'),
                      items: [
                        const DropdownMenuItem<int>(
                          value: null,
                          child: Text('Sin asignar (quedará ABIERTA)', style: TextStyle(fontSize: 12, color: Colors.grey)),
                        ),
                        ...usuariosAsignables.map((u) {
                          return DropdownMenuItem<int>(
                            value: u['id_usuario'] as int,
                            child: Text('${u['nombre_completo']} (${u['rol']})', style: const TextStyle(fontSize: 12)),
                          );
                        }),
                      ],
                      onChanged: (val) => setModalState(() => asignadoA = val),
                    ),
                    const SizedBox(height: 20),

                    // Botón Guardar
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primary,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 14),
                        ),
                        onPressed: () async {
                          final asunto = asuntoCtrl.text.trim();
                          final desc = descCtrl.text.trim();
                          if (asunto.length < 3) {
                            ScaffoldMessenger.of(ctx).showSnackBar(
                              const SnackBar(content: Text('El asunto debe tener al menos 3 caracteres.')),
                            );
                            return;
                          }
                          if (desc.length < 5) {
                            ScaffoldMessenger.of(ctx).showSnackBar(
                              const SnackBar(content: Text('La descripción debe tener al menos 5 caracteres.')),
                            );
                            return;
                          }
                          if (idObraSeleccionada <= 0) {
                            ScaffoldMessenger.of(ctx).showSnackBar(
                              const SnackBar(content: Text('Debe seleccionar una obra válida.')),
                            );
                            return;
                          }

                          final nav = Navigator.of(context);
                          final sm = ScaffoldMessenger.of(context);
                          Navigator.pop(ctx);
                          try {
                            final nueva = await _service.crearConsulta(
                              idObra: idObraSeleccionada,
                              asunto: asunto,
                              descripcion: desc,
                              referenciaTecnica: refCtrl.text.trim().isNotEmpty ? refCtrl.text.trim() : null,
                              asignadoA: asignadoA,
                            );
                            _cargarConsultas();
                            if (mounted) {
                              nav.push(
                                MaterialPageRoute(
                                  builder: (_) => ConsultaTecnicaDetalleScreen(
                                    idConsultaTecnica: nueva['id_consulta_tecnica'] as int,
                                  ),
                                ),
                              );
                            }
                          } catch (e) {
                            if (mounted) {
                              sm.showSnackBar(
                                SnackBar(content: Text(e.toString().replaceAll('Exception: ', ''))),
                              );
                            }
                          }
                        },
                        child: const Text('Registrar Consulta Técnica', style: TextStyle(fontWeight: FontWeight.bold)),
                      ),
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

  Widget _buildFiltroPill(String label, String valor) {
    final sel = _filtroEstado == valor;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Padding(
      padding: const EdgeInsets.only(right: 6),
      child: FilterChip(
        label: Text(label),
        selected: sel,
        selectedColor: AppTheme.primary.withValues(alpha: 0.15),
        labelStyle: TextStyle(
          fontSize: 11,
          fontWeight: sel ? FontWeight.w800 : FontWeight.w500,
          color: sel ? AppTheme.primary : (isDark ? Colors.white70 : Colors.black87),
        ),
        onSelected: (_) {
          setState(() => _filtroEstado = valor);
          _pagina = 1;
          _cargarConsultas();
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
    final auth = Provider.of<AuthProvider>(context, listen: false);
    final puedeRegistrar = auth.hasPermission('Registrar_consultas_tecnicas');

    final titulo = widget.nombreObraFiltro != null
        ? 'RFI — ${widget.nombreObraFiltro}'
        : 'Consultas Técnicas (RFI)';

    return Scaffold(
      appBar: AppBar(
        title: Text(titulo, style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w800)),
      ),
      floatingActionButton: puedeRegistrar
          ? FloatingActionButton.extended(
              backgroundColor: AppTheme.primary,
              foregroundColor: Colors.white,
              onPressed: _abrirModalCrear,
              icon: const Icon(Icons.add_rounded),
              label: const Text('Nueva RFI', style: TextStyle(fontWeight: FontWeight.bold)),
            )
          : null,
      body: Column(
        children: [
          // Barra de búsqueda y filtros
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 6),
            child: TextField(
              controller: _searchCtrl,
              onChanged: _onSearchChanged,
              decoration: InputDecoration(
                hintText: 'Buscar por código, asunto, referencia...',
                prefixIcon: const Icon(Icons.search_rounded, size: 20),
                suffixIcon: _searchCtrl.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear_rounded, size: 18),
                        onPressed: () {
                          _searchCtrl.clear();
                          _cargarConsultas();
                        },
                      )
                    : null,
              ),
            ),
          ),

          // Pills de estado
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Row(
              children: [
                _buildFiltroPill('Todas ($_total)', ''),
                _buildFiltroPill('Abiertas', 'ABIERTA'),
                _buildFiltroPill('Asignadas', 'ASIGNADA'),
                _buildFiltroPill('Respondidas', 'RESPONDIDA'),
                _buildFiltroPill('Cerradas', 'CERRADA'),
              ],
            ),
          ),
          const SizedBox(height: 6),

          // Lista de Consultas
          Expanded(
            child: RefreshIndicator(
              onRefresh: _cargarConsultas,
              child: _cargando
                  ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
                  : _error != null
                      ? Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(_error!, style: const TextStyle(color: AppTheme.error)),
                              const SizedBox(height: 8),
                              ElevatedButton(onPressed: _cargarConsultas, child: const Text('Reintentar')),
                            ],
                          ),
                        )
                      : _consultas.isEmpty
                          ? Center(
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  const Icon(Icons.contact_support_outlined, size: 48, color: Color(0xFF94A3B8)),
                                  const SizedBox(height: 12),
                                  Text(
                                    'No hay consultas técnicas registradas',
                                    style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w700, color: titleColor),
                                  ),
                                  const SizedBox(height: 4),
                                  const Text(
                                    'Pulsa "Nueva RFI" para registrar una consulta.',
                                    style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
                                  ),
                                ],
                              ),
                            )
                          : ListView.builder(
                              padding: const EdgeInsets.fromLTRB(16, 6, 16, 80),
                              itemCount: _consultas.length,
                              itemBuilder: (context, index) {
                                final c = _consultas[index];
                                final id = c['id_consulta_tecnica'] as int;
                                final codigo = c['codigo']?.toString() ?? 'CT-000';
                                final asunto = c['asunto']?.toString() ?? '';
                                final ref = c['referencia_tecnica']?.toString();
                                final estado = c['estado']?.toString() ?? 'ABIERTA';
                                final resp = c['responsable_nombre']?.toString();
                                final obra = c['obra_nombre']?.toString();
                                final totalRespuestas = (c['total_respuestas'] as num?)?.toInt() ?? 0;
                                final fecha = (c['created_at']?.toString() ?? '').substring(0, 10);

                                return Container(
                                  margin: const EdgeInsets.only(bottom: 10),
                                  decoration: BoxDecoration(
                                    color: cardBg,
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(color: borderColor),
                                  ),
                                  child: Material(
                                    color: Colors.transparent,
                                    borderRadius: BorderRadius.circular(12),
                                    child: InkWell(
                                      borderRadius: BorderRadius.circular(12),
                                      onTap: () async {
                                        await Navigator.push(
                                          context,
                                          MaterialPageRoute(
                                            builder: (_) => ConsultaTecnicaDetalleScreen(idConsultaTecnica: id),
                                          ),
                                        );
                                        _cargarConsultas();
                                      },
                                      child: Padding(
                                        padding: const EdgeInsets.all(14),
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            // Código y estado
                                            Row(
                                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                              children: [
                                                Text(
                                                  codigo,
                                                  style: GoogleFonts.jetBrainsMono(
                                                    fontSize: 12,
                                                    fontWeight: FontWeight.w800,
                                                    color: AppTheme.primary,
                                                  ),
                                                ),
                                                Container(
                                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2.5),
                                                  decoration: BoxDecoration(
                                                    color: _colorEstado(estado).withValues(alpha: 0.15),
                                                    borderRadius: BorderRadius.circular(6),
                                                    border: Border.all(color: _colorEstado(estado).withValues(alpha: 0.3)),
                                                  ),
                                                  child: Text(
                                                    estado,
                                                    style: GoogleFonts.inter(
                                                      fontSize: 10,
                                                      fontWeight: FontWeight.w800,
                                                      color: _colorEstado(estado),
                                                    ),
                                                  ),
                                                ),
                                              ],
                                            ),
                                            const SizedBox(height: 6),

                                            // Asunto
                                            Text(
                                              asunto,
                                              style: GoogleFonts.inter(
                                                fontSize: 14,
                                                fontWeight: FontWeight.w700,
                                                color: titleColor,
                                              ),
                                              maxLines: 2,
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                            const SizedBox(height: 4),

                                            // Referencia técnica
                                            if (ref != null && ref.isNotEmpty)
                                              Text(
                                                '📍 $ref',
                                                style: const TextStyle(fontSize: 11, color: Color(0xFF64748B)),
                                                maxLines: 1,
                                                overflow: TextOverflow.ellipsis,
                                              ),

                                            const SizedBox(height: 10),
                                            const Divider(height: 1),
                                            const SizedBox(height: 8),

                                            // Responsable, respuestas y fecha
                                            Row(
                                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                              children: [
                                                Expanded(
                                                  child: Row(
                                                    children: [
                                                      const Icon(Icons.person_outline, size: 14, color: Color(0xFF94A3B8)),
                                                      const SizedBox(width: 4),
                                                      Expanded(
                                                        child: Text(
                                                          resp ?? 'Sin asignar',
                                                          style: TextStyle(
                                                            fontSize: 11.5,
                                                            color: resp != null ? titleColor : const Color(0xFF94A3B8),
                                                            fontStyle: resp == null ? FontStyle.italic : FontStyle.normal,
                                                          ),
                                                          overflow: TextOverflow.ellipsis,
                                                        ),
                                                      ),
                                                    ],
                                                  ),
                                                ),
                                                Row(
                                                  children: [
                                                    if (totalRespuestas > 0) ...[
                                                      Container(
                                                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                                        decoration: BoxDecoration(
                                                          color: const Color(0xFF0D9488).withValues(alpha: 0.15),
                                                          borderRadius: BorderRadius.circular(4),
                                                        ),
                                                        child: Row(
                                                          children: [
                                                            const Icon(Icons.chat_bubble_outline, size: 11, color: Color(0xFF0D9488)),
                                                            const SizedBox(width: 3),
                                                            Text(
                                                              totalRespuestas.toString(),
                                                              style: const TextStyle(fontSize: 10.5, fontWeight: FontWeight.bold, color: Color(0xFF0D9488)),
                                                            ),
                                                          ],
                                                        ),
                                                      ),
                                                      const SizedBox(width: 8),
                                                    ],
                                                    Text(fecha, style: const TextStyle(fontSize: 10.5, color: Color(0xFF94A3B8))),
                                                  ],
                                                ),
                                              ],
                                            ),
                                            if (widget.idObraFiltro == null && obra != null)
                                              Padding(
                                                padding: const EdgeInsets.only(top: 6),
                                                child: Text(
                                                  '🏗 $obra',
                                                  style: const TextStyle(fontSize: 10.5, color: Color(0xFF94A3B8)),
                                                ),
                                              ),
                                          ],
                                        ),
                                      ),
                                    ),
                                  ),
                                );
                              },
                            ),
            ),
          ),
        ],
      ),
    );
  }
}
