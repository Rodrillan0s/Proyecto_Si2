import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { EstimacionesService, Apu, ApuInsumo, ApuDetalle, ManoObra, Estimacion, EstimacionDetalle } from '../../services/estimaciones.service';
import { MaterialsService, UnidadMedida, Material } from '../../services/materials.service';
import { ProyectosService, Proyecto } from '../../services/proyectos';

interface InsumoFila {
  editing: boolean;
  guardando: boolean;
  id?: number;
  tipo_insumo: string;
  id_material?: number | null;
  id_mano_obra?: number | null;
  nombre: string;
  id_unidad_medida?: number;
  cantidad: number;
  precio_unitario: number;
  orden: number;
  nuevo: boolean;
  error?: string;
}

@Component({
  selector: 'app-estimaciones',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './estimaciones.html',
  styleUrl: './estimaciones.css'
})
export class EstimacionesComponent implements OnInit {
  private readonly service = inject(EstimacionesService);
  private readonly materials = inject(MaterialsService);
  private readonly proyectos = inject(ProyectosService);
  private readonly route = inject(ActivatedRoute);
  private readonly cdr = inject(ChangeDetectorRef);

  idObra?: number;
  apus: Apu[] = [];
  estimaciones: Estimacion[] = [];
  unidades: UnidadMedida[] = [];
  materiales: Material[] = [];
  manoObra: ManoObra[] = [];
  obras: Proyecto[] = [];

  filtro = { texto: '', tipo: '', calidad: '' };
  cargando = true;
  error = '';
  guardando = false;
  mensaje = '';

  // Editor de partida / APU
  editor: { abierto: boolean; editar: boolean; idApu?: number; form: { nombre: string; descripcion: string; id_unidad_medida?: number; tipo_analisis_precio_unitario: string; calidad: string } } = {
    abierto: false, editar: false, form: { nombre: '', descripcion: '', tipo_analisis_precio_unitario: 'OBRA_GRIS', calidad: '' }
  };
  insumos: InsumoFila[] = [];

  // Delector de material / cuadrilla para el editor
  editorColumna = '';

  // Estimación
  est: { abierto: boolean; nuevo: boolean; form: { id_obra?: number; nombre: string; descripcion: string; factor_utilidad: number | null } } = {
    abierto: false, nuevo: false, form: { nombre: '', descripcion: '', factor_utilidad: null }
  };
  detalle: Estimacion | null = null;
  mostrarDetalle = false;
  agregarApu = false;
  apuSeleccionado?: number;
  cantidadApu = 1;
  guardandoDetalle = false;

  // Nueva cuadrilla
  mo: { abierto: boolean; nombre: string; costo_unitario: number | null } = { abierto: false, nombre: '', costo_unitario: null };

  ngOnInit(): void {
    const id = this.route.snapshot.queryParamMap.get('id_obra');
    this.idObra = id ? Number(id) : undefined;
    this.cargarCatalogo();
  }

  private cargarCatalogo(): void {
    this.materials.unidadesMedida().subscribe({ next: r => { this.unidades = r.data || []; this.cdr.detectChanges(); } });
    this.materials.listar({ limit: 200 }).subscribe({ next: r => { this.materiales = r.data || []; this.cdr.detectChanges(); } });
    this.service.listarManoObra().subscribe({ next: r => { this.manoObra = r.data || []; this.cdr.detectChanges(); } });
    this.cargarObras();
  }

  private cargarObras(): void {
    this.proyectos.listarProyectos().subscribe({
      next: r => { this.obras = r.data || []; if (!this.idObra && this.obras.length && this.obras[0].id_obra) this.idObra = this.obras[0].id_obra; this.cargar(); this.cdr.detectChanges(); },
      error: () => { this.cargar(); }
    });
  }

  cambiarObra(obraId: number): void {
    this.idObra = obraId || undefined;
    this.filtro.tipo = '';
    this.filtro.calidad = '';
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    this.service.listarApu({ id_obra: this.idObra, tipo_analisis_precio_unitario: this.filtro.tipo || undefined, calidad: this.filtro.calidad || undefined }).subscribe({
      next: response => { this.apus = response.data || []; this.cargando = false; this.cdr.detectChanges(); },
      error: error => { this.error = error?.error?.error || error?.error?.detail || 'No se pudieron cargar las partidas.'; this.cargando = false; this.cdr.detectChanges(); }
    });
    this.service.listarEstimaciones(this.idObra).subscribe({ next: response => { this.estimaciones = response.data || []; this.cdr.detectChanges(); } });
  }

  get apusFiltradas(): Apu[] {
    const query = this.filtro.texto.trim().toLowerCase();
    return this.apus.filter(apu => !query || apu.nombre.toLowerCase().includes(query) || (apu.descripcion || '').toLowerCase().includes(query));
  }

