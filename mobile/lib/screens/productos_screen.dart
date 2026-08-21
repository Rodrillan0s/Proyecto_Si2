import 'package:flutter/material.dart';
import '../services/offline_pedido_service.dart';
import '../services/pedido_service.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class ProductosScreen extends StatefulWidget {
  const ProductosScreen({super.key});

  @override
  State<ProductosScreen> createState() => _ProductosScreenState();
}

class _ProductosScreenState extends State<ProductosScreen> {
  bool loading = true;
  bool enviando = false;

  String message = '';
  bool messageSuccess = false;

  final searchController = TextEditingController();

  List<Insumo> catalogo = [];
  final Map<int, CarritoItem> carrito = {};

  double get totalCarrito {
    return carrito.values.fold(0.0, (sum, item) => sum + item.subtotal);
  }

  int get cantidadItemsCarrito {
    return carrito.values.fold(0, (sum, item) => sum + item.cantidad.toInt());
  }

  List<Insumo> get catalogoFiltrado {
    final busqueda = searchController.text.trim().toLowerCase();

    if (busqueda.isEmpty) return catalogo;

    return catalogo.where((prod) {
      return prod.nombreProducto.toLowerCase().contains(busqueda) ||
          prod.categoria.toLowerCase().contains(busqueda);
    }).toList();
  }

  @override
  void initState() {
    super.initState();
    cargarCatalogo();
  }

  @override
  void dispose() {
    searchController.dispose();
    super.dispose();
  }

  Future<void> cargarCatalogo() async {
    setState(() {
      loading = true;
      message = '';
    });

    final result = await PedidoService.obtenerCatalogo();

    if (!mounted) return;

    setState(() {
      loading = false;
      catalogo = result.catalogo;
      message = result.success ? '' : result.message;
      messageSuccess = false;
    });
  }

  void agregarAlCarrito(Insumo producto) {
    final existe = carrito[producto.idProducto];

    setState(() {
      if (existe == null) {
        carrito[producto.idProducto] = CarritoItem(
          insumo: producto,
          cantidad: 1,
        );
        return;
      }

      if (existe.cantidad < producto.stockActual) {
        existe.cantidad += 1;
      }
    });
  }

  void quitarDelCarrito(int idProducto) {
    setState(() {
      carrito.remove(idProducto);
    });
  }

  void actualizarCantidad(Insumo producto, double nuevaCantidad) {
    if (nuevaCantidad < 1 || nuevaCantidad > producto.stockActual) return;

    setState(() {
      final item = carrito[producto.idProducto];
      if (item != null) {
        item.cantidad = nuevaCantidad;
      }
    });
  }

  Future<void> confirmarPedido() async {
    // Evita doble clic y pedidos duplicados
    if (enviando || carrito.isEmpty) return;

    setState(() {
      enviando = true;
      message = '';
    });

    final result = await OfflinePedidoService.instance.createPedidoOrSaveOffline(
      carrito.values.toList(),
    );

    if (!mounted) return;

    if (!result.success) {
      setState(() {
        enviando = false;
        message = result.message;
        messageSuccess = false;
      });
      return;
    }

    setState(() {
      carrito.clear();
      enviando = false;
      message = result.message;
      messageSuccess = true;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(result.message),
        backgroundColor: AppTheme.primaryGreen,
      ),
    );

    Navigator.pushNamedAndRemoveUntil(
      context,
      '/home',
      (route) => false,
    );
  }

