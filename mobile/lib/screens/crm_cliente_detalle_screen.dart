import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../services/crm_service.dart';
import '../theme/app_theme.dart';
import '../widgets/ev_widgets.dart';

class CrmClienteDetalleScreen extends StatefulWidget {
  final int idCliente;
  final String nombreCompleto;
  final String tipoCliente;

  const CrmClienteDetalleScreen({
    super.key,
    required this.idCliente,
    required this.nombreCompleto,
    required this.tipoCliente,
  });

  @override
  State<CrmClienteDetalleScreen> createState() => _CrmClienteDetalleScreenState();
}

class _CrmClienteDetalleScreenState extends State<CrmClienteDetalleScreen> {
  final CrmService _crmService = CrmService();
  late Future<Map<String, dynamic>> _futureDetalle;

  final List<String> _pipelineEtapas = [
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
    _cargarDetalle();
  }

  void _cargarDetalle() {
    _futureDetalle = _crmService.obtenerDetalleCliente(widget.idCliente);
  }

  Future<void> _refrescar() async {
    setState(() {
      _cargarDetalle();
    });
    await _futureDetalle;
  }

  Color _colorEtapa(String etapa, bool isDark) {
    switch (etapa.toUpperCase()) {
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
      default:
        return isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);
    }
  }

  IconData _iconoInteraccion(String tipo) {
    switch (tipo.toUpperCase()) {
      case 'LLAMADA':
        return Icons.phone_in_talk_rounded;
      case 'MENSAJE':
        return Icons.chat_rounded;
      case 'REUNION':
      case 'REUNIÓN':
        return Icons.groups_rounded;
      case 'VISITA':
      case 'VISITA A OBRA':
        return Icons.location_city_rounded;
      case 'CONSULTA':
        return Icons.help_outline_rounded;
      case 'SEGUIMIENTO':
        return Icons.timeline_rounded;
      default:
        return Icons.notes_rounded;
    }
  }

  void _mostrarModalAvanzarEtapa(String estadoActual) {
    String etapaSeleccionada = estadoActual;
    final notaCtrl = TextEditingController();
    bool guardando = false;

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
                      'Avanzar Etapa Comercial',
                      style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w800, color: titleColor),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'Seleccione la nueva fase en el pipeline de ventas:',
                      style: GoogleFonts.inter(fontSize: 12, color: const Color(0xFF94A3B8)),
                    ),
                    const SizedBox(height: 14),

                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: _pipelineEtapas.map((etapa) {
                        final sel = etapaSeleccionada == etapa;
                        final color = _colorEtapa(etapa, isDark);
                        return ChoiceChip(
                          label: Text(etapa.replaceAll('_', ' ')),
                          selected: sel,
                          selectedColor: color,
                          labelStyle: TextStyle(
                            color: sel ? Colors.white : (isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B)),
                            fontWeight: FontWeight.w700,
                            fontSize: 11.5,
                          ),
                          onSelected: (selected) {
                            if (selected) {
                              setModalState(() => etapaSeleccionada = etapa);
                            }
                          },
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 14),

                    TextField(
                      controller: notaCtrl,
                      maxLines: 2,
                      decoration: const InputDecoration(
                        labelText: 'Nota de seguimiento / Justificación',
                        hintText: 'Ej: El cliente solicitó propuesta formal para el Dpto 301',
                      ),
                    ),
                    const SizedBox(height: 18),

                    ObratecPrimaryButton(
                      label: 'Confirmar Avance',
                      loading: guardando,
                      onPressed: () async {
                        setModalState(() => guardando = true);
                        try {
                          await _crmService.avanzarEtapaComercial(
                            idCliente: widget.idCliente,
                            nuevoEstado: etapaSeleccionada,
                            nota: notaCtrl.text.trim(),
                          );

                          if (!ctx.mounted) return;
                          Navigator.pop(ctx);
                          _refrescar();

                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                              content: Text('Etapa comercial actualizada exitosamente.'),
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

  void _mostrarModalNuevaInteraccion() {
    String tipoSeleccionado = 'LLAMADA';
    final tiposDisponibles = [
      'LLAMADA',
      'MENSAJE',
      'REUNION',
      'VISITA',
      'CONSULTA',
      'SEGUIMIENTO',
      'OBSERVACION',
    ];
    final obsCtrl = TextEditingController();
    bool guardando = false;

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
                      'Registrar Interacción Comercial',
                      style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w800, color: titleColor),
                    ),
                    const SizedBox(height: 14),

                    DropdownButtonFormField<String>(
                      initialValue: tipoSeleccionado,
                      decoration: const InputDecoration(labelText: 'Tipo de Interacción'),
                      items: tiposDisponibles
                          .map((t) => DropdownMenuItem(value: t, child: Text(t.replaceAll('_', ' '))))
                          .toList(),
                      onChanged: (v) => setModalState(() => tipoSeleccionado = v ?? 'LLAMADA'),
                    ),
                    const SizedBox(height: 14),

                    TextField(
                      controller: obsCtrl,
                      maxLines: 3,
                      decoration: const InputDecoration(
                        labelText: 'Minuta / Observaciones del Contacto *',
                        hintText: 'Detalles acordados, preguntas del cliente o compromisos asumidos',
                      ),
                    ),
                    const SizedBox(height: 18),

                    ObratecPrimaryButton(
                      label: 'Guardar Interacción',
                      loading: guardando,
                      onPressed: () async {
                        final obs = obsCtrl.text.trim();
                        if (obs.isEmpty) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Por favor ingrese las observaciones de la interacción.')),
                          );
                          return;
                        }

                        setModalState(() => guardando = true);
                        try {
                          await _crmService.registrarInteraccion(
                            idCliente: widget.idCliente,
                            tipoInteraccion: tipoSeleccionado,
                            observaciones: obs,
                          );

                          if (!ctx.mounted) return;
                          Navigator.pop(ctx);
                          _refrescar();

                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                              content: Text('Interacción registrada exitosamente.'),
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

  void _mostrarModalAsociarUnidad() async {
    bool cargando = true;
    List<Map<String, dynamic>> unidadesDisponibles = [];
    int? idUnidadSeleccionada;
    String estadoAsociacion = 'INTERES';
    final precioCtrl = TextEditingController();
    final obsCtrl = TextEditingController();

    try {
      unidadesDisponibles = await _crmService.listarUnidadesDisponibles();
      if (unidadesDisponibles.isNotEmpty) {
        idUnidadSeleccionada = int.tryParse(unidadesDisponibles.first['id_unidad']?.toString() ?? '');
      }
    } catch (_) {}
    cargando = false;

    if (!mounted) return;
    bool guardando = false;

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
                      'Vincular Unidad Inmobiliaria',
                      style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w800, color: titleColor),
                    ),
                    const SizedBox(height: 14),

                    if (cargando)
                      const Center(child: CircularProgressIndicator(color: AppTheme.primary))
                    else if (unidadesDisponibles.isEmpty)
                      const Padding(
                        padding: EdgeInsets.symmetric(vertical: 12.0),
                        child: Text('No hay unidades inmobiliarias disponibles para asociar.'),
                      )
                    else
                      DropdownButtonFormField<int>(
                        initialValue: idUnidadSeleccionada,
                        isExpanded: true,
                        decoration: const InputDecoration(labelText: 'Unidad Disponible *'),
                        items: unidadesDisponibles.map((u) {
                          final id = int.parse(u['id_unidad'].toString());
                          final cod = u['codigo'] ?? u['nombre'] ?? 'Unidad';
                          final proyecto = u['proyecto_nombre'] ?? 'Obra';
                          final tipo = u['tipo_unidad'] ?? u['tipo'] ?? 'DPTO';
                          return DropdownMenuItem(
                            value: id,
                            child: Text('$cod ($tipo) - $proyecto', style: const TextStyle(fontSize: 12)),
                          );
                        }).toList(),
                        onChanged: (v) => setModalState(() => idUnidadSeleccionada = v),
                      ),
                    const SizedBox(height: 12),

                    DropdownButtonFormField<String>(
                      initialValue: estadoAsociacion,
                      decoration: const InputDecoration(labelText: 'Tipo de Vinculación *'),
                      items: const [
                        DropdownMenuItem(value: 'INTERES', child: Text('Interés / Cotización')),
                        DropdownMenuItem(value: 'RESERVA', child: Text('Reserva')),
                        DropdownMenuItem(value: 'VENTA', child: Text('Venta Concluida')),
                      ],
                      onChanged: (v) => setModalState(() => estadoAsociacion = v ?? 'INTERES'),
                    ),
                    const SizedBox(height: 12),

                    TextField(
                      controller: precioCtrl,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      decoration: const InputDecoration(
                        labelText: 'Precio Pactado (BOB)',
                        hintText: 'Ej: 380000',
                      ),
                    ),
                    const SizedBox(height: 12),

                    TextField(
                      controller: obsCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Observaciones de la negociación',
                        hintText: 'Ej: Incluye parqueo y baulera',
                      ),
                    ),
                    const SizedBox(height: 18),

                    ObratecPrimaryButton(
                      label: 'Vincular Unidad',
                      loading: guardando,
                      onPressed: idUnidadSeleccionada == null ? null : () async {
                        if (idUnidadSeleccionada == null) return;
                        setModalState(() => guardando = true);
                        try {
                          await _crmService.asociarUnidad(
                            idCliente: widget.idCliente,
                            idUnidad: idUnidadSeleccionada!,
                            estadoAsociacion: estadoAsociacion,
                            precioPactado: double.tryParse(precioCtrl.text.trim()),
                            observaciones: obsCtrl.text.trim(),
                          );

                          if (!ctx.mounted) return;
                          Navigator.pop(ctx);
                          _refrescar();

                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                              content: Text('Unidad inmobiliaria vinculada exitosamente.'),
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
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
    final subColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);

    return Scaffold(
      appBar: AppBar(
        title: Text(
          'Ficha Comercial',
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
        icon: const Icon(Icons.add_comment_rounded, color: Colors.white, size: 20),
        label: Text('Nueva Interacción', style: GoogleFonts.inter(fontWeight: FontWeight.w700, color: Colors.white)),
        onPressed: _mostrarModalNuevaInteraccion,
      ),
      body: RefreshIndicator(
        color: AppTheme.primary,
        onRefresh: _refrescar,
        child: FutureBuilder<Map<String, dynamic>>(
          future: _futureDetalle,
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

            final data = snapshot.data ?? {};
            final cliente = (data['cliente'] is Map) ? data['cliente'] as Map : data;
            final rawInteracciones = data['interacciones'];
            final List<dynamic> interacciones = (rawInteracciones is List) ? rawInteracciones : [];
            final rawUnidades = data['unidades_asociadas'];
            final List<dynamic> unidades = (rawUnidades is List) ? rawUnidades : [];

            final estado = (cliente['estado'] ?? 'NUEVO').toString().toUpperCase();
            final colorEst = _colorEtapa(estado, isDark);
            final tel = cliente['telefono']?.toString() ?? '-';
            final email = cliente['email']?.toString() ?? '-';
            final ci = cliente['ci']?.toString() ?? '-';
            final origen = cliente['origen']?.toString() ?? 'Visita a Obra';
            final asesor = cliente['asesor_nombre']?.toString() ?? 'Sin asignar';
            final presupuesto = cliente['presupuesto_estimado'] != null
                ? '${cliente['presupuesto_estimado']} BOB'
                : 'No especificado';
            final notas = cliente['notas']?.toString() ?? '';

            final int etapaIndex = _pipelineEtapas.indexOf(estado);

            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 80),
              children: [
                // 1. CABECERA DE CONTACTO COMERCIAL
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: cardBg,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: borderColor),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          CircleAvatar(
                            radius: 24,
                            backgroundColor: colorEst.withValues(alpha: 0.15),
                            child: Text(
                              widget.nombreCompleto.isNotEmpty ? widget.nombreCompleto[0].toUpperCase() : 'C',
                              style: GoogleFonts.inter(fontSize: 20, fontWeight: FontWeight.w900, color: colorEst),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(widget.nombreCompleto,
                                    style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w900, color: titleColor)),
                                const SizedBox(height: 2),
                                Text('${widget.tipoCliente} · CI: $ci',
                                    style: GoogleFonts.inter(fontSize: 12, color: subColor, fontWeight: FontWeight.w500)),
                              ],
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: colorEst.withValues(alpha: isDark ? 0.2 : 0.1),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              estado.replaceAll('_', ' '),
                              style: GoogleFonts.inter(fontSize: 10, fontWeight: FontWeight.w800, color: colorEst),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      Divider(height: 1, color: borderColor),
                      const SizedBox(height: 12),

                      Row(
                        children: [
                          Expanded(child: _buildDato('Teléfono', tel, subColor, titleColor)),
                          Expanded(child: _buildDato('Correo', email, subColor, titleColor)),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          Expanded(child: _buildDato('Presupuesto Estimado', presupuesto, subColor, isDark ? const Color(0xFF34D399) : AppTheme.success)),
                          Expanded(child: _buildDato('Origen de Contacto', origen, subColor, titleColor)),
                        ],
                      ),
                      const SizedBox(height: 10),
                      _buildDato('Asesor Comercial', asesor, subColor, titleColor),

                      if (notas.isNotEmpty) ...[
                        const SizedBox(height: 10),
                        Text('Notas:', style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w700, color: subColor)),
                        const SizedBox(height: 2),
                        Text(notas, style: GoogleFonts.inter(fontSize: 12.5, color: titleColor)),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 14),

                // 2. PIPELINE COMERCIAL INTERACTIVO (STEPPER)
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: cardBg,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: borderColor),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('PIPELINE DE VENTAS',
                              style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w900, color: AppTheme.primary, letterSpacing: 0.6)),
                          InkWell(
                            onTap: () => _mostrarModalAvanzarEtapa(estado),
                            child: Row(
                              children: [
                                const Icon(Icons.touch_app_rounded, size: 14, color: AppTheme.primary),
                                const SizedBox(width: 4),
                                Text('Avanzar Etapa', style: GoogleFonts.inter(fontSize: 11.5, fontWeight: FontWeight.w700, color: AppTheme.primary)),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),

                      // Barra visual de etapas
                      Row(
                        children: _pipelineEtapas.asMap().entries.map((entry) {
                          final idx = entry.key;
                          final e = entry.value;
                          final alcanzado = etapaIndex >= 0 && idx <= etapaIndex;
                          final esActual = idx == etapaIndex;
                          final color = _colorEtapa(e, isDark);

                          return Expanded(
                            child: Container(
                              margin: const EdgeInsets.symmetric(horizontal: 2),
                              height: 6,
                              decoration: BoxDecoration(
                                color: alcanzado ? color : borderColor,
                                borderRadius: BorderRadius.circular(3),
                                border: esActual ? Border.all(color: Colors.white, width: 1.5) : null,
                              ),
                            ),
                          );
                        }).toList(),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Fase actual: ${estado.replaceAll('_', ' ')}',
                        style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w700, color: colorEst),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),

                // 3. UNIDADES INMOBILIARIAS ASOCIADAS
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: cardBg,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: borderColor),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('UNIDADES INMOBILIARIAS ASOCIADAS',
                              style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w900, color: AppTheme.primary, letterSpacing: 0.6)),
                          IconButton(
                            icon: const Icon(Icons.add_circle_outline_rounded, size: 20, color: AppTheme.primary),
                            tooltip: 'Vincular Unidad',
                            onPressed: _mostrarModalAsociarUnidad,
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),

                      if (unidades.isEmpty)
                        const Padding(
                          padding: EdgeInsets.symmetric(vertical: 8.0),
                          child: Text('No hay unidades vinculadas (interés, reserva o venta) con este cliente.',
                              style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8))),
                        )
                      else
                        ...unidades.map((u) {
                          final cod = u['unidad_codigo'] ?? u['nombre'] ?? 'Unidad';
                          final proyecto = u['proyecto_nombre'] ?? 'Obra';
                          final estadoAsoc = (u['estado_asociacion'] ?? 'INTERES').toString().toUpperCase();
                          final precioPactado = u['precio_pactado'] != null ? '${u['precio_pactado']} BOB' : '-';

                          return Container(
                            margin: const EdgeInsets.only(bottom: 8),
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                            decoration: BoxDecoration(
                              color: isDark ? const Color(0xFF0F172A) : const Color(0xFFF8FAFC),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: borderColor),
                            ),
                            child: Row(
                              children: [
                                const Icon(Icons.meeting_room_rounded, color: AppTheme.primary, size: 20),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text('$cod · $proyecto',
                                          style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w700, color: titleColor)),
                                      Text('Monto pactado: $precioPactado',
                                          style: GoogleFonts.inter(fontSize: 11.5, color: subColor)),
                                    ],
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: (estadoAsoc == 'VENTA' ? AppTheme.success : AppTheme.primary).withValues(alpha: 0.15),
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: Text(
                                    estadoAsoc,
                                    style: TextStyle(
                                      fontSize: 9.5,
                                      fontWeight: FontWeight.w800,
                                      color: estadoAsoc == 'VENTA' ? AppTheme.success : AppTheme.primary,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          );
                        }),
                    ],
                  ),
                ),
                const SizedBox(height: 14),

                // 4. HISTORIAL DE INTERACCIONES Y SEGUIMIENTO
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: cardBg,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: borderColor),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('HISTORIAL DE INTERACCIONES COMERCIALES',
                          style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w900, color: AppTheme.primary, letterSpacing: 0.6)),
                      const SizedBox(height: 12),

                      if (interacciones.isEmpty)
                        const Padding(
                          padding: EdgeInsets.symmetric(vertical: 8.0),
                          child: Text('No hay interacciones comerciales registradas en la bitácora.',
                              style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8))),
                        )
                      else
                        ...interacciones.map((i) {
                          final tipo = (i['tipo_interaccion'] ?? 'NOTA').toString().toUpperCase();
                          final obs = i['observaciones']?.toString() ?? '';
                          final fecha = i['fecha_contacto']?.toString() ?? i['created_at']?.toString() ?? '';
                          final usuario = i['usuario_nombre']?.toString() ?? '';

                          return Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: isDark ? const Color(0xFF0F172A) : const Color(0xFFF8FAFC),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: borderColor),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Icon(_iconoInteraccion(tipo), size: 16, color: AppTheme.primary),
                                    const SizedBox(width: 6),
                                    Text(
                                      tipo.replaceAll('_', ' '),
                                      style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w800, color: titleColor),
                                    ),
                                    const Spacer(),
                                    if (fecha.isNotEmpty)
                                      Text(
                                        fecha.length >= 10 ? fecha.substring(0, 10) : fecha,
                                        style: GoogleFonts.inter(fontSize: 10.5, color: subColor),
                                      ),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Text(obs, style: GoogleFonts.inter(fontSize: 12.5, color: titleColor, height: 1.35)),
                                if (usuario.isNotEmpty) ...[
                                  const SizedBox(height: 4),
                                  Text('Registrado por: $usuario', style: GoogleFonts.inter(fontSize: 10.5, color: subColor)),
                                ],
                              ],
                            ),
                          );
                        }),
                    ],
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildDato(String label, String valor, Color subColor, Color titleColor) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: GoogleFonts.inter(fontSize: 11, color: subColor, fontWeight: FontWeight.w500)),
        const SizedBox(height: 2),
        Text(valor, style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w700, color: titleColor), maxLines: 1, overflow: TextOverflow.ellipsis),
      ],
    );
  }
}
