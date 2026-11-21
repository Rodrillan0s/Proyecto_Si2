import 'dart:async';
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:path_provider/path_provider.dart';
import 'package:provider/provider.dart';
import 'package:record/record.dart';
import 'package:share_plus/share_plus.dart';
import 'package:speech_to_text/speech_to_text.dart';

import '../services/auth_provider.dart';
import '../services/reportes_service.dart';
import '../services/reportes_voice.dart';
import '../theme/app_theme.dart';
import 'asistente_screen.dart';

class ReportesScreen extends StatefulWidget {
  final String? initialExecutionId;
  final String? initialFamily;
  final int? initialObraId;

  const ReportesScreen({
    super.key,
    this.initialExecutionId,
    this.initialFamily,
    this.initialObraId,
  });

  @override
  State<ReportesScreen> createState() => _ReportesScreenState();
}

class _ReportesScreenState extends State<ReportesScreen> {
  final ReportesService _api = ReportesService();
  final SpeechToText _speech = ReportesVoice.speech;
  final AudioRecorder _recorder = AudioRecorder();

  final TextEditingController _textCtrl = TextEditingController();
  final TextEditingController _queryCtrl = TextEditingController();
  final TextEditingController _stateCtrl = TextEditingController();
  final TextEditingController _categoryCtrl = TextEditingController();
  final TextEditingController _customTitleCtrl = TextEditingController();
  final TextEditingController _zoneCtrl = TextEditingController(text: 'America/La_Paz');

  Map<String, dynamic> _catalog = {};
  Map<String, dynamic> _response = {};
  Map<String, dynamic> _execution = {};
  List<dynamic> _history = [];
  List<dynamic> _recipients = [];
  List<dynamic> _schedules = [];
  List<dynamic> _deliveries = [];
  final Set<int> _receivers = {};

  String _tab = 'generar'; // 'generar' | 'historial' | 'programaciones'
  String _family = '';
  String? _selected;
  String? _conversation;
  String? _error;
  String? _notice;
  String? _desde;
  String? _hasta;
  String _datePreset = 'todo';
  int? _company;
  int? _work;

  bool _initialized = false;
  bool _loadingCatalog = false;
  bool _busy = false;
  bool _listening = false;
  bool _recording = false;
  bool _showAdvancedFilters = false;
  bool _showPresentationOptions = false;
  bool _customColumns = false;

  String _orientation = 'horizontal';
  String _sortField = '';
  String _sortOrder = 'asc';
  List<String> _selectedColumns = [];

  int _generation = 0;
  int _day = 1;
  int _page = 1;
  String _format = 'pdf';
  String _frequency = 'diaria';
  String _period = 'fijo';
  String _hour = '08:00';
  String _identity = '';
  String? _priority;
  String? _pendingExecutionId;
  Timer? _voiceTimer;

  List<Map<String, dynamic>> get _allReports =>
      (_catalog['reportes'] as List? ?? [])
          .whereType<Map>()
          .map((e) => Map<String, dynamic>.from(e))
          .toList();

  List<Map<String, dynamic>> get _filteredReports {
    if (_family.isEmpty || !reportFamilies.containsKey(_family)) {
      return _allReports;
    }
    final allowed = reportFamilies[_family]!;
    return _allReports.where((r) => allowed.contains(r['id']?.toString())).toList();
  }

  List<Map<String, dynamic>> get _works =>
      (_catalog['obras'] as List? ?? [])
          .whereType<Map>()
          .map((e) => Map<String, dynamic>.from(e))
          .toList();

  Map<String, dynamic> get _definition =>
      _allReports.where((r) => r['id']?.toString() == _selected).firstOrNull ?? {};

  Map<String, dynamic>? get _result =>
      _execution['resultado'] is Map
          ? Map<String, dynamic>.from(_execution['resultado'] as Map)
          : null;

  bool _can(String permission) =>
      (_catalog['acciones'] as List? ?? []).contains(permission);

  List<Map<String, dynamic>> get _columnChoices {
    final defCampos = _definition['campos'] as List?;
    if (defCampos != null && defCampos.isNotEmpty) {
      return defCampos.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
    }
    final res = _result;
    if (res != null && (res['solicitud'] as Map?)?['reporte'] == _selected) {
      final disp = (res['columnas_disponibles'] ?? res['columnas']) as List? ?? [];
      return disp.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
    }
    return [];
  }

  @override
  void initState() {
    super.initState();
    _family = widget.initialFamily ?? '';
    _pendingExecutionId = widget.initialExecutionId;
    _work = widget.initialObraId;
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final auth = context.watch<AuthProvider>();
    final company = auth.idEmpresaActiva;
    if (!_initialized || company != _company) {
      _initialized = true;
      _company = company;
      _generation++;
      _catalog = {};
      _response = {};
      _execution = {};
      _conversation = null;
      _receivers.clear();
      _history = [];
      _recipients = [];
      _schedules = [];
      _deliveries = [];
      _selected = null;
      if (widget.initialObraId == null) _work = null;
      _priority = null;
      _desde = _hasta = null;
      _datePreset = 'todo';
      _textCtrl.clear();
      _queryCtrl.clear();
      _stateCtrl.clear();
      _categoryCtrl.clear();
      _resetPresentation();
      unawaited(_cancelVoice());
      unawaited(_load());
    }
  }

  @override
  void dispose() {
    _generation++;
    _voiceTimer?.cancel();
    ReportesVoice.release(this);
    _recorder.dispose();
    _textCtrl.dispose();
    _queryCtrl.dispose();
    _zoneCtrl.dispose();
    _stateCtrl.dispose();
    _categoryCtrl.dispose();
    _customTitleCtrl.dispose();
    super.dispose();
  }

  void _resetPresentation() {
    _customTitleCtrl.clear();
    _orientation = 'horizontal';
    _sortField = '';
    _sortOrder = 'asc';
    _customColumns = false;
    _selectedColumns = [];
  }

  void _applyDatePreset(String preset) {
    final now = DateTime.now();
    DateTime start = DateTime(now.year, now.month, now.day);
    DateTime end = DateTime(now.year, now.month, now.day);

    setState(() {
      _datePreset = preset;
      if (preset == 'todo') {
        _desde = null;
        _hasta = null;
        return;
      }
      if (preset == 'manual') return;
      if (preset == '7') {
        start = start.subtract(const Duration(days: 6));
      } else if (preset == '30') {
        start = start.subtract(const Duration(days: 29));
      } else if (preset == 'mes') {
        start = DateTime(now.year, now.month, 1);
      } else if (preset == 'anterior') {
        start = DateTime(now.year, now.month - 1, 1);
        end = DateTime(now.year, now.month, 0);
      }
      _desde = _isoDate(start);
      _hasta = _isoDate(end);
    });
  }

