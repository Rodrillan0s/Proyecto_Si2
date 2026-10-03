import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../services/auth_provider.dart';
import '../services/incidencia_service.dart';
import '../theme/app_theme.dart';
import '../widgets/incidencia_widgets.dart';
import 'incidencia_form_screen.dart';

/// Acciones de cambio de estado del flujo CU19. ABIERTA→ASIGNADA se hace al
/// asignar responsable (HU71). Iniciar/finalizar: solo el responsable (el
/// backend lo exige). Cerrar: permiso Cerrar_incidencias (HU74).
class _AccionEstado {
  final String estado;
  final String texto;
  final IconData icon;
  final String confirmacion;
  final bool peligro;

  const _AccionEstado(this.estado, this.texto, this.icon, this.confirmacion, {this.peligro = false});
}

const _iniciar = _AccionEstado(
  'EN_PROCESO',
  'Iniciar atención',
  Icons.play_arrow_rounded,
  'La incidencia pasará a EN PROCESO. El servidor registrará la fecha y hora de inicio de atención.',
);
const _finalizar = _AccionEstado(
  'PENDIENTE_VALIDACION',
  'Finalizar atención',
  Icons.task_alt_rounded,
  'La incidencia pasará a PENDIENTE VALIDACION. El servidor registrará la fecha y hora de fin de atención.',
);
const _aprobar = _AccionEstado('RESUELTA', 'Aprobar resolución', Icons.task_alt_rounded, 'La resolución quedará aprobada y la incidencia pasará a RESUELTA.');
const _rechazar = _AccionEstado('EN_PROCESO', 'Rechazar resolución', Icons.replay_rounded, 'El responsable continuará la atención en EN PROCESO.');
const _cerrar = _AccionEstado(
  'CERRADA',
  'Cerrar incidencia',
  Icons.lock_outline_rounded,
  'Verifica que la solución haya sido confirmada. Una incidencia cerrada ya no puede modificarse.',
  peligro: true,
);

const int _maxBytesEvidencia = 10 * 1024 * 1024; // límite del backend

class IncidenciaDetalleScreen extends StatefulWidget {
  final int idIncidencia;

  const IncidenciaDetalleScreen({super.key, required this.idIncidencia});

  @override
  State<IncidenciaDetalleScreen> createState() => _IncidenciaDetalleScreenState();
}

class _IncidenciaDetalleScreenState extends State<IncidenciaDetalleScreen> {
  final IncidenciaService _service = IncidenciaService();
  final ImagePicker _picker = ImagePicker();

  Map<String, dynamic>? _inc;
  List<Map<String, dynamic>> _seguimiento = [];
  List<Map<String, dynamic>> _evidencias = [];
  String? _errorSeguimiento;
  String? _errorEvidencias;
  final Map<int, Future<Uint8List>> _imagenes = {};

  int? _nroUsuario;
  bool _cargando = true;
  String? _error;
  bool _procesando = false;

  int get _id => widget.idIncidencia;
  String get _estado => (_inc?['estado'] ?? '').toString();

  @override
  void initState() {
    super.initState();
    _cargarTodo();
  }

  Future<void> _cargarTodo() async {
    setState(() {
      _cargando = _inc == null;
      _error = null;
    });
    _nroUsuario ??= await PermisosIncidencia.usuarioActual();
    try {
      final inc = await _service.obtener(_id);
      if (!mounted) return;
      setState(() {
        _inc = inc;
        _cargando = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _cargando = false;
        _error = e.toString();
      });
      return;
    }
    await Future.wait([_cargarSeguimiento(), _cargarEvidencias()]);
  }

