import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { despertarBackend } from "./services/api";

// COMPONENTES SEGURIDAD Y LAYOUT
import ProtectedRoute from "./components/ProtectedRoute";
import AdminRoute from "./components/AdminRoute"; 
import DashboardLayout from "./components/DashboardLayout"; 

// PANTALLAS
import Login from "./pages/Login";
import Welcome from "./pages/Welcome";
import Register from "./pages/Register";
import Home from "./pages/Home";
import SecurityUsers from "./pages/SecurityUsers"; 
import SecurityAudit from "./pages/SecurityAudit";
import SecurityRole from "./pages/SecurityRole";
import SecurityTenants from "./pages/SecurityTenant";
import SecurityBackup from "./pages/SecurityBackup";
import AgroLotes from "./pages/AgroLotes";
import AgroCampanias from "./pages/AgroCampanias";
import AgroMaquinarias from "./pages/AgroMaquinarias";
import AgroBodega from "./pages/AgroBodega";
import Downloads from "./pages/Downloads";
import Profile from "./pages/Profile";
import AgroOrdenes from "./pages/AgroOrdenes";
import AgroCRM from "./pages/ClientesGestion";
import VentasCatalogo from "./pages/VentasCatalogo";
import HistorialPedidos from "./pages/VentasHistorial";
import ReportesBi from "./pages/ReportesBi";
import ImportarMasivo from "./pages/ImportarMasivo";
import LogisticaRutas from "./pages/LogisticaRutas";
import CrmFidelizacion from "./pages/CrmFidelizacion";
import AgroDispositivos from "./pages/AgroDispositivos";


function AnimatedRoutes() {
  const location = useLocation();
  const [displayLocation, setDisplayLocation] = useState(location);
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    if (location.pathname !== displayLocation.pathname) {
      setIsTransitioning(true);
      const timer = setTimeout(() => {
        setDisplayLocation(location);
        setIsTransitioning(false);
      }, 300); 
      return () => clearTimeout(timer);
    }
  }, [location, displayLocation]);

  return (
    <div className={`transition-opacity duration-300 ease-linear ${isTransitioning ? 'opacity-0' : 'opacity-100'}`}>
      <Routes location={displayLocation}>
        
        {/* PÚBLICAS */}
        <Route path="/" element={<Welcome />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        

        {/* PRIVADAS GENERALES (Cualquier usuario logueado: Admin, Supervisor, Empleado, Cliente) */}
        <Route element={<ProtectedRoute />}>
          <Route path="/home" element={<Home />} />
          <Route path="/downloads" element={<Downloads />} />
          <Route path='/profile' element={<Profile/>}/>
          
          {/* EL SIDEBAR DEBE ESTAR DISPONIBLE PARA TODOS LOS LOGUEADOS */}
          <Route element={<DashboardLayout />}>
            
            {/* Rutas compartidas (Las validaciones de qué pueden ver/hacer están dentro de cada componente y en tu menuSidebarBase) */}
            <Route path="/agro/lote" element={<AgroLotes />} />
            <Route path="/agro/campana" element={<AgroCampanias/>} />
            <Route path="/agro/maquinaria" element={<AgroMaquinarias/>} />
            <Route path="/agro/cultivo" element={<AgroBodega />} />
            <Route path="/crm/clientes" element={<AgroCRM />} />
            <Route path="/crm/fidelizacion" element={<CrmFidelizacion />} />
            <Route path="/agro/ordenes" element={<AgroOrdenes/>} />
            
            <Route path="/ventas/catalogo" element={<VentasCatalogo />} />
            <Route path="/ventas/historial" element={<HistorialPedidos />} />
            
            <Route path="/logistica/rutas" element={<LogisticaRutas />} />

            <Route path="/dispositivos-iot" element={<AgroDispositivos/>} />
            
            {/* PRIVADAS SOLO ADMINISTRADORES (Rol 1) */}
            <Route element={<AdminRoute />}>
              <Route path="/security/users" element={<SecurityUsers />} />
              <Route path="/security/roles" element={<SecurityRole/>} />
              <Route path="/security/audit" element={<SecurityAudit/>} />
              <Route path="/security/tenants" element={<SecurityTenants/>} />
              <Route path="/security/backup" element={<SecurityBackup/>} />
              <Route path="/reportes" element={<ReportesBi/>} />
              <Route path="/import-export" element={<ImportarMasivo/>} />
            </Route>

          </Route>
        </Route>

      </Routes>
    </div>
  );
}

export default function App() {
  useEffect(() => {
    despertarBackend();
  }, []);
  
  return (
    <BrowserRouter>
      {/* El fondo base se mantiene para las pantallas de Login/Welcome */}
      <div className="bg-[#D9F0FB] min-h-screen">
        <AnimatedRoutes />
      </div>
    </BrowserRouter>
  );
}
