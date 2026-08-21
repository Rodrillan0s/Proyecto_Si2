import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';
import 'dart:convert';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../services/orden_service.dart';
import '../services/token_storage.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class OrdenesScreen extends StatefulWidget {
  const OrdenesScreen({super.key});

  @override
  State<OrdenesScreen> createState() => _OrdenesScreenState();
}

class _OrdenesScreenState extends State<OrdenesScreen> {
  bool loading = true;
  String message = '';
  String filtroEstado = 'TODAS';

  int? userId;
  int? userRole;

  List<OrdenTrabajo> ordenes = [];

  List<OrdenTrabajo> get ordenesFiltradas {
    if (filtroEstado == 'TODAS') return ordenes;

    return ordenes.where((orden) {
      return orden.estado.toUpperCase() == filtroEstado;
    }).toList();
  }

  @override
  void initState() {
    super.initState();
    cargarDatos();
  }

  Future<void> cargarDatos() async {
    final currentUserId = await TokenStorage.getUserId();
    final currentRole = await TokenStorage.getUserRole();

    if (!mounted) return;

    setState(() {
      userId = currentUserId;
      userRole = currentRole;
    });

    await cargarOrdenes();
  }

  Future<void> cargarOrdenes() async {
    setState(() {
      loading = true;
      message = '';
    });

    final result = await OrdenService.obtenerOrdenes();

    if (!mounted) return;

    setState(() {
      loading = false;
      ordenes = result.ordenes;
      message = result.success ? '' : result.message;
    });
  }

  bool puedeEditar(OrdenTrabajo orden) {
    return userRole == 3 && orden.idEmpleado == userId;
  }