  unidadAbr(id?: number | null): string {
    if (!id) return '—';
    const u = this.unidades.find(x => x.id_unidad_medida === id);
    return u ? `${u.abreviatura}` : `#${id}`;
  }

  obraNombre(idObra: number): string {
    return this.obras.find(o => o.id_obra === idObra)?.nombre || `Obra #${idObra}`;
  }

  totalInsumo(row: InsumoFila): number {
    return (Number(row.cantidad) || 0) * (Number(row.precio_unitario) || 0);
  }

  get costoTemporal(): number {
    return this.insumos.reduce((acc, row) => acc + this.totalInsumo(row), 0);
  }

  // ---------------- Editor de partida (APU) ----------------

  abrirNuevaPartida(): void {
    this.editor = { abierto: true, editar: false, form: { nombre: '', descripcion: '', id_unidad_medida: undefined, tipo_analisis_precio_unitario: 'OBRA_GRIS', calidad: '' } };
    this.insumos = [];
    this.error = '';
  }

  abrirEditar(apu: Apu): void {
    this.error = '';
    this.mensaje = '';
    this.service.detalleApu(apu.id_analisis_precio_unitario).subscribe({
      next: r => {
        const d: ApuDetalle = r.data;
        this.editor = {
          abierto: true, editar: true, idApu: d.id_analisis_precio_unitario,
          form: { nombre: d.nombre, descripcion: d.descripcion || '', id_unidad_medida: d.id_unidad_medida, tipo_analisis_precio_unitario: d.tipo_analisis_precio_unitario, calidad: d.calidad || '' }
        };
        this.insumos = (d.insumos || []).map(i => ({
          editing: false, guardando: false, id: i.id_analisis_precio_unitario_insumo, nuevo: false,
          tipo_insumo: i.tipo_insumo, id_material: i.id_material, id_mano_obra: i.id_mano_obra,
          nombre: i.nombre, id_unidad_medida: i.id_unidad_medida, cantidad: i.cantidad, precio_unitario: i.precio_unitario, orden: i.orden
        }));
        this.cdr.detectChanges();
      },
      error: e => { this.error = e?.error?.error || e?.error?.detail || 'No se pudo cargar la partida.'; this.cdr.detectChanges(); }
    });
  }

  cerrarEditor(): void {
    this.editor.abierto = false;
    this.insumos = [];
  }

  guardarPartida(): void {
    const f = this.editor.form;
    if (!f.nombre.trim() || !f.id_unidad_medida) { this.error = 'Nombre y unidad de medida son obligatorios.'; return; }
    this.guardando = true;
    this.error = '';
    const payload = { ...f, calidad: f.tipo_analisis_precio_unitario === 'ACABADO' ? (f.calidad || 'NORMAL') : undefined, id_obra: this.idObra };
    const op = this.editor.editar && this.editor.idApu
      ? this.service.actualizarApu(this.editor.idApu, payload)
      : this.service.crearApu(payload);
    op.subscribe({
      next: () => { this.guardando = false; this.cerrarEditor(); this.mensaje = 'Partida guardada correctamente.'; this.cargar(); this.cdr.detectChanges(); },
      error: e => { this.guardando = false; this.error = e?.error?.error || e?.error?.detail || 'No se pudo guardar la partida.'; this.cdr.detectChanges(); }
    });
  }

  duplicarApu(apu: Apu): void {
    this.error = '';
    this.service.duplicarApu(apu.id_analisis_precio_unitario).subscribe({
      next: () => { this.mensaje = 'Partida duplicada correctamente.'; this.cargar(); },
      error: e => { this.error = e?.error?.error || e?.error?.detail || 'No se pudo duplicar.'; this.cdr.detectChanges(); }
    });
  }

  desactivarApu(apu: Apu): void {
    if (!confirm(`¿Desactivar la partida "${apu.nombre}"?`)) return;
    this.error = '';
    this.service.actualizarApu(apu.id_analisis_precio_unitario, { activo: false }).subscribe({
      next: () => { this.mensaje = 'Partida desactivada.'; this.cargar(); },
      error: e => { this.error = e?.error?.error || e?.error?.detail || 'No se pudo desactivar.'; this.cdr.detectChanges(); }
    });
  }

  // ---------------- Insumos ----------------

  agregarInsumo(): void {
    this.insumos.push({ editing: true, guardando: false, nuevo: true, tipo_insumo: 'MATERIAL', nombre: '', cantidad: 0, precio_unitario: 0, orden: (this.insumos.length || 0) + 1 });
  }

  private materialPorId(id?: number | null): Material | undefined {
    return this.materiales.find(m => m.id_material === id);
  }

