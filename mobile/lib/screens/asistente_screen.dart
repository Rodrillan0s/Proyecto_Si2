import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:provider/provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:speech_to_text/speech_to_text.dart';

import '../services/ai_assistant_service.dart';
import '../services/auth_provider.dart';
import '../services/notificacion_service.dart';
import '../services/reportes_service.dart';
import '../services/reportes_voice.dart';
import '../theme/app_theme.dart';
import '../widgets/architectural_prototype_card.dart';
import '../widgets/chart_spec_card.dart';
import 'reportes_screen.dart';

class AsistenteScreen extends StatefulWidget {
  final int? idObraContexto;
  final String? nombreObraContexto;
  final String? initialMode; // 'admin' | 'comercial'
  final String? initialPrompt;

  const AsistenteScreen({
    super.key,
    this.idObraContexto,
    this.nombreObraContexto,
    this.initialMode,
    this.initialPrompt,
  });

  @override
  State<AsistenteScreen> createState() => _AsistenteScreenState();
}

class _AsistenteScreenState extends State<AsistenteScreen> {
  final AiAssistantService _aiService = AiAssistantService();
  final ReportesService _reportesService = ReportesService();
  final TextEditingController _inputController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final SpeechToText _speech = ReportesVoice.speech;
  final ImagePicker _imagePicker = ImagePicker();

  // Controladores para el formulario CRM inline en modo comercial
  final TextEditingController _crmNombreCtrl = TextEditingController();
  final TextEditingController _crmTelefonoCtrl = TextEditingController();
  final TextEditingController _crmEmailCtrl = TextEditingController();
  final TextEditingController _crmNotasCtrl = TextEditingController();

  String _assistantType = 'admin'; // 'admin' | 'comercial'
  bool _enviando = false;
  bool _escuchandoVoz = false;
  bool _cargandoCatalogoComercial = false;
  bool _recalculandoEstilo = false;
  bool _enviandoContactoCrm = false;
  String? _errorBanner;

  String? _lastUserIdentity;
  int? _lastEmpresaId;
  int _requestEpoch = 0;

  List<Map<String, dynamic>> _empresasComerciales = [];
  dynamic _empresaRefComercial;
  bool _empresaFijaPorSesion = false;

  static const List<String> _estilosAcabadoCodigos = [
    'ESTANDAR',
    'INDUSTRIAL',
    'MINIMALISTA',
    'CONTEMPORANEO',
    'LUJO',
  ];

  bool _isComercialMode(AuthProvider auth) {
    if (!auth.puedeUsarAsistenteAdmin) return true;
    return _assistantType == 'comercial';
  }

  AdminChatSession _adminSession(AuthProvider auth) {
    return AiAssistantService.obtenerSesionAdmin(
      userIdentity: auth.userIdentityKey,
      idEmpresa: auth.idEmpresaActiva,
      idObraContexto: widget.idObraContexto,
    );
  }

  CommercialChatSession _commercialSession(AuthProvider auth) {
    return AiAssistantService.obtenerSesionComercial(
      userIdentity: auth.userIdentityKey,
      empresaRef: _empresaRefComercial ?? auth.idEmpresaActiva ?? 'default',
    );
  }

  @override
  void initState() {
    super.initState();
    if (widget.initialMode != null) {
      _assistantType = widget.initialMode!;
    }
    if (widget.initialPrompt != null && widget.initialPrompt!.trim().isNotEmpty) {
      _inputController.text = widget.initialPrompt!.trim();
    }
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final auth = context.watch<AuthProvider>();
    final currentIdentity = auth.userIdentityKey;
    final currentEmpresa = auth.idEmpresaActiva;

    final userChanged = _lastUserIdentity != null && _lastUserIdentity != currentIdentity;
    final companyChanged = _lastEmpresaId != currentEmpresa;

    if (userChanged || companyChanged) {
      _requestEpoch++;
      _enviando = false;
      _errorBanner = null;
      _detenerVoz();
    }

    _lastUserIdentity = currentIdentity;
    _lastEmpresaId = currentEmpresa;
    AiAssistantService.syncUserIdentity(currentIdentity);

    if (!auth.puedeUsarAsistenteAdmin) {
      _assistantType = 'comercial';
    }

    if (auth.estaAutenticado && !auth.esAdminGlobal && auth.idEmpresaActiva != null) {
      _empresaFijaPorSesion = true;
      _empresaRefComercial = auth.idEmpresaActiva;
      AiAssistantService.empresaRefComercialActiva = _empresaRefComercial;
    } else {
      _empresaFijaPorSesion = false;
      if (currentEmpresa != null) {
        _empresaRefComercial = currentEmpresa;
        AiAssistantService.empresaRefComercialActiva = _empresaRefComercial;
      } else if (AiAssistantService.empresaRefComercialActiva != null) {
        _empresaRefComercial = AiAssistantService.empresaRefComercialActiva;
      }
    }

    _sincronizarFormularioCrm(auth);
    unawaited(_inicializarDatosSegunModo(auth));
  }

  void _sincronizarFormularioCrm(AuthProvider auth) {
    final sesion = _commercialSession(auth);
    final fc = sesion.formContacto;
    if (_crmNombreCtrl.text.isEmpty && (fc['nombre_completo']?.toString() ?? '').isNotEmpty) {
      _crmNombreCtrl.text = fc['nombre_completo'].toString();
    } else if (_crmNombreCtrl.text.isEmpty && (auth.usuarioCompleto ?? '').isNotEmpty) {
      _crmNombreCtrl.text = auth.usuarioCompleto!;
      fc['nombre_completo'] = auth.usuarioCompleto!;
    }
    if (_crmEmailCtrl.text.isEmpty && (fc['email']?.toString() ?? '').isNotEmpty) {
      _crmEmailCtrl.text = fc['email'].toString();
    } else if (_crmEmailCtrl.text.isEmpty && (auth.correo ?? '').isNotEmpty) {
      _crmEmailCtrl.text = auth.correo!;
      fc['email'] = auth.correo!;
    }
    if (_crmTelefonoCtrl.text.isEmpty && (fc['telefono']?.toString() ?? '').isNotEmpty) {
      _crmTelefonoCtrl.text = fc['telefono'].toString();
    }
    if (_crmNotasCtrl.text.isEmpty && (fc['notas']?.toString() ?? '').isNotEmpty) {
      _crmNotasCtrl.text = fc['notas'].toString();
    }
  }

  Future<void> _inicializarDatosSegunModo(AuthProvider auth) async {
    if (_isComercialMode(auth)) {
      await _cargarEmpresasYCatalogoComercial(auth);
    } else {
      await _cargarCatalogoReportesAdmin(auth);
    }
  }

  Future<void> _cargarCatalogoReportesAdmin(AuthProvider auth) async {
    if (auth.esAdminGlobal && auth.idEmpresaActiva == null) return;
    final sesion = _adminSession(auth);
    if (sesion.catalog != null) return;
    try {
      final cat = await _reportesService.catalog(auth.idEmpresaActiva);
      if (mounted) {
        setState(() {
          sesion.catalog = cat;
        });
      }
    } catch (_) {}
  }

  Future<void> _cargarEmpresasYCatalogoComercial(AuthProvider auth) async {
    if (AiAssistantService.empresasComercialesCache.isNotEmpty) {
      _empresasComerciales = AiAssistantService.empresasComercialesCache;
    } else {
      try {
        setState(() => _cargandoCatalogoComercial = true);
        final list = await _aiService.listarEmpresasComerciales();
        if (!mounted) return;
        _empresasComerciales = list;
      } catch (e) {
        if (mounted) {
          setState(() {
            _cargandoCatalogoComercial = false;
            _errorBanner = e.toString().replaceAll('Exception: ', '');
          });
        }
        return;
      }
    }

    if (_empresaRefComercial == null && _empresasComerciales.isNotEmpty) {
      final conUnidades = _empresasComerciales
              .where((e) => (int.tryParse(e['total_unidades']?.toString() ?? '0') ?? 0) > 0)
              .firstOrNull ??
          _empresasComerciales.first;
      _empresaRefComercial = conUnidades['id_empresa'];
      AiAssistantService.empresaRefComercialActiva = _empresaRefComercial;
    }

    if (_empresaRefComercial != null) {
      await _cargarCatalogoEmpresaComercial(auth, _empresaRefComercial);
    } else if (mounted) {
      setState(() => _cargandoCatalogoComercial = false);
    }
  }

  Future<void> _cargarCatalogoEmpresaComercial(AuthProvider auth, dynamic empresaRef) async {
    final sesion = AiAssistantService.obtenerSesionComercial(
      userIdentity: auth.userIdentityKey,
      empresaRef: empresaRef,
    );
    if (sesion.catalogo != null) {
      if (mounted) setState(() => _cargandoCatalogoComercial = false);
      return;
    }

    if (mounted) setState(() => _cargandoCatalogoComercial = true);
    try {
      final cat = await _aiService.obtenerCatalogoComercial(empresaRef);
      if (!mounted) return;
      setState(() {
        sesion.catalogo = cat;
        _cargandoCatalogoComercial = false;
      });
    } catch (e) {
      if (mounted) {
        setState(() {
          _cargandoCatalogoComercial = false;
          _errorBanner = e.toString().replaceAll('Exception: ', '');
        });
      }
    }
  }

  @override
  void dispose() {
    _detenerVoz();
    ReportesVoice.release(this);
    _inputController.dispose();
    _scrollController.dispose();
    _crmNombreCtrl.dispose();
    _crmTelefonoCtrl.dispose();
    _crmEmailCtrl.dispose();
    _crmNotasCtrl.dispose();
    super.dispose();
  }

  // ── RECONOCIMIENTO DE VOZ ────────────────────────────────────────────────

