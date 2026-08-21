import { useEffect, useState } from 'react';
import { useAuthStore } from '../store/auth_store';

const API_URL = import.meta.env.VITE_API_URL;

const initialForm = {
  id_nivel: null,
  id_regla: null,
  nombre_nivel: '',
  descripcion: '',
  min_transacciones: 0,
  min_monto_acumulado: 0,
  prioridad: 1,
  estado: 'ACTIVO',
  tipo_transaccion: 'PEDIDO_INSUMO',
  porcentaje_descuento: 0,
  monto_max_descuento: '',
  vigencia_desde: '',
  vigencia_hasta: ''
};

export default function CrmFidelizacion() {
  const token = useAuthStore((state) => state.token);
  const { id_empresa } = useAuthStore((state) => state.user || { id_empresa: null });
  const empresaValida = id_empresa && id_empresa !== 'null';

  const [niveles, setNiveles] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('niveles');
  const [showModal, setShowModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(initialForm);

  const cargarDatos = async () => {
    if (!empresaValida) { setLoading(false); return; }
    setLoading(true);
    try {
      const [nivRes, cliRes] = await Promise.all([
        fetch(`${API_URL}/fidelizacion/niveles?id_empresa=${id_empresa}`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/fidelizacion/clientes?id_empresa=${id_empresa}`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      const nivData = await nivRes.json();
      const cliData = await cliRes.json();
      if (nivData.success) setNiveles(nivData.niveles || []);
      if (cliData.success) setClientes(cliData.clientes || []);
    } catch (err) {
      console.error('Error al cargar fidelización', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { cargarDatos(); }, []);

  const abrirNuevo = () => {
    setForm(initialForm);
    setShowModal(true);
  };

  const abrirEditar = (nivel) => {
    setForm({ ...initialForm, ...nivel, monto_max_descuento: nivel.monto_max_descuento ?? '' });
    setShowModal(true);
  };

  const guardarNivel = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const isEdit = Boolean(form.id_nivel);
      const url = isEdit ? `${API_URL}/fidelizacion/niveles/${form.id_nivel}` : `${API_URL}/fidelizacion/niveles`;
      const res = await fetch(url, {
        method: isEdit ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ ...form, id_empresa })
      });
      const data = await res.json();
      if (!data.success) { alert(data.message || 'No se pudo guardar'); return; }
      setShowModal(false);
      cargarDatos();
    } catch (err) {
      alert('Error de conexión');
    } finally {
      setSaving(false);
    }
  };

  const desactivarNivel = async (idNivel) => {
    if (!window.confirm('¿Desactivar este nivel de fidelización?')) return;
    try {
      const res = await fetch(`${API_URL}/fidelizacion/niveles/${idNivel}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (!data.success) { alert(data.message || 'No se pudo desactivar'); return; }
      cargarDatos();
    } catch (err) {
      alert('Error de conexión');
    }
  };

  const colorNivel = (nombre) => {
    const key = String(nombre || '').toUpperCase();
    if (key.includes('VIP')) return 'from-purple-600 to-fuchsia-500';
    if (key.includes('ORO')) return 'from-amber-500 to-yellow-400';
    if (key.includes('PLATA')) return 'from-slate-500 to-slate-300';
    return 'from-[#1A5729] to-[#7BC636]';
  };

  if (!empresaValida) {
    return <div className="p-8 bg-white rounded-2xl border border-red-100 text-red-700 font-bold">No tienes empresa asignada. Contacta al administrador.</div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <p className="text-[10px] font-black text-[#5B9D1E] uppercase tracking-[0.22em]">CRM y Clientes</p>
            <h1 className="text-2xl md:text-3xl font-black text-slate-900 tracking-tight">Programa de Fidelización</h1>
            <p className="text-xs text-slate-500 font-semibold mt-1">Parametriza niveles, reglas y beneficios automáticos por historial comercial.</p>
          </div>
          <button onClick={abrirNuevo} className="px-5 py-3 bg-[#1A5729] text-white rounded-xl font-black text-xs uppercase tracking-widest hover:bg-[#144320] transition">+ Nuevo Nivel</button>
        </div>
      </div>

      <div className="flex gap-2">
        {['niveles', 'clientes'].map((item) => (
          <button key={item} onClick={() => setTab(item)} className={`px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition ${tab === item ? 'bg-[#1A5729] text-white' : 'bg-white border border-slate-200 text-slate-500 hover:text-slate-900'}`}>
            {item === 'niveles' ? 'Niveles y Reglas' : 'Clientes Elegibles'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-200"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1A5729] mx-auto"></div></div>
      ) : tab === 'niveles' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {niveles.map((nivel) => (
            <div key={nivel.id_nivel} className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              <div className={`h-24 bg-gradient-to-br ${colorNivel(nivel.nombre_nivel)} p-4 text-white flex flex-col justify-between`}>
                <span className="text-[10px] font-black uppercase tracking-widest opacity-80">Prioridad {nivel.prioridad}</span>
                <h3 className="text-xl font-black uppercase tracking-wide">{nivel.nombre_nivel}</h3>
              </div>
              <div className="p-4 space-y-3">
                <p className="text-xs text-slate-500 min-h-8">{nivel.descripcion || 'Sin descripción registrada.'}</p>
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-slate-50 rounded-xl p-3"><p className="text-[9px] font-black text-slate-400 uppercase">Compras min.</p><p className="font-black text-slate-800">{nivel.min_transacciones}</p></div>
                  <div className="bg-slate-50 rounded-xl p-3"><p className="text-[9px] font-black text-slate-400 uppercase">Monto min.</p><p className="font-black text-slate-800">Bs. {Number(nivel.min_monto_acumulado).toFixed(0)}</p></div>
                </div>
                <div className="flex items-center justify-between bg-emerald-50 border border-emerald-100 rounded-xl p-3">
                  <span className="text-[10px] font-black text-emerald-700 uppercase tracking-widest">Descuento</span>
                  <span className="text-lg font-black text-emerald-800">{Number(nivel.porcentaje_descuento).toFixed(0)}%</span>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => abrirEditar(nivel)} className="flex-1 py-2 border border-slate-200 rounded-xl text-xs font-black text-slate-600 hover:bg-slate-50">Editar</button>
                  <button onClick={() => desactivarNivel(nivel.id_nivel)} className="flex-1 py-2 border border-red-100 rounded-xl text-xs font-black text-red-600 hover:bg-red-50">Desactivar</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-black text-slate-500 uppercase">Cliente</th>
                  <th className="text-left px-4 py-3 text-xs font-black text-slate-500 uppercase">Compras</th>
                  <th className="text-left px-4 py-3 text-xs font-black text-slate-500 uppercase">Monto</th>
                  <th className="text-left px-4 py-3 text-xs font-black text-slate-500 uppercase">Nivel</th>
                  <th className="text-left px-4 py-3 text-xs font-black text-slate-500 uppercase">Beneficio</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {clientes.map((c) => (
                  <tr key={c.id_usuario} className="hover:bg-slate-50">
                    <td className="px-4 py-3"><p className="font-bold text-slate-800">{c.nombre_razon_social}</p><p className="text-xs text-slate-400">{c.correo}</p></td>
                    <td className="px-4 py-3 font-bold text-slate-700">{c.total_transacciones}</td>
                    <td className="px-4 py-3 font-bold text-slate-700">Bs. {Number(c.monto_acumulado).toFixed(2)}</td>
                    <td className="px-4 py-3"><span className="px-3 py-1 rounded-full bg-[#1A5729]/10 text-[#1A5729] text-xs font-black">{c.nivel_fidelizacion}</span></td>
                    <td className="px-4 py-3 font-black text-emerald-700">{Number(c.porcentaje_descuento).toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <form onSubmit={guardarNivel} className="bg-white rounded-2xl shadow-xl w-full max-w-2xl p-6 space-y-4">
            <h2 className="text-xl font-black text-[#1A5729] uppercase tracking-widest">{form.id_nivel ? 'Editar Nivel' : 'Nuevo Nivel'}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <input className="border border-slate-300 rounded-xl px-3 py-2 text-sm" placeholder="Nombre del nivel" value={form.nombre_nivel} onChange={(e) => setForm({ ...form, nombre_nivel: e.target.value })} required />
              <input className="border border-slate-300 rounded-xl px-3 py-2 text-sm" placeholder="Descripción" value={form.descripcion || ''} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} />
              <input type="number" className="border border-slate-300 rounded-xl px-3 py-2 text-sm" placeholder="Mínimo transacciones" value={form.min_transacciones} onChange={(e) => setForm({ ...form, min_transacciones: e.target.value })} required />
              <input type="number" step="0.01" className="border border-slate-300 rounded-xl px-3 py-2 text-sm" placeholder="Mínimo monto acumulado" value={form.min_monto_acumulado} onChange={(e) => setForm({ ...form, min_monto_acumulado: e.target.value })} required />
              <input type="number" className="border border-slate-300 rounded-xl px-3 py-2 text-sm" placeholder="Prioridad" value={form.prioridad} onChange={(e) => setForm({ ...form, prioridad: e.target.value })} required />
              <input type="number" step="0.01" className="border border-slate-300 rounded-xl px-3 py-2 text-sm" placeholder="% Descuento" value={form.porcentaje_descuento} onChange={(e) => setForm({ ...form, porcentaje_descuento: e.target.value })} required />
              <input type="number" step="0.01" className="border border-slate-300 rounded-xl px-3 py-2 text-sm" placeholder="Monto máximo descuento" value={form.monto_max_descuento || ''} onChange={(e) => setForm({ ...form, monto_max_descuento: e.target.value })} />
              <select className="border border-slate-300 rounded-xl px-3 py-2 text-sm" value={form.estado} onChange={(e) => setForm({ ...form, estado: e.target.value })}>
                <option value="ACTIVO">ACTIVO</option>
                <option value="INACTIVO">INACTIVO</option>
              </select>
            </div>
            <div className="flex gap-3 pt-2">
              <button type="button" onClick={() => setShowModal(false)} className="flex-1 py-3 border border-slate-300 rounded-xl font-black text-slate-600">Cancelar</button>
              <button type="submit" disabled={saving} className="flex-1 py-3 bg-[#1A5729] text-white rounded-xl font-black disabled:opacity-50">{saving ? 'Guardando...' : 'Guardar'}</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
