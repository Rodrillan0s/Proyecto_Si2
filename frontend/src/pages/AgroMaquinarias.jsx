import { useState, useEffect } from 'react';
import { useAuthStore } from '../store/auth_store';
import * as XLSX from 'xlsx';

const API_URL = import.meta.env.VITE_API_URL;

export default function AgroMaquinarias() {
  const token = useAuthStore((state) => state.token);

  const [maquinaria, setMaquinaria] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [currentId, setCurrentId] = useState(null);
  const [categoryFilter, setCategoryFilter] = useState('TODOS');

  const initialForm = {
    tipo: '',
    modelo: '',
    placa: '',
    estado: 'DISPONIBLE',
    kilometraje: '',
    cant_tanque_comb: '',
    fecha_ult_mant: ''
  };
  const [formData, setFormData] = useState(initialForm);

  // ── ESTADO HISTORIAL DE MANTENIMIENTO ──────────────────────────────────────
  const [showMantModal, setShowMantModal] = useState(false);
  const [currentMaquina, setCurrentMaquina] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [loadingHistorial, setLoadingHistorial] = useState(false);
  const [showMantForm, setShowMantForm] = useState(false);
  const [isEditingMant, setIsEditingMant] = useState(false);
  const [currentNroOrden, setCurrentNroOrden] = useState(null);

  const initialMantForm = {
    tipo_mant: 'PREVENTIVO',
    descripcion: '',
    fecha_inicio: '',
    fecha_fin: '',
    estado: 'COMPLETADO',
    id_empleado: '',
    observaciones: ''
  };
  const [mantForm, setMantForm] = useState(initialMantForm);
  // ──────────────────────────────────────────────────────────────────────────

  const fetchMaquinaria = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/maquinaria`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const result = await response.json();
      if (result.success) {
        setMaquinaria(result.data || []);
      }
    } catch (error) {
      console.error("Error en la carga:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) fetchMaquinaria();
  }, [token]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const openAddModal = () => {
    setIsEditing(false);
    setFormData(initialForm);
    setShowModal(true);
  };

  const openEditModal = (maq) => {
    setIsEditing(true);
    setCurrentId(maq.nro_maquina);
    setFormData({
      tipo: maq.tipo,
      modelo: maq.modelo || '',
      placa: maq.placa,
      estado: maq.estado,
      kilometraje: maq.kilometraje || '',
      cant_tanque_comb: maq.cant_tanque_comb || '',
      fecha_ult_mant: maq.fecha_ult_mant || ''
    });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const payload = {
      ...formData,
      tipo: formData.tipo.toUpperCase(),
      placa: formData.placa.toUpperCase(),
      modelo: formData.modelo.toUpperCase(),
      kilometraje: parseFloat(formData.kilometraje) || 0,
      cant_tanque_comb: parseFloat(formData.cant_tanque_comb) || 0
    };

    const url = isEditing ? `${API_URL}/maquinaria/${currentId}` : `${API_URL}/maquinaria`;
    const method = isEditing ? 'PUT' : 'POST';

    try {
      const response = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      const result = await response.json();

      if (result.success) {
        setShowModal(false);
        fetchMaquinaria();
      } else {
        alert(`Atención: ${result.message}`);
      }
    } catch (error) {
      alert("Error de comunicación con el servidor.");
    }
  };

  const handleDelete = async (id, placa) => {
    if (!window.confirm(`¿Está seguro de dar de baja el vehículo con placa ${placa}?`)) return;
    try {
      const response = await fetch(`${API_URL}/maquinaria/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const result = await response.json();
      if (result.success) {
        fetchMaquinaria();
      } else {
        alert(result.message);
      }
    } catch (error) {
      alert("Error al procesar la baja.");
    }
  };

  // ── FUNCIONES HISTORIAL DE MANTENIMIENTO ──────────────────────────────────

  const fetchHistorial = async (nro_maquina) => {
    setLoadingHistorial(true);
    try {
      const response = await fetch(`${API_URL}/maquinaria/${nro_maquina}/mantenimiento`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const result = await response.json();
      if (result.success) setHistorial(result.data || []);
    } catch (error) {
      console.error("Error al cargar historial:", error);
    } finally {
      setLoadingHistorial(false);
    }
  };

  const openMantModal = (maq) => {
    setCurrentMaquina(maq);
    setShowMantForm(false);
    setHistorial([]);
    setShowMantModal(true);
    fetchHistorial(maq.nro_maquina);
  };

  const openAddMant = () => {
    setIsEditingMant(false);
    setCurrentNroOrden(null);
    setMantForm(initialMantForm);
    setShowMantForm(true);
  };

  const openEditMant = (record) => {
    setIsEditingMant(true);
    setCurrentNroOrden(record.nro_orden);
    setMantForm({
      tipo_mant: record.tipo_trabajo.replace('MANTENIMIENTO_', ''),
      descripcion: record.descripcion || '',
      fecha_inicio: record.fecha_inicio ? record.fecha_inicio.substring(0, 10) : '',
      fecha_fin: record.fecha_fin ? record.fecha_fin.substring(0, 10) : '',
      estado: record.estado || 'COMPLETADO',
      id_empleado: record.id_empleado || '',
      observaciones: record.observaciones || ''
    });
    setShowMantForm(true);
  };

  const handleMantChange = (e) => {
    setMantForm({ ...mantForm, [e.target.name]: e.target.value });
  };

  const handleMantSubmit = async (e) => {
    e.preventDefault();
    const payload = {
      ...mantForm,
      id_empleado: mantForm.id_empleado ? parseInt(mantForm.id_empleado) : null,
      ...(isEditingMant ? {} : { nro_maquina: currentMaquina.nro_maquina })
    };

    const url = isEditingMant
      ? `${API_URL}/mantenimiento/${currentNroOrden}`
      : `${API_URL}/mantenimiento`;
    const method = isEditingMant ? 'PUT' : 'POST';

    try {
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(payload)
      });
      const result = await response.json();
      if (result.success) {
        setShowMantForm(false);
        fetchHistorial(currentMaquina.nro_maquina);
      } else {
        alert(`Error: ${result.message}`);
      }
    } catch (error) {
      alert("Error de comunicación con el servidor.");
    }
  };

  const handleDeleteMant = async (nro_orden) => {
    if (!window.confirm('¿Eliminar este registro de mantenimiento?')) return;
    try {
      const response = await fetch(`${API_URL}/mantenimiento/${nro_orden}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const result = await response.json();
      if (result.success) {
        fetchHistorial(currentMaquina.nro_maquina);
      } else {
        alert(result.message);
      }
    } catch (error) {
      alert("Error al eliminar.");
    }
  };

  const getMantBadgeStyle = (tipo_trabajo) => {
    const tipo = tipo_trabajo.replace('MANTENIMIENTO_', '');
    switch (tipo) {
      case 'PREVENTIVO':  return 'bg-blue-50 text-blue-700';
      case 'CORRECTIVO':  return 'bg-orange-50 text-orange-700';
      case 'REVISION':    return 'bg-purple-50 text-purple-700';
      case 'EMERGENCIA':  return 'bg-red-50 text-red-700';
      default:            return 'bg-slate-50 text-slate-700';
    }
  };

  const formatDate = (dateStr) => dateStr ? dateStr.substring(0, 10) : '—';
  // ──────────────────────────────────────────────────────────────────────────

  const exportToCSV = () => {
    const headers = ['ID','TIPO','MODELO','PLACA','ESTADO','KILOMETRAJE','TANQUE','ULTIMO_MANTENIMIENTO'];
    const rows = filtered.map((m) => [m.nro_maquina,m.tipo,m.modelo,m.placa,m.estado,m.kilometraje,m.cant_tanque_comb,m.fecha_ult_mant]);
    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', 'reporte_maquinaria.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportToExcel = () => {
    const data = filtered.map((m) => ({
      ID: m.nro_maquina, TIPO: m.tipo, MODELO: m.modelo, PLACA: m.placa,
      ESTADO: m.estado, KILOMETRAJE: m.kilometraje, TANQUE: m.cant_tanque_comb,
      ULTIMO_MANTENIMIENTO: m.fecha_ult_mant
    }));
    const worksheet = XLSX.utils.json_to_sheet(data);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Maquinaria');
    XLSX.writeFile(workbook, 'reporte_maquinaria.xlsx');
  };

  const filtered = maquinaria.filter((m) => {
    const matchesSearch =
      m.placa.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.tipo.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === 'TODOS' || m.tipo === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const stats = {
    total: maquinaria.length,
    disponibles: maquinaria.filter(m => m.estado === 'DISPONIBLE').length,
    enUso: maquinaria.filter(m => m.estado === 'OCUPADO').length,
    mantenimiento: maquinaria.filter(m => m.estado === 'MANTENIMIENTO').length,
  };

  return (
    <div className="p-4 md:p-8 animate-in fade-in duration-500 bg-slate-50 min-h-screen max-w-[100vw] overflow-x-hidden">

      {/* SECCIÓN CABECERA */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 md:mb-8 gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-black text-slate-800 tracking-tight flex items-center gap-3">
            <div className="w-2 h-6 md:h-8 bg-[#1A5729]"></div>
            CONTROL DE FLOTA
          </h1>
          <p className="text-[9px] md:text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mt-1 ml-5">
            Gestión de Maquinaria y Equipos Agrícolas
          </p>
        </div>

        <div className="flex flex-col lg:flex-row w-full md:w-auto gap-3">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-4 py-2.5 border border-slate-200 rounded-md text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white shadow-sm transition-all"
          >
            <option value="TODOS">TODAS LAS CATEGORÍAS</option>
            <option value="TRACTOR">TRACTOR</option>
            <option value="COSECHADORA">COSECHADORA</option>
            <option value="SEMBRADORA">SEMBRADORA</option>
            <option value="PULVERIZADORA">PULVERIZADORA</option>
            <option value="CAMIONETA">CAMIONETA</option>
            <option value="CAMIÓN">CAMIÓN</option>
            <option value="IMPLEMENTO">IMPLEMENTO</option>
            <option value="OTRO">OTRO</option>
          </select>

          <div className="relative flex-1 md:w-64">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text" placeholder="BUSCAR PLACA O TIPO..."
              value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 border border-slate-200 rounded-md text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white shadow-sm transition-all"
            />
          </div>

          <div className="flex gap-2 flex-wrap">
            <button onClick={exportToCSV} className="bg-white border border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-600 px-4 py-2.5 rounded-lg font-semibold text-[10px] uppercase tracking-wider transition-all duration-200 active:scale-95 shadow-sm flex items-center justify-center gap-2 whitespace-nowrap">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
              CSV
            </button>
            <button onClick={exportToExcel} className="bg-[#1A5729]/10 hover:bg-[#1A5729]/15 border border-[#1A5729]/20 hover:border-[#1A5729]/30 text-[#1A5729] px-4 py-2.5 rounded-lg font-semibold text-[10px] uppercase tracking-wider transition-all duration-200 active:scale-95 shadow-sm flex items-center justify-center gap-2 whitespace-nowrap">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
              EXCEL
            </button>
          </div>

          <button
            onClick={openAddModal}
            className="bg-[#1A5729] hover:bg-[#144320] text-white px-6 py-2.5 rounded-md font-black text-[10px] uppercase tracking-widest transition-all active:scale-95 shadow-md flex items-center justify-center gap-2 whitespace-nowrap"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" /></svg>
            NUEVO EQUIPO
          </button>
        </div>
      </div>

      {/* DASHBOARD DE KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-6 md:mb-8">
        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-slate-100 p-2 md:p-3 rounded-md text-slate-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Total Flota</p>
            <p className="text-lg md:text-xl font-black text-slate-800">{stats.total}</p>
          </div>
        </div>
        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-emerald-50 p-2 md:p-3 rounded-md text-emerald-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Disponibles</p>
            <p className="text-lg md:text-xl font-black text-emerald-700">{stats.disponibles}</p>
          </div>
        </div>
        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-blue-50 p-2 md:p-3 rounded-md text-blue-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Ocupados</p>
            <p className="text-lg md:text-xl font-black text-blue-700">{stats.enUso}</p>
          </div>
        </div>
        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-red-50 p-2 md:p-3 rounded-md text-red-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">En Taller</p>
            <p className="text-lg md:text-xl font-black text-red-700">{stats.mantenimiento}</p>
          </div>
        </div>
      </div>

      {/* TABLA */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden w-full">
        <div className="overflow-x-auto w-full custom-scrollbar">
          <table className="w-full min-w-[900px] text-left border-collapse">
            <thead>
              <tr className="bg-slate-100 border-b border-slate-200 text-[10px] font-black text-slate-500 uppercase tracking-widest">
                <th className="px-6 py-4">Ficha</th>
                <th className="px-6 py-4">Equipo / Vehículo</th>
                <th className="px-6 py-4">Placa/Serie</th>
                <th className="px-6 py-4">Estado Operativo</th>
                <th className="px-6 py-4">Rendimiento / Mant.</th>
                <th className="px-6 py-4 text-center">Gestión</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr><td colSpan="6" className="text-center py-20 text-slate-400 font-bold uppercase text-[10px] tracking-widest">Sincronizando con los servidores...</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan="6" className="text-center py-20 text-slate-400 font-bold uppercase text-[10px] tracking-widest">No hay vehículos que coincidan con la búsqueda</td></tr>
              ) : (
                filtered.map((m) => (
                  <tr key={m.nro_maquina} className="hover:bg-slate-50 transition-colors group">
                    <td className="px-6 py-4 font-mono text-[10px] font-bold text-slate-400">
                      ID-{String(m.nro_maquina).padStart(4, '0')}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="bg-slate-100 p-2 rounded-md text-slate-400 shrink-0">
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>
                        </div>
                        <div className="min-w-0">
                          <div className="font-black text-slate-800 text-xs uppercase truncate">{m.tipo}</div>
                          <div className="text-[10px] text-slate-400 font-bold uppercase truncate">{m.modelo || 'SIN MODELO ESPECÍFICO'}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="inline-block border-2 border-slate-300 rounded px-2 py-0.5 bg-white relative">
                        <div className="absolute top-0 left-0 w-full h-1 bg-blue-800 rounded-t-sm"></div>
                        <span className="font-mono text-xs font-black text-slate-800 pt-1 tracking-widest whitespace-nowrap">{m.placa}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1.5 rounded-md text-[9px] font-black uppercase tracking-widest flex items-center w-fit whitespace-nowrap gap-2 ${
                        m.estado === 'DISPONIBLE' ? 'bg-emerald-50 text-emerald-700' :
                        m.estado === 'OCUPADO' ? 'bg-blue-50 text-blue-700' :
                        'bg-red-50 text-red-700'
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${
                          m.estado === 'DISPONIBLE' ? 'bg-emerald-500' : m.estado === 'OCUPADO' ? 'bg-blue-500 animate-pulse' : 'bg-red-500 animate-bounce'
                        }`}></span>
                        {m.estado}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1 text-[10px] font-bold text-slate-500 uppercase whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                          {m.kilometraje} <span className="text-slate-400">KM / Hrs</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-slate-400">
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
                          Últ. Mant: {m.fecha_ult_mant || 'N/A'}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex justify-center gap-3">
                        {/* HISTORIAL DE MANTENIMIENTO */}
                        <button onClick={() => openMantModal(m)} className="text-[#1A5729] hover:text-[#144320] font-black text-[10px] uppercase tracking-widest flex flex-col items-center gap-1">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          Mant.
                        </button>
                        <button onClick={() => openEditModal(m)} className="text-blue-600 hover:text-blue-800 font-black text-[10px] uppercase tracking-widest flex flex-col items-center gap-1">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                          Editar
                        </button>
                        <button onClick={() => handleDelete(m.nro_maquina, m.placa)} className="text-red-500 hover:text-red-700 font-black text-[10px] uppercase tracking-widest flex flex-col items-center gap-1">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                          Baja
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── MODAL FICHA TÉCNICA (existente) ─────────────────────────────────── */}
      {showModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-2 sm:p-4 bg-slate-900/70 backdrop-blur-sm">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-3xl flex flex-col max-h-[95vh] border border-slate-300 animate-in zoom-in-95 duration-200">

            <div className="bg-[#1A5729] px-4 sm:px-8 py-4 sm:py-5 flex justify-between items-center text-white shrink-0">
              <div className="flex items-center gap-3">
                <div className="bg-white/20 p-2 rounded-md hidden sm:block">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z" /><path strokeLinecap="round" strokeLinejoin="round" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0" /></svg>
                </div>
                <div>
                  <h3 className="text-sm sm:text-base font-black uppercase tracking-widest">
                    {isEditing ? 'FICHA TÉCNICA' : 'ALTA DE VEHÍCULO'}
                  </h3>
                  <p className="text-[9px] sm:text-[10px] text-emerald-100 font-bold uppercase mt-0.5 tracking-wider">Completa los datos operativos del activo</p>
                </div>
              </div>
              <button onClick={() => setShowModal(false)} className="text-emerald-100 hover:text-white hover:bg-white/10 p-2 rounded-md transition-colors shrink-0">
                <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-4 sm:p-8 bg-slate-50 overflow-y-auto custom-scrollbar">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 bg-white p-4 sm:p-6 rounded-md border border-slate-200 shadow-sm">
                <div className="md:col-span-1">
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2">Clasificación / Tipo *</label>
                  <select required name="tipo" value={formData.tipo} onChange={handleChange}
                    className="w-full px-3 sm:px-4 py-2 sm:py-2.5 border border-slate-200 rounded text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white cursor-pointer">
                    <option value="" disabled>SELECCIONE UN TIPO...</option>
                    <option value="TRACTOR">TRACTOR</option>
                    <option value="COSECHADORA">COSECHADORA</option>
                    <option value="SEMBRADORA">SEMBRADORA</option>
                    <option value="PULVERIZADORA">PULVERIZADORA</option>
                    <option value="CAMIONETA">CAMIONETA</option>
                    <option value="CAMIÓN">CAMIÓN PESADO</option>
                    <option value="IMPLEMENTO">IMPLEMENTO AGRÍCOLA</option>
                    <option value="OTRO">OTRO</option>
                  </select>
                </div>
                <div className="md:col-span-1">
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2">Placa Oficial / Nro. Serie *</label>
                  <input type="text" required name="placa" value={formData.placa} onChange={handleChange} placeholder="TRC-000"
                    className="w-full px-3 sm:px-4 py-2 sm:py-2.5 border border-slate-300 rounded text-sm font-black font-mono outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-blue-50/30 text-blue-900 uppercase" />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2">Marca - Modelo</label>
                  <input type="text" name="modelo" value={formData.modelo} onChange={handleChange} placeholder="EJ: JOHN DEERE 5090E (2022)"
                    className="w-full px-3 sm:px-4 py-2 sm:py-2.5 border border-slate-200 rounded text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]" />
                </div>
              </div>

              <div className="mt-4 sm:mt-6 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6 bg-white p-4 sm:p-6 rounded-md border border-slate-200 shadow-sm">
                <div>
                  <label className="block text-[9px] sm:text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2">Uso (Km / Hrs)</label>
                  <input type="number" step="0.01" name="kilometraje" value={formData.kilometraje} onChange={handleChange} placeholder="0.00"
                    className="w-full px-3 sm:px-4 py-2 border border-slate-200 rounded text-sm font-black font-mono outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]" />
                </div>
                <div>
                  <label className="block text-[9px] sm:text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2">Tanque (Lts)</label>
                  <input type="number" step="0.01" name="cant_tanque_comb" value={formData.cant_tanque_comb} onChange={handleChange} placeholder="0.00"
                    className="w-full px-3 sm:px-4 py-2 border border-slate-200 rounded text-sm font-black font-mono outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]" />
                </div>
                <div className="sm:col-span-2 md:col-span-1">
                  <label className="block text-[9px] sm:text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2">Último Mantenimiento</label>
                  <input type="date" name="fecha_ult_mant" value={formData.fecha_ult_mant} onChange={handleChange}
                    className="w-full px-3 sm:px-4 py-2 border border-slate-200 rounded text-xs font-bold outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] text-slate-600 uppercase" />
                </div>
              </div>

              {isEditing && (
                <div className="mt-4 sm:mt-6 bg-blue-50 border border-blue-100 p-4 sm:p-6 rounded-md">
                  <label className="block text-[9px] sm:text-[10px] font-black text-blue-800 uppercase tracking-widest mb-2">Estado de Operatividad Actual</label>
                  <select name="estado" value={formData.estado} onChange={handleChange}
                    className="w-full md:w-2/3 px-3 sm:px-4 py-2 sm:py-2.5 border border-blue-200 rounded-md text-[10px] sm:text-xs font-black uppercase outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 bg-white text-blue-900 shadow-sm cursor-pointer">
                    <option value="DISPONIBLE">🟢 VEHÍCULO DISPONIBLE</option>
                    <option value="OCUPADO">🔵 VEHÍCULO TRABAJANDO (OCUPADO)</option>
                    <option value="MANTENIMIENTO">🔴 EN TALLER / REPARACIÓN</option>
                  </select>
                </div>
              )}

              <div className="mt-6 sm:mt-8 flex flex-col-reverse sm:flex-row justify-end gap-3 pt-4 sm:pt-6 border-t border-slate-200 shrink-0">
                <button type="button" onClick={() => setShowModal(false)}
                  className="w-full sm:w-auto px-4 sm:px-6 py-3 sm:py-2.5 text-[10px] font-black text-slate-500 uppercase tracking-widest hover:bg-slate-200 rounded-md transition-colors text-center">
                  CANCELAR OPERACIÓN
                </button>
                <button type="submit"
                  className="w-full sm:w-auto px-6 sm:px-10 py-3 sm:py-2.5 bg-[#1A5729] text-white text-[10px] font-black uppercase tracking-widest rounded-md shadow-lg hover:bg-[#144320] transition-all flex items-center justify-center gap-2">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                  {isEditing ? 'GUARDAR FICHA' : 'REGISTRAR'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── MODAL HISTORIAL DE MANTENIMIENTO ────────────────────────────────── */}
      {showMantModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-2 sm:p-4 bg-slate-900/70 backdrop-blur-sm">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-3xl flex flex-col max-h-[95vh] border border-slate-300 animate-in zoom-in-95 duration-200">

            {/* Cabecera */}
            <div className="bg-[#1A5729] px-4 sm:px-8 py-4 sm:py-5 flex justify-between items-center text-white shrink-0">
              <div className="flex items-center gap-3">
                <div className="bg-white/20 p-2 rounded-md hidden sm:block">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-sm sm:text-base font-black uppercase tracking-widest">
                    {showMantForm
                      ? (isEditingMant ? 'EDITAR REGISTRO' : 'NUEVO MANTENIMIENTO')
                      : 'HISTORIAL DE MANTENIMIENTO'}
                  </h3>
                  <p className="text-[9px] sm:text-[10px] text-emerald-100 font-bold uppercase mt-0.5 tracking-wider font-mono">
                    {currentMaquina?.placa} — {currentMaquina?.tipo}
                  </p>
                </div>
              </div>
              <button onClick={() => setShowMantModal(false)} className="text-emerald-100 hover:text-white hover:bg-white/10 p-2 rounded-md transition-colors shrink-0">
                <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>

            {/* ── VISTA: LISTADO ─────────────────────────────────────────────── */}
            {!showMantForm && (
              <div className="flex-1 overflow-y-auto custom-scrollbar p-4 sm:p-6 bg-slate-50">

                {/* Barra superior del listado */}
                <div className="flex justify-between items-center mb-4">
                  <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
                    {historial.length} registro{historial.length !== 1 ? 's' : ''} encontrado{historial.length !== 1 ? 's' : ''}
                  </p>
                  <button
                    onClick={openAddMant}
                    className="bg-[#1A5729] hover:bg-[#144320] text-white px-4 py-2 rounded-md font-black text-[10px] uppercase tracking-widest transition-all active:scale-95 shadow-md flex items-center gap-2"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" /></svg>
                    REGISTRAR MANTENIMIENTO
                  </button>
                </div>

                {/* Contenido del listado */}
                {loadingHistorial ? (
                  <div className="flex items-center justify-center py-16 text-slate-400 font-bold uppercase text-[10px] tracking-widest">
                    Cargando historial...
                  </div>
                ) : historial.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-16 gap-3">
                    <div className="bg-slate-100 p-4 rounded-full">
                      <svg className="w-10 h-10 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    </div>
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest text-center">
                      Sin registros de mantenimiento
                    </p>
                    <p className="text-[9px] text-slate-400 uppercase tracking-wider text-center">
                      Presiona "Registrar Mantenimiento" para agregar el primer registro
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col gap-3">
                    {historial.map((record) => (
                      <div key={record.nro_orden} className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex justify-between items-start gap-3">
                          <div className="flex-1 min-w-0">
                            {/* Tipo + estado */}
                            <div className="flex flex-wrap items-center gap-2 mb-2">
                              <span className={`px-2.5 py-1 rounded text-[9px] font-black uppercase tracking-widest ${getMantBadgeStyle(record.tipo_trabajo)}`}>
                                {record.tipo_trabajo.replace('MANTENIMIENTO_', '')}
                              </span>
                              <span className={`px-2.5 py-1 rounded text-[9px] font-black uppercase tracking-widest ${
                                record.estado === 'COMPLETADO' ? 'bg-emerald-50 text-emerald-700' :
                                record.estado === 'PENDIENTE' ? 'bg-yellow-50 text-yellow-700' :
                                'bg-blue-50 text-blue-700'
                              }`}>
                                {record.estado}
                              </span>
                              <span className="text-[9px] font-mono font-bold text-slate-400 uppercase">
                                ORD-{String(record.nro_orden).padStart(4, '0')}
                              </span>
                            </div>
                            {/* Descripción */}
                            <p className="text-xs font-bold text-slate-700 uppercase mb-2 truncate">
                              {record.descripcion}
                            </p>
                            {/* Fechas */}
                            <div className="flex flex-wrap gap-3 text-[9px] font-bold text-slate-400 uppercase tracking-wider">
                              <span className="flex items-center gap-1">
                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                Inicio: {formatDate(record.fecha_inicio)}
                              </span>
                              {record.fecha_fin && (
                                <span className="flex items-center gap-1">
                                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                  Fin: {formatDate(record.fecha_fin)}
                                </span>
                              )}
                              {record.id_empleado && (
                                <span className="flex items-center gap-1">
                                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                                  Técnico ID: {record.id_empleado}
                                </span>
                              )}
                            </div>
                            {/* Observaciones */}
                            {record.observaciones && (
                              <p className="mt-2 text-[9px] text-slate-400 uppercase italic truncate">
                                Obs: {record.observaciones}
                              </p>
                            )}
                          </div>
                          {/* Acciones */}
                          <div className="flex flex-col gap-2 shrink-0">
                            <button onClick={() => openEditMant(record)} className="text-blue-600 hover:text-blue-800 font-black text-[9px] uppercase tracking-widest flex items-center gap-1">
                              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                              Editar
                            </button>
                            <button onClick={() => handleDeleteMant(record.nro_orden)} className="text-red-500 hover:text-red-700 font-black text-[9px] uppercase tracking-widest flex items-center gap-1">
                              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                              Borrar
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ── VISTA: FORMULARIO ──────────────────────────────────────────── */}
            {showMantForm && (
              <form onSubmit={handleMantSubmit} className="flex-1 overflow-y-auto custom-scrollbar p-4 sm:p-6 bg-slate-50">

                {/* Botón volver */}
                <button
                  type="button"
                  onClick={() => setShowMantForm(false)}
                  className="flex items-center gap-2 text-[10px] font-black text-slate-500 uppercase tracking-widest hover:text-slate-800 mb-5 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg>
                  Volver al historial
                </button>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-white p-4 sm:p-6 rounded-md border border-slate-200 shadow-sm">

                  {/* TIPO DE MANTENIMIENTO */}
                  <div>
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Tipo de Mantenimiento *</label>
                    <select required name="tipo_mant" value={mantForm.tipo_mant} onChange={handleMantChange}
                      className="w-full px-3 py-2.5 border border-slate-200 rounded text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white cursor-pointer">
                      <option value="PREVENTIVO">PREVENTIVO</option>
                      <option value="CORRECTIVO">CORRECTIVO</option>
                      <option value="REVISION">REVISIÓN</option>
                      <option value="EMERGENCIA">EMERGENCIA</option>
                    </select>
                  </div>

                  {/* ESTADO */}
                  <div>
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Estado *</label>
                    <select required name="estado" value={mantForm.estado} onChange={handleMantChange}
                      className="w-full px-3 py-2.5 border border-slate-200 rounded text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white cursor-pointer">
                      <option value="COMPLETADO">COMPLETADO</option>
                      <option value="PENDIENTE">PENDIENTE</option>
                      <option value="EN_PROCESO">EN PROCESO</option>
                    </select>
                  </div>

                  {/* FECHA INICIO */}
                  <div>
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Fecha de Inicio *</label>
                    <input required type="date" name="fecha_inicio" value={mantForm.fecha_inicio} onChange={handleMantChange}
                      className="w-full px-3 py-2.5 border border-slate-200 rounded text-xs font-bold outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] text-slate-600" />
                  </div>

                  {/* FECHA FIN */}
                  <div>
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Fecha de Fin</label>
                    <input type="date" name="fecha_fin" value={mantForm.fecha_fin} onChange={handleMantChange}
                      className="w-full px-3 py-2.5 border border-slate-200 rounded text-xs font-bold outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] text-slate-600" />
                  </div>

                  {/* ID EMPLEADO */}
                  <div className="sm:col-span-2">
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">
                      ID del Técnico / Empleado
                      <span className="ml-2 text-slate-400 normal-case font-bold">(opcional)</span>
                    </label>
                    <input type="number" name="id_empleado" value={mantForm.id_empleado} onChange={handleMantChange}
                      placeholder="Ingresa el ID del usuario responsable"
                      className="w-full px-3 py-2.5 border border-slate-200 rounded text-xs font-bold font-mono outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]" />
                  </div>

                  {/* DESCRIPCIÓN */}
                  <div className="sm:col-span-2">
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Descripción del trabajo *</label>
                    <textarea required name="descripcion" value={mantForm.descripcion} onChange={handleMantChange} rows={3}
                      placeholder="Ej: Cambio de aceite de motor, filtros de aire y combustible..."
                      className="w-full px-3 py-2.5 border border-slate-200 rounded text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] resize-none" />
                  </div>

                  {/* OBSERVACIONES */}
                  <div className="sm:col-span-2">
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">
                      Observaciones adicionales
                      <span className="ml-2 text-slate-400 normal-case font-bold">(opcional)</span>
                    </label>
                    <textarea name="observaciones" value={mantForm.observaciones} onChange={handleMantChange} rows={2}
                      placeholder="Ej: Próximo mantenimiento en 500 horas de uso..."
                      className="w-full px-3 py-2.5 border border-slate-200 rounded text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] resize-none" />
                  </div>
                </div>

                {/* Botonera */}
                <div className="mt-6 flex flex-col-reverse sm:flex-row justify-end gap-3 pt-4 border-t border-slate-200">
                  <button type="button" onClick={() => setShowMantForm(false)}
                    className="w-full sm:w-auto px-6 py-2.5 text-[10px] font-black text-slate-500 uppercase tracking-widest hover:bg-slate-200 rounded-md transition-colors text-center">
                    CANCELAR
                  </button>
                  <button type="submit"
                    className="w-full sm:w-auto px-8 py-2.5 bg-[#1A5729] text-white text-[10px] font-black uppercase tracking-widest rounded-md shadow-lg hover:bg-[#144320] transition-all flex items-center justify-center gap-2">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                    {isEditingMant ? 'GUARDAR CAMBIOS' : 'REGISTRAR'}
                  </button>
                </div>
              </form>
            )}

          </div>
        </div>
      )}

    </div>
  );
}
