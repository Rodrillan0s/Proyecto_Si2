import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/auth_provider.dart';
import '../services/incidencia_service.dart';
import '../services/obra_service.dart';
import '../services/unidad_service.dart';
import '../theme/app_theme.dart';
import '../widgets/incidencia_widgets.dart';

/// CU19 — HU69/HU70: registrar o editar una incidencia.
///
/// Registro: obra, unidad (opcional), ubicación, título, descripción, prioridad.
/// La incidencia nace ABIERTA (lo fija el backend). Al editar, la obra y la
/// unidad son de solo lectura (el backend no permite moverlas).
///
/// Devuelve por Navigator.pop: el id de la incidencia creada (registro) o
/// `true` (edición guardada).
class IncidenciaFormScreen extends StatefulWidget {
  final Map<String, dynamic>? incidencia;
  final int? idObraInicial;

  const IncidenciaFormScreen({super.key, this.incidencia, this.idObraInicial});

  @override
  State<IncidenciaFormScreen> createState() => _IncidenciaFormScreenState();
}

class _IncidenciaFormScreenState extends State<IncidenciaFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final IncidenciaService _service = IncidenciaService();
  final ObraService _obraService = ObraService();
  final UnidadService _unidadService = UnidadService();

  final _tituloCtrl = TextEditingController();
  final _descripcionCtrl = TextEditingController();
  final _ubicacionCtrl = TextEditingController();

  List<Map<String, dynamic>> _proyectos = [];
  List<Map<String, dynamic>> _unidades = [];
  int? _idObra;
  int? _idUnidad;
  String? _prioridad;

  bool _cargandoProyectos = false;
  bool _cargandoUnidades = false;
  String? _errorUnidades;
  int _solicitudUnidades = 0;
  bool _guardando = false;
  String? _errorCarga;

  bool get _editando => widget.incidencia != null;

  @override
  void initState() {
    super.initState();
    final inc = widget.incidencia;
    if (inc != null) {
      _tituloCtrl.text = (inc['titulo'] ?? '').toString();
      _descripcionCtrl.text = (inc['descripcion'] ?? '').toString();
      _ubicacionCtrl.text = (inc['ubicacion'] ?? '').toString();
      _prioridad = inc['prioridad']?.toString();
    } else {
      _cargarProyectos();
    }
  }

  @override
  void dispose() {
    _tituloCtrl.dispose();
    _descripcionCtrl.dispose();
    _ubicacionCtrl.dispose();
    super.dispose();
  }

  Future<void> _cargarProyectos() async {
    setState(() {
      _cargandoProyectos = true;
      _errorCarga = null;
    });
    try {
      final trabajador = context.read<AuthProvider>().esTrabajadorCampo;
      final lista = trabajador ? await _service.obrasRegistro() : await _obraService.listarProyectos();
      if (!mounted) return;
      setState(() {
        _proyectos = lista;
        _cargandoProyectos = false;
        _idObra ??= widget.idObraInicial;
        if (_idObra != null && !_proyectos.any((p) => _idDe(p['id_obra']) == _idObra)) _idObra = null;
      });
      if (_idObra != null) _cargarUnidades(_idObra!);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _cargandoProyectos = false;
        _errorCarga = e.toString().replaceAll('Exception: ', '');
      });
    }
  }

  /// HU69: al cambiar de obra se limpia la unidad y se cargan solo las de esa obra.
  Future<void> _cargarUnidades(int idObra) async {
    final solicitud = ++_solicitudUnidades;
    setState(() {
      _cargandoUnidades = true;
      _unidades = [];
      _idUnidad = null;
      _errorUnidades = null;
    });
    try {
      final lista = await _unidadService.listarUnidades(idObra);
      if (!mounted || _idObra != idObra || solicitud != _solicitudUnidades) return;
      setState(() {
        _unidades = lista;
        _cargandoUnidades = false;
      });
    } catch (e) {
      if (!mounted || _idObra != idObra || solicitud != _solicitudUnidades) return;
      setState(() {
        _cargandoUnidades = false;
        _errorUnidades = e.toString().replaceAll('Exception: ', '');
      });
    }
  }

  static int? _idDe(dynamic v) => int.tryParse(v?.toString() ?? '');

  Future<void> _guardar() async {
    if (_guardando || !(_formKey.currentState?.validate() ?? false)) return;
    setState(() => _guardando = true);

    try {
      if (_editando) {
        await _service.actualizar(
          (widget.incidencia!['id_incidencia'] as num).toInt(),
          titulo: _tituloCtrl.text,
          descripcion: _descripcionCtrl.text,
          prioridad: _prioridad!,
          ubicacion: _ubicacionCtrl.text,
        );
        if (!mounted) return;
        mostrarMensajeIncidencia(context, 'Incidencia actualizada exitosamente.');
        Navigator.pop(context, true);
      } else {
        final res = await _service.registrar(
          idObra: _idObra!,
          idUnidad: _idUnidad,
          titulo: _tituloCtrl.text,
          descripcion: _descripcionCtrl.text,
          prioridad: _prioridad!,
          ubicacion: _ubicacionCtrl.text,
        );
        if (!mounted) return;
        mostrarMensajeIncidencia(context, (res['message'] ?? 'Incidencia registrada exitosamente.').toString());
        Navigator.pop(context, (res['id_incidencia'] as num?)?.toInt());
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _guardando = false);
      mostrarMensajeIncidencia(context, e.toString(), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final inc = widget.incidencia;

    return Scaffold(
      backgroundColor: isDark ? AppTheme.darkBackground : AppTheme.background,
      appBar: AppBar(title: Text(_editando ? 'Editar incidencia' : 'Registrar incidencia')),
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (_errorCarga != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Material(
                    color: AppTheme.error.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                    child: ListTile(
                      leading: const Icon(Icons.error_outline, color: AppTheme.error),
                      title: Text(_errorCarga!, style: const TextStyle(fontSize: 12.5)),
                      trailing: IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargarProyectos),
                    ),
                  ),
                ),

              // ── Obra ──
              _etiqueta(_editando ? 'Proyecto / Obra' : 'Proyecto / Obra *'),
              if (_editando)
                _soloLectura([inc?['obra_codigo'], inc?['obra_nombre']].where((v) => v != null).join(' · '))
              else
                DropdownButtonFormField<int>(
                  key: ValueKey('obra-${_proyectos.length}'),
                  initialValue: _idObra,
                  isExpanded: true,
                  hint: Text(_cargandoProyectos ? 'Cargando proyectos...' : 'Seleccione un proyecto'),
                  items: _proyectos
                      .where((p) => _idDe(p['id_obra']) != null)
                      .map((p) => DropdownMenuItem<int>(
                            value: _idDe(p['id_obra']),
                            child: Text('${p['codigo'] ?? ''} · ${p['nombre'] ?? ''}', overflow: TextOverflow.ellipsis),
                          ))
                      .toList(),
                  onChanged: _cargandoProyectos || _guardando
                      ? null
                      : (v) {
                          setState(() => _idObra = v);
                          if (v != null) _cargarUnidades(v);
                        },
                  validator: (v) => v == null || !_proyectos.any((p) => _idDe(p['id_obra']) == v)
                      ? 'Debe seleccionar el proyecto/obra.' : null,
                ),
              const SizedBox(height: 16),

              // ── Unidad ──
              if (_editando) ...[
                if ((inc?['unidad_codigo'] ?? '').toString().isNotEmpty) ...[
                  _etiqueta('Unidad de construcción'),
                  _soloLectura(inc!['unidad_codigo'].toString()),
                  const SizedBox(height: 16),
                ],
              ] else ...[
                _etiqueta('Unidad'),
                DropdownButtonFormField<int?>(
                  key: ValueKey('unidad-$_idObra-$_cargandoUnidades-${_unidades.length}'),
                  initialValue: _idUnidad,
                  isExpanded: true,
                  items: [
                    DropdownMenuItem<int?>(
                      value: null,
                      child: Text(_idObra == null
                          ? 'Seleccione un proyecto primero'
                          : (_cargandoUnidades ? 'Cargando unidades...' : (_errorUnidades != null
                              ? 'No se pudieron cargar las unidades'
                              : (_unidades.isEmpty ? 'Sin unidades disponibles' : 'Sin unidad específica')))),
                    ),
                    ..._unidades.where((u) => _idDe(u['id_unidad']) != null).map((u) => DropdownMenuItem<int?>(
                          value: _idDe(u['id_unidad']),
                          child: Text('${u['codigo'] ?? ''} · ${u['nombre'] ?? ''}', overflow: TextOverflow.ellipsis),
                        )),
                  ],
                  onChanged: _idObra == null || _cargandoUnidades || _guardando ? null : (v) => setState(() => _idUnidad = v),
                  validator: (v) => v != null && !_unidades.any((u) => _idDe(u['id_unidad']) == v)
                      ? 'Seleccione una unidad de la obra actual.' : null,
                ),
                const Text('Opcional', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                if (_errorUnidades != null)
                  ListTile(
                    title: Text(_errorUnidades!, style: const TextStyle(fontSize: 12, color: AppTheme.error)),
                    trailing: IconButton(
                      tooltip: 'Reintentar carga de unidades',
                      icon: const Icon(Icons.refresh_rounded),
                      onPressed: _guardando ? null : () => _cargarUnidades(_idObra!),
                    ),
                  ),
                const SizedBox(height: 16),
              ],

              // ── Ubicación ──
              _etiqueta('Ubicación (opcional)'),
              TextFormField(
                controller: _ubicacionCtrl,
                maxLength: 255,
                textCapitalization: TextCapitalization.sentences,
                decoration: const InputDecoration(hintText: 'Ej.: Bloque 1, pared norte del piso 2', counterText: ''),
              ),
              const SizedBox(height: 16),

              // ── Título ──
              _etiqueta('Título *'),
              TextFormField(
                controller: _tituloCtrl,
                maxLength: 200,
                textCapitalization: TextCapitalization.sentences,
                decoration: const InputDecoration(hintText: 'Ej.: Filtración de agua en muro', counterText: ''),
                validator: (v) {
                  final t = v?.trim() ?? '';
                  if (t.isEmpty) return 'El título es obligatorio.';
                  if (t.length > 200) return 'El título no puede superar 200 caracteres.';
                  return null;
                },
              ),
              const SizedBox(height: 16),

              // ── Descripción ──
              _etiqueta('Descripción *'),
              TextFormField(
                controller: _descripcionCtrl,
                minLines: 4,
                maxLines: 8,
                maxLength: 4000,
                textCapitalization: TextCapitalization.sentences,
                decoration: const InputDecoration(hintText: 'Describe con detalle la incidencia observada en obra...'),
                validator: (v) {
                  final t = v?.trim() ?? '';
                  if (t.isEmpty) return 'La descripción es obligatoria.';
                  if (t.length > 4000) return 'La descripción no puede superar 4000 caracteres.';
                  return null;
                },
              ),
              const SizedBox(height: 8),

              // ── Prioridad (HU70) ──
              _etiqueta('Prioridad *'),
              FormField<String>(
                initialValue: _prioridad,
                validator: (_) => _prioridad == null ? 'Debe seleccionar una prioridad.' : null,
                builder: (state) => Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: IncidenciaService.prioridades.map((p) {
                        final color = colorPrioridad(p);
                        return ChoiceChip(
                          label: Text(etiquetaPrioridad(p)),
                          selected: _prioridad == p,
                          selectedColor: color.withValues(alpha: 0.2),
                          avatar: Icon(Icons.flag_rounded, size: 16, color: color),
                          onSelected: _guardando
                              ? null
                              : (_) {
                                  setState(() => _prioridad = p);
                                  state.didChange(p);
                                },
                        );
                      }).toList(),
                    ),
                    if (state.hasError)
                      Padding(
                        padding: const EdgeInsets.only(top: 6),
                        child: Text(state.errorText!, style: const TextStyle(color: AppTheme.error, fontSize: 12)),
                      ),
                  ],
                ),
              ),

              if (!_editando) ...[
                const SizedBox(height: 16),
                const Text(
                  'La incidencia se registrará en estado ABIERTA. Podrás adjuntar fotografías desde su detalle.',
                  style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                ),
              ],
              const SizedBox(height: 24),
              SizedBox(
                height: 48,
                child: ElevatedButton.icon(
                  onPressed: _guardando ? null : _guardar,
                  icon: _guardando
                      ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : Icon(_editando ? Icons.save_outlined : Icons.add_task_rounded),
                  label: Text(_guardando ? 'Guardando...' : (_editando ? 'Guardar cambios' : 'Registrar incidencia')),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _etiqueta(String texto) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Text(
          texto.toUpperCase(),
          style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800, letterSpacing: 0.4, color: AppTheme.textSecondary),
        ),
      );

  Widget _soloLectura(String texto) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      decoration: BoxDecoration(
        color: isDark ? AppTheme.darkSurfaceCard : AppTheme.surfaceSubtle,
        borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
        border: Border.all(color: isDark ? AppTheme.darkBorder : AppTheme.border),
      ),
      child: Text(texto.isEmpty ? '—' : texto, style: const TextStyle(fontSize: 13.5)),
    );
  }
}
