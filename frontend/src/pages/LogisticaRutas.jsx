import { useState, useEffect } from 'react';
import { useAuthStore } from '../store/auth_store';

const API_URL = import.meta.env.VITE_API_URL;

export default function LogisticaRutas() {
  const token = useAuthStore((state) => state.token);
  const { id_empresa: idEmpresa } = useAuthStore((state) => state.user || { id_empresa: null });
  const empresaValida = idEmpresa && idEmpresa !== 'null';

  const [rutas, setRutas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtroEstado, setFiltroEstado] = useState('');

  const [showModal, setShowModal] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [pedidosPendientes, setPedidosPendientes] = useState([]);
  const [choferes, setChoferes] = useState([]);
  const [formData, setFormData] = useState({
    id_transaccion: '',
    id_chofer: '',
    origen: '',
    destino: '',
    fecha_entrega_estimada: ''
  });

  const [detalleRuta, setDetalleRuta] = useState(null);
  const [showDetalle, setShowDetalle] = useState(false);

  const fetchRutas = async (estado = '') => {
    if (!empresaValida) return;
    setLoading(true);
    try {
      const params = new URLSearchParams({ id_empresa: idEmpresa });
      if (estado) params.append('estado', estado);
      const url = `${API_URL}/logistica/rutas?${params}`;
      const res = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } });
      const data = await res.json();
      if (data.success) setRutas(data.rutas || []);
    } catch (err) {
      console.error('Error al cargar rutas:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRutas(filtroEstado); }, [filtroEstado]);

  const abrirModalCrear = async () => {
    if (!empresaValida) { alert('No tienes empresa asignada. Contacta al administrador.'); return; }
    setFormData({ id_transaccion: '', id_chofer: '', origen: '', destino: '', fecha_entrega_estimada: '' });
    setShowModal(true);
    try {
      const [pedRes, chofRes] = await Promise.all([
        fetch(`${API_URL}/logistica/pedidos-pendientes?id_empresa=${idEmpresa}`, { headers: { 'Authorization': `Bearer ${token}` } }),
        fetch(`${API_URL}/logistica/choferes?id_empresa=${idEmpresa}`, { headers: { 'Authorization': `Bearer ${token}` } })
      ]);
      const pedData = await pedRes.json();
      const chofData = await chofRes.json();
      if (pedData.success) setPedidosPendientes(pedData.pedidos || []);
      if (chofData.success) setChoferes(chofData.choferes || []);
    } catch (err) {
      console.error('Error cargando datos para crear ruta:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.id_transaccion || !formData.id_chofer || !formData.origen || !formData.destino || !formData.fecha_entrega_estimada) {
      alert('Completa todos los campos obligatorios.');
      return;
    }
    setEnviando(true);
    try {
      const res = await fetch(`${API_URL}/logistica/rutas`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ ...formData, id_empresa: idEmpresa })
      });
      const data = await res.json();
      if (data.success) {
        setShowModal(false);
        fetchRutas(filtroEstado);
      } else {
        alert(data.message || 'Error al crear la ruta');
      }
    } catch (err) {
      alert('Error de conexión');
    } finally {
      setEnviando(false);
    }
  };

  const verDetalle = async (idRuta) => {
    try {
      const res = await fetch(`${API_URL}/logistica/rutas/${idRuta}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.success) {
        setDetalleRuta(data.ruta);
        setShowDetalle(true);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const cancelarRuta = async (idRuta) => {
    if (!window.confirm('¿Estás seguro de cancelar esta ruta?')) return;
    try {
      const res = await fetch(`${API_URL}/logistica/rutas/${idRuta}/cancelar`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.success) {
        fetchRutas(filtroEstado);
      } else {
        alert(data.message || 'Error al cancelar ruta');
      }
    } catch (err) {
      alert('Error de conexión');
    }
  };

  const badgeEstado = (estado) => {
    const map = {
      'ASIGNADA': 'bg-blue-100 text-blue-800',
      'ENTREGADA': 'bg-emerald-100 text-emerald-800',
      'CANCELADA': 'bg-red-100 text-red-800'
    };
    return `px-3 py-1 rounded-full text-xs font-bold ${map[estado] || 'bg-gray-100 text-gray-800'}`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-black text-[#1A5729] uppercase tracking-widest">
          Gestión de Rutas Logísticas
        </h1>
        <button onClick={abrirModalCrear}
          className="px-5 py-2.5 bg-[#1A5729] text-white font-bold rounded-xl hover:bg-[#144320] transition shadow-md text-sm">
          + Nueva Ruta
        </button>
      </div>

      <div className="flex gap-2">
        {['', 'ASIGNADA', 'ENTREGADA', 'CANCELADA'].map((est) => (
          <button key={est}
            onClick={() => setFiltroEstado(est)}
            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition ${
              filtroEstado === est
                ? 'bg-[#1A5729] text-white'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}>
            {est || 'TODAS'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1A5729] mx-auto"></div>
        </div>
      ) : rutas.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-2xl border border-gray-200">
          <p className="text-gray-400 font-bold text-sm">No hay rutas registradas</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-3 font-bold text-gray-600 text-xs uppercase">#</th>
                  <th className="text-left px-4 py-3 font-bold text-gray-600 text-xs uppercase">Pedido</th>
                  <th className="text-left px-4 py-3 font-bold text-gray-600 text-xs uppercase">Chofer</th>
                  <th className="text-left px-4 py-3 font-bold text-gray-600 text-xs uppercase">Cliente</th>
                  <th className="text-left px-4 py-3 font-bold text-gray-600 text-xs uppercase">Destino</th>
                  <th className="text-left px-4 py-3 font-bold text-gray-600 text-xs uppercase">Fecha Est.</th>
                  <th className="text-left px-4 py-3 font-bold text-gray-600 text-xs uppercase">Estado</th>
                  <th className="text-left px-4 py-3 font-bold text-gray-600 text-xs uppercase">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {rutas.map((r) => (
                  <tr key={r.id_ruta} className="hover:bg-gray-50/50">
                    <td className="px-4 py-3 font-bold text-gray-800">#{r.id_ruta}</td>
                    <td className="px-4 py-3">ORD-{String(r.nro_transaccion).padStart(5, '0')}</td>
                    <td className="px-4 py-3 font-medium text-gray-700">{r.chofer_nombre || r.chofer_usuario}</td>
                    <td className="px-4 py-3 text-gray-600">{r.cliente_nombre}</td>
                    <td className="px-4 py-3 text-gray-600">{r.destino}</td>
                    <td className="px-4 py-3 text-gray-600">{r.fecha_entrega_estimada}</td>
                    <td className="px-4 py-3"><span className={badgeEstado(r.estado)}>{r.estado}</span></td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button onClick={() => verDetalle(r.id_ruta)}
                          className="text-xs font-bold text-[#5B9D1E] hover:text-[#1A5729] transition">
                          Ver
                        </button>
                        {r.estado === 'ASIGNADA' && (
                          <button onClick={() => cancelarRuta(r.id_ruta)}
                            className="text-xs font-bold text-red-500 hover:text-red-700 transition">
                            Cancelar
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-lg font-black text-[#1A5729] uppercase tracking-widest mb-6">Nueva Ruta Logística</h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-gray-600 mb-1">Pedido *</label>
                  <select
                    value={formData.id_transaccion}
                    onChange={(e) => {
                      const pedido = pedidosPendientes.find(p => p.nro_transaccion === Number(e.target.value));
                      setFormData({
                        ...formData,
                        id_transaccion: e.target.value,
                        destino: pedido?.direccion || formData.destino,
                        origen: pedido?.direccion ? formData.origen : formData.origen
                      });
                    }}
                    className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm font-medium focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent"
                    required>
                    <option value="">Seleccionar pedido...</option>
                    {pedidosPendientes.map((p) => (
                      <option key={p.nro_transaccion} value={p.nro_transaccion}>
                        ORD-{String(p.nro_transaccion).padStart(5, '0')} - {p.cliente} - Bs.{p.monto_total}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-600 mb-1">Chofer/Repartidor *</label>
                  <select
                    value={formData.id_chofer}
                    onChange={(e) => setFormData({ ...formData, id_chofer: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm font-medium focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent"
                    required>
                    <option value="">Seleccionar chofer...</option>
                    {choferes.map((c) => (
                      <option key={c.id_usuario} value={c.id_usuario}>
                        {c.nombre_razon_social} ({c.user_name})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-gray-600 mb-1">Origen *</label>
                    <input type="text" value={formData.origen}
                      onChange={(e) => setFormData({ ...formData, origen: e.target.value })}
                      className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm font-medium focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent"
                      placeholder="Ej: Almacén Central" required />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-600 mb-1">Destino *</label>
                    <input type="text" value={formData.destino}
                      onChange={(e) => setFormData({ ...formData, destino: e.target.value })}
                      className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm font-medium focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent"
                      placeholder="Dirección del cliente" required />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-600 mb-1">Fecha estimada de entrega *</label>
                  <input type="date" value={formData.fecha_entrega_estimada}
                    onChange={(e) => setFormData({ ...formData, fecha_entrega_estimada: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm font-medium focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent"
                    required />
                </div>
                <div className="flex gap-3 pt-2">
                  <button type="button" onClick={() => setShowModal(false)}
                    className="flex-1 px-4 py-2.5 border border-gray-300 text-gray-600 font-bold rounded-xl hover:bg-gray-50 transition text-sm">
                    Cancelar
                  </button>
                  <button type="submit" disabled={enviando}
                    className="flex-1 px-4 py-2.5 bg-[#1A5729] text-white font-bold rounded-xl hover:bg-[#144320] transition text-sm disabled:opacity-50">
                    {enviando ? 'Guardando...' : 'Guardar Ruta'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {showDetalle && detalleRuta && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-lg font-black text-[#1A5729] uppercase tracking-widest mb-4">
                Ruta #{detalleRuta.id_ruta}
              </h2>
              <div className="space-y-3 text-sm">
                <div className="grid grid-cols-2 gap-3">
                  <div><span className="font-bold text-gray-500 text-xs uppercase">Pedido:</span>
                    <p className="font-medium">ORD-{String(detalleRuta.nro_transaccion).padStart(5, '0')}</p></div>
                  <div><span className="font-bold text-gray-500 text-xs uppercase">Monto:</span>
                    <p className="font-medium text-[#1A5729]">Bs.{detalleRuta.monto_total}</p></div>
                </div>
                <div className="border-t pt-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div><span className="font-bold text-gray-500 text-xs uppercase">Chofer:</span>
                      <p className="font-medium">{detalleRuta.chofer_nombre}</p></div>
                    <div><span className="font-bold text-gray-500 text-xs uppercase">Cliente:</span>
                      <p className="font-medium">{detalleRuta.cliente_nombre}</p></div>
                  </div>
                </div>
                <div className="border-t pt-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div><span className="font-bold text-gray-500 text-xs uppercase">Origen:</span>
                      <p className="font-medium">{detalleRuta.origen}</p></div>
                    <div><span className="font-bold text-gray-500 text-xs uppercase">Destino:</span>
                      <p className="font-medium">{detalleRuta.destino}</p></div>
                  </div>
                </div>
                <div className="border-t pt-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div><span className="font-bold text-gray-500 text-xs uppercase">Estado:</span>
                      <p><span className={badgeEstado(detalleRuta.estado)}>{detalleRuta.estado}</span></p></div>
                    <div><span className="font-bold text-gray-500 text-xs uppercase">Fecha Est.:</span>
                      <p className="font-medium">{detalleRuta.fecha_entrega_estimada}</p></div>
                  </div>
                  {detalleRuta.fecha_entrega_real && (
                    <div className="mt-2">
                      <span className="font-bold text-gray-500 text-xs uppercase">Entregado el:</span>
                      <p className="font-medium">{detalleRuta.fecha_entrega_real}</p>
                    </div>
                  )}
                </div>
                {detalleRuta.observaciones && (
                  <div className="border-t pt-3">
                    <span className="font-bold text-gray-500 text-xs uppercase">Observaciones:</span>
                    <p className="text-gray-700 mt-1">{detalleRuta.observaciones}</p>
                  </div>
                )}
                <div className="flex gap-3 pt-4">
                  {detalleRuta.url_evidencia_imagen && (
                    <a href={detalleRuta.url_evidencia_imagen} target="_blank" rel="noopener noreferrer"
                      className="text-xs font-bold text-[#5B9D1E] hover:text-[#1A5729] underline">
                      Ver evidencia imagen
                    </a>
                  )}
                  {detalleRuta.url_evidencia_audio && (
                    <a href={detalleRuta.url_evidencia_audio} target="_blank" rel="noopener noreferrer"
                      className="text-xs font-bold text-[#5B9D1E] hover:text-[#1A5729] underline">
                      Escuchar audio
                    </a>
                  )}
                </div>
              </div>
              <div className="mt-6">
                <button onClick={() => setShowDetalle(false)}
                  className="w-full px-4 py-2.5 bg-gray-100 text-gray-700 font-bold rounded-xl hover:bg-gray-200 transition text-sm">
                  Cerrar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
