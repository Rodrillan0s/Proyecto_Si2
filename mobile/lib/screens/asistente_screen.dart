import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:speech_to_text/speech_to_text.dart';

import '../services/ai_assistant_service.dart';
import '../services/auth_provider.dart';
import '../services/reportes_voice.dart';
import '../theme/app_theme.dart';

class AsistenteScreen extends StatefulWidget {
  final int? idObraContexto;
  final String? nombreObraContexto;

  const AsistenteScreen({
    super.key,
    this.idObraContexto,
    this.nombreObraContexto,
  });

  @override
  State<AsistenteScreen> createState() => _AsistenteScreenState();
}

class _MensajeChat {
  final String emisor; // 'usuario' o 'asistente'
  final String texto;
  final DateTime fecha;
  final Map<String, dynamic>? propuesta;
  final Map<String, dynamic>? diagnostico;
  bool propuestaConfirmada = false;
  bool propuestaCancelada = false;
  bool ejecutandoAccion = false;

  _MensajeChat({
    required this.emisor,
    required this.texto,
    required this.fecha,
    this.propuesta,
    this.diagnostico,
  });
}

class _AsistenteScreenState extends State<AsistenteScreen> {
  final AiAssistantService _aiService = AiAssistantService();
  final TextEditingController _inputController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final SpeechToText _speech = ReportesVoice.speech;

  final List<_MensajeChat> _mensajes = [];
  bool _enviando = false;
  bool _escuchandoVoz = false;
  String? _conversacionId;
  int? _empresaSesion;
  int _requestEpoch = 0;

  @override
  void initState() {
    super.initState();
    _mensajes.add(
      _MensajeChat(
        emisor: 'asistente',
        texto: 'Hola. Soy el Asistente Inteligente Administrativo y Operativo de OBRATEC. '
            'Puedo asistirte con diagnósticos de proyectos, consultas del estado de obras, '
            'indicadores operativos y propuestas administrativas estructuradas.\n\n'
            '¿En qué puedo ayudarte hoy?',
        fecha: DateTime.now(),
      ),
    );
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final auth = Provider.of<AuthProvider>(context, listen: false);
    if (_empresaSesion != null && _empresaSesion != auth.idEmpresaActiva) {
      // Invalida conversación si cambia de empresa para prevenir mezclar contextos
      setState(() {
        _conversacionId = null;
        _requestEpoch++;
        _mensajes.clear();
        _mensajes.add(
          _MensajeChat(
            emisor: 'asistente',
            texto: 'Contexto de empresa actualizado. ¿En qué puedo ayudarte ahora?',
            fecha: DateTime.now(),
          ),
        );
      });
    }
    _empresaSesion = auth.idEmpresaActiva;
  }

  @override
  void dispose() {
    _detenerVoz();
    ReportesVoice.release(this);
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

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

  bool _tieneAcceso(AuthProvider auth) {
    return auth.esAdminGlobal || auth.esAdminEmpresa;
  }

  Future<void> _enviarMensaje() async {
    final texto = _inputController.text.trim();
    if (texto.isEmpty || _enviando) return;

    _inputController.clear();
    final auth = Provider.of<AuthProvider>(context, listen: false);
    final epoch = ++_requestEpoch;

    setState(() {
      _mensajes.add(
        _MensajeChat(
          emisor: 'usuario',
          texto: texto,
          fecha: DateTime.now(),
        ),
      );
      _enviando = true;
    });

    _scrollHaciaAbajo();

    try {
      final respuesta = await _aiService.enviarConsulta(
        texto: texto,
        conversacionId: _conversacionId,
        idEmpresa: auth.idEmpresaActiva,
        idObraContexto: widget.idObraContexto,
      );

      if (!mounted || epoch != _requestEpoch) return;

      final conversacion = respuesta['conversacion_id']?.toString() ??
          respuesta['conversacion']?.toString();
      if (conversacion != null && conversacion.isNotEmpty) {
        _conversacionId = conversacion;
      }

      final textoRespuesta = respuesta['respuesta']?.toString() ??
          respuesta['mensaje']?.toString() ??
          'Consulta procesada.';

      final propuesta = (respuesta['propuesta_operacion'] is Map)
          ? Map<String, dynamic>.from(respuesta['propuesta_operacion'])
          : null;

      final diagnostico = (respuesta['diagnostico'] is Map)
          ? Map<String, dynamic>.from(respuesta['diagnostico'])
          : null;

      setState(() {
        _mensajes.add(
          _MensajeChat(
            emisor: 'asistente',
            texto: textoRespuesta,
            fecha: DateTime.now(),
            propuesta: propuesta,
            diagnostico: diagnostico,
          ),
        );
        _enviando = false;
      });

      _scrollHaciaAbajo();
    } catch (e) {
      if (!mounted || epoch != _requestEpoch) return;
      setState(() {
        _mensajes.add(
          _MensajeChat(
            emisor: 'asistente',
            texto: 'Lo siento, ocurrió un error al procesar tu solicitud: '
                '${e.toString().replaceAll("Exception: ", "")}',
            fecha: DateTime.now(),
          ),
        );
        _enviando = false;
      });
      _scrollHaciaAbajo();
    }
  }

  Future<void> _confirmarPropuesta(_MensajeChat mensaje) async {
    final propuesta = mensaje.propuesta;
    if (propuesta == null || mensaje.ejecutandoAccion || mensaje.propuestaConfirmada) return;

    final idPropuesta = propuesta['id_propuesta']?.toString();
    if (idPropuesta == null || idPropuesta.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('ID de propuesta no válido.')),
      );
      return;
    }

