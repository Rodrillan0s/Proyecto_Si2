import { useState, useEffect, useRef } from 'react';
import { useAuthStore } from '../store/auth_store';

const getVal = (obj, keyName) => {
  if (!obj || typeof obj !== 'object') return '';
  const exactKey = Object.keys(obj).find(k => k.toLowerCase() === keyName.toLowerCase());
  const value = exactKey ? obj[exactKey] : '';
  return value !== null && value !== undefined ? value : '';
};

export default function SecurityTenants() {
  const API_URL = import.meta.env.VITE_API_URL;
  const token = useAuthStore((state) => state.token);
  const logout = useAuthStore((state) => state.logout); 
  
  const [empresas, setEmpresas] = useState([]); 
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  
  const initialForm = {
    id_empresa: '', 
    nombre_empresa: '', 
    nit: '', 
    estado: 'ACTIVO'
  };
  const [formData, setFormData] = useState(initialForm);

  const isFetching = useRef(false);

  // CARGA DE DATOS DE EMPRESAS
  const cargarEmpresas = async () => {
    setLoading(true);
    setError('');
    try {
      // Nota: Ajusta la ruta si tu VITE_API_URL ya incluye el '/api'
      const resEmp = await fetch(`${API_URL}/get-empresas`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (resEmp.status === 401 || resEmp.status === 403) {
        logout(); window.location.href = '/login'; return;
      }
      
      const dataEmp = await resEmp.json();
      if (dataEmp.success) {
        setEmpresas(dataEmp.list_empresas || []);
      } else {
        setError(dataEmp.message || "Error al obtener las empresas");
      }
    } catch (err) {
      setError("Error de conexión con el servidor");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isFetching.current) return;
    isFetching.current = true;
    cargarEmpresas().finally(() => { isFetching.current = false; });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const endpoint = isEditing ? '/update-empresa' : '/add-empresa';
    const payload = { ...formData };
    
    // El backend espera null o string vacío si no hay NIT
    if (!payload.nit) payload.nit = null;

    if (!isEditing) delete payload.id_empresa;

    try {
      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(payload)
      });
      const res = await response.json();
      if (res.success) {
        setShowModal(false);
        if (!isFetching.current) {
          isFetching.current = true;
          cargarEmpresas().finally(() => { isFetching.current = false; });
        }
      } else {
        alert(res.message);
      }
    } catch (err) { alert('Error al procesar la petición.'); }
  };

  const handleEliminar = async (idEmpresa, nombreEmpresa) => {
    if (!window.confirm(`¿Está seguro de eliminar la empresa "${nombreEmpresa}"?\n\nEsta acción podría fallar si la empresa tiene usuarios u otros datos asociados.`)) return;
    
    try {
      const response = await fetch(`${API_URL}/delete-empresa`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ id_empresa: idEmpresa })
      });
      const res = await response.json();
      
      if (res.success) {
        if (!isFetching.current) {
          isFetching.current = true;
          cargarEmpresas().finally(() => { isFetching.current = false; });
        }
      } else {
        alert(res.message); // Mostrará el error 409 de llave foránea si tiene datos
      }
    } catch (err) { alert('Error de red al intentar eliminar.'); }
  };

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const openAddModal = () => {
    setIsEditing(false);
    setFormData(initialForm);
    setShowModal(true);
  };

  const openEditModal = (emp) => {
    setIsEditing(true);
    setFormData({
      id_empresa: getVal(emp, 'id_empresa'), 
      nombre_empresa: getVal(emp, 'nombre_empresa') || '',
      nit: getVal(emp, 'nit') || '',
      estado: String(getVal(emp, 'estado')).toUpperCase() || 'ACTIVO'
    });
    setShowModal(true);
  };

  const empresasFiltradas = empresas.filter((emp) => {
    const term = searchTerm.toLowerCase();
    return getVal(emp, 'nombre_empresa').toLowerCase().includes(term) || 
           String(getVal(emp, 'nit')).toLowerCase().includes(term);
  });

  return (
    <div className="p-4 md:p-8 animate-in fade-in duration-500 bg-slate-50 min-h-screen max-w-[100vw] overflow-x-hidden">
      
      {/* CABECERA */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 md:mb-8 gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-black text-slate-800 tracking-tight flex items-center gap-3">
            <div className="w-2 h-6 md:h-8 bg-blue-600"></div>
            TENANTS Y EMPRESAS
          </h1>
          <p className="text-[9px] md:text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mt-1 ml-5">
            Gestión principal de Multi-Tenancy
          </p>
        </div>

        <div className="flex flex-col sm:flex-row w-full md:w-auto gap-3">
          <div className="relative flex-1 md:w-64">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text" placeholder="BUSCAR POR NOMBRE O NIT..."
              value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 border border-slate-200 rounded-md text-xs font-bold uppercase outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 bg-white shadow-sm"
            />
          </div>

          <button
            onClick={openAddModal}
            className="bg-blue-600 hover:bg-blue-800 text-white px-6 py-2.5 rounded-md font-black text-[10px] uppercase tracking-widest transition-all active:scale-95 shadow-md flex items-center justify-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" /></svg>
            NUEVO TENANT
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 text-sm text-red-700 font-medium shadow-sm">
          {error}
        </div>
      )}

      {/* DASHBOARD DE KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-6 md:mb-8">
        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-slate-100 p-2 md:p-3 rounded-md text-slate-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Total Registradas</p>
            <p className="text-lg md:text-xl font-black text-slate-800">{empresas.length}</p>
          </div>
        </div>
        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-emerald-50 p-2 md:p-3 rounded-md text-emerald-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Empresas Activas</p>
            <p className="text-lg md:text-xl font-black text-emerald-700">
              {empresas.filter(e => String(getVal(e, 'estado')).toUpperCase() === 'ACTIVO').length}
            </p>
          </div>
        </div>
        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-rose-50 p-2 md:p-3 rounded-md text-rose-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Inactivas / Suspendidas</p>
            <p className="text-lg md:text-xl font-black text-rose-700">
              {empresas.filter(e => String(getVal(e, 'estado')).toUpperCase() !== 'ACTIVO').length}
            </p>
          </div>
        </div>
        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-blue-50 p-2 md:p-3 rounded-md text-blue-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Estado del Sistema</p>
            <p className="text-sm font-black text-blue-700 uppercase">Operativo</p>
          </div>
        </div>
      </div>

      {/* TABLA PRINCIPAL */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden w-full">
        <div className="overflow-x-auto w-full custom-scrollbar">
          <table className="w-full min-w-[800px] text-left border-collapse">
            <thead>
              <tr className="bg-slate-100 border-b border-slate-200 text-[10px] font-black text-slate-500 uppercase tracking-widest">
                <th className="px-6 py-4">ID</th>
                <th className="px-6 py-4">Información de la Empresa</th>
                <th className="px-6 py-4">Documento / NIT</th>
                <th className="px-6 py-4">Estado Operativo</th>
                <th className="px-6 py-4">Fecha de Registro</th>
                <th className="px-6 py-4 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan="6" className="text-center py-20 text-slate-400 font-bold uppercase text-[10px] tracking-widest">
                    Sincronizando con los servidores...
                  </td>
                </tr>
              ) : empresasFiltradas.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center py-20 text-slate-400 font-bold uppercase text-[10px] tracking-widest">
                    No se encontraron empresas (Tenants)
                  </td>
                </tr>
              ) : (
                empresasFiltradas.map((emp) => {
                  const estadoStr = String(getVal(emp, 'estado')).toUpperCase();
                  const badgeClass = estadoStr === 'ACTIVO' 
                    ? 'bg-emerald-100 text-emerald-800 border-emerald-200' 
                    : 'bg-rose-100 text-rose-800 border-rose-200';

                  return (
                    <tr key={getVal(emp, 'id_empresa')} className="hover:bg-slate-50 transition-colors group">
                      <td className="px-6 py-4 font-mono text-[10px] font-bold text-slate-400">
                        TEN-{String(getVal(emp, 'id_empresa')).padStart(4, '0')}
                      </td>

                      <td className="px-6 py-4">
                        <div className="font-black text-slate-800 text-sm uppercase">
                          {getVal(emp, 'nombre_empresa')}
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <div className="text-xs font-bold text-slate-600 font-mono">
                          {getVal(emp, 'nit') || <span className="text-slate-300 italic text-[10px]">SIN NIT REGISTRADO</span>}
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <span className={`px-3 py-1 rounded text-[9px] font-black uppercase tracking-widest border ${badgeClass}`}>
                          {estadoStr}
                        </span>
                      </td>

                      <td className="px-6 py-4">
                        <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">
                          {getVal(emp, 'created_at') || 'N/A'}
                        </div>
                      </td>

                      <td className="px-6 py-4 text-center">
                        <div className="flex justify-center gap-4">
                          <button
                            onClick={() => openEditModal(emp)}
                            className="text-blue-600 hover:text-blue-800 font-black text-[10px] uppercase tracking-widest flex flex-col items-center gap-1 opacity-100 sm:opacity-50 group-hover:opacity-100 transition-opacity"
                          >
                            Editar
                          </button>

                          <button
                            onClick={() => handleEliminar(getVal(emp, 'id_empresa'), getVal(emp, 'nombre_empresa'))}
                            className="text-red-500 hover:text-red-700 font-black text-[10px] uppercase tracking-widest flex flex-col items-center gap-1 opacity-100 sm:opacity-50 group-hover:opacity-100 transition-opacity"
                          >
                            Borrar
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* MODAL */}
      {showModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-2 sm:p-4 bg-slate-900/70 backdrop-blur-sm">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-2xl flex flex-col max-h-[95vh] border border-slate-300 animate-in zoom-in-95 duration-200">

            {/* Cabecera Fija */}
            <div className="bg-blue-700 px-4 sm:px-8 py-4 sm:py-5 flex justify-between items-center text-white shrink-0">
              <div className="flex items-center gap-3">
                <div className="bg-white/20 p-2 rounded-md hidden sm:block">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
                </div>
                <div>
                  <h3 className="text-sm sm:text-base font-black uppercase tracking-widest">
                    {isEditing ? 'MODIFICAR TENANT (EMPRESA)' : 'REGISTRAR NUEVA EMPRESA'}
                  </h3>
                  <p className="text-[9px] sm:text-[10px] text-blue-100 font-bold uppercase mt-0.5 tracking-wider">
                    Configuración de entorno de trabajo
                  </p>
                </div>
              </div>
              <button onClick={() => setShowModal(false)} className="text-blue-100 hover:text-white hover:bg-white/10 p-2 rounded-md transition-colors shrink-0">
                <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>

            {/* Contenido Deslizable */}
            <form onSubmit={handleSubmit} className="p-4 sm:p-8 bg-slate-50 overflow-y-auto custom-scrollbar">

              <div className="grid grid-cols-1 gap-4 sm:gap-6 bg-white p-4 sm:p-6 rounded-md border border-slate-200 shadow-sm">
                
                <div>
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2">Nombre o Razón Social *</label>
                  <input
                    type="text" required name="nombre_empresa" value={formData.nombre_empresa} onChange={handleChange} placeholder="Ej: AgroIndustrias S.A."
                    className="w-full px-3 sm:px-4 py-2 sm:py-2.5 border border-slate-200 rounded text-xs font-bold uppercase outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2">Documento / NIT <span className="text-slate-400 font-normal">(Opcional)</span></label>
                  <input
                    type="text" name="nit" value={formData.nit} onChange={handleChange} placeholder="Ej: 1234567890"
                    className="w-full px-3 sm:px-4 py-2 sm:py-2.5 border border-slate-200 rounded text-xs font-bold uppercase outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2">Estado Operativo *</label>
                  <select
                    required name="estado" value={formData.estado} onChange={handleChange}
                    className="w-full px-3 sm:px-4 py-2 sm:py-2.5 border border-slate-200 rounded text-xs font-black uppercase outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 bg-slate-50 cursor-pointer"
                  >
                    <option value="ACTIVO">✅ ACTIVO (PERMITE OPERACIONES)</option>
                    <option value="INACTIVO">⛔ INACTIVO (ACCESO BLOQUEADO)</option>
                    <option value="SUSPENDIDO">⚠️ SUSPENDIDO (SOLO LECTURA)</option>
                  </select>
                </div>

              </div>

              {/* Botonera */}
              <div className="mt-6 sm:mt-8 flex flex-col-reverse sm:flex-row justify-end gap-3 pt-4 sm:pt-6 border-t border-slate-200 shrink-0">
                <button type="button" onClick={() => setShowModal(false)}
                  className="w-full sm:w-auto px-4 sm:px-6 py-3 sm:py-2.5 text-[10px] font-black text-slate-500 uppercase tracking-widest hover:bg-slate-200 rounded-md transition-colors text-center">
                  CANCELAR
                </button>
                <button type="submit"
                  className="w-full sm:w-auto px-6 sm:px-10 py-3 sm:py-2.5 bg-blue-600 text-white text-[10px] font-black uppercase tracking-widest rounded-md shadow-lg hover:bg-blue-800 transition-all flex items-center justify-center gap-2">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                  {isEditing ? 'GUARDAR CAMBIOS' : 'REGISTRAR EMPRESA'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}