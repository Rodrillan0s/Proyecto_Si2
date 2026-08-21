import { useState, useEffect, useRef } from 'react';
import { useAuthStore } from '../store/auth_store';

// Función infalible para leer llaves de la BD ignorando mayúsculas/minúsculas
const getVal = (obj, keyName) => {
  if (!obj) return '';
  const exactKey = Object.keys(obj).find(k => k.toLowerCase() === keyName.toLowerCase());
  return exactKey ? obj[exactKey] : '';
};

// Helper para formatear fecha a YYYY-MM-DD
const formatDateForInput = (dateString) => {
  if (!dateString) return '';
  try {
    const d = new Date(dateString);
    return d.toISOString().split('T')[0];
  } catch (e) {
    return dateString;
  }
};

export default function AgroCampanias() {
  const API_URL = import.meta.env.VITE_API_URL;
  const token = useAuthStore((state) => state.token);
  const logout = useAuthStore((state) => state.logout); 
  
  const [campanias, setCampanias] = useState([]);
  const [terrenos, setTerrenos] = useState([]); 
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const [iaLoading, setIaLoading] = useState(false);
  const [iaResultado, setIaResultado] = useState(null);
  const [iaError, setIaError] = useState('');
  const [rendimientoConfirmado, setRendimientoConfirmado] = useState(false);
  
  const [formData, setFormData] = useState({
    id_campana: '',
    nombre_campana: '',
    variedad: '',
    fecha_siembra: '',
    fecha_cosecha: '',
    estado: 'PLANIFICADA',
    rendimiento_estimado: '',
    rendimiento_real: '',
    nro_lote: ''
  });

  // GUARDIA DE SEGURIDAD CONTRA PETICIONES DOBLES (Strict Mode)
  const dataFetchedRef = useRef(false);

  const cargarCampanias = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_URL}/get-campanias`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        }
      });
      
      if (response.status === 401 || response.status === 403) {
        if (response.status === 401) logout();
        window.location.href = '/login';
        return;
      }

      if (!response.ok) {
        throw new Error(`Error de conexión con el servidor (Código: ${response.status})`);
      }
      
      const data = await response.json();
      if (!data.success) throw new Error(data.message || 'Error al obtener campañas');
      
      setCampanias(data.list_campanias || []);
    } catch (err) {
      setError(err.message);
      setCampanias([]); 
    } finally {
      setLoading(false);
    }
  };

  const cargarTerrenos = async () => {
    try {
      const response = await fetch(`${API_URL}/get-terrenos`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setTerrenos(data.list_terrenos || []);
        }
      }
    } catch (err) {
      console.warn("Error al cargar terrenos para el select:", err.message);
      setTerrenos([]); 
    }
  };

  useEffect(() => {
    // Si ya empezamos a pedir datos, ignoramos el segundo disparo de React Strict Mode
    if (dataFetchedRef.current) return;
    dataFetchedRef.current = true;

    const inicializarPantalla = async () => {
      // Se ejecutan de forma perfectamente secuencial
      await cargarTerrenos();
      await cargarCampanias();
    };
    
    inicializarPantalla();
  }, []);

  const handleEliminar = async (id_campana, nombre) => {
    if (!window.confirm(`¿Estás seguro de eliminar la campaña "${nombre}"?`)) return;
    try {
      const response = await fetch(`${API_URL}/delete-campania`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ id_campana: id_campana }) 
      });
      
      if (!response.ok) throw new Error('Error de servidor al eliminar');
      
      const data = await response.json();
      if (!data.success) throw new Error(data.message);
      
      cargarCampanias(); 
    } catch (err) {
      alert(`Error al eliminar: ${err.message}`);
    }
  };

  const resetIaState = () => {
    setIaLoading(false);
    setIaResultado(null);
    setIaError('');
    setRendimientoConfirmado(false);
  };

  const openAddModal = () => {
    setIsEditing(false);
    setFormData({
      id_campana: '', nombre_campana: '', variedad: '',
      fecha_siembra: '', fecha_cosecha: '', estado: 'PLANIFICADA',
      rendimiento_estimado: '', rendimiento_real: '', nro_lote: ''
    });
    resetIaState();
    setShowModal(true);
  };

  const openEditModal = (campania) => {
    setIsEditing(true);
    resetIaState();
    setFormData({
      id_campana: getVal(campania, 'id_campana'),
      nombre_campana: getVal(campania, 'nombre_campana'),
      variedad: getVal(campania, 'variedad'),
      fecha_siembra: formatDateForInput(getVal(campania, 'fecha_siembra')),
      fecha_cosecha: formatDateForInput(getVal(campania, 'fecha_cosecha')),
      estado: getVal(campania, 'estado') || 'PLANIFICADA',
      rendimiento_estimado: getVal(campania, 'rendimiento_estimado'),
      rendimiento_real: getVal(campania, 'rendimiento_real') || '',
      // Mapeo blindado por si el backend manda el ID con otro nombre
      nro_lote: getVal(campania, 'nro_lote') || getVal(campania, 'id_terreno') || getVal(campania, 'id') || ''
    });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const endpoint = isEditing ? '/update-campania' : '/add-campania';
    
    const payload = {
      ...formData,
      rendimiento_estimado: parseFloat(formData.rendimiento_estimado),
      rendimiento_real: formData.rendimiento_real ? parseFloat(formData.rendimiento_real) : null,
      nro_lote: parseInt(formData.nro_lote, 10)
    };

    if (!isEditing) {
      delete payload.id_campana; 
    }

    try {
      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) throw new Error('Error de servidor al guardar');
      
      const data = await response.json();
      if (!data.success) throw new Error(data.message);
      
      setShowModal(false);
      cargarCampanias(); 
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const handleCalcularIA = async () => {
    setIaLoading(true);
    setIaResultado(null);
    setIaError('');
    setRendimientoConfirmado(false);
    try {
      const response = await fetch(`${API_URL}/prediccion/campana/${formData.id_campana}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.message || `Error ${response.status}`);
      }
      setIaResultado({
        rendimiento_estimado: data.rendimiento_estimado,
        justificacion: data.justificacion,
      });
    } catch (err) {
      setIaError(err.message);
    } finally {
      setIaLoading(false);
    }
  };

  const handleUsarValorIA = () => {
    setFormData({ ...formData, rendimiento_estimado: iaResultado.rendimiento_estimado });
    setRendimientoConfirmado(true);
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const campaniasFiltradas = campanias.filter((c) => {
    const termino = searchTerm.toLowerCase();
    const nombre = String(getVal(c, 'nombre_campana')).toLowerCase();
    const sector = String(getVal(c, 'nombre_sector')).toLowerCase();
    const variedad = String(getVal(c, 'variedad')).toLowerCase();
    return nombre.includes(termino) || sector.includes(termino) || variedad.includes(termino);
  });

  return (
    <div className="animate-fade-in relative max-w-full">
      
      {/* Cabecera Responsiva */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-5 gap-4">
        <div className="w-full sm:w-auto">
          <h3 className="text-xl font-bold text-gray-800 dark:text-white tracking-tight">Gestión de Campañas</h3>
          <p className="text-sm text-gray-500 dark:text-slate-400 mt-0.5">Control de ciclos de cultivo, variedades y rendimientos.</p>
        </div>
        <button 
          onClick={openAddModal}
          className="w-full sm:w-auto justify-center bg-[#1A5729] hover:bg-[#144320] dark:bg-cyan-600 dark:hover:bg-cyan-700 text-white text-sm sm:text-xs font-semibold px-4 py-2.5 sm:py-2 rounded-lg shadow-sm transition-colors flex items-center gap-1.5"
        >
          <svg fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-4 h-4"><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>
          Nueva Campaña
        </button>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 text-red-700 dark:text-red-400 p-3 rounded mb-5 text-sm">
          <span className="font-semibold">Aviso:</span> {error}
        </div>
      )}
      
      {/* Contenedor Principal */}
      <div className="bg-white dark:bg-[#1E293B] border border-gray-200 dark:border-slate-700/80 rounded-xl shadow-sm overflow-hidden flex flex-col">
        
        {/* Buscador */}
        <div className="px-4 sm:px-5 py-3 border-b border-gray-200 dark:border-slate-700/80 bg-gray-50/40 dark:bg-slate-800/40 flex items-center">
          <div className="relative w-full sm:w-80">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" /></svg>
            </div>
            <input 
              type="text" 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar por campaña, variedad o lote..." 
              className="w-full pl-9 pr-4 py-2 sm:py-1.5 text-base sm:text-sm border border-gray-300 dark:border-slate-600 rounded-md bg-white dark:bg-[#0F172A] focus:ring-1 focus:ring-[#1A5729] outline-none transition-all dark:text-slate-200 placeholder:text-gray-400"
            />
          </div>
        </div>

        {/* Tabla */}
        <div className="overflow-x-auto custom-scrollbar">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400">
              <svg className="animate-spin h-6 w-6 text-[#1A5729] dark:text-cyan-600 mb-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p className="text-xs font-semibold tracking-wider uppercase">Cargando...</p>
            </div>
          ) : campaniasFiltradas.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p className="text-sm font-medium">No se encontraron campañas.</p>
            </div>
          ) : (
            <table className="w-full text-left border-collapse whitespace-nowrap">
              <thead>
                <tr className="bg-gray-50/80 dark:bg-slate-800/80 border-b border-gray-200 dark:border-slate-700 text-[11px] font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">
                  <th className="px-4 sm:px-5 py-3 w-12 text-center">ID</th>
                  <th className="px-4 sm:px-5 py-3">Campaña</th>
                  <th className="px-4 sm:px-5 py-3">Variedad</th>
                  <th className="px-4 sm:px-5 py-3">Lote (Sector)</th>
                  <th className="px-4 sm:px-5 py-3">Estado</th>
                  <th className="px-4 sm:px-5 py-3">Rend. Est.</th>
                  <th className="px-4 sm:px-5 py-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-slate-700/80 text-sm">
                {campaniasFiltradas.map((c, index) => {
                  const idCampana = getVal(c, 'id_campana');
                  const estado = getVal(c, 'estado') || 'PLANIFICADA';
                  
                  return (
                  <tr key={idCampana || index} className="hover:bg-gray-50/60 dark:hover:bg-slate-800/40 transition-colors group">
                    <td className="px-4 sm:px-5 py-3 sm:py-2.5 text-center text-gray-400 dark:text-slate-500 font-mono text-xs">{idCampana}</td>
                    <td className="px-4 sm:px-5 py-3 sm:py-2.5 font-bold text-gray-800 dark:text-slate-200">{getVal(c, 'nombre_campana')}</td>
                    <td className="px-4 sm:px-5 py-3 sm:py-2.5 text-gray-600 dark:text-slate-300 font-medium">{getVal(c, 'variedad')}</td>
                    <td className="px-4 sm:px-5 py-3 sm:py-2.5 text-gray-500 dark:text-slate-400 font-mono text-[11px]">{getVal(c, 'nombre_sector')}</td>
                    <td className="px-4 sm:px-5 py-3 sm:py-2.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border ${
                        estado === 'FINALIZADA' ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20' : 
                        estado === 'PLANIFICADA' ? 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/20' : 
                        estado === 'EN CURSO' ? 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/20' :
                        'bg-red-50 text-red-700 border-red-200 dark:bg-red-500/10 dark:text-red-400 dark:border-red-500/20'
                      }`}>
                        {estado}
                      </span>
                    </td>
                    <td className="px-4 sm:px-5 py-3 sm:py-2.5 font-semibold text-[#1A5729] dark:text-cyan-400">{getVal(c, 'rendimiento_estimado')} t/ha</td>
                    <td className="px-4 sm:px-5 py-3 sm:py-2.5 text-right">
                      <div className="flex items-center justify-end gap-2 sm:gap-1 opacity-100 sm:opacity-60 group-hover:opacity-100 transition-opacity">
                        <button onClick={() => openEditModal(c)} title="Editar" className="p-2 sm:p-1.5 text-gray-500 hover:text-cyan-600 hover:bg-cyan-50 dark:hover:text-cyan-400 dark:hover:bg-slate-700 rounded transition-colors">
                          <svg fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-4 h-4 sm:w-4 sm:h-4"><path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L6.832 19.82a4.5 4.5 0 01-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 011.13-1.897L16.863 4.487zm0 0L19.5 7.125" /></svg>
                        </button>
                        <button onClick={() => handleEliminar(idCampana, getVal(c, 'nombre_campana'))} title="Eliminar" className="p-2 sm:p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 dark:hover:text-red-400 dark:hover:bg-slate-700 rounded transition-colors">
                          <svg fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-4 h-4 sm:w-4 sm:h-4"><path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" /></svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                )})}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* MODAL RESPONSIVO */}
      {showModal && (
        <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-4 sm:p-0 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
          <div className="bg-white dark:bg-[#1E293B] rounded-2xl sm:rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden border border-gray-200 dark:border-slate-700 animate-slide-up sm:animate-none max-h-[90vh] overflow-y-auto custom-scrollbar">
            
            <div className="px-5 py-4 sm:py-3.5 border-b border-gray-200 dark:border-slate-700 flex justify-between items-center bg-gray-50/50 dark:bg-slate-800/50 sticky top-0 z-10">
              <h3 className="text-base font-bold text-gray-800 dark:text-white">
                {isEditing ? 'Editar Campaña' : 'Nueva Campaña'}
              </h3>
              <button onClick={() => { setShowModal(false); resetIaState(); }} className="text-gray-400 hover:text-red-500 transition-colors p-1">
                <svg fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6 sm:w-5 sm:h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-5 sm:p-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-4">
                
                <div className="md:col-span-2">
                  <label className="block text-[11px] font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wide mb-1.5">ID Campaña</label>
                  <input type="text" name="id_campana" disabled value={isEditing ? formData.id_campana : 'AUTO-GENERADO'}
                    className="w-full px-3 py-2.5 sm:py-2 bg-gray-100 dark:bg-slate-800/50 border border-gray-200 dark:border-slate-700 rounded-md text-base sm:text-sm text-gray-500 font-mono cursor-not-allowed outline-none" />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wide mb-1.5">Nombre de la Campaña *</label>
                  <input type="text" name="nombre_campana" required value={formData.nombre_campana} onChange={handleChange} placeholder="Ej: SOYA INVIERNO 2026"
                    className="w-full px-3 py-2.5 sm:py-2 bg-white dark:bg-[#0F172A] border border-gray-300 dark:border-slate-600 rounded-md text-base sm:text-sm text-gray-800 dark:text-slate-200 focus:ring-2 sm:focus:ring-1 focus:ring-[#1A5729] outline-none uppercase" />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wide mb-1.5">Variedad Sembrada *</label>
                  <input type="text" name="variedad" required value={formData.variedad} onChange={handleChange} placeholder="Ej: SOYA MUNASQA"
                    className="w-full px-3 py-2.5 sm:py-2 bg-white dark:bg-[#0F172A] border border-gray-300 dark:border-slate-600 rounded-md text-base sm:text-sm text-gray-800 dark:text-slate-200 focus:ring-2 sm:focus:ring-1 focus:ring-[#1A5729] outline-none uppercase" />
                </div>

                {/* AQUÍ EL MAPEO BLINDADO DE LOTES */}
                <div className="md:col-span-2">
                  <label className="block text-[11px] font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wide mb-1.5">Asignar a Lote (Terreno) *</label>
                  <select name="nro_lote" required value={formData.nro_lote} onChange={handleChange}
                    className="w-full px-3 py-2.5 sm:py-2 bg-white dark:bg-[#0F172A] border border-gray-300 dark:border-slate-600 rounded-md text-base sm:text-sm text-gray-800 dark:text-slate-200 focus:ring-2 sm:focus:ring-1 focus:ring-[#1A5729] outline-none"
                  >
                    <option value="" disabled>Seleccione el terreno para esta campaña</option>
                    {terrenos.map((t, index) => {
                      // El cazador de IDs para cualquier variante que mande Flask
                      const idLote = getVal(t, 'nro_lote') || getVal(t, 'id') || getVal(t, 'id_terreno') || getVal(t, 'lote');
                      return (
                        <option key={idLote || index} value={idLote}>
                          Lote #{idLote} - Sector: {getVal(t, 'nombre_sector')} ({getVal(t, 'tamano_hectareas')} Ha)
                        </option>
                      );
                    })}
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wide mb-1.5">Estado *</label>
                  <select name="estado" required value={formData.estado} onChange={handleChange}
                    className="w-full px-3 py-2.5 sm:py-2 bg-white dark:bg-[#0F172A] border border-gray-300 dark:border-slate-600 rounded-md text-base sm:text-sm text-gray-800 dark:text-slate-200 focus:ring-2 sm:focus:ring-1 focus:ring-[#1A5729] outline-none"
                  >
                    <option value="PLANIFICADA">PLANIFICADA</option>
                    <option value="EN CURSO">EN CURSO</option>
                    <option value="FINALIZADA">FINALIZADA</option>
                    <option value="CANCELADA">CANCELADA</option>
                  </select>
                </div>

                {/* CAMPO RENDIMIENTO ESTIMADO + IA */}
                <div className="md:col-span-2">
                  <label className="block text-[11px] font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wide mb-1.5">Rend. Estimado (ton/ha)</label>

                  {/* Input oculto que conserva el valor para el submit */}
                  <input type="hidden" name="rendimiento_estimado" value={formData.rendimiento_estimado} />

                  {isEditing ? (
                    <div className="space-y-3">
                      {/* Botón calcular */}
                      <button
                        type="button"
                        onClick={handleCalcularIA}
                        disabled={iaLoading}
                        className="flex items-center gap-2 px-4 py-2.5 sm:py-2 text-sm sm:text-xs font-semibold text-white bg-[#1A5729] hover:bg-[#144320] disabled:opacity-60 disabled:cursor-not-allowed rounded-lg shadow-sm transition-colors w-full sm:w-auto justify-center"
                      >
                        {iaLoading ? (
                          <>
                            <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                            </svg>
                            Calculando...
                          </>
                        ) : (
                          <>
                            <svg fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                              <path strokeLinecap="round" strokeLinejoin="round" d="M18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z" />
                            </svg>
                            Calcular con IA
                          </>
                        )}
                      </button>

                      {/* Error de IA */}
                      {iaError && (
                        <p className="text-xs text-red-500 dark:text-red-400 flex items-center gap-1.5">
                          <svg fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-3.5 h-3.5 shrink-0">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126z" />
                          </svg>
                          {iaError}
                        </p>
                      )}

                      {/* Tarjeta resultado IA */}
                      {iaResultado && (
                        <div className="rounded-xl border border-emerald-200 dark:border-emerald-500/30 bg-emerald-50/60 dark:bg-emerald-500/5 p-4 space-y-3">
                          <div className="flex items-center gap-3">
                            <div className="shrink-0 w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-500/15 flex items-center justify-center">
                              <svg fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor" className="w-5 h-5 text-emerald-600 dark:text-emerald-400">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
                              </svg>
                            </div>
                            <div>
                              <p className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">Estimación IA</p>
                              <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-300 leading-tight">
                                {iaResultado.rendimiento_estimado} <span className="text-base font-semibold">t/ha</span>
                              </p>
                            </div>
                          </div>

                          <div className="flex items-start gap-2 text-xs text-gray-600 dark:text-slate-400">
                            <svg fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-3.5 h-3.5 shrink-0 mt-0.5 text-gray-400">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
                            </svg>
                            <span className="leading-relaxed">{iaResultado.justificacion}</span>
                          </div>

                          <div className="pt-1">
                            {rendimientoConfirmado ? (
                              <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                                <svg fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-4 h-4">
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                                </svg>
                                Valor aplicado al formulario
                              </div>
                            ) : (
                              <button
                                type="button"
                                onClick={handleUsarValorIA}
                                className="text-xs font-semibold px-3 py-1.5 rounded-md border border-emerald-300 dark:border-emerald-500/40 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-500/10 transition-colors"
                              >
                                Usar este valor
                              </button>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-xs text-gray-400 dark:text-slate-500 flex items-center gap-1.5 py-2">
                      <svg fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-3.5 h-3.5 shrink-0">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
                      </svg>
                      Guarda la campaña primero para poder calcular el rendimiento estimado con IA.
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wide mb-1.5">Fecha de Siembra *</label>
                  <input type="date" name="fecha_siembra" required value={formData.fecha_siembra} onChange={handleChange}
                    className="w-full px-3 py-2.5 sm:py-2 bg-white dark:bg-[#0F172A] border border-gray-300 dark:border-slate-600 rounded-md text-base sm:text-sm text-gray-800 dark:text-slate-200 focus:ring-2 sm:focus:ring-1 focus:ring-[#1A5729] outline-none dark:[color-scheme:dark]" />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wide mb-1.5">Fecha de Cosecha *</label>
                  <input type="date" name="fecha_cosecha" required value={formData.fecha_cosecha} onChange={handleChange}
                    className="w-full px-3 py-2.5 sm:py-2 bg-white dark:bg-[#0F172A] border border-gray-300 dark:border-slate-600 rounded-md text-base sm:text-sm text-gray-800 dark:text-slate-200 focus:ring-2 sm:focus:ring-1 focus:ring-[#1A5729] outline-none dark:[color-scheme:dark]" />
                </div>

                {isEditing && (
                  <div className="md:col-span-2">
                    <label className="block text-[11px] font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wide mb-1.5">Rend. Real (ton/ha) (Opcional)</label>
                    <input type="number" step="0.01" name="rendimiento_real" value={formData.rendimiento_real} onChange={handleChange} placeholder="Ej: 3.2"
                      className="w-full px-3 py-2.5 sm:py-2 bg-white dark:bg-[#0F172A] border border-gray-300 dark:border-slate-600 rounded-md text-base sm:text-sm text-gray-800 dark:text-slate-200 focus:ring-2 sm:focus:ring-1 focus:ring-[#1A5729] outline-none" />
                  </div>
                )}

              </div>

              <div className="mt-8 sm:mt-6 flex flex-col-reverse sm:flex-row items-center justify-end gap-3 sm:gap-2 pt-4 border-t border-gray-100 dark:border-slate-700">
                <button type="button" onClick={() => setShowModal(false)} className="w-full sm:w-auto px-4 py-3 sm:py-2 text-sm sm:text-xs font-bold sm:font-semibold text-gray-600 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg sm:rounded-md transition-colors">
                  Cancelar
                </button>
                <button type="submit" className="w-full sm:w-auto px-4 py-3 sm:py-2 text-sm sm:text-xs font-bold sm:font-semibold text-white bg-[#1A5729] hover:bg-[#144320] rounded-lg sm:rounded-md shadow-sm transition-colors">
                  {isEditing ? 'Guardar Cambios' : 'Confirmar Registro'}
                </button>
              </div>
            </form>

          </div>
        </div>
      )}
    </div>
  );
}