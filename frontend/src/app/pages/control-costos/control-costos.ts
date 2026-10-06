import { DestroyRef } from '@angular/core';
import { LecturasVigentes } from '../../services/lecturas';
import { ContextoOperativo } from '../../services/contexto-operativo';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { finalize, forkJoin } from 'rxjs';
import { DashboardCardComponent } from '../../components/ui/dashboard-card';
import { PageHeaderComponent } from '../../components/ui/page-header';
import { AuthService } from '../../services/auth';
import {
  CategoriaCosto, ComparacionPartida, ControlCostosService, CostoCreatePayload,
  CostoEjecutado, EstadoCosto, EstadoOrden, HistorialOrden, LineaBase,
  OrdenCambio, OrdenCreatePayload, OrdenDetallePayload, OrdenUpdatePayload,
  PresupuestoAprobado, TipoCambio, TotalesControl
} from '../../services/control-costos.service';
import { Proyecto, ProyectosService } from '../../services/proyectos';

type TabControl = 'resumen' | 'costos' | 'comparacion' | 'ordenes';
type ModalControl = 'costo' | 'anular' | 'orden' | 'decidir' | 'historial' | null;

interface ErrorHttp {
  status?: number;
  error?: { detail?: string | Array<{ msg?: string }>; message?: string };
}

interface CostoForm {
  id_partida_presupuestaria: number;
  fecha: string;
  concepto: string;
  categoria: CategoriaCosto;
  cantidad: number;
  costo_unitario: number;
  documento: string;
  observacion: string;
}

interface DetalleOrdenForm {
  id_partida_presupuestaria: number | null;
  tipo_cambio: TipoCambio;
  cantidad_delta: number;
  costo_nuevo: number | null;
  item_codigo_snapshot: string;
  descripcion_snapshot: string;
  unidad_snapshot: string;
  observacion: string;
}

interface OrdenForm {
  codigo: string;
  titulo: string;
  descripcion: string;
  justificacion: string;
  fecha: string;
  impacto_plazo_dias: number;
  detalles: DetalleOrdenForm[];
}

@Component({
  selector: 'app-control-costos',
  standalone: true,
  imports: [CommonModule, FormsModule, PageHeaderComponent, DashboardCardComponent],
  templateUrl: './control-costos.html',
  styleUrl: './control-costos.css'
})
export class ControlCostosComponent implements OnInit {
  get contextoCompatible() { return this.auth.obtenerIdEmpresaActiva() === Number(this.auth.obtenerUsuario()?.id_empresa); }
  private contexto = inject(ContextoOperativo);
  private destroyRef = inject(DestroyRef);
  private reads = new LecturasVigentes(this.destroyRef);
  private readonly service = inject(ControlCostosService);
  private readonly proyectosService = inject(ProyectosService);
  private readonly auth = inject(AuthService);
  private readonly cdr = inject(ChangeDetectorRef);

  proyectos: Proyecto[] = [];
  idObra = 0;
  presupuestos: PresupuestoAprobado[] = [];
  idEstimacionSeleccionada = 0;
  lineaBase: LineaBase | null = null;
  costos: CostoEjecutado[] = [];
  partidas: ComparacionPartida[] = [];
  ordenes: OrdenCambio[] = [];
  historial: HistorialOrden[] = [];
  totales: TotalesControl | null = null;
  tab: TabControl = 'resumen';
  modal: ModalControl = null;
  cargando = false;
  cargandoContexto = false;
  guardando = false;
  error = '';
  exito = '';
  filtroEstadoCosto: '' | EstadoCosto = '';
  filtroEstadoOrden: '' | EstadoOrden = '';
  costoObjetivo: CostoEjecutado | null = null;
  ordenObjetivo: OrdenCambio | null = null;
  ordenEditando: OrdenCambio | null = null;
  accionDecision: 'APROBAR' | 'RECHAZAR' = 'APROBAR';
  motivo = '';
  costoForm: CostoForm = this.nuevoCosto();
  ordenForm: OrdenForm = this.nuevaOrden();