  onMaterial(ev: Event, row: InsumoFila): void {
    const id = Number((ev.target as HTMLSelectElement).value) || null;
    row.id_material = id;
    row.id_mano_obra = null;
    if (id) {
      const mat = this.materialPorId(id);
      if (mat) {
        row.tipo_insumo = 'MATERIAL';
        row.nombre = mat.nombre_material;
        row.id_unidad_medida = mat.unidad_medida?.id_unidad_medida;
        row.precio_unitario = Number(mat.precio) || 0;
      }
    }
  }

  onManoObra(ev: Event, row: InsumoFila): void {
    const id = Number((ev.target as HTMLSelectElement).value) || null;
    row.id_mano_obra = id;
    row.id_material = null;
    if (id) {
      const mo = this.manoObra.find(x => x.id_mano_obra === id);
      if (mo) {
        row.tipo_insumo = 'MANO_OBRA';
        row.nombre = mo.nombre;
        row.id_unidad_medida = mo.id_unidad_medida;
        row.precio_unitario = Number(mo.costo_unitario) || 0;
      }
    }
  }

  cambiarTipoInsumo(row: InsumoFila): void {
    row.id_material = null;
    row.id_mano_obra = null;
  }

  guardarInsumo(row: InsumoFila): void {
    const idApu = this.editor.idApu;
    if (!idApu) { this.error = 'Primero guarda la partida para poder agregar insumos.'; return; }
    this.error = '';
    if (!row.nombre.trim() || !row.id_unidad_medida) { row.error = 'Nombre y unidad son obligatorios.'; return; }
    if (row.tipo_insumo === 'MATERIAL' && !row.id_material) { row.error = 'Selecciona un material del catálogo.'; return; }
    if (row.tipo_insumo === 'MANO_OBRA' && !row.id_mano_obra) { row.error = 'Selecciona una cuadrilla / mano de obra.'; return; }
    row.guardando = true;
    const payload = {
      tipo_insumo: row.tipo_insumo, id_material: row.tipo_insumo === 'MATERIAL' ? row.id_material : null,
      id_mano_obra: row.tipo_insumo === 'MANO_OBRA' ? row.id_mano_obra : null, nombre: row.nombre,
      id_unidad_medida: row.id_unidad_medida, cantidad: row.cantidad, precio_unitario: row.precio_unitario, orden: row.orden
    };
    const op = row.nuevo ? this.service.crearInsumo(idApu, payload) : this.service.actualizarInsumo(idApu, row.id!, payload);
    op.subscribe({
      next: r => {
        if (row.nuevo) { row.id = (r.data as any)?.id_analisis_precio_unitario_insumo; row.nuevo = false; }
        row.editing = false; row.guardando = false; row.error = undefined;
        this.mensaje = 'Insumo guardado.'; this.refrescarPartida(); this.cdr.detectChanges();
      },
      error: e => { row.guardando = false; row.error = e?.error?.error || e?.error?.detail || 'No se pudo guardar el insumo.'; this.cdr.detectChanges(); }
    });
  }

  eliminarInsumo(row: InsumoFila): void {
    this.error = '';
    if (row.nuevo) { this.insumos = this.insumos.filter(r => r !== row); return; }
    if (!this.editor.idApu) return;
    if (!confirm(`¿Eliminar el insumo "${row.nombre}"?`)) return;
    this.service.eliminarInsumo(this.editor.idApu, row.id!).subscribe({
      next: () => { this.insumos = this.insumos.filter(r => r !== row); this.mensaje = 'Insumo eliminado.'; this.refrescarPartida(); this.cdr.detectChanges(); },
      error: e => { this.error = e?.error?.error || e?.error?.detail || 'No se pudo eliminar.'; this.cdr.detectChanges(); }
    });
  }

  cancelarInsumo(row: InsumoFila): void {
    if (row.nuevo) { this.insumos = this.insumos.filter(r => r !== row); return; }
    row.editing = false; row.error = undefined;
  }

  private refrescarPartida(): void {
    if (this.editor.idApu) {
      this.service.detalleApu(this.editor.idApu).subscribe({
        next: r => {
          this.insumos = (r.data.insumos || []).map(i => ({
            editing: false, guardando: false, id: i.id_analisis_precio_unitario_insumo, nuevo: false,
            tipo_insumo: i.tipo_insumo, id_material: i.id_material, id_mano_obra: i.id_mano_obra,
            nombre: i.nombre, id_unidad_medida: i.id_unidad_medida, cantidad: i.cantidad, precio_unitario: i.precio_unitario, orden: i.orden
          }));
          this.cdr.detectChanges();
        }
      });
    }
  }

  // ---------------- Mano de obra ----------------

