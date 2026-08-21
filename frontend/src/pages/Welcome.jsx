import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import logoAgro from '../assets/LOGO.png'; 

export default function Welcome() {
  const [isLoaded, setIsLoaded] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token'); 
    if (token) navigate('/home'); 
    setIsLoaded(true);
  }, [navigate]);

  return (
    <div className={`min-h-screen bg-[#EBF5FF] flex flex-col font-sans antialiased transition-opacity duration-700 ${isLoaded ? 'opacity-100' : 'opacity-0'}`}>
      
      {/* Línea de acento superior */}
      <div className="h-1.5 w-full bg-[#1A5729]"></div>

      <div className="flex-1 flex flex-col lg:flex-row max-w-7xl mx-auto w-full">
        
        {/* PANEL IZQUIERDO: BRANDING INSTITUCIONAL */}
        <div className="flex-1 flex flex-col items-center lg:items-start justify-center p-10 lg:p-20">
          <div className="bg-white/50 p-6 rounded-xl border border-blue-100 shadow-sm inline-block mb-10">
            <img 
              src={logoAgro} 
              alt="Logo AgroEnlace" 
              className="w-32 h-32 md:w-40 md:h-40 object-contain"
            />
          </div>
          
          <h1 className="text-4xl md:text-6xl font-black text-slate-800 tracking-tight leading-none text-center lg:text-left">
            AGRO<span className="text-[#1A5729]">ENLACE</span>
          </h1>
          
          <div className="h-1 w-24 bg-[#5B9D1E] my-6"></div>
          
          <p className="text-xl text-slate-600 font-semibold max-w-md leading-snug text-center lg:text-left">
            Plataforma de Control y Trazabilidad para Empresas del Sector Agroindustrial.
          </p>

          <div className="mt-12 hidden lg:block">
            <div className="flex items-center gap-4 text-[11px] font-bold text-slate-400 uppercase tracking-[0.3em]">
              <span>Módulo Web</span>
              <span className="w-1.5 h-1.5 bg-slate-300 rounded-full"></span>
              <span>UAGRM - SI2</span>
            </div>
          </div>
        </div>

        {/* PANEL DERECHO: INTERFAZ DE ACCESO */}
        <div className="flex-1 flex items-center justify-center p-6 lg:p-10">
          <div className="w-full max-w-md bg-white border border-slate-200 shadow-2xl rounded-lg overflow-hidden">
            
            {/* Cabecera del formulario */}
            <div className="bg-slate-50 border-b border-slate-100 px-8 py-6">
              <h2 className="text-sm font-black text-slate-500 uppercase tracking-[0.2em]">Autenticación de Usuario</h2>
              <p className="text-xs text-slate-400 mt-1 font-medium text-pretty">Acceso restringido a personal técnico y administrativo.</p>
            </div>

            <div className="p-8 lg:p-10 flex flex-col gap-5">
              <Link
                to="/login"
                className="w-full bg-[#1A5729] hover:bg-[#144320] text-white font-bold py-4 px-6 rounded-md shadow-sm transition-all duration-200 text-center text-sm uppercase tracking-widest flex items-center justify-center gap-3 group"
              >
                <span>Ingresar al Sistema</span>
                <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Link>
              
              <div className="relative py-2">
                <div className="absolute inset-0 flex items-center"><span className="w-full border-t border-slate-100"></span></div>
                <div className="relative flex justify-center text-[10px] font-bold uppercase tracking-widest text-slate-300">
                  <span className="bg-white px-4">Gestión de Cuentas</span>
                </div>
              </div>

              <Link
                to="/register"
                className="w-full bg-white hover:bg-slate-50 text-slate-600 border border-slate-300 font-bold py-3.5 px-6 rounded-md transition-all duration-200 text-center text-sm uppercase tracking-widest shadow-sm"
              >
                Registrar Nuevo Operador
              </Link>
            </div>

            <div className="bg-slate-50/80 px-8 py-4 border-t border-slate-100">
               <p className="text-[9px] text-center text-slate-400 font-bold uppercase tracking-tighter italic leading-none">
                 © 2026 AgroEnlace S.A. Reservados todos los derechos.
               </p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer minimalista */}
      <footer className="bg-white/80 backdrop-blur-sm border-t border-slate-200 px-8 py-3 flex flex-col sm:flex-row justify-between items-center gap-4 text-[10px] font-extrabold text-slate-400 uppercase tracking-[0.2em]">
        <div>Santa Cruz de la Sierra • Bolivia</div>
        <div className="flex gap-8">
          <span className="text-slate-300 hover:text-slate-500 transition-colors cursor-default">Infraestructura Crítica</span>
          <span className="text-slate-300 hover:text-slate-500 transition-colors cursor-default">Soporte TI</span>
        </div>
      </footer>
    </div>
  );
}