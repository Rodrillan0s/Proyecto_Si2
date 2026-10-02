import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_provider.dart';
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
    final auth = Provider.of<AuthProvider>(context, listen: false);
    final int? idEmpresa = auth.esAdminGlobal ? auth.idEmpresaActiva : auth.empresaId;

    try {
      final list = await _materialService.listarMateriales(
        q: _busqueda,
        idEmpresa: idEmpresa,
      );
      if (!mounted) return;
      setState(() {
        _materiales = list;
        _cargando = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _cargando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF1E293B) : Colors.white;
    final borderColor = isDark ? const Color(0xFF334155) : const Color(0xFFE2E8F0);

    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF0F172A) : AppTheme.background,
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
            // Banner de contexto multi-tenant para Administrador
            if (auth.esAdminGlobal)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                color: auth.esVistaGlobal
                    ? (isDark ? const Color(0xFF1E293B) : const Color(0xFFEFF6FF))
                    : (isDark ? const Color(0xFF14532D).withValues(alpha: 0.3) : const Color(0xFFDCFCE7)),
                child: Row(
                  children: [
                    Icon(
                      auth.esVistaGlobal ? Icons.public_rounded : Icons.business_rounded,
                      size: 18,
                      color: auth.esVistaGlobal ? AppTheme.primary : AppTheme.success,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        auth.esVistaGlobal
                            ? 'Vista Global: Todas las Empresas'
                            : 'Empresa Activa: ${auth.nombreEmpresaActiva ?? "Empresa"}',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: auth.esVistaGlobal ? AppTheme.primary : AppTheme.success,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),

            // Barra de Búsqueda
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
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

            // Conteo
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '${_materiales.length} materiales registrados',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      color: isDark ? const Color(0xFF94A3B8) : AppTheme.textSecondary,
                    ),
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
                                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
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
                              // Resuelve correctamente nombre_material del backend de FastAPI
                              final nombre = m['nombre_material']?.toString() ??
                                  m['nombre']?.toString() ??
                                  'Material sin nombre';

                              // Resuelve la categoría tanto si viene anidada como si viene plana
                              final categoria = (m['categoria'] is Map
                                      ? m['categoria']['nombre']?.toString()
                                      : null) ??
                                  m['categoria_nombre']?.toString() ??
                                  'General';

                              // Resuelve unidad de medida
                              final unidad = (m['unidad_medida'] is Map
                                      ? (m['unidad_medida']['abreviatura'] ??
                                          m['unidad_medida']['nombre'])
                                      : null) ??
                                  m['unidad_medida_codigo']?.toString() ??
                                  'UND';

                              final stock = m['stock_actual']?.toString() ?? '0';
                              final stockMinimo = m['stock_minimo']?.toString() ?? '0';
                              final stockBajo = m['stock_bajo'] == true;
                              final estado = (m['estado']?.toString() ?? 'ACTIVO').toUpperCase();
                              final nombreEmpresa = m['nombre_empresa']?.toString();
                              final descripcion = m['descripcion']?.toString();

                              return Container(
                                margin: const EdgeInsets.only(bottom: 10),
                                decoration: BoxDecoration(
                                  color: cardBg,
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: borderColor),
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withValues(alpha: isDark ? 0.2 : 0.04),
                                      blurRadius: 6,
                                      offset: const Offset(0, 2),
                                    ),
                                  ],
                                ),
                                child: InkWell(
                                  borderRadius: BorderRadius.circular(12),
                                  onTap: () => _mostrarDetalleMaterial(context, m, nombre, codigo, categoria, unidad, stock, stockMinimo, stockBajo, estado, nombreEmpresa, descripcion),
                                  child: Padding(
                                    padding: const EdgeInsets.all(14.0),
                                    child: Row(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Container(
                                          padding: const EdgeInsets.all(10),
                                          decoration: BoxDecoration(
                                            color: const Color(0xFF10B981).withValues(alpha: 0.12),
                                            borderRadius: BorderRadius.circular(10),
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
                                                      fontSize: 10.5,
                                                      fontFamily: 'monospace',
                                                      fontWeight: FontWeight.w800,
                                                      color: AppTheme.primary,
                                                    ),
                                                  ),
                                                  const SizedBox(width: 8),
                                                  Expanded(
                                                    child: Text(
                                                      '· $categoria',
                                                      style: TextStyle(
                                                        fontSize: 11,
                                                        color: isDark ? const Color(0xFF94A3B8) : AppTheme.textSecondary,
                                                      ),
                                                      maxLines: 1,
                                                      overflow: TextOverflow.ellipsis,
                                                    ),
                                                  ),
                                                  if (nombreEmpresa != null && nombreEmpresa.isNotEmpty)
                                                    Container(
                                                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                                                      decoration: BoxDecoration(
                                                        color: isDark ? const Color(0xFF334155) : const Color(0xFFF1F5F9),
                                                        borderRadius: BorderRadius.circular(4),
                                                      ),
                                                      child: Text(
                                                        nombreEmpresa,
                                                        style: const TextStyle(fontSize: 9.5, color: AppTheme.textMuted),
                                                      ),
                                                    ),
                                                ],
                                              ),
                                              const SizedBox(height: 5),

                                              // Nombre del material
                                              Text(
                                                nombre,
                                                style: TextStyle(
                                                  fontSize: 14.5,
                                                  fontWeight: FontWeight.w800,
                                                  color: isDark ? Colors.white : AppTheme.textPrimary,
                                                ),
                                              ),
                                              const SizedBox(height: 8),

                                              // Fila de Stock y Estado
                                              Row(
                                                children: [
                                                  Container(
                                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                                    decoration: BoxDecoration(
                                                      color: stockBajo
                                                          ? Colors.amber.withValues(alpha: 0.15)
                                                          : (isDark ? const Color(0xFF334155) : const Color(0xFFF1F5F9)),
                                                      borderRadius: BorderRadius.circular(6),
                                                      border: Border.all(
                                                        color: stockBajo
                                                            ? Colors.amber.withValues(alpha: 0.4)
                                                            : borderColor,
                                                      ),
                                                    ),
                                                    child: Row(
                                                      mainAxisSize: MainAxisSize.min,
                                                      children: [
                                                        if (stockBajo) ...[
                                                          const Icon(Icons.warning_amber_rounded, size: 13, color: Colors.amber),
                                                          const SizedBox(width: 4),
                                                        ],
                                                        Text(
                                                          'Stock: $stock $unidad',
                                                          style: TextStyle(
                                                            fontSize: 11,
                                                            fontWeight: FontWeight.w700,
                                                            color: stockBajo
                                                                ? Colors.amber.shade700
                                                                : (isDark ? Colors.white : AppTheme.textPrimary),
                                                          ),
                                                        ),
                                                      ],
                                                    ),
                                                  ),
                                                  const SizedBox(width: 8),
                                                  Container(
                                                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                                                    decoration: BoxDecoration(
                                                      color: estado == 'ACTIVO'
                                                          ? AppTheme.success.withValues(alpha: 0.12)
                                                          : AppTheme.textMuted.withValues(alpha: 0.12),
                                                      borderRadius: BorderRadius.circular(6),
                                                    ),
                                                    child: Text(
                                                      estado,
                                                      style: TextStyle(
                                                        fontSize: 9.5,
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

  void _mostrarDetalleMaterial(
    BuildContext context,
    Map<String, dynamic> m,
    String nombre,
    String codigo,
    String categoria,
    String unidad,
    String stock,
    String stockMinimo,
    bool stockBajo,
    String estado,
    String? nombreEmpresa,
    String? descripcion,
  ) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF1E293B) : Colors.white;
    final precio = m['precio'] != null ? '${m['precio']} BOB' : 'No especificado';

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Container(
        padding: const EdgeInsets.all(22),
        decoration: BoxDecoration(
          color: cardBg,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey.withValues(alpha: 0.3),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),

            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppTheme.primary.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    codigo,
                    style: const TextStyle(fontWeight: FontWeight.w800, color: AppTheme.primary, fontSize: 12),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: estado == 'ACTIVO' ? AppTheme.success.withValues(alpha: 0.12) : Colors.grey.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    estado,
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: estado == 'ACTIVO' ? AppTheme.success : Colors.grey),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),

            Text(
              nombre,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            if (descripcion != null && descripcion.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(descripcion, style: const TextStyle(fontSize: 13, color: AppTheme.textMuted)),
            ],
            const Divider(height: 24),

            _buildDetalleRow('Categoría:', categoria),
            _buildDetalleRow('Unidad de Medida:', unidad),
            _buildDetalleRow('Stock Actual:', '$stock $unidad'),
            _buildDetalleRow('Stock Mínimo:', '$stockMinimo $unidad'),
            _buildDetalleRow('Precio Referencial:', precio),
            if (nombreEmpresa != null && nombreEmpresa.isNotEmpty)
              _buildDetalleRow('Empresa:', nombreEmpresa),

            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildDetalleRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 13, color: AppTheme.textMuted)),
          Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}
