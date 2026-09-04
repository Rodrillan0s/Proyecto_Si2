import 'package:flutter/material.dart';
import '../services/material_service.dart';
import '../theme/app_theme.dart';

class MaterialesScreen extends StatefulWidget {
  const MaterialesScreen({super.key});

  @override
  State<MaterialesScreen> createState() => _MaterialesScreenState();
}

class _MaterialesScreenState extends State<MaterialesScreen> {
  final MaterialService _materialService = MaterialService();
  final TextEditingController _searchCtrl = TextEditingController();

  List<Map<String, dynamic>> _materiales = [];
  bool _cargando = true;
  String _busqueda = '';

  @override
  void initState() {
    super.initState();
    _cargarMateriales();
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  Future<void> _cargarMateriales() async {
    setState(() => _cargando = true);
    final list = await _materialService.listarMateriales(q: _busqueda);
    if (!mounted) return;
    setState(() {
      _materiales = list;
      _cargando = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Catálogo de Materiales'),
        actions: [
          IconButton(
            tooltip: 'Recargar',
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _cargando ? null : _cargarMateriales,
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Barra de Búsqueda
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
              child: TextField(
                controller: _searchCtrl,
                decoration: InputDecoration(
                  hintText: 'Buscar por código, nombre o categoría...',
                  prefixIcon: const Icon(Icons.search_rounded, size: 20, color: AppTheme.textMuted),
                  suffixIcon: _busqueda.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear_rounded, size: 18),
                          onPressed: () {
                            _searchCtrl.clear();
                            setState(() => _busqueda = '');
                            _cargarMateriales();
                          },
                        )
                      : null,
                ),
                onSubmitted: (val) {
                  setState(() => _busqueda = val.trim());
                  _cargarMateriales();
                },
              ),
            ),

            // Conteo y Filtro
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '${_materiales.length} materiales registrados',
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textSecondary),
                  ),
                ],
              ),
            ),

            // Lista
            Expanded(
              child: _cargando
                  ? const Center(child: CircularProgressIndicator(color: AppTheme.primary, strokeWidth: 2.5))
                  : _materiales.isEmpty
                      ? Center(
                          child: Padding(
                            padding: const EdgeInsets.all(32.0),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const Icon(Icons.inventory_2_outlined, size: 48, color: AppTheme.textMuted),
                                const SizedBox(height: 12),
                                const Text(
                                  'No se encontraron materiales',
                                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  _busqueda.isNotEmpty
                                      ? 'No hay coincidencias para "$_busqueda".'
                                      : 'No hay materiales registrados en el inventario.',
                                  textAlign: TextAlign.center,
                                  style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                                ),
                              ],
                            ),
                          ),
                        )
                      : RefreshIndicator(
                          color: AppTheme.primary,
                          onRefresh: _cargarMateriales,
                          child: ListView.builder(
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                            itemCount: _materiales.length,
                            itemBuilder: (ctx, i) {
                              final m = _materiales[i];
                              final codigo = m['codigo']?.toString() ?? 'MAT-000';
                              final nombre = m['nombre']?.toString() ?? 'Material';
                              final categoria = m['categoria_nombre']?.toString() ?? 'General';
                              final unidad = m['unidad_medida_codigo']?.toString() ?? 'UND';
                              final stock = m['stock_actual']?.toString() ?? '0';
                              final estado = (m['estado']?.toString() ?? 'ACTIVO').toUpperCase();

                              return Card(
                                margin: const EdgeInsets.only(bottom: 10),
                                child: Padding(
                                  padding: const EdgeInsets.all(14.0),
                                  child: Row(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Container(
                                        padding: const EdgeInsets.all(10),
                                        decoration: BoxDecoration(
                                          color: const Color(0xFF10B981).withValues(alpha: 0.12),
                                          borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
                                        ),
                                        child: const Icon(Icons.inventory_2_rounded, color: Color(0xFF10B981), size: 22),
                                      ),
                                      const SizedBox(width: 12),
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Row(
                                              children: [
                                                Text(
                                                  codigo,
                                                  style: const TextStyle(
                                                    fontSize: 10,
                                                    fontFamily: 'monospace',
                                                    fontWeight: FontWeight.w800,
                                                    color: AppTheme.primaryDark,
                                                  ),
                                                ),
                                                const SizedBox(width: 8),
                                                Text(
                                                  '· $categoria',
                                                  style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                                                ),
                                              ],
                                            ),
                                            const SizedBox(height: 4),
                                            Text(
                                              nombre,
                                              style: const TextStyle(
                                                fontSize: 14,
                                                fontWeight: FontWeight.w800,
                                                color: AppTheme.textPrimary,
                                              ),
                                            ),
                                            const SizedBox(height: 8),
                                            Row(
                                              children: [
                                                Container(
                                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                                  decoration: BoxDecoration(
                                                    color: AppTheme.surfaceSubtle,
                                                    borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                                                    border: Border.all(color: AppTheme.border),
                                                  ),
                                                  child: Text(
                                                    'Stock: $stock $unidad',
                                                    style: const TextStyle(
                                                      fontSize: 11,
                                                      fontWeight: FontWeight.w700,
                                                      color: AppTheme.textPrimary,
                                                    ),
                                                  ),
                                                ),
                                                const SizedBox(width: 8),
                                                Container(
                                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                                  decoration: BoxDecoration(
                                                    color: estado == 'ACTIVO'
                                                        ? AppTheme.success.withValues(alpha: 0.12)
                                                        : AppTheme.textMuted.withValues(alpha: 0.12),
                                                    borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                                                  ),
                                                  child: Text(
                                                    estado,
                                                    style: TextStyle(
                                                      fontSize: 9,
                                                      fontWeight: FontWeight.w800,
                                                      color: estado == 'ACTIVO' ? AppTheme.success : AppTheme.textMuted,
                                                    ),
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
                            },
                          ),
                        ),
            ),
          ],
        ),
      ),
    );
  }
}