    setState(() => mensaje.ejecutandoAccion = true);
    final auth = Provider.of<AuthProvider>(context, listen: false);

    try {
      final res = await _aiService.confirmarOperacion(
        idPropuesta: idPropuesta,
        idEmpresa: auth.idEmpresaActiva,
        idObraContexto: widget.idObraContexto,
      );

      if (!mounted) return;
      setState(() {
        mensaje.propuestaConfirmada = true;
        mensaje.ejecutandoAccion = false;
        _mensajes.add(
          _MensajeChat(
            emisor: 'asistente',
            texto: 'Operación confirmada y ejecutada exitosamente: '
                '${res["mensaje"] ?? res["resultado"] ?? "Cambios guardados en el sistema."}',
            fecha: DateTime.now(),
          ),
        );
      });
      _scrollHaciaAbajo();
    } catch (e) {
      if (!mounted) return;
      setState(() => mensaje.ejecutandoAccion = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.toString().replaceAll('Exception: ', '')),
          backgroundColor: AppTheme.error,
        ),
      );
    }
  }

  Future<void> _cancelarPropuesta(_MensajeChat mensaje) async {
    final propuesta = mensaje.propuesta;
    if (propuesta == null || mensaje.ejecutandoAccion || mensaje.propuestaCancelada) return;

    final idPropuesta = propuesta['id_propuesta']?.toString();
    if (idPropuesta == null || idPropuesta.isEmpty) return;

    setState(() => mensaje.ejecutandoAccion = true);

    try {
      await _aiService.cancelarOperacion(idPropuesta: idPropuesta);
      if (!mounted) return;
      setState(() {
        mensaje.propuestaCancelada = true;
        mensaje.ejecutandoAccion = false;
        _mensajes.add(
          _MensajeChat(
            emisor: 'asistente',
            texto: 'La propuesta de operación ha sido cancelada.',
            fecha: DateTime.now(),
          ),
        );
      });
      _scrollHaciaAbajo();
    } catch (e) {
      if (!mounted) return;
      setState(() => mensaje.ejecutandoAccion = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.toString().replaceAll('Exception: ', '')),
          backgroundColor: AppTheme.error,
        ),
      );
    }
  }

  void _scrollHaciaAbajo() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF131D31) : Colors.white;
    final borderColor = isDark ? const Color(0xFF22304C) : const Color(0xFFE2E8F0);
    final titleColor = isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A);

    // Verificación estricta de rol
    if (!_tieneAcceso(auth)) {
      return Scaffold(
        appBar: AppBar(
          title: Text(
            'Asistente',
            style: GoogleFonts.inter(fontWeight: FontWeight.w800),
          ),
        ),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(28.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: const BoxDecoration(
                    color: AppTheme.warningBg,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.lock_outline_rounded,
                    size: 48,
                    color: AppTheme.warning,
                  ),
                ),
                const SizedBox(height: 20),
                Text(
                  'Acceso Restringido',
                  style: GoogleFonts.inter(
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    color: titleColor,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'El Asistente Inteligente Administrativo y Operativo está disponible '
                  'exclusivamente para los roles de Administración y Gerencia de Empresa.',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.inter(
                    fontSize: 13.5,
                    color: isDark ? const Color(0xFF94A3B8) : const Color(0xFF64748B),
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

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
                    'Asistente OBRATEC',
                    style: GoogleFonts.inter(
                      fontSize: 15.5,
                      fontWeight: FontWeight.w800,
                      color: titleColor,
                    ),
                  ),
                  Text(
                    widget.nombreObraContexto != null
                        ? 'Obra: ${widget.nombreObraContexto}'
                        : (auth.empresaActivaNombre ?? 'Gestión Administrativa'),
                    style: GoogleFonts.inter(
                      fontSize: 11,
                      fontWeight: FontWeight.w500,
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
          IconButton(
            tooltip: 'Nueva conversación',
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () {
              setState(() {
                _conversacionId = null;
                _requestEpoch++;
                _mensajes.clear();
                _mensajes.add(
                  _MensajeChat(
                    emisor: 'asistente',
                    texto: 'Nueva conversación iniciada. ¿En qué puedo colaborarte?',
                    fecha: DateTime.now(),
                  ),
                );
              });
            },
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Listado de Mensajes
            Expanded(
              child: ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                itemCount: _mensajes.length,
                itemBuilder: (context, index) {
                  final msg = _mensajes[index];
                  return _buildMensajeItem(msg, isDark, cardBg, borderColor, titleColor);
                },
              ),
            ),

            // Indicador de escritura
            if (_enviando)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 6),
                child: Row(
                  children: [
                    const SizedBox(
                      width: 14,
                      height: 14,
                      child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primary),
                    ),
                    const SizedBox(width: 10),
                    Text(
                      'El asistente está analizando...',
                      style: GoogleFonts.inter(fontSize: 12, color: AppTheme.primary),
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
                      child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primary),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Escuchando... Habla con claridad.',
                        style: GoogleFonts.inter(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.primary,
                        ),
                      ),
                    ),
                    InkWell(
                      onTap: _detenerVoz,
                      child: const Icon(Icons.stop_circle_outlined, color: AppTheme.error, size: 22),
                    ),
                  ],
                ),
              ),

            // Barra de entrada de texto
            Container(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
              decoration: BoxDecoration(
                color: cardBg,
                border: Border(top: BorderSide(color: borderColor)),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _inputController,
                      textCapitalization: TextCapitalization.sentences,
                      maxLines: 3,
                      minLines: 1,
                      style: GoogleFonts.inter(fontSize: 13.5),
                      decoration: InputDecoration(
                        hintText: _escuchandoVoz ? 'Escuchando tu voz...' : 'Escribe tu consulta o instrucción...',
                        hintStyle: GoogleFonts.inter(fontSize: 13, color: const Color(0xFF94A3B8)),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        filled: true,
                        fillColor: isDark ? const Color(0xFF0B0F19) : const Color(0xFFF1F5F9),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(20),
                          borderSide: BorderSide.none,
                        ),
                      ),
                      onSubmitted: (_) => _enviarMensaje(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  // Botón de micrófono para comandos de voz
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
                      tooltip: _escuchandoVoz ? 'Detener escucha' : 'Preguntar por voz',
                      onPressed: _enviando ? null : _conmutarVoz,
                    ),
                  ),
                  const SizedBox(width: 8),
                  // Botón enviar
                  Container(
                    decoration: const BoxDecoration(
                      color: AppTheme.primary,
                      shape: BoxShape.circle,
                    ),
                    child: IconButton(
                      icon: const Icon(Icons.arrow_upward_rounded, color: Colors.white, size: 20),
                      onPressed: _enviando ? null : _enviarMensaje,
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

  Widget _buildMensajeItem(
    _MensajeChat msg,
    bool isDark,
    Color cardBg,
    Color borderColor,
    Color titleColor,
  ) {
    final esUsuario = msg.emisor == 'usuario';

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: esUsuario ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: esUsuario ? MainAxisAlignment.end : MainAxisAlignment.start,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (!esUsuario)
                Container(
                  margin: const EdgeInsets.only(right: 8, top: 2),
                  padding: const EdgeInsets.all(5),
                  decoration: BoxDecoration(
                    color: AppTheme.primary,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.auto_awesome_rounded, color: Colors.white, size: 14),
                ),
              Flexible(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
                  decoration: BoxDecoration(
                    color: esUsuario
                        ? AppTheme.primary
                        : (isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9)),
                    borderRadius: BorderRadius.only(
                      topLeft: const Radius.circular(14),
                      topRight: const Radius.circular(14),
                      bottomLeft: Radius.circular(esUsuario ? 14 : 2),
                      bottomRight: Radius.circular(esUsuario ? 2 : 14),
                    ),
                  ),
                  child: Text(
                    msg.texto,
                    style: GoogleFonts.inter(
                      fontSize: 13.5,
                      color: esUsuario
                          ? Colors.white
                          : (isDark ? const Color(0xFFF8FAFC) : const Color(0xFF0F172A)),
                      height: 1.4,
                    ),
                  ),
                ),
              ),
            ],
          ),

          // Tarjeta de Diagnóstico (si existe)
          if (msg.diagnostico != null) ...[
            const SizedBox(height: 10),
            _buildDiagnosticoCard(msg.diagnostico!, isDark, cardBg, borderColor),
          ],

          // Tarjeta de Propuesta de Operación (si existe)
          if (msg.propuesta != null) ...[
            const SizedBox(height: 10),
            _buildPropuestaCard(msg, isDark, cardBg, borderColor),
          ],
        ],
      ),
    );
  }

  Widget _buildDiagnosticoCard(
    Map<String, dynamic> diagnostico,
    bool isDark,
    Color cardBg,
    Color borderColor,
  ) {
    final riesgo = (diagnostico['nivel_riesgo'] ?? 'MEDIO').toString().toUpperCase();
    final indicadores = diagnostico['indicadores'] as List? ?? [];
    final recomendaciones = diagnostico['recomendaciones'] as List? ?? [];

    Color riesgoColor = AppTheme.info;
    if (riesgo.contains('ALTO') || riesgo.contains('CRITICO')) riesgoColor = AppTheme.error;
    if (riesgo.contains('MEDIO')) riesgoColor = AppTheme.warning;
    if (riesgo.contains('BAJO')) riesgoColor = AppTheme.success;

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(left: 28),
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
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0.5,
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
                    fontWeight: FontWeight.w700,
                    color: riesgoColor,
                  ),
                ),
              ),
            ],
          ),
          if (indicadores.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              'Indicadores:',
              style: GoogleFonts.inter(fontSize: 11.5, fontWeight: FontWeight.w700),
            ),
            ...indicadores.map((ind) => Padding(
                  padding: const EdgeInsets.only(top: 2, left: 6),
                  child: Text(
                    '• $ind',
                    style: GoogleFonts.inter(fontSize: 12, color: const Color(0xFF64748B)),
                  ),
                )),
          ],
          if (recomendaciones.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              'Recomendaciones:',
              style: GoogleFonts.inter(fontSize: 11.5, fontWeight: FontWeight.w700),
            ),
            ...recomendaciones.map((rec) => Padding(
                  padding: const EdgeInsets.only(top: 2, left: 6),
                  child: Text(
                    '• $rec',
                    style: GoogleFonts.inter(fontSize: 12, color: const Color(0xFF64748B)),
                  ),
                )),
          ],
        ],
      ),
    );
  }

  Widget _buildPropuestaCard(
    _MensajeChat msg,
    bool isDark,
    Color cardBg,
    Color borderColor,
  ) {
    final p = msg.propuesta!;
    final tipo = p['tipo_operacion']?.toString() ?? 'OPERACIÓN';
    final desc = p['descripcion']?.toString() ?? 'Propuesta administrativa generada';

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(left: 28),
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
            children: [
              const Icon(Icons.shield_outlined, size: 16, color: AppTheme.primary),
              const SizedBox(width: 6),
              Text(
                'PROPUESTA DE ACCIÓN ADMINISTRATIVA',
                style: GoogleFonts.inter(
                  fontSize: 10.5,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.primary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            tipo,
            style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 4),
          Text(
            desc,
            style: GoogleFonts.inter(fontSize: 12.5, color: const Color(0xFF64748B), height: 1.3),
          ),
          const SizedBox(height: 12),
          if (msg.propuestaConfirmada)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: AppTheme.successBg,
                borderRadius: BorderRadius.circular(6),
              ),
              child: Row(
                children: [
                  const Icon(Icons.check_circle_rounded, size: 16, color: AppTheme.success),
                  const SizedBox(width: 6),
                  Text(
                    'Operación confirmada',
                    style: GoogleFonts.inter(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      color: AppTheme.success,
                    ),
                  ),
                ],
              ),
            )
          else if (msg.propuestaCancelada)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: AppTheme.errorBg,
                borderRadius: BorderRadius.circular(6),
              ),
              child: Row(
                children: [
                  const Icon(Icons.cancel_rounded, size: 16, color: AppTheme.error),
                  const SizedBox(width: 6),
                  Text(
                    'Propuesta cancelada',
                    style: GoogleFonts.inter(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      color: AppTheme.error,
                    ),
                  ),
                ],
              ),
            )
          else
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: msg.ejecutandoAccion ? null : () => _cancelarPropuesta(msg),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      side: BorderSide(color: borderColor),
                    ),
                    child: Text(
                      'Cancelar',
                      style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w700),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton(
                    onPressed: msg.ejecutandoAccion ? null : () => _confirmarPropuesta(msg),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      backgroundColor: AppTheme.primary,
                      foregroundColor: Colors.white,
                    ),
                    child: msg.ejecutandoAccion
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : Text(
                            'Confirmar',
                            style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w800),
                          ),
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }
}
