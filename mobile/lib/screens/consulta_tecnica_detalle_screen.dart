import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../services/auth_provider.dart';
import '../services/consulta_tecnica_service.dart';
import '../theme/app_theme.dart';

class ConsultaTecnicaDetalleScreen extends StatefulWidget {
  final int idConsultaTecnica;

  const ConsultaTecnicaDetalleScreen({super.key, required this.idConsultaTecnica});

  @override
  State<ConsultaTecnicaDetalleScreen> createState() => _ConsultaTecnicaDetalleScreenState();
}

class _ConsultaTecnicaDetalleScreenState extends State<ConsultaTecnicaDetalleScreen> {
  final ConsultaTecnicaService _service = ConsultaTecnicaService();
  final TextEditingController _respuestaCtrl = TextEditingController();

  Map<String, dynamic>? _consulta;
  bool _cargando = true;
  bool _enviando = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _cargarDetalle();
  }

  @override
  void dispose() {
    _respuestaCtrl.dispose();
    super.dispose();
  }

  Future<void> _cargarDetalle() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final data = await _service.obtenerDetalle(widget.idConsultaTecnica);
      if (!mounted) return;
      setState(() {
        _consulta = data;
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

  Future<void> _enviarRespuesta() async {
    final texto = _respuestaCtrl.text.trim();
    if (texto.length < 3) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('La respuesta debe tener al menos 3 caracteres.')),
      );
      return;
    }

    setState(() => _enviando = true);
    try {
      await _service.responder(
        idConsultaTecnica: widget.idConsultaTecnica,
        respuesta: texto,
      );
      _respuestaCtrl.clear();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Aclaración técnica registrada correctamente.')),
      );
      await _cargarDetalle();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceAll('Exception: ', ''))),
      );
    } finally {
      if (mounted) setState(() => _enviando = false);
    }
  }

  void _mostrarModalAsignar() async {
    if (_consulta == null) return;
    final idObra = _consulta!['id_obra'] as int;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        int? idSeleccionado = _consulta!['asignado_a'];
        final motivoCtrl = TextEditingController();
        bool guardando = false;

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
              child: FutureBuilder<List<Map<String, dynamic>>>(
                future: _service.obtenerUsuariosAsignables(idObra),
                builder: (context, snapshot) {
                  final usuarios = snapshot.data ?? [];

                  return Column(
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
                        'Asignar Responsable Técnico',
                        style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w800, color: titleColor),
                      ),
                      const SizedBox(height: 14),
                      if (snapshot.connectionState == ConnectionState.waiting)
                        const Center(child: CircularProgressIndicator())
                      else
                        DropdownButtonFormField<int>(
                          initialValue: idSeleccionado,
                          decoration: const InputDecoration(labelText: 'Usuario Responsable *'),
                          items: usuarios.map((u) {
                            final id = u['id_usuario'] as int;
                            final nombre = u['nombre_completo'] ?? 'Usuario';
                            final rol = u['rol'] ?? '';
                            return DropdownMenuItem(
                              value: id,
                              child: Text('$nombre ($rol)', style: const TextStyle(fontSize: 12)),
                            );
                          }).toList(),
                          onChanged: (val) => setModalState(() => idSeleccionado = val),
                        ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: motivoCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Motivo u observación de asignación',
                          hintText: 'Ej. Especialista en cálculo estructural',
                        ),
                      ),
                      const SizedBox(height: 20),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF6366F1),
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 14),
                          ),
                          onPressed: (guardando || idSeleccionado == null)
                              ? null
                              : () async {
                                  setModalState(() => guardando = true);
                                  try {
                                    await _service.asignarResponsable(
                                      idConsultaTecnica: widget.idConsultaTecnica,
                                      idResponsable: idSeleccionado!,
                                      motivo: motivoCtrl.text,
                                    );
                                    if (ctx.mounted) Navigator.pop(ctx);
                                    _cargarDetalle();
                                  } catch (err) {
                                    setModalState(() => guardando = false);
                                    if (ctx.mounted) {
                                      ScaffoldMessenger.of(ctx).showSnackBar(
                                        SnackBar(content: Text(err.toString())),
                                      );
                                    }
                                  }
                                },
                          child: guardando
                              ? const SizedBox(height: 16, width: 16, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                              : const Text('Guardar Asignación', style: TextStyle(fontWeight: FontWeight.bold)),
                        ),
                      ),
                    ],
                  );
                },
              ),
            );
          },
        );
      },
    );
  }

  void _confirmarCierre() {
    final motivoCtrl = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Cerrar Consulta Técnica (RFI)'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '¿Desea cerrar esta consulta técnica? Quedará archivada y se registrará la fecha y usuario de cierre.',
              style: TextStyle(fontSize: 13),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: motivoCtrl,
              decoration: const InputDecoration(
                labelText: 'Motivo o conclusión de cierre',
                hintText: 'Ej. Solución técnica aceptada en obra',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error, foregroundColor: Colors.white),
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                await _service.cambiarEstado(
                  idConsultaTecnica: widget.idConsultaTecnica,
                  estado: 'CERRADA',
                  motivo: motivoCtrl.text,
                );
                _cargarDetalle();
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
                }
              }
            },
            child: const Text('Confirmar Cierre'),
          ),
        ],
      ),
    );
  }

  void _reabrirConsulta() async {
    try {
      final asignado = _consulta?['asignado_a'] != null;
      await _service.cambiarEstado(
        idConsultaTecnica: widget.idConsultaTecnica,
        estado: asignado ? 'ASIGNADA' : 'ABIERTA',
        motivo: 'Reapertura desde app móvil',
      );
      _cargarDetalle();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
    final auth = Provider.of<AuthProvider>(context, listen: false);

    final puedeAsignar = auth.hasPermission('Asignar_consultas_tecnicas');
    final puedeResponder = auth.hasPermission('Responder_consultas_tecnicas');
    final puedeCerrar = auth.hasPermission('Cerrar_consultas_tecnicas');

    if (_cargando) {
      return Scaffold(
        appBar: AppBar(title: const Text('Consulta Técnica')),
        body: const Center(child: CircularProgressIndicator(color: AppTheme.primary)),
      );
    }

    if (_error != null || _consulta == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Consulta Técnica')),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(_error ?? 'No encontrada', style: const TextStyle(color: AppTheme.error)),
              const SizedBox(height: 12),
              ElevatedButton(onPressed: _cargarDetalle, child: const Text('Reintentar')),
            ],
          ),
        ),
      );
    }

    final estado = (_consulta!['estado'] ?? 'ABIERTA').toString();
    final esCerrada = estado == 'CERRADA';
    final respuestas = List<Map<String, dynamic>>.from(_consulta!['respuestas'] ?? []);
    final historial = List<Map<String, dynamic>>.from(_consulta!['historial'] ?? []);

    return Scaffold(
      appBar: AppBar(
        title: Text(
          _consulta!['codigo'] ?? 'RFI',
          style: GoogleFonts.jetBrainsMono(fontSize: 16, fontWeight: FontWeight.w700),
        ),
        actions: [
          if (puedeCerrar && !esCerrada)
            IconButton(
              icon: const Icon(Icons.lock_outline_rounded, color: AppTheme.error),
              tooltip: 'Cerrar RFI',
              onPressed: _confirmarCierre,
            ),
          if (puedeCerrar && esCerrada)
            IconButton(
              icon: const Icon(Icons.lock_open_rounded, color: Color(0xFFF59E0B)),
              tooltip: 'Reabrir Consulta',
              onPressed: _reabrirConsulta,
            ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _cargarDetalle,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Cabecera de Estado y Código
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    _consulta!['asunto'] ?? '',
                    style: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w800, color: titleColor),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: _colorEstado(estado).withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: _colorEstado(estado).withValues(alpha: 0.4)),
                  ),
                  child: Text(
                    estado,
                    style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w800, color: _colorEstado(estado)),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),

            // Obra y creador
            Row(
              children: [
                const Icon(Icons.apartment_rounded, size: 14, color: AppTheme.primary),
                const SizedBox(width: 4),
                Text(
                  _consulta!['obra_nombre'] ?? 'Obra',
                  style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w600, color: titleColor),
                ),
                const SizedBox(width: 12),
                const Icon(Icons.person_outline, size: 14, color: Color(0xFF94A3B8)),
                const SizedBox(width: 4),
                Text(
                  _consulta!['creador_nombre'] ?? 'Usuario',
                  style: const TextStyle(fontSize: 11, color: Color(0xFF94A3B8)),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Referencia Técnica
            if (_consulta!['referencia_tecnica'] != null && _consulta!['referencia_tecnica'].toString().isNotEmpty)
              Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: AppTheme.primary.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppTheme.primary.withValues(alpha: 0.2)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.description_outlined, size: 16, color: AppTheme.primary),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Ref: ${_consulta!['referencia_tecnica']}',
                        style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.primary),
                      ),
                    ),
                  ],
                ),
              ),

            // Descripción Detallada
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: cardBg,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: borderColor),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'DESCRIPCIÓN DEL REQUERIMIENTO',
                    style: GoogleFonts.inter(fontSize: 10.5, fontWeight: FontWeight.w800, color: const Color(0xFF94A3B8)),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    _consulta!['descripcion'] ?? '',
                    style: GoogleFonts.inter(fontSize: 13, color: titleColor, height: 1.4),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // Tarjeta Responsable Asignado
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: cardBg,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: borderColor),
              ),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 18,
                    backgroundColor: const Color(0xFF6366F1).withValues(alpha: 0.15),
                    child: const Icon(Icons.person_rounded, size: 20, color: Color(0xFF6366F1)),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Responsable Asignado', style: TextStyle(fontSize: 10.5, color: Color(0xFF94A3B8))),
                        Text(
                          _consulta!['responsable_nombre'] ?? 'Sin asignar',
                          style: GoogleFonts.inter(
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: _consulta!['responsable_nombre'] != null ? titleColor : const Color(0xFF94A3B8),
                            fontStyle: _consulta!['responsable_nombre'] == null ? FontStyle.italic : FontStyle.normal,
                          ),
                        ),
                      ],
                    ),
                  ),
                  if (puedeAsignar && !esCerrada)
                    OutlinedButton(
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        minimumSize: Size.zero,
                      ),
                      onPressed: _mostrarModalAsignar,
                      child: Text(_consulta!['asignado_a'] != null ? 'Reasignar' : 'Asignar', style: const TextStyle(fontSize: 11)),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // SECCIÓN: ACLARACIONES TÉCNICAS (HU139)
            Text(
              'ACLARACIONES TÉCNICAS (${respuestas.length})',
              style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w900, color: AppTheme.primary, letterSpacing: 0.6),
            ),
            const SizedBox(height: 10),

            if (respuestas.isEmpty)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: cardBg,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: borderColor),
                ),
                child: const Center(
                  child: Text('No hay respuestas registradas aún.', style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8))),
                ),
              )
            else
              ...respuestas.map((r) {
                final esRespAsignado = r['es_responsable_asignado'] == true;
                return Container(
                  margin: const EdgeInsets.only(bottom: 10),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: cardBg,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: esRespAsignado ? const Color(0xFF0D9488) : borderColor, width: esRespAsignado ? 1.5 : 1),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              Text(r['autor_nombre'] ?? 'Usuario', style: GoogleFonts.inter(fontSize: 12.5, fontWeight: FontWeight.w700, color: titleColor)),
                              const SizedBox(width: 6),
                              if (esRespAsignado)
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFF0D9488).withValues(alpha: 0.15),
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: const Text('⭐ Responsable', style: TextStyle(fontSize: 9.5, fontWeight: FontWeight.bold, color: Color(0xFF0D9488))),
                                ),
                            ],
                          ),
                          Text(
                            (r['created_at']?.toString() ?? '').substring(0, 16).replaceAll('T', ' '),
                            style: const TextStyle(fontSize: 10, color: Color(0xFF94A3B8)),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(r['respuesta'] ?? '', style: GoogleFonts.inter(fontSize: 12.5, color: titleColor, height: 1.3)),
                    ],
                  ),
                );
              }),

            // Formulario para responder
            if (puedeResponder && !esCerrada) ...[
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: cardBg,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: borderColor),
                ),
                child: Column(
                  children: [
                    TextField(
                      controller: _respuestaCtrl,
                      maxLines: 3,
                      decoration: const InputDecoration(
                        hintText: 'Escriba una aclaración técnica o respuesta oficial...',
                        border: InputBorder.none,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Align(
                      alignment: Alignment.centerRight,
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF0D9488),
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                        ),
                        onPressed: _enviando ? null : _enviarRespuesta,
                        icon: _enviando
                            ? const SizedBox(height: 14, width: 14, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                            : const Icon(Icons.send_rounded, size: 16),
                        label: const Text('Publicar Respuesta', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 20),

            // SECCIÓN: HISTORIAL Y TRAZABILIDAD (HU140)
            Text(
              'HISTORIAL Y SEGUIMIENTO (${historial.length})',
              style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w900, color: AppTheme.primary, letterSpacing: 0.6),
            ),
            const SizedBox(height: 10),

            ...historial.map((h) {
              return Container(
                margin: const EdgeInsets.only(bottom: 6),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: isDark ? const Color(0xFF0F172A) : const Color(0xFFF8FAFC),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: borderColor),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(h['tipo_accion'] ?? 'ACCIÓN', style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w700, color: titleColor)),
                        Text(
                          (h['created_at']?.toString() ?? '').substring(0, 16).replaceAll('T', ' '),
                          style: const TextStyle(fontSize: 9.5, color: Color(0xFF94A3B8)),
                        ),
                      ],
                    ),
                    if (h['detalle'] != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 2),
                        child: Text(h['detalle'].toString(), style: const TextStyle(fontSize: 11, color: Color(0xFF64748B))),
                      ),
                  ],
                ),
              );
            }),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }
}