  Future<void> _conmutarVoz() async {
    if (_escuchandoVoz) {
      await _detenerVoz();
      return;
    }

    try {
      final available = await ReportesVoice.initialize(
        this,
        () {
          if (mounted) setState(() => _escuchandoVoz = false);
        },
        (status) {
          if (mounted && (status == 'notListening' || status == 'done')) {
            setState(() => _escuchandoVoz = false);
          }
        },
      );

      if (!mounted) return;

      if (available) {
        final locales = await _speech.locales();
        final spanish = locales.where((l) => l.localeId.startsWith('es')).firstOrNull;

        setState(() => _escuchandoVoz = true);

        await _speech.listen(
          listenOptions: SpeechListenOptions(
            localeId: spanish?.localeId,
            listenFor: const Duration(seconds: 45),
            partialResults: true,
          ),
          onResult: (result) {
            if (mounted) {
              setState(() {
                _inputController.text = result.recognizedWords;
                _inputController.selection = TextSelection.fromPosition(
                  TextPosition(offset: _inputController.text.length),
                );
              });
            }
          },
        );
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Reconocimiento de voz no disponible o permisos denegados.'),
              backgroundColor: AppTheme.warning,
            ),
          );
        }
      }
    } catch (_) {
      if (mounted) setState(() => _escuchandoVoz = false);
    }
  }

  Future<void> _detenerVoz() async {
    try {
      await _speech.stop();
    } catch (_) {}
    if (mounted) {
      setState(() => _escuchandoVoz = false);
    }
  }

  void _scrollHaciaAbajo() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 280),
          curve: Curves.easeOut,
        );
      }
    });
  }

  // ── ACCIONES MODO GESTIÓN / ADMIN ────────────────────────────────────────

  List<String> _sugerenciasAdmin(AuthProvider auth) {
    final sesion = _adminSession(auth);
    final reportes = (sesion.catalog?['reportes'] as List? ?? []);
    final tieneSaldoComercial =
        reportes.any((r) => (r is Map) && r['id']?.toString() == 'saldo_comercial');

    return [
      'Analizar estado general y riesgos de la empresa',
      'Generame un reporte de las obras con mas deficit',
      if (tieneSaldoComercial || auth.esAdminGlobal || auth.esAdminEmpresa)
        '¿Cuáles son las obras que han generado ganancias?',
      '¿Cuáles son los materiales con stock agotado?',
      if (auth.hasPermission('Visualizar_clientes'))
        '¿Cuántos prospectos están en negociación?',
    ];
  }

  String _topicLabel(String? topic) {
    switch (topic) {
      case 'crm':
        return 'Clientes y ventas';
      case 'finanzas':
        return 'Finanzas';
      case 'conocimiento':
        return 'Conocimiento del sistema';
      case 'analisis':
        return 'Diagnóstico operativo';
      case 'operacion':
        return 'Asistencia operativa';
      default:
        return 'Reportes y proyectos';
    }
  }

  Future<void> _enviarMensajeAdmin([String? textoForzado]) async {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    if (auth.esAdminGlobal && auth.idEmpresaActiva == null) {
      setState(() => _errorBanner = 'Selecciona primero una empresa en el panel de Inicio.');
      return;
    }

    final texto = (textoForzado ?? _inputController.text).trim();
    if (texto.isEmpty || _enviando) return;

    if (textoForzado == null) {
      _inputController.clear();
    }

    final sesion = _adminSession(auth);
    final epoch = ++_requestEpoch;
    final userMsg = AdminChatMessage(
      author: 'user',
      text: texto,
      fecha: DateTime.now(),
    );

    setState(() {
      _errorBanner = null;
      sesion.historyFilter = 'todos';
      sesion.mensajes.add(userMsg);
      _enviando = true;
    });

    _scrollHaciaAbajo();

    try {
      final respuesta = await _aiService.enviarConsulta(
        texto: texto,
        conversacionId: sesion.conversacionId,
        idEmpresa: auth.idEmpresaActiva,
        idObraContexto: widget.idObraContexto,
      );

      if (!mounted || epoch != _requestEpoch) return;

      final conversacion = respuesta['conversacion']?.toString() ??
          respuesta['conversacion_id']?.toString();
      if (conversacion != null && conversacion.isNotEmpty) {
        sesion.conversacionId = conversacion;
      }

      final tema = respuesta['tema']?.toString() ?? 'reportes';
      userMsg.topic = tema;

      final textoRespuesta = respuesta['respuesta']?.toString() ??
          respuesta['mensaje']?.toString() ??
          'Consulta procesada.';

      final ejecucion = (respuesta['ejecucion'] is Map)
          ? Map<String, dynamic>.from(respuesta['ejecucion'] as Map)
          : null;

      final ejecucionesRaw = respuesta['ejecuciones'] as List?;
      final ejecuciones = ejecucionesRaw != null
          ? ejecucionesRaw
              .whereType<Map>()
              .map((e) => Map<String, dynamic>.from(e))
              .toList()
          : (ejecucion != null ? [ejecucion] : <Map<String, dynamic>>[]);

      final opciones = (respuesta['opciones'] as List? ?? [])
          .map((e) => e.toString())
          .toList();

      final obras = (respuesta['obras'] as List? ?? [])
          .whereType<Map>()
          .map((e) => Map<String, dynamic>.from(e))
          .toList();

      final solicitud = (respuesta['solicitud'] is Map)
          ? Map<String, dynamic>.from(respuesta['solicitud'] as Map)
          : null;

      final operacionPropuesta = (respuesta['operacion_propuesta'] is Map)
          ? Map<String, dynamic>.from(respuesta['operacion_propuesta'] as Map)
          : ((respuesta['propuesta_operacion'] is Map)
              ? Map<String, dynamic>.from(respuesta['propuesta_operacion'] as Map)
              : null);

      final resultadoAnalisis = (respuesta['resultado_analisis'] is Map)
          ? Map<String, dynamic>.from(respuesta['resultado_analisis'] as Map)
          : ((respuesta['diagnostico'] is Map)
              ? Map<String, dynamic>.from(respuesta['diagnostico'] as Map)
              : null);

      final execChart = (ejecucion?['resultado'] is Map &&
              (ejecucion!['resultado'] as Map)['chart_spec'] is Map)
          ? Map<String, dynamic>.from((ejecucion['resultado'] as Map)['chart_spec'] as Map)
          : null;
      final chartSpec = (respuesta['chart_spec'] is Map)
          ? Map<String, dynamic>.from(respuesta['chart_spec'] as Map)
          : execChart;

      final pendientes = (respuesta['pendientes'] is Map)
          ? Map<String, dynamic>.from(respuesta['pendientes'] as Map)
          : null;

      final sugerencias = (respuesta['sugerencias'] as List? ?? [])
          .map((e) => e.toString())
          .toList();

      final referencias = (respuesta['referencias'] as List? ?? [])
          .map((e) => e.toString())
          .toList();

      setState(() {
        sesion.mensajes.add(
          AdminChatMessage(
            author: 'assistant',
            text: textoRespuesta,
            fecha: DateTime.now(),
            query: texto,
            topic: tema,
            execution: ejecucion,
            executions: ejecuciones,
            choices: opciones,
            works: obras,
            request: solicitud,
            operacionPropuesta: operacionPropuesta,
            resultadoAnalisis: resultadoAnalisis,
            chartSpec: chartSpec,
            pendientes: pendientes,
            sugerencias: sugerencias,
            referencias: referencias,
          ),
        );
        _enviando = false;
      });

      _scrollHaciaAbajo();
    } catch (e) {
      if (!mounted || epoch != _requestEpoch) return;
      setState(() {
        _errorBanner = e.toString().replaceAll('Exception: ', '');
        _enviando = false;
      });
    }
  }

  Future<void> _seleccionarObraEnMensajeAdmin(
    AdminChatMessage msg,
    Map<String, dynamic> work,
  ) async {
    final nombreObra = work['nombre']?.toString() ?? 'Obra';
    if (msg.request == null) {
      await _enviarMensajeAdmin('${msg.query ?? "Reporte de avance"} de la obra $nombreObra');
      return;
    }
    if (_enviando) return;

    final auth = Provider.of<AuthProvider>(context, listen: false);
    final sesion = _adminSession(auth);
    final epoch = ++_requestEpoch;

    setState(() {
      _enviando = true;
      _errorBanner = null;
    });

    try {
      final filtrosPrevios = (msg.request!['filtros'] is Map)
          ? Map<String, dynamic>.from(msg.request!['filtros'] as Map)
          : <String, dynamic>{};
      final nuevaSolicitud = {
        ...msg.request!,
        'filtros': {
          ...filtrosPrevios,
          'id_obra': work['id_obra'],
        },
      };

      final respuesta = await _aiService.enviarConsulta(
        texto: nombreObra,
        conversacionId: sesion.conversacionId,
        idEmpresa: auth.idEmpresaActiva,
        idObraContexto: widget.idObraContexto,
        solicitud: nuevaSolicitud,
      );

      if (!mounted || epoch != _requestEpoch) return;

      sesion.conversacionId =
          respuesta['conversacion']?.toString() ?? sesion.conversacionId;
      final tema = respuesta['tema']?.toString() ?? 'reportes';
      final ejecucion = (respuesta['ejecucion'] is Map)
          ? Map<String, dynamic>.from(respuesta['ejecucion'] as Map)
          : null;
      final ejecucionesRaw = respuesta['ejecuciones'] as List?;
      final ejecuciones = ejecucionesRaw != null
          ? ejecucionesRaw
              .whereType<Map>()
              .map((e) => Map<String, dynamic>.from(e))
              .toList()
          : (ejecucion != null ? [ejecucion] : <Map<String, dynamic>>[]);

      setState(() {
        msg.works = [];
        sesion.mensajes.add(
          AdminChatMessage(
            author: 'user',
            text: nombreObra,
            fecha: DateTime.now(),
            topic: tema,
          ),
        );
        sesion.mensajes.add(
          AdminChatMessage(
            author: 'assistant',
            text: respuesta['respuesta']?.toString() ??
                respuesta['mensaje']?.toString() ??
                'Reporte generado.',
            fecha: DateTime.now(),
            topic: tema,
            execution: ejecucion,
            executions: ejecuciones,
            choices: (respuesta['opciones'] as List? ?? [])
                .map((e) => e.toString())
                .toList(),
            works: (respuesta['obras'] as List? ?? [])
                .whereType<Map>()
                .map((e) => Map<String, dynamic>.from(e))
                .toList(),
            request: (respuesta['solicitud'] is Map)
                ? Map<String, dynamic>.from(respuesta['solicitud'] as Map)
                : null,
          ),
        );
        _enviando = false;
      });
      _scrollHaciaAbajo();
    } catch (e) {
      if (!mounted || epoch != _requestEpoch) return;
      setState(() {
        _errorBanner = e.toString().replaceAll('Exception: ', '');
        _enviando = false;
      });
    }
  }

  Future<void> _confirmarPropuesta(AdminChatMessage mensaje) async {
    final prop = mensaje.operacionPropuesta;
    if (prop == null || mensaje.ejecutandoAccion || prop['ejecutado'] == true) return;

    final idPropuesta = prop['id_propuesta']?.toString();
    if (idPropuesta == null || idPropuesta.isEmpty) return;

    setState(() => mensaje.ejecutandoAccion = true);
    final auth = Provider.of<AuthProvider>(context, listen: false);
    final sesion = _adminSession(auth);

    try {
      final res = await _aiService.confirmarOperacion(
        idPropuesta: idPropuesta,
        idEmpresa: auth.idEmpresaActiva,
        idObraContexto: widget.idObraContexto,
      );

      if (!mounted) return;
      setState(() {
        prop['ejecutado'] = true;
        mensaje.ejecutandoAccion = false;
        sesion.mensajes.add(
          AdminChatMessage(
            author: 'assistant',
            text:
                '✓ ${res["mensaje"] ?? "Operación confirmada."} La acción quedó registrada en la bitácora del sistema.',
            fecha: DateTime.now(),
            topic: 'operacion',
          ),
        );
      });
      NotificacionService.instance.emitLocalPush(
        titulo: 'Operación Asistida Ejecutada',
        cuerpo: res['mensaje']?.toString() ??
            'La operación "${prop["entidad"] ?? "propuesta"}" fue ejecutada.',
        tipo: 'OBRA',
      );
      unawaited(NotificacionService.instance.sincronizarSilencioso());
      _scrollHaciaAbajo();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        mensaje.ejecutandoAccion = false;
        _errorBanner = e.toString().replaceAll('Exception: ', '');
      });
    }
  }

  Future<void> _cancelarPropuesta(AdminChatMessage mensaje) async {
    final prop = mensaje.operacionPropuesta;
    if (prop == null || mensaje.ejecutandoAccion || prop['cancelado'] == true) return;

    final idPropuesta = prop['id_propuesta']?.toString();
    if (idPropuesta == null || idPropuesta.isEmpty) return;

    setState(() => mensaje.ejecutandoAccion = true);
    final auth = Provider.of<AuthProvider>(context, listen: false);
    final sesion = _adminSession(auth);

    try {
      await _aiService.cancelarOperacion(
        idPropuesta: idPropuesta,
        idEmpresa: auth.idEmpresaActiva,
        idObraContexto: widget.idObraContexto,
      );
      if (!mounted) return;
      setState(() {
        prop['cancelado'] = true;
        mensaje.ejecutandoAccion = false;
        sesion.mensajes.add(
          AdminChatMessage(
            author: 'assistant',
            text: 'La operación "${prop["entidad"] ?? "propuesta"}" fue cancelada.',
            fecha: DateTime.now(),
            topic: 'operacion',
          ),
        );
      });
      _scrollHaciaAbajo();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        mensaje.ejecutandoAccion = false;
        _errorBanner = e.toString().replaceAll('Exception: ', '');
      });
    }
  }

  Future<void> _descargarReporteDesdeChat(
    Map<String, dynamic> execution,
    String format,
  ) async {
    final id = execution['id']?.toString();
    if (id == null || id.isEmpty || _enviando) return;
    setState(() {
      _enviando = true;
      _errorBanner = null;
    });
    try {
      final file = await _reportesService.download(id, format);
      if (!mounted) return;
      final dir = await getTemporaryDirectory();
      final path = '${dir.path}/${ReportesService.identity()}-${file.name}';
      await File(path).writeAsBytes(file.bytes);
      try {
        if (!mounted) return;
        final box = context.findRenderObject() as RenderBox?;
        await Share.shareXFiles(
          [XFile(path)],
          subject: (execution['resultado'] as Map?)?['titulo']?.toString(),
          sharePositionOrigin:
              box == null ? null : box.localToGlobal(Offset.zero) & box.size,
        );
      } finally {
        if (await File(path).exists()) await File(path).delete();
      }
    } catch (e) {
      if (mounted) {
        setState(() => _errorBanner = e.toString().replaceAll('Exception: ', ''));
      }
    } finally {
      if (mounted) setState(() => _enviando = false);
    }
  }

  // ── ACCIONES MODO COMERCIAL & PLANOS ─────────────────────────────────────

  String _etiquetaIntencionComercial(String? intencion) {
    switch (intencion) {
      case 'buscar_unidades':
        return 'Catálogo Inmobiliario';
      case 'recomendar_presupuesto':
        return 'Recomendación a Medida';
      case 'comparar_unidades':
        return 'Comparativa Lado a Lado';
      case 'analizar_plano':
        return 'Lectura de Planos & Costos';
      case 'estimar_costo':
        return 'Estimación Paramétrica por Estilo';
      case 'solicitar_contacto':
        return 'Contacto Comercial CRM';
      default:
        return 'Asistente Comercial';
    }
  }

  List<String> _generarSugerenciasSeguimientoComercial({
    String? intencion,
    required List<Map<String, dynamic>> unidades,
    required bool tieneComparativa,
    required bool tieneEstimacion,
    required bool tieneCrm,
  }) {
    final chips = <String>[];
    if (unidades.length >= 2 && !tieneComparativa) {
      chips.add('Compárame las opciones recomendadas lado a lado');
    }
    if (!tieneEstimacion) {
      chips.add('¿Cuánto cuesta construir 110 m² en estilo Minimalista vs Lujo?');
    }
    if (!tieneCrm) {
      chips.add('Quiero que un asesor comercial me contacte');
    }
    return chips.take(3).toList();
  }

  Future<void> _seleccionarImagenPlano(AuthProvider auth) async {
    try {
      final picked = await _imagePicker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 88,
      );
      if (picked == null || !mounted) return;
      final sesion = _commercialSession(auth);
      setState(() {
        sesion.archivoPlanoPath = picked.path;
        sesion.archivoPlanoNombre = picked.name;
        _errorBanner = null;
      });
    } catch (_) {
      if (mounted) {
        setState(() => _errorBanner = 'No se pudo seleccionar la imagen del plano.');
      }
    }
  }

  void _quitarPlanoAdjunto(AuthProvider auth) {
    final sesion = _commercialSession(auth);
    setState(() {
      sesion.archivoPlanoPath = null;
      sesion.archivoPlanoNombre = null;
    });
  }

  Future<void> _enviarAccionComercial([String? textoForzado]) async {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    final sesion = _commercialSession(auth);
    final empresaRef = _empresaRefComercial ?? auth.idEmpresaActiva;
    if (_enviando || empresaRef == null) return;

    if (sesion.archivoPlanoPath != null && textoForzado == null) {
      await _enviarPlanoComercial(auth, empresaRef, sesion);
      return;
    }

    final texto = (textoForzado ?? _inputController.text).trim();
    if (texto.isEmpty) return;

    if (textoForzado == null) {
      _inputController.clear();
    }

    final epoch = ++_requestEpoch;
    final horaStr = TimeOfDay.now().format(context);

    setState(() {
      _errorBanner = null;
      _enviando = true;
      sesion.mensajes.add(
        CommercialChatMessage(
          id: 'u-${DateTime.now().millisecondsSinceEpoch}',
          rol: 'user',
          texto: texto,
          fecha: horaStr,
        ),
      );
    });
    _scrollHaciaAbajo();

    try {
      final payload = <String, dynamic>{
        'mensaje': texto,
        'conversacion_id': sesion.conversacionId,
        'moneda': 'USD',
        if (sesion.unidadesSeleccionadasComparar.length >= 2)
          'ids_unidades_comparar': sesion.unidadesSeleccionadasComparar,
      };

      final res = await _aiService.enviarChatComercial(empresaRef, payload);
      if (!mounted || epoch != _requestEpoch) return;

      sesion.conversacionId =
          res['conversacion_id']?.toString() ?? sesion.conversacionId;

      final recomendadas = (res['unidades_recomendadas'] as List? ?? [])
          .whereType<Map>()
          .map((e) => Map<String, dynamic>.from(e))
          .take(4)
          .toList();

      final comparativa = (res['comparativa'] is Map)
          ? Map<String, dynamic>.from(res['comparativa'] as Map)
          : null;

      final estimacion = (res['estimacion_costo'] is Map)
          ? Map<String, dynamic>.from(res['estimacion_costo'] as Map)
          : null;

      final propuestaProyecto = (res['propuesta_proyecto'] is Map)
          ? Map<String, dynamic>.from(res['propuesta_proyecto'] as Map)
          : null;

      final motivosExclusion = (res['motivos_exclusion'] is Map)
          ? Map<String, dynamic>.from(res['motivos_exclusion'] as Map)
          : null;

      final registroCrm = (res['registro_crm'] is Map)
          ? Map<String, dynamic>.from(res['registro_crm'] as Map)
          : null;

      final requiereContacto = res['requiere_datos_contacto'] == true;
      final intencion = res['intencion']?.toString();

      final sugerencias = _generarSugerenciasSeguimientoComercial(
        intencion: intencion,
        unidades: recomendadas,
        tieneComparativa: comparativa != null,
        tieneEstimacion: estimacion != null,
        tieneCrm: registroCrm != null,
      );

      setState(() {
        sesion.mensajes.add(
          CommercialChatMessage(
            id: 'a-${DateTime.now().millisecondsSinceEpoch}',
            rol: 'assistant',
            texto: res['respuesta']?.toString() ??
                res['resumen_estructurado']?.toString() ??
                'Consulta comercial procesada.',
            fecha: TimeOfDay.now().format(context),
            intencion: intencion,
            unidades: recomendadas,
            comparativa: comparativa,
            estimacionCosto: estimacion,
            propuestaProyecto: propuestaProyecto,
            motivosExclusion: motivosExclusion,
            registroCrm: registroCrm,
            requiereContacto: requiereContacto,
            mostrarFormularioContacto: requiereContacto,
            sugerencias: sugerencias,
          ),
        );
        _enviando = false;
      });
      if (registroCrm != null) {
        final msgConf = registroCrm['mensaje_confirmacion']?.toString() ??
            'Tu solicitud de contacto comercial fue registrada en el CRM.';
        NotificacionService.instance.simulateIncomingPush({
          'id_notificacion': DateTime.now().millisecondsSinceEpoch ~/ 1000,
          'titulo': 'Solicitud de Contacto Registrada en CRM',
          'cuerpo': msgConf,
          'tipo_referencia': 'CRM_PROSPECTO',
          'leido': false,
          'fecha_creacion': TimeOfDay.now().format(context),
        });
        unawaited(NotificacionService.instance.sincronizarSilencioso());
      }
      _scrollHaciaAbajo();
    } catch (e) {
      if (!mounted || epoch != _requestEpoch) return;
      setState(() {
        _enviando = false;
        _errorBanner = e.toString().replaceAll('Exception: ', '');
      });
    }
  }

  Future<void> _enviarPlanoComercial(
    AuthProvider auth,
    dynamic empresaRef,
    CommercialChatSession sesion,
  ) async {
    final filePath = sesion.archivoPlanoPath!;
    final fileName = sesion.archivoPlanoNombre ?? 'plano.png';
    final estilo = sesion.estiloPlanoSeleccionado;
    final notaUsuario = _inputController.text.trim().isNotEmpty
        ? _inputController.text.trim()
        : 'Analizar este plano arquitectónico y estimar su costo constructivo en estilo $estilo.';

    _inputController.clear();
    final epoch = ++_requestEpoch;

    setState(() {
      _enviando = true;
      _errorBanner = null;
      sesion.archivoPlanoPath = null;
      sesion.archivoPlanoNombre = null;
      sesion.mensajes.add(
        CommercialChatMessage(
          id: 'u-plano-${DateTime.now().millisecondsSinceEpoch}',
          rol: 'user',
          texto: notaUsuario,
          fecha: TimeOfDay.now().format(context),
          planoPath: filePath,
          planoNombre: fileName,
          estiloPlano: estilo,
        ),
      );
    });
    _scrollHaciaAbajo();

    try {
      final res = await _aiService.analizarPlanoComercial(
        empresaRef,
        filePath: filePath,
        fileName: fileName,
        mensaje: notaUsuario,
        moneda: 'USD',
        estiloPreferido: estilo,
        conversacionId: sesion.conversacionId,
      );

      if (!mounted || epoch != _requestEpoch) return;
      sesion.conversacionId =
          res['conversacion_id']?.toString() ?? sesion.conversacionId;

      final lecturaPlano = (res['lectura_plano'] is Map)
          ? Map<String, dynamic>.from(res['lectura_plano'] as Map)
          : null;
      final estimacionCosto = (res['estimacion_costo'] is Map)
          ? Map<String, dynamic>.from(res['estimacion_costo'] as Map)
          : null;
      final similares = (res['unidades_similares_disponibles'] as List? ?? [])
          .whereType<Map>()
          .map((e) => Map<String, dynamic>.from(e))
          .take(3)
          .toList();

      setState(() {
        sesion.mensajes.add(
          CommercialChatMessage(
            id: 'a-plano-${DateTime.now().millisecondsSinceEpoch}',
            rol: 'assistant',
            texto: res['respuesta']?.toString() ?? 'Análisis de plano completado.',
            fecha: TimeOfDay.now().format(context),
            intencion: 'analizar_plano',
            lecturaPlano: lecturaPlano,
            estimacionCosto: estimacionCosto,
            unidades: similares,
            sugerencias: const [
              'Compárame las unidades similares a mi plano',
              'Quiero agendar una revisión técnica de mi plano con un asesor',
            ],
          ),
        );
        _enviando = false;
      });
      _scrollHaciaAbajo();
    } catch (e) {
      if (!mounted || epoch != _requestEpoch) return;
      setState(() {
        _enviando = false;
        _errorBanner = e.toString().replaceAll('Exception: ', '');
      });
    }
  }

  Future<void> _cambiarEstiloEnMensajeComercial(
    CommercialChatMessage msg,
    String nuevoEstilo,
  ) async {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    final empresaRef = _empresaRefComercial ?? auth.idEmpresaActiva;
    if (msg.estimacionCosto == null || _recalculandoEstilo || empresaRef == null) return;

    final params = (msg.estimacionCosto!['parametros_entrada'] is Map)
        ? Map<String, dynamic>.from(msg.estimacionCosto!['parametros_entrada'] as Map)
        : <String, dynamic>{};

    setState(() => _recalculandoEstilo = true);
    try {
      final res = await _aiService.estimarCostoComercial(empresaRef, {
        'superficie_m2': double.tryParse(params['superficie_m2']?.toString() ?? '95') ?? 95.0,
        'tipo_inmueble': params['tipo_inmueble']?.toString() ?? 'DEPARTAMENTO',
        'estilo_acabado': nuevoEstilo,
        'cantidad_plantas': int.tryParse(params['cantidad_plantas']?.toString() ?? '1') ?? 1,
        'dormitorios': int.tryParse(params['dormitorios']?.toString() ?? '2') ?? 2,
        'banos': int.tryParse(params['banos']?.toString() ?? '2') ?? 2,
        'moneda': 'USD',
        'incluir_parqueo': true,
        'incluir_baulera': false,
        'incluir_domotica': nuevoEstilo == 'LUJO',
      });
      if (!mounted) return;
      setState(() {
        _recalculandoEstilo = false;
        if (res['estimacion'] is Map) {
          msg.estimacionCosto = Map<String, dynamic>.from(res['estimacion'] as Map);
        }
      });
    } catch (_) {
      if (mounted) setState(() => _recalculandoEstilo = false);
    }
  }

  void _toggleCompararUnidad(AuthProvider auth, int idUnidad) {
    final sesion = _commercialSession(auth);
    setState(() {
      final lista = sesion.unidadesSeleccionadasComparar;
      if (lista.contains(idUnidad)) {
        lista.remove(idUnidad);
      } else {
        if (lista.length >= 4) lista.removeAt(0);
        lista.add(idUnidad);
      }
    });
  }

  void _abrirTarjetaContactoEnChat(
    AuthProvider auth, {
    int? idUnidad,
    String? codigoUnidad,
  }) {
    final sesion = _commercialSession(auth);
    setState(() {
      if (idUnidad != null && !sesion.unidadesInteresContacto.contains(idUnidad)) {
        sesion.unidadesInteresContacto.add(idUnidad);
      }
      if (codigoUnidad != null && !_crmNotasCtrl.text.contains(codigoUnidad)) {
        _crmNotasCtrl.text = _crmNotasCtrl.text.isEmpty
            ? 'Interesado en unidad $codigoUnidad'
            : '${_crmNotasCtrl.text} | Interés en $codigoUnidad';
        sesion.formContacto['notas'] = _crmNotasCtrl.text;
      }

      if (sesion.mensajes.isNotEmpty &&
          sesion.mensajes.last.rol == 'assistant' &&
          sesion.mensajes.last.registroCrm == null) {
        sesion.mensajes.last.mostrarFormularioContacto = true;
      } else {
        sesion.mensajes.add(
          CommercialChatMessage(
            id: 'a-contacto-${DateTime.now().millisecondsSinceEpoch}',
            rol: 'assistant',
            texto:
                'Completa tus datos de contacto aquí mismo para registrar tu solicitud en el CRM comercial y asignarte un asesor:',
            fecha: TimeOfDay.now().format(context),
            intencion: 'solicitar_contacto',
            mostrarFormularioContacto: true,
          ),
        );
      }
    });
    _scrollHaciaAbajo();
  }

  Future<void> _enviarContactoDesdeTarjeta(
    AuthProvider auth,
    CommercialChatMessage msg,
  ) async {
    final empresaRef = _empresaRefComercial ?? auth.idEmpresaActiva;
    if (empresaRef == null || _enviandoContactoCrm) return;

    final nombre = _crmNombreCtrl.text.trim();
    final telefono = _crmTelefonoCtrl.text.trim();
    final email = _crmEmailCtrl.text.trim();
    final notas = _crmNotasCtrl.text.trim();

    if (nombre.isEmpty) {
      setState(() => _errorBanner = 'Ingresa tu nombre completo para registrar el contacto.');
      return;
    }
    if (telefono.isEmpty && email.isEmpty) {
      setState(() => _errorBanner = 'Ingresa un teléfono/WhatsApp o correo electrónico.');
      return;
    }

    final sesion = _commercialSession(auth);
    setState(() {
      _errorBanner = null;
      _enviandoContactoCrm = true;
    });

    try {
      final res = await _aiService.solicitarContactoComercial(empresaRef, {
        'nombre_completo': nombre,
        'telefono': telefono,
        'email': email,
        'notas': notas,
        'moneda': 'USD',
        'unidades_interes': sesion.unidadesInteresContacto,
        'conversacion_id': sesion.conversacionId,
      });

      if (!mounted) return;
      final crmMap = (res['data'] is Map)
          ? Map<String, dynamic>.from(res['data'] as Map)
          : (res['registro_crm'] is Map)
              ? Map<String, dynamic>.from(res['registro_crm'] as Map)
              : {'mensaje_confirmacion': 'Solicitud registrada exitosamente en CRM.'};
      setState(() {
        _enviandoContactoCrm = false;
        msg.mostrarFormularioContacto = false;
        msg.requiereContacto = false;
        msg.registroCrm = crmMap;
      });
      final msgConf = crmMap['mensaje_confirmacion']?.toString() ??
          'Prospecto $nombre ($telefono) registrado exitosamente en el CRM.';
      NotificacionService.instance.simulateIncomingPush({
        'id_notificacion': DateTime.now().millisecondsSinceEpoch ~/ 1000,
        'titulo': 'Nuevo Prospecto Comercial: $nombre',
        'cuerpo': msgConf,
        'tipo_referencia': 'CRM_PROSPECTO',
        'leido': false,
        'fecha_creacion': TimeOfDay.now().format(context),
      });
      unawaited(NotificacionService.instance.sincronizarSilencioso());
      _scrollHaciaAbajo();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _enviandoContactoCrm = false;
        _errorBanner = e.toString().replaceAll('Exception: ', '');
      });
    }
  }

  // ── CONSTRUCCIÓN DE INTERFAZ PRINCIPAL ───────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);
    final subColor = isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B);
    final isComercial = _isComercialMode(auth);
    final comercialSession = _commercialSession(auth);

    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC),
      appBar: AppBar(
        titleSpacing: 16,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: AppTheme.primary,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.auto_awesome_rounded, color: Colors.white, size: 18),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    isComercial ? 'Asistente Comercial OBRATEC' : 'Asistente OBRATEC',
                    style: GoogleFonts.inter(
                      fontSize: 15,
                      fontWeight: FontWeight.w800,
                      color: titleColor,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    widget.nombreObraContexto != null
                        ? 'Obra: ${widget.nombreObraContexto}'
                        : (auth.empresaActivaNombre ??
                            auth.nombreEmpresa ??
                            'Consultas, Reportes y Catálogo'),
                    style: GoogleFonts.inter(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.primary,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          if (isComercial)
            IconButton(
              tooltip: 'Solicitar contacto de asesor',
              icon: const Icon(Icons.support_agent_rounded, color: AppTheme.primary),
              onPressed: () => _abrirTarjetaContactoEnChat(auth),
            ),
          IconButton(
            tooltip: 'Nueva conversación',
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _enviando
                ? null
                : () {
                    setState(() {
                      _requestEpoch++;
                      _errorBanner = null;
                      if (isComercial) {
                        AiAssistantService.reiniciarSesionComercial(
                          userIdentity: auth.userIdentityKey,
                          empresaRef: _empresaRefComercial ?? auth.idEmpresaActiva ?? 'default',
                        );
                      } else {
                        AiAssistantService.reiniciarSesionAdmin(
                          userIdentity: auth.userIdentityKey,
                          idEmpresa: auth.idEmpresaActiva,
                          idObraContexto: widget.idObraContexto,
                        );
                      }
                    });
                  },
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Selector unificado de modo (Gestión / Admin | Comercial & Planos)
            if (auth.puedeUsarAsistenteAdmin)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: cardBg,
                  border: Border(bottom: BorderSide(color: borderColor)),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: InkWell(
                        onTap: () {
                          setState(() {
                            _assistantType = 'admin';
                            _errorBanner = null;
                          });
                          unawaited(_cargarCatalogoReportesAdmin(auth));
                        },
                        borderRadius: BorderRadius.circular(8),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          decoration: BoxDecoration(
                            color: !isComercial
                                ? AppTheme.primary
                                : (isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9)),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            'Gestión / Admin',
                            textAlign: TextAlign.center,
                            style: GoogleFonts.inter(
                              fontSize: 12,
                              fontWeight: !isComercial ? FontWeight.w800 : FontWeight.w600,
                              color: !isComercial ? Colors.white : subColor,
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: InkWell(
                        onTap: () {
                          setState(() {
                            _assistantType = 'comercial';
                            _errorBanner = null;
                          });
                          unawaited(_cargarEmpresasYCatalogoComercial(auth));
                        },
                        borderRadius: BorderRadius.circular(8),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          decoration: BoxDecoration(
                            color: isComercial
                                ? AppTheme.primary
                                : (isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9)),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            'Comercial & Planos',
                            textAlign: TextAlign.center,
                            style: GoogleFonts.inter(
                              fontSize: 12,
                              fontWeight: isComercial ? FontWeight.w800 : FontWeight.w600,
                              color: isComercial ? Colors.white : subColor,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),

            // Barra de contexto según modo
            if (isComercial)
              _buildComercialTopBar(auth, comercialSession, isDark, cardBg, borderColor, titleColor, subColor)
            else
              _buildAdminFilterBar(auth, isDark, cardBg, borderColor, titleColor, subColor),

            // Banner de error si existe
            if (_errorBanner != null)
              Container(
                width: double.infinity,
                margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: AppTheme.errorBg,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AppTheme.error.withValues(alpha: 0.35)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.error_outline_rounded, size: 16, color: AppTheme.error),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _errorBanner!,
                        style: GoogleFonts.inter(
                          fontSize: 11.5,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.error,
                        ),
                      ),
                    ),
                    InkWell(
                      onTap: () => setState(() => _errorBanner = null),
                      child: const Icon(Icons.close_rounded, size: 16, color: AppTheme.error),
                    ),
                  ],
                ),
              ),

            // Área principal de conversación
            Expanded(
              child: isComercial
                  ? _buildComercialConversation(
                      auth,
                      comercialSession,
                      isDark,
                      cardBg,
                      borderColor,
                      titleColor,
                      subColor,
                    )
                  : _buildAdminConversation(
                      auth,
                      _adminSession(auth),
                      isDark,
                      cardBg,
                      borderColor,
                      titleColor,
                      subColor,
                    ),
            ),

            // Indicador minimalista de carga
            if (_enviando || _cargandoCatalogoComercial)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 6),
                child: Row(
                  children: [
                    const SizedBox(
                      width: 13,
                      height: 13,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: AppTheme.primary,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Text(
                      'Cargando…',
                      style: GoogleFonts.inter(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.primary,
                      ),
                    ),
                  ],
                ),
              ),

            // Banner de escucha por voz
            if (_escuchandoVoz)
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                decoration: BoxDecoration(
                  color: AppTheme.primary.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AppTheme.primary.withValues(alpha: 0.35)),
                ),
                child: Row(
                  children: [
                    const SizedBox(
                      width: 14,
                      height: 14,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: AppTheme.primary,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Escuchando… Habla con claridad.',
                        style: GoogleFonts.inter(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.primary,
                        ),
                      ),
                    ),
                    InkWell(
                      onTap: _detenerVoz,
                      child: const Icon(
                        Icons.stop_circle_outlined,
                        color: AppTheme.error,
                        size: 22,
                      ),
                    ),
                  ],
                ),
              ),

            // Vista previa de plano adjunto (solo en modo Comercial)
            if (isComercial && comercialSession.archivoPlanoPath != null)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: isDark ? const Color(0xFF1E293B) : const Color(0xFFFFF7ED),
                  border: Border(top: BorderSide(color: borderColor)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.architecture_rounded, color: AppTheme.primary, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            comercialSession.archivoPlanoNombre ?? 'Plano adjunto',
                            style: GoogleFonts.inter(
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              color: titleColor,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          Text(
                            'Estilo: ${comercialSession.estiloPlanoSeleccionado}',
                            style: GoogleFonts.inter(fontSize: 11, color: AppTheme.primary),
                          ),
                        ],
                      ),
                    ),
                    DropdownButton<String>(
                      value: comercialSession.estiloPlanoSeleccionado,
                      underline: const SizedBox.shrink(),
                      isDense: true,
                      style: GoogleFonts.inter(
                        fontSize: 11.5,
                        fontWeight: FontWeight.w700,
                        color: titleColor,
                      ),
                      items: _estilosAcabadoCodigos
                          .map((e) => DropdownMenuItem(value: e, child: Text(e)))
                          .toList(),
                      onChanged: (v) {
                        if (v != null) {
                          setState(() => comercialSession.estiloPlanoSeleccionado = v);
                        }
                      },
                    ),
                    const SizedBox(width: 6),
                    IconButton(
                      icon: const Icon(Icons.close_rounded, size: 18, color: AppTheme.error),
                      onPressed: () => _quitarPlanoAdjunto(auth),
                    ),
                  ],
                ),
              ),

            // Barra inferior de entrada
            Container(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
              decoration: BoxDecoration(
                color: cardBg,
                border: Border(top: BorderSide(color: borderColor)),
              ),
              child: Row(
                children: [
                  if (isComercial) ...[
                    Container(
                      decoration: BoxDecoration(
                        color: isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9),
                        shape: BoxShape.circle,
                      ),
                      child: IconButton(
                        icon: const Icon(
                          Icons.architecture_rounded,
                          color: AppTheme.primary,
                          size: 20,
                        ),
                        tooltip: 'Subir plano arquitectónico',
                        onPressed: _enviando ? null : () => _seleccionarImagenPlano(auth),
                      ),
                    ),
                    const SizedBox(width: 6),
                  ],
                  Expanded(
                    child: TextField(
                      controller: _inputController,
                      textCapitalization: TextCapitalization.sentences,
                      maxLines: 3,
                      minLines: 1,
                      style: GoogleFonts.inter(fontSize: 13.5),
                      decoration: InputDecoration(
                        hintText: _escuchandoVoz
                            ? 'Escuchando tu voz…'
                            : (isComercial
                                ? 'Busca unidades, compara o sube tu plano…'
                                : 'Escribe tu consulta o solicita un reporte…'),
                        hintStyle: GoogleFonts.inter(fontSize: 12.5, color: subColor),
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 14,
                          vertical: 11,
                        ),
                        filled: true,
                        fillColor: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF1F5F9),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(20),
                          borderSide: BorderSide.none,
                        ),
                      ),
                      onSubmitted: (_) =>
                          isComercial ? _enviarAccionComercial() : _enviarMensajeAdmin(),
                    ),
                  ),
                  const SizedBox(width: 6),
                  Container(
                    decoration: BoxDecoration(
                      color: _escuchandoVoz
                          ? AppTheme.error
                          : (isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9)),
                      shape: BoxShape.circle,
                    ),
                    child: IconButton(
                      icon: Icon(
                        _escuchandoVoz ? Icons.mic_rounded : Icons.mic_none_rounded,
                        color: _escuchandoVoz ? Colors.white : AppTheme.primary,
                        size: 20,
                      ),
                      tooltip: _escuchandoVoz ? 'Detener dictado' : 'Dictar por voz',
                      onPressed: _enviando ? null : _conmutarVoz,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Container(
                    decoration: const BoxDecoration(
                      color: AppTheme.primary,
                      shape: BoxShape.circle,
                    ),
                    child: IconButton(
                      icon: const Icon(Icons.arrow_upward_rounded, color: Colors.white, size: 20),
                      onPressed: _enviando
                          ? null
                          : () => isComercial
                              ? _enviarAccionComercial()
                              : _enviarMensajeAdmin(),
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

  // ── WIDGETS MODO GESTIÓN / ADMIN ─────────────────────────────────────────

  Widget _buildAdminFilterBar(
    AuthProvider auth,
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    final sesion = _adminSession(auth);
    if (sesion.mensajes.isEmpty) return const SizedBox.shrink();

    const filters = {
      'todos': 'Toda la conversación',
      'reportes': 'Reportes y proyectos',
      'finanzas': 'Finanzas',
      'crm': 'Clientes y ventas',
      'analisis': 'Diagnóstico',
      'operacion': 'Operaciones',
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      decoration: BoxDecoration(
        color: cardBg,
        border: Border(bottom: BorderSide(color: borderColor)),
      ),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: filters.entries.map((e) {
            final active = sesion.historyFilter == e.key;
            return Padding(
              padding: const EdgeInsets.only(right: 6),
              child: ChoiceChip(
                label: Text(e.value),
                selected: active,
                selectedColor: AppTheme.primary.withValues(alpha: 0.18),
                labelStyle: GoogleFonts.inter(
                  fontSize: 11,
                  fontWeight: active ? FontWeight.w800 : FontWeight.w600,
                  color: active ? AppTheme.primary : subColor,
                ),
                onSelected: (_) => setState(() => sesion.historyFilter = e.key),
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildAdminConversation(
    AuthProvider auth,
    AdminChatSession sesion,
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    final visible = sesion.historyFilter == 'todos'
        ? sesion.mensajes
        : sesion.mensajes.where((m) => m.topic == sesion.historyFilter).toList();

    if (sesion.mensajes.isEmpty) {
      final suggestions = _sugerenciasAdmin(auth);
      return ListView(
        controller: _scrollController,
        padding: const EdgeInsets.all(16),
        children: [
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: cardBg,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: borderColor),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '¿QUÉ NECESITAS CONSULTAR?',
                  style: GoogleFonts.inter(
                    fontSize: 10.5,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.6,
                    color: AppTheme.primary,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Los datos de tu empresa, en una conversación.',
                  style: GoogleFonts.inter(
                    fontSize: 17,
                    fontWeight: FontWeight.w900,
                    color: titleColor,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Consulta proyectos, rentabilidad y déficit de obras, costos, materiales, personal, incidencias y clientes según tus permisos. Escribe o dicta tu solicitud.',
                  style: GoogleFonts.inter(fontSize: 12.5, color: subColor, height: 1.4),
                ),
                const SizedBox(height: 14),
                for (final sug in suggestions)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: InkWell(
                      onTap: _enviando ? null : () => _enviarMensajeAdmin(sug),
                      borderRadius: BorderRadius.circular(10),
                      child: Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        decoration: BoxDecoration(
                          color: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: borderColor),
                        ),
                        child: Row(
                          children: [
                            Expanded(
                              child: Text(
                                sug,
                                style: GoogleFonts.inter(
                                  fontSize: 12.5,
                                  fontWeight: FontWeight.w600,
                                  color: titleColor,
                                ),
                              ),
                            ),
                            const Icon(
                              Icons.north_east_rounded,
                              size: 15,
                              color: AppTheme.primary,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ],
      );
    }

    if (visible.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            'No hay consultas en este tema. Cambia el filtro o escribe abajo.',
            textAlign: TextAlign.center,
            style: GoogleFonts.inter(fontSize: 13, color: subColor),
          ),
        ),
      );
    }

    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      itemCount: visible.length,
      itemBuilder: (context, index) {
        final msg = visible[index];
        return _buildAdminMensajeItem(
          auth,
          msg,
          isDark,
          cardBg,
          borderColor,
          titleColor,
          subColor,
        );
      },
    );
  }

  Widget _buildAdminMensajeItem(
    AuthProvider auth,
    AdminChatMessage msg,
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    final esUsuario = msg.author == 'user';
    final canExport = (_adminSession(auth).catalog?['acciones'] as List? ?? [])
            .contains('Exportar_reportes') ||
        auth.hasPermission('Exportar_reportes') ||
        auth.esAdminGlobal ||
        auth.esAdminEmpresa;

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: esUsuario ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(bottom: 4, left: 4, right: 4),
            child: Text(
              esUsuario ? 'Tú' : 'OBRATEC · ${_topicLabel(msg.topic)}',
              style: GoogleFonts.inter(
                fontSize: 10.5,
                fontWeight: FontWeight.w700,
                color: esUsuario ? subColor : AppTheme.primary,
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
            decoration: BoxDecoration(
              color: esUsuario
                  ? AppTheme.primary
                  : (isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9)),
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(14),
                topRight: const Radius.circular(14),
                bottomLeft: Radius.circular(esUsuario ? 14 : 3),
                bottomRight: Radius.circular(esUsuario ? 3 : 14),
              ),
            ),
            child: Text(
              msg.text,
              style: GoogleFonts.inter(
                fontSize: 13.5,
                color: esUsuario ? Colors.white : titleColor,
                height: 1.4,
              ),
            ),
          ),

          // Tarjeta de Operación Asistida
          if (msg.operacionPropuesta != null) ...[
            const SizedBox(height: 10),
            _buildPropuestaAdminCard(msg, isDark, cardBg, borderColor, titleColor, subColor),
          ],

          // Tarjeta de Análisis / Diagnóstico Operativo
          if (msg.resultadoAnalisis != null) ...[
            const SizedBox(height: 10),
            _buildAnalisisAdminCard(
              msg.resultadoAnalisis!,
              isDark,
              cardBg,
              borderColor,
              titleColor,
              subColor,
            ),
          ],

          // Tarjetas de Ejecución de Reportes (ej. Obras con déficit / ganancias)
          if (msg.executions.isNotEmpty)
            for (final exec in msg.executions) ...[
              const SizedBox(height: 10),
              _buildExecutionCardInChat(
                exec,
                canExport,
                isDark,
                cardBg,
                borderColor,
                titleColor,
                subColor,
              ),
            ],

          // Visualización gráfica (ChartSpec)
          if (msg.chartSpec != null &&
              (msg.chartSpec!['tipo']?.toString() ?? 'none') != 'none') ...[
            ChartSpecCard(
              spec: msg.chartSpec,
              rows: (msg.execution?['resultado'] is Map &&
                      (msg.execution!['resultado'] as Map)['filas'] is List)
                  ? List<dynamic>.from((msg.execution!['resultado'] as Map)['filas'] as List)
                  : const [],
              resumen: (msg.execution?['resultado'] is Map &&
                      (msg.execution!['resultado'] as Map)['resumen'] is Map)
                  ? Map<String, dynamic>.from((msg.execution!['resultado'] as Map)['resumen'] as Map)
                  : null,
              compact: true,
            ),
          ],

          // Bandeja Proactiva de Pendientes
          if (msg.pendientes != null &&
              (msg.pendientes!['items'] is List) &&
              (msg.pendientes!['items'] as List).isNotEmpty) ...[
            const SizedBox(height: 8),
            _buildPendientesAdminCard(
              msg.pendientes!,
              isDark,
              cardBg,
              borderColor,
              titleColor,
              subColor,
            ),
          ],

          // Chips de desambiguación (Opciones de reportes u Obras)
          if (msg.choices.isNotEmpty || msg.works.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                for (final choice in msg.choices)
                  ActionChip(
                    label: Text(choice, style: const TextStyle(fontSize: 11.5)),
                    onPressed: _enviando ? null : () => _enviarMensajeAdmin(choice),
                  ),
                for (final work in msg.works)
                  ActionChip(
                    avatar: const Icon(Icons.apartment_rounded, size: 14, color: AppTheme.primary),
                    label: Text(
                      work['nombre']?.toString() ?? 'Obra',
                      style: const TextStyle(fontSize: 11.5),
                    ),
                    onPressed: _enviando ? null : () => _seleccionarObraEnMensajeAdmin(msg, work),
                  ),
              ],
            ),
          ],

          // Chips de seguimiento sugeridos
          if (msg.sugerencias.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: msg.sugerencias
                  .map(
                    (sug) => ActionChip(
                      label: Text(sug, style: const TextStyle(fontSize: 11.5)),
                      onPressed: _enviando ? null : () => _enviarMensajeAdmin(sug),
                    ),
                  )
                  .toList(),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildExecutionCardInChat(
    Map<String, dynamic> execution,
    bool canExport,
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    final resultado = (execution['resultado'] is Map)
        ? Map<String, dynamic>.from(execution['resultado'] as Map)
        : null;
    final titulo = resultado?['titulo']?.toString() ?? 'Reporte generado';
    final resumen = (resultado?['resumen'] is Map)
        ? Map<String, dynamic>.from(resultado!['resumen'] as Map)
        : <String, dynamic>{};
    final filas = (resultado?['filas'] as List? ?? []);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.analytics_outlined, size: 16, color: AppTheme.primary),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  titulo,
                  style: GoogleFonts.inter(
                    fontSize: 13,
                    fontWeight: FontWeight.w800,
                    color: titleColor,
                  ),
                ),
              ),
              Text(
                '${filas.length} reg.',
                style: GoogleFonts.inter(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.primary,
                ),
              ),
            ],
          ),
          if (resumen.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: resumen.entries.take(4).map((e) {
                final valStr = e.value?.toString() ?? '—';
                final neg = valStr.contains('-');
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(
                      color: neg ? AppTheme.error.withValues(alpha: 0.4) : borderColor,
                    ),
                  ),
                  child: Text(
                    '${e.key.replaceAll("_", " ")}: $valStr',
                    style: GoogleFonts.inter(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: neg ? AppTheme.error : titleColor,
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              ElevatedButton.icon(
                onPressed: _enviando
                    ? null
                    : () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => ReportesScreen(
                              initialExecutionId: execution['id']?.toString(),
                            ),
                          ),
                        );
                      },
                icon: const Icon(Icons.open_in_new_rounded, size: 14),
                label: const Text('Ver reporte completo', style: TextStyle(fontSize: 11.5)),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                ),
              ),
              if (canExport) ...[
                OutlinedButton.icon(
                  onPressed: _enviando ? null : () => _descargarReporteDesdeChat(execution, 'pdf'),
                  icon: const Icon(Icons.picture_as_pdf_outlined, size: 14),
                  label: const Text('PDF', style: TextStyle(fontSize: 11.5)),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  ),
                ),
                OutlinedButton.icon(
                  onPressed:
                      _enviando ? null : () => _descargarReporteDesdeChat(execution, 'xlsx'),
                  icon: const Icon(Icons.table_view_outlined, size: 14),
                  label: const Text('Excel', style: TextStyle(fontSize: 11.5)),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPendientesAdminCard(
    Map<String, dynamic> pendientes,
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    final items = (pendientes['items'] as List? ?? []).whereType<Map>().take(6).toList();
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
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
              Text(
                'PENDIENTES PRIORIZADOS',
                style: GoogleFonts.inter(
                  fontSize: 10.5,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.primary,
                ),
              ),
              Text(
                '${items.length}',
                style: GoogleFonts.inter(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.primary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          for (final item in items)
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: borderColor),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '[${item['prioridad'] ?? 'MEDIA'}] ${item['titulo'] ?? ''}',
                      style: GoogleFonts.inter(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: titleColor,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '${item['modulo'] ?? ''}${item['obra'] != null ? ' · ${item['obra']}' : ''} — ${item['motivo'] ?? ''}',
                      style: GoogleFonts.inter(fontSize: 11, color: subColor),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildAnalisisAdminCard(
    Map<String, dynamic> analisis,
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    final riesgo = (analisis['nivel_riesgo'] ?? 'MEDIO').toString().toUpperCase();
    final indicadores = (analisis['indicadores'] as List? ?? []);

    Color riesgoColor = AppTheme.info;
    if (riesgo.contains('ALTO') || riesgo.contains('CRITICO')) riesgoColor = AppTheme.error;
    if (riesgo.contains('MEDIO')) riesgoColor = AppTheme.warning;
    if (riesgo.contains('BAJO')) riesgoColor = AppTheme.success;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
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
              Text(
                'DIAGNÓSTICO OPERATIVO',
                style: GoogleFonts.inter(
                  fontSize: 10.5,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.primary,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: riesgoColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  'Riesgo: $riesgo',
                  style: GoogleFonts.inter(
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    color: riesgoColor,
                  ),
                ),
              ),
            ],
          ),
          if (indicadores.isNotEmpty) ...[
            const SizedBox(height: 8),
            for (final ind in indicadores)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text(
                  ind is Map
                      ? '• ${ind["titulo"] ?? ""}: ${ind["valor"] ?? ""} (${ind["detalle"] ?? ""})'
                      : '• $ind',
                  style: GoogleFonts.inter(fontSize: 12, color: titleColor, height: 1.35),
                ),
              ),
          ],
        ],
      ),
    );
  }

  Widget _buildPropuestaAdminCard(
    AdminChatMessage msg,
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    final p = msg.operacionPropuesta!;
    final entidad = p['entidad']?.toString() ?? p['tipo_operacion']?.toString() ?? 'OPERACIÓN';
    final resumen = p['resumen']?.toString() ?? p['descripcion']?.toString() ?? '';
    final params = (p['parametros'] is Map)
        ? Map<String, dynamic>.from(p['parametros'] as Map)
        : <String, dynamic>{};
    final ejecutado = p['ejecutado'] == true;
    final cancelado = p['cancelado'] == true;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.primary.withValues(alpha: 0.4), width: 1.2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                entidad.toUpperCase(),
                style: GoogleFonts.inter(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.primary,
                ),
              ),
              Text(
                ejecutado
                    ? '✓ Ejecutado'
                    : (cancelado ? 'Cancelado' : 'Pendiente de confirmación'),
                style: GoogleFonts.inter(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  color: ejecutado
                      ? AppTheme.success
                      : (cancelado ? AppTheme.error : AppTheme.warning),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            resumen,
            style: GoogleFonts.inter(fontSize: 12.5, color: titleColor, height: 1.35),
          ),
          if (params.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: params.entries
                  .map(
                    (e) => Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC),
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(color: borderColor),
                      ),
                      child: Text(
                        '${e.key}: ${e.value}',
                        style: GoogleFonts.inter(fontSize: 11, color: subColor),
                      ),
                    ),
                  )
                  .toList(),
            ),
          ],
          if (!ejecutado && !cancelado) ...[
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: msg.ejecutandoAccion ? null : () => _cancelarPropuesta(msg),
                    child: const Text('Cancelar'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton(
                    onPressed: msg.ejecutandoAccion ? null : () => _confirmarPropuesta(msg),
                    child: Text(msg.ejecutandoAccion ? 'Cargando…' : 'Confirmar ✓'),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  // ── WIDGETS MODO COMERCIAL & PLANOS ──────────────────────────────────────

  Widget _buildComercialTopBar(
    AuthProvider auth,
    CommercialChatSession sesion,
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    final resumenInv = (sesion.catalogo?['resumen_inventario'] is Map)
        ? Map<String, dynamic>.from(sesion.catalogo!['resumen_inventario'] as Map)
        : <String, dynamic>{};
    final disp = resumenInv['unidades_disponibles'] ?? 0;
    final comparandoCount = sesion.unidadesSeleccionadasComparar.length;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: cardBg,
        border: Border(bottom: BorderSide(color: borderColor)),
      ),
      child: Column(
        children: [
          Row(
            children: [
              const Icon(Icons.apartment_rounded, size: 16, color: AppTheme.primary),
              const SizedBox(width: 8),
              Expanded(
                child: (!_empresaFijaPorSesion && _empresasComerciales.length > 1)
                    ? DropdownButtonHideUnderline(
                        child: DropdownButton<dynamic>(
                          value: _empresasComerciales
                                  .any((e) => e['id_empresa'] == _empresaRefComercial)
                              ? _empresaRefComercial
                              : (_empresasComerciales.isNotEmpty
                                  ? _empresasComerciales.first['id_empresa']
                                  : null),
                          isDense: true,
                          isExpanded: true,
                          style: GoogleFonts.inter(
                            fontSize: 12.5,
                            fontWeight: FontWeight.w800,
                            color: titleColor,
                          ),
                          items: _empresasComerciales.map((emp) {
                            return DropdownMenuItem<dynamic>(
                              value: emp['id_empresa'],
                              child: Text(
                                emp['nombre_empresa']?.toString() ?? 'Constructora',
                                overflow: TextOverflow.ellipsis,
                              ),
                            );
                          }).toList(),
                          onChanged: (nuevaRef) {
                            if (nuevaRef != null) {
                              setState(() {
                                _empresaRefComercial = nuevaRef;
                                AiAssistantService.empresaRefComercialActiva = nuevaRef;
                              });
                              unawaited(_cargarCatalogoEmpresaComercial(auth, nuevaRef));
                            }
                          },
                        ),
                      )
                    : Text(
                        (sesion.catalogo?['empresa'] as Map?)?['nombre_empresa']?.toString() ??
                            auth.empresaActivaNombre ??
                            auth.nombreEmpresa ??
                            'Catálogo Inmobiliario',
                        style: GoogleFonts.inter(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w800,
                          color: titleColor,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: AppTheme.success.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '$disp disponibles',
                  style: GoogleFonts.inter(
                    fontSize: 10.5,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.success,
                  ),
                ),
              ),
            ],
          ),
          if (comparandoCount >= 2) ...[
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '$comparandoCount unidades seleccionadas para comparar',
                  style: GoogleFonts.inter(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.primary,
                  ),
                ),
                ElevatedButton(
                  onPressed: _enviando
                      ? null
                      : () => _enviarAccionComercial(
                            'Compárame lado a lado las unidades seleccionadas en precio, superficie y disponibilidad.',
                          ),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    minimumSize: Size.zero,
                  ),
                  child: const Text('Comparar ahora', style: TextStyle(fontSize: 11.5)),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildComercialConversation(
    AuthProvider auth,
    CommercialChatSession sesion,
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    final sugeridasRaw = (sesion.catalogo?['preguntas_sugeridas'] as List? ?? []);
    final sugeridas = sugeridasRaw.isNotEmpty
        ? sugeridasRaw.map((e) => e.toString()).toList()
        : const [
            '¿Qué departamentos o viviendas tienen disponibles actualmente?',
            'Tengo un presupuesto de 85.000 USD, ¿qué opciones me recomiendan?',
            'Compárame las mejores unidades disponibles en relación precio y superficie',
            '¿Cuánto cuesta construir 110 m² en estilo Minimalista vs Lujo?',
            'Quiero que un asesor comercial me contacte para agendar una visita',
          ];

    if (sesion.mensajes.isEmpty) {
      return ListView(
        controller: _scrollController,
        padding: const EdgeInsets.all(16),
        children: [
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: cardBg,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: borderColor),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'PORTAFOLIO INMOBILIARIO Y TASACIÓN DE PLANOS',
                  style: GoogleFonts.inter(
                    fontSize: 10.5,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.5,
                    color: AppTheme.primary,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Encuentra tu unidad ideal o cotiza tu plano.',
                  style: GoogleFonts.inter(
                    fontSize: 16.5,
                    fontWeight: FontWeight.w900,
                    color: titleColor,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Busca departamentos y casas por presupuesto, compara unidades lado a lado, sube la imagen de tu plano arquitectónico para estimar su costo por estilo o solicita contacto con un asesor.',
                  style: GoogleFonts.inter(fontSize: 12.5, color: subColor, height: 1.4),
                ),
                const SizedBox(height: 14),
                for (final preg in sugeridas)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: InkWell(
                      onTap: _enviando ? null : () => _enviarAccionComercial(preg),
                      borderRadius: BorderRadius.circular(10),
                      child: Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        decoration: BoxDecoration(
                          color: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: borderColor),
                        ),
                        child: Row(
                          children: [
                            Expanded(
                              child: Text(
                                preg,
                                style: GoogleFonts.inter(
                                  fontSize: 12.5,
                                  fontWeight: FontWeight.w600,
                                  color: titleColor,
                                ),
                              ),
                            ),
                            const Icon(
                              Icons.north_east_rounded,
                              size: 15,
                              color: AppTheme.primary,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ],
      );
    }

    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      itemCount: sesion.mensajes.length,
      itemBuilder: (context, index) {
        final msg = sesion.mensajes[index];
        return _buildComercialMensajeItem(
          auth,
          sesion,
          msg,
          isDark,
          cardBg,
          borderColor,
          titleColor,
          subColor,
        );
      },
    );
  }

  Widget _buildComercialMensajeItem(
    AuthProvider auth,
    CommercialChatSession sesion,
    CommercialChatMessage msg,
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    final esUsuario = msg.rol == 'user';

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: esUsuario ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(bottom: 4, left: 4, right: 4),
            child: Text(
              esUsuario
                  ? 'Tú · ${msg.fecha}'
                  : '${_etiquetaIntencionComercial(msg.intencion)} · ${msg.fecha}',
              style: GoogleFonts.inter(
                fontSize: 10.5,
                fontWeight: FontWeight.w700,
                color: esUsuario ? subColor : AppTheme.primary,
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
            decoration: BoxDecoration(
              color: esUsuario
                  ? AppTheme.primary
                  : (isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9)),
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(14),
                topRight: const Radius.circular(14),
                bottomLeft: Radius.circular(esUsuario ? 14 : 3),
                bottomRight: Radius.circular(esUsuario ? 3 : 14),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (msg.planoNombre != null) ...[
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.architecture_rounded, size: 15, color: Colors.white),
                      const SizedBox(width: 6),
                      Flexible(
                        child: Text(
                          'Plano: ${msg.planoNombre} (${msg.estiloPlano ?? "MINIMALISTA"})',
                          style: GoogleFonts.inter(
                            fontSize: 11.5,
                            fontWeight: FontWeight.w800,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                ],
                Text(
                  msg.texto,
                  style: GoogleFonts.inter(
                    fontSize: 13.5,
                    color: esUsuario ? Colors.white : titleColor,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),

          // 1. Lectura de Plano y Estimación Paramétrica por Estilo
          if (msg.lecturaPlano != null || msg.estimacionCosto != null) ...[
            const SizedBox(height: 10),
            _buildEstimacionYPlanoCard(
              msg,
              isDark,
              cardBg,
              borderColor,
              titleColor,
              subColor,
            ),
          ],

          // 2. Unidades Recomendadas
          if (msg.unidades.isNotEmpty) ...[
            const SizedBox(height: 10),
            for (final u in msg.unidades)
              _buildUnidadRecomendadaCard(
                auth,
                sesion,
                u,
                isDark,
                cardBg,
                borderColor,
                titleColor,
                subColor,
              ),
          ],

          // 2b. Propuesta de Proyecto de Construcción Personalizado
          if (msg.propuestaProyecto != null) ...[
            const SizedBox(height: 10),
            _buildPropuestaProyectoCard(
              auth,
              msg.propuestaProyecto!,
              isDark,
              cardBg,
              borderColor,
              titleColor,
              subColor,
            ),
          ],

          // 3. Tabla Comparativa Lado a Lado
          if (msg.comparativa != null) ...[
            const SizedBox(height: 10),
            _buildComparativaCard(
              msg.comparativa!,
              isDark,
              cardBg,
              borderColor,
              titleColor,
              subColor,
            ),
          ],

          // 4. Formulario CRM Inline o Confirmación de Registro CRM
          if (msg.mostrarFormularioContacto) ...[
            const SizedBox(height: 10),
            _buildFormularioContactoCrmCard(
              auth,
              msg,
              isDark,
              cardBg,
              borderColor,
              titleColor,
              subColor,
            ),
          ],
          if (msg.registroCrm != null) ...[
            const SizedBox(height: 10),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.successBg,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.success.withValues(alpha: 0.4)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.check_circle_rounded, color: AppTheme.success, size: 20),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      msg.registroCrm!['mensaje_confirmacion']?.toString() ??
                          'Solicitud comercial registrada exitosamente en el CRM.',
                      style: GoogleFonts.inter(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.success,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],

          // 5. Sugerencias de seguimiento comercial
          if (msg.sugerencias.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: msg.sugerencias
                  .map(
                    (sug) => ActionChip(
                      label: Text(sug, style: const TextStyle(fontSize: 11.5)),
                      onPressed: _enviando ? null : () => _enviarAccionComercial(sug),
                    ),
                  )
                  .toList(),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildUnidadRecomendadaCard(
    AuthProvider auth,
    CommercialChatSession sesion,
    Map<String, dynamic> u,
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    final idUnidad = int.tryParse(u['id_unidad']?.toString() ?? '0') ?? 0;
    final codigo = u['codigo_unidad']?.toString() ?? 'U-00';
    final nombre = u['nombre_unidad']?.toString() ?? 'Unidad Inmobiliaria';
    final obra = u['nombre_obra']?.toString() ?? 'Proyecto';
    final precioUsd = u['precio_usd']?.toString() ?? '—';
    final precioBob = u['precio_bob']?.toString() ?? '—';
    final sup = u['superficie_m2']?.toString() ?? '—';
    final dorms = u['dormitorios']?.toString() ?? '0';
    final banos = u['banos']?.toString() ?? '0';
    final score = u['afinidad_score'];
    final razones = (u['razones_recomendacion'] as List? ?? []);
    final observaciones = (u['observaciones_criterio'] as List? ?? []);
    final amoblamiento = u['estado_amoblamiento']?.toString() ?? 'DESCONOCIDO';
    final esEstimacionPrecio = u['es_estimacion_precio'] == true;
    final cotMob = (u['cotizacion_mobiliario_separada'] is Map)
        ? Map<String, dynamic>.from(u['cotizacion_mobiliario_separada'] as Map)
        : null;
    final seleccionada = sesion.unidadesSeleccionadasComparar.contains(idUnidad);

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: seleccionada ? AppTheme.primary : borderColor,
          width: seleccionada ? 1.5 : 1.0,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                decoration: BoxDecoration(
                  color: AppTheme.primary.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  codigo,
                  style: GoogleFonts.inter(
                    fontSize: 10.5,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.primary,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  obra,
                  style: GoogleFonts.inter(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w600,
                    color: subColor,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              if (score != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppTheme.success.withValues(alpha: 0.14),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    '$score% afinidad',
                    style: GoogleFonts.inter(
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      color: AppTheme.success,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            nombre,
            style: GoogleFonts.inter(
              fontSize: 13.5,
              fontWeight: FontWeight.w800,
              color: titleColor,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '\$$precioUsd USD · Bs $precioBob',
            style: GoogleFonts.inter(
              fontSize: 13,
              fontWeight: FontWeight.w900,
              color: AppTheme.primary,
            ),
          ),
          const SizedBox(height: 6),
          Wrap(
            spacing: 10,
            runSpacing: 4,
            children: [
              Text('📐 $sup m²', style: GoogleFonts.inter(fontSize: 11.5, color: subColor)),
              Text('🛏 $dorms dorms', style: GoogleFonts.inter(fontSize: 11.5, color: subColor)),
              Text('🚿 $banos baños', style: GoogleFonts.inter(fontSize: 11.5, color: subColor)),
              Text(
                '🪑 $amoblamiento',
                style: GoogleFonts.inter(fontSize: 11.5, color: subColor, fontWeight: FontWeight.w600),
              ),
              Text(
                esEstimacionPrecio ? 'Precio: Estimado' : 'Precio: Publicado',
                style: GoogleFonts.inter(
                  fontSize: 11,
                  color: esEstimacionPrecio ? AppTheme.warning : AppTheme.success,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          if (razones.isNotEmpty) ...[
            const SizedBox(height: 6),
            for (final r in razones.take(3))
              Text(
                '✓ $r',
                style: GoogleFonts.inter(fontSize: 11, color: AppTheme.success),
              ),
          ],
          if (observaciones.isNotEmpty) ...[
            const SizedBox(height: 4),
            for (final obs in observaciones.take(2))
              Text(
                '⚠ $obs',
                style: GoogleFonts.inter(fontSize: 11, color: AppTheme.warning),
              ),
          ],
          if (cotMob != null) ...[
            const SizedBox(height: 6),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: borderColor),
              ),
              child: Text(
                cotMob['disponible'] == true
                    ? 'Mobiliario por separado: +\$${cotMob['monto_usd']} USD (Bs ${cotMob['monto_bob']})'
                        '${cotMob['total_inmueble_mas_mobiliario_usd'] != null ? ' · Total: \$${cotMob['total_inmueble_mas_mobiliario_usd']} USD' : ''}'
                    : (cotMob['nota']?.toString() ?? 'Mobiliario cotizable por separado.'),
                style: GoogleFonts.inter(fontSize: 11, color: titleColor, fontWeight: FontWeight.w600),
              ),
            ),
          ],
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: idUnidad == 0
                      ? null
                      : () => _toggleCompararUnidad(auth, idUnidad),
                  icon: Icon(
                    seleccionada
                        ? Icons.check_box_rounded
                        : Icons.compare_arrows_rounded,
                    size: 15,
                  ),
                  label: Text(
                    seleccionada ? 'En comparativa' : 'Comparar',
                    style: const TextStyle(fontSize: 11.5),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => _abrirTarjetaContactoEnChat(
                    auth,
                    idUnidad: idUnidad,
                    codigoUnidad: codigo,
                  ),
                  icon: const Icon(Icons.person_add_alt_1_rounded, size: 15),
                  label: const Text('Me interesa', style: TextStyle(fontSize: 11.5)),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPropuestaProyectoCard(
    AuthProvider auth,
    Map<String, dynamic> propuesta,
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    final viable = propuesta['viable'] == true;
    final escenarios = (propuesta['escenarios'] as List? ?? []).whereType<Map>().toList();
    final terreno = (propuesta['terreno'] is Map)
        ? Map<String, dynamic>.from(propuesta['terreno'] as Map)
        : <String, dynamic>{};
    final preguntas = (propuesta['preguntas_progresivas'] as List? ?? [])
        .map((e) => e.toString())
        .toList();
    final aviso = propuesta['aviso_alcance']?.toString() ?? '';

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.primary.withValues(alpha: 0.45), width: 1.2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  viable
                      ? 'PROPUESTA DE PROYECTO PERSONALIZADO'
                      : 'LIMITACIÓN DE ESTIMACIÓN',
                  style: GoogleFonts.inter(
                    fontSize: 10.5,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.primary,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                decoration: BoxDecoration(
                  color: AppTheme.primary.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  'Confianza: ${propuesta['nivel_confianza'] ?? 'MEDIO'}',
                  style: GoogleFonts.inter(
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.primary,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          if (!viable) ...[
            Text(
              propuesta['motivo']?.toString() ??
                  'Información técnica o económica insuficiente para estimar el proyecto.',
              style: GoogleFonts.inter(fontSize: 12, color: titleColor, height: 1.35),
            ),
          ] else ...[
            if (propuesta['prototipo_destacado'] is Map) ...[
              ArchitecturalPrototypeCard(
                prototipo: Map<String, dynamic>.from(propuesta['prototipo_destacado'] as Map),
              ),
            ],
            if (terreno.isNotEmpty) ...[
              Text(
                'Terreno (${terreno['estado'] ?? 'POR_CONFIRMAR'}): ${terreno['nota'] ?? ''}',
                style: GoogleFonts.inter(fontSize: 11.5, color: subColor, height: 1.35),
              ),
              const SizedBox(height: 8),
            ],
            for (final esc in escenarios)
              Container(
                width: double.infinity,
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: borderColor),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          '${esc['escenario']} · ${esc['superficie_aprox_m2']} m²',
                          style: GoogleFonts.inter(
                            fontSize: 12,
                            fontWeight: FontWeight.w800,
                            color: titleColor,
                          ),
                        ),
                        Text(
                          '\$${esc['presupuesto_preliminar_usd']} USD',
                          style: GoogleFonts.inter(
                            fontSize: 12.5,
                            fontWeight: FontWeight.w900,
                            color: AppTheme.primary,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 3),
                    Text(
                      '${esc['estilo_nombre'] ?? ''} · Bs ${esc['presupuesto_preliminar_bob']} (\$${esc['costo_m2_usd']} USD/m²)',
                      style: GoogleFonts.inter(fontSize: 11, color: subColor),
                    ),
                  ],
                ),
              ),
          ],
          if (preguntas.isNotEmpty) ...[
            const SizedBox(height: 6),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: preguntas
                  .map(
                    (q) => ActionChip(
                      label: Text(q, style: const TextStyle(fontSize: 11)),
                      onPressed: _enviando
                          ? null
                          : () {
                              _inputController.text = q;
                              _inputController.selection = TextSelection.fromPosition(
                                TextPosition(offset: _inputController.text.length),
                              );
                            },
                    ),
                  )
                  .toList(),
            ),
          ],
          if (aviso.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              aviso,
              style: GoogleFonts.inter(
                fontSize: 10.5,
                fontStyle: FontStyle.italic,
                color: subColor,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildComparativaCard(
    Map<String, dynamic> comp,
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    final unidades = (comp['unidades'] as List? ?? [])
        .whereType<Map>()
        .map((e) => Map<String, dynamic>.from(e))
        .toList();
    if (unidades.isEmpty) return const SizedBox.shrink();

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'MATRIZ COMPARATIVA LADO A LADO',
            style: GoogleFonts.inter(
              fontSize: 10.5,
              fontWeight: FontWeight.w800,
              color: AppTheme.primary,
            ),
          ),
          const SizedBox(height: 8),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              headingRowHeight: 34,
              dataRowMinHeight: 32,
              dataRowMaxHeight: 44,
              columnSpacing: 16,
              columns: [
                DataColumn(
                  label: Text(
                    'Criterio',
                    style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w800),
                  ),
                ),
                for (final u in unidades)
                  DataColumn(
                    label: Text(
                      u['codigo_unidad']?.toString() ?? 'Unidad',
                      style: GoogleFonts.inter(
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.primary,
                      ),
                    ),
                  ),
              ],
              rows: [
                DataRow(
                  cells: [
                    const DataCell(Text('Precio USD', style: TextStyle(fontSize: 11.5))),
                    for (final u in unidades)
                      DataCell(
                        Text(
                          '\$${u["precio_usd"] ?? "—"}',
                          style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w700),
                        ),
                      ),
                  ],
                ),
                DataRow(
                  cells: [
                    const DataCell(Text('Superficie', style: TextStyle(fontSize: 11.5))),
                    for (final u in unidades)
                      DataCell(
                        Text(
                          '${u["superficie_m2"] ?? "—"} m²',
                          style: const TextStyle(fontSize: 11.5),
                        ),
                      ),
                  ],
                ),
                DataRow(
                  cells: [
                    const DataCell(Text('USD / m²', style: TextStyle(fontSize: 11.5))),
                    for (final u in unidades)
                      DataCell(
                        Text(
                          '\$${u["costo_m2_usd"] ?? "—"}',
                          style: const TextStyle(fontSize: 11.5),
                        ),
                      ),
                  ],
                ),
                DataRow(
                  cells: [
                    const DataCell(Text('Dorms / Baños', style: TextStyle(fontSize: 11.5))),
                    for (final u in unidades)
                      DataCell(
                        Text(
                          '${u["dormitorios"] ?? 0}D / ${u["banos"] ?? 0}B',
                          style: const TextStyle(fontSize: 11.5),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEstimacionYPlanoCard(
    CommercialChatMessage msg,
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    final est = msg.estimacionCosto;
    final lectura = msg.lecturaPlano;
    final resumenFin = (est?['resumen_financiero'] is Map)
        ? Map<String, dynamic>.from(est!['resumen_financiero'] as Map)
        : <String, dynamic>{};
    final params = (est?['parametros_entrada'] is Map)
        ? Map<String, dynamic>.from(est!['parametros_entrada'] as Map)
        : <String, dynamic>{};
    final estiloActual = (params['estilo_acabado'] ?? 'MINIMALISTA').toString().toUpperCase();
    final totalUsd = resumenFin['total_estimado_usd'] ?? '—';
    final totalBob = resumenFin['total_estimado_bob'] ?? '—';
    final costoM2Usd =
        resumenFin['costo_m2_usd'] ?? resumenFin['costo_unitario_m2_usd'] ?? '—';
    final ambientes = (lectura?['ambientes_detectados'] as List? ?? []);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.primary.withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'ESTIMACIÓN PARAMÉTRICA POR ESTILO',
                style: GoogleFonts.inter(
                  fontSize: 10.5,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.primary,
                ),
              ),
              if (_recalculandoEstilo)
                const SizedBox(
                  width: 14,
                  height: 14,
                  child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primary),
                ),
            ],
          ),
          if (ambientes.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              'Ambientes identificados en el plano:',
              style: GoogleFonts.inter(fontSize: 11.5, fontWeight: FontWeight.w700, color: titleColor),
            ),
            const SizedBox(height: 4),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: ambientes.map((a) {
                final label = a is Map
                    ? '${a["nombre"] ?? "Ambiente"} (${a["area_aprox_m2"] ?? ""} m²)'
                    : a.toString();
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF8FAFC),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: borderColor),
                  ),
                  child: Text(label, style: GoogleFonts.inter(fontSize: 10.5, color: subColor)),
                );
              }).toList(),
            ),
          ],
          if (est != null) ...[
            const SizedBox(height: 10),
            Text(
              '\$$totalUsd USD · Bs $totalBob',
              style: GoogleFonts.inter(
                fontSize: 16,
                fontWeight: FontWeight.w900,
                color: titleColor,
              ),
            ),
            Text(
              'Razón unitaria: \$$costoM2Usd USD/m² · Superficie: ${params["superficie_m2"] ?? "—"} m²',
              style: GoogleFonts.inter(fontSize: 11.5, color: subColor),
            ),
            const SizedBox(height: 10),
            Text(
              'Cambiar estilo arquitectónico en vivo:',
              style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w700, color: subColor),
            ),
            const SizedBox(height: 6),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: _estilosAcabadoCodigos.map((estCode) {
                final active = estiloActual == estCode;
                return ChoiceChip(
                  label: Text(estCode, style: const TextStyle(fontSize: 10.5)),
                  selected: active,
                  selectedColor: AppTheme.primary,
                  labelStyle: GoogleFonts.inter(
                    fontWeight: active ? FontWeight.w800 : FontWeight.w600,
                    color: active ? Colors.white : titleColor,
                  ),
                  onSelected: _recalculandoEstilo
                      ? null
                      : (_) => _cambiarEstiloEnMensajeComercial(msg, estCode),
                );
              }).toList(),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildFormularioContactoCrmCard(
    AuthProvider auth,
    CommercialChatMessage msg,
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
    Color subColor,
  ) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.primary.withValues(alpha: 0.45)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.support_agent_rounded, size: 18, color: AppTheme.primary),
              const SizedBox(width: 6),
              Text(
                'SOLICITAR CONTACTO COMERCIAL',
                style: GoogleFonts.inter(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.primary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          TextField(
            controller: _crmNombreCtrl,
            decoration: const InputDecoration(labelText: 'Nombre completo *'),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _crmTelefonoCtrl,
            keyboardType: TextInputType.phone,
            decoration: const InputDecoration(labelText: 'Teléfono / WhatsApp *'),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _crmEmailCtrl,
            keyboardType: TextInputType.emailAddress,
            decoration: const InputDecoration(labelText: 'Correo electrónico'),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _crmNotasCtrl,
            maxLines: 2,
            decoration: const InputDecoration(labelText: 'Notas o unidad de interés'),
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _enviandoContactoCrm
                  ? null
                  : () => _enviarContactoDesdeTarjeta(auth, msg),
              icon: const Icon(Icons.check_circle_outline_rounded, size: 16),
              label: Text(_enviandoContactoCrm ? 'Cargando…' : 'Registrar solicitud en CRM'),
            ),
          ),
        ],
      ),
    );
  }
}