  String _isoDate(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  Future<void> _load() async {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    if (auth.esAdminGlobal && _company == null) return;

    final generation = _generation;
    setState(() {
      _loadingCatalog = true;
      _error = null;
    });

    try {
      final catalog = await _api.catalog(_company);
      if (!mounted || generation != _generation) return;

      setState(() {
        _catalog = catalog;
        final options = _filteredReports;
        if (_selected == null || !options.any((r) => r['id']?.toString() == _selected)) {
          _selected = options.isNotEmpty
              ? options.first['id']?.toString()
              : (_allReports.isNotEmpty ? _allReports.first['id']?.toString() : null);
        }
        if (_work != null && !_works.any((w) => w['id_obra'] == _work)) {
          _work = null;
        }
        _loadingCatalog = false;
      });

      final history = await _api.history(_company);
      final recipients = _can('Enviar_reportes') ? await _api.recipients(_company) : [];
      final schedules = _can('Programar_reportes') ? await _api.schedules(_company) : [];

      if (mounted && generation == _generation) {
        setState(() {
          _history = history;
          _recipients = recipients;
          _schedules = schedules;
        });
      }

      if (_pendingExecutionId != null && _pendingExecutionId!.isNotEmpty) {
        final execId = _pendingExecutionId!;
        _pendingExecutionId = null;
        await _openById(execId);
      }
    } catch (e) {
      if (mounted && generation == _generation) {
        setState(() {
          _loadingCatalog = false;
          _error = _message(e);
        });
      }
    }
  }

  String _message(Object e) {
    if (e is DioException && e.response?.data is Map && e.response?.data['detail'] is String) {
      return e.response!.data['detail'].toString();
    }
    return e.toString().replaceAll('Exception: ', '');
  }

  Future<void> _perform(Future<void> Function() action) async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _error = null;
      _notice = null;
    });
    final generation = _generation;
    try {
      await action();
    } catch (e) {
      if (mounted && generation == _generation) {
        setState(() => _error = _message(e));
      }
    } finally {
      if (mounted && generation == _generation) {
        setState(() => _busy = false);
      }
    }
  }

  String? get _validationMessage {
    if (_selected == null || _definition.isEmpty) {
      return 'Selecciona un tipo de reporte.';
    }
    if (_definition['requiere_obra'] == true && _work == null) {
      return 'Este reporte requiere seleccionar una obra específica.';
    }
    if (_definition['fechas'] == true &&
        _desde != null &&
        _hasta != null &&
        _desde!.compareTo(_hasta!) > 0) {
      return 'La fecha inicial debe ser anterior o igual a la fecha final.';
    }
    if (_customColumns && _selectedColumns.isEmpty) {
      return 'Selecciona al menos una columna personalizada.';
    }
    return null;
  }

  Map<String, dynamic> _buildRequestPayload() {
    final filtros = <String, dynamic>{
      if (_work != null && _selected != 'stock') 'id_obra': _work,
      if (_definition['fechas'] == true && _desde != null && _desde!.isNotEmpty) 'desde': _desde,
      if (_definition['fechas'] == true && _hasta != null && _hasta!.isNotEmpty) 'hasta': _hasta,
      if (_queryCtrl.text.trim().isNotEmpty) 'q': _queryCtrl.text.trim(),
      if (_selected == 'incidencias_criticas')
        'prioridad': 'CRITICA'
      else if (_selected == 'incidencias' && _priority != null && _priority!.isNotEmpty)
        'prioridad': _priority,
      if (_stateCtrl.text.trim().isNotEmpty) 'estado': _stateCtrl.text.trim(),
      if (_selected == 'stock' && int.tryParse(_categoryCtrl.text.trim()) != null)
        'id_categoria': int.parse(_categoryCtrl.text.trim()),
    };

    final presentacion = <String, dynamic>{};
    if (_customTitleCtrl.text.trim().isNotEmpty) {
      presentacion['titulo'] = _customTitleCtrl.text.trim();
    }
    if (_orientation != 'horizontal') {
      presentacion['orientacion'] = _orientation;
    }
    if (_customColumns && _selectedColumns.isNotEmpty) {
      presentacion['columnas'] = List<String>.from(_selectedColumns);
    }
    if (_sortField.isNotEmpty) {
      presentacion['ordenar_por'] = _sortField;
      presentacion['orden'] = _sortOrder;
    }

    return {
      'reporte': _selected,
      'filtros': filtros,
      if (presentacion.isNotEmpty) 'presentacion': presentacion,
    };
  }

  void _applyRequestFromData(Map<String, dynamic> req) {
    _resetPresentation();
    final pres = req['presentacion'] is Map
        ? Map<String, dynamic>.from(req['presentacion'] as Map)
        : <String, dynamic>{};
    _customTitleCtrl.text = pres['titulo']?.toString() ?? '';
    _orientation = pres['orientacion']?.toString() ?? 'horizontal';
    _sortField = pres['ordenar_por']?.toString() ?? '';
    _sortOrder = pres['orden']?.toString() ?? 'asc';
    final cols = (pres['columnas'] as List? ?? []).map((e) => e.toString()).toList();
    _selectedColumns = cols;
    _customColumns = cols.isNotEmpty;

    _selected = req['reporte']?.toString() ?? _selected;
    final filters = req['filtros'] is Map
        ? Map<String, dynamic>.from(req['filtros'] as Map)
        : <String, dynamic>{};
    _work = filters['id_obra'] is int
        ? filters['id_obra'] as int
        : int.tryParse(filters['id_obra']?.toString() ?? '');
    _desde = filters['desde']?.toString();
    _hasta = filters['hasta']?.toString();
    _datePreset = (_desde != null || _hasta != null) ? 'manual' : 'todo';
    _priority = filters['prioridad']?.toString();
    _queryCtrl.text = filters['q']?.toString() ?? '';
    _stateCtrl.text = filters['estado']?.toString() ?? '';
    _categoryCtrl.text = filters['id_categoria']?.toString() ?? '';
    _period = 'fijo';
  }

  Future<void> _interpret() => _perform(() async {
        if (_textCtrl.text.trim().isEmpty) return;
        final generation = _generation;
        final response = await _api.interpret(
          _textCtrl.text.trim(),
          _company,
          _conversation,
          _can('Usar_ia'),
        );
        if (!mounted || generation != _generation) return;
        setState(() {
          _response = response;
          _conversation = response['conversacion']?.toString();
          if (response['solicitud'] is Map) {
            _applyRequestFromData(Map<String, dynamic>.from(response['solicitud'] as Map));
          }
        });
      });

  Future<void> _generate() => _perform(() async {
        final val = _validationMessage;
        if (val != null) {
          throw Exception(val);
        }
        final generation = _generation;
        final execution = await _api.create(_buildRequestPayload(), _company);
        final history = await _api.history(_company);
        if (mounted && generation == _generation) {
          setState(() {
            _execution = execution;
            _page = 1;
            _history = history;
            _identity = ReportesService.identity();
            _deliveries = [];
            _response = {};
          });
        }
      });

  Future<void> _openById(String id) => _perform(() async {
        final generation = _generation;
        final execution = await _api.execution(id);
        final deliveries = _can('Enviar_reportes') ? await _api.deliveries(id) : [];
        if (mounted && generation == _generation) {
          setState(() {
            _execution = execution;
            _page = 1;
            _tab = 'generar';
            _deliveries = deliveries;
            _identity = ReportesService.identity();
            final req = (execution['resultado'] as Map?)?['solicitud'] ?? execution['solicitud'];
            if (req is Map) {
              _applyRequestFromData(Map<String, dynamic>.from(req));
            }
          });
        }
      });

  Future<void> _download(String format) => _perform(() async {
        final id = _execution['id']?.toString();
        if (id == null || id.isEmpty) return;
        final generation = _generation;
        final file = await _api.download(id, format);
        if (!mounted || generation != _generation) return;
        final dir = await getTemporaryDirectory();
        final path = '${dir.path}/${ReportesService.identity()}-${file.name}';
        await File(path).writeAsBytes(file.bytes);
        try {
          if (!mounted) return;
          final box = context.findRenderObject() as RenderBox?;
          await Share.shareXFiles(
            [XFile(path)],
            subject: _result?['titulo']?.toString(),
            sharePositionOrigin:
                box == null ? null : box.localToGlobal(Offset.zero) & box.size,
          );
        } finally {
          if (await File(path).exists()) {
            await File(path).delete();
          }
        }
      });

  Future<void> _send() => _perform(() async {
        final generation = _generation;
        final id = _execution['id']?.toString();
        if (id == null || id.isEmpty || _receivers.isEmpty) return;
        await _api.send(id, _receivers.toList(), _format, _identity);
        final deliveries = await _api.deliveries(id);
        if (mounted && generation == _generation) {
          setState(() {
            _deliveries = deliveries;
            _notice = 'Solicitud de envío registrada en la cola de distribución.';
          });
        }
      });

  Future<void> _saveSchedule() => _perform(() async {
        final val = _validationMessage;
        if (val != null) throw Exception(val);
        if (_receivers.isEmpty) {
          throw Exception('Selecciona al menos un destinatario para programar el envío.');
        }
        await _api.post(
          'programaciones',
          {
            'solicitud': _buildRequestPayload(),
            'destinatarios': _receivers.toList(),
            'formatos': [_format],
            'frecuencia': _frequency,
            'hora': _hour,
            'zona': _zoneCtrl.text.trim(),
            'dia': _day,
            'periodo': _period,
            'habilitada': true,
          },
          _company,
        );
        final schedules = await _api.schedules(_company);
        if (mounted) {
          setState(() {
            _schedules = schedules;
            _notice = 'Programación guardada correctamente.';
            _tab = 'programaciones';
          });
        }
      });

  Future<void> _voice() async {
    if (_listening) {
      await _stopVoice();
      return;
    }
    final generation = _generation;
    try {
      final available = await ReportesVoice.initialize(
        this,
        () {
          if (mounted) {
            setState(() {
              _listening = false;
              _error = 'Revisa el permiso del micrófono o escribe tu solicitud.';
            });
          }
        },
        (status) {
          if (mounted && status == 'notListening') {
            setState(() => _listening = false);
          }
        },
      );
      if (!mounted || generation != _generation) return;
      if (available) {
        final locales = await _speech.locales();
        final spanish = locales.where((l) => l.localeId.startsWith('es')).firstOrNull;
        setState(() => _listening = true);
        await _speech.listen(
          listenOptions: SpeechListenOptions(
            localeId: spanish?.localeId,
            listenFor: const Duration(seconds: 60),
          ),
          onResult: (r) {
            if (mounted && generation == _generation) {
              setState(() => _textCtrl.text = r.recognizedWords);
            }
          },
        );
      } else {
        if (!await _recorder.hasPermission()) {
          if (mounted) {
            setState(() => _error = 'Permiso del micrófono denegado. Puedes usar texto.');
          }
          return;
        }
        final dir = await getTemporaryDirectory();
        await _recorder.start(
          const RecordConfig(encoder: AudioEncoder.aacLc),
          path: '${dir.path}/reporte-${ReportesService.identity()}.m4a',
        );
        if (!mounted || generation != _generation) {
          await _recorder.cancel();
          return;
        }
        setState(() {
          _recording = true;
          _listening = true;
        });
        _voiceTimer = Timer(const Duration(seconds: 60), () => unawaited(_stopVoice()));
      }
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'No se pudo activar la voz. Puedes escribir tu solicitud.');
      }
    }
  }

  Future<void> _stopVoice() async {
    _voiceTimer?.cancel();
    await _speech.stop();
    if (_recording) {
      final generation = _generation;
      final path = await _recorder.stop();
      _recording = false;
      if (path != null) {
        try {
          if (mounted && generation == _generation) {
            await _perform(() async {
              final text = await _api.transcribe(path, _company);
              if (mounted && generation == _generation) {
                setState(() => _textCtrl.text = text);
              }
            });
          }
        } finally {
          if (await File(path).exists()) await File(path).delete();
        }
      }
    }
    if (mounted) setState(() => _listening = false);
  }

  Future<void> _cancelVoice() async {
    _voiceTimer?.cancel();
    final wasRecording = _recording;
    _recording = false;
    _listening = false;
    await _speech.cancel();
    if (wasRecording) await _recorder.cancel();
  }

  Future<void> _pickDate(bool isStart) async {
    final value = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
    );
    if (value != null && mounted) {
      setState(() {
        final date = _isoDate(value);
        _datePreset = 'manual';
        if (isStart) {
          _desde = date;
        } else {
          _hasta = date;
        }
      });
    }
  }

  String _formatDisplayValue(dynamic value) {
    if (value == null) return '—';
    if (value is Map) {
      return value.entries
          .map((e) => '${e.key.toString().replaceAll('_', ' ')}: ${_formatDisplayValue(e.value)}')
          .join(' · ');
    }
    return value.toString();
  }

  String _statusLabel(String? raw) {
    final labels = {
      'LISTO': 'Listo',
      'COMPLETADO': 'Completado',
      'PENDIENTE': 'Pendiente',
      'PROCESANDO': 'Procesando',
      'GENERANDO': 'Generando',
      'ENVIANDO': 'Enviando',
      'ACEPTADO': 'Aceptado',
      'FALLIDO': 'Falló',
      'INCIERTO': 'Incierto',
      'ACTIVA': 'Activa',
      'PAUSADA': 'Pausada',
    };
    return labels[raw] ?? (raw?.replaceAll('_', ' ') ?? '—');
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
    final subColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);
    final needsCompany = auth.esAdminGlobal && _company == null;

    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC),
      appBar: AppBar(
        titleSpacing: 16,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Reportes y Analítica',
              style: GoogleFonts.inter(
                fontSize: 16,
                fontWeight: FontWeight.w800,
                color: titleColor,
              ),
            ),
            Text(
              needsCompany
                  ? 'Selecciona una empresa activa'
                  : (auth.empresaActivaNombre ?? auth.nombreEmpresa ?? 'Empresa activa'),
              style: GoogleFonts.inter(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: AppTheme.primary,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'Consultar al Asistente',
            icon: const Icon(Icons.auto_awesome_rounded, color: AppTheme.primary),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => AsistenteScreen(
                    idObraContexto: _work,
                    initialMode: 'admin',
                  ),
                ),
              );
            },
          ),
          IconButton(
            tooltip: 'Actualizar catálogo',
            onPressed: (_busy || _loadingCatalog || needsCompany) ? null : _load,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: SafeArea(
        child: needsCompany
            ? Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: cardBg,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: borderColor),
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.business_rounded, size: 44, color: AppTheme.primary),
                        const SizedBox(height: 12),
                        Text(
                          'Selecciona una empresa',
                          style: GoogleFonts.inter(
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                            color: titleColor,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'Para generar o consultar reportes en modo Administrador Global, selecciona primero una constructora en el panel de Inicio.',
                          textAlign: TextAlign.center,
                          style: GoogleFonts.inter(fontSize: 12.5, color: subColor, height: 1.4),
                        ),
                      ],
                    ),
                  ),
                ),
              )
            : Column(
                children: [
                  if (_busy || _loadingCatalog)
                    const LinearProgressIndicator(color: AppTheme.primary, minHeight: 2.5),

                  // Selector de pestañas (Generar | Historial | Programaciones)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    decoration: BoxDecoration(
                      color: cardBg,
                      border: Border(bottom: BorderSide(color: borderColor)),
                    ),
                    child: Row(
                      children: [
                        _buildTabChip('generar', 'Generar reporte', isDark),
                        const SizedBox(width: 8),
                        _buildTabChip('historial', 'Historial (${_history.length})', isDark),
                        if (_can('Programar_reportes')) ...[
                          const SizedBox(width: 8),
                          _buildTabChip(
                            'programaciones',
                            'Programados (${_schedules.length})',
                            isDark,
                          ),
                        ],
                      ],
                    ),
                  ),

                  if (_error != null)
                    Container(
                      width: double.infinity,
                      margin: const EdgeInsets.fromLTRB(16, 10, 16, 0),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppTheme.errorBg,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: AppTheme.error.withValues(alpha: 0.35)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.error_outline_rounded, color: AppTheme.error, size: 18),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              _error!,
                              style: GoogleFonts.inter(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: AppTheme.error,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),

                  if (_notice != null)
                    Container(
                      width: double.infinity,
                      margin: const EdgeInsets.fromLTRB(16, 10, 16, 0),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppTheme.successBg,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: AppTheme.success.withValues(alpha: 0.35)),
                      ),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.check_circle_outline_rounded,
                            color: AppTheme.success,
                            size: 18,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              _notice!,
                              style: GoogleFonts.inter(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: AppTheme.success,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),

                  Expanded(
                    child: _tab == 'generar'
                        ? _buildGenerarTab(isDark, cardBg, borderColor, titleColor, subColor)
                        : _tab == 'historial'
                            ? _buildHistorialTab(isDark, cardBg, borderColor, titleColor, subColor)
                            : _buildProgramacionesTab(
                                isDark,
                                cardBg,
                                borderColor,
                                titleColor,
                                subColor,
                              ),
                  ),
                ],
              ),
      ),
    );
  }

  Widget _buildTabChip(String tabId, String label, bool isDark) {
    final active = _tab == tabId;
    return Expanded(
      child: InkWell(
        onTap: () => setState(() => _tab = tabId),
        borderRadius: BorderRadius.circular(8),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 6),
          decoration: BoxDecoration(
            color: active
                ? AppTheme.primary
                : (isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9)),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(
            label,
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: GoogleFonts.inter(
              fontSize: 11.5,
              fontWeight: active ? FontWeight.w800 : FontWeight.w600,
              color: active
                  ? Colors.white
                  : (isDark ? const Color(0xFFCBD5E1) : const Color(0xFF475569)),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildGenerarTab(
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    final soloLectura = (_catalog['suscripcion'] as Map?)?['solo_lectura'] == true;
    final options = _filteredReports;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (soloLectura)
          Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppTheme.warningBg,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(
              'Tu empresa está en modo de solo lectura. Puedes consultar los reportes existentes en Historial.',
              style: GoogleFonts.inter(fontSize: 12, color: AppTheme.warning, fontWeight: FontWeight.w600),
            ),
          ),

        // 1. Preparar filtros escribiendo o por voz
        if (_allReports.isNotEmpty && _can('Generar_reportes'))
          Container(
            margin: const EdgeInsets.only(bottom: 16),
            padding: const EdgeInsets.all(14),
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
                    const Icon(Icons.auto_awesome_rounded, size: 16, color: AppTheme.primary),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        'PREPARAR FILTROS POR TEXTO O VOZ',
                        style: GoogleFonts.inter(
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.4,
                          color: AppTheme.primary,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: _textCtrl,
                  maxLines: 2,
                  minLines: 1,
                  style: GoogleFonts.inter(fontSize: 13),
                  decoration: InputDecoration(
                    hintText: 'Ej.: obras con más déficit, stock agotado o incidencias críticas...',
                    hintStyle: GoogleFonts.inter(fontSize: 12, color: subColor),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  ),
                ),
                const SizedBox(height: 10),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    if (_can('Usar_ia'))
                      OutlinedButton.icon(
                        onPressed: _busy ? null : _voice,
                        icon: Icon(
                          _listening ? Icons.stop_circle_outlined : Icons.mic_none_rounded,
                          size: 16,
                          color: _listening ? AppTheme.error : AppTheme.primary,
                        ),
                        label: Text(_listening ? 'Detener voz' : 'Dictar'),
                      ),
                    ElevatedButton.icon(
                      onPressed: _busy ? null : _interpret,
                      icon: const Icon(Icons.tune_rounded, size: 16),
                      label: const Text('Preparar filtros'),
                    ),
                  ],
                ),
                if (_response.isNotEmpty) ...[
                  const SizedBox(height: 10),
                  Text(
                    _response['mensaje']?.toString() ?? '',
                    style: GoogleFonts.inter(fontSize: 12.5, color: titleColor),
                  ),
                  const SizedBox(height: 6),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: [
                      for (final title in (_response['opciones'] as List? ?? []))
                        ActionChip(
                          label: Text(title.toString(), style: const TextStyle(fontSize: 11.5)),
                          onPressed: () {
                            final report = _allReports
                                .where((r) => r['titulo'] == title)
                                .firstOrNull;
                            if (report != null) {
                              setState(() {
                                _family = '';
                                _selected = report['id']?.toString();
                                _response = {};
                              });
                            }
                          },
                        ),
                      for (final work in (_response['obras'] as List? ?? []))
                        if (work is Map)
                          ActionChip(
                            label: Text(
                              work['nombre']?.toString() ?? 'Obra',
                              style: const TextStyle(fontSize: 11.5),
                            ),
                            onPressed: () => setState(() {
                              _work = work['id_obra'] as int?;
                              _response = {};
                            }),
                          ),
                    ],
                  ),
                ],
              ],
            ),
          ),

        // 2. Selección de Familia, Tipo de Reporte y Filtros
        if (_allReports.isNotEmpty && _can('Generar_reportes'))
          Container(
            margin: const EdgeInsets.only(bottom: 16),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: cardBg,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: borderColor),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'CONFIGURAR REPORTE',
                  style: GoogleFonts.inter(
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.4,
                    color: subColor,
                  ),
                ),
                const SizedBox(height: 10),

                // Familias de reportes
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: reportFamilyLabels.entries.map((entry) {
                      final active = _family == entry.key;
                      return Padding(
                        padding: const EdgeInsets.only(right: 6),
                        child: ChoiceChip(
                          label: Text(entry.value),
                          selected: active,
                          selectedColor: AppTheme.primary.withValues(alpha: 0.2),
                          labelStyle: GoogleFonts.inter(
                            fontSize: 11.5,
                            fontWeight: active ? FontWeight.w800 : FontWeight.w600,
                            color: active ? AppTheme.primary : titleColor,
                          ),
                          onSelected: (_) {
                            setState(() {
                              _family = entry.key;
                              final newOptions = _filteredReports;
                              if (newOptions.isNotEmpty &&
                                  !newOptions.any((r) => r['id']?.toString() == _selected)) {
                                _selected = newOptions.first['id']?.toString();
                              }
                            });
                          },
                        ),
                      );
                    }).toList(),
                  ),
                ),
                const SizedBox(height: 12),

                // Dropdown Tipo de reporte
                DropdownButtonFormField<String>(
                  initialValue: options.any((r) => r['id']?.toString() == _selected)
                      ? _selected
                      : (options.isNotEmpty ? options.first['id']?.toString() : null),
                  key: ValueKey('report-$_family-$_selected'),
                  isExpanded: true,
                  decoration: const InputDecoration(labelText: 'Tipo de reporte'),
                  items: options
                      .map(
                        (r) => DropdownMenuItem(
                          value: r['id'].toString(),
                          child: Text(
                            r['titulo']?.toString() ?? r['id'].toString(),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      )
                      .toList(),
                  onChanged: (v) => setState(() {
                    _selected = v;
                    _execution = {};
                    _desde = _hasta = null;
                    _datePreset = 'todo';
                    _priority = null;
                    _stateCtrl.clear();
                    _categoryCtrl.clear();
                    _queryCtrl.clear();
                    _resetPresentation();
                  }),
                ),
                if ((_definition['descripcion']?.toString() ?? '').isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    _definition['descripcion'].toString(),
                    style: GoogleFonts.inter(fontSize: 12, color: subColor, height: 1.35),
                  ),
                ],
                const SizedBox(height: 12),

                // Dropdown Obra
                if (_selected != 'stock')
                  DropdownButtonFormField<int?>(
                    initialValue: _works.any((w) => w['id_obra'] == _work) ? _work : null,
                    key: ValueKey('work-$_work'),
                    isExpanded: true,
                    decoration: InputDecoration(
                      labelText: _definition['requiere_obra'] == true
                          ? 'Obra (Obligatoria *)'
                          : 'Obra',
                    ),
                    items: [
                      DropdownMenuItem<int?>(
                        value: null,
                        child: Text(
                          _definition['requiere_obra'] == true
                              ? 'Selecciona una obra...'
                              : 'Todas las obras accesibles',
                        ),
                      ),
                      ..._works.map(
                        (w) => DropdownMenuItem<int?>(
                          value: w['id_obra'] as int?,
                          child: Text(
                            w['nombre']?.toString() ?? 'Obra',
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ),
                    ],
                    onChanged: (v) => setState(() => _work = v),
                  ),

                // Rango de fechas y período rápido
                if (_definition['fechas'] == true) ...[
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: _datePreset,
                    key: ValueKey('preset-$_datePreset'),
                    decoration: const InputDecoration(labelText: 'Período'),
                    items: const [
                      DropdownMenuItem(value: 'todo', child: Text('Todas las fechas')),
                      DropdownMenuItem(value: 'hoy', child: Text('Hoy')),
                      DropdownMenuItem(value: '7', child: Text('Últimos 7 días')),
                      DropdownMenuItem(value: '30', child: Text('Últimos 30 días')),
                      DropdownMenuItem(value: 'mes', child: Text('Este mes')),
                      DropdownMenuItem(value: 'anterior', child: Text('Mes anterior')),
                      DropdownMenuItem(value: 'manual', child: Text('Rango personalizado')),
                    ],
                    onChanged: (v) {
                      if (v != null) _applyDatePreset(v);
                    },
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _busy ? null : () => _pickDate(true),
                          icon: const Icon(Icons.calendar_today_rounded, size: 14),
                          label: Text(
                            'Desde: ${_desde ?? "inicio"}',
                            style: const TextStyle(fontSize: 11.5),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _busy ? null : () => _pickDate(false),
                          icon: const Icon(Icons.event_rounded, size: 14),
                          label: Text(
                            'Hasta: ${_hasta ?? "hoy"}',
                            style: const TextStyle(fontSize: 11.5),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],

                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  children: [
                    TextButton.icon(
                      onPressed: () =>
                          setState(() => _showAdvancedFilters = !_showAdvancedFilters),
                      icon: Icon(
                        _showAdvancedFilters
                            ? Icons.expand_less_rounded
                            : Icons.expand_more_rounded,
                        size: 18,
                      ),
                      label: Text(_showAdvancedFilters ? 'Ocultar filtros' : 'Más filtros'),
                    ),
                    TextButton.icon(
                      onPressed: () => setState(
                        () => _showPresentationOptions = !_showPresentationOptions,
                      ),
                      icon: const Icon(Icons.auto_awesome_mosaic_outlined, size: 16),
                      label: Text(
                        _showPresentationOptions
                            ? 'Ocultar presentación'
                            : 'Personalizar presentación',
                      ),
                    ),
                  ],
                ),

                if (_showAdvancedFilters) ...[
                  const SizedBox(height: 8),
                  TextField(
                    controller: _queryCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Búsqueda opcional (nombre o código)',
                    ),
                  ),
                  const SizedBox(height: 10),
                  TextField(
                    controller: _stateCtrl,
                    decoration: const InputDecoration(labelText: 'Estado opcional'),
                  ),
                  if (_selected == 'stock') ...[
                    const SizedBox(height: 10),
                    TextField(
                      controller: _categoryCtrl,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(labelText: 'ID categoría opcional'),
                    ),
                  ],
                  if (_selected == 'incidencias') ...[
                    const SizedBox(height: 10),
                    DropdownButtonFormField<String?>(
                      initialValue: _priority,
                      key: ValueKey('priority-$_priority'),
                      decoration: const InputDecoration(labelText: 'Prioridad'),
                      items: [
                        const DropdownMenuItem(value: null, child: Text('Todas')),
                        ...['BAJA', 'MEDIA', 'ALTA', 'CRITICA'].map(
                          (v) => DropdownMenuItem(value: v, child: Text(v)),
                        ),
                      ],
                      onChanged: (v) => setState(() => _priority = v),
                    ),
                  ],
                ],

                if (_showPresentationOptions) ...[
                  const SizedBox(height: 10),
                  TextField(
                    controller: _customTitleCtrl,
                    maxLength: 120,
                    decoration: InputDecoration(
                      labelText: 'Título personalizado',
                      hintText: _definition['titulo']?.toString() ?? 'Título del reporte',
                    ),
                  ),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<String>(
                    initialValue: _orientation,
                    decoration: const InputDecoration(labelText: 'Orientación PDF'),
                    items: const [
                      DropdownMenuItem(value: 'horizontal', child: Text('Horizontal')),
                      DropdownMenuItem(value: 'vertical', child: Text('Vertical')),
                    ],
                    onChanged: (v) => setState(() => _orientation = v ?? 'horizontal'),
                  ),
                  if (_columnChoices.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    DropdownButtonFormField<String>(
                      initialValue: _columnChoices.any((c) => c['campo'] == _sortField)
                          ? _sortField
                          : '',
                      decoration: const InputDecoration(labelText: 'Ordenar por'),
                      items: [
                        const DropdownMenuItem(value: '', child: Text('Orden original')),
                        ..._columnChoices.map(
                          (c) => DropdownMenuItem(
                            value: c['campo']?.toString() ?? '',
                            child: Text(c['titulo']?.toString() ?? ''),
                          ),
                        ),
                      ],
                      onChanged: (v) => setState(() => _sortField = v ?? ''),
                    ),
                    if (_sortField.isNotEmpty) ...[
                      const SizedBox(height: 10),
                      DropdownButtonFormField<String>(
                        initialValue: _sortOrder,
                        decoration: const InputDecoration(labelText: 'Dirección de orden'),
                        items: const [
                          DropdownMenuItem(value: 'asc', child: Text('Ascendente')),
                          DropdownMenuItem(value: 'desc', child: Text('Descendente')),
                        ],
                        onChanged: (v) => setState(() => _sortOrder = v ?? 'asc'),
                      ),
                    ],
                    CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      title: Text(
                        'Elegir columnas visibles',
                        style: GoogleFonts.inter(fontSize: 12.5, fontWeight: FontWeight.w600),
                      ),
                      value: _customColumns,
                      onChanged: (v) {
                        setState(() {
                          _customColumns = v ?? false;
                          if (_customColumns && _selectedColumns.isEmpty) {
                            _selectedColumns = _columnChoices
                                .map((c) => c['campo']?.toString() ?? '')
                                .where((s) => s.isNotEmpty)
                                .toList();
                          }
                        });
                      },
                    ),
                    if (_customColumns)
                      Wrap(
                        spacing: 6,
                        runSpacing: 6,
                        children: _columnChoices.map((col) {
                          final field = col['campo']?.toString() ?? '';
                          final selected = _selectedColumns.contains(field);
                          return FilterChip(
                            label: Text(
                              col['titulo']?.toString() ?? field,
                              style: const TextStyle(fontSize: 11),
                            ),
                            selected: selected,
                            onSelected: (val) {
                              setState(() {
                                if (val) {
                                  if (!_selectedColumns.contains(field)) {
                                    _selectedColumns.add(field);
                                  }
                                } else {
                                  _selectedColumns.remove(field);
                                }
                              });
                            },
                          );
                        }).toList(),
                      ),
                  ],
                ],

                if (_validationMessage != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    _validationMessage!,
                    style: GoogleFonts.inter(
                      fontSize: 12,
                      color: AppTheme.warning,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
                const SizedBox(height: 14),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: (_busy || _validationMessage != null) ? null : _generate,
                    icon: const Icon(Icons.analytics_outlined, size: 18),
                    label: Text(_busy ? 'Cargando…' : 'Generar reporte'),
                  ),
                ),
              ],
            ),
          ),

        // 3. Resultado del Reporte
        if (_result != null)
          _buildResultSection(_result!, isDark, cardBg, borderColor, titleColor, subColor),

        // 4. Envío y Programación
        if (_can('Enviar_reportes') || _can('Programar_reportes'))
          _buildShareAndScheduleSection(isDark, cardBg, borderColor, titleColor, subColor),
      ],
    );
  }

  Widget _buildResultSection(
    Map<String, dynamic> result,
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    final rows = (result['filas'] as List? ?? []);
    final columns = (result['columnas'] as List? ?? []);
    final resumen = (result['resumen'] as Map? ?? {});
    final advertencias = (result['advertencias'] as List? ?? []);
    final recomendaciones = (result['recomendaciones'] as List? ?? []);
    final pages = (rows.length / 50).ceil().clamp(1, 400);
    final visibleRows = rows.skip((_page - 1) * 50).take(50).toList();

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'REPORTE GENERADO',
                      style: GoogleFonts.inter(
                        fontSize: 10.5,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.5,
                        color: AppTheme.primary,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      result['titulo']?.toString() ?? 'Reporte',
                      style: GoogleFonts.inter(
                        fontSize: 15.5,
                        fontWeight: FontWeight.w800,
                        color: titleColor,
                      ),
                    ),
                    Text(
                      'Corte: ${result['corte'] ?? ''}',
                      style: GoogleFonts.inter(fontSize: 11.5, color: subColor),
                    ),
                  ],
                ),
              ),
              if (_can('Exportar_reportes'))
                Wrap(
                  spacing: 6,
                  children: [
                    OutlinedButton.icon(
                      onPressed: _busy ? null : () => _download('pdf'),
                      icon: const Icon(Icons.picture_as_pdf_outlined, size: 15),
                      label: const Text('PDF', style: TextStyle(fontSize: 12)),
                    ),
                    OutlinedButton.icon(
                      onPressed: _busy ? null : () => _download('xlsx'),
                      icon: const Icon(Icons.table_view_outlined, size: 15),
                      label: const Text('Excel', style: TextStyle(fontSize: 12)),
                    ),
                  ],
                ),
            ],
          ),
          const SizedBox(height: 12),

          // Tarjetas de Resumen (KPIs)
          if (resumen.isNotEmpty) ...[
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: resumen.entries.map((entry) {
                final valStr = _formatDisplayValue(entry.value);
                final isNegative = valStr.contains('-');
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                      color: isNegative
                          ? AppTheme.error.withValues(alpha: 0.4)
                          : borderColor,
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        entry.key.toString().replaceAll('_', ' ').toUpperCase(),
                        style: GoogleFonts.inter(
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          color: subColor,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        valStr,
                        style: GoogleFonts.inter(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w800,
                          color: isNegative ? AppTheme.error : titleColor,
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 12),
          ],

          // Advertencias
          if (advertencias.isNotEmpty) ...[
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppTheme.warningBg,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: advertencias
                    .map(
                      (note) => Padding(
                        padding: const EdgeInsets.symmetric(vertical: 2),
                        child: Text(
                          '• $note',
                          style: GoogleFonts.inter(fontSize: 11.5, color: AppTheme.warning),
                        ),
                      ),
                    )
                    .toList(),
              ),
            ),
            const SizedBox(height: 12),
          ],

          // Tabla de datos
          if (columns.isNotEmpty && visibleRows.isNotEmpty)
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                headingRowHeight: 38,
                dataRowMinHeight: 36,
                dataRowMaxHeight: 52,
                columnSpacing: 18,
                columns: [
                  for (final c in columns)
                    DataColumn(
                      label: Text(
                        (c as Map)['titulo']?.toString() ?? '',
                        style: GoogleFonts.inter(
                          fontSize: 11.5,
                          fontWeight: FontWeight.w800,
                          color: titleColor,
                        ),
                      ),
                    ),
                ],
                rows: [
                  for (final row in visibleRows)
                    if (row is Map)
                      DataRow(
                        cells: [
                          for (final c in columns)
                            DataCell(
                              Text(
                                _formatDisplayValue(row[(c as Map)['campo']]),
                                style: GoogleFonts.inter(
                                  fontSize: 12,
                                  fontWeight: row[c['campo']]
                                              ?.toString()
                                              .contains('SALDO_NEGATIVO') ==
                                          true
                                      ? FontWeight.w800
                                      : FontWeight.w500,
                                  color: row[c['campo']]
                                                  ?.toString()
                                                  .contains('SALDO_NEGATIVO') ==
                                              true ||
                                          (c['campo']?.toString().contains('saldo') == true &&
                                              row[c['campo']]?.toString().startsWith('-') ==
                                                  true)
                                      ? AppTheme.error
                                      : (row[c['campo']]
                                                  ?.toString()
                                                  .contains('SALDO_POSITIVO') ==
                                              true
                                          ? AppTheme.success
                                          : titleColor),
                                ),
                              ),
                            ),
                        ],
                      ),
                ],
              ),
            ),

          if (rows.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 16),
              child: Center(
                child: Text(
                  'No hay registros para estos filtros.',
                  style: GoogleFonts.inter(fontSize: 12.5, color: subColor),
                ),
              ),
            ),

          if (rows.isNotEmpty) ...[
            const SizedBox(height: 10),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '${rows.length} registros · Pág. $_page de $pages',
                  style: GoogleFonts.inter(fontSize: 11.5, color: subColor),
                ),
                Row(
                  children: [
                    IconButton(
                      onPressed: _page <= 1 ? null : () => setState(() => _page--),
                      icon: const Icon(Icons.chevron_left_rounded),
                    ),
                    IconButton(
                      onPressed: _page >= pages ? null : () => setState(() => _page++),
                      icon: const Icon(Icons.chevron_right_rounded),
                    ),
                  ],
                ),
              ],
            ),
          ],

          if (recomendaciones.isNotEmpty) ...[
            const Divider(height: 20),
            Text(
              'RECOMENDACIONES BASADAS EN REGISTROS',
              style: GoogleFonts.inter(
                fontSize: 10.5,
                fontWeight: FontWeight.w800,
                color: AppTheme.primary,
              ),
            ),
            const SizedBox(height: 6),
            for (final rec in recomendaciones)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text(
                  '• ${_formatDisplayValue(rec)}',
                  style: GoogleFonts.inter(fontSize: 12, color: titleColor, height: 1.35),
                ),
              ),
          ],
        ],
      ),
    );
  }

  Widget _buildShareAndScheduleSection(
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'COMPARTIR Y PROGRAMAR ENTREGA',
            style: GoogleFonts.inter(
              fontSize: 11,
              fontWeight: FontWeight.w800,
              color: subColor,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Cada destinatario recibe únicamente los datos permitidos a su cuenta.',
            style: GoogleFonts.inter(fontSize: 12, color: subColor),
          ),
          const SizedBox(height: 8),
          for (final recipient in _recipients)
            if (recipient is Map)
              CheckboxListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                title: Text(
                  recipient['nombre']?.toString() ?? 'Destinatario',
                  style: GoogleFonts.inter(fontSize: 12.5, fontWeight: FontWeight.w600),
                ),
                value: _receivers.contains(recipient['id_usuario']),
                onChanged: (v) => setState(() {
                  final id = recipient['id_usuario'] as int;
                  if (v == true) {
                    _receivers.add(id);
                  } else {
                    _receivers.remove(id);
                  }
                }),
              ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: DropdownButtonFormField<String>(
                  initialValue: _format,
                  decoration: const InputDecoration(labelText: 'Formato de entrega'),
                  items: const [
                    DropdownMenuItem(value: 'pdf', child: Text('PDF')),
                    DropdownMenuItem(value: 'xlsx', child: Text('Excel')),
                  ],
                  onChanged: (v) => setState(() => _format = v ?? 'pdf'),
                ),
              ),
              const SizedBox(width: 10),
              if (_can('Enviar_reportes'))
                ElevatedButton.icon(
                  onPressed: (_busy || _result == null || _receivers.isEmpty) ? null : _send,
                  icon: const Icon(Icons.send_rounded, size: 16),
                  label: const Text('Enviar'),
                ),
            ],
          ),
          if (_deliveries.isNotEmpty) ...[
            const SizedBox(height: 10),
            for (final d in _deliveries)
              if (d is Map)
                Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Text(
                    'Destinatario ${d['id_usuario']}: ${_statusLabel(d['estado']?.toString())} ${d['error'] ?? ''}',
                    style: GoogleFonts.inter(fontSize: 11.5, color: subColor),
                  ),
                ),
          ],
          if (_can('Programar_reportes')) ...[
            const Divider(height: 24),
            Text(
              'PROGRAMAR ENVÍO AUTOMÁTICO',
              style: GoogleFonts.inter(
                fontSize: 11,
                fontWeight: FontWeight.w800,
                color: AppTheme.primary,
              ),
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _frequency,
                    decoration: const InputDecoration(labelText: 'Frecuencia'),
                    items: const [
                      DropdownMenuItem(value: 'diaria', child: Text('Diaria')),
                      DropdownMenuItem(value: 'semanal', child: Text('Semanal')),
                      DropdownMenuItem(value: 'mensual', child: Text('Mensual')),
                    ],
                    onChanged: (v) => setState(() {
                      _frequency = v ?? 'diaria';
                      _day = 1;
                    }),
                  ),
                ),
                const SizedBox(width: 10),
                OutlinedButton.icon(
                  onPressed: _busy
                      ? null
                      : () async {
                          final t = await showTimePicker(
                            context: context,
                            initialTime: const TimeOfDay(hour: 8, minute: 0),
                          );
                          if (mounted && t != null) {
                            setState(() {
                              _hour =
                                  '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';
                            });
                          }
                        },
                  icon: const Icon(Icons.schedule_rounded, size: 16),
                  label: Text('Hora: $_hour'),
                ),
              ],
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _zoneCtrl,
              decoration: const InputDecoration(labelText: 'Zona horaria IANA'),
            ),
            if (_frequency != 'diaria') ...[
              const SizedBox(height: 10),
              DropdownButtonFormField<int>(
                initialValue: _day,
                decoration: const InputDecoration(labelText: 'Día de ejecución'),
                items: List.generate(
                  _frequency == 'semanal' ? 7 : 31,
                  (i) => DropdownMenuItem(value: i + 1, child: Text('Día ${i + 1}')),
                ),
                onChanged: (v) => setState(() => _day = v ?? 1),
              ),
            ],
            const SizedBox(height: 10),
            DropdownButtonFormField<String>(
              initialValue: _period,
              decoration: const InputDecoration(labelText: 'Período relativo'),
              items: [
                const DropdownMenuItem(value: 'fijo', child: Text('Filtros actuales')),
                if (_definition['fechas'] == true) ...const [
                  DropdownMenuItem(value: 'ayer', child: Text('Ayer')),
                  DropdownMenuItem(value: 'semana_anterior', child: Text('Semana anterior')),
                  DropdownMenuItem(value: 'mes_anterior', child: Text('Mes anterior')),
                ],
              ],
              onChanged: (v) => setState(() => _period = v ?? 'fijo'),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: (_busy || _receivers.isEmpty || _selected == null)
                    ? null
                    : _saveSchedule,
                icon: const Icon(Icons.event_repeat_rounded, size: 16),
                label: const Text('Guardar programación'),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildHistorialTab(
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    if (_history.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            'Todavía no has generado reportes.',
            style: GoogleFonts.inter(fontSize: 13.5, color: subColor),
          ),
        ),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: _history.length,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: (context, index) {
        final item = _history[index] as Map;
        final id = item['id']?.toString() ?? '';
        final repId = (item['solicitud'] as Map?)?['reporte']?.toString() ?? 'Reporte';
        final repTitle = _allReports
                .where((r) => r['id']?.toString() == repId)
                .firstOrNull?['titulo']
                ?.toString() ??
            repId.replaceAll('_', ' ');
        final estado = item['estado']?.toString() ?? 'LISTO';

        return Container(
          decoration: BoxDecoration(
            color: cardBg,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: borderColor),
          ),
          child: ListTile(
            title: Text(
              repTitle,
              style: GoogleFonts.inter(
                fontSize: 13.5,
                fontWeight: FontWeight.w800,
                color: titleColor,
              ),
            ),
            subtitle: Text(
              '${item['created_at'] ?? ''} · ${_statusLabel(estado)}',
              style: GoogleFonts.inter(fontSize: 11.5, color: subColor),
            ),
            trailing: const Icon(Icons.open_in_new_rounded, size: 18, color: AppTheme.primary),
            onTap: (_busy || id.isEmpty) ? null : () => _openById(id),
          ),
        );
      },
    );
  }

  Widget _buildProgramacionesTab(
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    if (_schedules.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            'Sin programaciones registradas.',
            style: GoogleFonts.inter(fontSize: 13.5, color: subColor),
          ),
        ),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: _schedules.length,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: (context, index) {
        final item = _schedules[index] as Map;
        final id = item['id']?.toString() ?? '';
        final hab = item['habilitada'] == true;
        final conf = item['configuracion'] as Map? ?? {};
        final repId = (conf['solicitud'] as Map?)?['reporte']?.toString() ?? 'Reporte';

        return Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: cardBg,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: borderColor),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      repId.replaceAll('_', ' ').toUpperCase(),
                      style: GoogleFonts.inter(
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                        color: titleColor,
                      ),
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: (hab ? AppTheme.success : AppTheme.warning).withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      hab ? 'Activa' : 'Pausada',
                      style: GoogleFonts.inter(
                        fontSize: 10.5,
                        fontWeight: FontWeight.w700,
                        color: hab ? AppTheme.success : AppTheme.warning,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                'Próxima ejecución: ${item['next_run'] ?? '—'}',
                style: GoogleFonts.inter(fontSize: 11.5, color: subColor),
              ),
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                children: [
                  OutlinedButton(
                    onPressed: _busy
                        ? null
                        : () => _perform(() async {
                              await _api.pause(id, !hab);
                              await _load();
                            }),
                    child: Text(hab ? 'Pausar' : 'Activar'),
                  ),
                  ElevatedButton(
                    onPressed: (_busy || !hab)
                        ? null
                        : () => _perform(() async {
                              await _api.runScheduleNow(id);
                              await _load();
                            }),
                    child: const Text('Ejecutar ahora'),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }
}
