import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';
import 'dart:convert';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../services/ruta_service.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class EntregasScreen extends StatefulWidget {
  const EntregasScreen({super.key});

  @override
  State<EntregasScreen> createState() => _EntregasScreenState();
}

class _EntregasScreenState extends State<EntregasScreen> {
  bool loading = true;
  String message = '';
  String filtroEstado = 'TODAS';
  List<RutaLogistica> rutas = [];

  List<RutaLogistica> get rutasFiltradas {
    if (filtroEstado == 'TODAS') return rutas;
    return rutas.where((r) => r.estado.toUpperCase() == filtroEstado).toList();
  }

  @override
  void initState() {
    super.initState();
    cargarRutas();
  }

  Future<void> cargarRutas() async {
    setState(() { loading = true; message = ''; });
    final result = await RutaService.obtenerMisRutas();
    if (!mounted) return;
    setState(() { loading = false; rutas = result.rutas; message = result.success ? '' : result.message; });
  }

  void abrirDetalle(RutaLogistica ruta) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.backgroundBlue,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(18)),
      ),
      builder: (_) => EntregaDetalleSheet(ruta: ruta, onSaved: () async {
        Navigator.pop(context);
        await cargarRutas();
      }),
    );
  }

  @override
  Widget build(BuildContext context) {
    final lista = rutasFiltradas;
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: SafeArea(
        child: Column(
          children: [
            _buildTopBar(),
            Expanded(
              child: RefreshIndicator(
                onRefresh: cargarRutas,
                color: AppTheme.primaryGreen,
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _buildHeader(),
                    const SizedBox(height: 12),
                    _buildFiltros(),
                    if (message.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      AgroErrorBox(message: message),
                    ],
                    const SizedBox(height: 16),
                    if (loading) _buildLoading()
                    else if (lista.isEmpty) _buildEmpty()
                    else ...lista.map(_buildRutaCard),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTopBar() {
    return Container(
      color: AppTheme.primaryGreen,
      padding: const EdgeInsets.fromLTRB(10, 10, 12, 12),
      child: Row(
        children: [
          IconButton(
            onPressed: () => Navigator.pop(context),
            style: IconButton.styleFrom(backgroundColor: Colors.white.withOpacity(0.12), foregroundColor: Colors.white),
            icon: const Icon(Icons.arrow_back),
          ),
          const SizedBox(width: 8),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('ENTREGAS', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1)),
                SizedBox(height: 2),
                Text('Rutas de distribución asignadas', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: Colors.white70, letterSpacing: 0.6)),
              ],
            ),
          ),
          IconButton(
            onPressed: cargarRutas,
            style: IconButton.styleFrom(backgroundColor: Colors.white.withOpacity(0.12), foregroundColor: Colors.white),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, border: Border.all(color: AppTheme.borderColor), borderRadius: BorderRadius.circular(10)),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              SizedBox(width: 7, height: 30, child: DecoratedBox(decoration: BoxDecoration(color: AppTheme.primaryGreen))),
              SizedBox(width: 10),
              Expanded(child: Text('MIS ENTREGAS', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: AppTheme.slateText))),
            ],
          ),
          Padding(
            padding: EdgeInsets.only(left: 17, top: 4),
            child: Text('Rutas asignadas para distribución', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: AppTheme.mutedText, letterSpacing: 1)),
          ),
        ],
      ),
    );
  }

  Widget _buildFiltros() {
    final estados = ['TODAS', 'ASIGNADA', 'ENTREGADA', 'CANCELADA'];
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: estados.map((est) {
          final activo = filtroEstado == est;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: _buildFiltroChip(est, activo),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildFiltroChip(String label, bool activo) {
    return GestureDetector(
      onTap: () => setState(() => filtroEstado = label),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: activo ? AppTheme.primaryGreen : Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: activo ? AppTheme.primaryGreen : AppTheme.borderColor),
        ),
        child: Text(label, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: activo ? Colors.white : AppTheme.mutedText, letterSpacing: 0.7)),
      ),
    );
  }

  Widget _buildLoading() {
    return const Center(child: Padding(
      padding: EdgeInsets.all(40),
      child: CircularProgressIndicator(color: AppTheme.primaryGreen),
    ));
  }

  Widget _buildEmpty() {
    return Container(
      padding: const EdgeInsets.all(40),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14), border: Border.all(color: AppTheme.borderColor)),
      child: const Center(child: Text('No hay rutas asignadas', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.mutedText))),
    );
  }

  String getEstadoLabel(String est) {
    switch (est.toUpperCase()) {
      case 'ASIGNADA': return 'PENDIENTE';
      case 'ENTREGADA': return 'ENTREGADO';
      case 'CANCELADA': return 'CANCELADO';
      default: return est;
    }
  }

  Color getEstadoColor(String est) {
    switch (est.toUpperCase()) {
      case 'ASIGNADA': return Colors.blue;
      case 'ENTREGADA': return Colors.green;
      case 'CANCELADA': return Colors.red;
      default: return Colors.grey;
    }
  }

  Widget _buildRutaCard(RutaLogistica ruta) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        child: InkWell(
          onTap: ruta.estado == 'ASIGNADA' ? () => abrirDetalle(ruta) : null,
          borderRadius: BorderRadius.circular(14),
          child: Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(borderRadius: BorderRadius.circular(14), border: Border.all(color: AppTheme.borderColor)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(color: getEstadoColor(ruta.estado).withOpacity(0.10), borderRadius: BorderRadius.circular(20)),
                      child: Text(getEstadoLabel(ruta.estado), style: TextStyle(fontSize: 8, fontWeight: FontWeight.w900, color: getEstadoColor(ruta.estado), letterSpacing: 0.8)),
                    ),
                    const Spacer(),
                    Text('RUTA #${ruta.idRuta}', style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: AppTheme.mutedText, letterSpacing: 0.6)),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    const Icon(Icons.person, size: 14, color: AppTheme.mutedText),
                    const SizedBox(width: 6),
                    Expanded(child: Text(ruta.clienteNombre, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w900, color: AppTheme.slateText))),
                  ],
                ),
                const SizedBox(height: 6),
                Row(
                  children: [
                    const Icon(Icons.location_on, size: 14, color: AppTheme.mutedText),
                    const SizedBox(width: 6),
                    Expanded(child: Text(ruta.destino, style: const TextStyle(fontSize: 11, color: AppTheme.mutedText))),
                  ],
                ),
                const SizedBox(height: 6),
                Row(
                  children: [
                    const Icon(Icons.receipt, size: 14, color: AppTheme.mutedText),
                    const SizedBox(width: 6),
                    Text('Bs.${ruta.montoTotal.toStringAsFixed(2)}', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen)),
                    const Spacer(),
                    Text(ruta.fechaEntregaEstimada, style: const TextStyle(fontSize: 10, color: AppTheme.mutedText)),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class EntregaDetalleSheet extends StatefulWidget {
  final RutaLogistica ruta;
  final Future<void> Function() onSaved;

  const EntregaDetalleSheet({super.key, required this.ruta, required this.onSaved});

  @override
  State<EntregaDetalleSheet> createState() => _EntregaDetalleSheetState();
}

class _EntregaDetalleSheetState extends State<EntregaDetalleSheet> {
  bool saving = false;
  bool grabandoAudio = false;
  final AudioRecorder audioRecorder = AudioRecorder();
  final TextEditingController observacionesController = TextEditingController();

  String? imagenBase64;
  String? audioBase64;
  String? imagenNombre;
  String? audioNombre;

  @override
  void dispose() {
    observacionesController.dispose();
    audioRecorder.dispose();
    super.dispose();
  }

  Future<void> iniciarGrabacionAudio() async {
    final tienePermiso = await audioRecorder.hasPermission();
    if (!tienePermiso) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('No se otorgó permiso para el micrófono.')));
      return;
    }
    final dir = await getTemporaryDirectory();
    final path = '${dir.path}/entrega_${widget.ruta.idRuta}_${DateTime.now().millisecondsSinceEpoch}.m4a';
    await audioRecorder.start(const RecordConfig(encoder: AudioEncoder.aacLc, bitRate: 64000, sampleRate: 44100), path: path);
    if (!mounted) return;
    setState(() { grabandoAudio = true; audioNombre = 'Grabando audio...'; });
  }

  Future<void> detenerGrabacionAudio() async {
    final path = await audioRecorder.stop();
    if (!mounted) return;
    setState(() { grabandoAudio = false; });
    if (path == null) return;
    final file = File(path);
    final bytes = await file.readAsBytes();
    setState(() { audioBase64 = 'data:audio/mp4;base64,${base64Encode(bytes)}'; audioNombre = 'Audio grabado'; });
  }

  Future<void> seleccionarImagen() async {
    final file = await _EntregaBase64Service.pickImageFromGallery();
    if (file == null) return;
    setState(() { imagenBase64 = file.dataUrl; imagenNombre = file.name; });
  }

  Future<void> tomarFoto() async {
    final file = await _EntregaBase64Service.takePhoto();
    if (file == null) return;
    setState(() { imagenBase64 = file.dataUrl; imagenNombre = file.name; });
  }

  Future<void> seleccionarAudio() async {
    final file = await _EntregaBase64Service.pickAudio();
    if (file == null) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('No se pudo cargar el audio.')));
      return;
    }
    setState(() { audioBase64 = file.dataUrl; audioNombre = file.name; });
  }

  Future<void> confirmarEntrega() async {
    if (imagenBase64 == null && audioBase64 == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Debes adjuntar al menos una evidencia (foto o audio).')));
      return;
    }
    setState(() { saving = true; });
    final result = await RutaService.confirmarEntrega(
      idRuta: widget.ruta.idRuta,
      observaciones: observacionesController.text.trim(),
      urlEvidenciaImagen: imagenBase64,
      urlEvidenciaAudio: audioBase64,
    );
    if (!mounted) return;
    setState(() { saving = false; });
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result.message)));
    if (!result.success) return;
    await widget.onSaved();
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.88,
        minChildSize: 0.50,
        maxChildSize: 0.95,
        builder: (context, scrollController) {
          return ListView(
            controller: scrollController,
            padding: const EdgeInsets.all(18),
            children: [
              Container(
                width: 40, height: 4,
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(color: Colors.grey.shade300, borderRadius: BorderRadius.circular(10)),
              ),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(color: AppTheme.primaryGreen, borderRadius: BorderRadius.circular(14)),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('CONFIRMAR ENTREGA', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: Colors.white70, letterSpacing: 1.5)),
                    const SizedBox(height: 8),
                    Text(widget.ruta.clienteNombre, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: Colors.white)),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        const Icon(Icons.location_on, size: 14, color: Colors.white70),
                        const SizedBox(width: 4),
                        Expanded(child: Text(widget.ruta.destino, style: const TextStyle(fontSize: 12, color: Colors.white70))),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        _buildWhiteBadge('ORD-${widget.ruta.nroTransaccion.toString().padLeft(5, '0')}'),
                        const SizedBox(width: 8),
                        _buildWhiteBadge('Bs.${widget.ruta.montoTotal.toStringAsFixed(2)}'),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              const Text('OBSERVACIONES', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: AppTheme.slateText, letterSpacing: 0.8)),
              const SizedBox(height: 8),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('NOTAS DE ENTREGA', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: AppTheme.mutedText, letterSpacing: 1.2)),
                  const SizedBox(height: 6),
                  TextFormField(
                    controller: observacionesController,
                    maxLines: 3,
                    decoration: const InputDecoration(
                      hintText: 'Estado del pedido, novedades...',
                      hintStyle: TextStyle(fontSize: 13, color: Colors.grey),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              _buildEvidenciaPanel(),
              const SizedBox(height: 20),
              AgroButton(
                text: 'CONFIRMAR ENTREGA',
                loading: saving,
                onPressed: confirmarEntrega,
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildWhiteBadge(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(color: Colors.white.withOpacity(0.14), borderRadius: BorderRadius.circular(20), border: Border.all(color: Colors.white24)),
      child: Text(text, style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 0.5)),
    );
  }

  Widget _buildEvidenciaPanel() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: AppTheme.borderColor)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('EVIDENCIA DIGITAL', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: AppTheme.slateText, letterSpacing: 0.8)),
          const SizedBox(height: 12),
          Text('Fotografía', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: AppTheme.mutedText)),
          const SizedBox(height: 6),
          Row(
            children: [
              Expanded(child: _buildEvidenciaBtn('Galería', Icons.photo_library, seleccionarImagen)),
              const SizedBox(width: 8),
              Expanded(child: _buildEvidenciaBtn('Cámara', Icons.camera_alt, tomarFoto)),
            ],
          ),
          if (imagenBase64 != null) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(color: Colors.green.shade50, borderRadius: BorderRadius.circular(8)),
              child: Row(
                children: [
                  const Icon(Icons.check_circle, size: 14, color: Colors.green),
                  const SizedBox(width: 6),
                  Expanded(child: Text(imagenNombre ?? 'Foto adjuntada', style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: Colors.green))),
                  GestureDetector(onTap: () => setState(() { imagenBase64 = null; imagenNombre = null; }), child: const Icon(Icons.close, size: 14, color: Colors.red)),
                ],
              ),
            ),
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Image.memory(
                _EntregaBase64Service.bytesFromDataUrl(imagenBase64) ?? Uint8List(0),
                height: 120, width: double.infinity, fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => Container(height: 120, color: Colors.grey.shade100, child: const Center(child: Text('Vista previa no disponible', style: TextStyle(fontSize: 10)))),
              ),
            ),
          ],
          const SizedBox(height: 14),
          const Divider(height: 1),
          const SizedBox(height: 14),
          const Text('Audio / Voz', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: AppTheme.mutedText)),
          const SizedBox(height: 6),
          Row(
            children: [
              Expanded(child: _buildEvidenciaBtn(grabandoAudio ? 'Grabando...' : 'Grabar audio', Icons.mic, grabandoAudio ? detenerGrabacionAudio : iniciarGrabacionAudio)),
              const SizedBox(width: 8),
              Expanded(child: _buildEvidenciaBtn('Cargar audio', Icons.audiotrack, seleccionarAudio)),
            ],
          ),
          if (audioBase64 != null) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(color: Colors.green.shade50, borderRadius: BorderRadius.circular(8)),
              child: Row(
                children: [
                  const Icon(Icons.check_circle, size: 14, color: Colors.green),
                  const SizedBox(width: 6),
                  Expanded(child: Text(audioNombre ?? 'Audio adjuntado', style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: Colors.green))),
                  GestureDetector(onTap: () => setState(() { audioBase64 = null; audioNombre = null; }), child: const Icon(Icons.close, size: 14, color: Colors.red)),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildEvidenciaBtn(String label, IconData icon, VoidCallback onTap) {
    return OutlinedButton.icon(
      onPressed: onTap,
      icon: Icon(icon, size: 16),
      label: Text(label, style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w900)),
      style: OutlinedButton.styleFrom(
        foregroundColor: AppTheme.primaryGreen,
        side: const BorderSide(color: AppTheme.primaryGreen),
        padding: const EdgeInsets.symmetric(vertical: 10),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    );
  }
}

