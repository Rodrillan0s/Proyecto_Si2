import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/auth_provider.dart';
import '../services/incidencia_service.dart';
import '../theme/app_theme.dart';
import '../widgets/incidencia_widgets.dart';
import 'incidencia_detalle_screen.dart';
import 'incidencia_form_screen.dart';

/// CU19 — Listado de incidencias (filtros y paginación del backend).
class IncidenciasScreen extends StatefulWidget {
  /// Filtra por obra (opcional), p. ej. al abrir desde el detalle de un proyecto.
  final bool soloAsignadas;
  final int? idObraFiltro;
  final String? nombreObraFiltro;

  const IncidenciasScreen({super.key, this.idObraFiltro, this.nombreObraFiltro, this.soloAsignadas = false});

  @override
  State<IncidenciasScreen> createState() => _IncidenciasScreenState();
}

class _IncidenciasScreenState extends State<IncidenciasScreen> {
  static const int _limite = 20;

  final IncidenciaService _service = IncidenciaService();
  final TextEditingController _searchCtrl = TextEditingController();
  final ScrollController _scrollCtrl = ScrollController();
  Timer? _debounce;

  List<Map<String, dynamic>> _incidencias = [];
  int _pagina = 1;
  int _totalPaginas = 0;
  int _total = 0;
  bool _cargando = true;
  bool _cargandoMas = false;
  String? _error;

  String? _filtroEstado;
  String? _filtroPrioridad;

  @override
  void initState() {
    super.initState();
    _scrollCtrl.addListener(_onScroll);
    _cargar();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _searchCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollCtrl.position.pixels >= _scrollCtrl.position.maxScrollExtent - 200) {
      _cargarMas();
    }
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final usuario = widget.soloAsignadas ? await PermisosIncidencia.usuarioActual() : null;
      if (widget.soloAsignadas && usuario == null) throw Exception('No se pudo identificar al usuario.');
      final res = await _service.listar(
        idResponsable: usuario,
        idObra: widget.idObraFiltro,
        estado: _filtroEstado,
        prioridad: _filtroPrioridad,
        busqueda: _searchCtrl.text,
        page: 1,
        limit: _limite,
      );
      if (!mounted) return;
      final pag = res['pagination'] as Map<String, dynamic>;
      setState(() {
        _incidencias = List<Map<String, dynamic>>.from(res['data'] as List);
        _pagina = 1;
        _totalPaginas = (pag['total_pages'] as num?)?.toInt() ?? 0;
        _total = (pag['total'] as num?)?.toInt() ?? _incidencias.length;
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

  Future<void> _cargarMas() async {
    if (_cargando || _cargandoMas || _pagina >= _totalPaginas) return;
    setState(() => _cargandoMas = true);
    try {
      final usuario = widget.soloAsignadas ? await PermisosIncidencia.usuarioActual() : null;
      if (widget.soloAsignadas && usuario == null) throw Exception('No se pudo identificar al usuario.');
      final res = await _service.listar(
        idResponsable: usuario,
        idObra: widget.idObraFiltro,
        estado: _filtroEstado,
        prioridad: _filtroPrioridad,
        busqueda: _searchCtrl.text,
        page: _pagina + 1,
        limit: _limite,
      );
      if (!mounted) return;
      setState(() {
        _incidencias.addAll(List<Map<String, dynamic>>.from(res['data'] as List));
        _pagina++;
        _cargandoMas = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _cargandoMas = false);
      mostrarMensajeIncidencia(context, e.toString(), error: true);
    }
  }

  void _onBuscar(String _) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 450), _cargar);
  }