  void abrirCarrito() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(18),
        ),
      ),
      builder: (_) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            void update(VoidCallback action) {
              setState(action);
              setModalState(() {});
            }

            return SafeArea(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 18),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 46,
                      height: 4,
                      decoration: BoxDecoration(
                        color: Colors.grey.shade300,
                        borderRadius: BorderRadius.circular(20),
                      ),
                    ),
                    const SizedBox(height: 16),
                    _buildCartHeader(),
                    const SizedBox(height: 12),
                    Flexible(
                      child: carrito.isEmpty
                          ? _buildCartEmpty()
                          : ListView(
                              shrinkWrap: true,
                              children: carrito.values.map((item) {
                                return _buildCartItem(
                                  item,
                                  onRemove: () {
                                    update(() {
                                      quitarDelCarrito(item.insumo.idProducto);
                                    });
                                  },
                                  onMinus: () {
                                    update(() {
                                      actualizarCantidad(
                                        item.insumo,
                                        item.cantidad - 1,
                                      );
                                    });
                                  },
                                  onPlus: () {
                                    update(() {
                                      actualizarCantidad(
                                        item.insumo,
                                        item.cantidad + 1,
                                      );
                                    });
                                  },
                                );
                              }).toList(),
                            ),
                    ),
                    const SizedBox(height: 14),
                    _buildCartFooter(),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final productos = catalogoFiltrado;

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: SafeArea(
        child: Stack(
          children: [
            Column(
              children: [
                _buildTopBar(),
                Expanded(
                  child: RefreshIndicator(
                    onRefresh: cargarCatalogo,
                    color: AppTheme.primaryGreen,
                    child: ListView(
                      padding: EdgeInsets.fromLTRB(
                        16,
                        16,
                        16,
                        carrito.isEmpty ? 18 : 94,
                      ),
                      children: [
                        _buildHeaderAndSearch(),
                        if (message.isNotEmpty) ...[
                          const SizedBox(height: 12),
                          AgroErrorBox(
                            message: message,
                            success: messageSuccess,
                          ),
                        ],
                        const SizedBox(height: 16),
                        if (loading)
                          _buildLoading()
                        else if (productos.isEmpty)
                          _buildEmptyState()
                        else
                          LayoutBuilder(
                            builder: (context, constraints) {
                              final columns = constraints.maxWidth > 620 ? 2 : 1;

                              return GridView.builder(
                                shrinkWrap: true,
                                physics: const NeverScrollableScrollPhysics(),
                                itemCount: productos.length,
                                gridDelegate:
                                    SliverGridDelegateWithFixedCrossAxisCount(
                                  crossAxisCount: columns,
                                  crossAxisSpacing: 12,
                                  mainAxisSpacing: 12,
                                  childAspectRatio: columns == 1 ? 0.88 : 0.78,
                                ),
                                itemBuilder: (context, index) {
                                  return _buildProductCard(productos[index]);
                                },
                              );
                            },
                          ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            if (carrito.isNotEmpty) _buildFloatingCartButton(),
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
                  'CATÁLOGO DE INSUMOS',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w900,
                    color: Colors.white,
                    letterSpacing: 1,
                  ),
                ),
                SizedBox(height: 2),
                Text(
                  'Gestión de pedidos comerciales',
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
            onPressed: cargarCatalogo,
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

  Widget _buildHeaderAndSearch() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(10),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.03),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              SizedBox(
                width: 6,
                height: 28,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: AppTheme.primaryGreen,
                  ),
                ),
              ),
              SizedBox(width: 10),
              Expanded(
                child: Text(
                  'CATÁLOGO DE INSUMOS',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                    color: AppTheme.slateText,
                    letterSpacing: 0.3,
                  ),
                ),
              ),
            ],
          ),
          const Padding(
            padding: EdgeInsets.only(left: 16, top: 4),
            child: Text(
              'Fertilizantes y semillas disponibles',
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w900,
                color: AppTheme.mutedText,
                letterSpacing: 1.1,
              ),
            ),
          ),
          const SizedBox(height: 14),
          TextField(
            controller: searchController,
            onChanged: (_) {
              setState(() {});
            },
            decoration: InputDecoration(
              hintText: 'Buscar producto o categoría...',
              prefixIcon: const Icon(Icons.search, size: 20),
              suffixIcon: searchController.text.isEmpty
                  ? null
                  : IconButton(
                      onPressed: () {
                        setState(() {
                          searchController.clear();
                        });
                      },
                      icon: const Icon(Icons.close, size: 18),
                    ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProductCard(Insumo prod) {
    final itemCarrito = carrito[prod.idProducto];
    final cantidadActual = itemCarrito?.cantidad ?? 0;
    final sinStock = prod.stockActual <= 0;
    final limiteAlcanzado = cantidadActual >= prod.stockActual;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(
          color: sinStock ? AppTheme.borderColor : Colors.grey.shade300,
        ),
        borderRadius: BorderRadius.circular(8),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.025),
            blurRadius: 8,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Opacity(
        opacity: sinStock ? 0.58 : 1,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildProductImage(prod.categoria),
            const SizedBox(height: 12),
            Row(
              children: [
                _buildCategoryTag(prod.categoria),
                const Spacer(),
                Text(
                  'Stock: ${prod.stockActual.toStringAsFixed(0)} ${prod.unidadMedida}',
                  style: TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.w900,
                    color: sinStock ? Colors.red : AppTheme.mutedText,
                    letterSpacing: 0.4,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Expanded(
              child: Text(
                prod.nombreProducto,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontSize: 14,
                  height: 1.25,
                  fontWeight: FontWeight.w900,
                  color: AppTheme.slateText,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                const Text(
                  'Bs.',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w900,
                    color: AppTheme.mutedText,
                  ),
                ),
                const SizedBox(width: 4),
                Text(
                  prod.precioUnitario.toStringAsFixed(2),
                  style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w900,
                    color: Colors.black87,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              height: 42,
              child: OutlinedButton.icon(
                onPressed: sinStock || limiteAlcanzado
                    ? null
                    : () => agregarAlCarrito(prod),
                icon: const Icon(Icons.shopping_cart_outlined, size: 17),
                label: Text(
                  sinStock
                      ? 'AGOTADO'
                      : limiteAlcanzado
                          ? 'LÍMITE ALCANZADO'
                          : cantidadActual > 0
                              ? 'AGREGAR OTRO (${cantidadActual.toInt()})'
                              : 'AGREGAR A LA ORDEN',
                  style: const TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 1,
                  ),
                ),
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppTheme.primaryGreen,
                  side: const BorderSide(color: AppTheme.primaryGreen),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(7),
                  ),
                  disabledForegroundColor: Colors.grey,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProductImage(String categoria) {
    final esSemilla = categoria.toUpperCase() == 'SEMILLA';

    return Container(
      height: 112,
      width: double.infinity,
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Icon(
        esSemilla ? Icons.public : Icons.science_outlined,
        size: 48,
        color: Colors.grey.shade400,
      ),
    );
  }

  Widget _buildCategoryTag(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(5),
      ),
      child: Text(
        text.toUpperCase(),
        style: const TextStyle(
          fontSize: 9,
          fontWeight: FontWeight.w900,
          color: AppTheme.mutedText,
          letterSpacing: 1,
        ),
      ),
    );
  }

  Widget _buildCartHeader() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: const BoxDecoration(
        color: Color(0xFFF8FAFC),
        border: Border(
          bottom: BorderSide(color: AppTheme.borderColor),
        ),
      ),
      child: Row(
        children: [
          const Icon(
            Icons.assignment_outlined,
            color: AppTheme.mutedText,
          ),
          const SizedBox(width: 10),
          const Expanded(
            child: Text(
              'ORDEN EN PROCESO',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w900,
                color: AppTheme.slateText,
                letterSpacing: 1.4,
              ),
            ),
          ),
          Text(
            '$cantidadItemsCarrito ÍTEMS',
            style: const TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w900,
              color: AppTheme.mutedText,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCartItem(
    CarritoItem item, {
    required VoidCallback onRemove,
    required VoidCallback onMinus,
    required VoidCallback onPlus,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(7),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  item.insumo.nombreProducto,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w900,
                    color: AppTheme.slateText,
                  ),
                ),
              ),
              IconButton(
                onPressed: onRemove,
                icon: const Icon(Icons.close, size: 18),
                color: Colors.red,
              ),
            ],
          ),
          Row(
            children: [
              Text(
                'Bs. ${item.insumo.precioUnitario.toStringAsFixed(2)} / ${item.insumo.unidadMedida}',
                style: const TextStyle(
                  fontSize: 10,
                  color: AppTheme.mutedText,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const Spacer(),
              Container(
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey.shade300),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Row(
                  children: [
                    _buildSmallQtyButton('-', onMinus),
                    Container(
                      width: 34,
                      alignment: Alignment.center,
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      decoration: const BoxDecoration(
                        border: Border.symmetric(
                          vertical: BorderSide(color: AppTheme.borderColor),
                        ),
                      ),
                      child: Text(
                        item.cantidad.toStringAsFixed(0),
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ),
                    _buildSmallQtyButton('+', onPlus),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerRight,
            child: Text(
              'Bs. ${item.subtotal.toStringAsFixed(2)}',
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w900,
                color: Colors.black87,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSmallQtyButton(String text, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      child: SizedBox(
        width: 28,
        height: 28,
        child: Center(
          child: Text(
            text,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w900,
              color: AppTheme.slateText,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildCartFooter() {
    return Container(
      padding: const EdgeInsets.only(top: 14),
      decoration: const BoxDecoration(
        border: Border(
          top: BorderSide(color: AppTheme.borderColor),
        ),
      ),
      child: Column(
        children: [
          Row(
            children: [
              const Text(
                'TOTAL ESTIMADO',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w900,
                  color: AppTheme.mutedText,
                  letterSpacing: 1.2,
                ),
              ),
              const Spacer(),
              Text(
                'Bs. ${totalCarrito.toStringAsFixed(2)}',
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w900,
                  color: Colors.black87,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: Colors.green.shade50,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.green.shade100),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'FIDELIZACIÓN CRM',
                  style: TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.w900,
                    color: AppTheme.primaryGreen,
                    letterSpacing: 1.1,
                  ),
                ),
                SizedBox(height: 3),
                Text(
                  'El descuento se calcula automáticamente al confirmar o sincronizar el pedido.',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.mutedText,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            height: 46,
            child: ElevatedButton(
              onPressed: carrito.isEmpty || enviando ? null : confirmarPedido,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryGreen,
                foregroundColor: Colors.white,
                disabledBackgroundColor: Colors.grey.shade300,
                disabledForegroundColor: Colors.grey.shade600,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(7),
                ),
              ),
              child: Text(
                enviando ? 'PROCESANDO...' : 'GENERAR PEDIDO',
                style: const TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 1.5,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFloatingCartButton() {
    return Positioned(
      left: 18,
      right: 18,
      bottom: 18,
      child: ElevatedButton.icon(
        onPressed: abrirCarrito,
        icon: const Icon(Icons.shopping_cart_outlined, size: 18),
        label: Text(
          'REVISAR ORDEN ($cantidadItemsCarrito)  •  Bs. ${totalCarrito.toStringAsFixed(2)}',
          style: const TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w900,
            letterSpacing: 1,
          ),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: AppTheme.primaryGreen,
          foregroundColor: Colors.white,
          elevation: 10,
          padding: const EdgeInsets.symmetric(vertical: 15),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
        ),
      ),
    );
  }

  Widget _buildLoading() {
    return Container(
      height: 220,
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(8),
      ),
      child: const Center(
        child: CircularProgressIndicator(
          color: AppTheme.primaryGreen,
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Container(
      height: 220,
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(8),
      ),
      child: const Center(
        child: Text(
          'NO SE ENCONTRARON RESULTADOS',
          style: TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w900,
            color: AppTheme.mutedText,
            letterSpacing: 1.2,
          ),
        ),
      ),
    );
  }

  Widget _buildCartEmpty() {
    return const Padding(
      padding: EdgeInsets.all(28),
      child: Column(
        children: [
          Icon(
            Icons.shopping_cart_outlined,
            size: 42,
            color: Colors.grey,
          ),
          SizedBox(height: 10),
          Text(
            'ORDEN VACÍA',
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w900,
              color: AppTheme.mutedText,
              letterSpacing: 1.2,
            ),
          ),
        ],
      ),
    );
  }
}
