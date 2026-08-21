import { useState, useEffect } from 'react';
import { useAuthStore } from '../store/auth_store';
import ExcelJS from 'exceljs';

const API_URL = import.meta.env.VITE_API_URL;

const CATEGORIAS = [
  'SEMILLA', 'FERTILIZANTE', 'PLAGUICIDA', 'HERBICIDA',
  'FUNGICIDA', 'COMBUSTIBLE', 'HERRAMIENTA', 'EQUIPO', 'INSUMO GENERAL'
];

const UNIDADES = [
  'KG', 'LITRO', 'TONELADA', 'SACO (50KG)', 'SACO (25KG)', 
  'UNIDAD', 'CAJA', 'GALÓN', 'GRAMO', 'MILILITRO'
];

export default function AgroBodega() {
  const token = useAuthStore((state) => state.token);

  const [productos, setProductos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [currentId, setCurrentId] = useState(null);

  const initialForm = {
    nombre_producto: '',
    categoria: '', 
    unidad_medida: '', 
    precio_unitario: '',
    stock_actual: '0',
    stock_minimo: '0',
  };
  const [formData, setFormData] = useState(initialForm);

  // --- 1. OBTENER (GET) ---
  const fetchProductos = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/bodega`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const result = await response.json();
      if (result.success) {
        setProductos(result.data || result.list_cultivos || []);
      }
    } catch (error) {
      console.error("Error en la carga:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) fetchProductos();
  }, [token]);

  // --- 2. FORMULARIO ---
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const openAddModal = () => {
    setIsEditing(false);
    setFormData(initialForm);
    setShowModal(true);
  };

  const openEditModal = (p) => {
    setIsEditing(true);
    setCurrentId(p.id_producto);
    setFormData({
      nombre_producto: p.nombre_producto,
      categoria: p.categoria,
      unidad_medida: p.unidad_medida || '',
      precio_unitario: p.precio_unitario ?? '',
      stock_actual: p.stock_actual ?? '0',
      stock_minimo: p.stock_minimo ?? '0',
    });
    setShowModal(true);
  };

  // --- 3. GUARDAR (POST/PUT) ---
  const handleSubmit = async (e) => {
    e.preventDefault();
    const payload = {
      ...formData,
      precio_unitario: formData.precio_unitario !== '' ? parseFloat(formData.precio_unitario) : null,
      stock_actual: parseFloat(formData.stock_actual) || 0,
      stock_minimo: parseFloat(formData.stock_minimo) || 0,
    };

    const url = isEditing ? `${API_URL}/bodega/${currentId}` : `${API_URL}/bodega`;
    const method = isEditing ? 'PUT' : 'POST';

    try {
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      const result = await response.json();
      if (result.success) {
        setShowModal(false);
        fetchProductos();
      } else {
        alert(`Atención: ${result.message}`);
      }
    } catch (error) {
      alert("Error de comunicación con el servidor.");
    }
  };

  // --- 4. ELIMINAR (DELETE) ---
  const handleDelete = async (id, nombre) => {
    if (!window.confirm(`¿Está seguro de eliminar el producto "${nombre}"?`)) return;
    try {
      const response = await fetch(`${API_URL}/bodega/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const result = await response.json();
      if (result.success) {
        fetchProductos();
      } else {
        alert(result.message);
      }
    } catch (error) {
      alert("Error al procesar la eliminación.");
    }
  };

  const filtered = productos.filter(p =>
    p.nombre_producto.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.categoria.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const stats = {
    total: productos.length,
    stockBajo: productos.filter(p => parseFloat(p.stock_actual) <= parseFloat(p.stock_minimo)).length,
    categorias: [...new Set(productos.map(p => p.categoria))].length,
    valorTotal: productos.reduce((sum, p) => sum + (parseFloat(p.precio_unitario || 0) * parseFloat(p.stock_actual || 0)), 0),
  };

  const isStockBajo = (p) => parseFloat(p.stock_actual) <= parseFloat(p.stock_minimo);

  const buildExportRows = () => productos.map(p => ({
    'ID':               `ID-${String(p.id_producto).padStart(4, '0')}`,
    'Nombre Producto':  p.nombre_producto,
    'Categoría':        p.categoria,
    'Unidad de Medida': p.unidad_medida || '',
    'Precio Unitario':  p.precio_unitario ?? '',
    'Stock Actual':     p.stock_actual,
    'Stock Mínimo':     p.stock_minimo,
    'Estado Stock':     isStockBajo(p) ? 'STOCK BAJO' : 'OK',
  }));

  const exportCSV = () => {
    const rows = buildExportRows();
    const headers = Object.keys(rows[0] || {});
    const csv = [
      headers.join(','),
      ...rows.map(r => headers.map(h => `"${String(r[h]).replace(/"/g, '""')}"`).join(','))
    ].join('\n');
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bodega_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportXLSX = async () => {
    const wb = new ExcelJS.Workbook();
    wb.creator = 'AgroEnlace';
    wb.created = new Date();

    const ws = wb.addWorksheet('Bodega', { views: [{ state: 'frozen', ySplit: 4 }] });

    // Anchos de columna: ID, Nombre, Categoría, Unidad, Precio, Stock Actual, Stock Mín, Estado
    ws.columns = [
      { width: 10 }, { width: 36 }, { width: 20 }, { width: 18 },
      { width: 18 }, { width: 16 }, { width: 16 }, { width: 16 },
    ];

    const COLOR_VERDE   = '1A5729';
    const COLOR_VERDE2  = '2D7A3A';
    const COLOR_HEADER  = 'F1F5F9';
    const COLOR_FILA_A  = 'F0FDF4';
    const COLOR_BAJO    = 'FEF3C7';
    const COLOR_BAJO_TX = '92400E';

    const styleTitle = {
      font: { bold: true, size: 15, color: { argb: 'FFFFFFFF' } },
      fill: { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + COLOR_VERDE } },
      alignment: { horizontal: 'center', vertical: 'middle' },
    };
    const styleSubtitle = {
      font: { italic: true, size: 9, color: { argb: 'FF64748B' } },
      fill: { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF8FAFC' } },
      alignment: { horizontal: 'center', vertical: 'middle' },
    };
    const styleColHeader = (center = false) => ({
      font: { bold: true, size: 9, color: { argb: 'FF' + COLOR_VERDE } },
      fill: { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + COLOR_HEADER } },
      alignment: { horizontal: center ? 'center' : 'left', vertical: 'middle', wrapText: true },
      border: {
        top:    { style: 'medium', color: { argb: 'FF' + COLOR_VERDE2 } },
        bottom: { style: 'medium', color: { argb: 'FF' + COLOR_VERDE2 } },
        left:   { style: 'thin',   color: { argb: 'FFE2E8F0' } },
        right:  { style: 'thin',   color: { argb: 'FFE2E8F0' } },
      },
    });
    const thinBorder = {
      top:    { style: 'thin', color: { argb: 'FFE2E8F0' } },
      bottom: { style: 'thin', color: { argb: 'FFE2E8F0' } },
      left:   { style: 'thin', color: { argb: 'FFE2E8F0' } },
      right:  { style: 'thin', color: { argb: 'FFE2E8F0' } },
    };

    // --- Fila 1: Título ---
    ws.addRow(['AGROENLACE — CONTROL DE BODEGA', '', '', '', '', '', '', '']);
    ws.mergeCells('A1:H1');
    ws.getRow(1).height = 30;
    ws.getCell('A1').style = styleTitle;

    // --- Fila 2: Subtítulo ---
    const ahora = new Date();
    const fecha = ahora.toLocaleDateString('es-BO', { year: 'numeric', month: 'long', day: 'numeric' });
    const hora  = ahora.toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit' });
    ws.addRow([`Reporte generado el ${fecha} a las ${hora}`, '', '', '', '', '', '', '']);
    ws.mergeCells('A2:H2');
    ws.getRow(2).height = 18;
    ws.getCell('A2').style = styleSubtitle;

    // --- Fila 3: Espacio ---
    ws.addRow([]);
    ws.getRow(3).height = 6;

    // --- Fila 4: Encabezados ---
    const headerRow = ws.addRow([
      'ID', 'NOMBRE PRODUCTO', 'CATEGORÍA', 'UNIDAD DE MEDIDA',
      'PRECIO UNIT. (Bs.)', 'STOCK ACTUAL', 'STOCK MÍNIMO', 'ESTADO',
    ]);
    headerRow.height = 22;
    headerRow.eachCell(cell => {
      const isNum = ['E', 'F', 'G', 'H'].includes(cell.col);
      cell.style = styleColHeader(isNum || cell.col === 'H');
    });

    // --- Filas de datos ---
    productos.forEach((p, i) => {
      const bajo = isStockBajo(p);
      const bgFill = bajo
        ? { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + COLOR_BAJO } }
        : i % 2 === 0
          ? { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + COLOR_FILA_A } }
          : { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFFFFFFF' } };

      const row = ws.addRow([
        `ID-${String(p.id_producto).padStart(4, '0')}`,
        p.nombre_producto,
        p.categoria,
        p.unidad_medida || '—',
        p.precio_unitario != null ? parseFloat(p.precio_unitario) : null,
        parseFloat(p.stock_actual),
        parseFloat(p.stock_minimo),
        bajo ? 'STOCK BAJO' : 'OK',
      ]);
      row.height = 18;

      row.eachCell({ includeEmpty: true }, (cell, colIdx) => {
        const isNumCol = colIdx >= 5 && colIdx <= 7;
        const isEstado = colIdx === 8;
        cell.border = thinBorder;
        cell.fill   = bgFill;
        cell.font   = {
          size: 9,
          bold:  colIdx === 1,
          color: { argb: bajo && isEstado ? 'FF' + COLOR_BAJO_TX : 'FF1E293B' },
        };
        cell.alignment = {
          horizontal: isNumCol || isEstado ? 'center' : 'left',
          vertical: 'middle',
        };
        if (isNumCol && cell.value !== null) {
          cell.numFmt = '#,##0.00';
        }
      });
    });

    // --- Fila de resumen ---
    ws.addRow([]);
    const valorTotal = productos.reduce(
      (s, p) => s + parseFloat(p.precio_unitario || 0) * parseFloat(p.stock_actual || 0), 0
    );
    const resumenData = [
      ['Total de productos',          productos.length],
      ['Productos con stock bajo',     productos.filter(p => isStockBajo(p)).length],
      ['Categorías distintas',         [...new Set(productos.map(p => p.categoria))].length],
      ['Valor total del inventario',   valorTotal],
    ];
    resumenData.forEach(([label, val], idx) => {
      const r = ws.addRow(['', '', '', '', '', label, '', val]);
      r.height = 18;
      const cLabel = r.getCell(6);
      const cVal   = r.getCell(8);
      cLabel.style = {
        font: { bold: true, size: 9, color: { argb: 'FF' + COLOR_VERDE } },
        alignment: { horizontal: 'right', vertical: 'middle' },
      };
      cVal.style = {
        font: { bold: true, size: 9, color: { argb: 'FF1E293B' } },
        alignment: { horizontal: 'center', vertical: 'middle' },
        fill: { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF0FDF4' } },
        border: thinBorder,
      };
      if (idx === 3) cVal.numFmt = '"Bs." #,##0.00';
    });

    // --- Descargar ---
    const buffer = await wb.xlsx.writeBuffer();
    const blob   = new Blob([buffer], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    const url = URL.createObjectURL(blob);
    const a   = document.createElement('a');
    a.href     = url;
    a.download = `bodega_${new Date().toISOString().slice(0, 10)}.xlsx`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-4 md:p-8 animate-in fade-in duration-500 bg-slate-50 min-h-screen max-w-[100vw] overflow-x-hidden">

      {/* SECCIÓN CABECERA */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 md:mb-8 gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-black text-slate-800 tracking-tight flex items-center gap-3">
            <div className="w-2 h-6 md:h-8 bg-[#1A5729]"></div>
            CONTROL DE BODEGA
          </h1>
          <p className="text-[9px] md:text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mt-1 ml-5">
            Gestión de Productos e Insumos Agrícolas
          </p>
        </div>

        <div className="flex flex-col sm:flex-row w-full md:w-auto gap-3">
          <div className="relative flex-1 md:w-64">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text" placeholder="BUSCAR PRODUCTO O CATEGORÍA..."
              value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 border border-slate-200 rounded-md text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white shadow-sm"
            />
          </div>
          {/* Botones de exportación */}
          <div className="flex gap-2">
            <button
              onClick={exportCSV}
              disabled={productos.length === 0}
              title="Descargar CSV"
              className="flex items-center gap-1.5 px-3 py-2.5 border border-slate-300 rounded-md text-[10px] font-black uppercase tracking-widest text-slate-600 bg-white hover:bg-slate-50 hover:border-slate-400 transition-all active:scale-95 shadow-sm disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <svg className="w-4 h-4 text-emerald-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              CSV
            </button>
            <button
              onClick={() => exportXLSX()}
              disabled={productos.length === 0}
              title="Descargar Excel"
              className="flex items-center gap-1.5 px-3 py-2.5 border border-slate-300 rounded-md text-[10px] font-black uppercase tracking-widest text-slate-600 bg-white hover:bg-slate-50 hover:border-slate-400 transition-all active:scale-95 shadow-sm disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <svg className="w-4 h-4 text-blue-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              XLSX
            </button>
          </div>

          <button
            onClick={openAddModal}
            className="bg-[#1A5729] hover:bg-[#144320] text-white px-6 py-2.5 rounded-md font-black text-[10px] uppercase tracking-widest transition-all active:scale-95 shadow-md flex items-center justify-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" /></svg>
            NUEVO PRODUCTO
          </button>
        </div>
      </div>

      {/* DASHBOARD DE KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-6 md:mb-8">
        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-slate-100 p-2 md:p-3 rounded-md text-slate-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Total Productos</p>
            <p className="text-lg md:text-xl font-black text-slate-800">{stats.total}</p>
          </div>
        </div>
        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-amber-50 p-2 md:p-3 rounded-md text-amber-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Stock Bajo</p>
            <p className="text-lg md:text-xl font-black text-amber-700">{stats.stockBajo}</p>
          </div>
        </div>
        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-emerald-50 p-2 md:p-3 rounded-md text-emerald-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Categorías</p>
            <p className="text-lg md:text-xl font-black text-emerald-700">{stats.categorias}</p>
          </div>
        </div>
        <div className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="bg-blue-50 p-2 md:p-3 rounded-md text-blue-600">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </div>
          <div>
            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest">Valor Inventario</p>
            <p className="text-lg md:text-xl font-black text-blue-700">
              Bs. {stats.valorTotal.toLocaleString('es-BO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      </div>

      {/* TABLA */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden w-full">
        <div className="overflow-x-auto w-full custom-scrollbar">
          <table className="w-full min-w-[800px] text-left border-collapse">
            <thead>
              <tr className="bg-slate-100 border-b border-slate-200 text-[10px] font-black text-slate-500 uppercase tracking-widest">
                <th className="px-6 py-4">ID</th>
                <th className="px-6 py-4">Producto / Categoría</th>
                <th className="px-6 py-4">Unidad</th>
                <th className="px-6 py-4">Stock Actual / Mínimo</th>
                <th className="px-6 py-4">Precio Unitario</th>
                <th className="px-6 py-4 text-center">Gestión</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr><td colSpan="6" className="text-center py-20 text-slate-400 font-bold uppercase text-[10px] tracking-widest">Sincronizando con los servidores...</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan="6" className="text-center py-20 text-slate-400 font-bold uppercase text-[10px] tracking-widest">No hay productos que coincidan con la búsqueda</td></tr>
              ) : (
                filtered.map((p) => (
                  <tr key={p.id_producto} className="hover:bg-slate-50 transition-colors group">
                    <td className="px-6 py-4 font-mono text-[10px] font-bold text-slate-400">
                      ID-{String(p.id_producto).padStart(4, '0')}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="bg-slate-100 p-2 rounded-md text-slate-400 shrink-0">
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>
                        </div>
                        <div className="min-w-0">
                          <div className="font-black text-slate-800 text-xs uppercase truncate">{p.nombre_producto}</div>
                          <span className="inline-block mt-0.5 px-2 py-0.5 bg-emerald-50 text-emerald-700 text-[9px] font-black uppercase tracking-widest rounded">
                            {p.categoria}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">
                      {p.unidad_medida || '—'}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2">
                          <span className={`text-sm font-black ${isStockBajo(p) ? 'text-amber-600' : 'text-slate-800'}`}>
                            {parseFloat(p.stock_actual).toLocaleString('es-BO')}
                          </span>
                          {isStockBajo(p) && (
                            <span className="px-2 py-0.5 bg-amber-50 text-amber-700 text-[9px] font-black uppercase tracking-widest rounded flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
                              BAJO
                            </span>
                          )}
                        </div>
                        <div className="text-[10px] font-bold text-slate-400 uppercase">
                          Mín: {parseFloat(p.stock_minimo).toLocaleString('es-BO')}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs font-bold text-slate-700">
                      {p.precio_unitario != null
                        ? `Bs. ${parseFloat(p.precio_unitario).toLocaleString('es-BO', { minimumFractionDigits: 2 })}`
                        : '—'}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex justify-center gap-4">
                        <button onClick={() => openEditModal(p)} className="text-blue-600 hover:text-blue-800 font-black text-[10px] uppercase tracking-widest flex flex-col items-center gap-1">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                          Editar
                        </button>
                        <button onClick={() => handleDelete(p.id_producto, p.nombre_producto)} className="text-red-500 hover:text-red-700 font-black text-[10px] uppercase tracking-widest flex flex-col items-center gap-1">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                          Eliminar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* MODAL */}
      {showModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-2 sm:p-4 bg-slate-900/70 backdrop-blur-sm">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-3xl flex flex-col max-h-[95vh] border border-slate-300 animate-in zoom-in-95 duration-200">

            {/* Cabecera Fija */}
            <div className="bg-[#1A5729] px-4 sm:px-8 py-4 sm:py-5 flex justify-between items-center text-white shrink-0">
              <div className="flex items-center gap-3">
                <div className="bg-white/20 p-2 rounded-md hidden sm:block">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>
                </div>
                <div>
                  <h3 className="text-sm sm:text-base font-black uppercase tracking-widest">
                    {isEditing ? 'EDITAR PRODUCTO' : 'REGISTRAR PRODUCTO'}
                  </h3>
                  <p className="text-[9px] sm:text-[10px] text-emerald-100 font-bold uppercase mt-0.5 tracking-wider">
                    Completa los datos del insumo o producto
                  </p>
                </div>
              </div>
              <button onClick={() => setShowModal(false)} className="text-emerald-100 hover:text-white hover:bg-white/10 p-2 rounded-md transition-colors shrink-0">
                <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>

            {/* Contenido Deslizable */}
            <form onSubmit={handleSubmit} className="p-4 sm:p-8 bg-slate-50 overflow-y-auto custom-scrollbar">

              {/* Sección 1: Identificación */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 bg-white p-4 sm:p-6 rounded-md border border-slate-200 shadow-sm">
                <div className="md:col-span-2">
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2">Nombre del Producto *</label>
                  <input
                    type="text" required name="nombre_producto" value={formData.nombre_producto}
                    onChange={handleChange} placeholder="EJ: HERBICIDA GLIFOSATO 48%"
                    className="w-full px-3 sm:px-4 py-2 sm:py-2.5 border border-slate-200 rounded text-xs font-bold uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-slate-50/50"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2">Categoría *</label>
                  <select
                    required name="categoria" value={formData.categoria} onChange={handleChange}
                    className="w-full px-3 sm:px-4 py-2 sm:py-2.5 border border-slate-200 rounded text-xs font-black uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white cursor-pointer"
                  >
                    <option value="" disabled>SELECCIONE...</option>
                    {CATEGORIAS.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2">Unidad de Medida *</label>
                  <select
                    required name="unidad_medida" value={formData.unidad_medida} onChange={handleChange}
                    className="w-full px-3 sm:px-4 py-2 sm:py-2.5 border border-slate-200 rounded text-xs font-black uppercase outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729] bg-white cursor-pointer"
                  >
                    <option value="" disabled>SELECCIONE...</option>
                    {UNIDADES.map(u => (
                      <option key={u} value={u}>{u}</option>
                    ))}
                  </select>
                </div>

              </div>

              {/* Sección 2: Métricas de Stock y Precio */}
              <div className="mt-4 sm:mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 bg-white p-4 sm:p-6 rounded-md border border-slate-200 shadow-sm">
                <div>
                  <label className="block text-[9px] sm:text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2 flex items-center gap-1.5">
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    Precio Unitario (Bs.)
                  </label>
                  <input
                    type="number" step="0.01" min="0" name="precio_unitario"
                    value={formData.precio_unitario} onChange={handleChange} placeholder="0.00"
                    className="w-full px-3 sm:px-4 py-2 border border-slate-200 rounded text-sm font-black font-mono outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]"
                  />
                </div>
                <div>
                  <label className="block text-[9px] sm:text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2 flex items-center gap-1.5">
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>
                    Stock Actual
                  </label>
                  <input
                    type="number" step="0.01" min="0" name="stock_actual"
                    value={formData.stock_actual} onChange={handleChange} placeholder="0.00"
                    className="w-full px-3 sm:px-4 py-2 border border-slate-200 rounded text-sm font-black font-mono outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]"
                  />
                </div>
                <div>
                  <label className="block text-[9px] sm:text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 sm:mb-2 flex items-center gap-1.5">
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                    Stock Mínimo
                  </label>
                  <input
                    type="number" step="0.01" min="0" name="stock_minimo"
                    value={formData.stock_minimo} onChange={handleChange} placeholder="0.00"
                    className="w-full px-3 sm:px-4 py-2 border border-slate-200 rounded text-sm font-black font-mono outline-none focus:border-[#1A5729] focus:ring-1 focus:ring-[#1A5729]"
                  />
                </div>
              </div>

              {/* Botonera */}
              <div className="mt-6 sm:mt-8 flex flex-col-reverse sm:flex-row justify-end gap-3 pt-4 sm:pt-6 border-t border-slate-200 shrink-0">
                <button type="button" onClick={() => setShowModal(false)}
                  className="w-full sm:w-auto px-4 sm:px-6 py-3 sm:py-2.5 text-[10px] font-black text-slate-500 uppercase tracking-widest hover:bg-slate-200 rounded-md transition-colors text-center">
                  CANCELAR OPERACIÓN
                </button>
                <button type="submit"
                  className="w-full sm:w-auto px-6 sm:px-10 py-3 sm:py-2.5 bg-[#1A5729] text-white text-[10px] font-black uppercase tracking-widest rounded-md shadow-lg hover:bg-[#144320] transition-all flex items-center justify-center gap-2">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                  {isEditing ? 'GUARDAR CAMBIOS' : 'REGISTRAR'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}