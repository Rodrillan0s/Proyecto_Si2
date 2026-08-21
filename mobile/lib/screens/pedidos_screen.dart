import 'package:flutter/material.dart';

import '../services/pedido_service.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class PedidosScreen extends StatefulWidget {
  const PedidosScreen({super.key});

  @override
  State<PedidosScreen> createState() => _PedidosScreenState();
}

class _PedidosScreenState extends State<PedidosScreen> {
  bool loading = true;
  bool detalleLoading = false;
  bool procesandoPago = false;
  bool qrLoading = false;

  String message = '';
  String metodoPago = 'TARJETA';

  final numeroController = TextEditingController();
  final titularController = TextEditingController();
  final expiracionController = TextEditingController();
  final cvvController = TextEditingController();

  String tipoTarjeta = 'VISA';

  List<PedidoResumen> pedidos = [];
  final Map<int, List<PedidoDetalle>> detallesCache = {};
  final Set<int> pagosConfirmados = {};

  @override
  void initState() {
    super.initState();
    cargarHistorial();
  }

  @override
  void dispose() {
    numeroController.dispose();
    titularController.dispose();
    expiracionController.dispose();
    cvvController.dispose();
    super.dispose();
  }

  Future<void> cargarHistorial() async {
    setState(() {
      loading = true;
      message = '';
    });

    final result = await PedidoService.obtenerHistorial();

    if (!mounted) return;

    setState(() {
      loading = false;
      pedidos = result.historial;
      message = result.success ? '' : result.message;
    });
  }

  bool pedidoPagado(PedidoResumen pedido) {
    final estado = pedido.estadoTransaccion.toUpperCase();
    return estado == 'CONFIRMADO' ||
        estado == 'COMPLETADO' ||
        estado == 'APROBADO' ||
        pagosConfirmados.contains(pedido.nroTransaccion);
  }