  Future<void> _cargarSeguimiento() async {
    try {
      final lista = await _service.listarSeguimiento(_id);
      if (!mounted) return;
      setState(() {
        _seguimiento = lista;
        _errorSeguimiento = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _errorSeguimiento = e.toString());
    }
  }

  Future<void> _cargarEvidencias() async {
    try {
      final lista = await _service.listarEvidencias(_id);
      if (!mounted) return;
      setState(() {
        _evidencias = lista;
        _errorEvidencias = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _errorEvidencias = e.toString());
    }
  }

  // ── Reglas de visibilidad (permisos + estado + responsable) ────────────────
  bool _tiene(String permiso) => PermisosIncidencia.tiene(Provider.of<AuthProvider>(context, listen: false), permiso);
  bool get _puedeValidar => _estado == 'PENDIENTE_VALIDACION' && _tiene(PermisosIncidencia.modificar);
  bool get _abierta => _estado != 'CERRADA';
  bool get _esResponsable => _inc != null && PermisosIncidencia.esResponsable(_inc!, _nroUsuario);
  bool get _esRegistrador => _nroUsuario != null &&
      int.tryParse(_inc?['id_usuario_registro']?.toString() ?? '') == _nroUsuario;

  bool get _puedeEditar => _tiene(PermisosIncidencia.modificar) && _abierta;
  bool get _puedeAsignar => _tiene(PermisosIncidencia.asignar) && _abierta;
  bool get _puedeSeleccionarOt => _tiene(PermisosIncidencia.asignar) && _abierta;
  bool get _puedeComentar => (_tiene(PermisosIncidencia.modificar) || _esResponsable) && _abierta;
  bool get _puedeAdjuntar => (_tiene(PermisosIncidencia.modificar) || _esResponsable || _esRegistrador) && _abierta;

  _AccionEstado? get _accionEstado {
    if (_estado == 'ASIGNADA' && _esResponsable) return _iniciar;
    if (_estado == 'EN_PROCESO' && _esResponsable) return _finalizar;
    if (_estado == 'RESUELTA' && _tiene(PermisosIncidencia.cerrar)) return _cerrar;
    return null;
  }

  // ── Acciones ───────────────────────────────────────────────────────────────
  Future<void> _ejecutar(Future<Map<String, dynamic>> Function() accion, String exitoPorDefecto) async {
    if (_procesando) return;
    setState(() => _procesando = true);
    try {
      final res = await accion();
      if (!mounted) return;
      mostrarMensajeIncidencia(context, (res['message'] ?? exitoPorDefecto).toString());
      await _cargarTodo();
    } catch (e) {
      if (!mounted) return;
      mostrarMensajeIncidencia(context, e.toString(), error: true);
      // 409/404: el estado cambió o ya no es accesible → refrescar la vista.
      if (e is IncidenciaException && (e.statusCode == 409 || e.statusCode == 404)) _cargarTodo();
    } finally {
      if (mounted) setState(() => _procesando = false);
    }
  }

  Future<void> _confirmarCambioEstado(_AccionEstado accion) async {
    final observacion = await showDialog<String>(
      context: context,
      builder: (_) => _DialogoTexto(
        titulo: '${accion.texto}?',
        mensaje: accion.confirmacion,
        hint: 'Observación (opcional)',
        textoConfirmar: accion.texto,
        peligro: accion.peligro,
      ),
    );
    if (observacion == null) return; // cancelado
    await _ejecutar(
      () => _service.cambiarEstado(_id, accion.estado, observacion: observacion),
      'Estado actualizado exitosamente.',
    );
  }

  Future<void> _editar() async {
    final guardado = await Navigator.push<bool>(
      context,
      MaterialPageRoute(builder: (_) => IncidenciaFormScreen(incidencia: _inc)),
    );
    if (guardado == true && mounted) _cargarTodo();
  }

  Future<void> _asignarResponsable() async {
    final idSeleccionado = await showModalBottomSheet<int>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => _SelectorResponsable(service: _service, incidencia: _inc!),
    );
    if (idSeleccionado == null) return;
    await _ejecutar(() => _service.asignarResponsable(_id, idSeleccionado), 'Responsable asignado exitosamente.');
  }

  Future<void> _seleccionarOrdenes() async {
    final seleccion = await showModalBottomSheet<List<int>>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => _SelectorOrdenesTrabajo(service: _service, incidencia: _inc!),
    );
    if (seleccion == null) return;
    await _ejecutar(
      () => _service.actualizarOrdenesTrabajo(_id, seleccion),
      'Órdenes de trabajo afectadas actualizadas.',
    );
  }

  Future<void> _agregarSeguimiento() async {
    final observacion = await showDialog<String>(
      context: context,
      builder: (_) => const _DialogoTexto(
        titulo: 'Agregar seguimiento',
        hint: 'Describe el avance u observación...',
        textoConfirmar: 'Registrar',
        obligatorio: true,
      ),
    );
    if (observacion == null || observacion.isEmpty) return;
    await _ejecutar(() => _service.registrarSeguimiento(_id, observacion), 'Seguimiento registrado exitosamente.');
  }

