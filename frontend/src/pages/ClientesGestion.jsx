import { useEffect, useMemo, useState } from 'react';
import { useAuthStore } from '../store/auth_store';
import ExcelJS from 'exceljs';
import { io } from 'socket.io-client'; // <-- Importamos el socket

const API_URL =
  import.meta.env.VITE_API_URL ??
  (import.meta.env.DEV ? 'http://127.0.0.1:5000/api' : '');
// Extraemos la URL base (sin el /api) para conectar el socket correctamente
const SOCKET_URL = API_URL.replace(/\/api\/?$/, '');

const CATEGORIAS_CLIENTE = [
  'TODOS',
  'VIP',
  'FRECUENTE',
  'REGULAR',
  'NUEVO',
  'INACTIVO',
];

const CANALES = ['CORREO', 'WHATSAPP', 'SMS'];

const PLANTILLAS = {
  VIP: {
    asunto: 'Beneficio especial para clientes preferenciales',
    mensaje:
      'Estimado/a {cliente}, gracias por confiar en AgroEnlace. Tenemos una atención preferencial y beneficios comerciales disponibles para usted.',
  },
  FRECUENTE: {
    asunto: 'Nuevas oportunidades para su próxima compra',
    mensaje:
      'Estimado/a {cliente}, vimos que realiza operaciones frecuentes con AgroEnlace. Tenemos productos y servicios que pueden ayudarle en su próxima campaña.',
  },
  REGULAR: {
    asunto: 'Seguimiento comercial AgroEnlace',
    mensaje:
      'Estimado/a {cliente}, queremos acompañarle en sus próximas actividades agrícolas. Puede contactarnos para conocer nuestras opciones disponibles.',
  },
  NUEVO: {
    asunto: 'Bienvenido/a a AgroEnlace',
    mensaje:
      'Estimado/a {cliente}, bienvenido/a a AgroEnlace. Estamos listos para acompañarle con insumos, maquinaria y servicios agrícolas.',
  },
  INACTIVO: {
    asunto: 'Queremos volver a acompañarle',
    mensaje:
      'Estimado/a {cliente}, hace un tiempo no registra operaciones con AgroEnlace. Tenemos nuevas opciones que podrían interesarle.',
  },
};

