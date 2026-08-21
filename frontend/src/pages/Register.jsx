import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import logoAgro from '../assets/LOGO.png'; 

export default function Register() {

  const API_URL = import.meta.env.VITE_API_URL;

  //ESTADOS REACT
  const [userName, setUserName] = useState('');
  const [documentoIdentidad, setDocumentoIdentidad] = useState('');
  const [nombreRazonSocial, setNombreRazonSocial] = useState('');
  const [correo, setCorreo] = useState('');
  const [telefono, setTelefono] = useState('');
  const [direccion, setDireccion] = useState(''); // Opcional
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    
    //VALIDAMOS QUE SEA UN CORREO VALIDO CON UN REGEX
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (!emailRegex.test(correo)) {
      setError('Por favor, ingresa un correo electrónico válido.');
      return;
    }

    //VALIDAMOS QUE HAYA ESCRITO BIEN LA CONTRASEÑA
    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden.');
      return;
    }

    //CONTRASEÑA MAYOR A 6 CARACTERES
    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres.');
      return;
    }

    setLoading(true);
    
    try 
    {
      const response = await fetch(`${API_URL}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          user: userName,
          doc: documentoIdentidad,
          name: nombreRazonSocial,
          mail: correo,
          number: telefono,
          dir: direccion,
          password: password 
        }),
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message || 'Error al registrar el usuario.');
      }

      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 2000); 
      
    } 
    catch (err) 
    {
      setError(err.message);
    } 
    finally 
    {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#D9F0FB] flex items-center justify-center p-4 py-10 font-sans antialiased">
      
      {/* Tarjeta más ancha (max-w-2xl) para soportar 2 columnas */}
      <div className="bg-white p-8 md:p-10 rounded-xl shadow-2xl w-full max-w-2xl border border-white/20 relative overflow-hidden">
        
        <div className="absolute top-0 left-0 w-full h-1.5 bg-[#5B9D1E]"></div>

        <div className="text-center mb-6">
          <Link to="/">
            <img src={logoAgro} alt="Logo" className="w-16 h-16 mx-auto mb-3 rounded-xl shadow-sm hover:scale-105 transition-transform cursor-pointer" />
          </Link>
          <h2 className="text-2xl font-black text-[#1A5729] tracking-tight">Crear Cuenta</h2>
          <p className="text-gray-500 text-xs font-medium uppercase tracking-widest mt-1 opacity-70">Registro Institucional</p>
        </div>

        {/* MENSAJE DE ERROR */}
        {error && (
          <div className="bg-red-50/80 border border-red-100 text-red-600 px-4 py-3.5 rounded-lg mb-5 text-sm flex items-center shadow-sm animate-shake transition-all">
            <svg className="w-5 h-5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span className="font-medium tracking-wide">{error}</span>
          </div>
        )}

        {/* MENSAJE DE EXITO */}
        {success && (
          <div className="bg-[#F4F9F1] border border-[#5B9D1E]/30 text-[#1A5729] px-4 py-3.5 rounded-lg mb-5 text-sm flex items-center shadow-sm transition-all">
            <svg className="w-5 h-5 mr-3 text-[#5B9D1E] flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span className="font-medium tracking-wide">Cuenta creada exitosamente. Redirigiendo al login...</span>
          </div>
        )}

        {/* Formulario en Grid */}
        <form onSubmit={handleRegister} className="space-y-4">
          
          {/* Fila 1: Usuario y CI/NIT */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] font-bold text-[#1A5729] uppercase tracking-wider mb-1">
                Nombre de Usuario *
              </label>
              <input
                type="text"
                required
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent outline-none transition-all bg-gray-50/50 text-sm"
                placeholder="Ej: jperez_agro"
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-[#1A5729] uppercase tracking-wider mb-1">
                CI / NIT *
              </label>
              <input
                type="text"
                required
                value={documentoIdentidad}
                onChange={(e) => setDocumentoIdentidad(e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent outline-none transition-all bg-gray-50/50 text-sm"
                placeholder="Nro. Documento"
              />
            </div>
          </div>

          {/* Fila 2: Nombre Completo / Razón Social (Ocupa todo el ancho) */}
          <div>
            <label className="block text-[11px] font-bold text-[#1A5729] uppercase tracking-wider mb-1">
              Nombre Completo o Razón Social *
            </label>
            <input
              type="text"
              required
              value={nombreRazonSocial}
              onChange={(e) => setNombreRazonSocial(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent outline-none transition-all bg-gray-50/50 text-sm"
              placeholder="Nombre legal o empresa"
            />
          </div>

          {/* Fila 3: Correo y Teléfono */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] font-bold text-[#1A5729] uppercase tracking-wider mb-1">
                Correo Electrónico *
              </label>
              <input
                type="email"
                required
                value={correo}
                onChange={(e) => setCorreo(e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent outline-none transition-all bg-gray-50/50 text-sm"
                placeholder="correo@ejemplo.com"
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-[#1A5729] uppercase tracking-wider mb-1">
                Teléfono *
              </label>
              <input
                type="tel"
                required
                value={telefono}
                onChange={(e) => setTelefono(e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent outline-none transition-all bg-gray-50/50 text-sm"
                placeholder="+591 7XXXXXXX"
              />
            </div>
          </div>

          {/* Fila 4: Dirección (Opcional, sin 'required') */}
          <div>
            <label className="block text-[11px] font-bold text-[#1A5729] uppercase tracking-wider mb-1">
              Dirección (Opcional)
            </label>
            <input
              type="text"
              value={direccion}
              onChange={(e) => setDireccion(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent outline-none transition-all bg-gray-50/50 text-sm"
              placeholder="Av. Busch, 2do Anillo..."
            />
          </div>

          {/* Fila 5: Contraseñas */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] font-bold text-[#1A5729] uppercase tracking-wider mb-1">
                Contraseña *
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent outline-none transition-all bg-gray-50/50 text-sm"
                placeholder="••••••••"
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-[#1A5729] uppercase tracking-wider mb-1">
                Confirmar Contraseña *
              </label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#5B9D1E] focus:border-transparent outline-none transition-all bg-gray-50/50 text-sm"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || success}
            className={`w-full py-3 mt-4 rounded-lg font-bold text-white shadow-lg transition-all duration-300 transform active:scale-[0.98] flex items-center justify-center ${
              loading || success ? 'bg-gray-400 cursor-not-allowed' : 'bg-[#2D6A4F] hover:bg-[#1B4332] hover:shadow-[#2D6A4F]/20'
            }`}
          >
            {loading ? "PROCESANDO..." : "REGISTRAR USUARIO"}
          </button>
        </form>

        <div className="mt-6 pt-5 border-t border-gray-100 text-center">
          <p className="text-xs text-gray-500 font-medium">
            ¿Ya tienes una cuenta?{' '}
            <Link to="/login" className="text-[#5B9D1E] font-bold hover:text-[#1A5729] transition-colors">
              INICIA SESIÓN AQUÍ
            </Link>
          </p>
        </div>
        
      </div>
    </div>
  );
}