  Future<void> verDetalle(PedidoResumen pedido) async {
    setState(() {
      metodoPago = 'TARJETA';
      procesandoPago = false;
      qrLoading = false;
      numeroController.clear();
      titularController.clear();
      expiracionController.clear();
      cvvController.clear();
      tipoTarjeta = 'VISA';
    });

    if (detallesCache.containsKey(pedido.nroTransaccion)) {
      if (!mounted) return;
      _abrirDetalle(pedido, detallesCache[pedido.nroTransaccion]!);
      return;
    }

    setState(() {
      detalleLoading = true;
    });

    final result = await PedidoService.obtenerDetalle(pedido.nroTransaccion);

    if (!mounted) return;

    setState(() {
      detalleLoading = false;
    });

    if (!result.success) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(result.message)),
      );
      return;
    }

    detallesCache[pedido.nroTransaccion] = result.detalles;
    _abrirDetalle(pedido, result.detalles);
  }

  void seleccionarMetodo(String metodo, StateSetter setModalState) {
    setState(() {
      metodoPago = metodo;
    });

    setModalState(() {});

    if (metodo == 'QR_BANCARIO') {
      setState(() {
        qrLoading = true;
      });
      setModalState(() {});

      Future.delayed(const Duration(seconds: 2), () {
        if (!mounted) return;
        setState(() {
          qrLoading = false;
        });
        setModalState(() {});
      });
    }
  }

  Future<void> procesarPagoSimulado(
    PedidoResumen pedido,
    StateSetter setModalState,
  ) async {
    if (pedidoPagado(pedido)) return;

    if (metodoPago == 'TARJETA') {
      if (numeroController.text.trim().isEmpty ||
          titularController.text.trim().isEmpty ||
          expiracionController.text.trim().isEmpty ||
          cvvController.text.trim().isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Completa los datos de la tarjeta para simular el pago.'),
          ),
        );
        return;
      }
    }

    setState(() {
      procesandoPago = true;
    });
    setModalState(() {});

    await Future.delayed(const Duration(seconds: 2));

    if (!mounted) return;

    setState(() {
      procesandoPago = false;
      pagosConfirmados.add(pedido.nroTransaccion);
    });
    setModalState(() {});
  }

  void _abrirDetalle(PedidoResumen pedido, List<PedidoDetalle> detalles) {
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
        return StatefulBuilder(
          builder: (context, setModalState) {
            return _buildDetalleSheet(
              pedido,
              detalles,
              setModalState,
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final totalPedidos = pedidos.length;
    final montoTotal = pedidos.fold(0.0, (sum, p) => sum + p.montoTotal);

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: SafeArea(
        child: Column(
          children: [
            _buildTopBar(),
            Expanded(
              child: RefreshIndicator(
                onRefresh: cargarHistorial,
                color: AppTheme.primaryGreen,
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _buildMainHeader(),
                    const SizedBox(height: 12),
                    _buildStats(totalPedidos, montoTotal),
                    if (message.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      AgroErrorBox(message: message),
                    ],
                    const SizedBox(height: 16),
                    _buildHistorialCard(),
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
                  'MIS TRANSACCIONES',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w900,
                    color: Colors.white,
                    letterSpacing: 1,
                  ),
                ),
                SizedBox(height: 2),
                Text(
                  'Historial de compras y pagos',
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
            onPressed: cargarHistorial,
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

  Widget _buildMainHeader() {
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
                  'MIS TRANSACCIONES',
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
          Padding(
            padding: EdgeInsets.only(left: 17, top: 4),
            child: Text(
              'Historial de compras y pagos',
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w900,
                color: AppTheme.mutedText,
                letterSpacing: 1.1,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStats(int totalPedidos, double montoTotal) {
    return Row(
      children: [
        Expanded(
          child: _buildStatTile(
            icon: Icons.receipt_long,
            title: 'REGISTROS',
            value: totalPedidos.toString(),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _buildStatTile(
            icon: Icons.payments_outlined,
            title: 'TOTAL',
            value: 'Bs. ${montoTotal.toStringAsFixed(2)}',
          ),
        ),
      ],
    );
  }

  Widget _buildStatTile({
    required IconData icon,
    required String title,
    required String value,
  }) {
    return Container(
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(9),
      ),
      child: Row(
        children: [
          Icon(
            icon,
            color: AppTheme.primaryGreen,
            size: 23,
          ),
          const SizedBox(width: 9),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.w900,
                    color: AppTheme.mutedText,
                    letterSpacing: 1,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  value,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w900,
                    color: AppTheme.slateText,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHistorialCard() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(14),
            decoration: const BoxDecoration(
              color: Colors.white,
              border: Border(
                bottom: BorderSide(color: AppTheme.borderColor),
              ),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(9),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF1F5F9),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.description_outlined,
                    color: AppTheme.mutedText,
                    size: 22,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'HISTORIAL\n${pedidos.length} REGISTROS',
                    style: const TextStyle(
                      fontSize: 11,
                      height: 1.35,
                      fontWeight: FontWeight.w900,
                      color: AppTheme.slateText,
                      letterSpacing: 1,
                    ),
                  ),
                ),
              ],
            ),
          ),
          if (loading)
            const Padding(
              padding: EdgeInsets.all(32),
              child: CircularProgressIndicator(
                color: AppTheme.primaryGreen,
              ),
            )
          else if (pedidos.isEmpty)
            _buildEmpty()
          else
            Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                children: pedidos.map(_buildPedidoItem).toList(),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildPedidoItem(PedidoResumen pedido) {
    final confirmado = pedidoPagado(pedido);

    return InkWell(
      onTap: () => verDetalle(pedido),
      borderRadius: BorderRadius.circular(10),
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
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
                color: AppTheme.primaryGreen,
              ),
            ),
            Padding(
              padding: const EdgeInsets.only(left: 6),
              child: Column(
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          'ORD-${pedido.nroTransaccion.toString().padLeft(5, '0')}',
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w900,
                            color: AppTheme.slateText,
                            letterSpacing: 0.4,
                          ),
                        ),
                      ),
                      _buildEstadoBadge(confirmado),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      Text(
                        pedido.fechaHora,
                        style: const TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.mutedText,
                        ),
                      ),
                      const Spacer(),
                      const Text(
                        'TOTAL',
                        style: TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.w900,
                          color: AppTheme.mutedText,
                          letterSpacing: 1,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Align(
                    alignment: Alignment.centerRight,
                    child: Text(
                      'Bs. ${pedido.montoTotal.toStringAsFixed(2)}',
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w900,
                        color: AppTheme.slateText,
                      ),
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

  Widget _buildEstadoBadge(bool confirmado) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: confirmado ? Colors.green.shade50 : Colors.amber.shade50,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        children: [
          Icon(
            confirmado ? Icons.check : Icons.access_time,
            size: 13,
            color: confirmado ? Colors.green.shade700 : Colors.amber.shade700,
          ),
          const SizedBox(width: 4),
          Text(
            confirmado ? 'PAGADO' : 'PENDIENTE',
            style: TextStyle(
              fontSize: 9,
              fontWeight: FontWeight.w900,
              color: confirmado ? Colors.green.shade700 : Colors.amber.shade700,
              letterSpacing: 0.8,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDetalleSheet(
    PedidoResumen pedido,
    List<PedidoDetalle> detalles,
    StateSetter setModalState,
  ) {
    final montoTotal = detalles.fold(0.0, (sum, item) => sum + item.subtotal);
    final confirmado = pedidoPagado(pedido);

    return SafeArea(
      child: DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.90,
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
              _buildFacturaHeader(pedido),
              if (confirmado) ...[
                const SizedBox(height: 10),
                _buildPagoConfirmadoBanner(),
              ],
              const SizedBox(height: 12),
              if (detalleLoading)
                const Padding(
                  padding: EdgeInsets.all(32),
                  child: Center(
                    child: CircularProgressIndicator(
                      color: AppTheme.primaryGreen,
                    ),
                  ),
                )
              else
                _buildFacturaDetalle(detalles, montoTotal),
              if (!confirmado) ...[
                const SizedBox(height: 14),
                _buildPagoPanel(pedido, montoTotal, setModalState),
              ],
            ],
          );
        },
      ),
    );
  }

  Widget _buildFacturaHeader(PedidoResumen pedido) {
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
              Icons.receipt_long,
              color: Colors.white,
              size: 24,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'FACTURA DE COMPRA',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w900,
                    color: Colors.white,
                    letterSpacing: 1.1,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  'TRANSACCIÓN #${pedido.nroTransaccion.toString().padLeft(5, '0')}',
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
          Text(
            pedido.fechaHora.split(' ').first,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w900,
              color: Colors.white,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPagoConfirmadoBanner() {
    return Container(
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(
        color: Colors.green.shade50,
        border: Border.all(color: Colors.green.shade100),
        borderRadius: BorderRadius.circular(9),
      ),
      child: Row(
        children: [
          Icon(
            Icons.check_circle_outline,
            color: Colors.green.shade700,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              'PAGO CONFIRMADO EXITOSAMENTE',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w900,
                color: Colors.green.shade800,
                letterSpacing: 1,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFacturaDetalle(
    List<PedidoDetalle> detalles,
    double montoTotal,
  ) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
            decoration: const BoxDecoration(
              color: Color(0xFFF8FAFC),
              border: Border(
                bottom: BorderSide(color: AppTheme.borderColor),
              ),
            ),
            child: const Row(
              children: [
                Expanded(
                  flex: 3,
                  child: Text(
                    'INSUMO',
                    style: TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.w900,
                      color: AppTheme.mutedText,
                      letterSpacing: 1,
                    ),
                  ),
                ),
                Expanded(
                  child: Text(
                    'CANT.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.w900,
                      color: AppTheme.mutedText,
                      letterSpacing: 1,
                    ),
                  ),
                ),
                Expanded(
                  child: Text(
                    'SUBTOTAL',
                    textAlign: TextAlign.right,
                    style: TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.w900,
                      color: AppTheme.mutedText,
                      letterSpacing: 1,
                    ),
                  ),
                ),
              ],
            ),
          ),
          ...detalles.map((item) {
            return Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
              decoration: const BoxDecoration(
                border: Border(
                  bottom: BorderSide(color: Color(0xFFF1F5F9)),
                ),
              ),
              child: Row(
                children: [
                  Expanded(
                    flex: 3,
                    child: Text(
                      item.nombreProducto,
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.slateText,
                      ),
                    ),
                  ),
                  Expanded(
                    child: Text(
                      item.cantidad.toStringAsFixed(0),
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.mutedText,
                      ),
                    ),
                  ),
                  Expanded(
                    child: Text(
                      'Bs. ${item.subtotal.toStringAsFixed(2)}',
                      textAlign: TextAlign.right,
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w900,
                        color: AppTheme.primaryGreen,
                      ),
                    ),
                  ),
                ],
              ),
            );
          }),
          Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              children: [
                _buildTotalRow('SUBTOTAL', montoTotal),
                const SizedBox(height: 7),
                _buildTotalRow('IVA (13%)', 0),
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.all(13),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF1F5F9),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppTheme.borderColor),
                  ),
                  child: Row(
                    children: [
                      const Expanded(
                        child: Text(
                          'TOTAL A PAGAR',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w900,
                            color: AppTheme.slateText,
                            letterSpacing: 1,
                          ),
                        ),
                      ),
                      Text(
                        'Bs. ${montoTotal.toStringAsFixed(2)}',
                        style: const TextStyle(
                          fontSize: 19,
                          fontWeight: FontWeight.w900,
                          color: AppTheme.primaryGreen,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTotalRow(String label, double value) {
    return Row(
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w800,
            color: AppTheme.mutedText,
          ),
        ),
        const Spacer(),
        Text(
          'Bs. ${value.toStringAsFixed(2)}',
          style: const TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w900,
            color: AppTheme.mutedText,
          ),
        ),
      ],
    );
  }

  Widget _buildPagoPanel(
    PedidoResumen pedido,
    double montoTotal,
    StateSetter setModalState,
  ) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(
                Icons.lock_outline,
                color: Colors.amber,
                size: 18,
              ),
              SizedBox(width: 8),
              Text(
                'SELECCIONA UN MÉTODO DE PAGO',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w900,
                  color: AppTheme.slateText,
                  letterSpacing: 1,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              _buildMetodoButton(
                'TARJETA',
                Icons.credit_card,
                setModalState,
              ),
              const SizedBox(width: 8),
              _buildMetodoButton(
                'QR_BANCARIO',
                Icons.qr_code,
                setModalState,
              ),
              const SizedBox(width: 8),
              _buildMetodoButton(
                'EFECTIVO',
                Icons.payments_outlined,
                setModalState,
              ),
            ],
          ),
          const SizedBox(height: 14),
          _buildContenidoPago(setModalState),
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            height: 46,
            child: ElevatedButton.icon(
              onPressed: procesandoPago || qrLoading
                  ? null
                  : () => procesarPagoSimulado(pedido, setModalState),
              icon: procesandoPago
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(
                        color: Colors.white,
                        strokeWidth: 2,
                      ),
                    )
                  : const Icon(Icons.arrow_forward, size: 18),
              label: Text(
                procesandoPago
                    ? 'VERIFICANDO...'
                    : metodoPago == 'QR_BANCARIO'
                        ? 'VERIFICAR PAGO QR'
                        : 'PAGAR BS. ${montoTotal.toStringAsFixed(2)}',
                style: const TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 1.3,
                ),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.black87,
                foregroundColor: Colors.white,
                disabledBackgroundColor: Colors.grey.shade400,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetodoButton(
    String value,
    IconData icon,
    StateSetter setModalState,
  ) {
    final selected = metodoPago == value;

    return Expanded(
      child: InkWell(
        onTap: procesandoPago
            ? null
            : () => seleccionarMetodo(value, setModalState),
        borderRadius: BorderRadius.circular(10),
        child: Container(
          height: 82,
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.white,
            border: Border.all(
              color: selected ? AppTheme.primaryGreen : AppTheme.borderColor,
              width: selected ? 2 : 1,
            ),
            borderRadius: BorderRadius.circular(10),
            boxShadow: selected
                ? [
                    BoxShadow(
                      color: AppTheme.primaryGreen.withOpacity(0.12),
                      blurRadius: 8,
                      offset: const Offset(0, 4),
                    ),
                  ]
                : [],
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 22,
                color: selected ? AppTheme.primaryGreen : AppTheme.mutedText,
              ),
              const SizedBox(height: 7),
              Text(
                value.replaceAll('_', ' '),
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 8,
                  fontWeight: FontWeight.w900,
                  color: selected ? AppTheme.primaryGreen : AppTheme.mutedText,
                  letterSpacing: 0.8,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildContenidoPago(StateSetter setModalState) {
    if (metodoPago == 'QR_BANCARIO') {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border.all(color: AppTheme.borderColor),
          borderRadius: BorderRadius.circular(9),
        ),
        child: qrLoading
            ? const Column(
                children: [
                  CircularProgressIndicator(
                    color: AppTheme.primaryGreen,
                  ),
                  SizedBox(height: 12),
                  Text(
                    'GENERANDO CÓDIGO EN EL BANCO...',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w900,
                      color: AppTheme.mutedText,
                      letterSpacing: 1,
                    ),
                  ),
                ],
              )
            : Column(
                children: [
                  const Text(
                    'ESCANEA EL CÓDIGO PARA PAGAR',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w900,
                      color: AppTheme.mutedText,
                      letterSpacing: 1,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Container(
                    width: 160,
                    height: 160,
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      border: Border.all(
                        color: AppTheme.primaryGreen,
                        width: 2,
                      ),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Image.asset(
                      'assets/images/qr_agroenlace.jpeg',
                      fit: BoxFit.contain,
                    ),
                  ),
                  const SizedBox(height: 10),
                  const Text(
                    'Una vez escaneado, toca verificar pago QR.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.w700,
                      color: AppTheme.mutedText,
                    ),
                  ),
                ],
              ),
      );
    }

    if (metodoPago == 'EFECTIVO') {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.amber.shade50,
          border: Border.all(color: Colors.amber.shade100),
          borderRadius: BorderRadius.circular(9),
        ),
        child: Column(
          children: [
            Icon(
              Icons.warning_amber,
              color: Colors.amber.shade700,
              size: 32,
            ),
            const SizedBox(height: 8),
            Text(
              'PAGO CONTRA ENTREGA / CAJA',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w900,
                color: Colors.amber.shade800,
                letterSpacing: 1,
              ),
            ),
            const SizedBox(height: 5),
            Text(
              'Paga al momento de recibir tus insumos o acércate a la sucursal.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w700,
                color: Colors.amber.shade800,
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppTheme.borderColor),
        borderRadius: BorderRadius.circular(9),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'DATOS DE LA TARJETA',
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w900,
              color: AppTheme.mutedText,
              letterSpacing: 1,
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              _buildRadioTarjeta('VISA', setModalState),
              const SizedBox(width: 12),
              _buildRadioTarjeta('MASTERCARD', setModalState),
            ],
          ),
          const SizedBox(height: 12),
          _buildInput(
            label: 'Número de tarjeta',
            hint: '0000 0000 0000 0000',
            controller: numeroController,
            keyboardType: TextInputType.number,
          ),
          const SizedBox(height: 10),
          _buildInput(
            label: 'Titular de la tarjeta',
            hint: 'JUAN PEREZ',
            controller: titularController,
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: _buildInput(
                  label: 'Vencimiento',
                  hint: 'MM/YY',
                  controller: expiracionController,
                  keyboardType: TextInputType.datetime,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _buildInput(
                  label: 'CVV',
                  hint: '123',
                  controller: cvvController,
                  keyboardType: TextInputType.number,
                  obscureText: true,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRadioTarjeta(String value, StateSetter setModalState) {
    return InkWell(
      onTap: () {
        setState(() {
          tipoTarjeta = value;
        });
        setModalState(() {});
      },
      child: Row(
        children: [
          Radio<String>(
            value: value,
            groupValue: tipoTarjeta,
            activeColor: AppTheme.primaryGreen,
            onChanged: (selected) {
              setState(() {
                tipoTarjeta = selected ?? 'VISA';
              });
              setModalState(() {});
            },
          ),
          Text(
            value,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w900,
              color: AppTheme.slateText,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInput({
    required String label,
    required String hint,
    required TextEditingController controller,
    TextInputType keyboardType = TextInputType.text,
    bool obscureText = false,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
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
        const SizedBox(height: 5),
        TextField(
          controller: controller,
          keyboardType: keyboardType,
          obscureText: obscureText,
          decoration: InputDecoration(
            hintText: hint,
          ),
        ),
      ],
    );
  }

  Widget _buildEmpty() {
    return const Padding(
      padding: EdgeInsets.all(34),
      child: Column(
        children: [
          Icon(
            Icons.shopping_cart_outlined,
            size: 46,
            color: Colors.grey,
          ),
          SizedBox(height: 10),
          Text(
            'AÚN NO TIENES COMPRAS',
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