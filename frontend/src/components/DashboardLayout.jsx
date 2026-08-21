import { useState, useEffect } from 'react';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/auth_store';
import logoAgro from '../assets/LOGO.png';

export default function DashboardLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  
  // 1. ESTADO DEL MODO OSCURO
  const [isDarkMode, setIsDarkMode] = useState(false);
  
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

  // En móviles empieza cerrado, en PC empieza abierto
  const [isSidebarOpen, setIsSidebarOpen] = useState(window.innerWidth > 1024);

  const ModuleIcon = () => (
    <svg fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4 text-gray-400 dark:text-slate-500">
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
    </svg>
  );

  // BASE DE DATOS DEL MENÚ
  const menuSidebarBase = [
    {
      modulo: 'Producción Agrícola',
      rolesPermitidos: [1, 2, 3,4], 
      submenus: [
        {nombre:'Terrenos - Lotes',ruta:'/agro/lote'},
        {nombre:'Campañas de Siembra/Cosecha',ruta:'/agro/campana'},
        {nombre:'Ordenes de Trabajo',ruta:'/agro/ordenes'},
        {nombre:'Gestion de Maquinaria',ruta:'/agro/maquinaria'},
        {nombre:'Bodega de Cultivos',ruta:'/agro/cultivo'},
        {nombre: 'Dispositivos IOT',ruta:'/dispositivos-iot'}
      ]
    },
    {
      modulo: 'Ventas y Comercialización',
      rolesPermitidos: [1, 2, 3, 4], 
      submenus: [
        {nombre: 'Ventas - Pedidos', ruta:'/ventas/catalogo'},
        {nombre: 'Historial de Pedidos', ruta:'/ventas/historial'}
      ]
    },
    {
      modulo: 'CRM y Clientes',
      rolesPermitidos: [1, 2], 
      submenus: [
        {nombre:'Gestión de Clientes',ruta:'/crm/clientes'},
        {nombre:'Programa de Fidelización',ruta:'/crm/fidelizacion'}
      ]
    },
    {
      modulo: 'Reportes y Datos',
      rolesPermitidos: [1,2], 
      submenus: [
        { nombre: 'Dashboard Directivo', ruta: '/reportes'},
        { nombre: 'Importacion/Exportacion de Datos Masivos', ruta: '/import-export'},
      ]
    },
    {
      modulo: 'Logística de Distribución',
      rolesPermitidos: [1, 2],
      submenus: [
        {nombre: 'Gestión de Rutas', ruta: '/logistica/rutas'}
      ]
    },
    {
      modulo: 'Seguridad y Accesos',
      rolesPermitidos: [1], 
      submenus: [
        { nombre: 'Usuarios y Roles', ruta: '/security/users' },
        { nombre: 'Tenants/Empresas', ruta: 'security/tenants'},
        { nombre: 'Roles y Funcionalidades', ruta: '/security/roles' },
        { nombre: 'Bitácora del Sistema', ruta: '/security/audit' },
        { nombre: 'BackUp y Respaldo', ruta: 'security/backup'},
      ]
    }
  ];

  // FILTRADO DE SEGURIDAD DIRECTO
  const menuSidebar = menuSidebarBase.filter(mod => {
    if (!user || !user.id_rol) return false; 
    return mod.rolesPermitidos.includes(Number(user.id_rol));
  });

  const vistaActual = menuSidebar
    .flatMap(m => m.submenus || [])
    .find(s => location.pathname.includes(s.ruta))?.nombre || 'Panel de Control';

  return (
    <div className="flex h-screen bg-[#F8FAFC] dark:bg-[#0F172A] font-sans antialiased overflow-hidden transition-colors duration-300">
      
      {/* SIDEBAR GLOBAL */}
      <aside 
        className={`fixed lg:static inset-y-0 left-0 z-50 bg-white dark:bg-[#1E293B] border-r border-gray-200 dark:border-slate-700/80 transition-all duration-300 ease-in-out shadow-2xl lg:shadow-none overflow-hidden
        ${isSidebarOpen ? 'w-72 translate-x-0' : 'w-0 -translate-x-full lg:translate-x-0'}
        `}
      >
        <div className="w-72 h-full flex flex-col">
          
          <div className="h-16 flex items-center justify-between px-6 border-b border-gray-200 dark:border-slate-700/80 shrink-0">
            <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/home')}>
              <img src={logoAgro} alt="Logo" className="w-7 h-7 rounded bg-white border border-gray-100 dark:border-slate-600 object-contain" />
              <span className="font-black text-[#1A5729] dark:text-[#7BC636] tracking-tight">AgroEnlace</span>
            </div>
            <button onClick={() => setIsSidebarOpen(false)} className="lg:hidden text-gray-500 hover:text-red-500 transition-colors">
              <svg fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
            {menuSidebar.length === 0 && (
              <div className="text-center p-4 text-xs font-bold text-gray-400">
                Cargando módulos o sin acceso...
              </div>
            )}

            {/* RENDERIZADO SIMPLE: Sin acordeones, solo listas limpias */}
            {menuSidebar.map((seccion) => (
              <div key={seccion.modulo} className="mb-6">
                
                {/* Título Estático del Módulo */}
                <div className="flex items-center gap-2 px-3 mb-2 opacity-70">
                  <ModuleIcon />
                  <span className="text-[10px] font-black text-gray-500 dark:text-slate-400 uppercase tracking-widest">
                    {seccion.modulo}
                  </span>
                </div>
                
                {/* Enlaces de Funcionalidades */}
                {seccion.submenus && seccion.submenus.length > 0 ? (
                  <ul className="space-y-1">
                    {seccion.submenus.map((sub) => {
                      const isActive = location.pathname.includes(sub.ruta);
                      return (
                        <li key={sub.ruta}>
                          <button
                            onClick={() => navigate(sub.ruta)}
                            className={`w-full text-left px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150 flex items-center gap-2 ${
                              isActive 
                                ? 'bg-cyan-50 dark:bg-cyan-500/10 text-cyan-700 dark:text-cyan-400 font-bold' 
                                : 'text-gray-600 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-800/50 hover:text-gray-900 dark:hover:text-slate-200'
                            }`}
                          >
                            {/* Un pequeño punto para indicar la selección activa */}
                            {isActive && <div className="w-1.5 h-1.5 rounded-full bg-cyan-500"></div>}
                            <span className={isActive ? '' : 'ml-3.5'}>{sub.nombre}</span>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                ) : (
                  <div className="px-4 py-1">
                    <span className="text-xs text-gray-400 dark:text-slate-600 italic font-medium ml-3.5">Próximamente</span>
                  </div>
                )}
                
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* Sombra oscura para móviles */}
      {isSidebarOpen && (
        <div className="fixed inset-0 bg-black/20 dark:bg-black/40 z-40 lg:hidden" onClick={() => setIsSidebarOpen(false)}></div>
      )}

      {/* ÁREA PRINCIPAL CON TOPBAR */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        
        <header className="h-16 bg-white dark:bg-[#1E293B] border-b border-gray-200 dark:border-slate-700/80 flex items-center justify-between px-6 shrink-0 transition-colors duration-300">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)} 
              className="text-gray-500 hover:text-gray-800 dark:text-slate-400 dark:hover:text-white transition-colors"
            >
              <svg fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" />
              </svg>
            </button>
            
            {!isSidebarOpen && (
              <div className="hidden sm:flex items-center gap-2 mr-2 animate-fade-in cursor-pointer" onClick={() => navigate('/home')}>
                <img src={logoAgro} alt="Logo" className="w-6 h-6 rounded border border-gray-100 dark:border-slate-600 bg-white object-contain" />
                <span className="font-black text-[#1A5729] dark:text-[#7BC636] tracking-tight">AgroEnlace</span>
              </div>
            )}

            {!isSidebarOpen && <div className="hidden sm:block h-5 w-px bg-gray-200 dark:bg-slate-700"></div>}

            <h2 className="text-lg font-bold text-gray-800 dark:text-white tracking-tight hidden sm:block">
              {vistaActual}
            </h2>
          </div>

          {/* PÍLDORA DE CONTROLES */}
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-bold text-gray-700 dark:text-slate-200">
                {user?.nombre_razon_social?.split(' ')[0] || 'Administrador'}
              </p>
            </div>
            
            <div className="flex items-center bg-gray-50 dark:bg-slate-800/50 border border-gray-200 dark:border-slate-700 rounded-full p-1 shadow-inner ml-2">
              
              <button 
                onClick={() => navigate('/home')}
                className="p-2 text-gray-500 hover:text-[#5B9D1E] dark:text-slate-400 dark:hover:text-[#7BC636] hover:bg-white dark:hover:bg-slate-700 rounded-full transition-all hover:shadow-sm flex items-center justify-center"
                title="Ir al Home"
              >
                <svg fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.592 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
                </svg>
              </button>

              <div className="w-px h-4 bg-gray-200 dark:bg-slate-600 mx-0.5"></div>

              <button 
                onClick={toggleDarkMode}
                className="p-2 text-gray-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-amber-400 hover:bg-white dark:hover:bg-slate-700 rounded-full transition-all hover:shadow-sm flex items-center justify-center"
                title={isDarkMode ? "Modo Claro" : "Modo Oscuro"}
              >
                {isDarkMode ? (
                  <svg fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4"><path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" /></svg>
                ) : (
                  <svg fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4"><path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" /></svg>
                )}
              </button>

              <div className="w-px h-4 bg-gray-200 dark:bg-slate-600 mx-0.5"></div>

              <button
                onClick={() => navigate('/profile')}
                className="p-2 text-gray-500 hover:text-[#5B9D1E] dark:text-slate-400 dark:hover:text-[#7BC636] hover:bg-white dark:hover:bg-slate-700 rounded-full transition-all hover:shadow-sm flex items-center justify-center"
                title="Mi Perfil"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4"><path strokeLinecap="round" strokeLinejoin="round" d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
              </button>

              <div className="w-px h-4 bg-gray-200 dark:bg-slate-600 mx-0.5"></div>

              <button
                onClick={handleLogout}
                className="p-2 text-gray-400 hover:text-red-600 dark:text-slate-500 dark:hover:text-red-400 hover:bg-white dark:hover:bg-slate-700 rounded-full transition-all hover:shadow-sm flex items-center justify-center"
                title="Cerrar Sesión"
              >
                <svg fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-4 h-4"><path strokeLinecap="round" strokeLinejoin="round" d="M5.636 5.636a9 9 0 1012.728 0M12 3v9" /></svg>
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6 md:p-8 custom-scrollbar">
          <Outlet /> 
        </main>
      </div>
    </div>
  );
}
