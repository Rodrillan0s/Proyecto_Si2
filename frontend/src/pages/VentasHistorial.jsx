import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useAuthStore } from '../store/auth_store';
import imgQr from '../assets/qr_agroenlace.jpeg'

export default function HistorialPedidos() {
  const API_URL = import.meta.env.VITE_API_URL;
  const token = useAuthStore((state) => state.token);
  const { id_usuario } = useAuthStore((state) => state.user);
  
  const [pedidos, setPedidos] = useState([]);
  const [detalle, setDetalle] = useState(null);
  const [descuentoDetalle, setDescuentoDetalle] = useState(null);
  const [pedidoSeleccionado, setPedidoSeleccionado] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detalleLoading, setDetalleLoading] = useState(false);
  
  // Estados para simulación de pago
  const [metodoPago, setMetodoPago] = useState('TARJETA');
  const [procesandoPago, setProcesandoPago] = useState(false);
  const [pagoExitoso, setPagoExitoso] = useState(false);

  // --- NUEVOS ESTADOS PARA SIMULACIÓN AVANZADA ---
  const [qrLoading, setQrLoading] = useState(false);
  const [datosTarjeta, setDatosTarjeta] = useState({
    tipo: 'VISA',
    numero: '',
    titular: '',
    expiracion: '',
    cvv: ''
  });

  // Caché y Referencias
  const detallesCache = useRef({});
  const detalleRef = useRef(null); 

  const cargarHistorial = useCallback(() => {
    if (!id_usuario || !token) return;
    setLoading(true);
    fetch(`${API_URL}/pedidos/historial?id_usuario=${id_usuario}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => {
      setPedidos(data.listado || []);
      setLoading(false);
    })
    .catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, [id_usuario, token, API_URL]);

  useEffect(() => {
    cargarHistorial();
  }, [cargarHistorial]);

  const verDetalle = useCallback(async (pedido) => {
    // Resetear estados
    setMetodoPago('TARJETA');
    setPagoExitoso(false);
    setProcesandoPago(false);
    setPedidoSeleccionado(pedido);
    setDescuentoDetalle(null);
    setDatosTarjeta({ tipo: 'VISA', numero: '', titular: '', expiracion: '', cvv: '' });

    // Scroll suave automático en móviles hacia el detalle
    setTimeout(() => {
      detalleRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);

    if (detallesCache.current[pedido.nro_transaccion]) {
      setDetalle(detallesCache.current[pedido.nro_transaccion].detalles);
      setDescuentoDetalle(detallesCache.current[pedido.nro_transaccion].descuento);
      return;
    }

    setDetalleLoading(true);
    try {
      const res = await fetch(`${API_URL}/pedidos/detalle?nro_transaccion=${pedido.nro_transaccion}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      detallesCache.current[pedido.nro_transaccion] = {
        detalles: data.detalles,
        descuento: data.descuento
      };
      setDetalle(data.detalles);
      setDescuentoDetalle(data.descuento || null);
    } catch (err) {
      console.error('Error al cargar detalles:', err);
    } finally {
      setDetalleLoading(false);
    }
  }, [API_URL, token]);

  const montoTotal = useMemo(() => {
    return detalle?.reduce((acc, item) => acc + (item.cantidad * item.precio_venta), 0) || 0;
  }, [detalle]);

  // Manejador para seleccionar método de pago y simular loader del QR
  const handleSeleccionarMetodo = (metodo) => {
    setMetodoPago(metodo);
    if (metodo === 'QR_BANCARIO') {
      setQrLoading(true);
      // Simula generación de QR en el banco por 3 segundos
      setTimeout(() => {
        setQrLoading(false);
      }, 3000);
    }
  };

  const handleTarjetaChange = (e) => {
    setDatosTarjeta({ ...datosTarjeta, [e.target.name]: e.target.value });
  };

  // =========================================================
  // SIMULACIÓN DE PASARELA DE PAGO
  // =========================================================
  const procesarPagoSimulado = async () => {
    if (!pedidoSeleccionado || pedidoSeleccionado.estado_transaccion === 'CONFIRMADO') return;
    
    // Validación básica si es tarjeta
    if (metodoPago === 'TARJETA') {
      if (!datosTarjeta.numero || !datosTarjeta.titular || !datosTarjeta.expiracion || !datosTarjeta.cvv) {
        alert("Por favor, complete todos los campos de la tarjeta para simular el pago.");
        return;
      }
    }

    setProcesandoPago(true);
    await new Promise(resolve => setTimeout(resolve, 2000)); // Delay simulado procesando pago
    
    const nuevosPedidos = pedidos.map(p => 
      p.nro_transaccion === pedidoSeleccionado.nro_transaccion 
        ? { ...p, estado_transaccion: 'CONFIRMADO' } 
        : p
    );
    setPedidos(nuevosPedidos);
    setPedidoSeleccionado(prev => ({ ...prev, estado_transaccion: 'CONFIRMADO' }));
    
    setProcesandoPago(false);
    setPagoExitoso(true);
  };

  return (
    <div className="p-4 md:p-6 lg:p-8 animate-in fade-in duration-500 bg-slate-50 min-h-screen">
      
      {/* CABECERA */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-black text-slate-800 tracking-tight flex items-center gap-3">
            <div className="w-2 h-6 md:h-8 bg-[#1A5729]"></div>
            MIS TRANSACCIONES
          </h1>
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1 ml-5">
            Historial de compras y pagos
          </p>
        </div>
        <button 
          onClick={cargarHistorial}
          className="self-start sm:self-auto flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-[#1A5729] bg-[#1A5729]/10 hover:bg-[#1A5729]/20 px-4 py-2.5 rounded-lg transition-colors active:scale-95"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          Actualizar
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* ========================================= */}
        {/* LISTA DE PEDIDOS (COLUMNA IZQUIERDA)      */}
        {/* ========================================= */}
        <div className="lg:col-span-4 xl:col-span-3 flex flex-col gap-4">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col max-h-[450px] lg:max-h-[calc(100vh-140px)]">
            
            {/* Header Sticky */}
            <div className="p-4 bg-white border-b border-slate-100 flex items-center gap-3 shrink-0 sticky top-0 z-10 shadow-[0_4px_6px_-1px_rgba(0,0,0,0.02)]">
              <div className="bg-slate-100 p-2 rounded-lg text-slate-600">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              </div>
              <div>
                <h2 className="text-xs font-black text-slate-800 uppercase tracking-widest">Historial</h2>
                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">{pedidos.length} Registros</p>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-3 bg-slate-50/50">
              {loading ? (
                <div className="p-8 text-center flex flex-col items-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1A5729]"></div>
                  <p className="text-[10px] text-slate-400 font-bold uppercase mt-4 tracking-widest">Cargando...</p>
                </div>
              ) : pedidos.length === 0 ? (
                <div className="p-8 text-center text-slate-400 flex flex-col items-center">
                  <svg className="w-12 h-12 mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}><path strokeLinecap="round" strokeLinejoin="round" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
                  <p className="text-[10px] font-bold uppercase tracking-widest">Aún no tienes compras</p>
                </div>
              ) : (
                pedidos.map(p => {
                  const isSelected = pedidoSeleccionado?.nro_transaccion === p.nro_transaccion;
                  const isConfirmed = p.estado_transaccion?.toUpperCase() === 'CONFIRMADO';
                  
                  return (
                    <div 
                      key={p.nro_transaccion} 
                      onClick={() => verDetalle(p)}
                      className={`relative overflow-hidden p-4 rounded-xl cursor-pointer transition-all duration-200 border ${
                        isSelected 
                          ? 'bg-white border-[#1A5729] shadow-md ring-1 ring-[#1A5729]/20 scale-[1.02] z-10' 
                          : 'bg-white border-slate-200 hover:border-slate-300 hover:shadow-sm'
                      }`}
                    >
                      <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${isSelected ? 'bg-[#1A5729]' : 'bg-transparent'}`}></div>
                      
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <p className={`font-black text-xs md:text-sm tracking-tight ${isSelected ? 'text-[#1A5729]' : 'text-slate-800'}`}>
                            ORD-{String(p.nro_transaccion).padStart(5, '0')}
                          </p>
                          <p className="text-[10px] text-slate-400 font-bold uppercase mt-0.5">
                            {new Date(p.fecha_hora).toLocaleDateString('es-BO', { day: '2-digit', month: 'short', year: 'numeric' })}
                          </p>
                        </div>
                        <span className={`px-2 py-1 rounded text-[9px] font-black uppercase tracking-wider flex items-center gap-1 ${
                          isConfirmed ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-600'
                        }`}>
                          {isConfirmed ? (
                            <><svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg> Pagado</>
                          ) : (
                            <><svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg> Pendiente</>
                          )}
                        </span>
                      </div>
                      <div className="flex justify-between items-end mt-2 pt-2 border-t border-slate-50">
                        <p className="text-[9px] text-slate-400 font-bold uppercase tracking-widest">Total</p>
                        <p className="text-sm font-black text-slate-800">
                          Bs. {Number(p.monto_total).toFixed(2)}
                        </p>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* ========================================= */}
        {/* DETALLE Y PAGO (COLUMNA DERECHA)          */}
        {/* ========================================= */}
        <div ref={detalleRef} className="lg:col-span-8 xl:col-span-9 flex flex-col gap-6 scroll-mt-6">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden min-h-[400px] flex flex-col relative transition-all">
            
            {pedidoSeleccionado ? (
              <>
                {/* HEADER DE FACTURA */}
                <div className="bg-gradient-to-r from-[#1A5729] to-[#123e1d] px-4 md:px-6 py-5 text-white flex justify-between items-center shrink-0">
                  <div className="flex items-center gap-3 md:gap-4">
                    <div className="bg-white/10 p-2.5 md:p-3 rounded-full hidden min-[400px]:block">
                      <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2.5 2.5 0 00-2.5-2.5H15M9 11l3 3L22 4" /></svg>
                    </div>
                    <div>
                      <h3 className="text-sm md:text-base font-black uppercase tracking-widest">
                        Factura de Compra
                      </h3>
                      <p className="text-[10px] md:text-[11px] font-bold text-emerald-200/90 uppercase tracking-widest mt-0.5">
                        Transacción #{String(pedidoSeleccionado.nro_transaccion).padStart(5, '0')}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-[9px] md:text-[10px] font-bold uppercase tracking-widest text-emerald-200/90 mb-0.5">Emisión</p>
                    <p className="text-xs md:text-sm font-black tracking-tight">
                      {new Date(pedidoSeleccionado.fecha_hora).toLocaleDateString('es-BO')}
                    </p>
                  </div>
                </div>

                {/* BANNER DE ESTADO CONFIRMADO */}
                {pedidoSeleccionado.estado_transaccion === 'CONFIRMADO' && (
                  <div className="bg-emerald-50 border-b border-emerald-100 px-4 md:px-6 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-emerald-800">
                    <div className="flex items-center gap-2">
                      <svg className="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                      <span className="text-xs font-black uppercase tracking-widest">Pago Confirmado Exitosamente</span>
                    </div>
                    <button className="text-[10px] font-bold flex items-center gap-1 bg-white px-3 py-1.5 rounded border border-emerald-200 shadow-sm hover:bg-emerald-100 transition-colors uppercase">
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                      Recibo PDF
                    </button>
                  </div>
                )}

                {/* CUERPO DE FACTURA (TABLA) */}
                <div className="flex-1 p-4 md:p-6">
                  {detalleLoading ? (
                    <div className="flex justify-center items-center py-20">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1A5729]"></div>
                    </div>
                  ) : (
                    <>
                      <div className="overflow-x-auto custom-scrollbar border border-slate-100 rounded-lg">
                        <table className="w-full text-left text-sm min-w-[450px]">
                          <thead className="bg-slate-50">
                            <tr className="text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-slate-200">
                              <th className="p-3 w-1/2">Insumo</th>
                              <th className="p-3 text-center">Cant.</th>
                              <th className="p-3 text-right">P. Unit.</th>
                              <th className="p-3 text-right">Subtotal</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {detalle?.map((item, i) => (
                              <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                                <td className="p-3 text-xs font-bold text-slate-800">{item.nombre_producto}</td>
                                <td className="p-3 text-xs text-center font-medium text-slate-600 bg-slate-50/50">{item.cantidad}</td>
                                <td className="p-3 text-xs text-right font-medium text-slate-600">Bs. {Number(item.precio_venta).toFixed(2)}</td>
                                <td className="p-3 text-xs text-right font-black text-[#1A5729]">
                                  Bs. {(item.cantidad * item.precio_venta).toFixed(2)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {/* TOTALES */}
                      <div className="flex justify-end pt-6">
                        <div className="w-full sm:w-64 space-y-3">
                          <div className="flex justify-between text-xs font-bold text-slate-500 px-2">
                            <span>Subtotal:</span>
                            <span>Bs. {Number(descuentoDetalle?.subtotal_original || montoTotal).toFixed(2)}</span>
                          </div>
                          {descuentoDetalle && Number(descuentoDetalle.descuento_total || 0) > 0 && (
                            <>
                              <div className="flex justify-between text-xs font-bold text-emerald-700 px-2">
                                <span>Nivel {descuentoDetalle.nivel_fidelizacion} ({Number(descuentoDetalle.porcentaje_descuento).toFixed(0)}%):</span>
                                <span>- Bs. {Number(descuentoDetalle.descuento_total).toFixed(2)}</span>
                              </div>
                            </>
                          )}
                          <div className="flex justify-between text-xs font-bold text-slate-500 px-2">
                            <span>IVA (13%):</span>
                            <span>Bs. 0.00</span>
                          </div>
                          <div className="flex justify-between items-center bg-slate-100 p-3 rounded-lg border border-slate-200 shadow-sm mt-2">
                            <span className="text-[11px] font-black uppercase tracking-widest text-slate-700">Total a Pagar</span>
                            <span className="text-lg font-black text-[#1A5729]">Bs. {montoTotal.toFixed(2)}</span>
                          </div>
                        </div>
                      </div>
                    </>
                  )}
                </div>

                {/* ========================================= */}
                {/* ZONA DE PAGO (SOLO SI ESTÁ PENDIENTE)     */}
                {/* ========================================= */}
                {pedidoSeleccionado.estado_transaccion === 'PENDIENTE' && !detalleLoading && (
                  <div className="bg-slate-50 border-t border-slate-200 p-4 md:p-6 animate-in slide-in-from-bottom-4 duration-500">
                    <h4 className="text-[11px] font-black text-slate-800 uppercase tracking-widest mb-4 flex items-center gap-2">
                      <svg className="w-4 h-4 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                      Selecciona un Método de Pago
                    </h4>
                    
                    {pagoExitoso ? (
                      <div className="bg-emerald-100 border border-emerald-200 text-emerald-800 p-6 rounded-xl text-center animate-in zoom-in-95 duration-300">
                        <div className="w-12 h-12 bg-emerald-500 rounded-full flex items-center justify-center mx-auto mb-3 shadow-lg shadow-emerald-500/30">
                          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                        </div>
                        <h5 className="font-black uppercase tracking-widest mb-1 text-sm">¡Pago Procesado!</h5>
                        <p className="text-[10px] md:text-xs font-medium opacity-80 uppercase tracking-wider">La transacción ha sido aprobada con éxito.</p>
                      </div>
                    ) : (
                      <>
                        <div className="grid grid-cols-2 min-[500px]:grid-cols-3 gap-3 mb-6">
                          {/* Opciones de Pago Adaptables */}
                          {['TARJETA', 'QR_BANCARIO', 'EFECTIVO'].map((metodo) => (
                            <button
                              key={metodo}
                              type="button"
                              onClick={() => handleSeleccionarMetodo(metodo)}
                              disabled={procesandoPago}
                              className={`flex flex-col items-center justify-center p-3 md:p-4 rounded-xl border-2 transition-all duration-200 disabled:opacity-50 ${
                                metodoPago === metodo 
                                  ? 'border-[#1A5729] bg-white shadow-md text-[#1A5729] scale-[1.02]' 
                                  : 'border-slate-200 bg-white text-slate-500 hover:border-slate-300 hover:bg-slate-50'
                              }`}
                            >
                              {metodo === 'TARJETA' && <svg className="w-5 h-5 md:w-6 md:h-6 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>}
                              {metodo === 'QR_BANCARIO' && <svg className="w-5 h-5 md:w-6 md:h-6 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm14 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" /></svg>}
                              {metodo === 'EFECTIVO' && <svg className="w-5 h-5 md:w-6 md:h-6 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" /></svg>}
                              
                              <span className="text-[9px] font-black uppercase tracking-widest text-center">{metodo.replace('_', ' ')}</span>
                            </button>
                          ))}
                        </div>

                        {/* --- CONTENIDO DINÁMICO SEGÚN MÉTODO DE PAGO --- */}
                        <div className="mb-6 bg-white p-4 border border-slate-200 rounded-lg shadow-sm">
                          
                          {/* 1. TARJETA DE CRÉDITO/DÉBITO */}
                          {metodoPago === 'TARJETA' && (
                            <div className="animate-in fade-in zoom-in-95 duration-300">
                              <h5 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 border-b border-slate-100 pb-2">Datos de la Tarjeta</h5>
                              
                              <div className="mb-3">
                                <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">Tipo de Tarjeta</label>
                                <div className="flex gap-4">
                                  <label className="flex items-center gap-2 cursor-pointer">
                                    <input type="radio" name="tipo" value="VISA" checked={datosTarjeta.tipo === 'VISA'} onChange={handleTarjetaChange} className="accent-[#1A5729]" />
                                    <span className="text-xs font-black text-slate-700">VISA</span>
                                  </label>
                                  <label className="flex items-center gap-2 cursor-pointer">
                                    <input type="radio" name="tipo" value="MASTERCARD" checked={datosTarjeta.tipo === 'MASTERCARD'} onChange={handleTarjetaChange} className="accent-[#1A5729]" />
                                    <span className="text-xs font-black text-slate-700">MasterCard</span>
                                  </label>
                                </div>
                              </div>

                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
                                <div>
                                  <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">Número de Tarjeta</label>
                                  <input type="text" name="numero" value={datosTarjeta.numero} onChange={handleTarjetaChange} placeholder="0000 0000 0000 0000" maxLength="19" className="w-full px-3 py-2 border border-slate-300 rounded text-xs font-mono outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]" />
                                </div>
                                <div>
                                  <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">Titular de la Tarjeta</label>
                                  <input type="text" name="titular" value={datosTarjeta.titular} onChange={handleTarjetaChange} placeholder="JUAN PEREZ" className="w-full px-3 py-2 border border-slate-300 rounded text-xs uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]" />
                                </div>
                              </div>

                              <div className="grid grid-cols-2 gap-3">
                                <div>
                                  <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">Vencimiento</label>
                                  <input type="text" name="expiracion" value={datosTarjeta.expiracion} onChange={handleTarjetaChange} placeholder="MM/YY" maxLength="5" className="w-full px-3 py-2 border border-slate-300 rounded text-xs font-mono outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]" />
                                </div>
                                <div>
                                  <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">CVV</label>
                                  <input type="password" name="cvv" value={datosTarjeta.cvv} onChange={handleTarjetaChange} placeholder="123" maxLength="4" className="w-full px-3 py-2 border border-slate-300 rounded text-xs font-mono outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]" />
                                </div>
                              </div>
                            </div>
                          )}

                          {/* 2. QR BANCARIO */}
                          {metodoPago === 'QR_BANCARIO' && (
                            <div className="flex flex-col items-center justify-center p-4 min-h-[200px] animate-in fade-in duration-300">
                              {qrLoading ? (
                                <div className="flex flex-col items-center gap-3">
                                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1A5729]"></div>
                                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest animate-pulse">Generando código en el banco...</p>
                                </div>
                              ) : (
                                <div className="text-center animate-in zoom-in-95 duration-300">
                                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3">
                                    Escanea el código para pagar
                                  </p>
                                  
                                  <div className="w-40 h-40 border-2 border-dashed border-[#1A5729] rounded-xl p-2 flex items-center justify-center mx-auto mb-3 bg-white relative overflow-hidden shadow-sm">
                                    {/* --- PON LA RUTA DE TU IMAGEN QR AQUÍ EN EL ATRIBUTO src --- */}
                                    <img 
                                      src={imgQr} 
                                      alt="QR BANCARIO" 
                                      className="w-full h-full object-contain rounded-lg"
                                    />
                                  </div>
                                  
                                  <p className="text-[9px] text-slate-400 uppercase tracking-wider">
                                    Una vez escaneado, haz clic en procesar
                                  </p>
                                </div>
                              )}
                            </div>
                          )}

                          {/* 3. EFECTIVO */}
                          {metodoPago === 'EFECTIVO' && (
                            <div className="text-center p-6 bg-amber-50 rounded-lg border border-amber-100 animate-in fade-in duration-300">
                              <svg className="w-8 h-8 mx-auto text-amber-500 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                              <h5 className="text-[11px] font-black text-amber-800 uppercase tracking-widest mb-1">Pago Contra Entrega / Caja</h5>
                              <p className="text-[10px] font-medium text-amber-700">Por favor, acérquese a nuestra sucursal o pague al repartidor al momento de recibir sus insumos.</p>
                            </div>
                          )}
                        </div>

                        {/* BOTÓN DE ACCIÓN FINAL */}
                        <div className="flex flex-col sm:flex-row justify-end gap-3">
                          <button
                            onClick={procesarPagoSimulado}
                            disabled={procesandoPago || qrLoading}
                            className="w-full sm:w-auto bg-slate-900 hover:bg-black text-white px-6 py-3.5 md:py-3 rounded-lg text-xs font-black uppercase tracking-widest flex items-center justify-center gap-3 transition-all disabled:opacity-70 disabled:cursor-not-allowed shadow-lg active:scale-95"
                          >
                            {procesandoPago ? (
                              <>
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                VERIFICANDO...
                              </>
                            ) : (
                              <>
                                {(metodoPago === 'TARJETA' || metodoPago === 'EFECTIVO') ? `PAGAR BS. ${montoTotal.toFixed(2)}` : 'VERIFICAR PAGO QR'}
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                              </>
                            )}
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                )}
              </>
            ) : (
              // PANTALLA VACÍA CUANDO NO HAY PEDIDO SELECCIONADO
              <div className="flex-1 flex flex-col items-center justify-center p-8 md:p-12 text-center bg-slate-50/30">
                <div className="w-20 h-20 md:w-24 md:h-24 bg-white rounded-full shadow-sm border border-slate-100 flex items-center justify-center mb-5">
                  <svg className="w-10 h-10 md:w-12 md:h-12 text-slate-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                </div>
                <h3 className="text-xs md:text-sm font-black text-slate-600 uppercase tracking-widest mb-2">Seleccione un Pedido</h3>
                <p className="text-[10px] md:text-[11px] text-slate-400 font-bold uppercase tracking-wider max-w-xs leading-relaxed">
                  Haga clic en cualquier registro del panel para visualizar el detalle y procesar el pago.
                </p>
              </div>
            )}
            
          </div>
        </div>

      </div>
    </div>
  );
}
