import { useState, useEffect } from 'react';
import { useAuthStore } from '../store/auth_store';
import MapPicker from '../components/MapPicker';

const getVal = (obj, keyName) => {
  if (!obj) return '';
  const exactKey = Object.keys(obj).find(k => k.toLowerCase() === keyName.toLowerCase());
  return exactKey ? obj[exactKey] : '';
};

export default function AgroLotes() {
  const API_URL = import.meta.env.VITE_API_URL;
  const token = useAuthStore((state) => state.token);
  const logout = useAuthStore((state) => state.logout); 
  
  const [lotes, setLotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [showMapPicker, setShowMapPicker] = useState(false);
  
  const [formData, setFormData] = useState({
    nro_lote: '',
    nombre_sector: '',
    tamano_hectareas: '',
    latitud: '',
    longitud: '',
    estado: '' 
    // ¡Adiós id_usuario!
  });

  const cargarTerrenos = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${API_URL}/get-terrenos`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        }
      });
      const data = await response.json();
      
      if (response.status === 401 || response.status === 403) {
        if(response.status === 401) logout();
        window.location.href = '/login';
        return;
      }
      
      if (!data.success) throw new Error(data.message || 'Error al obtener terrenos');
      
      setLotes(data.list_terrenos || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargarTerrenos();
  }, []);

  const handleEliminar = async (nro_lote, nombre) => {
    if (!window.confirm(`¿Estás seguro de eliminar el terreno "${nombre}"?`)) return;
    try {
      const response = await fetch(`${API_URL}/delete-terreno`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ nro_lote: nro_lote }) 
      });
      const data = await response.json();
      if (!data.success) throw new Error(data.message);
      cargarTerrenos(); 
    } catch (err) {
      alert(`Error al eliminar: ${err.message}`);
    }
  };

  const openAddModal = () => {
    setIsEditing(false);
    setShowMapPicker(false);
    setFormData({ 
      nro_lote: '', nombre_sector: '', tamano_hectareas: '', 
      latitud: '', longitud: '', estado: '' 
    });
    setShowModal(true);
  };

  const openEditModal = (lote) => {
    setIsEditing(true);
    setShowMapPicker(false);
    setFormData({
      nro_lote: getVal(lote, 'nro_lote'),
      nombre_sector: getVal(lote, 'nombre_sector'),
      tamano_hectareas: getVal(lote, 'tamano_hectareas'),
      latitud: getVal(lote, 'latitud'),
      longitud: getVal(lote, 'longitud'),
      estado: getVal(lote, 'estado') || 'ACTIVO'
    });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const endpoint = isEditing ? '/update-terreno' : '/add-terreno';
    
    const payload = {
      ...formData,
      tamano_hectareas: parseFloat(formData.tamano_hectareas),
      latitud: parseFloat(formData.latitud),
      longitud: parseFloat(formData.longitud)
      // Ya no enviamos id_usuario
    };

    if (!isEditing) {
      delete payload.estado;
      delete payload.nro_lote; 
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
      const data = await response.json();
      if (!data.success) throw new Error(data.message);
      setShowModal(false);
      cargarTerrenos();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleMapCoordinates = (lat, lng) => {
    setFormData({ 
      ...formData, 
      latitud: lat.toFixed(6), 
      longitud: lng.toFixed(6) 
    });
  };

  const lotesFiltrados = lotes.filter((lote) => {
    const termino = searchTerm.toLowerCase();
    const nro = String(getVal(lote, 'nro_lote')).toLowerCase();
    const nombre = String(getVal(lote, 'nombre_sector')).toLowerCase();
    const propietario = String(getVal(lote, 'propietario')).toLowerCase();
    return nombre.includes(termino) || propietario.includes(termino) || nro.includes(termino);
  });

  return (
    <div className="animate-fade-in relative max-w-full">
      
      {/* Cabecera Responsiva */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-5 gap-4">
        <div className="w-full sm:w-auto">
          <h3 className="text-xl font-bold text-gray-800 dark:text-white tracking-tight">Gestión de Terrenos</h3>
          <p className="text-sm text-gray-500 dark:text-slate-400 mt-0.5">Control de áreas agrícolas de tu propiedad.</p>
        </div>
        <button 
          onClick={openAddModal}
          className="w-full sm:w-auto justify-center bg-[#1A5729] hover:bg-[#144320] dark:bg-cyan-600 dark:hover:bg-cyan-700 text-white text-sm sm:text-xs font-semibold px-4 py-2.5 sm:py-2 rounded-lg shadow-sm transition-colors flex items-center gap-1.5"
        >
          <svg fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-4 h-4"><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>
          Nuevo Terreno
        </button>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 text-red-700 dark:text-red-400 p-3 rounded mb-5 text-sm">
          <span className="font-semibold">Error:</span> {error}
        </div>
      )}
      
      {/* Contenedor Principal */}
      <div className="bg-white dark:bg-[#1E293B] border border-gray-200 dark:border-slate-700/80 rounded-xl shadow-sm overflow-hidden flex flex-col">
        
        {/* Buscador Premium */}
        <div className="px-4 sm:px-5 py-3 border-b border-gray-200 dark:border-slate-700/80 bg-gray-50/40 dark:bg-slate-800/40 flex items-center">
          <div className="relative w-full sm:w-80">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" /></svg>
            </div>
            <input 
              type="text" 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar por lote, sector o propietario..." 
              className="w-full pl-9 pr-4 py-2 sm:py-1.5 text-base sm:text-sm border border-gray-300 dark:border-slate-600 rounded-md bg-white dark:bg-[#0F172A] focus:ring-1 focus:ring-[#1A5729] outline-none transition-all dark:text-slate-200 placeholder:text-gray-400"
            />
          </div>
        </div>

        {/* Tabla Densidad Corporativa */}
        <div className="overflow-x-auto custom-scrollbar">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400">
              <svg className="animate-spin h-6 w-6 text-[#1A5729] dark:text-cyan-600 mb-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p className="text-xs font-semibold tracking-wider uppercase">Cargando terrenos...</p>
            </div>
          ) : lotesFiltrados.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p className="text-sm font-medium">No se encontraron terrenos.</p>
            </div>
          ) : (
            <table className="w-full text-left border-collapse whitespace-nowrap">
              <thead>
                <tr className="bg-gray-50/80 dark:bg-slate-800/80 border-b border-gray-200 dark:border-slate-700 text-[11px] font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">
                  <th className="px-4 sm:px-5 py-3 w-16 text-center">Lote</th>
                  <th className="px-4 sm:px-5 py-3">Sector</th>
                  <th className="px-4 sm:px-5 py-3">Superficie</th>
                  <th className="px-4 sm:px-5 py-3">Coordenadas</th>
                  <th className="px-4 sm:px-5 py-3">Estado</th>
                  <th className="px-4 sm:px-5 py-3">Propietario</th>
                  <th className="px-4 sm:px-5 py-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-slate-700/80 text-sm">
                {lotesFiltrados.map((lote, index) => {
                  const nroLote = getVal(lote, 'nro_lote');
                  const estado = getVal(lote, 'estado') || 'EN_DESCANSO';
                  const propietario = getVal(lote, 'propietario');
                  
                  return (
                  <tr key={nroLote || index} className="hover:bg-gray-50/60 dark:hover:bg-slate-800/40 transition-colors group">
                    <td className="px-4 sm:px-5 py-3 sm:py-2.5 text-center text-gray-400 dark:text-slate-500 font-mono text-xs">#{nroLote}</td>
                    <td className="px-4 sm:px-5 py-3 sm:py-2.5 font-bold text-gray-800 dark:text-slate-200">{getVal(lote, 'nombre_sector')}</td>
                    <td className="px-4 sm:px-5 py-3 sm:py-2.5 font-semibold text-[#1A5729] dark:text-cyan-400">{getVal(lote, 'tamano_hectareas')} Ha</td>
                    <td className="px-4 sm:px-5 py-3 sm:py-2.5 text-gray-500 dark:text-slate-400 font-mono text-[11px]">{getVal(lote, 'latitud')}, {getVal(lote, 'longitud')}</td>
                    <td className="px-4 sm:px-5 py-3 sm:py-2.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border ${
                        estado === 'ACTIVO' ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20' : 
                        estado === 'EN PREPARACION' ? 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/20' :
                        'bg-gray-100 text-gray-600 border-gray-200 dark:bg-slate-700 dark:text-slate-300 dark:border-slate-600'
                      }`}>
                        {estado}
                      </span>
                    </td>
                    <td className="px-4 sm:px-5 py-3 sm:py-2.5">
                      <span className="bg-cyan-50 text-cyan-700 border border-cyan-200 dark:bg-cyan-500/10 dark:text-cyan-400 dark:border-cyan-500/20 px-2 py-0.5 rounded text-[10px] font-bold tracking-wide">
                          @{propietario ? String(propietario).toLowerCase() : 'sin propietario'}
                      </span>
                    </td>
                    <td className="px-4 sm:px-5 py-3 sm:py-2.5 text-right">
                      <div className="flex items-center justify-end gap-2 sm:gap-1 opacity-100 sm:opacity-60 group-hover:opacity-100 transition-opacity">
                        <button onClick={() => openEditModal(lote)} title="Editar" className="p-2 sm:p-1.5 text-gray-500 hover:text-cyan-600 hover:bg-cyan-50 dark:hover:text-cyan-400 dark:hover:bg-slate-700 rounded transition-colors">
                          <svg fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-4 h-4 sm:w-4 sm:h-4"><path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L6.832 19.82a4.5 4.5 0 01-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 011.13-1.897L16.863 4.487zm0 0L19.5 7.125" /></svg>
                        </button>
                        <button onClick={() => handleEliminar(nroLote, getVal(lote, 'nombre_sector'))} title="Eliminar" className="p-2 sm:p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 dark:hover:text-red-400 dark:hover:bg-slate-700 rounded transition-colors">
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

      {/* MODAL NUEVO LOTE*/}
      {showModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-[#1E293B] rounded-2xl shadow-2xl w-full max-w-5xl overflow-hidden border border-slate-200 dark:border-slate-700 flex flex-col max-h-[90vh]">
            
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-gray-50/50 dark:bg-slate-800/50">
              <div>
                <h3 className="text-lg font-bold text-slate-800 dark:text-white">
                  {isEditing ? `Editar Terreno: ${formData.nombre_sector}` : 'Registrar Nuevo Terreno'}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">Complete la información técnica y geográfica del lote.</p>
              </div>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-red-500 transition-colors">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>

            <div className="flex flex-col md:flex-row overflow-y-auto">
              {/* Columna Izquierda: Formulario */}
              <form onSubmit={handleSubmit} id="loteForm" className="flex-1 p-6 space-y-5 border-r border-slate-100 dark:border-slate-800">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="sm:col-span-2">
                    <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Nombre del Sector</label>
                    <input type="text" name="nombre_sector" required value={formData.nombre_sector} onChange={handleChange}
                      className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-[#1A5729] outline-none" />
                  </div>

                  <div>
                    <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Superficie (Hectáreas)</label>
                    <div className="relative">
                      <input type="number" step="0.01" name="tamano_hectareas" required value={formData.tamano_hectareas} onChange={handleChange}
                        className="w-full pl-3 pr-10 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-[#1A5729] outline-none" />
                      <span className="absolute right-3 top-2 text-xs font-bold text-slate-400">Ha</span>
                    </div>
                  </div>

                  {isEditing && (
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Estado Operativo</label>
                      <select name="estado" required value={formData.estado} onChange={handleChange}
                        className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-[#1A5729] outline-none">
                        <option value="ACTIVO">ACTIVO</option>
                        <option value="EN PREPARACION">EN PREPARACIÓN</option>
                        <option value="EN_DESCANSO">EN DESCANSO</option>
                      </select>
                    </div>
                  )}

                  <div>
                    <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Latitud</label>
                    <input type="text" disabled value={formData.latitud} 
                      className="w-full px-3 py-2 bg-slate-100 dark:bg-slate-800 text-slate-500 border border-slate-200 dark:border-slate-700 rounded-lg font-mono text-xs" />
                  </div>

                  <div>
                    <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Longitud</label>
                    <input type="text" disabled value={formData.longitud} 
                      className="w-full px-3 py-2 bg-slate-100 dark:bg-slate-800 text-slate-500 border border-slate-200 dark:border-slate-700 rounded-lg font-mono text-xs" />
                  </div>
                </div>
              </form>

              {/* Columna Derecha: Mapa */}
              <div className="flex-1 p-6 bg-slate-50/50 dark:bg-slate-900/20">
                <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-3">Ubicación Geoespacial</label>
                <MapPicker 
                  latitud={formData.latitud} 
                  longitud={formData.longitud}
                  onCoordinatesChange={handleMapCoordinates}
                />
                <p className="mt-3 text-[10px] text-slate-400 italic">
                  * Haga clic en cualquier punto del mapa para capturar las coordenadas exactas del lote.
                </p>
              </div>
            </div>

            {/* Footer del Modal */}
            <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-800 bg-white dark:bg-[#1E293B] flex justify-end gap-3">
              <button type="button" onClick={() => setShowModal(false)} 
                className="px-4 py-2 text-sm font-bold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors">
                Descartar
              </button>
              <button type="submit" form="loteForm"
                className="px-6 py-2 bg-[#1A5729] dark:bg-[#5B9D1E] text-white text-sm font-bold rounded-lg shadow-lg shadow-emerald-900/20 hover:scale-[1.02] active:scale-95 transition-all">
                {isEditing ? 'Actualizar Terreno' : 'Registrar Lote'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}