  readonly categorias: CategoriaCosto[] = ['MATERIAL', 'MANO_OBRA', 'EQUIPO', 'SUBCONTRATO', 'OTRO'];
  readonly tiposCambio: TipoCambio[] = ['AUMENTO_CANTIDAD', 'DISMINUCION_CANTIDAD', 'CAMBIO_COSTO', 'NUEVA_PARTIDA', 'ELIMINACION_PARTIDA'];

  ngOnInit(): void {
    this.contexto.proteger(() => this.modal !== null, this.destroyRef);
    this.contexto.protegerEscritura(() => this.guardando, this.destroyRef);
    this.contexto.operativo$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.reads.cancelar(); this.modal = null; this.limpiarContexto(); this.proyectos = [];
      this.idObra = this.contexto.obra?.id_obra || 0;
      if (this.contextoCompatible) this.cargarProyectos(); else { this.cargando = false; this.cargandoContexto = false; }
    });
  }

  private hoy(): string { return new Date().toISOString().slice(0, 10); }

  private nuevoCosto(): CostoForm {
    return { id_partida_presupuestaria: 0, fecha: this.hoy(), concepto: '', categoria: 'MATERIAL', cantidad: 1, costo_unitario: 0, documento: '', observacion: '' };
  }

  private nuevoDetalle(): DetalleOrdenForm {
    return { id_partida_presupuestaria: null, tipo_cambio: 'AUMENTO_CANTIDAD', cantidad_delta: 1, costo_nuevo: null, item_codigo_snapshot: '', descripcion_snapshot: '', unidad_snapshot: '', observacion: '' };
  }

  private nuevaOrden(): OrdenForm {
    return { codigo: '', titulo: '', descripcion: '', justificacion: '', fecha: this.hoy(), impacto_plazo_dias: 0, detalles: [this.nuevoDetalle()] };
  }

  cargarProyectos(): void {
    this.cargando = true;
    this.proyectosService.listarProyectos().pipe(finalize(() => { this.cargando = false; this.cdr.detectChanges(); })).pipe(this.reads.reemplazar('obras')).subscribe({
      next: response => { this.proyectos = (response.data || []).filter(p => Boolean(p.id_obra) && Number(p.id_empresa) === this.auth.obtenerIdEmpresaActiva()); if (this.idObra && this.proyectos.some(p => p.id_obra === this.idObra)) this.cambiarObra(); },
      error: error => this.mostrarError(this.mensajeError(error, 'No se pudieron cargar las obras.'))
    });
  }

  cambiarObra(): void {
    if (!this.contextoCompatible) return;
    if ((this.contexto.obra?.id_obra || 0) !== this.idObra) { if (!this.contexto.confirmarCambio()) return; this.contexto.seleccionar(this.proyectos.find(work => work.id_obra === this.idObra) || null); return; }
    this.limpiarContexto();
    if (!this.idObra) return;
    this.cargandoContexto = true;
    this.service.presupuestosAprobados(this.idObra).pipe(this.reads.reemplazar('presupuestos')).subscribe({
      next: response => {
        this.presupuestos = response.data || [];
        this.idEstimacionSeleccionada = this.presupuestos[0]?.id_estimacion || 0;
        this.cdr.detectChanges();
      },
      error: error => this.mostrarError(this.mensajeError(error, 'No se pudieron cargar los presupuestos aprobados.'))
    });
    this.service.lineaBase(this.idObra).pipe(finalize(() => { this.cargandoContexto = false; this.cdr.detectChanges(); })).pipe(this.reads.reemplazar('linea-base')).subscribe({
      next: response => { this.lineaBase = response.data; this.cargarDatosControl(); },
      error: error => {
        const err = error as ErrorHttp;
        if (err.status !== 404) this.mostrarError(this.mensajeError(error, 'No se pudo consultar la línea base.'));
      }
    });
  }

  seleccionarLineaBase(): void {
    if (!this.idObra || !this.idEstimacionSeleccionada || this.guardando) return;
    this.guardando = true;
    this.service.crearLineaBase(this.idObra, this.idEstimacionSeleccionada).pipe(finalize(() => { this.guardando = false; this.cdr.detectChanges(); })).subscribe({
      next: response => { this.lineaBase = response.data; this.mostrarExito('Línea base seleccionada correctamente.'); this.cargarDatosControl(); },
      error: error => this.mostrarError(this.mensajeError(error, 'No se pudo seleccionar la línea base.'))
    });
  }

  cargarDatosControl(): void {
    if (!this.lineaBase || !this.idObra) return;
    this.cargando = true;
    forkJoin({
      comparacion: this.service.comparacion(this.idObra),
      resumen: this.service.resumen(this.idObra),
      costos: this.service.costos({ id_control_costo: this.lineaBase.id_control_costo, estado: this.filtroEstadoCosto || undefined }),
      ordenes: this.service.ordenes({ id_control_costo: this.lineaBase.id_control_costo, estado: this.filtroEstadoOrden || undefined })
    }).pipe(finalize(() => { this.cargando = false; this.cdr.detectChanges(); })).pipe(this.reads.reemplazar('control')).subscribe({
      next: response => {
        this.partidas = response.comparacion.data.partidas || [];
        this.totales = response.resumen.data.resumen;
        this.costos = response.costos.data || [];
        this.ordenes = response.ordenes.data || [];
      },
      error: error => this.mostrarError(this.mensajeError(error, 'No se pudo cargar el control de costos.'))
    });
  }

  filtrarCostos(): void {
    if (!this.lineaBase) return;
    this.service.costos({ id_control_costo: this.lineaBase.id_control_costo, estado: this.filtroEstadoCosto || undefined }).pipe(this.reads.reemplazar('costos')).subscribe({
      next: response => { this.costos = response.data || []; this.cdr.detectChanges(); },
      error: error => this.mostrarError(this.mensajeError(error, 'No se pudieron filtrar los costos.'))
    });
  }

  filtrarOrdenes(): void {
    if (!this.lineaBase) return;
    this.service.ordenes({ id_control_costo: this.lineaBase.id_control_costo, estado: this.filtroEstadoOrden || undefined }).pipe(this.reads.reemplazar('ordenes')).subscribe({
      next: response => { this.ordenes = response.data || []; this.cdr.detectChanges(); },
      error: error => this.mostrarError(this.mensajeError(error, 'No se pudieron filtrar las órdenes.'))
    });
  }

  abrirCosto(): void { this.costoForm = this.nuevoCosto(); this.modal = 'costo'; this.error = ''; }
  montoCosto(): number { return Math.round((Number(this.costoForm.cantidad) * Number(this.costoForm.costo_unitario) + Number.EPSILON) * 100) / 100; }

  guardarCosto(): void {
    if (!this.lineaBase || this.guardando) return;
    const validacion = this.validarCosto();
    if (validacion) { this.mostrarError(validacion); return; }
    const payload: CostoCreatePayload = {
      id_control_costo: this.lineaBase.id_control_costo,
      id_partida_presupuestaria: Number(this.costoForm.id_partida_presupuestaria),
      fecha: this.costoForm.fecha,
      concepto: this.costoForm.concepto.trim(),
      categoria: this.costoForm.categoria,
      cantidad: Number(this.costoForm.cantidad),
      costo_unitario: Number(this.costoForm.costo_unitario),
      monto: this.montoCosto(),
      documento: this.costoForm.documento.trim() || null,
      observacion: this.costoForm.observacion.trim() || null
    };
    this.guardando = true;
    this.service.registrarCosto(payload).pipe(finalize(() => { this.guardando = false; this.cdr.detectChanges(); })).subscribe({
      next: () => { this.modal = null; this.mostrarExito('Costo ejecutado registrado correctamente.'); this.cargarDatosControl(); },
      error: error => this.mostrarError(this.mensajeError(error, 'No se pudo registrar el costo.'))
    });
  }

  private validarCosto(): string | null {
    if (!this.costoForm.id_partida_presupuestaria) return 'Selecciona una partida presupuestaria.';
    if (!this.costoForm.fecha) return 'La fecha es obligatoria.';
    if (!this.costoForm.concepto.trim()) return 'El concepto es obligatorio.';
    if (!Number.isFinite(Number(this.costoForm.cantidad)) || Number(this.costoForm.cantidad) < 0) return 'La cantidad no puede ser negativa.';
    if (!Number.isFinite(Number(this.costoForm.costo_unitario)) || Number(this.costoForm.costo_unitario) < 0) return 'El costo unitario no puede ser negativo.';
    return null;
  }

  abrirAnular(costo: CostoEjecutado): void { this.costoObjetivo = costo; this.motivo = ''; this.modal = 'anular'; }
  confirmarAnulacion(): void {
    if (!this.costoObjetivo || !this.motivo.trim() || this.guardando) { if (!this.motivo.trim()) this.mostrarError('El motivo de anulación es obligatorio.'); return; }
    this.guardando = true;
    this.service.anularCosto(this.costoObjetivo.id_costo_ejecutado, this.motivo.trim()).pipe(finalize(() => { this.guardando = false; this.cdr.detectChanges(); })).subscribe({
      next: () => { this.modal = null; this.costoObjetivo = null; this.mostrarExito('Costo anulado correctamente.'); this.cargarDatosControl(); },
      error: error => this.mostrarError(this.mensajeError(error, 'No se pudo anular el costo.'))
    });
  }

  abrirNuevaOrden(): void { this.ordenEditando = null; this.ordenForm = this.nuevaOrden(); this.modal = 'orden'; this.error = ''; }
  abrirEditarOrden(orden: OrdenCambio): void {
    if (orden.estado !== 'PENDIENTE') return;
    this.cargando = true;
    this.service.orden(orden.id_orden_cambio).pipe(finalize(() => { this.cargando = false; this.cdr.detectChanges(); })).subscribe({
      next: response => {
        const full = response.data;
        this.ordenEditando = full;
        this.ordenForm = {
          codigo: full.codigo, titulo: full.titulo, descripcion: full.descripcion || '', justificacion: full.justificacion,
          fecha: full.fecha, impacto_plazo_dias: full.impacto_plazo_dias,
          detalles: (full.detalles || []).map(detail => ({
            id_partida_presupuestaria: detail.id_partida_presupuestaria || null, tipo_cambio: detail.tipo_cambio,
            cantidad_delta: detail.cantidad_delta, costo_nuevo: detail.costo_nuevo,
            item_codigo_snapshot: detail.item_codigo_snapshot, descripcion_snapshot: detail.descripcion_snapshot,
            unidad_snapshot: detail.unidad_snapshot, observacion: detail.observacion || ''
          }))
        };
        this.modal = 'orden';
      },
      error: error => this.mostrarError(this.mensajeError(error, 'No se pudo cargar la orden.'))
    });
  }

  agregarDetalle(): void { this.ordenForm.detalles.push(this.nuevoDetalle()); }
  quitarDetalle(index: number): void { if (this.ordenForm.detalles.length > 1) this.ordenForm.detalles.splice(index, 1); }
  cambioTipo(detalle: DetalleOrdenForm): void {
    if (detalle.tipo_cambio === 'NUEVA_PARTIDA') detalle.id_partida_presupuestaria = null;
    else { detalle.item_codigo_snapshot = ''; detalle.descripcion_snapshot = ''; detalle.unidad_snapshot = ''; }
    if (detalle.tipo_cambio === 'ELIMINACION_PARTIDA') detalle.cantidad_delta = 0;
  }

  guardarOrden(): void {
    if (!this.lineaBase || this.guardando) return;
    const validacion = this.validarOrden();
    if (validacion) { this.mostrarError(validacion); return; }
    const detalles: OrdenDetallePayload[] = this.ordenForm.detalles.map(detail => ({
      id_partida_presupuestaria: detail.tipo_cambio === 'NUEVA_PARTIDA' ? null : Number(detail.id_partida_presupuestaria),
      tipo_cambio: detail.tipo_cambio,
      item_codigo_snapshot: detail.tipo_cambio === 'NUEVA_PARTIDA' ? detail.item_codigo_snapshot.trim() : null,
      descripcion_snapshot: detail.tipo_cambio === 'NUEVA_PARTIDA' ? detail.descripcion_snapshot.trim() : null,
      unidad_snapshot: detail.tipo_cambio === 'NUEVA_PARTIDA' ? detail.unidad_snapshot.trim() : null,
      cantidad_delta: Number(detail.cantidad_delta),
      costo_nuevo: detail.tipo_cambio === 'CAMBIO_COSTO' || detail.tipo_cambio === 'NUEVA_PARTIDA' ? Number(detail.costo_nuevo) : null,
      observacion: detail.observacion.trim() || null
    }));
    const common = {
      titulo: this.ordenForm.titulo.trim(), descripcion: this.ordenForm.descripcion.trim() || null,
      justificacion: this.ordenForm.justificacion.trim(), fecha: this.ordenForm.fecha,
      impacto_plazo_dias: Number(this.ordenForm.impacto_plazo_dias), detalles
    };
    const request = this.ordenEditando
      ? this.service.actualizarOrden(this.ordenEditando.id_orden_cambio, common as OrdenUpdatePayload)
      : this.service.crearOrden({ ...common, id_control_costo: this.lineaBase.id_control_costo, codigo: this.ordenForm.codigo.trim() } as OrdenCreatePayload);
    this.guardando = true;
    request.pipe(finalize(() => { this.guardando = false; this.cdr.detectChanges(); })).subscribe({
      next: () => { this.modal = null; this.mostrarExito(this.ordenEditando ? 'Orden actualizada correctamente.' : 'Orden creada correctamente.'); this.ordenEditando = null; this.cargarDatosControl(); },
      error: error => this.mostrarError(this.mensajeError(error, 'No se pudo guardar la orden.'))
    });
  }

  private validarOrden(): string | null {
    if (!this.ordenEditando && !this.ordenForm.codigo.trim()) return 'El código de la orden es obligatorio.';
    if (!this.ordenForm.titulo.trim()) return 'El título es obligatorio.';
    if (!this.ordenForm.justificacion.trim()) return 'La justificación es obligatoria.';
    if (!this.ordenForm.fecha) return 'La fecha es obligatoria.';
    if (!Number.isFinite(Number(this.ordenForm.impacto_plazo_dias))) return 'El impacto de plazo debe ser válido.';
    if (!this.ordenForm.detalles.length) return 'Agrega al menos un detalle.';
    for (const [index, detail] of this.ordenForm.detalles.entries()) {
      const label = `Detalle ${index + 1}`;
      if (detail.tipo_cambio === 'NUEVA_PARTIDA') {
        if (!detail.item_codigo_snapshot.trim() || !detail.descripcion_snapshot.trim() || !detail.unidad_snapshot.trim()) return `${label}: código, descripción y unidad son obligatorios.`;
        if (!(Number(detail.cantidad_delta) > 0)) return `${label}: la cantidad nueva debe ser mayor que cero.`;
        if (detail.costo_nuevo === null || Number(detail.costo_nuevo) < 0) return `${label}: el costo nuevo es obligatorio y no puede ser negativo.`;
      } else {
        if (!detail.id_partida_presupuestaria) return `${label}: selecciona una partida.`;
        if (detail.tipo_cambio === 'AUMENTO_CANTIDAD' && !(Number(detail.cantidad_delta) > 0)) return `${label}: el aumento requiere una cantidad positiva.`;
        if (detail.tipo_cambio === 'DISMINUCION_CANTIDAD' && !(Number(detail.cantidad_delta) < 0)) return `${label}: la disminución requiere una cantidad negativa.`;
        if (detail.tipo_cambio === 'CAMBIO_COSTO' && (detail.costo_nuevo === null || Number(detail.costo_nuevo) < 0)) return `${label}: indica un costo nuevo válido.`;
      }
    }
    return null;
  }

  abrirDecision(orden: OrdenCambio, accion: 'APROBAR' | 'RECHAZAR'): void { this.ordenObjetivo = orden; this.accionDecision = accion; this.motivo = ''; this.modal = 'decidir'; }
  confirmarDecision(): void {
    if (!this.ordenObjetivo || this.guardando) return;
    if (this.accionDecision === 'RECHAZAR' && !this.motivo.trim()) { this.mostrarError('El motivo de rechazo es obligatorio.'); return; }
    const request = this.accionDecision === 'APROBAR'
      ? this.service.aprobarOrden(this.ordenObjetivo.id_orden_cambio, this.motivo)
      : this.service.rechazarOrden(this.ordenObjetivo.id_orden_cambio, this.motivo.trim());
    this.guardando = true;
    request.pipe(finalize(() => { this.guardando = false; this.cdr.detectChanges(); })).subscribe({
      next: () => { this.modal = null; this.ordenObjetivo = null; this.mostrarExito(`Orden ${this.accionDecision === 'APROBAR' ? 'aprobada' : 'rechazada'} correctamente.`); this.cargarDatosControl(); },
      error: error => this.mostrarError(this.mensajeError(error, 'No se pudo decidir la orden.'))
    });
  }

  verHistorial(orden: OrdenCambio): void {
    this.ordenObjetivo = orden; this.historial = []; this.modal = 'historial';
    this.service.historial(orden.id_orden_cambio).subscribe({
      next: response => { this.historial = response.data || []; this.cdr.detectChanges(); },
      error: error => this.mostrarError(this.mensajeError(error, 'No se pudo cargar el historial.'))
    });
  }

  cerrarModal(): void { if (this.guardando) return; this.modal = null; this.costoObjetivo = null; this.ordenObjetivo = null; this.ordenEditando = null; this.error = ''; }
  puede(permiso: string): boolean { return this.auth.hasPermission(permiso); }
  partidasBase(): ComparacionPartida[] { return this.partidas.filter(p => !p.nueva_partida && p.id_partida_presupuestaria !== null); }
  obraSeleccionada(): Proyecto | undefined { return this.proyectos.find(p => p.id_obra === Number(this.idObra)); }
  presupuestoSeleccionado(): PresupuestoAprobado | undefined { return this.presupuestos.find(p => p.id_estimacion === Number(this.idEstimacionSeleccionada)); }
  formatoTipo(tipo: string): string { return tipo.replaceAll('_', ' '); }
  dinero(valor: number | null | undefined): string { return new Intl.NumberFormat('es-BO', { style: 'currency', currency: this.lineaBase?.moneda || 'BOB', minimumFractionDigits: 2 }).format(Number(valor || 0)); }
  claseEstado(estado: string): string { return estado.toLowerCase(); }
  claseVariacion(valor: number): string { return Number(valor) > 0 ? 'negative' : Number(valor) < 0 ? 'positive' : 'neutral'; }

  private limpiarContexto(): void {
    this.presupuestos = []; this.idEstimacionSeleccionada = 0; this.lineaBase = null; this.costos = []; this.partidas = []; this.ordenes = []; this.totales = null;
  }

  private mensajeError(error: unknown, fallback: string): string {
    const err = error as ErrorHttp;
    const detail = err.error?.detail;
    if (Array.isArray(detail)) return detail.map(item => item.msg || 'Dato inválido.').join(' ');
    if (typeof detail === 'string') return detail;
    if (err.status === 403) return 'No tienes permisos para realizar esta acción.';
    if (err.status === 409) return err.error?.message || 'La operación entra en conflicto con el estado actual.';
    return err.error?.message || fallback;
  }

  private mostrarError(message: string): void { this.error = message; this.cdr.detectChanges(); setTimeout(() => { this.error = ''; this.cdr.detectChanges(); }, 6500); }
  private mostrarExito(message: string): void { this.exito = message; this.cdr.detectChanges(); setTimeout(() => { this.exito = ''; this.cdr.detectChanges(); }, 4500); }
}