const formatMoney = (value) =>
  `Bs. ${Number(value || 0).toLocaleString('es-BO', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;

const formatDate = (value) => {
  if (!value) return '—';
  return new Date(value).toLocaleDateString('es-BO', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  });
};

const daysBetweenToday = (value) => {
  if (!value) return null;
  const today = new Date();
  const date = new Date(value);
  const diff = today.getTime() - date.getTime();
  return Math.floor(diff / (1000 * 60 * 60 * 24));
};

const getCategoriaColor = (categoria) => {
  switch (categoria) {
    case 'VIP':
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    case 'FRECUENTE':
      return 'bg-blue-50 text-blue-700 border-blue-200';
    case 'NUEVO':
      return 'bg-lime-50 text-lime-700 border-lime-200';
    case 'INACTIVO':
      return 'bg-amber-50 text-amber-700 border-amber-200';
    default:
      return 'bg-slate-50 text-slate-700 border-slate-200';
  }
};

const getCategoriaCliente = (cliente) => {
  if (cliente.categoria_cliente) return cliente.categoria_cliente;

  const totalTransacciones = Number(cliente.total_transacciones || 0);
  const montoTotal = Number(cliente.monto_total || 0);
  const diasUltimaCompra = daysBetweenToday(cliente.ultima_transaccion);
  const diasRegistro = daysBetweenToday(cliente.created_at);

  if (diasUltimaCompra !== null && diasUltimaCompra > 90) return 'INACTIVO';
  if (diasUltimaCompra === null && diasRegistro !== null && diasRegistro > 45) return 'INACTIVO';
  if (montoTotal >= 10000 || totalTransacciones >= 8) return 'VIP';
  if (totalTransacciones >= 4) return 'FRECUENTE';
  if (totalTransacciones <= 1 && diasRegistro !== null && diasRegistro <= 45) return 'NUEVO';

  return 'REGULAR';
};

const buildMessage = (template, cliente) =>
  template.replaceAll('{cliente}', cliente?.nombre_razon_social || 'cliente');

export default function AgroCRM() {
  const token = useAuthStore((state) => state.token);

  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoriaFiltro, setCategoriaFiltro] = useState('TODOS');
  const [selectedIds, setSelectedIds] = useState([]);

  const [showNotifyModal, setShowNotifyModal] = useState(false);
  const [notifyTarget, setNotifyTarget] = useState(null);
  const [sending, setSending] = useState(false);

  const initialNotifyForm = {
    canal: 'CORREO',
    asunto: '',
    mensaje: '',
  };

  const [notifyForm, setNotifyForm] = useState(initialNotifyForm);

  // ==========================================
  // CONEXIÓN SOCKET EN TIEMPO REAL
  // ==========================================
  useEffect(() => {
    if (!token) return;

    const socket = io(SOCKET_URL, {
      query: { token },
      transports: ['websocket', 'polling']
    });

    socket.on('nueva_notificacion', (data) => {
      console.log('Mensaje Socket recibido:', data);
      alert(`🔔 NUEVA NOTIFICACIÓN CRM\n\nCanal: ${data.canal}\nAsunto: ${data.asunto}\nMensaje: ${data.mensaje}`);
    });

    return () => {
      socket.disconnect();
    };
  }, [token]);

  // ==========================================
  // PETICIÓN HTTP SEGURA
  // ==========================================
  const fetchClientes = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/crm/clientes`, {
        method: 'GET',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
      });

      // MANEJO EXPLÍCITO DEL ERROR 401
      if (response.status === 401) {
        alert("Tu sesión ha expirado o es inválida. Por favor, cierra sesión y vuelve a ingresar.");
        setLoading(false);
        return;
      }

      const result = await response.json();

      if (result.success) {
        const data = result.data || result.clientes || [];
        const normalized = data.map((cliente) => ({
          ...cliente,
          categoria_cliente: getCategoriaCliente(cliente),
        }));
        setClientes(normalized);
      } else {
        alert(result.message || 'No se pudieron cargar los clientes.');
      }
    } catch (error) {
      console.error('Error al cargar clientes CRM:', error);
      alert('Error de comunicación con el servidor.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) fetchClientes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const clientesFiltrados = useMemo(() => {
    const search = searchTerm.trim().toLowerCase();

    return clientes.filter((cliente) => {
      const categoria = getCategoriaCliente(cliente);
      const matchesCategoria =
        categoriaFiltro === 'TODOS' || categoria === categoriaFiltro;

      const matchesSearch =
        !search ||
        cliente.nombre_razon_social?.toLowerCase().includes(search) ||
        cliente.correo?.toLowerCase().includes(search) ||
        cliente.telefono?.toLowerCase().includes(search) ||
        cliente.documento_identidad?.toLowerCase().includes(search);

      return matchesCategoria && matchesSearch;
    });
  }, [clientes, searchTerm, categoriaFiltro]);

  const stats = useMemo(() => {
    const totalClientes = clientes.length;
    const totalMonto = clientes.reduce(
      (sum, cliente) => sum + Number(cliente.monto_total || 0),
      0
    );

    return {
      totalClientes,
      vip: clientes.filter((c) => getCategoriaCliente(c) === 'VIP').length,
      inactivos: clientes.filter((c) => getCategoriaCliente(c) === 'INACTIVO').length,
      montoTotal: totalMonto,
    };
  }, [clientes]);

  const selectedClientes = useMemo(
    () => clientes.filter((cliente) => selectedIds.includes(cliente.id_usuario)),
    [clientes, selectedIds]
  );

  const toggleSelect = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    const visibleIds = clientesFiltrados.map((cliente) => cliente.id_usuario);
    const allVisibleSelected = visibleIds.every((id) => selectedIds.includes(id));

    if (allVisibleSelected) {
      setSelectedIds((prev) => prev.filter((id) => !visibleIds.includes(id)));
    } else {
      setSelectedIds((prev) => [...new Set([...prev, ...visibleIds])]);
    }
  };

  const openNotifyModal = (cliente = null) => {
    const targetCategoria = cliente
      ? getCategoriaCliente(cliente)
      : selectedClientes.length > 0
        ? getCategoriaCliente(selectedClientes[0])
        : 'REGULAR';

    const plantilla = PLANTILLAS[targetCategoria] || PLANTILLAS.REGULAR;

    setNotifyTarget(cliente);
    setNotifyForm({
      canal: 'CORREO',
      asunto: plantilla.asunto,
      mensaje: cliente ? buildMessage(plantilla.mensaje, cliente) : plantilla.mensaje,
    });
    setShowNotifyModal(true);
  };

  const handleNotifyChange = (e) => {
    setNotifyForm({ ...notifyForm, [e.target.name]: e.target.value });
  };

  const handleSendNotification = async (e) => {
    e.preventDefault();

    const destinatarios = notifyTarget
      ? [notifyTarget.id_usuario]
      : selectedClientes.map((cliente) => cliente.id_usuario);

    if (destinatarios.length === 0) {
      alert('Debe seleccionar al menos un cliente.');
      return;
    }

    const payload = {
      canal: notifyForm.canal,
      asunto: notifyForm.asunto.trim(),
      mensaje: notifyForm.mensaje.trim(),
      clientes: destinatarios,
    };

    if (!payload.mensaje) {
      alert('El mensaje de la notificación es obligatorio.');
      return;
    }

    setSending(true);

    try {
      const response = await fetch(`${API_URL}/crm/notificaciones/enviar`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (response.status === 401) {
        alert("Tu sesión ha expirado. Por favor, vuelve a iniciar sesión.");
        setSending(false);
        return;
      }

      const result = await response.json();

      if (result.success) {
        alert(result.message || 'Notificación enviada correctamente al servidor.');
        setShowNotifyModal(false);
        setNotifyTarget(null);
        setNotifyForm(initialNotifyForm);
        setSelectedIds([]);
      } else {
        alert(result.message || 'No se pudo enviar la notificación.');
      }
    } catch (error) {
      console.error('Error al enviar notificación:', error);
      alert('Error de comunicación con el servidor.');
    } finally {
      setSending(false);
    }
  };

  const buildExportRows = () =>
    clientesFiltrados.map((cliente) => ({
      ID: `CLI-${String(cliente.id_usuario).padStart(4, '0')}`,
      Cliente: cliente.nombre_razon_social,
      Documento: cliente.documento_identidad,
      Correo: cliente.correo,
      Telefono: cliente.telefono,
      Categoria: getCategoriaCliente(cliente),
      Estado: cliente.estado_cuenta,
      Transacciones: Number(cliente.total_transacciones || 0),
      'Monto Total': Number(cliente.monto_total || 0),
      'Ultima Transaccion': cliente.ultima_transaccion
        ? formatDate(cliente.ultima_transaccion)
        : '',
    }));

  const exportCSV = () => {
    const rows = buildExportRows();
    const headers = Object.keys(rows[0] || {});

    if (headers.length === 0) return;

    const csv = [
      headers.join(','),
      ...rows.map((row) =>
        headers
          .map((header) => `"${String(row[header] ?? '').replace(/"/g, '""')}"`)
          .join(',')
      ),
    ].join('\n');

    const blob = new Blob(['\ufeff' + csv], {
      type: 'text/csv;charset=utf-8;',
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `crm_clientes_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportXLSX = async () => {
    const wb = new ExcelJS.Workbook();
    wb.creator = 'AgroEnlace';
    wb.created = new Date();

    const ws = wb.addWorksheet('CRM Clientes', {
      views: [{ state: 'frozen', ySplit: 4 }],
    });

    ws.columns = [
      { width: 12 },
      { width: 35 },
      { width: 18 },
      { width: 30 },
      { width: 16 },
      { width: 16 },
      { width: 14 },
      { width: 16 },
      { width: 18 },
      { width: 18 },
    ];

    const COLOR_VERDE = '1A5729';
    const COLOR_HEADER = 'F1F5F9';

    const thinBorder = {
      top: { style: 'thin', color: { argb: 'FFE2E8F0' } },
      bottom: { style: 'thin', color: { argb: 'FFE2E8F0' } },
      left: { style: 'thin', color: { argb: 'FFE2E8F0' } },
      right: { style: 'thin', color: { argb: 'FFE2E8F0' } },
    };

    ws.addRow(['AGROENLACE — CRM DE CLIENTES', '', '', '', '', '', '', '', '', '']);
    ws.mergeCells('A1:J1');
    ws.getRow(1).height = 30;
    ws.getCell('A1').style = {
      font: { bold: true, size: 15, color: { argb: 'FFFFFFFF' } },
      fill: { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + COLOR_VERDE } },
      alignment: { horizontal: 'center', vertical: 'middle' },
    };

    const ahora = new Date();
    ws.addRow([
      `Reporte generado el ${ahora.toLocaleDateString('es-BO')} a ${ahora.toLocaleTimeString('es-BO', {
        hour: '2-digit',
        minute: '2-digit',
      })}`,
      '', '', '', '', '', '', '', '', '',
    ]);
    ws.mergeCells('A2:J2');
    ws.getCell('A2').style = {
      font: { italic: true, size: 9, color: { argb: 'FF64748B' } },
      alignment: { horizontal: 'center', vertical: 'middle' },
    };

    ws.addRow([]);

    const headerRow = ws.addRow([
      'ID', 'CLIENTE', 'DOCUMENTO', 'CORREO', 'TELÉFONO',
      'CATEGORÍA', 'ESTADO', 'TRANSACCIONES', 'MONTO TOTAL', 'ÚLTIMA TRANSACCIÓN',
    ]);

    headerRow.eachCell((cell) => {
      cell.style = {
        font: { bold: true, size: 9, color: { argb: 'FF' + COLOR_VERDE } },
        fill: { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + COLOR_HEADER } },
        alignment: { horizontal: 'center', vertical: 'middle', wrapText: true },
        border: thinBorder,
      };
    });

    clientesFiltrados.forEach((cliente, index) => {
      const row = ws.addRow([
        `CLI-${String(cliente.id_usuario).padStart(4, '0')}`,
        cliente.nombre_razon_social,
        cliente.documento_identidad,
        cliente.correo,
        cliente.telefono,
        getCategoriaCliente(cliente),
        cliente.estado_cuenta,
        Number(cliente.total_transacciones || 0),
        Number(cliente.monto_total || 0),
        cliente.ultima_transaccion ? formatDate(cliente.ultima_transaccion) : '—',
      ]);

      row.eachCell((cell, colIdx) => {
        cell.border = thinBorder;
        cell.fill = {
          type: 'pattern',
          pattern: 'solid',
          fgColor: { argb: index % 2 === 0 ? 'FFF8FAFC' : 'FFFFFFFF' },
        };
        cell.font = { size: 9, color: { argb: 'FF1E293B' }, bold: colIdx === 1 };
        cell.alignment = {
          horizontal: colIdx >= 6 ? 'center' : 'left',
          vertical: 'middle',
        };
        if (colIdx === 9) cell.numFmt = '"Bs." #,##0.00';
      });
    });

    const buffer = await wb.xlsx.writeBuffer();
    const blob = new Blob([buffer], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `crm_clientes_${new Date().toISOString().slice(0, 10)}.xlsx`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const allVisibleSelected =
    clientesFiltrados.length > 0 &&
    clientesFiltrados.every((cliente) => selectedIds.includes(cliente.id_usuario));

  return (
    <div className="p-4 md:p-8 animate-in fade-in duration-500 bg-slate-50 min-h-screen max-w-[100vw] overflow-x-hidden">
      <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center mb-6 md:mb-8 gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-black text-slate-800 tracking-tight flex items-center gap-3">
            <div className="w-2 h-6 md:h-8 bg-[#1A5729]"></div>
            CRM DE CLIENTES
          </h1>
          <p className="text-[9px] md:text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mt-1 ml-5">
            Clasificación comercial y envío de notificaciones
          </p>
        </div>

        <div className="flex flex-col lg:flex-row w-full xl:w-auto gap-3">
          <div className="relative flex-1 lg:w-72">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              placeholder="BUSCAR CLIENTE, CORREO, TELÉFONO..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 border border-slate-200 rounded-md text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white shadow-sm"
            />
          </div>

          <select
            value={categoriaFiltro}
            onChange={(e) => setCategoriaFiltro(e.target.value)}
            className="px-4 py-2.5 border border-slate-200 rounded-md text-xs font-black uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white shadow-sm"
          >
            {CATEGORIAS_CLIENTE.map((categoria) => (
              <option key={categoria} value={categoria}>
                {categoria}
              </option>
            ))}
          </select>

          <div className="flex gap-2">
            <button
              onClick={exportCSV}
              disabled={clientesFiltrados.length === 0}
              className="px-3 py-2.5 border border-slate-300 rounded-md text-[10px] font-black uppercase tracking-widest text-slate-600 bg-white hover:bg-slate-50 transition-all disabled:opacity-40"
            >
              CSV
            </button>
            <button
              onClick={exportXLSX}
              disabled={clientesFiltrados.length === 0}
              className="px-3 py-2.5 border border-slate-300 rounded-md text-[10px] font-black uppercase tracking-widest text-slate-600 bg-white hover:bg-slate-50 transition-all disabled:opacity-40"
            >
              XLSX
            </button>
          </div>

          <button
            onClick={() => openNotifyModal(null)}
            disabled={selectedIds.length === 0}
            className="bg-[#1A5729] hover:bg-[#144320] text-white px-6 py-2.5 rounded-md font-black text-[10px] uppercase tracking-widest transition-all active:scale-95 shadow-md flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8m-18 8h18a2 2 0 002-2V8a2 2 0 00-2-2H3a2 2 0 00-2 2v6a2 2 0 002 2z" />
            </svg>
            NOTIFICAR SELECCIÓN
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-6 md:mb-8">
        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-slate-100 p-2 md:p-3 rounded-md text-slate-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a4 4 0 00-4-4h-1M9 20H4v-2a4 4 0 014-4h1m0-4a4 4 0 100-8 4 4 0 000 8zm8 0a4 4 0 100-8 4 4 0 000 8z" />
            </svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Total Clientes</p>
            <p className="text-lg md:text-xl font-black text-slate-800">{stats.totalClientes}</p>
          </div>
        </div>

        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-emerald-50 p-2 md:p-3 rounded-md text-emerald-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 3l14 9-14 9V3z" />
            </svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Clientes VIP</p>
            <p className="text-lg md:text-xl font-black text-emerald-700">{stats.vip}</p>
          </div>
        </div>

        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-amber-50 p-2 md:p-3 rounded-md text-amber-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Inactivos</p>
            <p className="text-lg md:text-xl font-black text-amber-700">{stats.inactivos}</p>
          </div>
        </div>

        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-blue-50 p-2 md:p-3 rounded-md text-blue-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8V7m0 9v1m9-5a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Valor Comercial</p>
            <p className="text-lg md:text-xl font-black text-blue-700">{formatMoney(stats.montoTotal)}</p>
          </div>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden w-full">
        <div className="overflow-x-auto w-full custom-scrollbar">
          <table className="w-full min-w-[1100px] text-left border-collapse">
            <thead>
              <tr className="bg-slate-100 border-b border-slate-200 text-[10px] font-black text-slate-500 uppercase tracking-widest">
                <th className="px-4 py-4 text-center">
                  <input
                    type="checkbox"
                    checked={allVisibleSelected}
                    onChange={toggleSelectAll}
                    className="accent-[#1A5729]"
                  />
                </th>
                <th className="px-6 py-4">Cliente</th>
                <th className="px-6 py-4">Contacto</th>
                <th className="px-6 py-4">Categoría</th>
                <th className="px-6 py-4">Actividad comercial</th>
                <th className="px-6 py-4">Estado</th>
                <th className="px-6 py-4 text-center">Gestión</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan="7" className="text-center py-20 text-slate-400 font-bold uppercase text-[10px] tracking-widest">
                    Sincronizando clientes del CRM...
                  </td>
                </tr>
              ) : clientesFiltrados.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-20 text-slate-400 font-bold uppercase text-[10px] tracking-widest">
                    No hay clientes que coincidan con la búsqueda
                  </td>
                </tr>
              ) : (
                clientesFiltrados.map((cliente) => {
                  const categoria = getCategoriaCliente(cliente);
                  const diasUltimaCompra = daysBetweenToday(cliente.ultima_transaccion);

                  return (
                    <tr key={cliente.id_usuario} className="hover:bg-slate-50 transition-colors group">
                      <td className="px-4 py-4 text-center">
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(cliente.id_usuario)}
                          onChange={() => toggleSelect(cliente.id_usuario)}
                          className="accent-[#1A5729]"
                        />
                      </td>

                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="bg-slate-100 p-2 rounded-md text-slate-500 shrink-0">
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M5.121 17.804A8.962 8.962 0 0112 15c2.21 0 4.236.8 5.879 2.129M15 11a3 3 0 10-6 0 3 3 0 006 0z" />
                            </svg>
                          </div>
                          <div className="min-w-0">
                            <div className="font-black text-slate-800 text-xs uppercase truncate">
                              {cliente.nombre_razon_social}
                            </div>
                            <div className="text-[10px] font-bold text-slate-400 uppercase">
                              CLI-{String(cliente.id_usuario).padStart(4, '0')} · CI/NIT: {cliente.documento_identidad || '—'}
                            </div>
                          </div>
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <div className="text-xs font-bold text-slate-700">{cliente.correo || '—'}</div>
                        <div className="text-[10px] font-bold text-slate-400 uppercase">{cliente.telefono || 'Sin teléfono'}</div>
                      </td>

                      <td className="px-6 py-4">
                        <span className={`inline-flex border px-2.5 py-1 rounded-full text-[9px] font-black uppercase tracking-widest ${getCategoriaColor(categoria)}`}>
                          {categoria}
                        </span>
                      </td>

                      <td className="px-6 py-4">
                        <div className="text-xs font-black text-slate-800">
                          {Number(cliente.total_transacciones || 0)} transacciones
                        </div>
                        <div className="text-[10px] font-bold text-slate-500">
                          {formatMoney(cliente.monto_total)}
                        </div>
                        <div className="text-[10px] font-bold text-slate-400 uppercase">
                          Última: {formatDate(cliente.ultima_transaccion)}
                          {diasUltimaCompra !== null ? ` · hace ${diasUltimaCompra} días` : ''}
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <span className={`inline-flex px-2.5 py-1 rounded-full text-[9px] font-black uppercase tracking-widest ${
                          cliente.estado_cuenta === 'ACTIVO'
                            ? 'bg-emerald-50 text-emerald-700'
                            : 'bg-red-50 text-red-700'
                        }`}>
                          {cliente.estado_cuenta || 'SIN ESTADO'}
                        </span>
                      </td>

                      <td className="px-6 py-4 text-center">
                        <button
                          onClick={() => openNotifyModal(cliente)}
                          className="text-[#1A5729] hover:text-[#144320] font-black text-[10px] uppercase tracking-widest flex flex-col items-center gap-1 mx-auto"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8m-18 8h18a2 2 0 002-2V8a2 2 0 00-2-2H3a2 2 0 00-2 2v6a2 2 0 002 2z" />
                          </svg>
                          Notificar
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showNotifyModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-2 sm:p-4 bg-slate-900/70 backdrop-blur-sm">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-3xl flex flex-col max-h-[95vh] border border-slate-300 animate-in zoom-in-95 duration-200">
            <div className="bg-[#1A5729] px-4 sm:px-8 py-4 sm:py-5 flex justify-between items-center text-white shrink-0">
              <div>
                <h3 className="text-sm sm:text-base font-black uppercase tracking-widest">
                  ENVIAR NOTIFICACIÓN
                </h3>
                <p className="text-[9px] sm:text-[10px] text-emerald-100 font-bold uppercase mt-0.5 tracking-wider">
                  {notifyTarget
                    ? `Destinatario: ${notifyTarget.nombre_razon_social}`
                    : `Destinatarios seleccionados: ${selectedClientes.length}`}
                </p>
              </div>

              <button
                onClick={() => setShowNotifyModal(false)}
                className="text-emerald-100 hover:text-white hover:bg-white/10 p-2 rounded-md transition-colors shrink-0"
              >
                <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleSendNotification} className="p-4 sm:p-8 bg-slate-50 overflow-y-auto custom-scrollbar">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 bg-white p-4 sm:p-6 rounded-md border border-slate-200 shadow-sm">
                <div>
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">
                    Canal de envío *
                  </label>
                  <select
                    required
                    name="canal"
                    value={notifyForm.canal}
                    onChange={handleNotifyChange}
                    className="w-full px-4 py-2.5 border border-slate-200 rounded text-xs font-black uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white"
                  >
                    {CANALES.map((canal) => (
                      <option key={canal} value={canal}>
                        {canal}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">
                    Asunto
                  </label>
                  <input
                    type="text"
                    name="asunto"
                    value={notifyForm.asunto}
                    onChange={handleNotifyChange}
                    placeholder="ASUNTO DE LA NOTIFICACIÓN"
                    className="w-full px-4 py-2.5 border border-slate-200 rounded text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-slate-50/50"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">
                    Mensaje *
                  </label>
                  <textarea
                    required
                    rows={7}
                    name="mensaje"
                    value={notifyForm.mensaje}
                    onChange={handleNotifyChange}
                    placeholder="ESCRIBA EL MENSAJE PARA EL CLIENTE..."
                    className="w-full px-4 py-3 border border-slate-200 rounded text-xs font-bold outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-slate-50/50 resize-none"
                  />
                  <p className="mt-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Puede usar {'{cliente}'} como variable cuando el envío sea masivo.
                  </p>
                </div>
              </div>

              {!notifyTarget && selectedClientes.length > 0 && (
                <div className="mt-4 bg-white p-4 rounded-md border border-slate-200">
                  <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">
                    Clientes seleccionados
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {selectedClientes.slice(0, 8).map((cliente) => (
                      <span
                        key={cliente.id_usuario}
                        className="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 text-[9px] font-black uppercase tracking-widest"
                      >
                        {cliente.nombre_razon_social}
                      </span>
                    ))}
                    {selectedClientes.length > 8 && (
                      <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 text-[9px] font-black uppercase tracking-widest">
                        +{selectedClientes.length - 8} más
                      </span>
                    )}
                  </div>
                </div>
              )}

              <div className="mt-6 sm:mt-8 flex flex-col-reverse sm:flex-row justify-end gap-3 pt-4 sm:pt-6 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowNotifyModal(false)}
                  className="w-full sm:w-auto px-6 py-3 sm:py-2.5 text-[10px] font-black text-slate-500 uppercase tracking-widest hover:bg-slate-200 rounded-md transition-colors"
                >
                  CANCELAR
                </button>

                <button
                  type="submit"
                  disabled={sending}
                  className="w-full sm:w-auto px-8 py-3 sm:py-2.5 bg-[#1A5729] text-white text-[10px] font-black uppercase tracking-widest rounded-md shadow-lg hover:bg-[#144320] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {sending ? 'ENVIANDO...' : 'ENVIAR NOTIFICACIÓN'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}