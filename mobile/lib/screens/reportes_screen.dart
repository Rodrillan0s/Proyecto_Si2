import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:record/record.dart';
import '../services/auth_provider.dart';
import '../services/reportes_service.dart';
import '../services/reportes_voice.dart';

class ReportesScreen extends StatefulWidget {
  const ReportesScreen({super.key});
  @override
  State<ReportesScreen> createState() => _ReportesScreenState();
}

class _ReportesScreenState extends State<ReportesScreen> {
  final _api = ReportesService();
  final _speech = ReportesVoice.speech;
  final _recorder = AudioRecorder();
  final _text = TextEditingController();
  final _query = TextEditingController();
  final _state = TextEditingController();
  final _category = TextEditingController();
  final _zone = TextEditingController(text: 'America/La_Paz');
  Map<String, dynamic> _catalog = {}, _response = {}, _execution = {};
  List<dynamic> _history = [], _recipients = [], _schedules = [], _deliveries = [];
  final Set<int> _receivers = {};
  String? _selected, _conversation, _error, _notice, _desde, _hasta;
  int? _company, _work;
  bool _initialized = false, _busy = false, _ai = false, _listening = false, _recording = false;
  int _generation = 0, _day = 1, _page = 1;
  String _format = 'pdf', _frequency = 'diaria', _period = 'fijo', _hour = '08:00', _identity = '';
  String? _priority;
  Timer? _voiceTimer;
  List<dynamic> get _reports => _catalog['reportes'] ?? [];
  List<dynamic> get _works => _catalog['obras'] ?? [];
  Map<String, dynamic> get _definition => Map<String, dynamic>.from(_reports.where((r) => r['id'] == _selected).firstOrNull ?? {});
  Map<String, dynamic>? get _result => _execution['resultado'] == null ? null : Map<String, dynamic>.from(_execution['resultado']);
  bool _can(String permission) => (_catalog['acciones'] as List? ?? []).contains(permission);

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final company = context.watch<AuthProvider>().idEmpresaActiva;
    if (!_initialized || company != _company) {
      _initialized = true; _company = company; _generation++;
      _catalog = {}; _response = {}; _execution = {}; _conversation = null; _receivers.clear();
      _history = []; _recipients = []; _schedules = []; _deliveries = [];
      _selected = null; _work = null; _priority = null; _desde = _hasta = null;
      _text.clear(); _query.clear(); _state.clear(); _category.clear();
      unawaited(_cancelVoice());
      unawaited(_load());
    }
  }

  @override
  void dispose() {
    _generation++; _voiceTimer?.cancel(); ReportesVoice.release(this); _recorder.dispose();
    _text.dispose(); _query.dispose(); _zone.dispose(); _state.dispose(); _category.dispose(); super.dispose();
  }

  Future<void> _load() async {
    final generation = _generation;
    try {
      final catalog = await _api.catalog(_company);
      if (!mounted || generation != _generation) return;
      setState(() { _catalog = catalog; _selected = _reports.isEmpty ? null : _reports.first['id']; _work = null; _error = null; });
      final history = await _api.get('ejecuciones', _company);
      final recipients = _can('Enviar_reportes') ? await _api.get('destinatarios', _company) : [];
      final schedules = _can('Programar_reportes') ? await _api.get('programaciones', _company) : [];
      if (mounted && generation == _generation) setState(() { _history = history; _recipients = recipients; _schedules = schedules; });
    } catch (e) { if (mounted && generation == _generation) setState(() => _error = _message(e)); }
  }

  String _message(Object e) {
    if (e is DioException && e.response?.data is Map && e.response?.data['detail'] is String) return e.response!.data['detail'];
    return 'No se pudo completar la operación. Revisa los filtros y la conexión.';
  }

  Future<void> _perform(Future<void> Function() action) async {
    if (_busy) return;
    setState(() { _busy = true; _error = null; _notice = null; });
    final generation = _generation;
    try { await action(); } catch (e) { if (mounted && generation == _generation) setState(() => _error = _message(e)); }
    finally { if (mounted) setState(() => _busy = false); }
  }

  Map<String, dynamic> _request() => {'reporte': _selected, 'filtros': {
    if (_work != null && _selected != 'stock') 'id_obra': _work,
    if (_definition['fechas'] == true && _desde != null) 'desde': _desde,
    if (_definition['fechas'] == true && _hasta != null) 'hasta': _hasta,
    if (_query.text.trim().isNotEmpty) 'q': _query.text.trim(),
    if (_selected?.startsWith('incidencias') == true && _priority != null) 'prioridad': _priority,
    if (_state.text.trim().isNotEmpty) 'estado': _state.text.trim(),
    if (_selected == 'stock' && int.tryParse(_category.text) != null) 'id_categoria': int.parse(_category.text),
  }};

  Future<void> _interpret() => _perform(() async {
    final generation = _generation;
    final response = await _api.interpret(_text.text, _company, _conversation, _ai);
    if (!mounted || generation != _generation) return;
    setState(() {
      _response = response; _conversation = response['conversacion'];
      if (response['solicitud'] != null) { final req = response['solicitud']; final filters = req['filtros'] ?? {};
        _selected = req['reporte']; _work = filters['id_obra']; _desde = filters['desde']; _hasta = filters['hasta']; _priority = filters['prioridad']; _query.text = filters['q'] ?? ''; _state.text = filters['estado'] ?? ''; _category.text = filters['id_categoria']?.toString() ?? ''; }
    });
  });

  Future<void> _generate() => _perform(() async {
    final generation = _generation;
    final execution = await _api.create(_request(), _company);
    final history = await _api.get('ejecuciones', _company);
    if (mounted && generation == _generation) setState(() { _execution = execution; _page = 1; _history = history; _identity = ReportesService.identity(); _deliveries = []; });
  });

  Future<void> _open(dynamic item) => _perform(() async {
    final generation = _generation;
    final execution = await _api.get('ejecuciones/${item['id']}');
    final deliveries = await _api.get('ejecuciones/${item['id']}/envios');
    if (mounted && generation == _generation) setState(() { _execution = Map<String,dynamic>.from(execution); _page = 1; _deliveries = deliveries; _identity = ReportesService.identity(); });
  });

  Future<void> _download(String format) => _perform(() async {
    final generation = _generation;
    final file = await _api.download(_execution['id'], format);
    if (!mounted || generation != _generation) return;
    final dir = await getTemporaryDirectory();
    final path = '${dir.path}/${ReportesService.identity()}-${file.name}';
    await File(path).writeAsBytes(file.bytes);
    try {
      if (!mounted) return;
      final box = context.findRenderObject() as RenderBox?;
      await Share.shareXFiles([XFile(path)], subject: _result?['titulo'], sharePositionOrigin: box == null ? null : box.localToGlobal(Offset.zero) & box.size);
    } finally { await File(path).delete(); }
  });

  Future<void> _send() => _perform(() async {
    final generation = _generation; final id = _execution['id'];
    await _api.send(id, _receivers.toList(), _format, _identity);
    final deliveries = await _api.get('ejecuciones/$id/envios');
    if (mounted && generation == _generation) setState(() { _deliveries = deliveries; _notice = 'Envío encolado para el worker.'; });
  });

  Future<void> _saveSchedule() => _perform(() async {
    await _api.post('programaciones', {'solicitud': _request(), 'destinatarios': _receivers.toList(), 'formatos': [_format],
      'frecuencia': _frequency, 'hora': _hour, 'zona': _zone.text.trim(), 'dia': _day, 'periodo': _period, 'habilitada': true}, _company);
    final schedules = await _api.get('programaciones', _company);
    if (mounted) setState(() { _schedules = schedules; _notice = 'Programación guardada.'; });
  });

  Future<void> _voice() async {
    if (_listening) { await _stopVoice(); return; }
    final generation = _generation;
    try {
      final available = await ReportesVoice.initialize(this, () { if (mounted) setState(() { _listening = false; _error = 'Revisa el permiso del micrófono o escribe tu solicitud.'; }); }, (status) { if (mounted && status == 'notListening') setState(() => _listening = false); });
      if (!mounted || generation != _generation) return;
      if (available) {
        final locales = await _speech.locales(); final spanish = locales.where((l) => l.localeId.startsWith('es')).firstOrNull;
        setState(() => _listening = true);
        await _speech.listen(listenOptions: SpeechListenOptions(localeId: spanish?.localeId, listenFor: const Duration(seconds: 60)), onResult: (r) { if (mounted && generation == _generation) setState(() => _text.text = r.recognizedWords); });
      } else {
        if (!await _recorder.hasPermission()) { if (mounted) setState(() => _error = 'Permiso del micrófono denegado. Puedes usar texto.'); return; }
        final dir = await getTemporaryDirectory();
        await _recorder.start(const RecordConfig(encoder: AudioEncoder.aacLc), path: '${dir.path}/reporte-${ReportesService.identity()}.m4a');
        if (!mounted || generation != _generation) { await _recorder.cancel(); return; }
        setState(() { _recording = true; _listening = true; });
        _voiceTimer = Timer(const Duration(seconds: 60), () => unawaited(_stopVoice()));
      }
    } catch (_) { if (mounted) setState(() => _error = 'No se pudo activar la voz. Puedes escribir tu solicitud.'); }
  }

  Future<void> _stopVoice() async {
    _voiceTimer?.cancel(); await _speech.stop();
    if (_recording) {
      final generation = _generation; final path = await _recorder.stop(); _recording = false;
      if (path != null) {
        try { if (mounted && generation == _generation) await _perform(() async { final text = await _api.transcribe(path, _company); if (mounted && generation == _generation) setState(() => _text.text = text); }); }
        finally { if (await File(path).exists()) await File(path).delete(); }
      }
    }
    if (mounted) setState(() => _listening = false);
  }

  Future<void> _cancelVoice() async {
    _voiceTimer?.cancel(); final wasRecording = _recording;
    _recording = false; _listening = false;
    await _speech.cancel();
    if (wasRecording) await _recorder.cancel();
  }

  Future<void> _date(bool start) async {
    final value = await showDatePicker(context: context, initialDate: DateTime.now(), firstDate: DateTime(2000), lastDate: DateTime(2100));
    if (value != null && mounted) setState(() { final date = value.toIso8601String().substring(0,10); if (start) { _desde = date; } else { _hasta = date; } });
  }

  Widget _section(String title, List<Widget> children) => Padding(padding: const EdgeInsets.symmetric(vertical: 12), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: Theme.of(context).textTheme.titleLarge), const SizedBox(height: 12), ...children]));
  Widget _button(String label, Future<void> Function() action, [bool enabled = true]) => Padding(padding: const EdgeInsets.only(right: 8, bottom: 8), child: OutlinedButton(onPressed: _busy || !enabled ? null : () => unawaited(action()), child: Text(label)));

  @override
  Widget build(BuildContext context) {
    final result = _result;
    final rows = result?['filas'] as List? ?? [];
    final pages = (rows.length / 50).ceil().clamp(1, 400);
    final visibleRows = rows.skip((_page - 1) * 50).take(50);
    return Scaffold(appBar: AppBar(title: const Text('Reportes'), actions: [IconButton(onPressed: _busy ? null : _load, icon: const Icon(Icons.refresh))]),
      body: ListView(padding: const EdgeInsets.all(20), children: [
        if (_busy) const LinearProgressIndicator(),
        if (_error != null) Padding(padding: const EdgeInsets.all(8), child: Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error))),
        if (_notice != null) Text(_notice!),
        if (_reports.isNotEmpty) _section('Solicitar por texto o voz', [
          TextField(controller: _text, maxLength: 2000, decoration: const InputDecoration(labelText: 'Ej.: incidencias críticas del mes pasado')),
          SwitchListTile(contentPadding: EdgeInsets.zero, title: const Text('Ayuda de IA para solicitudes complejas'), value: _ai, onChanged: (v) => setState(() => _ai = v)),
          Wrap(children: [_button(_listening ? 'Detener voz' : 'Micrófono', _voice), _button('Interpretar', _interpret)]),
          if (_response.isNotEmpty) Text(_response['mensaje'] ?? ''),
          Wrap(children: [for (final title in (_response['opciones'] as List? ?? [])) ActionChip(label: Text(title), onPressed: () { final report = _reports.where((r) => r['titulo'] == title).firstOrNull; if (report != null) setState(() { _selected = report['id']; _response = {}; }); }),
            for (final work in (_response['obras'] as List? ?? [])) ActionChip(label: Text(work['nombre']), onPressed: () => setState(() { _work = work['id_obra']; _response = {}; }))]),
        ]),
        if (_reports.isNotEmpty) _section('Preparar reporte', [
          DropdownButtonFormField<String>(initialValue: _selected, key: ValueKey('report-$_selected'), decoration: const InputDecoration(labelText: 'Reporte'), items: _reports.map((r) => DropdownMenuItem(value: r['id'].toString(), child: Text(r['titulo']))).toList(), onChanged: (v) => setState(() { _selected = v; _execution = {}; _desde = _hasta = null; _priority = null; _state.clear(); _category.clear(); _query.clear(); _period = 'fijo'; })),
          if (_selected != 'stock') DropdownButtonFormField<int>(initialValue: _work, key: ValueKey('work-$_work'), decoration: const InputDecoration(labelText: 'Obra'), items: [const DropdownMenuItem<int>(value: null, child: Text('Todas las obras accesibles')), ..._works.map((w) => DropdownMenuItem<int>(value: w['id_obra'], child: Text(w['nombre'])))], onChanged: (v) => setState(() => _work = v)),
          if (_definition['fechas'] == true) Wrap(children: [_button('Desde: ${_desde ?? 'sin filtro'}', () => _date(true)), _button('Hasta: ${_hasta ?? 'sin filtro'}', () => _date(false))]),
          TextField(controller: _query, decoration: const InputDecoration(labelText: 'Búsqueda opcional')),
          TextField(controller: _state, decoration: const InputDecoration(labelText: 'Estado opcional')),
          if (_selected == 'stock') TextField(controller: _category, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'ID categoría opcional')),
          if (_selected?.startsWith('incidencias') == true) DropdownButtonFormField<String>(initialValue: _priority, key: ValueKey('priority-$_priority'), decoration: const InputDecoration(labelText: 'Prioridad'), items: [const DropdownMenuItem(value: null, child: Text('Todas')), ...['BAJA','MEDIA','ALTA','CRITICA'].map((v) => DropdownMenuItem(value: v, child: Text(v)))], onChanged: (v) => setState(() => _priority = v)),
          Padding(padding: const EdgeInsets.symmetric(vertical: 12), child: Text(_definition['descripcion'] ?? '')),
          _button('Generar reporte', _generate, _selected != null && (_definition['requiere_obra'] != true || _work != null)),
        ]),
        if (result != null) _section(result['titulo'], [
          Text('Corte: ${result['corte']}'),
          for (final entry in (result['resumen'] as Map).entries) Padding(padding: const EdgeInsets.symmetric(vertical: 4), child: Text('${entry.key}: ${entry.value ?? 'Sin registro'}')),
          for (final note in result['advertencias']) Text(note),
          if (_can('Exportar_reportes')) Wrap(children: [_button('PDF · guardar/compartir', () => _download('pdf')), _button('Excel · guardar/compartir', () => _download('xlsx'))]),
          if ((result['columnas'] as List).isNotEmpty) SingleChildScrollView(scrollDirection: Axis.horizontal, child: DataTable(columns: [for (final c in result['columnas']) DataColumn(label: Text(c['titulo']))], rows: [for (final row in visibleRows) DataRow(cells: [for (final c in result['columnas']) DataCell(Text('${row[c['campo']] ?? '—'}'))])])),
          if (rows.isNotEmpty) Wrap(crossAxisAlignment: WrapCrossAlignment.center, children: [OutlinedButton(onPressed: _page <= 1 ? null : () => setState(() => _page--), child: const Text('Anterior')), Text(' Página $_page de $pages · ${rows.length} registros '), OutlinedButton(onPressed: _page >= pages ? null : () => setState(() => _page++), child: const Text('Siguiente')), const Text('Las exportaciones incluyen todo el detalle.')]),
          if ((result['filas'] as List).isEmpty) const Text('No hay registros para estos filtros.'),
          for (final recommendation in result['recomendaciones']) Text(recommendation.toString()),
        ]),
        if (_can('Enviar_reportes')) _section('Destinatarios y envío', [
          const Text('Cada destinatario recibe únicamente datos permitidos a su cuenta.'),
          for (final recipient in _recipients) CheckboxListTile(title: Text(recipient['nombre']), value: _receivers.contains(recipient['id_usuario']), onChanged: (v) => setState(() { if (v == true) { _receivers.add(recipient['id_usuario']); } else { _receivers.remove(recipient['id_usuario']); } })),
          DropdownButton<String>(value: _format, items: const [DropdownMenuItem(value: 'pdf', child: Text('PDF')), DropdownMenuItem(value: 'xlsx', child: Text('Excel'))], onChanged: (v) => setState(() => _format = v!)),
          _button('Enviar reporte manualmente', _send, _execution.isNotEmpty && _receivers.isNotEmpty),
          for (final delivery in _deliveries) Text('Destinatario ${delivery['id_usuario']}: ${delivery['estado']} ${delivery['error'] ?? ''}'),
        ]),
        if (_can('Programar_reportes')) _section('Programar envío', [
          DropdownButton<String>(value: _frequency, items: const [DropdownMenuItem(value: 'diaria', child: Text('Diaria')), DropdownMenuItem(value: 'semanal', child: Text('Semanal')), DropdownMenuItem(value: 'mensual', child: Text('Mensual'))], onChanged: (v) => setState(() { _frequency = v!; _day = 1; })),
          _button('Hora: $_hour', () async { final t = await showTimePicker(context: context, initialTime: const TimeOfDay(hour: 8, minute: 0)); if (mounted && t != null) setState(() => _hour = '${t.hour.toString().padLeft(2,'0')}:${t.minute.toString().padLeft(2,'0')}'); }),
          TextField(controller: _zone, decoration: const InputDecoration(labelText: 'Zona horaria IANA')),
          if (_frequency != 'diaria') DropdownButton<int>(value: _day, items: List.generate(_frequency == 'semanal' ? 7 : 31, (i) => DropdownMenuItem(value: i+1, child: Text('Día ${i+1}'))), onChanged: (v) => setState(() => _day = v!)),
          DropdownButton<String>(value: _period, items: [const DropdownMenuItem(value: 'fijo', child: Text('Filtros actuales')), if (_definition['fechas'] == true) ...const [DropdownMenuItem(value: 'ayer', child: Text('Ayer')), DropdownMenuItem(value: 'semana_anterior', child: Text('Semana anterior')), DropdownMenuItem(value: 'mes_anterior', child: Text('Mes anterior'))]], onChanged: (v) => setState(() => _period = v!)),
          const Text('Si el día mensual no existe, se usa el último día del mes.'),
          _button('Guardar programación', _saveSchedule, _receivers.isNotEmpty && _selected != null),
          for (final item in _schedules) Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text('${item['estado']} · próxima: ${item['next_run']} ${item['error'] ?? ''}'), Wrap(children: [
            _button(item['habilitada'] ? 'Pausar' : 'Activar', () => _perform(() async { await _api.pause(item['id'], !item['habilitada']); await _load(); })),
            _button('Ejecutar ahora', () => _perform(() async { await _api.post('programaciones/${item['id']}/ejecutar', {}); await _load(); })),
          ])]),
        ]),
        if (_reports.isNotEmpty) _section('Mis ejecuciones', [for (final item in _history) ListTile(contentPadding: EdgeInsets.zero, title: Text('${item['solicitud']['reporte']} · ${item['estado']}'), subtitle: Text('${item['created_at']} ${item['error'] ?? ''}'), onTap: _busy ? null : () => unawaited(_open(item)))]),
      ]));
  }
}
