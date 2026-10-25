import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_provider.dart';
import '../services/cronograma_service.dart';

String _hoy() => DateTime.now()
    .toUtc()
    .subtract(const Duration(hours: 4))
    .toIso8601String()
    .substring(0, 10);
String _error(Object e) => e.toString().replaceFirst('Exception: ', '');

Future<bool> _confirmar(BuildContext context, String texto) async =>
    await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
                title: const Text('Confirmar'),
                content: Text(texto),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(ctx, false),
                      child: const Text('Cancelar')),
                  FilledButton(
                      onPressed: () => Navigator.pop(ctx, true),
                      child: const Text('Continuar'))
                ])) ??
    false;

class CronogramasScreen extends StatefulWidget {
  final int idObra;
  final String nombreObra;
  const CronogramasScreen(
      {super.key, required this.idObra, required this.nombreObra});
  @override
  State<CronogramasScreen> createState() => _CronogramasScreenState();
}

class _CronogramasScreenState extends State<CronogramasScreen> {
  final _api = CronogramaService();
  List<Map<String, dynamic>> _planes = [];
  Map<String, dynamic>? _plan;
  int? _seleccion;
  bool _loading = true, _soloRetrasos = false;
  String _mensaje = '', _desde = '', _hasta = '', _corte = _hoy();
  int _request = 0;
  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar({bool lista = true}) async {
    final request = ++_request;
    setState(() {
      _loading = true;
      _mensaje = '';
    });
    try {
      final planes = lista ? await _api.listar(widget.idObra) : _planes;
      final id = planes.any((c) => c['id_cronograma'] == _seleccion)
          ? _seleccion
          : (planes.isEmpty ? null : planes.first['id_cronograma'] as int);
      final filtros = <String, String>{
        'corte': _corte,
        if (_desde.isNotEmpty) 'desde': _desde,
        if (_hasta.isNotEmpty) 'hasta': _hasta
      };
      final plan =
          id == null ? null : await _api.obtener(widget.idObra, id, filtros);
      if (!mounted || request != _request) return;
      setState(() {
        _planes = planes;
        _seleccion = id;
        _plan = plan;
        _loading = false;
      });
    } catch (e) {
      if (mounted && request == _request) {
        setState(() {
          _mensaje = _error(e);
          _loading = false;
          if (_plan?['id_cronograma'] != _seleccion) _plan = null;
        });
      }
    }
  }

  Future<void> _editar({bool nuevo = false}) async {
    final auth = context.read<AuthProvider>();
    final result = await Navigator.push<int>(
        context,
        MaterialPageRoute(
            builder: (_) => CronogramaEditorScreen(
                idObra: widget.idObra,
                plan: nuevo ? null : _plan,
                puedeCabecera: auth.hasPermission(
                    nuevo ? 'Registrar_cronograma' : 'Modificar_cronograma'))));
    if (result != null && mounted) {
      _seleccion = result;
      await _cargar();
    }
  }

  Future<void> _eliminar() async {
    if (_plan == null ||
        !await _confirmar(
            context, '¿Eliminar el cronograma y todas sus actividades?')) {
      return;
    }
    setState(() {
      _loading = true;
    });
    try {
      await _api.eliminar(widget.idObra, _plan!);
      if (mounted) await _cargar();
    } catch (e) {
      if (mounted) {
        setState(() {
          _mensaje = _error(e);
          _loading = false;
        });
      }
    }
  }