  crearManoObra(): void {
    if (!this.mo.nombre.trim() || this.mo.costo_unitario == null) { this.error = 'Nombre y costo por jornal son obligatorios.'; return; }
    this.guardando = true;
    const jornal = this.unidades.find(u => u.abreviatura === 'jornal' || u.nombre.toLowerCase() === 'jornal');
    this.service.crearManoObra({ nombre: this.mo.nombre, descripcion: 'Cuadrilla creada desde el editor', id_unidad_medida: jornal?.id_unidad_medida, costo_unitario: this.mo.costo_unitario }).subscribe({
      next: () => { this.mo = { abierto: false, nombre: '', costo_unitario: null }; this.guardando = false; this.service.listarManoObra().subscribe({ next: r => { this.manoObra = r.data || []; this.cdr.detectChanges(); } }); },
      error: e => { this.guardando = false; this.error = e?.error?.error || e?.error?.detail || 'No se pudo crear la cuadrilla.'; this.cdr.detectChanges(); }
    });
  }

  // ---------------- Estimaciones ----------------

  abrirNuevaEstimacion(): void {
    this.error = '';
    this.est = { abierto: true, nuevo: true, form: { id_obra: this.idObra, nombre: `Presupuesto ${(this.estimaciones.length || 0) + 1}`, descripcion: '', factor_utilidad: null } };
  }

  crearEstimacion(): void {
    const f = this.est.form;
    if (!f.nombre.trim() || !f.id_obra) { this.error = 'Nombre y obra son obligatorios.'; return; }
    this.guardando = true;
    this.error = '';
    this.service.crearEstimacion(f).subscribe({
      next: () => { this.guardando = false; this.est.abierto = false; this.mensaje = 'Estimación creada.'; this.cargar(); this.cdr.detectChanges(); },
      error: e => { this.guardando = false; this.error = e?.error?.error || e?.error?.detail || 'No se pudo crear la estimación.'; this.cdr.detectChanges(); }
    });
  }

  verDetalle(est: Estimacion): void {
    this.error = '';
    this.service.detalleEstimacion(est.id_estimacion).subscribe({
      next: r => { this.detalle = r.data; this.mostrarDetalle = true; this.cdr.detectChanges(); },
      error: e => { this.error = e?.error?.error || e?.error?.detail || 'No se pudo cargar la estimación.'; this.cdr.detectChanges(); }
    });
  }

  get detallePartidas(): EstimacionDetalle[] {
    return this.detalle?.calculo?.detalle || [];
  }

  get apusParaAgregar(): Apu[] {
    const idsUsados = new Set((this.detallePartidas || []).map(d => d.id_analisis_precio_unitario));
    return this.apus.filter(a => !idsUsados.has(a.id_analisis_precio_unitario));
  }

  agregarApuAEstimacion(): void {
    if (!this.detalle || !this.apuSeleccionado || this.cantidadApu <= 0) { this.error = 'Selecciona una partida y una cantidad válida.'; return; }
    this.guardandoDetalle = true;
    this.error = '';
    this.service.agregarApuEstimacion(this.detalle.id_estimacion, { id_analisis_precio_unitario: this.apuSeleccionado, cantidad: this.cantidadApu }).subscribe({
      next: () => { this.guardandoDetalle = false; this.apuSeleccionado = undefined; this.cantidadApu = 1; this.agregarApu = false; this.verDetalle(this.detalle!); this.cargar(); },
      error: e => { this.guardandoDetalle = false; this.error = e?.error?.error || e?.error?.detail || 'No se pudo agregar la partida.'; this.cdr.detectChanges(); }
    });
  }

  quitarApuEstimacion(det: EstimacionDetalle): void {
    if (!this.detalle) return;
    if (!confirm(`¿Quitar "${det.nombre}" de la estimación?`)) return;
    this.service.eliminarDetalleEstimacion(this.detalle.id_estimacion, det.id_estimacion_analisis_precio_unitario!).subscribe({
      next: () => { this.verDetalle(this.detalle!); this.cargar(); },
      error: e => { this.error = e?.error?.error || e?.error?.detail || 'No se pudo quitar la partida.'; this.cdr.detectChanges(); }
    });
  }

  aprobar(): void {
    if (!this.detalle) return;
    if (!confirm('¿Aprobar la estimación? Actualizará el estado de la obra.')) return;
    this.service.aprobarEstimacion(this.detalle.id_estimacion).subscribe({
      next: () => { this.mensaje = 'Estimación aprobada.'; this.verDetalle(this.detalle!); this.cargar(); },
      error: e => { this.error = e?.error?.error || e?.error?.detail || 'No se pudo aprobar.'; this.cdr.detectChanges(); }
    });
  }

  cerrarDetalle(): void {
    this.mostrarDetalle = false;
    this.detalle = null;
    this.agregarApu = false;
  }
}