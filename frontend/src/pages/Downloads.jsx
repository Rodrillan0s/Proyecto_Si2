import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Downloads() {
  const navigate = useNavigate();
  const [descargando, setDescargando] = useState(null);

  // Dejamos solo el recurso de la App Móvil por ahora
  const recursos = [
    {
      id: 'apk-movil',
      titulo: 'AgroEnlace Móvil (Android)',
      desc: 'Aplicación nativa para trabajo en campo. Permite registrar lotes y campañas con sincronización a la nube.',
      version: 'v1.0.0 (Beta)',
      peso: '50 MB', 
      tipo: 'APK',
      color: 'text-emerald-600 dark:text-emerald-400',
      bg: 'bg-emerald-50 dark:bg-emerald-500/10',
      url: `${window.location.origin}/downloads/agroenlace.apk`, 
      icono: (
        <svg fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8">
          <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 1.5H8.25A2.25 2.25 0 006 3.75v16.5a2.25 2.25 0 002.25 2.25h7.5A2.25 2.25 0 0018 20.25V3.75a2.25 2.25 0 00-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-3 18.75h3" />
        </svg>
      )
    }
  ];

  const handleDownload = (recurso) => {
    setDescargando(recurso.id);
    
    // Pequeño delay para mostrar el estado "Preparando..."
    setTimeout(() => {
      setDescargando(null);
      
      // CREACIÓN DEL LINK DE DESCARGA REAL
      const link = document.createElement('a');
      link.href = recurso.url;
      link.setAttribute('download', 'AgroEnlace_Mobile.apk'); // Nombre con el que se guardará
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }, 1200);
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] dark:bg-[#0F172A] font-sans antialiased transition-colors duration-300">
      
      <nav className="bg-white dark:bg-[#1E293B] shadow-sm border-b border-gray-200 dark:border-slate-700/80 px-4 md:px-6 py-4 flex items-center sticky top-0 z-50">
        <button 
          onClick={() => navigate('/')}
          className="flex items-center text-gray-500 hover:text-[#1A5729] dark:text-slate-400 dark:hover:text-[#7BC636] font-semibold transition-colors"
        >
          <svg fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-5 h-5 mr-2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          Volver al Inicio
        </button>
      </nav>

      <main className="max-w-6xl mx-auto p-4 md:p-10 animate-fade-in">
        
        <div className="mb-8 md:mb-12">
          <h2 className="text-2xl md:text-3xl font-black text-gray-800 dark:text-white tracking-tight">
            Descargas Corporativas
          </h2>
          <p className="text-sm md:text-base text-gray-500 dark:text-slate-400 mt-2 max-w-2xl">
            Obtén la última versión de la herramienta móvil de AgroEnlace para gestión en campo.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 md:gap-6">
          {recursos.map((rec) => (
            <div 
              key={rec.id}
              className="bg-white dark:bg-[#1E293B] rounded-2xl shadow-sm border border-gray-200 dark:border-slate-700/80 hover:shadow-md transition-shadow flex flex-col overflow-hidden group"
            >
              <div className="p-6 flex-grow">
                <div className={`inline-flex p-3 rounded-xl ${rec.bg} ${rec.color} mb-4`}>
                  {rec.icono}
                </div>
                
                <h3 className="text-lg font-bold text-gray-800 dark:text-slate-100 mb-2 leading-tight">
                  {rec.titulo}
                </h3>
                
                <p className="text-sm text-gray-500 dark:text-slate-400 leading-relaxed mb-4">
                  {rec.desc}
                </p>

                <div className="flex items-center gap-3 text-xs font-semibold text-gray-400 dark:text-slate-500">
                  <span className="flex items-center gap-1 bg-gray-100 dark:bg-slate-800 px-2 py-1 rounded-md">
                    {rec.version}
                  </span>
                  <span className="flex items-center gap-1 bg-gray-100 dark:bg-slate-800 px-2 py-1 rounded-md">
                    {rec.peso}
                  </span>
                </div>
              </div>

              <div className="px-6 py-4 border-t border-gray-100 dark:border-slate-700/80 bg-gray-50/50 dark:bg-slate-800/30">
                <button
                  onClick={() => handleDownload(rec)}
                  disabled={descargando === rec.id}
                  className={`w-full py-2.5 rounded-lg text-sm font-bold shadow-sm transition-all flex items-center justify-center gap-2 ${
                    descargando === rec.id
                      ? 'bg-gray-200 text-gray-500 dark:bg-slate-700 dark:text-slate-400 cursor-wait'
                      : 'bg-[#1A5729] hover:bg-[#144320] text-white dark:bg-cyan-600 dark:hover:bg-cyan-700'
                  }`}
                >
                  {descargando === rec.id ? (
                    <>
                      <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Iniciando descarga...
                    </>
                  ) : (
                    <>
                      <svg fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-4 h-4">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                      </svg>
                      Descargar Instalador
                    </>
                  )}
                </button>
              </div>

            </div>
          ))}
        </div>
      </main>
    </div>
  );
}