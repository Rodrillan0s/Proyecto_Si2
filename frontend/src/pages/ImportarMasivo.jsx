import { useState, useRef } from 'react';
import * as XLSX from 'xlsx';
import { useAuthStore } from '../store/auth_store';

// Configuración centralizada mapeada al 100% con los DDL y controladores del Backend
const CONFIG_ENTIDADES = {
  USUARIOS: {
    label: 'Usuarios / Personal',
    endpoint: '/api/import-users',
    columnas: [
      { key: 'user_name', label: 'Username' },
      { key: 'documento_identidad', label: 'C.I. / Doc' },
      { key: 'nombre_razon_social', label: 'Nombre Completo' },
      { key: 'correo', label: 'Correo Electrónico' },
      { key: 'telefono', label: 'Teléfono' },
      { key: 'password', label: 'Contraseña Inicial' },
      { key: 'id_rol', label: 'ID Rol' }
    ],
    ejemploPlantilla: [
      {
        user_name: 'm_andres',
        documento_identidad: '1234567',
        nombre_razon_social: 'MIGUEL ANDRES AUAD',
        correo: 'miguel@agroenlace.com',
        telefono: '77300000',
        password: 'password2026',
        id_rol: 3,
        direccion: 'SANTA CRUZ - BOLIVIA'
      }
    ]
  },
  BODEGA: {
    label: 'Bodega (Productos/Insumos)',
    endpoint: '/api/bodega/import',
    columnas: [
      { key: 'nombre_producto', label: 'Producto' },
      { key: 'categoria', label: 'Categoría' },
      { key: 'unidad_medida', label: 'U. Medida' },
      { key: 'precio_unitario', label: 'P. Unitario' },
      { key: 'stock_actual', label: 'Stock Actual' },
      { key: 'stock_minimo', label: 'Stock Mínimo' }
    ],
    ejemploPlantilla: [
      {
        nombre_producto: 'UREA GRANULADA 46%',
        categoria: 'FERTILIZANTE',
        unidad_medida: 'KG',
        precio_unitario: 15.50,
        stock_actual: 1000.00,
        stock_minimo: 100.00
      }
    ]
  },
  TERRENOS: {
    label: 'Terrenos (Lotes de Cultivo)',
    endpoint: '/api/import-terrenos',
    columnas: [
      { key: 'nombre_sector', label: 'Nombre Sector / Lote' },
      { key: 'tamano_hectareas', label: 'Hectáreas' },
      { key: 'latitud', label: 'Latitud' },
      { key: 'longitud', label: 'Longitud' },
      { key: 'estado', label: 'Estado' },
      { key: 'id_usuario', label: 'ID Usuario' }
    ],
    ejemploPlantilla: [
      {
        nombre_sector: 'SECTOR NORTE - LOTE A1',
        tamano_hectareas: 50.50,
        latitud: -17.7833,
        longitud: -63.1833,
        estado: 'EN_DESCANSO',
        id_usuario: 2
      }
    ]
  }
};