  Future<void> _fechaFiltro(String campo) async {
    final date = await showDatePicker(
        context: context,
        initialDate: DateTime.tryParse(campo == 'desde'
                ? _desde
                : campo == 'hasta'
                    ? _hasta
                    : _corte) ??
            DateTime.now(),
        firstDate: DateTime(2000),
        lastDate: campo == 'corte' ? DateTime.parse(_hoy()) : DateTime(2100));
    if (date == null || !mounted) return;
    setState(() {
      final value = date.toIso8601String().substring(0, 10);
      if (campo == 'desde') {
        _desde = value;
      } else if (campo == 'hasta') {
        _hasta = value;
      } else {
        _corte = value;
      }
    });
    await _cargar(lista: false);
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final actividades = (_plan?['programadas'] as List? ?? [])
        .where((a) =>
            !_soloRetrasos ||
            a['dias_retraso'] > 0 ||
            a['inicio_retrasado'] == true)
        .toList();
    final todas = (_plan?['actividades'] as List? ?? []);
    return Scaffold(
        appBar: AppBar(title: const Text('Cronogramas')),
        body: RefreshIndicator(
            onRefresh: () => _cargar(),
            child: ListView(padding: const EdgeInsets.all(16), children: [
              Text(widget.nombreObra,
                  style: Theme.of(context).textTheme.headlineSmall),
              const Text('CU39 · Planificación y seguimiento de obra'),
              const SizedBox(height: 16),
              if (_mensaje.isNotEmpty)
                Semantics(
                    liveRegion: true,
                    child: Text(_mensaje,
                        style: TextStyle(
                            color: Theme.of(context).colorScheme.error))),
              if (_loading) const LinearProgressIndicator(),
              if (auth.hasPermission('Registrar_cronograma'))
                FilledButton.icon(
                    onPressed: _loading ? null : () => _editar(nuevo: true),
                    icon: const Icon(Icons.add),
                    label: const Text('Crear cronograma')),
              const SizedBox(height: 12),
              if (_planes.isEmpty && !_loading && _mensaje.isEmpty)
                const Text(
                    'Aún no hay cronogramas. El Jefe de Obra puede crear el primero.'),
              if (_planes.isNotEmpty)
                DropdownButtonFormField<int>(
                    initialValue: _seleccion,
                    key: ValueKey(_seleccion),
                    isExpanded: true,
                    decoration: const InputDecoration(labelText: 'Cronograma'),
                    items: _planes
                        .map((p) => DropdownMenuItem(
                            value: p['id_cronograma'] as int,
                            child: Text(p['nombre'],
                                overflow: TextOverflow.ellipsis)))
                        .toList(),
                    onChanged: _loading
                        ? null
                        : (id) {
                            _seleccion = id;
                            _cargar(lista: false);
                          }),
              if (_plan != null && !_loading) ...[
                const SizedBox(height: 12),
                Text(_plan!['descripcion'] ?? ''),
                Text('${_plan!['fecha_inicio']} → ${_plan!['fecha_fin']}'),
                Wrap(spacing: 8, children: [
                  if (auth.hasPermission('Planificar_cronograma') ||
                      auth.hasPermission('Modificar_cronograma'))
                    OutlinedButton(
                        onPressed: () => _editar(),
                        child: const Text('Editar planificación')),
                  if (auth.hasPermission('Modificar_cronograma'))
                    TextButton(
                        onPressed: _eliminar, child: const Text('Eliminar'))
                ]),
                Wrap(spacing: 6, children: [
                  TextButton(
                      onPressed: () => _fechaFiltro('desde'),
                      child:
                          Text('Desde: ${_desde.isEmpty ? 'todas' : _desde}')),
                  TextButton(
                      onPressed: () => _fechaFiltro('hasta'),
                      child:
                          Text('Hasta: ${_hasta.isEmpty ? 'todas' : _hasta}')),
                  TextButton(
                      onPressed: () => _fechaFiltro('corte'),
                      child: Text('Corte: $_corte')),
                  TextButton(
                      onPressed: () {
                        _desde = '';
                        _hasta = '';
                        _corte = _hoy();
                        _cargar(lista: false);
                      },
                      child: const Text('Limpiar filtros'))
                ]),
                SwitchListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Solo desviaciones'),
                    value: _soloRetrasos,
                    onChanged: (v) => setState(() => _soloRetrasos = v)),
                Text(
                    '${_plan!['resumen']['total']} programadas · ${_plan!['resumen']['completadas']} completadas · ${_plan!['resumen']['retrasadas']} con retraso'),
                const Text(
                    'Días calendario al corte; las completadas conservan su retraso histórico. El avance es el último registrado.',
                    style: TextStyle(fontSize: 12)),
                const SizedBox(height: 12),
                for (final a in actividades)
                  Card(
                      child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                    '${a['tipo'] == 'HITO' ? '◆ Hito' : 'Actividad'} · ${a['nombre']}',
                                    style: Theme.of(context)
                                        .textTheme
                                        .titleMedium),
                                if ((a['descripcion'] ?? '').isNotEmpty)
                                  Text(a['descripcion']),
                                Text(
                                    'Previsto: ${a['fecha_inicio']} → ${a['fecha_fin']}'),
                                Text(
                                    'Real: ${a['inicio_real'] ?? 'sin inicio'} → ${a['fin_real'] ?? 'sin fin'}'),
                                Text('${a['estado']} · ${a['avance']}%'),
                                LinearProgressIndicator(
                                    value: (a['avance'] as num) / 100),
                                const SizedBox(height: 8),
                                Text(
                                    'Predecesoras: ${(a['dependencias'] as List).map((k) => todas.firstWhere((x) => x['clave'] == k)['nombre']).join(', ')}'),
                                if (a['bloqueada'] == true)
                                  const Text(
                                      'Predecesoras pendientes al corte'),
                                Text(
                                    '${a['dias_retraso']} días de retraso${a['inicio_retrasado'] == true ? ' · Inicio vencido' : ''}',
                                    style: TextStyle(
                                        color: a['dias_retraso'] > 0 ||
                                                a['inicio_retrasado'] == true
                                            ? Theme.of(context)
                                                .colorScheme
                                                .error
                                            : null)),
                              ]))),
                if (actividades.isEmpty)
                  const Padding(
                      padding: EdgeInsets.all(24),
                      child: Text('No hay actividades para estos filtros.')),
              ],
            ])));
  }
}

