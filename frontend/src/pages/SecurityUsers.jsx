import { useState, useEffect, useRef } from 'react';
import { useAuthStore } from '../store/auth_store';

const getVal = (obj, keyName) => {
  if (!obj || typeof obj !== 'object') return '';
  const exactKey = Object.keys(obj).find(k => k.toLowerCase() === keyName.toLowerCase());
  const value = exactKey ? obj[exactKey] : '';
  return value !== null && value !== undefined ? value : '';
};

export default function SecurityUsers() {
  const API_URL = import.meta.env.VITE_API_URL;
  const token = useAuthStore((state) => state.token);
  const logout = useAuthStore((state) => state.logout); 
  
  const [usuarios, setUsuarios] = useState([]);
  const [empresas, setEmpresas] = useState([]); 
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filtroEmpresa, setFiltroEmpresa] = useState('');

  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  
  const initialForm = {
    id_usuario: '', user: '', doc: '', name: '', mail: '', 
    number: '', dir: '', password: '', id_role: 4, id_empresa: ''
  };
  const [formData, setFormData] = useState(initialForm);

  const isFetching = useRef(false);

  // 1. CARGA DE DATOS TOTAL (Estrictamente Secuencial)
  const cargarTodo = async () => {
    setLoading(true);
    setError('');
    try {
      // PASO 1: Cargar empresas
      const resEmp = await fetch(`${API_URL}/get-empresas`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (resEmp.status === 401 || resEmp.status === 403) {
        logout(); window.location.href = '/login'; return;
      }
      
      const dataEmp = await resEmp.json();
      let empresasCargadas = [];
      if (dataEmp.success) {
        empresasCargadas = dataEmp.list_empresas || [];
      }

      // PASO 2: Cargar usuarios
      const endpoint = filtroEmpresa ? `${API_URL}/get-users?id_empresa=${filtroEmpresa}` : `${API_URL}/get-users`;
      const resUser = await fetch(endpoint, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const dataUser = await resUser.json();
      
      let usuariosCargados = [];
      if (dataUser.success) {
        usuariosCargados = dataUser.list_users || [];
      }

      setEmpresas(empresasCargadas);
      setUsuarios(usuariosCargados);
    } catch (err) {
      setError("Error de conexión con el servidor");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isFetching.current) return;
    isFetching.current = true;
    cargarTodo().finally(() => { isFetching.current = false; });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtroEmpresa]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.id_empresa) { alert("Debe seleccionar una empresa válida."); return; }

    const endpoint = isEditing ? '/update-users' : '/add-users';
    const payload = { ...formData };
    if (!isEditing) delete payload.id_usuario;

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
          cargarTodo().finally(() => { isFetching.current = false; });
        }
      } else alert(res.message);
    } catch (err) { alert('Error al procesar la petición.'); }
  };

  const handleEliminar = async (username) => {
    if (!window.confirm(`¿Está seguro de eliminar al usuario @${username}?`)) return;
    try {
      const response = await fetch(`${API_URL}/delete-users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ user: username })
      });
      if ((await response.json()).success) {
        if (!isFetching.current) {
          isFetching.current = true;
          cargarTodo().finally(() => { isFetching.current = false; });
        }
      }
    } catch (err) { alert('Error al eliminar.'); }
  };

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const openAddModal = () => {
    setIsEditing(false);
    setFormData(initialForm);
    setShowModal(true);
  };

  const openEditModal = (u) => {
    setIsEditing(true);
    
    // Deducimos el id_role para el formulario si el backend solo envía el texto
    let rolValue = getVal(u, 'id_rol');
    if (!rolValue) {
        const rolStr = String(getVal(u, 'rol')).toUpperCase();
        if(rolStr === 'ADMINISTRADOR') rolValue = 1;
        else if(rolStr === 'SUPERVISOR') rolValue = 2;
        else if(rolStr === 'EMPLEADO') rolValue = 3;
        else rolValue = 4; // CLIENTE por defecto
    }

    setFormData({
      id_usuario: getVal(u, 'id_usuario') || '', 
      user: getVal(u, 'user_name') || '',
      doc: getVal(u, 'documento_identidad') || '',
      name: getVal(u, 'nombre_razon_social') || '',
      mail: getVal(u, 'mail') || getVal(u, 'correo') || '', 
      number: getVal(u, 'telefono') || '',
      dir: getVal(u, 'direccion') || '',
      password: '', 
      id_role: Number(rolValue) || 4,
      id_empresa: getVal(u, 'id_empresa') || ''
    });
    setShowModal(true);
  };

  const usuariosFiltrados = usuarios.filter((u) => {
    const term = searchTerm.toLowerCase();
    return getVal(u, 'nombre_razon_social').toLowerCase().includes(term) || 
           getVal(u, 'user_name').toLowerCase().includes(term) ||
           String(getVal(u, 'documento_identidad')).toLowerCase().includes(term);
  });

  const getNombreRol = (u) => {
    // 1. Prioridad: Leemos directamente el string que manda el backend
    const rolTexto = getVal(u, 'rol');
    if (rolTexto) {
      return String(rolTexto).toUpperCase();
    }

    // 2. Respaldo: Si por algún motivo no llega el string, leemos el ID numérico
    const n = Number(getVal(u, 'id_rol'));
    if (n === 1) return 'ADMINISTRADOR';
    if (n === 2) return 'SUPERVISOR';
    if (n === 3) return 'EMPLEADO';
    if (n === 4) return 'CLIENTE';

    // 3. Por defecto si todo falla
    return 'USUARIO';
  };

  return (
    <div className="p-4 md:p-8 animate-in fade-in duration-500 bg-slate-50 min-h-screen max-w-[100vw] overflow-x-hidden">
      
      {/* CABECERA */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 md:mb-8 gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-black text-slate-800 tracking-tight flex items-center gap-3">
            <div className="w-2 h-6 md:h-8 bg-[#1A5729]"></div>
            USUARIOS Y ACCESOS
          </h1>
          <p className="text-[9px] md:text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mt-1 ml-5">
            Gestión de cuentas Multi-Tenant
          </p>
        </div>

        <div className="flex flex-col sm:flex-row w-full md:w-auto gap-3">
          
          <select 
            value={filtroEmpresa} 
            onChange={(e) => setFiltroEmpresa(e.target.value)} 
            className="px-4 py-2.5 border border-slate-200 rounded-md text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white shadow-sm text-[#1A5729]"
          >
            <option value="">Todas las Empresas</option>
            {empresas.map(emp => (
              <option key={emp.id_empresa} value={emp.id_empresa}>{emp.nombre_empresa}</option>
            ))}
          </select>

          <div className="relative flex-1 md:w-64">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text" placeholder="BUSCAR USUARIO O CI..."
              value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 border border-slate-200 rounded-md text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white shadow-sm"
            />
          </div>

          <button
            onClick={openAddModal}
            className="bg-[#1A5729] hover:bg-[#144320] text-white px-6 py-2.5 rounded-md font-black text-[10px] uppercase tracking-widest transition-all active:scale-95 shadow-md flex items-center justify-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" /></svg>
            CREAR USUARIO
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 text-sm text-red-700 font-medium">
          {error}
        </div>
      )}

      {/* DASHBOARD DE KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-6 md:mb-8">
        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-slate-100 p-2 md:p-3 rounded-md text-slate-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Total Usuarios</p>
            <p className="text-lg md:text-xl font-black text-slate-800">{usuarios.length}</p>
          </div>
        </div>
        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-purple-50 p-2 md:p-3 rounded-md text-purple-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Administradores</p>
            <p className="text-lg md:text-xl font-black text-purple-700">
              {usuarios.filter(u => String(getVal(u, 'rol')).toUpperCase() === 'ADMINISTRADOR').length}
            </p>
          </div>
        </div>
        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-blue-50 p-2 md:p-3 rounded-md text-blue-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Personal Base</p>
            <p className="text-lg md:text-xl font-black text-blue-700">
              {usuarios.filter(u => String(getVal(u, 'rol')).toUpperCase() === 'EMPLEADO').length}
            </p>
          </div>
        </div>
        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-emerald-50 p-2 md:p-3 rounded-md text-emerald-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Tenants (Empresas)</p>
            <p className="text-lg md:text-xl font-black text-emerald-700">{empresas.length}</p>
          </div>
        </div>
      </div>

      {/* TABLA PRINCIPAL */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden w-full">
        <div className="overflow-x-auto w-full custom-scrollbar">
          <table className="w-full min-w-[900px] text-left border-collapse">
            <thead>
              <tr className="bg-slate-100 border-b border-slate-200 text-[10px] font-black text-slate-500 uppercase tracking-widest">
                <th className="px-6 py-4">ID</th>
                <th className="px-6 py-4">Tenant (Empresa)</th>
                <th className="px-6 py-4">Credenciales</th>
                <th className="px-6 py-4">Identificación</th>
                <th className="px-6 py-4">Rol / Privilegio</th>
                <th className="px-6 py-4 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td
                    colSpan="6"
                    className="text-center py-20 text-slate-400 font-bold uppercase text-[10px] tracking-widest"
                  >
                    Sincronizando con los servidores...
                  </td>
                </tr>
              ) : usuariosFiltrados.length === 0 ? (
                <tr>
                  <td
                    colSpan="6"
                    className="text-center py-20 text-slate-400 font-bold uppercase text-[10px] tracking-widest"
                  >
                    No se encontraron usuarios en el sistema
                  </td>
                </tr>
              ) : (
                usuariosFiltrados.map((u) => {
                  const nombreRol = getNombreRol(u);

                  const badgeClass =
                    nombreRol === 'ADMINISTRADOR'
                      ? 'bg-purple-100 text-purple-800'
                      : nombreRol === 'SUPERVISOR'
                      ? 'bg-blue-100 text-blue-800'
                      : nombreRol === 'EMPLEADO'
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-slate-200 text-slate-700';

                  return (
                    <tr
                      key={getVal(u, 'id_usuario')}
                      className="hover:bg-slate-50 transition-colors group"
                    >
                      <td className="px-6 py-4 font-mono text-[10px] font-bold text-slate-400">
                        USR-{String(getVal(u, 'id_usuario')).padStart(4, '0')}
                      </td>

                      <td className="px-6 py-4">
                        <div className="inline-flex items-center px-2 py-1 rounded bg-slate-100 border border-slate-200 text-[10px] font-black uppercase text-slate-600">
                          {empresas.find(
                            (e) =>
                              String(e.id_empresa) ===
                              String(getVal(u, 'id_empresa'))
                          )?.nombre_empresa || 'NO ASIGNADA'}
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <div className="font-black text-slate-800 text-xs">
                          @{getVal(u, 'user_name').toLowerCase()}
                        </div>

                        <div className="text-[9px] text-slate-400 font-bold uppercase mt-0.5 tracking-widest">
                          {getVal(u, 'mail')}
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <div
                          className="text-xs font-bold text-slate-700 uppercase truncate max-w-[200px]"
                          title={getVal(u, 'nombre_razon_social')}
                        >
                          {getVal(u, 'nombre_razon_social')}
                        </div>

                        <div className="text-[9px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">
                          CI/NIT: {getVal(u, 'documento_identidad')}
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <span
                          className={`px-3 py-1 rounded text-[9px] font-black uppercase tracking-widest ${badgeClass}`}
                        >
                          {nombreRol}
                        </span>
                      </td>

                      <td className="px-6 py-4 text-center">
                        <div className="flex justify-center gap-4">
                          <button
                            onClick={() => openEditModal(u)}
                            className="text-blue-600 hover:text-blue-800 font-black text-[10px] uppercase tracking-widest flex flex-col items-center gap-1 opacity-100 sm:opacity-50 group-hover:opacity-100 transition-opacity"
                          >
                            Editar
                          </button>

                          <button
                            onClick={() =>
                              handleEliminar(getVal(u, 'user_name'))
                            }
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
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-3xl flex flex-col max-h-[95vh] border border-slate-300 animate-in zoom-in-95 duration-200">

            {/* Cabecera Fija */}
            <div className="bg-[#1A5729] px-4 sm:px-8 py-4 sm:py-5 flex justify-between items-center text-white shrink-0">
              <div className="flex items-center gap-3">
                <div className="bg-white/20 p-2 rounded-md hidden sm:block">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                </div>
                <div>
                  <h3 className="text-sm sm:text-base font-black uppercase tracking-widest">
                    {isEditing ? 'MODIFICAR USUARIO' : 'REGISTRAR NUEVO USUARIO'}
                  </h3>
                  <p className="text-[9px] sm:text-[10px] text-emerald-100 font-bold uppercase mt-0.5 tracking-wider">
                    Complete los datos del perfil y asigne permisos
                  </p>
                </div>
              </div>
              <button onClick={() => setShowModal(false)} className="text-emerald-100 hover:text-white hover:bg-white/10 p-2 rounded-md transition-colors shrink-0">
                <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>

            {/* Contenido Deslizable */}
            <form onSubmit={handleSubmit} className="p-4 sm:p-8 bg-slate-50 overflow-y-auto custom-scrollbar">

              {/* Sección 1: Asignación MultiTenant */}
              <div className="mb-4 sm:mb-6 p-4 sm:p-6 bg-blue-50 border border-blue-200 rounded-md shadow-sm">
                <label className="block text-[10px] font-black text-blue-800 uppercase tracking-widest mb-1 sm:mb-2 flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
                  ASIGNACIÓN DE EMPRESA (TENANT) *
                </label>
                <select 
                  name="id_empresa" value={formData.id_empresa} onChange={handleChange}
                  className="w-full px-3 sm:px-4 py-2 sm:py-2.5 border border-blue-300 rounded text-xs font-black uppercase outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 bg-white cursor-pointer text-blue-900"
                >
                  <option value="" disabled>-- SELECCIONE LA EMPRESA --</option>
                  {empresas.map(emp => (
                    <option key={emp.id_empresa} value={emp.id_empresa}>{emp.nombre_empresa}</option>
                  ))}
                </select>
                <p className="text-[9px] font-bold text-blue-600/70 uppercase mt-2">Atención: El usuario solo tendrá acceso a los datos de la empresa seleccionada.</p>
              </div>

              {/* Sección 2: Datos Personales */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 bg-white p-4 sm:p-6 rounded-md border border-slate-200 shadow-sm">
                
                <div className="md:col-span-2">
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2">Nombre Completo / Razón Social *</label>
                  <input
                    type="text" required name="name" value={formData.name} onChange={handleChange} placeholder="Ej: Juan Perez"
                    className="w-full px-3 sm:px-4 py-2 sm:py-2.5 border border-slate-200 rounded text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2">Documento (CI / NIT) *</label>
                  <input
                    type="text" required name="doc" value={formData.doc} onChange={handleChange} placeholder="Ej: 8123456"
                    className="w-full px-3 sm:px-4 py-2 sm:py-2.5 border border-slate-200 rounded text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2">Teléfono de Contacto *</label>
                  <input
                    type="text" required name="number" value={formData.number} onChange={handleChange} placeholder="Ej: 71234567"
                    className="w-full px-3 sm:px-4 py-2 sm:py-2.5 border border-slate-200 rounded text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2">Correo Electrónico *</label>
                  <input
                    type="email" required name="mail" value={formData.mail} onChange={handleChange} placeholder="correo@empresa.com"
                    className="w-full px-3 sm:px-4 py-2 sm:py-2.5 border border-slate-200 rounded text-xs font-bold lowercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]"
                  />
                </div>

              </div>

              {/* Sección 3: Credenciales y Rol */}
              <div className="mt-4 sm:mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6 bg-white p-4 sm:p-6 rounded-md border border-slate-200 shadow-sm">
                
                <div>
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2">Rol en el Sistema *</label>
                  <select
                    required name="id_role" value={formData.id_role} onChange={handleChange}
                    className="w-full px-3 sm:px-4 py-2 sm:py-2.5 border border-slate-200 rounded text-xs font-black uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-slate-50 cursor-pointer"
                  >
                    <option value={1}>1 - ADMINISTRADOR (TODO)</option>
                    <option value={2}>2 - SUPERVISOR (REPORTES)</option>
                    <option value={3}>3 - EMPLEADO OPERATIVO</option>
                    <option value={4}>4 - CLIENTE EXTERNO</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2">
                    Nombre de Usuario (Login) {isEditing ? <span className="text-red-500 ml-1">BLOQUEADO</span> : '*'}
                  </label>
                  <input
                    type="text" required disabled={isEditing} name="user" value={formData.user} onChange={handleChange} placeholder="Ej: jperez"
                    className="w-full px-3 sm:px-4 py-2 sm:py-2.5 border border-slate-200 rounded text-xs font-bold lowercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] disabled:bg-slate-100 disabled:text-slate-400"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2 flex items-center gap-1.5">
                    Contraseña de Acceso {isEditing && <span className="text-amber-500 font-bold">(Dejar en blanco para no cambiar)</span>}
                  </label>
                  <input
                    type="password" required={!isEditing} name="password" value={formData.password} onChange={handleChange} placeholder="••••••••"
                    className="w-full px-3 sm:px-4 py-2 sm:py-2.5 border border-slate-200 rounded text-sm font-bold font-mono outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]"
                  />
                </div>
              </div>

              {/* Botonera */}
              <div className="mt-6 sm:mt-8 flex flex-col-reverse sm:flex-row justify-end gap-3 pt-4 sm:pt-6 border-t border-slate-200 shrink-0">
                <button type="button" onClick={() => setShowModal(false)}
                  className="w-full sm:w-auto px-4 sm:px-6 py-3 sm:py-2.5 text-[10px] font-black text-slate-500 uppercase tracking-widest hover:bg-slate-200 rounded-md transition-colors text-center">
                  CANCELAR OPERACIÓN
                </button>
                <button type="submit"
                  className="w-full sm:w-auto px-6 sm:px-10 py-3 sm:py-2.5 bg-[#1A5729] text-white text-[10px] font-black uppercase tracking-widest rounded-md shadow-lg hover:bg-[#144320] transition-all flex items-center justify-center gap-2">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                  {isEditing ? 'GUARDAR CAMBIOS' : 'REGISTRAR'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}