  Future<void> _abrirDetalle(int idIncidencia) async {
    await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => IncidenciaDetalleScreen(idIncidencia: idIncidencia)),
    );
    if (mounted) _cargar();
  }

  Future<void> _abrirRegistro() async {
    final idCreada = await Navigator.push<int>(
      context,
      MaterialPageRoute(builder: (_) => IncidenciaFormScreen(idObraInicial: widget.idObraFiltro)),
    );
    if (!mounted) return;
    _cargar();
    if (idCreada != null) _abrirDetalle(idCreada);
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final puedeRegistrar = PermisosIncidencia.puedeRegistrar(auth);

    return Scaffold(
      backgroundColor: isDark ? AppTheme.darkBackground : AppTheme.background,
      appBar: AppBar(
        title: Text(widget.soloAsignadas ? 'Incidencias asignadas' : widget.nombreObraFiltro != null ? 'Incidencias: ${widget.nombreObraFiltro}' : 'Incidencias'),
        actions: [
          IconButton(
            tooltip: 'Actualizar',
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _cargando ? null : _cargar,
          ),
        ],
      ),
      floatingActionButton: puedeRegistrar
          ? FloatingActionButton.extended(
              onPressed: _abrirRegistro,
              icon: const Icon(Icons.report_problem_outlined),
              label: const Text('Registrar incidencia'),
            )
          : null,
      body: SafeArea(
        child: Column(
          children: [
            _buildFiltros(isDark),
            Expanded(
              child: RefreshIndicator(
                color: AppTheme.primary,
                onRefresh: _cargar,
                child: _buildContenido(isDark),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFiltros(bool isDark) {
    return Container(
      color: isDark ? AppTheme.darkSurface : Colors.white,
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      child: Column(
        children: [
          TextField(
            controller: _searchCtrl,
            onChanged: _onBuscar,
            textInputAction: TextInputAction.search,
            onSubmitted: (_) => _cargar(),
            decoration: InputDecoration(
              hintText: 'Buscar por título o descripción',
              prefixIcon: const Icon(Icons.search_rounded),
              isDense: true,
              suffixIcon: _searchCtrl.text.isEmpty
                  ? null
                  : IconButton(
                      icon: const Icon(Icons.close_rounded),
                      onPressed: () {
                        _searchCtrl.clear();
                        _cargar();
                      },
                    ),
            ),
          ),
          const SizedBox(height: 10),
          SizedBox(
            height: 34,
            child: ListView(
              scrollDirection: Axis.horizontal,
              children: [
                _chipFiltro('Todos', _filtroEstado == null, () => _setEstado(null)),
                for (final e in IncidenciaService.estados)
                  _chipFiltro(etiquetaEstadoIncidencia(e), _filtroEstado == e, () => _setEstado(e)),
              ],
            ),
          ),
          const SizedBox(height: 6),
          SizedBox(
            height: 34,
            child: ListView(
              scrollDirection: Axis.horizontal,
              children: [
                _chipFiltro('Toda prioridad', _filtroPrioridad == null, () => _setPrioridad(null)),
                for (final p in IncidenciaService.prioridades)
                  _chipFiltro(etiquetaPrioridad(p), _filtroPrioridad == p, () => _setPrioridad(p)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _setEstado(String? estado) {
    setState(() => _filtroEstado = estado);
    _cargar();
  }

  void _setPrioridad(String? prioridad) {
    setState(() => _filtroPrioridad = prioridad);
    _cargar();
  }

  Widget _chipFiltro(String texto, bool seleccionado, VoidCallback onTap) {
    return Padding(
      padding: const EdgeInsets.only(right: 6),
      child: ChoiceChip(
        label: Text(texto, style: const TextStyle(fontSize: 12)),
        selected: seleccionado,
        onSelected: (_) => onTap(),
        selectedColor: AppTheme.primary.withValues(alpha: 0.18),
        visualDensity: VisualDensity.compact,
      ),
    );
  }

  Widget _buildContenido(bool isDark) {
    if (_cargando) {
      return const Center(child: CircularProgressIndicator(color: AppTheme.primary));
    }
    // ListView para que el pull-to-refresh funcione también en vacío / error.
    if (_error != null) {
      return ListView(children: [
        IncidenciaMensaje(
          icon: Icons.cloud_off_rounded,
          titulo: 'No se pudieron cargar las incidencias',
          detalle: _error,
          onAccion: _cargar,
          esError: true,
        ),
      ]);
    }
    if (_incidencias.isEmpty) {
      final hayFiltros = _filtroEstado != null || _filtroPrioridad != null || _searchCtrl.text.isNotEmpty;
      return ListView(children: [
        IncidenciaMensaje(
          icon: Icons.task_alt_rounded,
          titulo: hayFiltros ? 'Sin resultados' : 'No hay incidencias registradas',
          detalle: hayFiltros ? 'Prueba con otros filtros o términos de búsqueda.' : null,
        ),
      ]);
    }

    return ListView.separated(
      controller: _scrollCtrl,
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 96),
      itemCount: _incidencias.length + 1,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: (context, index) {
        if (index == _incidencias.length) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Center(
              child: _cargandoMas
                  ? const CircularProgressIndicator(color: AppTheme.primary)
                  : Text(
                      '${_incidencias.length} de $_total incidencias',
                      style: const TextStyle(fontSize: 11.5, color: AppTheme.textMuted),
                    ),
            ),
          );
        }
        return _buildTarjeta(_incidencias[index], isDark);
      },
    );
  }

  Widget _buildTarjeta(Map<String, dynamic> inc, bool isDark) {
    final obra = [inc['obra_codigo'], inc['obra_nombre']].where((v) => v != null && v.toString().isNotEmpty).join(' · ');
    final ubicacion = (inc['ubicacion'] ?? '').toString();
    final unidad = (inc['unidad_codigo'] ?? '').toString();

    return Material(
      color: isDark ? AppTheme.darkSurface : Colors.white,
      borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
      child: InkWell(
        borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
        onTap: () => _abrirDetalle((inc['id_incidencia'] as num).toInt()),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
            border: Border.all(color: isDark ? AppTheme.darkBorder : AppTheme.border),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Text('#${inc['id_incidencia']}', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.textMuted)),
                  const Spacer(),
                  IncidenciaChip.prioridad(inc['prioridad']?.toString(), compact: true),
                  const SizedBox(width: 6),
                  IncidenciaChip.estado(inc['estado']?.toString(), compact: true),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                (inc['titulo'] ?? '').toString(),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 14.5, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 6),
              _linea(Icons.apartment_rounded, obra.isEmpty ? 'Obra #${inc['id_obra']}' : obra),
              if (unidad.isNotEmpty || ubicacion.isNotEmpty)
                _linea(Icons.place_outlined, [if (unidad.isNotEmpty) unidad, if (ubicacion.isNotEmpty) ubicacion].join(' · ')),
              _linea(Icons.person_outline_rounded, (inc['responsable_nombre'] ?? 'Sin responsable').toString()),
              _linea(Icons.schedule_rounded, 'Registrada ${formatearFechaHora(inc['created_at'])}'),
            ],
          ),
        ),
      ),
    );
  }

  Widget _linea(IconData icon, String texto) {
    return Padding(
      padding: const EdgeInsets.only(top: 3),
      child: Row(
        children: [
          Icon(icon, size: 14, color: AppTheme.textMuted),
          const SizedBox(width: 6),
          Expanded(
            child: Text(texto, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
          ),
        ],
      ),
    );
  }
}