  void abrirDetalle(OrdenTrabajo orden) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.backgroundBlue,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(18),
        ),
      ),
      builder: (_) {
        return OrdenDetalleSheet(
          orden: orden,
          editable: puedeEditar(orden),
          onSaved: () async {
            Navigator.pop(context);
            await cargarOrdenes();
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final lista = ordenesFiltradas;

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: SafeArea(
        child: Column(
          children: [
            _buildTopBar(),
            Expanded(
              child: RefreshIndicator(
                onRefresh: cargarOrdenes,
                color: AppTheme.primaryGreen,
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _buildHeader(),
                    const SizedBox(height: 12),
                    _buildStats(),
                    const SizedBox(height: 12),
                    _buildFiltros(),
                    if (message.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      AgroErrorBox(message: message),
                    ],
                    const SizedBox(height: 16),
                    if (loading)
                      _buildLoading()
                    else if (lista.isEmpty)
                      _buildEmpty()
                    else
                      ...lista.map(_buildOrdenCard),
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
            onPressed: () {
              Navigator.pop(context);
            },
            style: IconButton.styleFrom(
              backgroundColor: Colors.white.withOpacity(0.12),
              foregroundColor: Colors.white,
            ),
            icon: const Icon(Icons.arrow_back),
          ),
          const SizedBox(width: 8),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'ÓRDENES DE TRABAJO',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w900,
                    color: Colors.white,
                    letterSpacing: 1,
                  ),
                ),
                SizedBox(height: 2),
                Text(
                  'Seguimiento de actividades agrícolas',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    color: Colors.white70,
                    letterSpacing: 0.6,
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: cargarOrdenes,
            style: IconButton.styleFrom(
              backgroundColor: Colors.white.withOpacity(0.12),
              foregroundColor: Colors.white,
            ),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(10),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              SizedBox(
                width: 7,
                height: 30,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: AppTheme.primaryGreen,
                  ),
                ),
              ),
              SizedBox(width: 10),
              Expanded(
                child: Text(
                  'GESTIÓN DE ÓRDENES',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                    color: AppTheme.slateText,
                  ),
                ),
              ),
            ],
          ),
          Padding(
            padding: EdgeInsets.only(left: 17, top: 4),
            child: Text(
              'Lista, detalle y actualización de reportes',
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w900,
                color: AppTheme.mutedText,
                letterSpacing: 1,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStats() {
    final pendientes = ordenes.where((o) {
      return o.estado.toUpperCase() == 'PENDIENTE';
    }).length;

    final proceso = ordenes.where((o) {
      return o.estado.toUpperCase() == 'EN PROCESO';
    }).length;

    final finalizadas = ordenes.where((o) {
      return o.estado.toUpperCase() == 'FINALIZADA';
    }).length;

    return Row(
      children: [
        Expanded(
          child: _buildStatTile(
            label: 'PEND.',
            value: pendientes.toString(),
            color: Colors.amber.shade700,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _buildStatTile(
            label: 'PROC.',
            value: proceso.toString(),
            color: Colors.blue.shade700,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _buildStatTile(
            label: 'FIN.',
            value: finalizadas.toString(),
            color: Colors.green.shade700,
          ),
        ),
      ],
    );
  }

  Widget _buildStatTile({
    required String label,
    required String value,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(9),
      ),
      child: Column(
        children: [
          Text(
            value,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w900,
              color: color,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            label,
            style: const TextStyle(
              fontSize: 9,
              fontWeight: FontWeight.w900,
              color: AppTheme.mutedText,
              letterSpacing: 1,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFiltros() {
    return Row(
      children: [
        _buildFiltroButton('TODAS'),
        const SizedBox(width: 7),
        _buildFiltroButton('PENDIENTE'),
        const SizedBox(width: 7),
        _buildFiltroButton('EN PROCESO'),
        const SizedBox(width: 7),
        _buildFiltroButton('FINALIZADA'),
      ],
    );
  }

  Widget _buildFiltroButton(String value) {
    final selected = filtroEstado == value;

    return Expanded(
      child: InkWell(
        onTap: () {
          setState(() {
            filtroEstado = value;
          });
        },
        borderRadius: BorderRadius.circular(30),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 9),
          decoration: BoxDecoration(
            color: selected ? AppTheme.primaryGreen : Colors.white,
            border: Border.all(
              color: selected ? AppTheme.primaryGreen : AppTheme.borderColor,
            ),
            borderRadius: BorderRadius.circular(30),
          ),
          child: Text(
            value == 'EN PROCESO' ? 'PROCESO' : value,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 8,
              fontWeight: FontWeight.w900,
              color: selected ? Colors.white : AppTheme.mutedText,
              letterSpacing: 0.5,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildOrdenCard(OrdenTrabajo orden) {
    final editable = puedeEditar(orden);

    return InkWell(
      onTap: () => abrirDetalle(orden),
      borderRadius: BorderRadius.circular(10),
      child: Container(
        margin: const EdgeInsets.only(bottom: 11),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border.all(color: AppTheme.borderColor),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Stack(
          children: [
            Positioned(
              left: -14,
              top: -14,
              bottom: -14,
              child: Container(
                width: 5,
                color: _estadoColor(orden.estado),
              ),
            ),
            Padding(
              padding: const EdgeInsets.only(left: 6),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          'ORDEN #${orden.nroOrden.toString().padLeft(5, '0')}',
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w900,
                            color: AppTheme.slateText,
                          ),
                        ),
                      ),
                      _buildEstadoBadge(orden.estado),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    orden.tipoTrabajo.toUpperCase(),
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w900,
                      color: AppTheme.primaryGreen,
                      letterSpacing: 0.7,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Inicio: ${orden.fechaInicio}',
                    style: const TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      color: AppTheme.mutedText,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    'Empleado: ${orden.empleadoUsername.isEmpty ? 'Sin asignar' : orden.empleadoUsername}',
                    style: const TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      color: AppTheme.mutedText,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      _buildEvidenceMini(
                        icon: Icons.image_outlined,
                        active: orden.urlImagen.isNotEmpty,
                      ),
                      const SizedBox(width: 8),
                      _buildEvidenceMini(
                        icon: Icons.audiotrack,
                        active: orden.urlAudio.isNotEmpty,
                      ),
                      const Spacer(),
                      if (editable)
                        const Text(
                          'EDITABLE',
                          style: TextStyle(
                            fontSize: 9,
                            fontWeight: FontWeight.w900,
                            color: AppTheme.primaryGreen,
                            letterSpacing: 1,
                          ),
                        ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEvidenceMini({
    required IconData icon,
    required bool active,
  }) {
    return Container(
      padding: const EdgeInsets.all(6),
      decoration: BoxDecoration(
        color: active
            ? AppTheme.primaryGreen.withOpacity(0.10)
            : const Color(0xFFF1F5F9),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Icon(
        icon,
        size: 16,
        color: active ? AppTheme.primaryGreen : AppTheme.mutedText,
      ),
    );
  }

  Widget _buildEstadoBadge(String estado) {
    final color = _estadoColor(estado);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: color.withOpacity(0.10),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        estado.toUpperCase(),
        style: TextStyle(
          fontSize: 8,
          fontWeight: FontWeight.w900,
          color: color,
          letterSpacing: 0.7,
        ),
      ),
    );
  }

  Color _estadoColor(String estado) {
    final value = estado.toUpperCase();

    if (value == 'FINALIZADA') return Colors.green.shade700;
    if (value == 'EN PROCESO') return Colors.blue.shade700;

    return Colors.amber.shade700;
  }

  Widget _buildLoading() {
    return const Padding(
      padding: EdgeInsets.all(34),
      child: Center(
        child: CircularProgressIndicator(
          color: AppTheme.primaryGreen,
        ),
      ),
    );
  }

  Widget _buildEmpty() {
    return const Padding(
      padding: EdgeInsets.all(34),
      child: Column(
        children: [
          Icon(
            Icons.assignment_outlined,
            size: 46,
            color: Colors.grey,
          ),
          SizedBox(height: 10),
          Text(
            'NO HAY ÓRDENES PARA MOSTRAR',
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w900,
              color: AppTheme.mutedText,
              letterSpacing: 1,
            ),
          ),
        ],
      ),
    );
  }
}

class OrdenDetalleSheet extends StatefulWidget {
  final OrdenTrabajo orden;
  final bool editable;
  final Future<void> Function() onSaved;

  const OrdenDetalleSheet({
    super.key,
    required this.orden,
    required this.editable,
    required this.onSaved,
  });

  @override
  State<OrdenDetalleSheet> createState() => _OrdenDetalleSheetState();
}

class _OrdenDetalleSheetState extends State<OrdenDetalleSheet> {
  bool saving = false;
  bool grabandoAudio = false;
  final AudioRecorder audioRecorder = AudioRecorder();

  late String estadoSeleccionado;
  late TextEditingController reporteController;

  String? imagenBase64;
  String? audioBase64;

  String? imagenNombre;
  String? audioNombre;

  @override
  void initState() {
    super.initState();

    estadoSeleccionado = widget.orden.estado.isEmpty
        ? 'PENDIENTE'
        : widget.orden.estado.toUpperCase();

    reporteController = TextEditingController(
      text: widget.orden.reporteTexto,
    );

    imagenBase64 = widget.orden.urlImagen.isEmpty ? null : widget.orden.urlImagen;
    audioBase64 = widget.orden.urlAudio.isEmpty ? null : widget.orden.urlAudio;

    imagenNombre = imagenBase64 == null ? null : 'Imagen registrada';
    audioNombre = audioBase64 == null ? null : 'Audio registrado';
  }

  @override
  void dispose() {
    reporteController.dispose();
    audioRecorder.dispose();
    super.dispose();
  }

  Future<void> iniciarGrabacionAudio() async {
    final tienePermiso = await audioRecorder.hasPermission();

    if (!tienePermiso) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No se otorgó permiso para usar el micrófono.'),
        ),
      );
      return;
    }

    final dir = await getTemporaryDirectory();

    final path =
        '${dir.path}/orden_${widget.orden.nroOrden}_${DateTime.now().millisecondsSinceEpoch}.m4a';

    await audioRecorder.start(
      const RecordConfig(
        encoder: AudioEncoder.aacLc,
        bitRate: 64000,
        sampleRate: 44100,
      ),
      path: path,
    );

    if (!mounted) return;

    setState(() {
      grabandoAudio = true;
      audioNombre = 'Grabando audio...';
    });
  }

  Future<void> detenerGrabacionAudio() async {
    final path = await audioRecorder.stop();

    if (!mounted) return;

    setState(() {
      grabandoAudio = false;
    });

    if (path == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No se pudo guardar la grabación.'),
        ),
      );
      return;
    }

    final file = File(path);
    final bytes = await file.readAsBytes();

    setState(() {
      audioBase64 = 'data:audio/mp4;base64,${base64Encode(bytes)}';
      audioNombre = 'Audio grabado desde micrófono';
    });
  }

  Future<void> seleccionarImagen() async {
    final file = await _Base64FileService.pickImageFromGallery();

    if (file == null) return;

    setState(() {
      imagenBase64 = file.dataUrl;
      imagenNombre = file.name;
    });
  }

  Future<void> tomarFoto() async {
    final file = await _Base64FileService.takePhoto();

    if (file == null) return;

    setState(() {
      imagenBase64 = file.dataUrl;
      imagenNombre = file.name;
    });
  }

  Future<void> seleccionarAudio() async {
    final file = await _Base64FileService.pickAudio();

    if (file == null) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No se pudo cargar el audio seleccionado.'),
        ),
      );
      return;
    }

    setState(() {
      audioBase64 = file.dataUrl;
      audioNombre = file.name;
    });
  }

  Future<void> guardarCambios() async {
    setState(() {
      saving = true;
    });

    final result = await OrdenService.actualizarMiOrden(
      nroOrden: widget.orden.nroOrden,
      estado: estadoSeleccionado,
      reporteTexto: reporteController.text.trim(),
      urlImagen: imagenBase64,
      urlAudio: audioBase64,
    );

    if (!mounted) return;

    setState(() {
      saving = false;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(result.message)),
    );

    if (!result.success) return;

    await widget.onSaved();
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.92,
        minChildSize: 0.50,
        maxChildSize: 0.96,
        builder: (context, scrollController) {
          return ListView(
            controller: scrollController,
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 18),
            children: [
              Center(
                child: Container(
                  width: 46,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade300,
                    borderRadius: BorderRadius.circular(20),
                  ),
                ),
              ),
              const SizedBox(height: 14),
              _buildHeader(),
              const SizedBox(height: 12),
              _buildInfoCard(),
              const SizedBox(height: 12),
              if (widget.editable)
                _buildForm()
              else
                _buildReadOnlyReport(),
            ],
          );
        },
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.primaryGreen,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(11),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.12),
              borderRadius: BorderRadius.circular(50),
            ),
            child: const Icon(
              Icons.assignment,
              color: Colors.white,
              size: 24,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'ORDEN #${widget.orden.nroOrden.toString().padLeft(5, '0')}',
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w900,
                    color: Colors.white,
                    letterSpacing: 1,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  widget.orden.tipoTrabajo.toUpperCase(),
                  style: const TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w900,
                    color: Colors.white70,
                    letterSpacing: 1,
                  ),
                ),
              ],
            ),
          ),
          _buildEstadoMini(widget.orden.estado),
        ],
      ),
    );
  }

  Widget _buildEstadoMini(String estado) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.14),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        estado.toUpperCase(),
        style: const TextStyle(
          fontSize: 8,
          fontWeight: FontWeight.w900,
          color: Colors.white,
        ),
      ),
    );
  }

  Widget _buildInfoCard() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        children: [
          _buildInfoRow('Campaña', widget.orden.idCampana.toString()),
          _buildInfoRow('Supervisor', widget.orden.supervisorUsername),
          _buildInfoRow(
            'Empleado',
            widget.orden.empleadoUsername.isEmpty
                ? 'Sin asignar'
                : widget.orden.empleadoUsername,
          ),
          _buildInfoRow('Fecha inicio', widget.orden.fechaInicio),
          _buildInfoRow(
            'Fecha fin',
            widget.orden.fechaFin.isEmpty ? 'Sin fecha' : widget.orden.fechaFin,
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        children: [
          Text(
            label.toUpperCase(),
            style: const TextStyle(
              fontSize: 9,
              fontWeight: FontWeight.w900,
              color: AppTheme.mutedText,
              letterSpacing: 1,
            ),
          ),
          const Spacer(),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.right,
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w800,
                color: AppTheme.slateText,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildForm() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'ACTUALIZAR ORDEN',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w900,
              color: AppTheme.slateText,
              letterSpacing: 1,
            ),
          ),
          const SizedBox(height: 12),
          _buildEstadoSelector(),
          const SizedBox(height: 12),
          TextField(
            controller: reporteController,
            maxLines: 5,
            decoration: const InputDecoration(
              hintText: 'Escribe el reporte de la actividad realizada...',
            ),
          ),
          const SizedBox(height: 14),
          _buildEvidenciaPanel(),
          const SizedBox(height: 14),
          AgroButton(
            text: 'Guardar cambios',
            loading: saving,
            onPressed: saving ? null : guardarCambios,
          ),
        ],
      ),
    );
  }

  Widget _buildEstadoSelector() {
    final estados = ['PENDIENTE', 'EN PROCESO', 'FINALIZADA'];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'ESTADO',
          style: TextStyle(
            fontSize: 9,
            fontWeight: FontWeight.w900,
            color: AppTheme.mutedText,
            letterSpacing: 1,
          ),
        ),
        const SizedBox(height: 6),
        DropdownButtonFormField<String>(
          value: estados.contains(estadoSeleccionado)
              ? estadoSeleccionado
              : 'PENDIENTE',
          items: estados.map((estado) {
            return DropdownMenuItem(
              value: estado,
              child: Text(
                estado,
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w800,
                ),
              ),
            );
          }).toList(),
          onChanged: (value) {
            if (value == null) return;

            setState(() {
              estadoSeleccionado = value;
            });
          },
          decoration: const InputDecoration(
            hintText: 'Selecciona estado',
          ),
        ),
      ],
    );
  }

  Widget _buildEvidenciaPanel() {
    return Container(
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(9),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'EVIDENCIA EN BASE64',
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w900,
              color: AppTheme.slateText,
              letterSpacing: 1,
            ),
          ),
          const SizedBox(height: 12),
          _buildImagePreview(),
          if (imagenNombre != null) ...[
            const SizedBox(height: 8),
            Text(
              imagenNombre!,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w700,
                color: AppTheme.mutedText,
              ),
            ),
          ],
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: seleccionarImagen,
                  icon: const Icon(Icons.image_outlined, size: 17),
                  label: const Text('GALERÍA'),
                  style: _evidenceButtonStyle(),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: tomarFoto,
                  icon: const Icon(Icons.camera_alt_outlined, size: 17),
                  label: const Text('FOTO'),
                  style: _evidenceButtonStyle(),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: grabandoAudio
                      ? detenerGrabacionAudio
                      : iniciarGrabacionAudio,
                  icon: Icon(
                    grabandoAudio ? Icons.stop_circle_outlined : Icons.mic_none,
                    size: 17,
                  ),
                  label: Text(
                    grabandoAudio ? 'DETENER' : 'GRABAR',
                  ),
                  style: _evidenceButtonStyle(),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: grabandoAudio ? null : seleccionarAudio,
                  icon: const Icon(Icons.folder_open, size: 17),
                  label: const Text('CARGAR'),
                  style: _evidenceButtonStyle(),
                ),
              ),
            ],
          ),
          if (audioBase64 != null) ...[
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.white,
                border: Border.all(color: AppTheme.borderColor),
                borderRadius: BorderRadius.circular(7),
              ),
              child: Row(
                children: [
                  const Icon(
                    Icons.audiotrack,
                    size: 18,
                    color: AppTheme.primaryGreen,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      audioNombre ?? 'Audio en base64 listo para guardar',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.mutedText,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  ButtonStyle _evidenceButtonStyle() {
    return OutlinedButton.styleFrom(
      foregroundColor: AppTheme.primaryGreen,
      side: const BorderSide(color: AppTheme.primaryGreen),
      textStyle: const TextStyle(
        fontSize: 10,
        fontWeight: FontWeight.w900,
        letterSpacing: 0.8,
      ),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(7),
      ),
    );
  }

  Widget _buildImagePreview() {
    if (imagenBase64 == null || imagenBase64!.isEmpty) {
      return Container(
        width: double.infinity,
        height: 130,
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border.all(color: AppTheme.borderColor),
          borderRadius: BorderRadius.circular(9),
        ),
        child: const Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.image_outlined,
              size: 38,
              color: Colors.grey,
            ),
            SizedBox(height: 8),
            Text(
              'SIN IMAGEN',
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w900,
                color: AppTheme.mutedText,
                letterSpacing: 1,
              ),
            ),
          ],
        ),
      );
    }

    if (_Base64FileService.isImageDataUrl(imagenBase64)) {
      final bytes = _Base64FileService.bytesFromDataUrl(imagenBase64);

      if (bytes != null) {
        return ClipRRect(
          borderRadius: BorderRadius.circular(9),
          child: Image.memory(
            bytes,
            width: double.infinity,
            height: 160,
            fit: BoxFit.cover,
          ),
        );
      }
    }

    if (imagenBase64!.startsWith('http')) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(9),
        child: Image.network(
          imagenBase64!,
          width: double.infinity,
          height: 160,
          fit: BoxFit.cover,
        ),
      );
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(9),
      ),
      child: const Text(
        'Imagen registrada, pero no se pudo previsualizar.',
        style: TextStyle(
          fontSize: 11,
          color: AppTheme.mutedText,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }

  Widget _buildReadOnlyReport() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'REPORTE',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w900,
              color: AppTheme.slateText,
              letterSpacing: 1,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            widget.orden.reporteTexto.isEmpty
                ? 'Sin reporte registrado.'
                : widget.orden.reporteTexto,
            style: const TextStyle(
              fontSize: 12,
              color: AppTheme.mutedText,
              fontWeight: FontWeight.w700,
              height: 1.4,
            ),
          ),
          if (widget.orden.urlImagen.isNotEmpty) ...[
            const SizedBox(height: 14),
            const Text(
              'IMAGEN',
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w900,
                color: AppTheme.mutedText,
                letterSpacing: 1,
              ),
            ),
            const SizedBox(height: 8),
            _buildReadOnlyImage(widget.orden.urlImagen),
          ],
          if (widget.orden.urlAudio.isNotEmpty) ...[
            const SizedBox(height: 14),
            const Text(
              'AUDIO',
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w900,
                color: AppTheme.mutedText,
                letterSpacing: 1,
              ),
            ),
            const SizedBox(height: 8),
            _buildReadOnlyAudio(widget.orden.urlAudio),
          ],
        ],
      ),
    );
  }

  Widget _buildReadOnlyImage(String value) {
    if (_Base64FileService.isImageDataUrl(value)) {
      final bytes = _Base64FileService.bytesFromDataUrl(value);

      if (bytes != null) {
        return ClipRRect(
          borderRadius: BorderRadius.circular(9),
          child: Image.memory(
            bytes,
            height: 160,
            width: double.infinity,
            fit: BoxFit.cover,
          ),
        );
      }
    }

    if (value.startsWith('http')) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(9),
        child: Image.network(
          value,
          height: 160,
          width: double.infinity,
          fit: BoxFit.cover,
        ),
      );
    }

    return const Text(
      'Imagen registrada, pero no se pudo visualizar.',
      style: TextStyle(
        fontSize: 11,
        color: AppTheme.mutedText,
      ),
    );
  }

  Widget _buildReadOnlyAudio(String value) {
    final isBase64Audio = _Base64FileService.isAudioDataUrl(value);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(11),
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          const Icon(
            Icons.audiotrack,
            color: AppTheme.primaryGreen,
            size: 20,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              isBase64Audio ? 'Audio guardado en base64' : value,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: AppTheme.mutedText,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Base64FileService {
  static final ImagePicker _picker = ImagePicker();

  static Future<_Base64File?> pickImageFromGallery() async {
    final file = await _picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 55,
      maxWidth: 900,
      maxHeight: 900,
    );

    if (file == null) return null;

    final bytes = await file.readAsBytes();
    final mime = _getImageMime(file.path);

    return _Base64File(
      name: _fileName(file.path),
      mimeType: mime,
      dataUrl: 'data:$mime;base64,${base64Encode(bytes)}',
    );
  }

  static Future<_Base64File?> takePhoto() async {
    final file = await _picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 55,
      maxWidth: 900,
      maxHeight: 900,
    );

    if (file == null) return null;

    final bytes = await file.readAsBytes();
    final mime = _getImageMime(file.path);

    return _Base64File(
      name: _fileName(file.path),
      mimeType: mime,
      dataUrl: 'data:$mime;base64,${base64Encode(bytes)}',
    );
  }

  static Future<_Base64File?> pickAudio() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.audio,
      allowMultiple: false,
      withData: true,
    );

    if (result == null || result.files.isEmpty) return null;

    final picked = result.files.single;
    final bytes = picked.bytes;

    if (bytes == null) return null;

    final mime = _getAudioMime(picked.name);

    return _Base64File(
      name: picked.name,
      mimeType: mime,
      dataUrl: 'data:$mime;base64,${base64Encode(bytes)}',
    );
  }

  static bool isImageDataUrl(String? value) {
    if (value == null) return false;

    return value.startsWith('data:image') && value.contains('base64,');
  }

  static bool isAudioDataUrl(String? value) {
    if (value == null) return false;

    return value.startsWith('data:audio') && value.contains('base64,');
  }

  static Uint8List? bytesFromDataUrl(String? dataUrl) {
    if (dataUrl == null) return null;

    try {
      final base64Part = dataUrl.split('base64,').last;
      return base64Decode(base64Part);
    } catch (_) {
      return null;
    }
  }

  static String _fileName(String path) {
    return path.split('/').last.split('\\').last;
  }

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

class _Base64File {
  final String name;
  final String mimeType;
  final String dataUrl;

  _Base64File({
    required this.name,
    required this.mimeType,
    required this.dataUrl,
  });
}