export default function ImportarMasivo() {
  const API_URL = import.meta.env.VITE_API_URL;
  const token = useAuthStore((state) => state.token);
  const id_empresa = useAuthStore((state) => state.user?.id_empresa || 1);

  // Estados de la aplicación
  const [entidadSeleccionada, setEntidadSeleccionada] = useState('USUARIOS');
  const [archivo, setArchivo] = useState(null);
  const [datosPreview, setDatosPreview] = useState([]);
  const [loadingParse, setLoadingParse] = useState(false);
  const [loadingImport, setLoadingImport] = useState(false);
  const [resultado, setResultado] = useState(null);

  const fileInputRef = useRef(null);
  const configActual = CONFIG_ENTIDADES[entidadSeleccionada];

  const handleCambioEntidad = (e) => {
    setEntidadSeleccionada(e.target.value);
    resetFlujo();
  };

  const resetFlujo = () => {
    setArchivo(null);
    setDatosPreview([]);
    setResultado(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const descargarPlantilla = () => {
    const ws = XLSX.utils.json_to_sheet(configActual.ejemploPlantilla);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, `Plantilla_${entidadSeleccionada}`);
    XLSX.writeFile(wb, `plantilla_carga_${entidadSeleccionada.toLowerCase()}.xlsx`);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const extensionValida = file.name.match(/\.(xlsx|xls|csv)$/i);
    if (!extensionValida) {
      alert('Formato no soportado. Cargue únicamente archivos .xlsx, .xls o .csv');
      return;
    }

    setArchivo(file);
    parsearArchivoExcel(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      const extensionValida = file.name.match(/\.(xlsx|xls|csv)$/i);
      if (!extensionValida) return alert('Formato no soportado.');
      setArchivo(file);
      parsearArchivoExcel(file);
    }
  };

  const parsearArchivoExcel = (file) => {
    setLoadingParse(true);
    setResultado(null);

    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const bstr = evt.target.result;
        const wb = XLSX.read(bstr, { type: 'binary' });
        const wsname = wb.SheetNames[0];
        const ws = wb.Sheets[wsname];
        const jsonLeido = XLSX.utils.sheet_to_json(ws);

        // Inyección de id_empresa automática para control multitenant
        const datosNormalizados = jsonLeido.map((item) => ({
          ...item,
          id_empresa: id_empresa
        }));

        setDatosPreview(datosNormalizados);
      } catch (err) {
        console.error(err);
        alert("Error al estructurar el archivo. Verifique que no esté dañado.");
        setDatosPreview([]);
      } finally {
        setLoadingParse(false);
      }
    };
    reader.readAsBinaryString(file);
  };

  const ejecutarImportacion = async () => {
    if (datosPreview.length === 0) return;
    setLoadingImport(true);
    setResultado(null);

    try {
      // Conexión directa y limpia con tu API sin duplicación de segmentos de rutas
      const response = await fetch(`${API_URL}${configActual.endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(datosPreview)
      });
      const dataRes = await response.json();

      setResultado(dataRes);

      if (dataRes.success) {
        setArchivo(null);
        setDatosPreview([]);
        if (fileInputRef.current) fileInputRef.current.value = '';
      }
    } catch (error) {
      setResultado({
        success: false,
        message: "Error crítico de enlace. No se pudo establecer la comunicación con el servidor de la empresa."
      });
    } finally {
      setLoadingImport(false);
    }
  };

  return (
    <div className="p-4 md:p-6 lg:p-8 animate-in fade-in duration-500 bg-slate-50 min-h-screen text-slate-800">
      
      {/* SECCIÓN SUPERIOR: CONTROL PANEL */}
      <div className="mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white p-5 border border-slate-200 shadow-sm rounded-md">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4 w-full md:w-auto">
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-3">
              <div className="w-1.5 h-6 bg-[#1A5729]"></div>
              PROCESAMIENTO MASIVO
            </h1>
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1 ml-4">
              Carga e Integración de Estructuras de Datos
            </p>
          </div>

          <div className="sm:ml-4 flex-1 sm:flex-initial">
            <select 
              value={entidadSeleccionada}
              onChange={handleCambioEntidad}
              className="w-full sm:w-64 px-3 py-2 border border-slate-300 rounded-md text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white cursor-pointer transition-colors"
            >
              {Object.keys(CONFIG_ENTIDADES).map((key) => (
                <option key={key} value={key}>
                  Módulo: {CONFIG_ENTIDADES[key].label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button 
          type="button"
          onClick={descargarPlantilla}
          className="w-full md:w-auto flex items-center justify-center gap-2 text-[10px] font-bold uppercase tracking-widest text-[#1A5729] bg-[#1A5729]/10 hover:bg-[#1A5729]/20 border border-[#1A5729]/30 px-5 py-2.5 rounded-md transition-all active:scale-95 shadow-sm"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
          Descargar Layout
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* COLUMNA IZQUIERDA: GESTIÓN DE ARCHIVOS */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="bg-white p-5 border border-slate-200 shadow-sm rounded-md">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-widest mb-4 border-b border-slate-100 pb-2">Archivo Origen</h2>
            
            {!archivo ? (
              <div 
                onDragOver={(e) => e.preventDefault()} 
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-200 bg-slate-50 hover:bg-slate-100/70 h-44 flex flex-col items-center justify-center cursor-pointer transition-colors rounded-sm group"
              >
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  onChange={handleFileChange} 
                  accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel" 
                  className="hidden" 
                />
                <svg className="w-8 h-8 text-slate-400 group-hover:text-[#1A5729] mb-2 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                <p className="text-xs font-bold text-slate-700">Seleccione archivo Excel o CSV</p>
                <p className="text-[9px] text-slate-400 font-bold uppercase tracking-wider mt-0.5">Estructura según módulo actual</p>
              </div>
            ) : (
              <div className="bg-slate-50 border border-slate-200 p-4 rounded-md">
                <div className="flex items-start gap-3 mb-4">
                  <div className="bg-[#1A5729] text-white p-2 rounded-sm">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-slate-800 truncate">{archivo.name}</p>
                    <p className="text-[10px] font-bold text-slate-400 uppercase mt-0.5">Estructura Mapeada</p>
                  </div>
                </div>
                <button 
                  type="button"
                  onClick={resetFlujo} 
                  className="w-full bg-white border border-slate-300 text-slate-600 hover:bg-slate-100 py-2 rounded-md text-[10px] font-bold uppercase tracking-widest transition-colors shadow-sm"
                >
                  Remover Documento
                </button>
              </div>
            )}

            {/* PANEL DE RESULTADOS Y ALERTAS DE INTEGRIDAD */}
            {resultado && (
              <div className={`mt-5 p-4 rounded-md border text-left text-xs ${resultado.success ? 'bg-emerald-50 border-emerald-200 text-emerald-950' : 'bg-red-50 border-red-200 text-red-950'}`}>
                <h4 className="font-bold uppercase tracking-wider mb-1">
                  {resultado.success ? 'Proceso Finalizado' : 'Fallo de Carga'}
                </h4>
                <p className="font-medium opacity-90 leading-normal mb-3">{resultado.message}</p>
                
                {resultado.errores && resultado.errores.length > 0 && (
                  <div className="bg-white border border-slate-200 rounded-md p-2 max-h-36 overflow-y-auto custom-scrollbar">
                    {resultado.errores.map((err, i) => (
                      <p key={i} className="text-[9px] text-red-600 font-mono py-1 border-b border-slate-100 last:border-0 last:pb-0">
                        • {err}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* COLUMNA DERECHA: GRILLA DE AUDITORÍA PREVIA */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          <div className="bg-white border border-slate-200 shadow-sm rounded-md overflow-hidden flex flex-col h-[480px]">
            
            <div className="p-4 bg-slate-50 border-b border-slate-200 flex justify-between items-center shrink-0">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-widest flex items-center gap-2">
                <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                Auditoría Previa de Datos
              </h3>
              {datosPreview.length > 0 && (
                <span className="bg-slate-200 text-slate-700 px-2.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-widest border border-slate-300">
                  {datosPreview.length} Registros Cargados
                </span>
              )}
            </div>

            <div className="flex-1 overflow-auto custom-scrollbar bg-white">
              {loadingParse ? (
                <div className="h-full flex flex-col items-center justify-center text-slate-400">
                  <div className="animate-spin rounded-full h-7 w-7 border-b-2 border-slate-500 mb-3"></div>
                  <p className="text-[10px] font-bold uppercase tracking-widest">Sincronizando registros...</p>
                </div>
              ) : datosPreview.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-slate-300 p-8 text-center">
                  <svg className="w-12 h-12 mb-3 text-slate-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}><path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Grilla Vacía</p>
                  <p className="text-[10px] font-medium text-slate-400 max-w-xs mt-1 leading-relaxed">Cargue un archivo compatible a la izquierda para previsualizar y auditar la estructura de las celdas antes de enviarlas al entorno de producción.</p>
                </div>
              ) : (
                <div className="overflow-x-auto w-full">
                  <table className="w-full text-left border-collapse table-auto min-w-[750px] text-xs">
                    <thead className="bg-slate-50 sticky top-0 z-10 shadow-sm border-b border-slate-200">
                      <tr className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">
                        {configActual.columnas.map((col) => (
                          <th key={col.key} className="p-3 border-r border-slate-100 last:border-0">{col.label}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {datosPreview.slice(0, 50).map((row, index) => (
                        <tr key={index} className="hover:bg-slate-50/50 transition-colors">
                          {configActual.columnas.map((col) => {
                            // Flexibilidad de alias para mitigar diferencias de nombrado entre front/plantilla
                            const valorCelda = row[col.key] ?? row[col.key.replace('user_name', 'user').replace('documento_identidad', 'doc').replace('nombre_razon_social', 'name').replace('correo', 'mail').replace('id_rol', 'id_role')];
                            return (
                              <td key={col.key} className="p-3 text-slate-700 max-w-[180px] truncate font-medium border-r border-slate-100 last:border-0">
                                {valorCelda !== undefined ? String(valorCelda) : <span className="text-slate-300 italic font-normal">NULL</span>}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* BOTÓN DE ACCIÓN FINAL */}
            <div className="p-4 bg-slate-50 border-t border-slate-200 flex justify-end shrink-0 shadow-sm">
              <button 
                type="button"
                onClick={ejecutarImportacion}
                disabled={datosPreview.length === 0 || loadingImport}
                className="w-full md:w-auto bg-[#1A5729] hover:bg-[#12411e] text-white px-8 py-3 rounded-md font-bold text-[10px] uppercase tracking-widest transition-all disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-md active:scale-95"
              >
                {loadingImport ? (
                  <><div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div> Procesando bloque...</>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
                    Confirmar e Importar a {configActual.label.split(' ')[0]}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}