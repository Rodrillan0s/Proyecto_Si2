import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/auth_store';
import logoAgro from '../assets/LOGO.png';

export default function Home() {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const navigate = useNavigate();

  // Estado para el Modo Oscuro
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Efecto para leer la preferencia del sistema
  useEffect(() => {
    if (document.documentElement.classList.contains('dark')) {
      setIsDarkMode(true);
    }
  }, []);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    document.documentElement.classList.toggle('dark');
  };

  const handleLogout = () => {
    logout(); 
    navigate('/login'); 
  };

  // Saludo corporativo basado en la hora
  const obtenerSaludo = () => {
    const hora = new Date().getHours();
    if (hora < 12) return 'Buenos días';
    if (hora < 18) return 'Buenas tardes';
    return 'Buenas noches';
  };

  // Array de Módulos Operativos
  const modulos = [
    {
      id: 'produccion',
      titulo: 'Producción Agrícola',
      desc: 'Control de lotes, siembras, cosechas, inventario de agroquímicos y asignación de maquinaria.',
      ruta: '/agro/lote',
      color: 'text-emerald-600 dark:text-emerald-400',
      bg: 'bg-emerald-50 dark:bg-emerald-500/10',
      borde: 'hover:border-emerald-500 dark:hover:border-emerald-400',
      icono: (
        <svg fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-7 h-7">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z" />
        </svg>
      )
    },
    {
      id: 'comercial',
      titulo: 'Ventas y Comercialización',
      desc: 'Gestión de contratos, control de precios de granos, despachos y seguimiento de entregas.',
      ruta: '/ventas/catalogo',
      color: 'text-blue-600 dark:text-blue-400',
      bg: 'bg-blue-50 dark:bg-blue-500/10',
      borde: 'hover:border-blue-500 dark:hover:border-blue-400',
      icono: (
        <svg fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-7 h-7">
          <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 00-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 00-16.536-1.84M7.5 14.25L5.106 5.272M6 20.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm12.75 0a.75.75 0 11-1.5 0 .75.75 0 011.5 0z" />
        </svg>
      )
    },
    {
      id: 'crm',
      titulo: 'Gestión de Clientes (CRM)',
      desc: 'Seguimiento de cartera de clientes, proveedores, historial de interacciones y embudos de venta.',
      ruta: '/crm/clientes',
      color: 'text-purple-600 dark:text-purple-400',
      bg: 'bg-purple-50 dark:bg-purple-500/10',
      borde: 'hover:border-purple-500 dark:hover:border-purple-400',
      icono: (
        <svg fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-7 h-7">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
        </svg>
      )
    },
    {
      id: 'reportes',
      titulo: 'Reportes e Inteligencia',
      desc: 'Cuadros de mando, analítica de datos, exportación de reportes y cruce de información corporativa.',
      ruta: '/reportes',
      color: 'text-rose-600 dark:text-rose-400',
      bg: 'bg-rose-50 dark:bg-rose-500/10',
      borde: 'hover:border-rose-500 dark:hover:border-rose-400',
      icono: (
        <svg fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-7 h-7">
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
        </svg>
      )
    },
    {
      id: 'security',
      titulo: 'Seguridad y Accesos',
      desc: 'Administración de cuentas, asignación de roles, control de permisos y auditoría del sistema.',
      ruta: '/security/users',
      color: 'text-cyan-600 dark:text-cyan-400',
      bg: 'bg-cyan-50 dark:bg-cyan-500/10',
      borde: 'hover:border-cyan-500 dark:hover:border-cyan-400',
      icono: (
        <svg fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-7 h-7">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
        </svg>
      )
    },
    {
      id: 'downloads',
      titulo: 'Descargas y Recursos',
      desc: 'Descarga la aplicación móvil (APK), manuales de usuario y plantillas corporativas.',
      ruta: '/downloads',
      color: 'text-slate-600 dark:text-slate-400',
      bg: 'bg-slate-100 dark:bg-slate-500/10',
      borde: 'hover:border-slate-500 dark:hover:border-slate-400',
      icono: (
        <svg fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-7 h-7">
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
        </svg>
      )
    }
  ];

  // Filtramos los módulos permitidos según el rol
  const modulosPermitidos = modulos.filter((mod) => {
    if (mod.id === 'security') {
      return user?.id_rol === 1; // Solo Admin ve Seguridad
    }
    if (mod.id === 'produccion') {
      return [1, 2, 3].includes(user?.id_rol); 
    }
    // El módulo de descargas está disponible para todos los usuarios logueados
    return true;
  });

  return (
    <div className="min-h-screen bg-[#F8FAFC] dark:bg-[#0F172A] font-sans antialiased selection:bg-[#5B9D1E] selection:text-white transition-colors duration-300">
      
      {/* Navbar Superior */}
      <nav className="bg-white dark:bg-[#1E293B] shadow-sm border-b border-gray-200 dark:border-slate-700/80 px-4 md:px-6 py-3 flex justify-between items-center sticky top-0 z-50 transition-colors duration-300">
        
        {/* Logo y Branding */}
        <div className="flex items-center gap-3">
          <img src={logoAgro} alt="AgroEnlace" className="w-8 h-8 md:w-9 md:h-9 rounded-md border border-gray-100 dark:border-slate-600 object-contain bg-white" />
          <div className="flex flex-col">
            <h1 className="text-base md:text-lg font-black text-[#1A5729] dark:text-[#7BC636] tracking-tight leading-none">AgroEnlace</h1>
            <span className="text-[9px] md:text-[10px] text-gray-400 dark:text-slate-400 font-bold uppercase tracking-widest mt-0.5">Workspace</span>
          </div>
        </div>
        
        {/* Controles de Usuario a la derecha */}
        <div className="flex items-center gap-4">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-bold text-gray-700 dark:text-slate-200">
              {user?.nombre_razon_social?.split(' ')[0] || 'Administrador'}
            </p>
            <p className="text-[10px] text-gray-500 dark:text-slate-400 font-medium tracking-wider">
              {user?.correo || 'admin@agroenlace.com'}
            </p>
          </div>
          
          <div className="flex items-center bg-gray-50 dark:bg-slate-800/50 border border-gray-200 dark:border-slate-700 rounded-full p-1 shadow-inner md:ml-2">
            
            <button 
              onClick={toggleDarkMode}
              className="p-1.5 md:p-2 text-gray-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-amber-400 hover:bg-white dark:hover:bg-slate-700 rounded-full transition-all hover:shadow-sm flex items-center justify-center"
              title={isDarkMode ? "Modo Claro" : "Modo Oscuro"}
            >
              {isDarkMode ? (
                <svg fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4 md:w-4 md:h-4"><path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" /></svg>
              ) : (
                <svg fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4 md:w-4 md:h-4"><path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" /></svg>
              )}
            </button>

            <div className="w-px h-4 bg-gray-200 dark:bg-slate-600 mx-0.5"></div>

            <button
              onClick={() => navigate('/profile')}
              className="p-1.5 md:p-2 text-gray-500 hover:text-[#5B9D1E] dark:text-slate-400 dark:hover:text-[#7BC636] hover:bg-white dark:hover:bg-slate-700 rounded-full transition-all hover:shadow-sm flex items-center justify-center"
              title="Mi Perfil"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4 md:w-4 md:h-4"><path strokeLinecap="round" strokeLinejoin="round" d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
            </button>

            <div className="w-px h-4 bg-gray-200 dark:bg-slate-600 mx-0.5"></div>

            <button
              onClick={handleLogout}
              className="p-1.5 md:p-2 text-gray-400 hover:text-red-600 dark:text-slate-500 dark:hover:text-red-400 hover:bg-white dark:hover:bg-slate-700 rounded-full transition-all hover:shadow-sm flex items-center justify-center"
              title="Cerrar Sesión"
            >
              <svg fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-4 h-4 md:w-4 md:h-4"><path strokeLinecap="round" strokeLinejoin="round" d="M5.636 5.636a9 9 0 1012.728 0M12 3v9" /></svg>
            </button>

          </div>
        </div>
      </nav>

      {/* Contenido Principal */}
      <main className="max-w-7xl mx-auto p-4 md:p-10">
        
        {/* Saludo Dinámico */}
        <div className="mb-6 md:mb-10 text-center md:text-left">
          <h2 className="text-2xl md:text-3xl font-black text-gray-800 dark:text-white tracking-tight">
            {obtenerSaludo()}, {user?.nombre_razon_social?.split(' ')[0] || 'Administrador'}
          </h2>
          <p className="text-sm md:text-base text-gray-500 dark:text-slate-400 mt-1 font-medium">Selecciona un módulo para comenzar.</p>
        </div>

        {/* CAMBIO CLAVE: grid-cols-2 para móviles, md:grid-cols-3 para PC */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 md:gap-6">
          
          {modulosPermitidos.map((mod) => (
            <div 
              key={mod.id}
              onClick={() => navigate(mod.ruta)}
              className={`bg-white dark:bg-[#1E293B] p-4 md:p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-700 ${mod.borde} hover:shadow-md transition-all duration-150 cursor-pointer group flex flex-col h-full items-center md:items-start text-center md:text-left`}
            >
              {/* Icono centrado en móvil, a la izquierda en PC */}
              <div className="flex items-center md:items-start mb-3 md:mb-5">
                <div className={`p-2.5 md:p-3.5 rounded-xl ${mod.bg} ${mod.color}`}>
                  {mod.icono}
                </div>
              </div>
              
              <h3 className="text-[13px] md:text-lg font-bold text-gray-800 dark:text-slate-100 mb-1 md:mb-2 group-hover:text-[#1A5729] dark:group-hover:text-[#7BC636] transition-colors duration-150 leading-tight">
                {mod.titulo}
              </h3>
              
              {/* Descripción oculta en celulares para no romper la estética 2x2 */}
              <p className="hidden md:block text-sm text-gray-500 dark:text-slate-400 leading-relaxed flex-grow">
                {mod.desc}
              </p>
              
              {/* Texto de Ingresar oculto en celulares */}
              <div className="hidden md:flex mt-6 items-center text-sm font-bold text-[#5B9D1E] dark:text-[#7BC636] opacity-0 group-hover:opacity-100 transition-all transform -translate-x-2 group-hover:translate-x-0 duration-150">
                Ingresar al módulo 
                <svg fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-4 h-4 ml-1">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
              </div>
            </div>
          ))}

        </div>
      </main>
    </div>
  );
}