import { useState } from 'react';
import { useAuthStore } from '../store/auth_store';

export default function SystemBackups() {
  const API_URL = import.meta.env.VITE_API_URL;
  const token = useAuthStore((state) => state.token);
  
  // Estados para el Backup Manual
  const [descargando, setDescargando] = useState(false);

  // Estados para el Backup Automático
  const [autoEnabled, setAutoEnabled] = useState(false);
  const [guardandoConfig, setGuardandoConfig] = useState(false);
  const [config, setConfig] = useState({
    frecuencia: 'DIARIO',
    hora: '03:00',
    retencion: '7',
    correoNotificacion: ''
  });

  // --- LÓGICA DE RESPALDO MANUAL ---
  const handleDescargarBackup = async () => {
    setDescargando(true);
    try {
      const response = await fetch(`${API_URL}/backup/manual`, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('No se pudo generar el backup.');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      const fecha = new Date().toISOString().slice(0,10);
      link.setAttribute('download', `agroenlace_backup_${fecha}.sql`);
      
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
      
    } catch (error) {
      alert(error.message);
    } finally {
      setDescargando(false);
    }
  };

  // --- LÓGICA DE RESPALDO AUTOMÁTICO ---
  const handleConfigChange = (e) => {
    setConfig({ ...config, [e.target.name]: e.target.value });
  };

  const handleSaveAutoBackup = async (e) => {
    e.preventDefault();
    setGuardandoConfig(true);
    
    // Aquí iría el fetch() hacia tu nuevo endpoint de configuración
    
    setTimeout(() => {
      setGuardandoConfig(false);
      alert('Configuración de copias de seguridad automáticas guardada con éxito.');
    }, 1000); // Simulación
  };

  return (
    <div className="p-4 md:p-8 animate-in fade-in duration-500 bg-slate-50 min-h-screen max-w-[100vw] overflow-x-hidden">
      
      {/* CABECERA */}
      <div className="mb-6 md:mb-8">
        <h1 className="text-xl md:text-2xl font-black text-slate-800 tracking-tight flex items-center gap-3">
          <div className="w-2 h-6 md:h-8 bg-[#1A5729]"></div>
          RESPALDOS Y SEGURIDAD
        </h1>
        <p className="text-[9px] md:text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mt-1 ml-5">
          Gestión de copias de seguridad de la base de datos
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
        
        {/* --- TARJETA 1: BACKUP MANUAL --- */}
        <div className="bg-white p-6 md:p-8 rounded-xl border border-slate-200 shadow-sm flex flex-col h-full">
          <div className="flex items-center gap-4 mb-4">
            <div className="bg-emerald-50 p-3 rounded-lg text-emerald-600">
              <svg className="w-6 h-6 md:w-8 md:h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-3 3m0 0l-3-3m3 3V4" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-black text-slate-800 uppercase tracking-widest">Respaldo Manual</h2>
              <p className="text-[10px] md:text-xs font-bold text-slate-400 mt-1">Descarga inmediata (.SQL)</p>
            </div>
          </div>
          
          <p className="text-sm text-slate-600 mb-8 flex-1">
            Genera una copia de seguridad al instante con toda la información operativa, catálogos, transacciones y usuarios del sistema. El archivo se descargará directamente a su dispositivo.
          </p>

          <button 
            onClick={handleDescargarBackup}
            disabled={descargando}
            className="w-full bg-slate-800 hover:bg-slate-900 text-white px-6 py-4 rounded-lg font-black text-xs md:text-sm uppercase tracking-widest transition-all active:scale-95 shadow-md disabled:opacity-70 flex items-center justify-center gap-3"
          >
            {descargando ? (
              <>
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                PROCESANDO EXTRACCIÓN...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                </svg>
                GENERAR Y DESCARGAR AHORA
              </>
            )}
          </button>
        </div>

        {/* --- TARJETA 2: BACKUP AUTOMÁTICO --- */}
        <div className="bg-white p-6 md:p-8 rounded-xl border border-slate-200 shadow-sm flex flex-col h-full">
          
          {/* HEADER Y SWITCH (SIEMPRE VISIBLES) */}
          <div className="flex items-start justify-between mb-6 z-20 relative">
            <div className="flex items-center gap-4">
              <div className="bg-blue-50 p-3 rounded-lg text-blue-600">
                <svg className="w-6 h-6 md:w-8 md:h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-black text-slate-800 uppercase tracking-widest">Respaldo Automático</h2>
                <p className="text-[10px] md:text-xs font-bold text-slate-400 mt-1">Tareas programadas (Cron)</p>
              </div>
            </div>

            {/* TOGGLE SWITCH CORREGIDO */}
            <label className="relative inline-flex items-center cursor-pointer mt-2">
              <input 
                type="checkbox" 
                className="sr-only peer" 
                checked={autoEnabled}
                onChange={() => setAutoEnabled(!autoEnabled)}
              />
              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[#1A5729]/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#1A5729]"></div>
            </label>
          </div>

          {/* CONTENEDOR RELATIVO PARA EL FORMULARIO (Evita que el blur se escape) */}
          <div className="relative flex-1 flex flex-col">
            
            {/* FORMULARIO (Se difumina si autoEnabled es false) */}
            <div className={`transition-all duration-300 flex-1 flex flex-col ${autoEnabled ? 'opacity-100' : 'opacity-40 blur-[2px] pointer-events-none'}`}>
              <form onSubmit={handleSaveAutoBackup} className="flex flex-col flex-1">
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Frecuencia</label>
                    <select 
                      name="frecuencia" value={config.frecuencia} onChange={handleConfigChange} disabled={!autoEnabled}
                      className="w-full px-4 py-2.5 border border-slate-200 rounded text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]"
                    >
                      <option value="DIARIO">Diario</option>
                      <option value="SEMANAL">Semanal</option>
                      <option value="MENSUAL">Mensual</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Hora de Ejecución</label>
                    <input 
                      type="time" name="hora" value={config.hora} onChange={handleConfigChange} disabled={!autoEnabled}
                      className="w-full px-4 py-2.5 border border-slate-200 rounded text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]"
                    />
                  </div>
                </div>

                <div className="mb-4">
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Retener archivos por (Días)</label>
                  <select 
                    name="retencion" value={config.retencion} onChange={handleConfigChange} disabled={!autoEnabled}
                    className="w-full px-4 py-2.5 border border-slate-200 rounded text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]"
                  >
                    <option value="7">7 Días (Recomendado)</option>
                    <option value="15">15 Días</option>
                    <option value="30">30 Días</option>
                  </select>
                </div>

                <div className="mb-8">
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Notificar al correo</label>
                  <input 
                    type="email" name="correoNotificacion" value={config.correoNotificacion} onChange={handleConfigChange} disabled={!autoEnabled}
                    placeholder="admin@empresa.com"
                    className="w-full px-4 py-2.5 border border-slate-200 rounded text-xs font-bold outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]"
                  />
                </div>

                <div className="mt-auto">
                  <button 
                    type="submit"
                    disabled={!autoEnabled || guardandoConfig}
                    className="w-full bg-[#1A5729] hover:bg-[#144320] text-white px-6 py-4 rounded-lg font-black text-xs md:text-sm uppercase tracking-widest transition-all active:scale-95 shadow-md disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none flex items-center justify-center gap-3"
                  >
                    {guardandoConfig ? 'GUARDANDO...' : 'GUARDAR CONFIGURACIÓN AUTOMÁTICA'}
                  </button>
                </div>
              </form>
            </div>

            {/* MENSAJE FLOTANTE CUANDO ESTÁ DESACTIVADO (Contenido dentro del relative) */}
            {!autoEnabled && (
              <div className="absolute inset-0 z-10 flex items-center justify-center p-4">
                <p className="text-center text-sm font-bold text-slate-600 bg-white/90 p-4 rounded-lg shadow-lg border border-slate-200 backdrop-blur-sm">
                  Active el interruptor superior para configurar y programar las copias de seguridad automáticas en el servidor.
                </p>
              </div>
            )}

          </div>

        </div>
      </div>
    </div>
  );
}