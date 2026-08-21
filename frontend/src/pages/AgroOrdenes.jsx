import { useState, useEffect, useRef } from 'react';
import * as XLSX from 'xlsx';
import { useAuthStore } from '../store/auth_store';

const API_URL = import.meta.env.VITE_API_URL;

export default function AgroOrdenes() {
  const token = useAuthStore((state) => state.token);
  const userRole = useAuthStore((state) => state.user?.id_rol || state.role);
  const currentUserId = useAuthStore((state) => state.user?.id_usuario);
  const isBoss = Number(userRole) === 1 || Number(userRole) === 2;

  const [ordenes, setOrdenes] = useState([]);
  const [empleados, setEmpleados] = useState([]);
  const [campanias, setCampanias] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  // ESTADOS PARA FILTRAR REPORTE POR RANGO DE FECHAS
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');

  // ESTADOS DE MODALES
  const [showModal, setShowModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false); 

  const [currentOrder, setCurrentOrder] = useState(null);
  const [empleadoId, setEmpleadoId] = useState('');

  // ESTADOS PARA EDICIÓN DEL REPORTE
  const [isEditingReport, setIsEditingReport] = useState(false);
  const [isSubmittingReport, setIsSubmittingReport] = useState(false);
  const [reporteForm, setReporteForm] = useState({
    estado: 'PENDIENTE',
    reporte_texto: '',
    url_imagen: null,
    url_audio: null
  });

  const isFetching = useRef(false);

  // --- REFERENCIAS Y ESTADOS PARA MEDIA (CÁMARA Y MICRÓFONO) ---
  const videoRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [isRecording, setIsRecording] = useState(false);

  const initialForm = {
    tipo_trabajo: '',
    fecha_inicio: '',
    fecha_fin: '',
    id_campana: '',
  };

  const [formData, setFormData] = useState(initialForm);

  const fetchOrdenes = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/get-ordenes`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const result = await response.json();
      if (result.success) {
        setOrdenes(result.list_ordenes || []);
      }
    } catch (error) {
      console.error('Error en órdenes:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchEmpleados = async () => {
    try {
      const response = await fetch(`${API_URL}/get-empleados`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const result = await response.json();
      if (result.success) setEmpleados(result.list_empleados || []);
    } catch (error) {
      console.error('Error en empleados:', error);
    }
  };

  const fetchCampanias = async () => {
    try {
      const response = await fetch(`${API_URL}/get-campanias`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const result = await response.json();
      if (result.success) setCampanias(result.list_campanias || []);
    } catch (error) {
      console.error('Error de red al cargar campañas:', error);
    }
  };

  useEffect(() => {
    if (!token || isFetching.current) return;
    const cargarDatosProtegidos = async () => {
      isFetching.current = true;
      await fetchOrdenes();
      if (isBoss) {
        await fetchEmpleados();
        await fetchCampanias();
      }
      isFetching.current = false;
    };
    cargarDatosProtegidos();
  }, [token, isBoss]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const openAddModal = () => {
    if (!isBoss) return;
    setFormData(initialForm);
    setShowModal(true);
  };

  const openAssignModal = (orden) => {
    if (!isBoss) return;
    setCurrentOrder(orden);
    setEmpleadoId(orden.id_empleado || '');
    setShowAssignModal(true);
  };

  const openReportModal = (orden) => {
    setCurrentOrder(orden);
    setReporteForm({
      estado: orden.estado || 'PENDIENTE',
      reporte_texto: orden.reporte_texto || '',
      url_imagen: null, 
      url_audio: null  
    });
    setIsEditingReport(false);
    stopCamera(); 
    setShowReportModal(true);
  };

  // ==========================================================
  // MANEJO DE ARCHIVOS (MODIFICADO PARA SOPORTAR VIDEO)
  // ==========================================================
  const handleFileUpload = (e, fieldName) => {
    const file = e.target.files[0];
    if (!file) return;

    // Aumentamos a 20MB para permitir videos cortos
    if (file.size > 20 * 1024 * 1024) {
      alert("El archivo es demasiado grande. Máximo 20MB.");
      e.target.value = null;
      return;
    }

    const reader = new FileReader();
    reader.onloadend = () => {
      // Ahora guardamos el string completo (incluye si es data:video/mp4 o data:image/jpeg)
      const fullBase64 = reader.result;
      setReporteForm(prev => ({ ...prev, [fieldName]: fullBase64 }));
    };
    reader.readAsDataURL(file);
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsCameraActive(true);
    } catch (err) {
      alert('Error: No se pudo acceder a la cámara. Revisa los permisos de tu navegador.');
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      videoRef.current.srcObject.getTracks().forEach(track => track.stop());
    }
    setIsCameraActive(false);
  };

  const takePhoto = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    canvas.getContext('2d').drawImage(videoRef.current, 0, 0);
    
    // Guardamos con el prefijo completo
    const fullBase64 = canvas.toDataURL('image/jpeg');
    setReporteForm(prev => ({ ...prev, url_imagen: fullBase64 }));
    stopCamera();
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const reader = new FileReader();
        reader.onloadend = () => {
          const fullBase64 = reader.result;
          setReporteForm(prev => ({ ...prev, url_audio: fullBase64 }));
        };
        reader.readAsDataURL(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      alert('Error: No se pudo acceder al micrófono. Revisa los permisos.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // ==========================================================
  // PETICIONES A LA API
  // ==========================================================
  const handleSubmit = async (e) => {
    e.preventDefault();
    const payload = {
      ...formData,
      tipo_trabajo: formData.tipo_trabajo.toUpperCase(),
      fecha_fin: formData.fecha_fin ? formData.fecha_fin : null,
      id_campana: parseInt(formData.id_campana),
    };

    try {
      const response = await fetch(`${API_URL}/add-orden`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      if (result.success) {
        setShowModal(false);
        fetchOrdenes();
      } else {
        alert(`Atención: ${result.message}`);
      }
    } catch (error) {
      alert('Error de comunicación con el servidor.');
    }
  };

  const handleAssign = async (e) => {
    e.preventDefault();
    if (!empleadoId) return alert('Seleccione un empleado.');

    try {
      const response = await fetch(`${API_URL}/assign-responsible`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          nro_orden: currentOrder.nro_orden,
          id_empleado: parseInt(empleadoId),
        }),
      });
      const result = await response.json();
      if (result.success) {
        setShowAssignModal(false);
        fetchOrdenes();
      } else {
        alert(`Atención: ${result.message}`);
      }
    } catch (error) {
      alert('Error de comunicación con el servidor.');
    }
  };

  const handleUpdateReport = async (e) => {
    e.preventDefault();
    setIsSubmittingReport(true);
    try {
      const payload = {
        nro_orden: currentOrder.nro_orden,
        estado: reporteForm.estado,
        reporte_texto: reporteForm.reporte_texto,
      };
      
      // Enviamos el Base64 completo (con todo y prefijo data:video/ o data:image/)
      if (reporteForm.url_imagen) payload.url_imagen = reporteForm.url_imagen;
      if (reporteForm.url_audio) payload.url_audio = reporteForm.url_audio;

      const response = await fetch(`${API_URL}/update-mi-orden`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      if (result.success) {
        alert("Reporte actualizado correctamente.");
        setShowReportModal(false);
        fetchOrdenes();
      } else {
        alert(`Atención: ${result.message}`);
      }
    } catch (error) {
      alert('Error de comunicación con el servidor.');
    } finally {
      setIsSubmittingReport(false);
    }
  };

  const handleDelete = async (id, tipo) => {
    if (!isBoss) return;
    if (!window.confirm(`¿Está seguro de eliminar la orden de ${tipo}?`)) return;

    try {
      const response = await fetch(`${API_URL}/delete-orden`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ nro_orden: id }),
      });
      const result = await response.json();
      if (result.success) {
        fetchOrdenes();
      } else {
        alert(result.message);
      }
    } catch (error) {
      alert('Error al procesar la baja.');
    }
  };

  const normalizarFecha = (fecha) => {
    if (!fecha) return '';
    return String(fecha).split('T')[0];
  };

  const filtered = ordenes.filter((o) => {
    const textoBusqueda = searchTerm.toLowerCase();
    const fechaOrden = normalizarFecha(o.fecha_inicio);
    const coincideBusqueda =
      o.tipo_trabajo?.toLowerCase().includes(textoBusqueda) ||
      o.empleado_username?.toLowerCase().includes(textoBusqueda) ||
      o.estado?.toLowerCase().includes(textoBusqueda) ||
      String(o.nro_orden || '').includes(textoBusqueda);

    const cumpleFechaDesde = !fechaDesde || (fechaOrden && fechaOrden >= fechaDesde);
    const cumpleFechaHasta = !fechaHasta || (fechaOrden && fechaOrden <= fechaHasta);

    return coincideBusqueda && cumpleFechaDesde && cumpleFechaHasta;
  });

  const stats = {
    total: filtered.length,
    pendientes: filtered.filter((o) => o.estado === 'PENDIENTE').length,
    enProceso: filtered.filter((o) => o.estado === 'EN PROCESO').length,
    finalizadas: filtered.filter((o) => o.estado === 'FINALIZADA').length,
  };

  const prepararDatosReporte = () => {
    return filtered.map((o) => ({
      'Nro Orden': `ORD-${String(o.nro_orden).padStart(4, '0')}`,
      Actividad: o.tipo_trabajo || '',
      'Campaña ID': o.id_campana || '',
      'Fecha Inicio': normalizarFecha(o.fecha_inicio),
      'Fecha Fin': normalizarFecha(o.fecha_fin) || 'N/A',
      Estado: o.estado || '',
      Empleado: o.empleado_username || 'SIN ASIGNAR',
      Supervisor: o.supervisor_username || '',
      'Reporte del Empleado': o.reporte_texto || 'SIN REPORTE',
      'Media Adjunta': o.url_imagen ? (o.url_imagen.includes('video') ? 'VIDEO CARGADO' : 'FOTO CARGADA') : 'SIN MEDIA',
      'Audio': o.url_audio ? 'AUDIO CARGADO' : 'SIN AUDIO'
    }));
  };

  const validarRangoFechas = () => {
    if (fechaDesde && fechaHasta && fechaDesde > fechaHasta) {
      alert('La fecha desde no puede ser mayor que la fecha hasta.');
      return false;
    }
    if (filtered.length === 0) {
      alert('No hay datos para exportar con los filtros actuales.');
      return false;
    }
    return true;
  };

  const generarNombreArchivo = (extension) => {
    const desde = fechaDesde || 'inicio';
    const hasta = fechaHasta || 'fin';
    return `reporte_ordenes_${desde}_${hasta}.${extension}`;
  };

  const exportarCSV = () => {
    if (!validarRangoFechas()) return;
    const datos = prepararDatosReporte();
    const headers = Object.keys(datos[0]);
    const escapeCSV = (value) => {
      const valor = String(value ?? '').replace(/"/g, '""');
      return `"${valor}"`;
    };
    const csvRows = [
      headers.map(escapeCSV).join(','),
      ...datos.map((row) => headers.map((header) => escapeCSV(row[header])).join(',')),
    ];
    const csvContent = '\ufeff' + csvRows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = generarNombreArchivo('csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const exportarXLSX = () => {
    if (!validarRangoFechas()) return;
    const datos = prepararDatosReporte();
    const worksheet = XLSX.utils.json_to_sheet(datos);
    worksheet['!cols'] = [
      { wch: 14 }, { wch: 25 }, { wch: 12 }, { wch: 14 }, { wch: 14 }, 
      { wch: 16 }, { wch: 22 }, { wch: 22 }, { wch: 40 }, { wch: 18 }, { wch: 18 }
    ];
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Órdenes');
    XLSX.writeFile(workbook, generarNombreArchivo('xlsx'));
  };

  const limpiarFiltrosReporte = () => {
    setFechaDesde('');
    setFechaHasta('');
  };

  return (
    <div className="p-4 md:p-8 animate-in fade-in duration-500 bg-slate-50 min-h-screen max-w-[100vw] overflow-x-hidden">
      
      {/* CABECERA */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 md:mb-8 gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-black text-slate-800 tracking-tight flex items-center gap-3">
            <div className="w-2 h-6 md:h-8 bg-[#1A5729]"></div>
            ÓRDENES DE TRABAJO
          </h1>
          <p className="text-[9px] md:text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mt-1 ml-5">
            Planificación y Asignación de Actividades
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
              type="text"
              placeholder="BUSCAR ORDEN..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 border border-slate-200 rounded-md text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white shadow-sm"
            />
          </div>

          {isBoss && (
            <button
              onClick={openAddModal}
              className="bg-[#1A5729] hover:bg-[#144320] text-white px-6 py-2.5 rounded-md font-black text-[10px] uppercase tracking-widest transition-all active:scale-95 shadow-md flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              CREAR ORDEN
            </button>
          )}
        </div>
      </div>

      {/* FILTROS Y EXPORTACIÓN DE REPORTES */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-4 md:p-5 mb-6 md:mb-8">
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
          <div>
            <h2 className="text-xs font-black text-slate-700 uppercase tracking-widest flex items-center gap-2">
              <span className="w-1.5 h-5 bg-[#1A5729] rounded-sm"></span>
              Exportar reportes
            </h2>
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-1">
              Filtra por fecha de inicio antes de exportar
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 w-full lg:w-auto">
            <div>
              <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Desde</label>
              <input type="date" value={fechaDesde} onChange={(e) => setFechaDesde(e.target.value)} className="w-full px-3 py-2.5 border border-slate-200 rounded-md text-xs font-bold text-slate-700 outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white shadow-sm" />
            </div>
            <div>
              <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Hasta</label>
              <input type="date" value={fechaHasta} onChange={(e) => setFechaHasta(e.target.value)} className="w-full px-3 py-2.5 border border-slate-200 rounded-md text-xs font-bold text-slate-700 outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white shadow-sm" />
            </div>
            <button type="button" onClick={limpiarFiltrosReporte} className="self-end px-4 py-2.5 border border-slate-200 text-slate-500 hover:bg-slate-100 rounded-md font-black text-[10px] uppercase tracking-widest transition-all active:scale-95">
              Limpiar
            </button>
            <button type="button" onClick={exportarCSV} className="self-end bg-[#C5E5F9] hover:bg-[#b4daf3] text-[#1D512E] px-4 py-2.5 rounded-md font-black text-[10px] uppercase tracking-widest transition-all active:scale-95 shadow-sm flex items-center justify-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              CSV
            </button>
            <button type="button" onClick={exportarXLSX} className="self-end bg-[#1A5729] hover:bg-[#144320] text-white px-4 py-2.5 rounded-md font-black text-[10px] uppercase tracking-widest transition-all active:scale-95 shadow-md flex items-center justify-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              XLSX
            </button>
          </div>
        </div>
      </div>

      {/* DASHBOARD DE KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-6 md:mb-8">
        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-slate-100 p-2 md:p-3 rounded-md text-slate-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Total Órdenes</p>
            <p className="text-lg md:text-xl font-black text-slate-800">{stats.total}</p>
          </div>
        </div>

        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-amber-50 p-2 md:p-3 rounded-md text-amber-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Pendientes</p>
            <p className="text-lg md:text-xl font-black text-amber-700">{stats.pendientes}</p>
          </div>
        </div>

        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-blue-50 p-2 md:p-3 rounded-md text-blue-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">En Proceso</p>
            <p className="text-lg md:text-xl font-black text-blue-700">{stats.enProceso}</p>
          </div>
        </div>

        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-emerald-50 p-2 md:p-3 rounded-md text-emerald-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Finalizadas</p>
            <p className="text-lg md:text-xl font-black text-emerald-700">{stats.finalizadas}</p>
          </div>
        </div>
      </div>

      {/* TABLA PRINCIPAL */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden w-full">
        <div className="overflow-x-auto w-full custom-scrollbar">
          <table className="w-full min-w-[800px] text-left border-collapse">
            <thead>
              <tr className="bg-slate-100 border-b border-slate-200 text-[10px] font-black text-slate-500 uppercase tracking-widest">
                <th className="px-6 py-4">Nro</th>
                <th className="px-6 py-4">Actividad</th>
                <th className="px-6 py-4">Fechas</th>
                <th className="px-6 py-4">Estado</th>
                <th className="px-6 py-4">Personal</th>
                <th className="px-6 py-4 text-center">Evidencia / Reporte</th>
                {isBoss && <th className="px-6 py-4 text-center">Acciones</th>}
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={isBoss ? '7' : '6'} className="text-center py-20 text-slate-400 font-bold uppercase text-[10px] tracking-widest">Cargando Órdenes...</td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={isBoss ? '7' : '6'} className="text-center py-20 text-slate-400 font-bold uppercase text-[10px] tracking-widest">No hay órdenes registradas</td>
                </tr>
              ) : (
                filtered.map((o) => (
                  <tr key={o.nro_orden} className="hover:bg-slate-50 transition-colors group">
                    <td className="px-6 py-4 font-mono text-[10px] font-bold text-slate-400">
                      ORD-{String(o.nro_orden).padStart(4, '0')}
                    </td>

                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="bg-[#1A5729]/10 p-2 rounded-md text-[#1A5729] shrink-0">
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        </div>
                        <div className="min-w-0">
                          <div className="font-black text-slate-800 text-xs uppercase truncate">{o.tipo_trabajo}</div>
                          <div className="text-[9px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">Campaña ID: {o.id_campana}</div>
                        </div>
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1 text-[10px] font-bold text-slate-500 uppercase whitespace-nowrap">
                        <div className="flex items-center gap-1.5 text-slate-700">
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                          Inicio: {o.fecha_inicio ? new Date(o.fecha_inicio).toLocaleDateString() : 'N/A'}
                        </div>
                        {o.fecha_fin && (
                          <div className="flex items-center gap-1.5 text-slate-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-300"></span>
                            Fin: {new Date(o.fecha_fin).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded text-[9px] font-black uppercase tracking-widest ${
                          o.estado === 'FINALIZADA' ? 'bg-emerald-100 text-emerald-800' : o.estado === 'EN PROCESO' ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {o.estado}
                      </span>
                    </td>

                    <td className="px-6 py-4">
                      <div className="text-[10px]">
                        <div className="font-bold text-slate-700"><span className="text-slate-400 font-normal">Emp:</span> {o.empleado_username || 'SIN ASIGNAR'}</div>
                        <div className="text-slate-500 mt-1"><span className="text-slate-400 font-normal">Sup:</span> {o.supervisor_username}</div>
                      </div>
                    </td>

                    {/* BOTÓN VER/EDITAR REPORTE (MODIFICADO PARA PERMITIR ADMINS) */}
                    <td className="px-6 py-4">
                      <div className="flex justify-center">
                        <button 
                          onClick={() => openReportModal(o)}
                          className="flex items-center justify-center gap-2 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100 transition-colors"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                          <span className="text-[10px] font-black uppercase tracking-tighter">
                            {(o.id_empleado === currentUserId || isBoss) ? 'Editar/Ver' : 'Ver Evidencia'}
                          </span>
                        </button>
                      </div>
                    </td>

                    {isBoss && (
                      <td className="px-6 py-4 text-center">
                        <div className="flex justify-center gap-3">
                          <button onClick={() => openAssignModal(o)} className="text-[#1A5729] hover:text-[#0f3418] font-black text-[9px] uppercase tracking-widest flex flex-col items-center gap-1 transition-colors">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" /></svg>
                            Asignar
                          </button>

                          <button onClick={() => handleDelete(o.nro_orden, o.tipo_trabajo)} className="text-red-500 hover:text-red-700 font-black text-[9px] uppercase tracking-widest flex flex-col items-center gap-1 transition-colors">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                            Borrar
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* MODAL MULTIPROPÓSITO: VER O EDITAR REPORTE Y EVIDENCIA                      */}
      {/* ========================================================================= */}
      {showReportModal && currentOrder && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl overflow-hidden animate-in zoom-in-95 flex flex-col max-h-[95vh]">
            
            <div className="bg-[#1A5729] px-6 py-4 flex justify-between items-center text-white shrink-0">
              <div>
                <h3 className="text-sm font-black uppercase tracking-widest">
                  {isEditingReport ? 'ACTUALIZAR REPORTE DE TRABAJO' : 'VISOR DE EVIDENCIA DE CAMPO'}
                </h3>
                <p className="text-[10px] text-emerald-100 font-bold uppercase mt-0.5">
                  ORD-{String(currentOrder.nro_orden).padStart(4, '0')} - {currentOrder.tipo_trabajo}
                </p>
              </div>
              <div className="flex gap-2">
                {/* CONDICIÓN MODIFICADA AQUÍ: isBoss o empleado dueño */}
                {(currentOrder.id_empleado === currentUserId || isBoss) && !isEditingReport && (
                  <button 
                    onClick={() => setIsEditingReport(true)} 
                    className="bg-white/20 hover:bg-white/30 px-3 py-1.5 rounded text-[10px] font-black tracking-widest transition-colors flex items-center gap-1"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                    Editar
                  </button>
                )}
                <button 
                  onClick={() => { 
                    setShowReportModal(false); 
                    stopCamera(); 
                  }} 
                  className="hover:bg-white/10 p-2 rounded-full transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
            </div>
            
            <div className="p-6 md:p-8 overflow-y-auto custom-scrollbar bg-slate-50 flex-1">
              {isEditingReport ? (
                /* --- MODO EDICIÓN --- */
                <form id="formReporte" onSubmit={handleUpdateReport} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  
                  {/* Columna Izquierda: Textos y Estado */}
                  <div className="space-y-4">
                    <div>
                      <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Estado del Trabajo *</label>
                      <select 
                        required
                        value={reporteForm.estado}
                        onChange={(e) => setReporteForm({...reporteForm, estado: e.target.value})}
                        className="w-full px-3 py-2.5 border border-slate-300 rounded text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white"
                      >
                        <option value="PENDIENTE">Pendiente</option>
                        <option value="EN PROCESO">En Proceso</option>
                        <option value="FINALIZADA">Finalizada</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Reporte Escrito (Opcional)</label>
                      <textarea 
                        rows="5"
                        value={reporteForm.reporte_texto}
                        onChange={(e) => setReporteForm({...reporteForm, reporte_texto: e.target.value})}
                        placeholder="Describe las tareas realizadas..."
                        className="w-full p-3 border border-slate-300 rounded text-sm font-medium outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white resize-none"
                      />
                    </div>
                  </div>

                  {/* Columna Derecha: Carga de Archivos y Captura Media */}
                  <div className="space-y-6">
                    
                    {/* Input Imagen / Video / Cámara */}
                    <div className="bg-white p-4 border border-slate-200 rounded-lg shadow-sm">
                      <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                        Evidencia (Foto o Video)
                      </label>
                      
                      {isCameraActive ? (
                        <div className="flex flex-col gap-2">
                          <video ref={videoRef} autoPlay playsInline className="w-full rounded-md bg-black" />
                          <div className="flex justify-between gap-2 mt-2">
                            <button type="button" onClick={takePhoto} className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white py-2 text-xs font-bold uppercase rounded shadow transition-colors">
                              Tomar Foto
                            </button>
                            <button type="button" onClick={stopCamera} className="flex-1 bg-slate-300 hover:bg-slate-400 text-slate-800 py-2 text-xs font-bold uppercase rounded transition-colors">
                              Cancelar
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex flex-col gap-3">
                          {/* SOPORTE DE VIDEO AÑADIDO AL ACCEPT */}
                          <input 
                            type="file" 
                            accept="image/*,video/*"
                            onChange={(e) => handleFileUpload(e, 'url_imagen')}
                            className="block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-bold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100 cursor-pointer"
                          />
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">O también</span>
                            <button 
                              type="button" 
                              onClick={startCamera} 
                              className="bg-emerald-100 hover:bg-emerald-200 text-emerald-800 text-xs font-bold py-2 px-4 rounded border border-emerald-300 flex items-center gap-2 transition-colors"
                            >
                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                              Usar Cámara Web
                            </button>
                          </div>
                        </div>
                      )}

                      {(reporteForm.url_imagen || currentOrder.url_imagen) && !isCameraActive && (
                         <div className="mt-4 border-t border-slate-100 pt-3">
                           <p className="text-[10px] text-emerald-600 font-bold uppercase tracking-wider">✓ Archivo Listo</p>
                           {/* RENDERIZADO DINÁMICO: VIDEO O IMAGEN */}
                           {reporteForm.url_imagen && reporteForm.url_imagen.includes('video') ? (
                             <video 
                               src={reporteForm.url_imagen} 
                               controls 
                               className="mt-2 w-full max-h-48 object-cover rounded shadow border border-slate-200" 
                             />
                           ) : (
                             reporteForm.url_imagen && (
                               <img 
                                 src={reporteForm.url_imagen.startsWith('data:') ? reporteForm.url_imagen : `data:image/jpeg;base64,${reporteForm.url_imagen}`} 
                                 alt="Preview" 
                                 className="mt-2 w-24 h-24 object-cover rounded shadow border border-slate-200" 
                               />
                             )
                           )}
                         </div>
                      )}
                    </div>

                    {/* Input Audio / Micrófono */}
                    <div className="bg-white p-4 border border-slate-200 rounded-lg shadow-sm">
                      <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>
                        Nota de Voz
                      </label>
                      
                      <div className="flex flex-col gap-3">
                        <input 
                          type="file" 
                          accept="audio/*"
                          onChange={(e) => handleFileUpload(e, 'url_audio')}
                          className="block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-bold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
                        />
                        
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">O también</span>
                          {!isRecording ? (
                            <button 
                              type="button" 
                              onClick={startRecording} 
                              className="bg-blue-100 hover:bg-blue-200 text-blue-800 text-xs font-bold py-2 px-4 rounded border border-blue-300 flex items-center gap-2 transition-colors"
                            >
                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>
                              Grabar Audio
                            </button>
                          ) : (
                            <button 
                              type="button" 
                              onClick={stopRecording} 
                              className="bg-red-500 hover:bg-red-600 text-white text-xs font-bold py-2 px-4 rounded shadow flex items-center gap-2 animate-pulse"
                            >
                              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" /></svg>
                              Detener y Guardar
                            </button>
                          )}
                        </div>
                      </div>

                      {(reporteForm.url_audio || currentOrder.url_audio) && !isRecording && (
                         <div className="mt-4 border-t border-slate-100 pt-3">
                           <p className="text-[10px] text-blue-600 font-bold uppercase tracking-wider">✓ Audio Listo</p>
                           {reporteForm.url_audio && (
                             <audio controls className="w-full h-10 mt-2 rounded outline-none">
                               <source src={reporteForm.url_audio.startsWith('data:') ? reporteForm.url_audio : `data:audio/webm;base64,${reporteForm.url_audio}`} />
                             </audio>
                           )}
                         </div>
                      )}
                    </div>
                  </div>

                </form>
              ) : (
                /* --- MODO SOLO LECTURA --- */
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div>
                    <label className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">Reporte Escrito</label>
                    <div className="bg-white p-4 rounded-lg border border-slate-200 min-h-[120px] shadow-sm">
                      <p className="text-sm text-slate-700 leading-relaxed font-medium italic">
                        {currentOrder.reporte_texto || "El empleado no proporcionó un reporte escrito."}
                      </p>
                    </div>

                    {/* MOSTRAR AUDIO SI EXISTE */}
                    {currentOrder.url_audio && (
                      <div className="mt-6">
                        <label className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-2 flex items-center gap-1">
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" /></svg>
                          Audio del Empleado
                        </label>
                        <audio controls className="w-full h-10 rounded-md outline-none border border-slate-200">
                          <source src={currentOrder.url_audio.startsWith('data:') ? currentOrder.url_audio : `data:audio/webm;base64,${currentOrder.url_audio}`} />
                          Tu navegador no soporta el reproductor.
                        </audio>
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">Evidencia (Foto/Video)</label>
                    {currentOrder.url_imagen ? (
                      <div className="rounded-lg overflow-hidden border border-slate-200 shadow-sm bg-white flex items-center justify-center p-1">
                        {/* RENDERIZADO DINÁMICO EN LECTURA: VIDEO O IMAGEN */}
                        {currentOrder.url_imagen.includes('video') ? (
                          <video 
                            src={currentOrder.url_imagen} 
                            controls 
                            className="w-full max-h-[300px] rounded object-cover" 
                          />
                        ) : (
                          <img 
                            src={currentOrder.url_imagen.startsWith('data:') ? currentOrder.url_imagen : `data:image/jpeg;base64,${currentOrder.url_imagen}`} 
                            alt="Evidencia del Trabajo" 
                            className="w-full h-auto object-cover rounded max-h-[300px]"
                          />
                        )}
                      </div>
                    ) : (
                      <div className="h-[200px] bg-slate-100/50 rounded-lg border-2 border-dashed border-slate-200 flex flex-col items-center justify-center text-slate-400">
                        <svg className="w-12 h-12 mb-2 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                        <span className="text-[10px] font-bold uppercase tracking-wider">Sin archivo adjunto</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
            
            {/* FOOTER DEL MODAL */}
            <div className="bg-white px-6 py-4 border-t border-slate-200 flex justify-end gap-3 shrink-0 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
              {isEditingReport ? (
                <>
                  <button type="button" onClick={() => { setIsEditingReport(false); stopCamera(); }} className="px-6 py-2.5 bg-slate-100 text-slate-600 hover:bg-slate-200 text-[10px] font-black uppercase tracking-widest rounded transition-all">Cancelar Edición</button>
                  <button type="submit" form="formReporte" disabled={isSubmittingReport} className="px-6 py-2.5 bg-[#1A5729] text-white text-[10px] font-black uppercase tracking-widest rounded shadow-md hover:bg-[#144320] disabled:bg-slate-400 transition-all">
                    {isSubmittingReport ? 'GUARDANDO...' : 'GUARDAR CAMBIOS'}
                  </button>
                </>
              ) : (
                <button onClick={() => setShowReportModal(false)} className="px-6 py-2.5 bg-slate-800 text-white text-[10px] font-black uppercase tracking-widest rounded shadow-md hover:bg-slate-700 transition-all">Cerrar Vista</button>
              )}
            </div>

          </div>
        </div>
      )}

      {/* MODAL 1: CREAR ORDEN */}
      {showModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="bg-gradient-to-r from-[#1A5729] to-[#247638] px-6 py-5 flex justify-between items-center text-white">
              <div>
                <h3 className="text-sm font-black uppercase tracking-widest">NUEVA ORDEN DE TRABAJO</h3>
                <p className="text-[10px] text-emerald-100 font-bold uppercase mt-1">Planificación Inicial</p>
              </div>
              <button onClick={() => setShowModal(false)} className="hover:bg-white/20 p-2 rounded-full transition-colors">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 bg-slate-50">
              <div className="space-y-5">
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Actividad / Tarea *</label>
                  <select required name="tipo_trabajo" value={formData.tipo_trabajo} onChange={handleChange} className="w-full px-4 py-3 border border-slate-300 rounded-lg text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-2 focus:ring-[#1A5729]/20 bg-white transition-all shadow-sm">
                    <option value="" disabled>-- SELECCIONE ACTIVIDAD --</option>
                    <option value="SIEMBRA">SIEMBRA</option>
                    <option value="FUMIGACION">FUMIGACIÓN</option>
                    <option value="COSECHA">COSECHA</option>
                    <option value="PREPARACION_SUELO">PREPARACIÓN DE SUELO</option>
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Fecha Inicio *</label>
                    <input type="date" required name="fecha_inicio" value={formData.fecha_inicio} onChange={handleChange} className="w-full px-4 py-3 border border-slate-300 rounded-lg text-xs font-bold uppercase text-slate-700 outline-none focus:border-[#1A5729] focus:ring-2 focus:ring-[#1A5729]/20 transition-all shadow-sm" />
                  </div>
                  <div>
                    <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Fecha Fin (Aprox)</label>
                    <input type="date" name="fecha_fin" value={formData.fecha_fin} onChange={handleChange} className="w-full px-4 py-3 border border-slate-300 rounded-lg text-xs font-bold uppercase text-slate-700 outline-none focus:border-[#1A5729] focus:ring-2 focus:ring-[#1A5729]/20 transition-all shadow-sm" />
                  </div>
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Campaña Agrícola *</label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <svg className="w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    </div>
                    <select required name="id_campana" value={formData.id_campana} onChange={handleChange} className="w-full pl-10 pr-10 py-3 border border-slate-300 rounded-lg text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-2 focus:ring-[#1A5729]/20 bg-white cursor-pointer transition-all shadow-sm appearance-none">
                      <option value="" disabled>-- SELECCIONE CAMPAÑA --</option>
                      {campanias.map((camp) => (
                        <option key={camp.id_campana} value={camp.id_campana}>{camp.nombre_campana} (Lote #{camp.nro_lote})</option>
                      ))}
                    </select>
                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                      <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                  </div>
                </div>
              </div>
              <div className="mt-8 flex justify-end gap-3 pt-5 border-t border-slate-200">
                <button type="button" onClick={() => setShowModal(false)} className="px-6 py-2.5 text-xs font-bold text-slate-500 uppercase tracking-widest hover:bg-slate-200 rounded-lg transition-colors">Cancelar</button>
                <button type="submit" className="px-6 py-2.5 bg-[#1A5729] text-white text-xs font-bold uppercase tracking-widest rounded-lg shadow-md hover:bg-[#144320] transition-colors">CREAR ORDEN</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: ASIGNAR RESPONSABLE */}
      {showAssignModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="bg-gradient-to-r from-blue-800 to-blue-600 px-6 py-5 flex justify-between items-center text-white">
              <div>
                <h3 className="text-sm font-black uppercase tracking-widest">ASIGNAR PERSONAL</h3>
                <p className="text-[10px] text-blue-200 font-bold uppercase mt-1">Orden #{String(currentOrder?.nro_orden).padStart(4, '0')}</p>
              </div>
              <button onClick={() => setShowAssignModal(false)} className="hover:bg-white/20 p-2 rounded-full transition-colors">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
            <form onSubmit={handleAssign} className="p-6 bg-slate-50">
              <div className="mb-6 bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-start gap-4">
                <div className="bg-blue-50 text-blue-600 p-2.5 rounded-lg shrink-0">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M21 13.255A23.931 23.931 0 01112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                </div>
                <div>
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Actividad Requerida</p>
                  <p className="font-black text-slate-800 text-sm uppercase">{currentOrder?.tipo_trabajo}</p>
                  <p className="text-[11px] text-slate-500 font-bold mt-1">Campaña ID: {currentOrder?.id_campana}</p>
                </div>
              </div>
              <div>
                <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Seleccione al Personal *</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                  </div>
                  <select required value={empleadoId} onChange={(e) => setEmpleadoId(e.target.value)} className="w-full pl-10 pr-10 py-3 border border-slate-300 rounded-lg text-xs font-bold uppercase outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 bg-white cursor-pointer transition-all shadow-sm appearance-none">
                    <option value="" disabled>-- DESPLIEGUE PARA SELECCIONAR --</option>
                    {empleados.map((emp) => (
                      <option key={emp.id_usuario} value={emp.id_usuario}>{emp.user_name} - {emp.nombre_razon_social}</option>
                    ))}
                  </select>
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
                  </div>
                </div>
                <p className="text-[9px] text-slate-400 mt-2 font-bold tracking-wide">* Mostrando únicamente usuarios con Rol Operativo.</p>
              </div>
              <div className="mt-8 flex justify-end gap-3 pt-5 border-t border-slate-200">
                <button type="button" onClick={() => setShowAssignModal(false)} className="px-6 py-2.5 text-xs font-bold text-slate-500 uppercase tracking-widest hover:bg-slate-200 rounded-lg transition-colors">Cancelar</button>
                <button type="submit" className="px-6 py-2.5 bg-blue-700 text-white text-xs font-bold uppercase tracking-widest rounded-lg shadow-md hover:bg-blue-800 transition-colors">GUARDAR ASIGNACIÓN</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}