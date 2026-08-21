import { useState, useEffect } from 'react';
import { useAuthStore } from '../store/auth_store';
import { 
  PieChart, Pie, Cell, 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer 
} from 'recharts';

export default function ReportesBi() {
  const API_URL = import.meta.env.VITE_API_URL;
  const token = useAuthStore((state) => state.token);
  const userEmpresaId = useAuthStore((state) => state.user?.id_empresa || 1);
  
  // Estado para controlar la empresa (0 significa TODAS)
  const [idEmpresa, setIdEmpresa] = useState(0); // Iniciamos en 0 para mostrar la vista global por defecto
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Lista estática o dinámica de empresas autorizadas
  const EMPRESAS_SISTEMA = [
    { id: 1, nombre: 'Corporación Agrícola Norte' },
    { id: 2, nombre: 'Finca El Trompillo B2B' },
    { id: 3, nombre: 'AgroEmpresa Oriental S.A.' }
  ];

  const COLORS_PIE = ['#f59e0b', '#3b82f6', '#1A5729']; 
  const COLORS_BAR = ['#1A5729', '#64748b', '#ef4444']; 

  const cargarDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      // El frontend envía el parámetro; tu backend actual decide cómo procesarlo
      const res = await fetch(`${API_URL}/bi/dashboard?id_empresa=${idEmpresa}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const result = await res.json();
      
      if (result.success) {
        setData(result.data);
      } else {
        setError(result.message);
      }
    } catch (err) {
      console.error(err);
      setError("Error de conexión al obtener las métricas.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargarDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idEmpresa]);

  const formatDinero = (monto) => {
    return new Intl.NumberFormat('es-BO', { style: 'currency', currency: 'BOB' }).format(monto);
  };

  const dataOrdenes = data ? [
    { name: 'Pendientes', value: data.ordenes?.['PENDIENTE'] || 0 },
    { name: 'En Proceso', value: data.ordenes?.['EN PROCESO'] || 0 },
    { name: 'Finalizadas', value: data.ordenes?.['FINALIZADA'] || 0 }
  ] : [];

  const dataMaquinaria = data ? [
    { name: 'Disponible', cantidad: data.maquinaria?.['DISPONIBLE'] || 0 },
    { name: 'En Mantenimiento', cantidad: data.maquinaria?.['EN MANTENIMIENTO'] || 0 },
    { name: 'Ocupado', cantidad: data.maquinaria?.['OCUPADO'] || 0 }
  ] : [];

  if (loading) {
    return (
      <div className="p-8 min-h-screen bg-slate-50 flex flex-col items-center justify-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#1A5729] mb-4"></div>
        <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Generando Inteligencia de Negocios...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="bg-white p-6 rounded-md border border-red-200 text-center shadow-sm max-w-sm">
          <svg className="w-10 h-10 text-red-500 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-widest mb-1">Acceso Denegado / Error</h3>
          <p className="text-xs text-slate-500 mb-4">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 lg:p-8 animate-in fade-in duration-500 bg-slate-50 min-h-screen">
      
      {/* HEADER CORPORATIVO CON SELECTOR DE EMPRESA */}
      <div className="mb-6 flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-white p-5 border border-slate-200 shadow-sm rounded-md">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-3">
            <div className="w-1.5 h-6 bg-[#1A5729]"></div>
            DASHBOARD DIRECTIVO
          </h1>
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1 ml-4">
            Métricas de Inteligencia para Unidades de Negocio
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-3 w-full lg:w-auto">
          {/* ========================================================= */}
          {/* SELECTOR DINÁMICO DE EMPRESA (INCLUYE OPCIÓN "TODAS")       */}
          {/* ========================================================= */}
          <select
            value={idEmpresa}
            onChange={(e) => setIdEmpresa(Number(e.target.value))}
            className="px-3 py-2 border border-slate-300 rounded-md text-xs font-bold uppercase tracking-wider text-slate-800 bg-slate-50 outline-none focus:border-[#1A5729] focus:bg-white cursor-pointer min-w-[220px] transition-colors"
          >
            <option value={0} className="font-black text-[#1A5729]">-- TODAS LAS EMPRESAS (GLOBAL) --</option>
            {EMPRESAS_SISTEMA.map((emp) => (
              <option key={emp.id} value={emp.id}>
                {emp.nombre}
              </option>
            ))}
          </select>

          <button 
            onClick={cargarDashboard}
            className="flex items-center justify-center gap-2 text-[10px] font-bold uppercase tracking-widest text-slate-600 bg-white hover:bg-slate-100 border border-slate-300 px-4 py-2.5 rounded-md transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
            Sincronizar
          </button>
        </div>
      </div>

      {/* FILA 1: TARJETAS DE KPIs PRINCIPALES */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        
        {/* KPI: Finanzas */}
        <div className="bg-white p-5 rounded-md border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Ingresos Totales</h3>
            <div className="bg-emerald-50 p-1.5 rounded text-emerald-600">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            </div>
          </div>
          <p className="text-2xl font-black text-slate-800">{formatDinero(data?.finanzas?.ingresos_totales || 0)}</p>
          <p className="text-[10px] text-slate-400 font-medium mt-1">Basado en {data?.finanzas?.total_ventas || 0} transacciones</p>
        </div>

        {/* KPI: Valoración de Inventario */}
        <div className="bg-white p-5 rounded-md border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Capital en Inventario</h3>
            <div className="bg-blue-50 p-1.5 rounded text-blue-600">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>
            </div>
          </div>
          <p className="text-2xl font-black text-slate-800">{formatDinero(data?.inventario?.valoracion_total || 0)}</p>
          <p className="text-[10px] text-slate-400 font-medium mt-1">Valor de bodega actual</p>
        </div>

        {/* KPI: Hectáreas Activas */}
        <div className="bg-white p-5 rounded-md border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Uso de Suelo</h3>
            <div className="bg-[#1A5729]/10 p-1.5 rounded text-[#1A5729]">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <p className="text-2xl font-black text-slate-800">{data?.agricultura?.hectareas_activas || 0}</p>
            <p className="text-xs font-bold text-slate-500 pb-1">/ {data?.agricultura?.hectareas_totales || 0} ha</p>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full mt-2 overflow-hidden">
            <div 
              className="bg-[#1A5729] h-full transition-all duration-1000" 
              style={{ width: `${data?.agricultura?.hectareas_totales > 0 ? (data.agricultura.hectareas_activas / data.agricultura.hectareas_totales) * 100 : 0}%` }}
            ></div>
          </div>
        </div>

        {/* KPI: Alertas de Stock */}
        <div className={`p-5 rounded-md border shadow-sm ${data?.inventario?.alertas_stock_minimo > 0 ? 'bg-red-50 border-red-200' : 'bg-white border-slate-200'}`}>
          <div className="flex justify-between items-start mb-2">
            <h3 className={`text-[10px] font-bold uppercase tracking-widest ${data?.inventario?.alertas_stock_minimo > 0 ? 'text-red-700' : 'text-slate-500'}`}>Alertas de Stock</h3>
            <div className={`${data?.inventario?.alertas_stock_minimo > 0 ? 'bg-red-100 text-red-600' : 'bg-slate-100 text-slate-400'} p-1.5 rounded`}>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
            </div>
          </div>
          <p className={`text-2xl font-black ${data?.inventario?.alertas_stock_minimo > 0 ? 'text-red-700' : 'text-slate-800'}`}>
            {data?.inventario?.alertas_stock_minimo || 0}
          </p>
          <p className={`text-[10px] font-medium mt-1 ${data?.inventario?.alertas_stock_minimo > 0 ? 'text-red-500' : 'text-slate-400'}`}>Productos por debajo del mínimo</p>
        </div>

      </div>

      {/* FILA 2: GRÁFICOS ANALÍTICOS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        
        {/* GRÁFICO 1: Eficiencia Operativa */}
        <div className="bg-white p-5 rounded-md border border-slate-200 shadow-sm flex flex-col h-96">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-widest mb-4 border-b border-slate-100 pb-2">Estado de Órdenes de Trabajo</h3>
          <div className="flex-1 w-full h-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={dataOrdenes}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {dataOrdenes.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS_PIE[index % COLORS_PIE.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ borderRadius: '6px', border: '1px solid #e2e8f0', fontSize: '12px', fontWeight: 'bold' }}
                  itemStyle={{ color: '#1e293b' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          <div className="flex justify-center flex-wrap gap-4 mt-2">
            {dataOrdenes.map((entry, index) => (
              <div key={`legend-${index}`} className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: COLORS_PIE[index] }}></span>
                <span className="text-[10px] font-bold text-slate-500 uppercase">{entry.name} ({entry.value})</span>
              </div>
            ))}
          </div>
        </div>

        {/* GRÁFICO 2: Disponibilidad de Flota */}
        <div className="bg-white p-5 rounded-md border border-slate-200 shadow-sm flex flex-col h-96">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-widest mb-4 border-b border-slate-100 pb-2">Disponibilidad de Flota (Maquinaria)</h3>
          <div className="flex-1 w-full h-full mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dataMaquinaria} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis 
                  dataKey="name" 
                  tick={{ fontSize: 10, fill: '#64748b', fontWeight: 'bold' }} 
                  axisLine={false} 
                  tickLine={false} 
                />
                <YAxis 
                  tick={{ fontSize: 10, fill: '#64748b' }} 
                  axisLine={false} 
                  tickLine={false} 
                  allowDecimals={false}
                />
                <Tooltip 
                  cursor={{ fill: '#f8fafc' }}
                  contentStyle={{ borderRadius: '6px', border: '1px solid #e2e8f0', fontSize: '12px', fontWeight: 'bold' }}
                />
                <Bar dataKey="cantidad" radius={[4, 4, 0, 0]}>
                  {dataMaquinaria.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS_BAR[index % COLORS_BAR.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}