class _EntregaBase64File {
  final String name;
  final String mimeType;
  final String dataUrl;
  _EntregaBase64File({required this.name, required this.mimeType, required this.dataUrl});
}

class _EntregaBase64Service {
  static final ImagePicker _picker = ImagePicker();

  static Future<_EntregaBase64File?> pickImageFromGallery() async {
    final file = await _picker.pickImage(source: ImageSource.gallery, imageQuality: 55, maxWidth: 900, maxHeight: 900);
    if (file == null) return null;
    final bytes = await file.readAsBytes();
    final mime = _getImageMime(file.path);
    return _EntregaBase64File(name: _fileName(file.path), mimeType: mime, dataUrl: 'data:$mime;base64,${base64Encode(bytes)}');
  }

  static Future<_EntregaBase64File?> takePhoto() async {
    final file = await _picker.pickImage(source: ImageSource.camera, imageQuality: 55, maxWidth: 900, maxHeight: 900);
    if (file == null) return null;
    final bytes = await file.readAsBytes();
    final mime = _getImageMime(file.path);
    return _EntregaBase64File(name: _fileName(file.path), mimeType: mime, dataUrl: 'data:$mime;base64,${base64Encode(bytes)}');
  }

  static Future<_EntregaBase64File?> pickAudio() async {
    final result = await FilePicker.platform.pickFiles(type: FileType.audio, allowMultiple: false, withData: true);
    if (result == null || result.files.isEmpty) return null;
    final picked = result.files.single;
    final bytes = picked.bytes;
    if (bytes == null) return null;
    final mime = _getAudioMime(picked.name);
    return _EntregaBase64File(name: picked.name, mimeType: mime, dataUrl: 'data:$mime;base64,${base64Encode(bytes)}');
  }

  static Uint8List? bytesFromDataUrl(String? dataUrl) {
    if (dataUrl == null) return null;
    try {
      final base64Part = dataUrl.split('base64,').last;
      return base64Decode(base64Part);
    } catch (_) { return null; }
  }

  static String _fileName(String path) => path.split('/').last.split('\\').last;

  static String _getImageMime(String path) {
    final lower = path.toLowerCase();
    if (lower.endsWith('.png')) return 'image/png';
    if (lower.endsWith('.webp')) return 'image/webp';
    return 'image/jpeg';
  }

  static String _getAudioMime(String path) {
    final lower = path.toLowerCase();
    if (lower.endsWith('.mp3')) return 'audio/mpeg';
    if (lower.endsWith('.wav')) return 'audio/wav';
    if (lower.endsWith('.m4a')) return 'audio/mp4';
    if (lower.endsWith('.aac')) return 'audio/aac';
    if (lower.endsWith('.ogg')) return 'audio/ogg';
    return 'audio/mpeg';
  }
}