class CronogramaEditorScreen extends StatefulWidget {
  final int idObra;
  final Map<String, dynamic>? plan;
  final bool puedeCabecera;
  const CronogramaEditorScreen(
      {super.key,
      required this.idObra,
      this.plan,
      required this.puedeCabecera});
  @override
  State<CronogramaEditorScreen> createState() => _CronogramaEditorScreenState();
}

class _CronogramaEditorScreenState extends State<CronogramaEditorScreen> {
  final _form = GlobalKey<FormState>();
  final _api = CronogramaService();
  late Map<String, dynamic> _plan;
  bool _saving = false, _dirty = false;
  String _mensaje = '';
  @override
  void initState() {
    super.initState();
    _plan = widget.plan == null
        ? {
            'nombre': '',
            'descripcion': '',
            'fecha_inicio': _hoy(),
            'fecha_fin': _hoy(),
            'actividades': <dynamic>[]
          }
        : Map<String, dynamic>.from(jsonDecode(jsonEncode(widget.plan)));
  }

  List<dynamic> get _items => _plan['actividades'] as List;
  Future<void> _guardar() async {
    if (!_form.currentState!.validate()) return;
    setState(() {
      _saving = true;
      _mensaje = '';
    });
    try {
      final id = await _api.guardar(widget.idObra, _plan,
          soloPlanificacion: !widget.puedeCabecera);
      if (!mounted) return;
      setState(() {
        _saving = false;
        _dirty = false;
      });
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) Navigator.pop(context, id);
      });
    } catch (e) {
      if (mounted) {
        setState(() {
          _saving = false;
          _mensaje = _error(e);
        });
      }
    }
  }

  Future<void> _actividad([int? index, String tipo = 'ACTIVIDAD']) async {
    final item = index == null
        ? <String, dynamic>{
            'clave': 'a${DateTime.now().microsecondsSinceEpoch}',
            'nombre': '',
            'descripcion': '',
            'tipo': tipo,
            'fecha_inicio': _plan['fecha_inicio'],
            'fecha_fin': _plan['fecha_inicio'],
            'inicio_real': null,
            'fin_real': null,
            'avance': 0,
            'dependencias': <dynamic>[]
          }
        : Map<String, dynamic>.from(jsonDecode(jsonEncode(_items[index])));
    final result = await Navigator.push<Map<String, dynamic>>(
        context,
        MaterialPageRoute(
            builder: (_) => _ActividadEditor(item: item, otras: _items)));
    if (result != null && mounted) {
      setState(() {
        if (index == null) {
          _items.add(result);
        } else {
          _items[index] = result;
        }
        _dirty = true;
      });
    }
  }

  void _quitar(int index) {
    if (_items.any(
        (a) => (a['dependencias'] as List).contains(_items[index]['clave']))) {
      setState(() => _mensaje =
          'Quite primero las dependencias que apuntan a esta actividad.');
      return;
    }
    setState(() {
      _items.removeAt(index);
      _dirty = true;
    });
  }

  @override
  Widget build(BuildContext context) => PopScope(
      canPop: !_saving && !_dirty,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop || _saving) return;
        if (await _confirmar(context, '¿Descartar los cambios sin guardar?') &&
            mounted) {
          setState(() => _dirty = false);
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (mounted) Navigator.pop(context);
          });
        }
      },
      child: Scaffold(
          appBar: AppBar(
              title: Text(widget.plan == null
                  ? 'Nuevo cronograma'
                  : 'Editar planificación')),
          body: Form(
              key: _form,
              onChanged: () {
                if (!_dirty) setState(() => _dirty = true);
              },
              child: ListView(padding: const EdgeInsets.all(16), children: [
                if (_mensaje.isNotEmpty)
                  Text(_mensaje,
                      style: TextStyle(
                          color: Theme.of(context).colorScheme.error)),
                if (_saving) const LinearProgressIndicator(),
                _texto('Nombre', 'nombre',
                    obligatorio: true, editable: widget.puedeCabecera),
                _texto('Descripción', 'descripcion',
                    editable: widget.puedeCabecera),
                _fecha('Inicio previsto', 'fecha_inicio',
                    editable: widget.puedeCabecera),
                _fecha('Fin previsto', 'fecha_fin',
                    editable: widget.puedeCabecera),
                const SizedBox(height: 20),
                Text('Actividades e hitos',
                    style: Theme.of(context).textTheme.titleLarge),
                const Text(
                    'Dependencias fin-inicio. Los hitos ocupan un solo día. Los cambios se guardan juntos.'),
                for (var i = 0; i < _items.length; i++)
                  ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: Text('${i + 1}. ${_items[i]['nombre']}'),
                      subtitle: Text(
                          '${_items[i]['tipo']} · ${_items[i]['fecha_inicio']} → ${_items[i]['fecha_fin']}'),
                      onTap: _saving ? null : () => _actividad(i),
                      trailing: IconButton(
                          onPressed: _saving ? null : () => _quitar(i),
                          icon: const Icon(Icons.delete_outline),
                          tooltip: 'Quitar actividad')),
                Wrap(spacing: 8, children: [
                  OutlinedButton(
                      onPressed: _saving ? null : () => _actividad(),
                      child: const Text('+ Actividad')),
                  OutlinedButton(
                      onPressed:
                          _saving ? null : () => _actividad(null, 'HITO'),
                      child: const Text('+ Hito'))
                ]),
                const SizedBox(height: 24),
                FilledButton(
                    onPressed: _saving ? null : _guardar,
                    child:
                        Text(_saving ? 'Guardando…' : 'Guardar planificación')),
              ]))));
  Widget _texto(String label, String key,
          {bool obligatorio = false, bool editable = true}) =>
      Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: TextFormField(
              initialValue: _plan[key] ?? '',
              enabled: !_saving,
              readOnly: !editable,
              maxLength: key == 'nombre' ? 180 : 2000,
              decoration: InputDecoration(labelText: label),
              onChanged: (v) => _plan[key] = v,
              validator: (v) => obligatorio && (v ?? '').trim().isEmpty
                  ? 'Campo obligatorio'
                  : null));
  Widget _fecha(String label, String key, {bool editable = true}) => Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
          key: ValueKey('$key${_plan[key]}'),
          initialValue: _plan[key],
          readOnly: true,
          decoration: InputDecoration(
              labelText: label, suffixIcon: const Icon(Icons.calendar_today)),
          onTap: !editable || _saving
              ? null
              : () async {
                  final date = await showDatePicker(
                      context: context,
                      initialDate: DateTime.parse(_plan[key]),
                      firstDate: DateTime(2000),
                      lastDate: DateTime(2100));
                  if (date != null && mounted) {
                    setState(() {
                      _plan[key] = date.toIso8601String().substring(0, 10);
                      _dirty = true;
                    });
                  }
                }));
}

