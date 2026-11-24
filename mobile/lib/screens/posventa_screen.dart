import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_provider.dart';
import '../services/posventa_service.dart';
import '../theme/app_theme.dart';

class PosventaScreen extends StatefulWidget {
  const PosventaScreen({super.key});

  @override
  State<PosventaScreen> createState() => _PosventaScreenState();
}

class _PosventaScreenState extends State<PosventaScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final PosventaService _service = PosventaService();

  List<Map<String, dynamic>> _solicitudes = [];
  List<Map<String, dynamic>> _garantias = [];
  bool _cargando = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _cargarDatos();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _cargarDatos() async {
    setState(() => _cargando = true);
    try {
      final s = await _service.listarSolicitudes();
      final g = await _service.listarGarantias();
      if (mounted) {
        setState(() {
          _solicitudes = s;
          _garantias = g;
          _cargando = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _cargando = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  void _abrirModalNuevoTicket([int? idUnidadPreseleccionada]) {
    final titleCtrl = TextEditingController();
    final descCtrl = TextEditingController();
    final unidadCtrl = TextEditingController(text: idUnidadPreseleccionada?.toString() ?? '1');

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (ctx) {
        return Padding(
          padding: EdgeInsets.only(
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 20,
            top: 20,
            left: 20,
            right: 20,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'Nuevo Reclamo de Posventa (HU163)',
                style: Theme.of(ctx).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: unidadCtrl,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'ID de la Unidad Inmobiliaria',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.home_work),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: titleCtrl,
                decoration: const InputDecoration(
                  labelText: 'Título del Defecto / Problema',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.report_problem),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: descCtrl,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Descripción detallada',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryOrange,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                icon: const Icon(Icons.send),
                label: const Text('Enviar Solicitud', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                onPressed: () async {
                  if (titleCtrl.text.trim().isEmpty || descCtrl.text.trim().isEmpty) {
                    ScaffoldMessenger.of(ctx).showSnackBar(
                      const SnackBar(content: Text('Complete todos los campos')),
                    );
                    return;
                  }
                  Navigator.pop(ctx);
                  try {
                    final res = await _service.registrarSolicitud(
                      idUnidad: int.tryParse(unidadCtrl.text.trim()) ?? 1,
                      titulo: titleCtrl.text.trim(),
                      descripcionDefecto: descCtrl.text.trim(),
                    );
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text('Ticket ${res["codigo_ticket"]} registrado exitosamente'),
                          backgroundColor: Colors.green,
                        ),
                      );
                      _cargarDatos();
                    }
                  } catch (e) {
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
                      );
                    }
                  }
                },
              ),
            ],
          ),
        );
      },
    );
  }

  void _verDetalleTimeline(Map<String, dynamic> item) async {
    final id = item['id_solicitud'] as int;
    try {
      final det = await _service.obtenerDetalle(id);
      if (!mounted) return;

      final auth = Provider.of<AuthProvider>(context, listen: false);
      final rol = auth.rol.toUpperCase();
      final esSupervisor = rol.contains('SUPERVISOR') || rol.contains('JEFE');

      showModalBottomSheet(
        context: context,
        isScrollControlled: true,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
        builder: (ctx) {
          final timeline = (det['linea_tiempo'] as List?) ?? [];
          return DraggableScrollableSheet(
            initialChildSize: 0.7,
            minChildSize: 0.5,
            maxChildSize: 0.95,
            expand: false,
            builder: (_, scrollCtrl) {
              return Padding(
                padding: const EdgeInsets.all(20),
                child: ListView(
                  controller: scrollCtrl,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          det['codigo_ticket'] ?? '',
                          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.primaryOrange),
                        ),
                        Chip(
                          label: Text(det['estado'] ?? '', style: const TextStyle(color: Colors.white, fontSize: 11)),
                          backgroundColor: _colorEstado(det['estado']),
                        )
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(det['titulo'] ?? '', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    Text(det['descripcion_defecto'] ?? '', style: TextStyle(color: Colors.grey[700])),
                    const SizedBox(height: 16),
                    const Divider(),
                    const Text('Línea de Tiempo (HU167)', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 12),
                    if (timeline.isEmpty)
                      const Text('Sin eventos registrados', style: TextStyle(color: Colors.grey))
                    else
                      ...timeline.map((e) {
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(Icons.circle, size: 10, color: AppTheme.primaryOrange),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      (e['tipo_evento'] as String).replaceAll('_', ' '),
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                                    ),
                                    Text(e['detalle_acciones'] ?? '', style: const TextStyle(fontSize: 12)),
                                    if (e['materiales_utilizados'] != null)
                                      Text('Materiales: ${e['materiales_utilizados']}', style: TextStyle(fontSize: 11, color: Colors.blue[800])),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        );
                      }),
                    if (esSupervisor && det['estado'] != 'CERRADA') ...[
                      const SizedBox(height: 16),
                      ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.indigo, foregroundColor: Colors.white),
                        icon: const Icon(Icons.build),
                        label: const Text('Registrar Atención Técnica (HU166)'),
                        onPressed: () {
                          Navigator.pop(ctx);
                          _abrirModalAtencionSupervisor(det);
                        },
                      ),
                    ]
                  ],
                ),
              );
            },
          );
        },
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    }
  }

  void _abrirModalAtencionSupervisor(Map<String, dynamic> det) {
    final accionesCtrl = TextEditingController();
    final matCtrl = TextEditingController();
    String estadoSeleccionado = 'EN_ATENCION';

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                bottom: MediaQuery.of(ctx).viewInsets.bottom + 20,
                top: 20,
                left: 20,
                right: 20,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    'Atención Técnica: ${det['codigo_ticket']}',
                    style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    value: estadoSeleccionado,
                    decoration: const InputDecoration(labelText: 'Nuevo Estado', border: OutlineInputBorder()),
                    items: const [
                      DropdownMenuItem(value: 'EN_ATENCION', child: Text('En Atención')),
                      DropdownMenuItem(value: 'RESUELTA', child: Text('Resuelta / Concluida')),
                      DropdownMenuItem(value: 'CERRADA', child: Text('Cerrada')),
                    ],
                    onChanged: (v) => setModalState(() => estadoSeleccionado = v!),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: accionesCtrl,
                    maxLines: 3,
                    decoration: const InputDecoration(
                      labelText: 'Acciones realizadas / Bitácora',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: matCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Materiales e Insumos utilizados',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white),
                    onPressed: () async {
                      if (accionesCtrl.text.trim().isEmpty) return;
                      Navigator.pop(ctx);
                      try {
                        await _service.atenderSolicitud(
                          idSolicitud: det['id_solicitud'],
                          nuevoEstado: estadoSeleccionado,
                          accionesRealizadas: accionesCtrl.text.trim(),
                          materialesUtilizados: matCtrl.text.trim(),
                        );
                        _cargarDatos();
                      } catch (e) {
                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
                      }
                    },
                    child: const Text('Guardar Atención'),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  Color _colorEstado(String? estado) {
    switch (estado) {
      case 'PENDIENTE':
        return Colors.orange[800]!;
      case 'CLASIFICADA':
        return Colors.indigo[600]!;
      case 'ASIGNADA':
        return Colors.blue[700]!;
      case 'EN_ATENCION':
        return Colors.pink[700]!;
      case 'RESUELTA':
        return Colors.green[700]!;
      case 'CERRADA':
        return Colors.grey[700]!;
      default:
        return Colors.grey[600]!;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Garantías y Posventa (CU33)'),
        backgroundColor: AppTheme.navyDark,
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppTheme.primaryOrange,
          tabs: [
            Tab(text: 'Solicitudes (${_solicitudes.length})'),
            Tab(text: 'Garantías (${_garantias.length})'),
          ],
        ),
      ),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                // TAB 1: Solicitudes
                _solicitudes.isEmpty
                    ? const Center(child: Text('No hay solicitudes registradas'))
                    : RefreshIndicator(
                        onRefresh: _cargarDatos,
                        child: ListView.builder(
                          padding: const EdgeInsets.all(12),
                          itemCount: _solicitudes.length,
                          itemBuilder: (ctx, i) {
                            final s = _solicitudes[i];
                            return Card(
                              elevation: 2,
                              margin: const EdgeInsets.only(bottom: 10),
                              child: ListTile(
                                leading: CircleAvatar(
                                  backgroundColor: _colorEstado(s['estado']),
                                  child: const Icon(Icons.handyman, color: Colors.white, size: 20),
                                ),
                                title: Text(s['titulo'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold)),
                                subtitle: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('${s['codigo_ticket']} • ${s['nombre_unidad']}'),
                                    Text('Estado: ${s['estado']} • Prioridad: ${s['prioridad']}'),
                                  ],
                                ),
                                trailing: const Icon(Icons.chevron_right),
                                onTap: () => _verDetalleTimeline(s),
                              ),
                            );
                          },
                        ),
                      ),

                // TAB 2: Garantías
                _garantias.isEmpty
                    ? const Center(child: Text('No hay garantías inmobiliarias registradas'))
                    : RefreshIndicator(
                        onRefresh: _cargarDatos,
                        child: ListView.builder(
                          padding: const EdgeInsets.all(12),
                          itemCount: _garantias.length,
                          itemBuilder: (ctx, i) {
                            final g = _garantias[i];
                            final esVigente = g['estado'] == 'VIGENTE';
                            return Card(
                              elevation: 2,
                              margin: const EdgeInsets.only(bottom: 10),
                              child: Padding(
                                padding: const EdgeInsets.all(14),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                      children: [
                                        Text(g['nombre_unidad'] ?? '', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                                        Chip(
                                          label: Text(g['estado'] ?? '', style: const TextStyle(color: Colors.white, fontSize: 11)),
                                          backgroundColor: esVigente ? Colors.green[700] : Colors.red[700],
                                        ),
                                      ],
                                    ),
                                    Text('Tipo: ${g['tipo_garantia']}', style: const TextStyle(color: AppTheme.primaryOrange, fontWeight: FontWeight.bold)),
                                    const SizedBox(height: 4),
                                    Text(g['descripcion_cobertura'] ?? '', style: TextStyle(color: Colors.grey[800])),
                                    const SizedBox(height: 6),
                                    Text('Vigencia: ${g['fecha_inicio']} al ${g['fecha_fin']}', style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                                    const SizedBox(height: 8),
                                    Align(
                                      alignment: Alignment.centerRight,
                                      child: TextButton.icon(
                                        icon: const Icon(Icons.report, size: 18),
                                        label: const Text('Reportar Defecto'),
                                        onPressed: () => _abrirModalNuevoTicket(g['id_unidad']),
                                      ),
                                    )
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                      ),
              ],
            ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: AppTheme.primaryOrange,
        onPressed: () => _abrirModalNuevoTicket(),
        child: const Icon(Icons.add, color: Colors.white),
      ),
    );
  }
}
