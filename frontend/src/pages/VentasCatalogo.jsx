import { useState, useEffect, useRef } from 'react';
import { useAuthStore } from '../store/auth_store';

export default function VentasCatalogo() {
  const API_URL = import.meta.env.VITE_API_URL;
  const token = useAuthStore((state) => state.token);
  const { id_usuario, id_empresa } = useAuthStore((state) => state.user || { id_usuario: 2, id_empresa: 1 });
  
  const [catalogo, setCatalogo] = useState([]);
  const [carrito, setCarrito] = useState([]);
  const [loading, setLoading] = useState(true);
  const [enviando, setEnviando] = useState(false);
  const [busqueda, setBusqueda] = useState('');
  
  const [pedidoExitoso, setPedidoExitoso] = useState(null);
  const carritoRef = useRef(null);

  useEffect(() => {
    cargarCatalogo();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const cargarCatalogo = async () => {
    try {
      const res = await fetch(`${API_URL}/insumos/catalogo?id_empresa=${id_empresa}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.success) {
        setCatalogo(data.catalogo);
      }
    } catch (error) {
      console.error("Error al cargar el catálogo", error);
    } finally {
      setLoading(false);
    }
  };

  const agregarAlCarrito = (producto) => {
    setCarrito((prev) => {
      const existe = prev.find((item) => item.id_producto === producto.id_producto);
      if (existe) {
        if (existe.cantidad >= producto.stock_actual) return prev;
        return prev.map((item) =>
          item.id_producto === producto.id_producto
            ? { ...item, cantidad: item.cantidad + 1 }
            : item
        );
      }
      return [...prev, { ...producto, cantidad: 1 }];
    });
  };

  const quitarDelCarrito = (id_producto) => {
    setCarrito((prev) => prev.filter((item) => item.id_producto !== id_producto));
  };

  const actualizarCantidad = (id_producto, nuevaCantidad, stock_max) => {
    if (nuevaCantidad < 1 || nuevaCantidad > stock_max) return;
    setCarrito((prev) =>
      prev.map((item) =>
        item.id_producto === id_producto ? { ...item, cantidad: nuevaCantidad } : item
      )
    );
  };

  const totalCarrito = carrito.reduce((acc, item) => acc + (item.cantidad * item.precio_unitario), 0);
  const cantidadItemsCarrito = carrito.reduce((acc, item) => acc + item.cantidad, 0);

  const confirmarPedido = async () => {
    if (carrito.length === 0) return;
    setEnviando(true);

    const payload = {
      id_cliente: id_usuario,
      id_supervisor_admin: 15,
      id_empresa: id_empresa,
      detalles: carrito.map(item => ({
        id_producto: item.id_producto,
        cantidad: item.cantidad,
        precio_unitario: item.precio_unitario
      }))
    };

    try {
      const response = await fetch(`${API_URL}/pedidos/crear`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      const res = await response.json();
      
      if (res.success) {
        setPedidoExitoso({
          transaccion: res.nro_transaccion,
          total: res.monto_total,
          subtotal: res.subtotal_original,
          descuento: res.descuento_total,
          porcentaje: res.porcentaje_descuento,
          nivel: res.nivel_fidelizacion
        });
        setCarrito([]);
        cargarCatalogo(); 
      } else {
        alert(`Atención: ${res.message}`);
      }
    } catch (error) {
      alert('Error de red al procesar el pedido.');
    } finally {
      setEnviando(false);
    }
  };

  const catalogoFiltrado = catalogo.filter(prod => 
    prod.nombre_producto.toLowerCase().includes(busqueda.toLowerCase()) || 
    prod.categoria.toLowerCase().includes(busqueda.toLowerCase())
  );

  const irAlCarrito = () => {
    carritoRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Íconos SVG más sobrios y monocromáticos
  const getCategoryIcon = (categoria) => {
    if (categoria === 'SEMILLA') {
      return <svg className="w-10 h-10 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" /></svg>;
    }
    return <svg className="w-10 h-10 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>;
  };

  return (
    <div className="p-4 md:p-6 lg:p-8 animate-in fade-in duration-500 bg-slate-50 min-h-screen flex flex-col lg:flex-row gap-6 lg:gap-8 relative pb-24 lg:pb-8">
      
      {/* SECCIÓN IZQUIERDA: CATÁLOGO */}
      <div className="flex-1 w-full max-w-7xl mx-auto">
        
        {/* HEADER Y BUSCADOR (Diseño Corporativo) */}
        <div className="mb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-4 bg-white p-5 border border-slate-200 shadow-sm rounded-md">
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-3">
              <div className="w-1.5 h-6 bg-[#1A5729]"></div>
              CATÁLOGO DE INSUMOS
            </h1>
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1 ml-4">
              Gestión de Pedidos Comerciales
            </p>
          </div>
          
          <div className="w-full md:w-72 relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            </div>
            <input
              type="text"
              placeholder="Buscar producto o categoría..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-md text-xs font-medium text-slate-700 outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] transition-all bg-white"
            />
          </div>
        </div>

        {/* GRILLA DE PRODUCTOS */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400 border border-slate-200 bg-white rounded-md">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1A5729] mb-4"></div>
            <span className="font-bold uppercase text-[10px] tracking-widest">Cargando inventario...</span>
          </div>
        ) : catalogoFiltrado.length === 0 ? (
          <div className="text-center py-20 bg-white border border-slate-200 rounded-md">
            <svg className="w-12 h-12 text-slate-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}><path strokeLinecap="round" strokeLinejoin="round" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <p className="text-slate-500 font-bold uppercase text-[10px] tracking-widest">No se encontraron resultados</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {catalogoFiltrado.map((prod) => {
              const itemCarrito = carrito.find(i => i.id_producto === prod.id_producto);
              const cantidadActual = itemCarrito ? itemCarrito.cantidad : 0;
              const sinStock = prod.stock_actual <= 0;
              const limiteAlcanzado = cantidadActual >= prod.stock_actual;

              return (
                <div key={prod.id_producto} className={`bg-white border ${sinStock ? 'border-slate-200 opacity-60' : 'border-slate-300 hover:border-[#1A5729]/50'} p-4 shadow-sm transition-colors duration-200 flex flex-col h-full rounded-md`}>
                  
                  {/* Placeholder de Imagen más sobrio */}
                  <div className="h-28 bg-slate-50 border border-slate-200 mb-4 flex items-center justify-center rounded-sm">
                    {getCategoryIcon(prod.categoria)}
                  </div>

                  <div className="flex justify-between items-center mb-3">
                    <span className="px-2 py-0.5 border border-slate-200 bg-slate-50 text-slate-600 rounded text-[9px] font-bold uppercase tracking-widest">
                      {prod.categoria}
                    </span>
                    <span className={`text-[9px] font-bold uppercase tracking-wider ${sinStock ? 'text-red-600' : 'text-slate-500'}`}>
                      Stock: {prod.stock_actual} {prod.unidad_medida}
                    </span>
                  </div>
                  
                  <h3 className="font-bold text-slate-800 text-sm mb-1 flex-1">{prod.nombre_producto}</h3>
                  <div className="flex items-end gap-1 mb-4">
                    <span className="text-xs text-slate-500 font-bold mb-0.5">Bs.</span>
                    <span className="text-lg font-bold text-slate-900">{Number(prod.precio_unitario).toFixed(2)}</span>
                  </div>

                  <button 
                    onClick={() => agregarAlCarrito(prod)}
                    disabled={sinStock || limiteAlcanzado}
                    className={`w-full py-2.5 rounded-md font-bold text-[10px] uppercase tracking-widest transition-colors flex items-center justify-center gap-2 ${
                      limiteAlcanzado || sinStock
                        ? 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200' 
                        : 'bg-white border border-[#1A5729] text-[#1A5729] hover:bg-[#1A5729] hover:text-white'
                    }`}
                  >
                    {limiteAlcanzado ? (
                      'Límite Alcanzado'
                    ) : sinStock ? (
                      'Agotado'
                    ) : (
                      <>
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
                        {cantidadActual > 0 ? `Agregar otro (${cantidadActual})` : 'Agregar a la orden'}
                      </>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* SECCIÓN DERECHA: CARRITO Y CHECKOUT */}
      <div ref={carritoRef} className="w-full lg:w-[350px] xl:w-[380px] shrink-0 mt-8 lg:mt-0 scroll-mt-6">
        <div className="bg-white border border-slate-300 shadow-sm flex flex-col h-auto lg:h-[calc(100vh-64px)] lg:sticky lg:top-8 rounded-md overflow-hidden">
          
          <div className="p-4 border-b border-slate-200 bg-slate-50">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-widest flex items-center gap-2">
              <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
              Orden en Proceso
            </h2>
            <p className="text-[10px] text-slate-500 font-medium mt-1">
              {cantidadItemsCarrito} ítems agregados
            </p>
          </div>

          <div className="flex-1 overflow-y-auto p-4 custom-scrollbar bg-white">
            {carrito.length === 0 ? (
              <div className="h-full min-h-[150px] flex flex-col items-center justify-center text-slate-400">
                <svg className="w-10 h-10 mb-3 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}><path strokeLinecap="round" strokeLinejoin="round" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Orden vacía</p>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {carrito.map((item) => (
                  <div key={item.id_producto} className="bg-white p-3 border border-slate-200 flex flex-col gap-3 relative rounded-sm">
                    
                    <button onClick={() => quitarDelCarrito(item.id_producto)} className="absolute top-2 right-2 text-slate-400 hover:text-red-600 transition-colors bg-white">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>

                    <div className="pr-6">
                      <h4 className="text-xs font-bold text-slate-800 leading-tight">{item.nombre_producto}</h4>
                      <p className="text-[10px] font-medium text-slate-500 mt-1">Bs. {Number(item.precio_unitario).toFixed(2)} / {item.unidad_medida}</p>
                    </div>
                    
                    <div className="flex items-center justify-between mt-1 pt-2 border-t border-slate-100">
                      <div className="flex items-center border border-slate-300 rounded-sm overflow-hidden">
                        <button onClick={() => actualizarCantidad(item.id_producto, item.cantidad - 1, item.stock_actual)} className="w-6 h-6 flex items-center justify-center bg-slate-50 hover:bg-slate-200 text-slate-600 transition-colors">-</button>
                        <span className="text-xs font-bold w-8 text-center text-slate-800 border-x border-slate-300 bg-white">{item.cantidad}</span>
                        <button onClick={() => actualizarCantidad(item.id_producto, item.cantidad + 1, item.stock_actual)} className="w-6 h-6 flex items-center justify-center bg-slate-50 hover:bg-slate-200 text-slate-600 transition-colors">+</button>
                      </div>
                      <span className="text-xs font-bold text-slate-900">
                        Bs. {(item.cantidad * item.precio_unitario).toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="p-4 border-t border-slate-200 bg-slate-50">
            <div className="flex justify-between items-center mb-4">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Total Estimado</span>
              <span className="text-lg font-bold text-slate-900">
                Bs. {totalCarrito.toFixed(2)}
              </span>
            </div>
            <div className="mb-4 rounded-md border border-emerald-100 bg-emerald-50 p-3">
              <p className="text-[10px] font-bold text-emerald-800 uppercase tracking-widest">Fidelización CRM</p>
              <p className="text-[10px] text-emerald-700 mt-1 font-medium">El backend validará tu historial y aplicará el descuento automáticamente al confirmar.</p>
            </div>
            <button 
              onClick={confirmarPedido}
              disabled={carrito.length === 0 || enviando}
              className="w-full py-3 bg-[#1A5729] hover:bg-[#12421d] text-white rounded-md font-bold text-[10px] uppercase tracking-widest transition-colors disabled:bg-slate-300 disabled:text-slate-500 flex items-center justify-center gap-2"
            >
              {enviando ? (
                <><div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div> PROCESANDO...</>
              ) : (
                'GENERAR PEDIDO'
              )}
            </button>
          </div>
        </div>
      </div>

      {/* BOTÓN FLOTANTE MÓVIL */}
      {carrito.length > 0 && (
        <button 
          onClick={irAlCarrito}
          className="lg:hidden fixed bottom-6 left-1/2 -translate-x-1/2 z-40 bg-[#1A5729] text-white px-6 py-3 rounded-md font-bold text-[10px] uppercase tracking-widest shadow-lg flex items-center gap-2 border border-[#12421d]"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
          Revisar Orden ({cantidadItemsCarrito})
        </button>
      )}

      {/* MODAL DE ÉXITO CORPORATIVO */}
      {pedidoExitoso && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white border border-slate-200 shadow-xl w-full max-w-sm rounded-md p-6">
            <div className="flex items-center gap-3 border-b border-slate-200 pb-3 mb-4">
              <svg className="w-6 h-6 text-[#1A5729]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              <h2 className="text-sm font-bold text-slate-800 uppercase tracking-widest">Transacción Registrada</h2>
            </div>
            
            <p className="text-slate-600 text-xs mb-5 leading-relaxed">
              La orden de compra ha sido generada en el sistema. Queda en estado pendiente hasta su confirmación o pago.
            </p>
            
            <div className="bg-slate-50 border border-slate-200 p-3 mb-6 rounded-sm text-xs">
              <div className="flex justify-between mb-2">
                <span className="font-bold text-slate-500">Nro. Transacción</span>
                <span className="font-bold text-slate-800">ORD-{String(pedidoExitoso.transaccion).padStart(5, '0')}</span>
              </div>
              <div className="flex justify-between mb-2">
                <span className="font-bold text-slate-500">Subtotal</span>
                <span className="font-bold text-slate-800">Bs. {Number(pedidoExitoso.subtotal || pedidoExitoso.total).toFixed(2)}</span>
              </div>
              {Number(pedidoExitoso.descuento || 0) > 0 && (
                <>
                  <div className="flex justify-between mb-2 text-emerald-700">
                    <span className="font-bold">Nivel CRM</span>
                    <span className="font-bold">{pedidoExitoso.nivel} ({Number(pedidoExitoso.porcentaje).toFixed(0)}%)</span>
                  </div>
                  <div className="flex justify-between mb-2 text-emerald-700">
                    <span className="font-bold">Descuento</span>
                    <span className="font-bold">- Bs. {Number(pedidoExitoso.descuento).toFixed(2)}</span>
                  </div>
                </>
              )}
              <div className="flex justify-between">
                <span className="font-bold text-slate-500">Monto Total</span>
                <span className="font-bold text-slate-800">Bs. {Number(pedidoExitoso.total).toFixed(2)}</span>
              </div>
            </div>

            <button 
              onClick={() => setPedidoExitoso(null)}
              className="w-full border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 py-2.5 rounded-md font-bold text-[10px] uppercase tracking-widest transition-colors"
            >
              Cerrar y Continuar
            </button>
          </div>
        </div>
      )}

    </div>
  );
}