  // ── HU73: fotografías ──────────────────────────────────────────────────────
  Future<void> _adjuntarFoto() async {
    final origen = await showModalBottomSheet<ImageSource>(
      context: context,
      showDragHandle: true,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.photo_camera_outlined),
              title: const Text('Tomar fotografía'),
              onTap: () => Navigator.pop(ctx, ImageSource.camera),
            ),
            ListTile(
              leading: const Icon(Icons.photo_library_outlined),
              title: const Text('Elegir de la galería'),
              onTap: () => Navigator.pop(ctx, ImageSource.gallery),
            ),
          ],
        ),
      ),
    );
    if (origen == null) return;

    XFile? foto;
    try {
      // imageQuality fuerza re-codificación a JPEG y reduce el peso.
      foto = await _picker.pickImage(source: origen, maxWidth: 2048, maxHeight: 2048, imageQuality: 85);
    } catch (e) {
      if (mounted) {
        mostrarMensajeIncidencia(context, 'No se pudo acceder a la cámara o galería. Revisa los permisos de la app.', error: true);
      }
      return;
    }
    if (foto == null || !mounted) return;

    final bytes = await foto.readAsBytes();
    if (!mounted) return;
    if (bytes.isEmpty) {
      mostrarMensajeIncidencia(context, 'La imagen seleccionada está vacía.', error: true);
      return;
    }
    if (bytes.length > _maxBytesEvidencia) {
      mostrarMensajeIncidencia(context, 'La imagen supera el tamaño máximo permitido (10 MB).', error: true);
      return;
    }

    final nombre = foto.name.contains('.') ? foto.name : '${foto.name}.jpg';
    final progreso = ValueNotifier<double?>(null);
    showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (_) => PopScope(
        canPop: false,
        child: AlertDialog(
          title: const Text('Subiendo fotografía'),
          content: ValueListenableBuilder<double?>(
            valueListenable: progreso,
            builder: (_, valor, __) => Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                LinearProgressIndicator(value: valor, color: AppTheme.primary),
                const SizedBox(height: 10),
                Text(valor == null ? 'Preparando...' : '${(valor * 100).toStringAsFixed(0)} %'),
              ],
            ),
          ),
        ),
      ),
    );

    try {
      final res = await _service.subirEvidencia(
        _id,
        bytes: bytes,
        nombreArchivo: nombre,
        onProgreso: (enviados, total) {
          if (total > 0) progreso.value = enviados / total;
        },
      );
      if (!mounted) return;
      Navigator.of(context, rootNavigator: true).pop();
      mostrarMensajeIncidencia(context, (res['message'] ?? 'Fotografía adjuntada.').toString());
      await _cargarEvidencias();
    } catch (e) {
      if (!mounted) return;
      Navigator.of(context, rootNavigator: true).pop();
      mostrarMensajeIncidencia(context, e.toString(), error: true);
    }
    // `progreso` no se libera aquí: el diálogo aún puede estar animando su
    // cierre y escuchándolo; no retiene recursos y lo recoge el GC.
  }

  Future<Uint8List> _imagen(int idEvidencia) {
    return _imagenes.putIfAbsent(idEvidencia, () {
      final futuro = _service.descargarEvidencia(_id, idEvidencia);
      // Si falla, se descarta del caché para permitir reintentar.
      futuro.catchError((_) {
        _imagenes.remove(idEvidencia);
        return Uint8List(0);
      });
      return futuro;
    });
  }

  void _verFoto(Map<String, dynamic> ev) {
    final idEv = (ev['id_evidencia'] as num).toInt();
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => _VisorEvidencia(
          titulo: (ev['nombre_archivo'] ?? 'Fotografía').toString(),
          subtitulo: formatearFechaHora(ev['fecha']),
          cargar: () => _imagen(idEv),
          reintentar: () {
            _imagenes.remove(idEv);
            return _imagen(idEv);
          },
        ),
      ),
    );
  }

  // ── UI ─────────────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    context.watch<AuthProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: isDark ? AppTheme.darkBackground : AppTheme.background,
      appBar: AppBar(
        title: Text(_inc == null ? 'Incidencia' : 'Incidencia #${_inc!['id_incidencia']}'),
        actions: [
          if (_inc != null && _puedeEditar)
            IconButton(tooltip: 'Editar', icon: const Icon(Icons.edit_outlined), onPressed: _procesando ? null : _editar),
          IconButton(
            tooltip: 'Actualizar',
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _procesando ? null : _cargarTodo,
          ),
        ],
      ),
      body: SafeArea(child: _buildCuerpo(isDark)),
    );
  }

  Widget _buildCuerpo(bool isDark) {
    if (_cargando) return const Center(child: CircularProgressIndicator(color: AppTheme.primary));
    if (_inc == null) {
      return Center(
        child: SingleChildScrollView(
          child: IncidenciaMensaje(
            icon: Icons.error_outline_rounded,
            titulo: 'No se pudo mostrar la incidencia',
            detalle: _error,
            onAccion: _cargarTodo,
            esError: true,
          ),
        ),
      );
    }

    final inc = _inc!;
    return Stack(
      children: [
        RefreshIndicator(
          color: AppTheme.primary,
          onRefresh: _cargarTodo,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _buildEncabezado(inc, isDark),
              const SizedBox(height: 12),
              _buildAcciones(inc),
              _buildInformacion(inc),
              const SizedBox(height: 12),
              _buildOrdenesTrabajo(inc),
              const SizedBox(height: 12),
              _buildEvidencias(isDark),
              const SizedBox(height: 12),
              _buildSeguimiento(isDark),
              const SizedBox(height: 24),
            ],
          ),
        ),
        if (_procesando)
          const Positioned(top: 0, left: 0, right: 0, child: LinearProgressIndicator(color: AppTheme.primary)),
      ],
    );
  }

  Widget _buildEncabezado(Map<String, dynamic> inc, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (_estado == 'PENDIENTE_VALIDACION')
            Wrap(
              spacing: 6, runSpacing: 6, crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                const Text('INCIDENCIA', style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.w800, color: AppTheme.primary, letterSpacing: 1)),
                IncidenciaChip.prioridad(inc['prioridad']?.toString(), compact: true),
                IncidenciaChip.estado(inc['estado']?.toString(), compact: true),
              ],
            )
          else Row(
            children: [
              const Text('INCIDENCIA', style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.w800, color: AppTheme.primary, letterSpacing: 1)),
              const Spacer(),
              IncidenciaChip.prioridad(inc['prioridad']?.toString(), compact: true),
              const SizedBox(width: 6),
              IncidenciaChip.estado(inc['estado']?.toString(), compact: true),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            (inc['titulo'] ?? '').toString(),
            style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w900, color: Colors.white),
          ),
          const SizedBox(height: 8),
          Text(
            (inc['descripcion'] ?? '').toString(),
            style: const TextStyle(fontSize: 13, color: Color(0xFFCBD5E1), height: 1.35),
          ),
        ],
      ),
    );
  }

  Widget _buildAcciones(Map<String, dynamic> inc) {
    final accion = _accionEstado;
    final botones = <Widget>[
      if (_puedeValidar) ...[
        const Text('Validar resolución'),
        for (final validacion in [_aprobar, _rechazar])
          OutlinedButton.icon(
            onPressed: _procesando ? null : () => _confirmarCambioEstado(validacion),
            icon: Icon(validacion.icon, size: 18),
            label: Text(validacion.texto),
          ),
      ],
      if (accion != null)
        ElevatedButton.icon(
          style: accion.peligro ? ElevatedButton.styleFrom(backgroundColor: AppTheme.error) : null,
          onPressed: _procesando ? null : () => _confirmarCambioEstado(accion),
          icon: Icon(accion.icon, size: 18),
          label: Text(accion.texto),
        ),
      if (_puedeAsignar)
        OutlinedButton.icon(
          onPressed: _procesando ? null : _asignarResponsable,
          icon: const Icon(Icons.person_add_alt_1_outlined, size: 18),
          label: Text(inc['id_responsable'] != null ? 'Reasignar responsable' : 'Asignar responsable'),
        ),
    ];

    String? aviso;
    if ((_estado == 'ASIGNADA' || _estado == 'EN_PROCESO') && !_esResponsable) {
      aviso = 'Solo el responsable asignado puede ${_estado == 'ASIGNADA' ? 'iniciar' : 'finalizar'} la atención.';
    }

    if (botones.isEmpty && aviso == null) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (botones.isNotEmpty) Wrap(spacing: 8, runSpacing: 8, children: botones),
          if (aviso != null)
            Padding(
              padding: EdgeInsets.only(top: botones.isEmpty ? 0 : 8),
              child: Row(
                children: [
                  const Icon(Icons.info_outline_rounded, size: 15, color: AppTheme.textMuted),
                  const SizedBox(width: 6),
                  Expanded(child: Text(aviso, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary))),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildInformacion(Map<String, dynamic> inc) {
    final obra = [inc['obra_codigo'], inc['obra_nombre']].where((v) => v != null && v.toString().isNotEmpty).join(' · ');
    final datos = <IncidenciaDato>[
      IncidenciaDato(etiqueta: 'Proyecto / Obra', valor: obra.isEmpty ? '#${inc['id_obra']}' : obra),
      IncidenciaDato(etiqueta: 'Unidad', valor: (inc['unidad_codigo'] ?? 'No aplica').toString()),
      IncidenciaDato(etiqueta: 'Ubicación', valor: (inc['ubicacion'] ?? 'No especificada').toString()),
      IncidenciaDato(etiqueta: 'Responsable', valor: (inc['responsable_nombre'] ?? 'Sin asignar').toString()),
      IncidenciaDato(
        etiqueta: 'Registrado por',
        valor: (inc['usuario_registro_nombre'] ?? 'Usuario #${inc['id_usuario_registro']}').toString(),
      ),
      IncidenciaDato(etiqueta: 'Fecha de registro', valor: formatearFechaHora(inc['created_at'])),
      IncidenciaDato(etiqueta: 'Última actualización', valor: formatearFechaHora(inc['updated_at'])),
      IncidenciaDato(etiqueta: 'Inicio de atención', valor: formatearFechaHora(inc['fecha_inicio_atencion'], vacio: 'Pendiente')),
      IncidenciaDato(etiqueta: 'Fin de atención', valor: formatearFechaHora(inc['fecha_fin_atencion'], vacio: 'Pendiente')),
    ];

    return IncidenciaSeccion(
      titulo: 'Información general',
      icon: Icons.info_outline_rounded,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final ancho = (constraints.maxWidth - 12) / 2;
          return Wrap(
            spacing: 12,
            runSpacing: 14,
            children: datos.map((d) => SizedBox(width: ancho, child: d)).toList(),
          );
        },
      ),
    );
  }

  Widget _buildOrdenesTrabajo(Map<String, dynamic> inc) {
    final ordenes = (inc['ordenes_trabajo'] is List)
        ? (inc['ordenes_trabajo'] as List).map((e) => Map<String, dynamic>.from(e as Map)).toList()
        : <Map<String, dynamic>>[];

    return IncidenciaSeccion(
      titulo: 'Órdenes de trabajo afectadas',
      icon: Icons.assignment_outlined,
      accion: _puedeSeleccionarOt
          ? TextButton.icon(
              onPressed: _procesando ? null : _seleccionarOrdenes,
              icon: Icon(ordenes.isEmpty ? Icons.add_rounded : Icons.edit_outlined, size: 16),
              label: Text(ordenes.isEmpty ? 'Agregar' : 'Editar'),
            )
          : null,
      child: ordenes.isEmpty
          ? const Text('No se han indicado órdenes de trabajo afectadas.', style: TextStyle(fontSize: 12.5, color: AppTheme.textSecondary))
          : Column(
              children: [
                for (final ot in ordenes)
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    dense: true,
                    leading: const Icon(Icons.assignment_turned_in_outlined, color: Color(0xFF10B981)),
                    title: Text(
                      '${IncidenciaService.etiquetaOrden(ot['orden_nro'])} — ${ot['tipo_trab'] ?? 'Sin tipo de trabajo'}',
                      style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
                    ),
                    subtitle: Text(
                      'Vinculada ${formatearFechaHora(ot['fecha_vinculo'])}'
                      '${ot['usuario_vinculo_nombre'] != null ? ' por ${ot['usuario_vinculo_nombre']}' : ''}',
                      style: const TextStyle(fontSize: 11.5),
                    ),
                    trailing: Text(
                      (ot['estado'] ?? '').toString(),
                      style: const TextStyle(fontSize: 10.5, fontWeight: FontWeight.w800, color: AppTheme.textSecondary),
                    ),
                  ),
              ],
            ),
    );
  }

  Widget _buildEvidencias(bool isDark) {
    return IncidenciaSeccion(
      titulo: 'Fotografías',
      icon: Icons.photo_library_outlined,
      accion: _puedeAdjuntar
          ? TextButton.icon(
              onPressed: _procesando ? null : _adjuntarFoto,
              icon: const Icon(Icons.add_a_photo_outlined, size: 16),
              label: const Text('Adjuntar'),
            )
          : null,
      child: _errorEvidencias != null
          ? _errorSeccion(_errorEvidencias!, _cargarEvidencias)
          : _evidencias.isEmpty
              ? const Text('Aún no hay fotografías adjuntas.', style: TextStyle(fontSize: 12.5, color: AppTheme.textSecondary))
              : GridView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: _evidencias.length,
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 3,
                    mainAxisSpacing: 8,
                    crossAxisSpacing: 8,
                  ),
                  itemBuilder: (_, i) {
                    final ev = _evidencias[i];
                    final idEv = (ev['id_evidencia'] as num).toInt();
                    return InkWell(
                      onTap: () => _verFoto(ev),
                      borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                        child: Container(
                          color: isDark ? AppTheme.darkSurfaceCard : AppTheme.surfaceSubtle,
                          child: FutureBuilder<Uint8List>(
                            future: _imagen(idEv),
                            builder: (_, snap) {
                              if (snap.connectionState != ConnectionState.done) {
                                return const Center(
                                  child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)),
                                );
                              }
                              if (snap.hasError || (snap.data?.isEmpty ?? true)) {
                                return const Center(child: Icon(Icons.broken_image_outlined, color: AppTheme.textMuted));
                              }
                              return Image.memory(
                                snap.data!,
                                fit: BoxFit.cover,
                                cacheWidth: 300,
                                errorBuilder: (_, __, ___) =>
                                    const Center(child: Icon(Icons.broken_image_outlined, color: AppTheme.textMuted)),
                              );
                            },
                          ),
                        ),
                      ),
                    );
                  },
                ),
    );
  }

  Widget _buildSeguimiento(bool isDark) {
    return IncidenciaSeccion(
      titulo: 'Seguimiento',
      icon: Icons.timeline_rounded,
      accion: _puedeComentar
          ? TextButton.icon(
              onPressed: _procesando ? null : _agregarSeguimiento,
              icon: const Icon(Icons.add_comment_outlined, size: 16),
              label: const Text('Agregar'),
            )
          : null,
      child: _errorSeguimiento != null
          ? _errorSeccion(_errorSeguimiento!, _cargarSeguimiento)
          : _seguimiento.isEmpty
              ? const Text('Sin movimientos registrados.', style: TextStyle(fontSize: 12.5, color: AppTheme.textSecondary))
              : Column(
                  children: [
                    for (var i = 0; i < _seguimiento.length; i++) _itemSeguimiento(_seguimiento[i], i == _seguimiento.length - 1, isDark),
                  ],
                ),
    );
  }

  Widget _itemSeguimiento(Map<String, dynamic> s, bool ultimo, bool isDark) {
    final anterior = s['estado_anterior']?.toString();
    final nuevo = s['estado_nuevo']?.toString();
    final cambioEstado = anterior != nuevo;
    final color = colorEstadoIncidencia(nuevo);

    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Column(
            children: [
              Container(
                width: 10,
                height: 10,
                margin: const EdgeInsets.only(top: 4),
                decoration: BoxDecoration(color: cambioEstado ? color : AppTheme.textMuted, shape: BoxShape.circle),
              ),
              if (!ultimo)
                Expanded(child: Container(width: 2, color: isDark ? AppTheme.darkBorder : AppTheme.border)),
            ],
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Padding(
              padding: EdgeInsets.only(bottom: ultimo ? 0 : 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          (s['usuario_nombre'] ?? 'Sistema').toString(),
                          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12.5),
                        ),
                      ),
                      Text(formatearFechaHora(s['fecha']), style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                    ],
                  ),
                  if (cambioEstado) ...[
                    const SizedBox(height: 4),
                    Wrap(
                      crossAxisAlignment: WrapCrossAlignment.center,
                      spacing: 4,
                      children: [
                        if (anterior != null) IncidenciaChip.estado(anterior, compact: true),
                        if (anterior != null) const Icon(Icons.arrow_forward_rounded, size: 14, color: AppTheme.textMuted),
                        IncidenciaChip.estado(nuevo, compact: true),
                      ],
                    ),
                  ],
                  if ((s['observacion'] ?? '').toString().isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(s['observacion'].toString(), style: const TextStyle(fontSize: 12.5, height: 1.3)),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _errorSeccion(String mensaje, Future<void> Function() reintentar) {
    return Row(
      children: [
        const Icon(Icons.error_outline_rounded, color: AppTheme.error, size: 18),
        const SizedBox(width: 8),
        Expanded(child: Text(mensaje, style: const TextStyle(fontSize: 12.5))),
        IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: reintentar),
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Diálogo con campo de texto. Es dueño de su controlador para no liberarlo
// mientras el TextField sigue montado durante la animación de cierre.
// Devuelve el texto (posiblemente vacío) al confirmar, o null al cancelar.
// ─────────────────────────────────────────────────────────────────────────────
class _DialogoTexto extends StatefulWidget {
  final String titulo;
  final String? mensaje;
  final String hint;
  final String textoConfirmar;
  final bool peligro;
  final bool obligatorio;

  const _DialogoTexto({
    required this.titulo,
    this.mensaje,
    required this.hint,
    required this.textoConfirmar,
    this.peligro = false,
    this.obligatorio = false,
  });

  @override
  State<_DialogoTexto> createState() => _DialogoTextoState();
}

class _DialogoTextoState extends State<_DialogoTexto> {
  final TextEditingController _ctrl = TextEditingController();

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.titulo),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (widget.mensaje != null) ...[
            Text(widget.mensaje!, style: const TextStyle(fontSize: 13)),
            const SizedBox(height: 14),
          ],
          TextField(
            controller: _ctrl,
            autofocus: widget.obligatorio,
            minLines: widget.obligatorio ? 3 : 1,
            maxLines: 6,
            maxLength: 2000,
            textCapitalization: TextCapitalization.sentences,
            onChanged: widget.obligatorio ? (_) => setState(() {}) : null,
            decoration: InputDecoration(hintText: widget.hint),
          ),
        ],
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
        ElevatedButton(
          style: widget.peligro ? ElevatedButton.styleFrom(backgroundColor: AppTheme.error) : null,
          onPressed: widget.obligatorio && _ctrl.text.trim().isEmpty
              ? null
              : () => Navigator.pop(context, _ctrl.text.trim()),
          child: Text(widget.textoConfirmar),
        ),
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// HU71 — Selector de responsable (candidatos del MISMO tenant, según backend)
// ─────────────────────────────────────────────────────────────────────────────
class _SelectorResponsable extends StatefulWidget {
  final IncidenciaService service;
  final Map<String, dynamic> incidencia;

  const _SelectorResponsable({required this.service, required this.incidencia});

  @override
  State<_SelectorResponsable> createState() => _SelectorResponsableState();
}

class _SelectorResponsableState extends State<_SelectorResponsable> {
  List<Map<String, dynamic>> _usuarios = [];
  int? _seleccionado;
  bool _cargando = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _seleccionado = int.tryParse(widget.incidencia['id_responsable']?.toString() ?? '');
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final lista = await widget.service.listarResponsables((widget.incidencia['id_incidencia'] as num).toInt());
      if (!mounted) return;
      setState(() {
        _usuarios = lista;
        _cargando = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _cargando = false;
        _error = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final estado = widget.incidencia['estado']?.toString();
    return _HojaInferior(
      titulo: 'Asignar responsable',
      descripcion: 'Selecciona el usuario que atenderá la incidencia.'
          '${estado == 'ABIERTA' ? ' Al asignarla pasará a ASIGNADA.' : ''}',
      cargando: _cargando,
      error: _error,
      onReintentar: _cargar,
      vacio: _usuarios.isEmpty ? 'No hay responsables disponibles en tu empresa.' : null,
      textoConfirmar: 'Asignar',
      onConfirmar: _seleccionado == null || _usuarios.isEmpty ? null : () => Navigator.pop(context, _seleccionado),
      child: RadioGroup<int>(
        groupValue: _seleccionado,
        onChanged: (v) => setState(() => _seleccionado = v),
        child: Column(
          children: [
            for (final u in _usuarios)
              RadioListTile<int>(
                value: (u['nro_usuario'] as num).toInt(),
                activeColor: AppTheme.primary,
                title: Text((u['nombre_completo'] ?? u['nombre_usuario'] ?? '').toString(), style: const TextStyle(fontWeight: FontWeight.w700)),
                subtitle: Text((u['nombre_rol'] ?? 'Sin rol').toString()),
              ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Selector de OT afectadas: solo las OT que el backend devuelve como
// disponibles (misma obra y empresa de la incidencia).
// ─────────────────────────────────────────────────────────────────────────────
class _SelectorOrdenesTrabajo extends StatefulWidget {
  final IncidenciaService service;
  final Map<String, dynamic> incidencia;

  const _SelectorOrdenesTrabajo({required this.service, required this.incidencia});

  @override
  State<_SelectorOrdenesTrabajo> createState() => _SelectorOrdenesTrabajoState();
}

class _SelectorOrdenesTrabajoState extends State<_SelectorOrdenesTrabajo> {
  List<Map<String, dynamic>> _ordenes = [];
  final Set<int> _seleccionadas = {};
  bool _cargando = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final lista = await widget.service.listarOrdenesTrabajoDisponibles((widget.incidencia['id_incidencia'] as num).toInt());
      if (!mounted) return;
      setState(() {
        _ordenes = lista;
        _seleccionadas
          ..clear()
          ..addAll(lista.where((o) => o['afectada'] == true).map((o) => (o['orden_nro'] as num).toInt()));
        _cargando = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _cargando = false;
        _error = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final obra = [widget.incidencia['obra_codigo'], widget.incidencia['obra_nombre']].where((v) => v != null).join(' · ');
    return _HojaInferior(
      titulo: 'Órdenes de trabajo afectadas',
      descripcion: 'Marca las órdenes de $obra afectadas por esta incidencia. Solo se muestran órdenes de esta obra.',
      cargando: _cargando,
      error: _error,
      onReintentar: _cargar,
      vacio: _ordenes.isEmpty ? 'Esta obra no tiene órdenes de trabajo registradas.' : null,
      textoConfirmar: 'Guardar (${_seleccionadas.length})',
      onConfirmar: _error != null || _cargando || _ordenes.isEmpty
          ? null
          : () => Navigator.pop(context, _seleccionadas.toList()..sort()),
      child: Column(
        children: [
          for (final o in _ordenes)
            CheckboxListTile(
              value: _seleccionadas.contains((o['orden_nro'] as num).toInt()),
              activeColor: AppTheme.primary,
              controlAffinity: ListTileControlAffinity.leading,
              onChanged: (marcado) => setState(() {
                final nro = (o['orden_nro'] as num).toInt();
                marcado == true ? _seleccionadas.add(nro) : _seleccionadas.remove(nro);
              }),
              title: Text(
                '${IncidenciaService.etiquetaOrden(o['orden_nro'])} — ${o['tipo_trab'] ?? 'Sin tipo de trabajo'}',
                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13.5),
              ),
              subtitle: Text(
                [
                  (o['estado'] ?? 'Sin estado').toString(),
                  if (o['fecha_inicio'] != null)
                    '${formatearFechaHora(o['fecha_inicio'], conHora: false)}'
                        '${o['fecha_fin'] != null ? ' – ${formatearFechaHora(o['fecha_fin'], conHora: false)}' : ''}',
                ].join(' · '),
                style: const TextStyle(fontSize: 11.5),
              ),
            ),
        ],
      ),
    );
  }
}

/// Estructura común de hoja inferior con carga / error / vacío / confirmar.
class _HojaInferior extends StatelessWidget {
  final String titulo;
  final String descripcion;
  final bool cargando;
  final String? error;
  final VoidCallback onReintentar;
  final String? vacio;
  final String textoConfirmar;
  final VoidCallback? onConfirmar;
  final Widget child;

  const _HojaInferior({
    required this.titulo,
    required this.descripcion,
    required this.cargando,
    required this.error,
    required this.onReintentar,
    required this.vacio,
    required this.textoConfirmar,
    required this.onConfirmar,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    Widget contenido;
    if (cargando) {
      contenido = const Padding(
        padding: EdgeInsets.all(24),
        child: Center(child: CircularProgressIndicator(color: AppTheme.primary)),
      );
    } else if (error != null) {
      contenido = IncidenciaMensaje(icon: Icons.error_outline_rounded, titulo: 'Error', detalle: error, onAccion: onReintentar, esError: true);
    } else if (vacio != null) {
      contenido = Padding(
        padding: const EdgeInsets.all(20),
        child: Text(vacio!, textAlign: TextAlign.center, style: const TextStyle(color: AppTheme.textSecondary)),
      );
    } else {
      contenido = child;
    }

    return SafeArea(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(titulo, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 4),
                  Text(descripcion, style: const TextStyle(fontSize: 12.5, color: AppTheme.textSecondary)),
                ],
              ),
            ),
            Flexible(child: SingleChildScrollView(child: contenido)),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 12),
              child: Row(
                children: [
                  Expanded(child: OutlinedButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar'))),
                  const SizedBox(width: 10),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: cargando ? null : onConfirmar,
                      child: Text(textoConfirmar),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Visor de fotografía (descargada por el endpoint autenticado)
// ─────────────────────────────────────────────────────────────────────────────
class _VisorEvidencia extends StatefulWidget {
  final String titulo;
  final String subtitulo;
  final Future<Uint8List> Function() cargar;
  final Future<Uint8List> Function() reintentar;

  const _VisorEvidencia({required this.titulo, required this.subtitulo, required this.cargar, required this.reintentar});

  @override
  State<_VisorEvidencia> createState() => _VisorEvidenciaState();
}

class _VisorEvidenciaState extends State<_VisorEvidencia> {
  late Future<Uint8List> _futuro = widget.cargar();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(widget.titulo, style: const TextStyle(fontSize: 14, color: Colors.white), overflow: TextOverflow.ellipsis),
            Text(widget.subtitulo, style: const TextStyle(fontSize: 11, color: Colors.white70)),
          ],
        ),
      ),
      body: FutureBuilder<Uint8List>(
        future: _futuro,
        builder: (_, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator(color: AppTheme.primary));
          }
          if (snap.hasError || (snap.data?.isEmpty ?? true)) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.broken_image_outlined, color: Colors.white54, size: 48),
                  const SizedBox(height: 10),
                  Text(
                    snap.error?.toString() ?? 'No se pudo cargar la fotografía.',
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.white70),
                  ),
                  const SizedBox(height: 12),
                  OutlinedButton(
                    onPressed: () => setState(() => _futuro = widget.reintentar()),
                    child: const Text('Reintentar'),
                  ),
                ],
              ),
            );
          }
          return InteractiveViewer(
            minScale: 1,
            maxScale: 5,
            child: Center(
              child: Image.memory(
                snap.data!,
                errorBuilder: (_, __, ___) => const Text('Formato de imagen no soportado.', style: TextStyle(color: Colors.white70)),
              ),
            ),
          );
        },
      ),
    );
  }
}
