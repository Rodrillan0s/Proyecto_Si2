import { useState, useEffect } from 'react';
import { useAuthStore } from '../store/auth_store';

const API_URL = import.meta.env.VITE_API_URL;

const TIPOS = ['TELEMETRIA', 'HUMEDAD', 'TEMPERATURA', 'CLIMA', 'SUELO'];
const ESTADOS = ['ACTIVO', 'INACTIVO', 'MANTENIMIENTO'];

export default function AgroDispositivos() {
  const token = useAuthStore((state) => state.token);

  const [dispositivos, setDispositivos] = useState([]);
  const [terrenos, setTerrenos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const [showModal, setShowModal] = useState(false);
  const [step, setStep] = useState(1);
  const [linking, setLinking] = useState(false);

  const initialForm = {
    codigo_dispositivo: '',
    nombre_dispositivo: '',
    tipo_dispositivo: 'TELEMETRIA',
    estado: 'ACTIVO',
    nro_lote: '',
  };

  const [formData, setFormData] = useState(initialForm);

  const fetchDispositivos = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/iot/dispositivos`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      const result = await response.json();

      if (result.success) {
        setDispositivos(result.dispositivos || []);
      } else {
        alert(result.message || 'No se pudieron cargar los dispositivos.');
      }
    } catch (error) {
      console.error('Error cargando dispositivos:', error);
      alert('Error de comunicación con el servidor.');
    } finally {
      setLoading(false);
    }
  };

  const fetchTerrenos = async () => {
    try {
      const response = await fetch(`${API_URL}/get-terrenos`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      const result = await response.json();

      if (result.success) {
        setTerrenos(result.list_terrenos || []);
      }
    } catch (error) {
      console.error('Error cargando terrenos:', error);
    }
  };

  useEffect(() => {
    if (token) {
      fetchDispositivos();
      fetchTerrenos();
    }
  }, [token]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const openAddModal = () => {
    setFormData(initialForm);
    setStep(1);
    setLinking(false);
    setShowModal(true);
  };

  const validateStep = () => {
    if (step === 1) {
      if (!formData.codigo_dispositivo.trim()) {
        alert('Ingrese el código del dispositivo.');
        return false;
      }

      if (!formData.nombre_dispositivo.trim()) {
        alert('Ingrese el nombre del dispositivo.');
        return false;
      }
    }

    if (step === 2 && !formData.nro_lote) {
      alert('Seleccione una parcela o lote.');
      return false;
    }

    return true;
  };

  const nextStep = () => {
    if (!validateStep()) return;
    setStep(step + 1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateStep()) return;

    setLinking(true);

    const payload = {
      ...formData,
      nro_lote: parseInt(formData.nro_lote, 10),
    };

    try {
      await new Promise((resolve) => setTimeout(resolve, 900));

      const response = await fetch(`${API_URL}/iot/dispositivos`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const result = await response.json();

      if (result.success) {
        setShowModal(false);
        setFormData(initialForm);
        fetchDispositivos();
      } else {
        alert(`Atención: ${result.message}`);
      }
    } catch (error) {
      alert('Error de comunicación con el servidor.');
    } finally {
      setLinking(false);
    }
  };

  const cambiarEstado = async (dispositivo, nuevoEstado) => {
    try {
      const response = await fetch(`${API_URL}/iot/dispositivos/estado`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          id_dispositivo: dispositivo.id_dispositivo,
          estado: nuevoEstado,
        }),
      });

      const result = await response.json();

      if (result.success) {
        fetchDispositivos();
      } else {
        alert(result.message || 'No se pudo actualizar el estado.');
      }
    } catch (error) {
      alert('Error al actualizar el estado.');
    }
  };

  const filtered = dispositivos.filter((d) => {
    const term = searchTerm.toLowerCase();

    return (
      String(d.codigo_dispositivo || '').toLowerCase().includes(term) ||
      String(d.nombre_dispositivo || '').toLowerCase().includes(term) ||
      String(d.tipo_dispositivo || '').toLowerCase().includes(term) ||
      String(d.estado || '').toLowerCase().includes(term) ||
      String(d.nombre_sector || '').toLowerCase().includes(term)
    );
  });

  const stats = {
    total: dispositivos.length,
    activos: dispositivos.filter((d) => d.estado === 'ACTIVO').length,
    mantenimiento: dispositivos.filter((d) => d.estado === 'MANTENIMIENTO').length,
    lotes: [...new Set(dispositivos.map((d) => d.nro_lote))].length,
  };

  const selectedTerreno = terrenos.find((t) => String(t.nro_lote) === String(formData.nro_lote));

  const getEstadoStyle = (estado) => {
    if (estado === 'ACTIVO') return 'bg-emerald-50 text-emerald-700';
    if (estado === 'MANTENIMIENTO') return 'bg-amber-50 text-amber-700';
    return 'bg-slate-100 text-slate-500';
  };

  const getEstadoPulse = (estado) => {
    if (estado === 'ACTIVO') return 'bg-emerald-400';
    if (estado === 'MANTENIMIENTO') return 'bg-amber-400';
    return 'bg-slate-400';
  };

  const formatFecha = (fecha) => {
    if (!fecha) return 'Sin fecha';
    return new Date(fecha).toLocaleDateString('es-BO', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  };

  return (
    <div className="p-4 md:p-8 animate-in fade-in duration-500 bg-slate-50 min-h-screen max-w-[100vw] overflow-x-hidden">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 md:mb-8 gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-black text-slate-800 tracking-tight flex items-center gap-3">
            <div className="w-2 h-6 md:h-8 bg-[#1A5729]"></div>
            DISPOSITIVOS IOT
          </h1>
          <p className="text-[9px] md:text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mt-1 ml-5">
            Vinculación de sensores a parcelas agrícolas
          </p>
        </div>

        <div className="flex flex-col sm:flex-row w-full md:w-auto gap-3">
          <div className="relative flex-1 md:w-72">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              placeholder="BUSCAR SENSOR, CÓDIGO O PARCELA..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 border border-slate-200 rounded-md text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white shadow-sm"
            />
          </div>

          <button
            onClick={openAddModal}
            className="bg-[#1A5729] hover:bg-[#144320] text-white px-6 py-2.5 rounded-md font-black text-[10px] uppercase tracking-widest transition-all active:scale-95 shadow-md flex items-center justify-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            VINCULAR SENSOR
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-6 md:mb-8">
        <KpiCard title="Total" value={stats.total} color="slate" icon="wifi" />
        <KpiCard title="Activos" value={stats.activos} color="emerald" icon="check" />
        <KpiCard title="Mant." value={stats.mantenimiento} color="amber" icon="tool" />
        <KpiCard title="Parcelas" value={stats.lotes} color="blue" icon="map" />
      </div>

      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden w-full">
        <div className="overflow-x-auto w-full custom-scrollbar">
          <table className="w-full min-w-[900px] text-left border-collapse">
            <thead>
              <tr className="bg-slate-100 border-b border-slate-200 text-[10px] font-black text-slate-500 uppercase tracking-widest">
                <th className="px-6 py-4">ID</th>
                <th className="px-6 py-4">Dispositivo</th>
                <th className="px-6 py-4">Parcela</th>
                <th className="px-6 py-4">Tipo</th>
                <th className="px-6 py-4">Estado</th>
                <th className="px-6 py-4">Vinculación</th>
                <th className="px-6 py-4 text-center">Gestión</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan="7" className="text-center py-20 text-slate-400 font-bold uppercase text-[10px] tracking-widest">
                    Sincronizando dispositivos...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-20 text-slate-400 font-bold uppercase text-[10px] tracking-widest">
                    No hay dispositivos registrados
                  </td>
                </tr>
              ) : (
                filtered.map((d) => (
                  <tr key={d.id_dispositivo} className="hover:bg-slate-50 transition-colors group">
                    <td className="px-6 py-4 font-mono text-[10px] font-bold text-slate-400">
                      IOT-{String(d.id_dispositivo).padStart(4, '0')}
                    </td>

                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="relative bg-slate-100 p-2 rounded-md text-slate-400 shrink-0">
                          <span className={`absolute -right-1 -top-1 w-2.5 h-2.5 rounded-full ${getEstadoPulse(d.estado)}`}></span>
                          <WifiIcon className="w-5 h-5" />
                        </div>
                        <div className="min-w-0">
                          <div className="font-black text-slate-800 text-xs uppercase truncate">
                            {d.nombre_dispositivo}
                          </div>
                          <span className="inline-block mt-0.5 px-2 py-0.5 bg-emerald-50 text-emerald-700 text-[9px] font-black uppercase tracking-widest rounded">
                            {d.codigo_dispositivo}
                          </span>
                        </div>
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <div className="font-black text-slate-700 text-xs uppercase">
                        {d.nombre_sector || 'SIN SECTOR'}
                      </div>
                      <div className="text-[10px] font-bold text-slate-400 uppercase">
                        Lote Nro. {d.nro_lote}
                      </div>
                    </td>

                    <td className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">
                      {d.tipo_dispositivo}
                    </td>

                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-[9px] font-black uppercase tracking-widest ${getEstadoStyle(d.estado)}`}>
                        {d.estado}
                      </span>
                    </td>

                    <td className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">
                      {formatFecha(d.fecha_vinculacion)}
                    </td>

                    <td className="px-6 py-4 text-center">
                      <select
                        value={d.estado}
                        onChange={(e) => cambiarEstado(d, e.target.value)}
                        className="px-3 py-2 border border-slate-200 rounded-md text-[10px] font-black uppercase outline-none focus:border-[#1A5729] bg-white cursor-pointer"
                      >
                        {ESTADOS.map((estado) => (
                          <option key={estado} value={estado}>{estado}</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-2 sm:p-4 bg-slate-900/70 backdrop-blur-sm">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-5xl flex flex-col max-h-[95vh] border border-slate-300 animate-in zoom-in-95 duration-200">
            <div className="bg-[#1A5729] px-4 sm:px-8 py-4 sm:py-5 flex justify-between items-center text-white shrink-0">
              <div className="flex items-center gap-3">
                <div className="bg-white/20 p-2 rounded-md hidden sm:block">
                  <WifiIcon className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm sm:text-base font-black uppercase tracking-widest">
                    VINCULAR DISPOSITIVO IOT
                  </h3>
                  <p className="text-[9px] sm:text-[10px] text-emerald-100 font-bold uppercase mt-0.5 tracking-wider">
                    Flujo guiado de conexión a parcela agrícola
                  </p>
                </div>
              </div>

              <button
                onClick={() => setShowModal(false)}
                className="text-emerald-100 hover:text-white hover:bg-white/10 p-2 rounded-md transition-colors shrink-0"
              >
                <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-4 sm:p-8 bg-slate-50 overflow-y-auto custom-scrollbar">
              <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-4 sm:gap-6">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    {[1, 2, 3].map((n) => (
                      <div key={n} className="flex items-center flex-1">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-black transition-all ${
                          step >= n ? 'bg-[#1A5729] text-white' : 'bg-slate-200 text-slate-500'
                        }`}>
                          {n}
                        </div>
                        {n < 3 && (
                          <div className={`h-1 flex-1 mx-2 rounded transition-all ${
                            step > n ? 'bg-[#1A5729]' : 'bg-slate-200'
                          }`} />
                        )}
                      </div>
                    ))}
                  </div>

                  {step === 1 && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-white p-4 sm:p-6 rounded-md border border-slate-200 shadow-sm">
                      <InputField
                        label="Código del dispositivo *"
                        name="codigo_dispositivo"
                        value={formData.codigo_dispositivo}
                        onChange={handleChange}
                        placeholder="EJ: IOT-001"
                      />

                      <InputField
                        label="Nombre del dispositivo *"
                        name="nombre_dispositivo"
                        value={formData.nombre_dispositivo}
                        onChange={handleChange}
                        placeholder="EJ: SENSOR HUMEDAD NORTE"
                      />

                      <SelectField
                        label="Tipo *"
                        name="tipo_dispositivo"
                        value={formData.tipo_dispositivo}
                        onChange={handleChange}
                        options={TIPOS}
                      />

                      <SelectField
                        label="Estado *"
                        name="estado"
                        value={formData.estado}
                        onChange={handleChange}
                        options={ESTADOS}
                      />
                    </div>
                  )}

                  {step === 2 && (
                    <div className="bg-white p-4 sm:p-6 rounded-md border border-slate-200 shadow-sm">
                      <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">
                        Parcela o lote *
                      </label>

                      {terrenos.length > 0 ? (
                        <select
                          required
                          name="nro_lote"
                          value={formData.nro_lote}
                          onChange={handleChange}
                          className="w-full px-4 py-2.5 border border-slate-200 rounded text-xs font-black uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white cursor-pointer"
                        >
                          <option value="" disabled>SELECCIONE UNA PARCELA...</option>
                          {terrenos.map((t) => (
                            <option key={t.nro_lote} value={t.nro_lote}>
                              LOTE {t.nro_lote} - {t.nombre_sector}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <input
                          type="number"
                          required
                          min="1"
                          name="nro_lote"
                          value={formData.nro_lote}
                          onChange={handleChange}
                          placeholder="INGRESE EL NRO_LOTE"
                          className="w-full px-4 py-2.5 border border-slate-200 rounded text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]"
                        />
                      )}

                      <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
                        <MiniInfo title="Parcela" value={selectedTerreno?.nombre_sector || 'Sin seleccionar'} />
                        <MiniInfo title="Lote" value={formData.nro_lote ? `Nro. ${formData.nro_lote}` : 'Pendiente'} />
                        <MiniInfo title="Uso" value="Telemetría" />
                      </div>

                      <div className="mt-4 p-4 rounded-md bg-emerald-50 border border-emerald-100">
                        <p className="text-[10px] font-black text-emerald-700 uppercase tracking-widest">
                          El dispositivo quedará asociado a esta parcela para futuras lecturas de humedad y temperatura.
                        </p>
                      </div>
                    </div>
                  )}

                  {step === 3 && (
                    <div className="bg-white p-4 sm:p-6 rounded-md border border-slate-200 shadow-sm">
                      <h4 className="text-sm font-black text-slate-800 uppercase mb-4">
                        Confirmar vinculación
                      </h4>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-bold text-slate-600 uppercase">
                        <p>Código: {formData.codigo_dispositivo}</p>
                        <p>Nombre: {formData.nombre_dispositivo}</p>
                        <p>Tipo: {formData.tipo_dispositivo}</p>
                        <p>Estado: {formData.estado}</p>
                        <p>Lote: {formData.nro_lote}</p>
                        <p>Parcela: {selectedTerreno?.nombre_sector || 'Manual'}</p>
                      </div>

                      <div className="mt-5 p-4 bg-blue-50 border border-blue-100 rounded-md flex items-center gap-3">
                        <span className={`w-3 h-3 rounded-full ${linking ? 'bg-blue-600 animate-ping' : 'bg-blue-600'}`}></span>
                        <span className="text-[10px] font-black text-blue-700 uppercase tracking-widest">
                          {linking ? 'Vinculando dispositivo con parcela...' : 'Listo para confirmar la conexión IoT.'}
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="bg-slate-900 rounded-lg p-5 text-white border border-slate-700 shadow-lg">
                  <div className="flex justify-between items-start mb-5">
                    <div>
                      <p className="text-[9px] font-black text-emerald-300 uppercase tracking-widest">
                        Vista previa IoT
                      </p>
                      <h4 className="text-sm font-black uppercase mt-1">
                        {formData.nombre_dispositivo || 'Nuevo sensor'}
                      </h4>
                    </div>

                    <div className="relative">
                      <span className={`absolute inset-0 rounded-full ${getEstadoPulse(formData.estado)} animate-ping opacity-40`}></span>
                      <span className={`relative block w-3 h-3 rounded-full ${getEstadoPulse(formData.estado)}`}></span>
                    </div>
                  </div>

                  <div className="h-28 rounded-md bg-slate-800 border border-slate-700 flex items-center justify-center mb-5">
                    <WifiIcon className="w-16 h-16 text-emerald-400" />
                  </div>

                  <div className="space-y-3 text-[10px] font-black uppercase tracking-widest">
                    <PreviewRow label="Código" value={formData.codigo_dispositivo || 'IOT-000'} />
                    <PreviewRow label="Tipo" value={formData.tipo_dispositivo} />
                    <PreviewRow label="Estado" value={formData.estado} />
                    <PreviewRow label="Parcela" value={formData.nro_lote ? `LOTE ${formData.nro_lote}` : 'SIN ASIGNAR'} />
                  </div>
                </div>
              </div>

              <div className="mt-6 sm:mt-8 flex flex-col-reverse sm:flex-row justify-between gap-3 pt-4 sm:pt-6 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => step === 1 ? setShowModal(false) : setStep(step - 1)}
                  disabled={linking}
                  className="w-full sm:w-auto px-6 py-3 text-[10px] font-black text-slate-500 uppercase tracking-widest hover:bg-slate-200 rounded-md transition-colors disabled:opacity-60"
                >
                  {step === 1 ? 'CANCELAR' : 'VOLVER'}
                </button>

                {step < 3 ? (
                  <button
                    type="button"
                    onClick={nextStep}
                    className="w-full sm:w-auto px-10 py-3 bg-[#1A5729] text-white text-[10px] font-black uppercase tracking-widest rounded-md shadow-lg hover:bg-[#144320] transition-all"
                  >
                    CONTINUAR
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={linking}
                    className="w-full sm:w-auto px-10 py-3 bg-[#1A5729] text-white text-[10px] font-black uppercase tracking-widest rounded-md shadow-lg hover:bg-[#144320] transition-all disabled:opacity-60"
                  >
                    {linking ? 'VINCULANDO...' : 'CONFIRMAR VINCULACIÓN'}
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function KpiCard({ title, value, color, icon }) {
  const colorMap = {
    slate: 'bg-slate-100 text-slate-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    amber: 'bg-amber-50 text-amber-600',
    blue: 'bg-blue-50 text-blue-600',
  };

  const textMap = {
    slate: 'text-slate-800',
    emerald: 'text-emerald-700',
    amber: 'text-amber-700',
    blue: 'text-blue-700',
  };

  return (
    <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
      <div className={`${colorMap[color]} p-2 md:p-3 rounded-md`}>
        {icon === 'wifi' && <WifiIcon className="w-5 h-5 md:w-6 md:h-6" />}
        {icon === 'check' && <CheckIcon className="w-5 h-5 md:w-6 md:h-6" />}
        {icon === 'tool' && <ToolIcon className="w-5 h-5 md:w-6 md:h-6" />}
        {icon === 'map' && <MapIcon className="w-5 h-5 md:w-6 md:h-6" />}
      </div>
      <div>
        <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">{title}</p>
        <p className={`text-lg md:text-xl font-black ${textMap[color]}`}>{value}</p>
      </div>
    </div>
  );
}

function InputField({ label, name, value, onChange, placeholder }) {
  return (
    <div>
      <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">
        {label}
      </label>
      <input
        type="text"
        required
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="w-full px-4 py-2.5 border border-slate-200 rounded text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-slate-50/50"
      />
    </div>
  );
}

function SelectField({ label, name, value, onChange, options }) {
  return (
    <div>
      <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">
        {label}
      </label>
      <select
        required
        name={name}
        value={value}
        onChange={onChange}
        className="w-full px-4 py-2.5 border border-slate-200 rounded text-xs font-black uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white cursor-pointer"
      >
        {options.map((item) => (
          <option key={item} value={item}>{item}</option>
        ))}
      </select>
    </div>
  );
}

function MiniInfo({ title, value }) {
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-md p-3">
      <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{title}</p>
      <p className="text-xs font-black text-slate-700 uppercase mt-1">{value}</p>
    </div>
  );
}

function PreviewRow({ label, value }) {
  return (
    <div className="flex justify-between gap-3">
      <span className="text-slate-400">{label}</span>
      <span className="text-right">{value}</span>
    </div>
  );
}

function WifiIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01M4.93 12.929a10 10 0 0114.14 0M1.394 9.393a15 15 0 0121.213 0" />
    </svg>
  );
}

function CheckIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  );
}

function ToolIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M11.42 15.17L17.25 21A2.652 2.652 0 0021 17.25l-5.83-5.83M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 11-3.586-3.586l5.653-4.655" />
    </svg>
  );
}

function MapIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
    </svg>
  );
}