class _ActividadEditor extends StatefulWidget {
  final Map<String, dynamic> item;
  final List<dynamic> otras;
  const _ActividadEditor({required this.item, required this.otras});
  @override
  State<_ActividadEditor> createState() => _ActividadEditorState();
}

class _ActividadEditorState extends State<_ActividadEditor> {
  final _form = GlobalKey<FormState>();
  late final Map<String, dynamic> a = widget.item;
  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(title: Text(a['tipo'] == 'HITO' ? 'Hito' : 'Actividad')),
      body: Form(
          key: _form,
          child: ListView(padding: const EdgeInsets.all(16), children: [
            TextFormField(
                initialValue: a['nombre'],
                maxLength: 180,
                decoration: const InputDecoration(labelText: 'Nombre'),
                onChanged: (v) => a['nombre'] = v,
                validator: (v) =>
                    (v ?? '').trim().isEmpty ? 'Escribe un nombre' : null),
            TextFormField(
                initialValue: a['descripcion'],
                maxLength: 2000,
                decoration: const InputDecoration(labelText: 'Descripción'),
                onChanged: (v) => a['descripcion'] = v),
            if (a['tipo'] == 'HITO')
              _fecha('Fecha prevista', 'fecha_inicio')
            else ...[
              _fecha('Inicio previsto', 'fecha_inicio'),
              _fecha('Fin previsto', 'fecha_fin'),
            ],
            _fecha('Inicio real', 'inicio_real', real: true),
            _fecha('Fin real', 'fin_real', real: true),
            if (a['tipo'] == 'HITO')
              DropdownButtonFormField<int>(
                  initialValue: a['avance'],
                  decoration: const InputDecoration(labelText: 'Avance'),
                  items: const [
                    DropdownMenuItem(value: 0, child: Text('Pendiente · 0%')),
                    DropdownMenuItem(value: 100, child: Text('Cumplido · 100%'))
                  ],
                  onChanged: (v) => a['avance'] = v)
            else
              TextFormField(
                  initialValue: '${a['avance']}',
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Avance (%)'),
                  onChanged: (v) => a['avance'] = int.tryParse(v),
                  validator: (v) {
                    final n = int.tryParse(v ?? '');
                    return n == null || n < 0 || n > 100
                        ? 'Usa un entero entre 0 y 100'
                        : null;
                  }),
            const SizedBox(height: 16),
            const Text('Predecesoras · deben finalizar antes de comenzar'),
            for (final p in widget.otras)
              if (p['clave'] != a['clave'])
                CheckboxListTile(
                    contentPadding: EdgeInsets.zero,
                    title: Text(p['nombre']),
                    value: (a['dependencias'] as List).contains(p['clave']),
                    onChanged: (v) => setState(() {
                          final deps = a['dependencias'] as List;
                          if (v == true) {
                            deps.add(p['clave']);
                          } else {
                            deps.remove(p['clave']);
                          }
                        })),
            const Text(
                'Al completar: registra inicio real, fin real y avance 100%. Las fechas reales no pueden estar en el futuro.'),
            const SizedBox(height: 20),
            FilledButton(
                onPressed: () {
                  if (_form.currentState!.validate()) Navigator.pop(context, a);
                },
                child: const Text('Aceptar actividad')),
          ])));
  Widget _fecha(String label, String key,
          {bool real = false, bool editable = true}) =>
      Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: TextFormField(
              key: ValueKey('$key${a[key]}'),
              initialValue: a[key] ?? '',
              readOnly: true,
              decoration: InputDecoration(
                  labelText: label,
                  suffixIcon: real
                      ? IconButton(
                          icon: const Icon(Icons.clear),
                          onPressed: () => setState(() => a[key] = null))
                      : const Icon(Icons.calendar_today)),
              onTap: !editable
                  ? null
                  : () async {
                      final date = await showDatePicker(
                          context: context,
                          initialDate: DateTime.tryParse(a[key] ?? '') ??
                              DateTime.parse(_hoy()),
                          firstDate: DateTime(2000),
                          lastDate:
                              real ? DateTime.parse(_hoy()) : DateTime(2100));
                      if (date != null && mounted) {
                        setState(() {
                          a[key] = date.toIso8601String().substring(0, 10);
                          if (a['tipo'] == 'HITO' &&
                              (key == 'fecha_inicio' || key == 'fecha_fin')) {
                            a['fecha_inicio'] = a[key];
                            a['fecha_fin'] = a[key];
                          }
                        });
                      }
                    }));
}
