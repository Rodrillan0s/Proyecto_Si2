import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/auth_store';

const API_URL = import.meta.env.VITE_API_URL;

export default function Profile() {
  const token = useAuthStore((state) => state.token);
  const user = useAuthStore((state) => state.user);
  
  const navigate = useNavigate();

  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  const [profileData, setProfileData] = useState(null);
  const [formData, setFormData] = useState({
    nombre_razon_social: '',
    correo: '',
    telefono: '',
    direccion: '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await fetch(`${API_URL}/profile`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });

        const result = await response.json();

        if (result.success) {
          const data = result.data; 
          if(!data) return;

          setProfileData(data);
          setFormData(prev => ({
            ...prev,
            nombre_razon_social: data.nombre_razon_social || '',
            correo: data.correo || '',
            telefono: data.telefono || '',
            direccion: data.direccion || '',
          }));
        }
      } catch (error) {
        console.error("Error cargando perfil:", error);
      } finally {
        setIsLoading(false);
      }
    };

    if (token) fetchProfile();
  }, [token]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleCancel = () => {
    setFormData(prev => ({
      ...prev,
      nombre_razon_social: profileData?.nombre_razon_social || '',
      correo: profileData?.correo || '',
      telefono: profileData?.telefono || '',
      direccion: profileData?.direccion || '',
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
    }));
    setIsEditing(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    
    if (formData.newPassword && formData.newPassword !== formData.confirmPassword) {
      alert("Las nuevas contraseñas no coinciden");
      return;
    }

    try {
      const response = await fetch(`${API_URL}/update-profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      const result = await response.json();

      if (result.success) {
        alert("Perfil actualizado con éxito");
        setIsEditing(false);
        // Refrescamos los datos para ver los cambios reflejados
        window.location.reload(); 
      } else {
        alert(result.message);
      }
    } catch (error) {
      console.error("Error al actualizar:", error);
    }
  };

  const getInitials = (name) => {
    if (!name) return 'AE';
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] dark:bg-[#0B1121] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-4 border-[#5B9D1E]/30 border-t-[#5B9D1E] rounded-full animate-spin"></div>
          <span className="text-sm font-medium text-slate-500 tracking-wide">Sincronizando perfil...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] dark:bg-[#0B1121] font-sans text-slate-900 dark:text-slate-100 pb-12">
      
      {/* HEADER BREADCRUMB */}
      <div className="bg-white dark:bg-[#111827] border-b border-slate-200 dark:border-slate-800 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center gap-3 text-sm font-medium text-slate-500 dark:text-slate-400">
          <button onClick={() => navigate(-1)} className="hover:text-[#5B9D1E] transition-colors flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
            Volver
          </button>
          <span className="text-slate-300 dark:text-slate-600">|</span>
          <span className="text-slate-900 dark:text-slate-200">Configuración de Cuenta</span>
        </div>
      </div>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">Mi Perfil</h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Administra tu identidad y preferencias de seguridad.</p>
          </div>
          {!isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="hidden sm:flex items-center gap-2 px-4 py-2 bg-white dark:bg-[#1F2937] border border-slate-300 dark:border-slate-700 rounded-lg text-sm font-semibold hover:bg-slate-50 dark:hover:bg-slate-800 transition-all shadow-sm"
            >
              <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
              Editar Perfil
            </button>
          )}
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          
          {/* COLUMNA IZQUIERDA (Info Fija) */}
          <div className="w-full lg:w-1/3 flex flex-col gap-6">
            
            {/* Tarjeta de Identidad */}
            <div className="bg-white dark:bg-[#111827] rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm flex flex-col items-center text-center relative overflow-hidden">
              <div className="absolute top-0 w-full h-24 bg-gradient-to-r from-[#1A5729] to-[#5B9D1E] opacity-90"></div>
              
              <div className="relative mt-8 mb-4">
                <div className="h-24 w-24 rounded-full bg-white dark:bg-[#111827] p-1 shadow-md">
                  <div className="w-full h-full rounded-full bg-[#1A5729] flex items-center justify-center text-white text-2xl font-bold">
                    {getInitials(profileData?.nombre_razon_social)}
                  </div>
                </div>
                <div className="absolute bottom-1 right-1 w-5 h-5 bg-emerald-500 border-2 border-white dark:border-[#111827] rounded-full" title="Cuenta Activa"></div>
              </div>

              <h2 className="text-xl font-bold text-slate-900 dark:text-white">{profileData?.nombre_razon_social}</h2>
              <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mt-1">@{profileData?.user_name}</p>

              <div className="mt-5 w-full pt-5 border-t border-slate-100 dark:border-slate-800 space-y-3 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-slate-500">Rol</span>
                  <span className="font-semibold text-[#5B9D1E] uppercase">{profileData?.rol}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-500">Documento</span>
                  <span className="font-medium text-slate-700 dark:text-slate-300">{profileData?.documento_identidad}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-500">Registro</span>
                  <span className="font-medium text-slate-700 dark:text-slate-300">
                    {new Date(profileData?.fecha_registro).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Botón en Móvil */}
            {!isEditing && (
              <button onClick={() => setIsEditing(true)} className="sm:hidden w-full flex items-center justify-center gap-2 px-4 py-3 bg-white dark:bg-[#1F2937] border border-slate-300 dark:border-slate-700 rounded-xl text-sm font-semibold shadow-sm">
                Editar Perfil
              </button>
            )}
          </div>

          {/* COLUMNA DERECHA (Formulario / Detalles) */}
          <div className="w-full lg:w-2/3">
            <form onSubmit={handleSubmit} className="bg-white dark:bg-[#111827] rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden transition-all">
              
              <div className="p-6 md:p-8">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
                  <svg className="w-5 h-5 text-[#5B9D1E]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2M15 11h3m-3 4h2" /></svg>
                  Información de Contacto
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Nombre */}
                  <div className="md:col-span-2">
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Nombre o Razón Social</label>
                    {!isEditing ? (
                      <p className="text-slate-900 dark:text-slate-200 font-medium py-1">{profileData?.nombre_razon_social}</p>
                    ) : (
                      <input type="text" name="nombre_razon_social" value={formData.nombre_razon_social} onChange={handleChange} className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-[#1F2937] px-4 py-2.5 text-sm focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent outline-none transition-all text-slate-900 dark:text-white" />
                    )}
                  </div>

                  {/* Correo */}
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Correo Electrónico</label>
                    {!isEditing ? (
                      <p className="text-slate-900 dark:text-slate-200 font-medium py-1">{profileData?.correo}</p>
                    ) : (
                      <input type="email" name="correo" value={formData.correo} onChange={handleChange} className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-[#1F2937] px-4 py-2.5 text-sm focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent outline-none transition-all text-slate-900 dark:text-white" />
                    )}
                  </div>

                  {/* Teléfono */}
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Teléfono de Contacto</label>
                    {!isEditing ? (
                      <p className="text-slate-900 dark:text-slate-200 font-medium py-1">{profileData?.telefono || 'No registrado'}</p>
                    ) : (
                      <input type="text" name="telefono" value={formData.telefono} onChange={handleChange} className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-[#1F2937] px-4 py-2.5 text-sm focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent outline-none transition-all text-slate-900 dark:text-white" />
                    )}
                  </div>

                  {/* Dirección */}
                  <div className="md:col-span-2">
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Dirección Física</label>
                    {!isEditing ? (
                      <p className="text-slate-900 dark:text-slate-200 font-medium py-1">{profileData?.direccion || 'No registrada'}</p>
                    ) : (
                      <textarea name="direccion" rows={2} value={formData.direccion} onChange={handleChange} className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-[#1F2937] px-4 py-2.5 text-sm focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent outline-none transition-all text-slate-900 dark:text-white resize-none" />
                    )}
                  </div>
                </div>
              </div>

              {/* SECCIÓN SEGURIDAD (Se despliega suavemente) */}
              {isEditing && (
                <div className="px-6 md:px-8 py-6 bg-slate-50 dark:bg-[#1F2937]/30 border-t border-slate-200 dark:border-slate-800 animate-in fade-in slide-in-from-top-4 duration-300">
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                    <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                    Seguridad
                  </h3>
                  <p className="text-xs text-slate-500 mb-6">Deja estos campos en blanco si no deseas cambiar tu contraseña.</p>
                  
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Nueva Contraseña</label>
                        <input type="password" name="newPassword" value={formData.newPassword} onChange={handleChange} className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-[#111827] px-4 py-2.5 text-sm focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent outline-none transition-all text-slate-900 dark:text-white" />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Repetir Contraseña</label>
                        <input type="password" name="confirmPassword" value={formData.confirmPassword} onChange={handleChange} className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-[#111827] px-4 py-2.5 text-sm focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent outline-none transition-all text-slate-900 dark:text-white" />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ACTION BUTTONS */}
              {isEditing && (
                <div className="px-6 md:px-8 py-5 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111827] flex items-center justify-end gap-3 rounded-b-2xl">
                  <button type="button" onClick={handleCancel} className="px-5 py-2.5 rounded-lg text-sm font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                    Cancelar
                  </button>
                  <button type="submit" className="px-6 py-2.5 rounded-lg text-sm font-semibold text-white bg-[#5B9D1E] hover:bg-[#467c17] shadow-md shadow-[#5B9D1E]/20 transition-all transform active:scale-95">
                    Guardar Cambios
                  </button>
                </div>
              )}

            </form>
          </div>
        </div>

      </main>
    </div>
  );
}