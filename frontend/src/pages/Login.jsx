import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import logoAgro from '../assets/LOGO.png'; 
import { useAuthStore } from '../store/auth_store';

export default function Login() {
  const API_URL = import.meta.env.VITE_API_URL;
  const [user, setUser] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const navigate = useNavigate();
  const { login } = useAuthStore();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_input: user, password: password }),
      });
      const data = await response.json();
      if (!data.success) throw new Error(data.message || 'Credenciales incorrectas');
      login(data.access_token, data.user);
      navigate('/home'); 
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    // h-screen + overflow-hidden evita el scroll global
    <div className="h-screen w-full bg-[#EBF5FF] flex flex-col items-center justify-center p-4 overflow-hidden font-sans antialiased">
      
      {/* Línea decorativa superior */}
      <div className="fixed top-0 left-0 w-full h-1 bg-[#1A5729] z-50"></div>

      <div className="w-full max-w-[400px] flex flex-col gap-4">
        
        {/* TARJETA DE LOGIN */}
        <div className="bg-white border border-slate-200 shadow-xl rounded-lg overflow-hidden">
          
          {/* Header Compacto */}
          <div className="bg-slate-50 border-b border-slate-100 px-6 py-4 md:py-6 text-center">
            <Link to="/">
              <img src={logoAgro} alt="Logo" className="w-16 h-16 md:w-20 md:h-20 mx-auto mb-2 object-contain" />
            </Link>
            <h2 className="text-lg font-black text-slate-800 uppercase tracking-widest">Acceso al Sistema</h2>
          </div>

          <div className="p-6 md:p-8">
            {error && (
              <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-3 rounded mb-4 text-[10px] font-bold animate-shake">
                {error.toUpperCase()}
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Usuario</label>
                <input
                  type="text" required value={user} onChange={(e) => setUser(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded bg-slate-50/50 text-sm outline-none focus:border-[#1A5729]"
                  placeholder="admin@agro.com"
                />
              </div>

              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest">Contraseña</label>
                </div>
                <input
                  type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded bg-slate-50/50 text-sm outline-none focus:border-[#1A5729]"
                  placeholder="••••••••"
                />
              </div>

              <button
                type="submit" disabled={loading}
                className={`w-full py-3 rounded font-black text-white text-[11px] tracking-[0.2em] transition-all ${
                  loading ? 'bg-slate-400' : 'bg-[#1A5729] hover:bg-[#144320] active:scale-95'
                }`}
              >
                {loading ? "AUTENTICANDO..." : "INGRESAR"}
              </button>
            </form>
          </div>
        </div>

        {/* BANNER DE PRUEBA COMPACTO */}
        <div className="bg-blue-600/10 border border-blue-200 rounded-lg p-3 flex items-center justify-between backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="hidden sm:block bg-blue-600 p-1.5 rounded text-white">
              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z"/></svg>
            </div>
            <div>
              <p className="text-[9px] font-black text-blue-700 uppercase tracking-tighter">Usuario Demo</p>
              <p className="text-[11px] text-slate-600 font-bold">admin@agro.com / admin123</p>
            </div>
          </div>
          <button 
            onClick={() => {setUser('admin@agro.com'); setPassword('admin123');}}
            className="text-[9px] font-black bg-blue-600 text-white px-3 py-1.5 rounded uppercase hover:bg-blue-700 transition-transform active:scale-90"
          >
            Cargar
          </button>
        </div>

        {/* Footer mínimo */}
        <p className="text-[9px] text-center text-slate-400 font-bold uppercase tracking-[0.2em] mt-2">
          UAGRM • 2026
        </p>

      </div>
    </div>
  );
}