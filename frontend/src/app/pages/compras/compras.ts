import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, DestroyRef, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject, debounceTime, distinctUntilChanged } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AuthService } from '../../services/auth';
import {
  ComprasService,
  EstadoOrdenCompra,
  OrdenCompra,
  OrdenCompraDetalle
} from '../../services/compras.service';
import { Proveedor, ProveedorService } from '../../services/proveedor.service';
import { Material, MaterialsService } from '../../services/materials.service';
import { Empresa, EmpresaService } from '../../services/empresa';

interface FormItem {
  id_material: number | null;
  codigo?: string;
  nombre_material?: string;
  unidad_medida?: string;
  cantidad_solicitada: number;
  precio_unitario: number;
  subtotal: number;
}

interface RecepcionItemForm {
  id_material: number;
  codigo_material: string;
  nombre_material: string;
  unidad_medida: string;
  cantidad_solicitada: number;
  cantidad_recibida_previa: number;
  cantidad_pendiente: number;
  cantidad_a_recibir: number;
  precio_unitario: number;
}

@Component({
  selector: 'app-compras',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './compras.html',
  styleUrl: './compras.css'
})
export class ComprasComponent implements OnInit {
  private comprasSvc = inject(ComprasService);
  private proveedorSvc = inject(ProveedorService);
  private materialSvc = inject(MaterialsService);
  private empresaSvc = inject(EmpresaService);
  private auth = inject(AuthService);
  private cdr = inject(ChangeDetectorRef);
  private destroyRef = inject(DestroyRef);
  private busqueda$ = new Subject<string>();

  // Listado principal
  ordenes: OrdenCompra[] = [];
  q = '';
  estadoFiltro = '';
  proveedorFiltro: number | null = null;
  pagina = 1;
  limite = 15;
  total = 0;
  totalPaginas = 0;

  // Estados de carga
  loading = false;
  guardando = false;
  procesandoAccion = false;

  // Feedback
  error = '';
  exito = '';

  // Contexto de empresa
  empresaActiva: any = null;
  empresas: Empresa[] = [];

  // Modales: 'nueva' | 'detalle' | 'aprobar_rechazar' | 'recepcion' | 'cancelar' | null
  modalActivo: 'nueva' | 'detalle' | 'aprobar_rechazar' | 'recepcion' | 'cancelar' | null = null;

  // Catálogos para formulario
  proveedores: Proveedor[] = [];
  materiales: Material[] = [];

  // Formulario Nueva Orden
  formNueva = {
    id_empresa: null as number | null,
    id_proveedor: null as number | null,
    fecha: new Date().toISOString().split('T')[0],
    observaciones: '',
    enviar_aprobacion: false,
    items: [] as FormItem[]
  };

  // Detalle activo
  ordenSeleccionada?: OrdenCompra;
  tabDetalle: 'materiales' | 'recepciones' = 'materiales';

  // Modal Aprobación / Rechazo
  accionAprobacion: 'APROBADA' | 'RECHAZADA' = 'APROBADA';
  observacionAprobacion = '';

  // Modal Recepción
  recepcionItems: RecepcionItemForm[] = [];
  observacionesRecepcion = '';

  // Modal Cancelar
  motivoCancelacion = '';

  ngOnInit(): void {
    this.busqueda$
      .pipe(debounceTime(350), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        this.pagina = 1;
        this.cargarOrdenes();
      });

    this.auth.empresaActiva$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(emp => {
        this.empresaActiva = emp;
        this.pagina = 1;
        this.cargarOrdenes();
        this.cargarCatalogos();
      });

    this.empresaActiva = this.auth.obtenerEmpresaActiva();
    if (this.esVistaGlobal()) {
      this.empresaSvc.listarEmpresas().subscribe({
        next: res => {
          this.empresas = res.data || [];
          this.cdr.detectChanges();
        }
      });
    }

    this.cargarOrdenes();
    this.cargarCatalogos();
  }

  esVistaGlobal(): boolean {
    return this.auth.esVistaGlobal();
  }

  // ── Permisos ───────────────────────────────────────────────────────────────
  puedeVisualizar(): boolean {
    return this.auth.hasPermission('Visualizar_ordenes_compra');
  }

  puedeRegistrar(): boolean {
    return this.auth.hasPermission('Registrar_ordenes_compra');
  }

  puedeAprobar(): boolean {
    return this.auth.hasPermission('Aprobar_ordenes_compra');
  }

  puedeRecepcionar(): boolean {
    return this.auth.hasPermission('Recepcionar_ordenes_compra');
  }

  // ── Cargas de datos ────────────────────────────────────────────────────────
  onBuscar(termino: string): void {
    this.busqueda$.next(termino);
  }

  cambiarFiltroEstado(estado: string): void {
    this.estadoFiltro = estado;
    this.pagina = 1;
    this.cargarOrdenes();
  }

  cargarOrdenes(): void {
    this.loading = true;
    this.error = '';
    const idEmpresa = this.auth.obtenerIdEmpresaActiva();
    this.comprasSvc.listar({
      q: this.q.trim() || undefined,
      estado: this.estadoFiltro || undefined,
      id_proveedor: this.proveedorFiltro || undefined,
      id_empresa: idEmpresa || undefined,
      page: this.pagina,
      limit: this.limite
    }).subscribe({
      next: res => {
        this.ordenes = res.data || [];
        this.total = res.pagination?.total || 0;
        this.totalPaginas = res.pagination?.total_pages || 0;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: err => {
        this.loading = false;
        this.mostrarError(this.extraerError(err, 'Error al cargar órdenes de compra.'));
      }
    });
  }

  cargarCatalogos(idEmpresaOverride?: number): void {
    const idEmpresa = idEmpresaOverride !== undefined ? idEmpresaOverride : this.auth.obtenerIdEmpresaActiva();
    this.proveedorSvc.listar({ estado: 'ACTIVO', limit: 100, id_empresa: idEmpresa || undefined }).subscribe({
      next: res => { this.proveedores = res.data || []; this.cdr.detectChanges(); }
    });

    this.materialSvc.listar({ estado: 'ACTIVO', limit: 500, id_empresa: idEmpresa || undefined }).subscribe({
      next: res => { this.materiales = res.data || []; this.cdr.detectChanges(); },
      error: err => { console.error('Error al cargar materiales:', err); }
    });
  }

  // ── Métricas rápidas ───────────────────────────────────────────────────────
  get conteoPendientes(): number {
    return this.ordenes.filter(o => o.estado === 'PENDIENTE_APROBACION').length;
  }

  get conteoAprobadas(): number {
    return this.ordenes.filter(o => o.estado === 'APROBADA' || o.estado === 'RECIBIDA_PARCIAL').length;
  }

  get conteoRecibidas(): number {
    return this.ordenes.filter(o => o.estado === 'RECIBIDA').length;
  }

  abrirModalNueva(): void {
    const idEmpresa = this.auth.obtenerIdEmpresaActiva();
    this.formNueva = {
      id_empresa: idEmpresa || null,
      id_proveedor: null,
      fecha: new Date().toISOString().split('T')[0],
      observaciones: '',
      enviar_aprobacion: false,
      items: []
    };
    this.cargarCatalogos(this.formNueva.id_empresa || undefined);
    this.agregarItemForm();
    this.modalActivo = 'nueva';
    this.cdr.detectChanges();
  }

  onEmpresaFormCambiada(): void {
    this.formNueva.id_proveedor = null;
    this.formNueva.items = [];
    this.agregarItemForm();
    this.cargarCatalogos(this.formNueva.id_empresa || undefined);
  }

  agregarItemForm(): void {
    this.formNueva.items.push({
      id_material: null,
      cantidad_solicitada: 1,
      precio_unitario: 0,
      subtotal: 0
    });
  }

  eliminarItemForm(index: number): void {
    this.formNueva.items.splice(index, 1);
    this.recalcularTotalesForm();
  }

  onMaterialSeleccionado(item: FormItem): void {
    if (!item.id_material) return;
    const mat = this.materiales.find(m => m.id_material === Number(item.id_material));
    if (mat) {
      item.codigo = mat.codigo;
      item.nombre_material = mat.nombre_material;
      item.unidad_medida = mat.unidad_medida?.abreviatura || 'u';
      item.precio_unitario = mat.precio || 0;
      this.calcularSubtotalItem(item);
    }
  }

  calcularSubtotalItem(item: FormItem): void {
    const cant = Number(item.cantidad_solicitada) || 0;
    const precio = Number(item.precio_unitario) || 0;
    item.subtotal = Math.round(cant * precio * 100) / 100;
  }

  get totalFormNueva(): number {
    return this.formNueva.items.reduce((acc, it) => acc + (it.subtotal || 0), 0);
  }

  recalcularTotalesForm(): void {
    this.formNueva.items.forEach(it => this.calcularSubtotalItem(it));
  }

  guardarOrden(): void {
    if (this.esVistaGlobal() && !this.formNueva.id_empresa) {
      this.mostrarError('Debe seleccionar la empresa para la orden de compra.');
      return;
    }
    if (!this.formNueva.id_proveedor) {
      this.mostrarError('Debe seleccionar un proveedor.');
      return;
    }
    if (!this.formNueva.items.length) {
      this.mostrarError('Debe agregar al menos un material a la orden.');
      return;
    }

    const itemsValidos = this.formNueva.items.filter(it => it.id_material && it.cantidad_solicitada > 0);
    if (itemsValidos.length !== this.formNueva.items.length) {
      this.mostrarError('Complete todos los materiales y cantidades antes de guardar.');
      return;
    }

    const idEmpresa = this.formNueva.id_empresa || this.auth.obtenerIdEmpresaActiva();
    const primerMat = this.materiales.find(m => m.id_material === Number(itemsValidos[0].id_material));
    const idEmpresaFinal = idEmpresa || primerMat?.id_empresa;

    this.guardando = true;
    const payload = {
      id_empresa: idEmpresaFinal ? Number(idEmpresaFinal) : undefined,
      id_proveedor: Number(this.formNueva.id_proveedor),
      fecha: this.formNueva.fecha,
      observaciones: this.formNueva.observaciones.trim() || undefined,
      enviar_aprobacion: this.formNueva.enviar_aprobacion,
      detalles: itemsValidos.map(it => ({
        id_material: Number(it.id_material),
        cantidad_solicitada: Number(it.cantidad_solicitada),
        precio_unitario: Number(it.precio_unitario) || 0
      }))
    };

    this.comprasSvc.crear(payload).subscribe({
      next: res => {
        this.guardando = false;
        this.cerrarModales();
        this.mostrarExito(res.message || 'Orden de compra registrada exitosamente.');
        this.cargarOrdenes();
      },
      error: err => {
        this.guardando = false;
        this.mostrarError(this.extraerError(err, 'Error al registrar orden de compra.'));
      }
    });
  }

  // ── Detalle de Orden ───────────────────────────────────────────────────────
  verDetalle(orden: OrdenCompra): void {
    this.comprasSvc.obtener(orden.id_orden_compra).subscribe({
      next: res => {
        this.ordenSeleccionada = res.data;
        this.tabDetalle = 'materiales';
        this.modalActivo = 'detalle';
        this.cdr.detectChanges();
      },
      error: err => {
        this.mostrarError(this.extraerError(err, 'Error al consultar detalle de la orden.'));
      }
    });
  }

  // ── Enviar a aprobación directa desde fila ──────────────────────────────────
  enviarAprobacion(orden: OrdenCompra): void {
    if (orden.estado !== 'BORRADOR') return;
    this.procesandoAccion = true;
    this.comprasSvc.cambiarEstado(orden.id_orden_compra, 'PENDIENTE_APROBACION').subscribe({
      next: res => {
        this.procesandoAccion = false;
        this.mostrarExito(res.message || 'Orden enviada a aprobación.');
        this.cargarOrdenes();
        if (this.ordenSeleccionada?.id_orden_compra === orden.id_orden_compra) {
          this.verDetalle(orden);
        }
      },
      error: err => {
        this.procesandoAccion = false;
        this.mostrarError(this.extraerError(err, 'Error al enviar orden a aprobación.'));
      }
    });
  }

  // ── Modal Aprobación / Rechazo ─────────────────────────────────────────────
  abrirModalAprobacion(orden: OrdenCompra, accion: 'APROBADA' | 'RECHAZADA'): void {
    this.ordenSeleccionada = orden;
    this.accionAprobacion = accion;
    this.observacionAprobacion = '';
    this.modalActivo = 'aprobar_rechazar';
    this.cdr.detectChanges();
  }

  confirmarAprobacionRechazo(): void {
    if (!this.ordenSeleccionada) return;
    if (this.accionAprobacion === 'RECHAZADA' && !this.observacionAprobacion.trim()) {
      this.mostrarError('Debe ingresar un motivo al rechazar la orden de compra.');
      return;
    }

    this.procesandoAccion = true;
    const req$ = this.accionAprobacion === 'APROBADA'
      ? this.comprasSvc.aprobar(this.ordenSeleccionada.id_orden_compra, this.observacionAprobacion.trim() || undefined)
      : this.comprasSvc.rechazar(this.ordenSeleccionada.id_orden_compra, this.observacionAprobacion.trim());

    req$.subscribe({
      next: res => {
        this.procesandoAccion = false;
        this.cerrarModales();
        this.mostrarExito(res.message || `Orden de compra ${this.accionAprobacion.toLowerCase()}.`);
        this.cargarOrdenes();
      },
      error: err => {
        this.procesandoAccion = false;
        this.mostrarError(this.extraerError(err, 'Error al procesar la aprobación/rechazo.'));
      }
    });
  }

  // ── Modal Recepción de Materiales ──────────────────────────────────────────
  abrirModalRecepcion(orden: OrdenCompra): void {
    this.comprasSvc.obtener(orden.id_orden_compra).subscribe({
      next: res => {
        this.ordenSeleccionada = res.data;
        this.observacionesRecepcion = '';
        this.recepcionItems = (this.ordenSeleccionada.detalles || [])
          .filter(d => d.cantidad_pendiente > 0)
          .map(d => ({
            id_material: d.id_material,
            codigo_material: d.codigo_material,
            nombre_material: d.nombre_material,
            unidad_medida: d.unidad_medida,
            cantidad_solicitada: d.cantidad_solicitada,
            cantidad_recibida_previa: d.cantidad_recibida,
            cantidad_pendiente: d.cantidad_pendiente,
            cantidad_a_recibir: d.cantidad_pendiente, // default al saldo pendiente
            precio_unitario: d.precio_unitario
          }));

        if (!this.recepcionItems.length) {
          this.mostrarError('Todos los materiales de esta orden ya han sido recibidos en su totalidad.');
          return;
        }

        this.modalActivo = 'recepcion';
        this.cdr.detectChanges();
      },
      error: err => {
        this.mostrarError(this.extraerError(err, 'Error al preparar recepción de materiales.'));
      }
    });
  }

  confirmarRecepcion(): void {
    if (!this.ordenSeleccionada) return;

    for (const item of this.recepcionItems) {
      if (item.cantidad_a_recibir < 0) {
        this.mostrarError(`La cantidad para ${item.nombre_material} no puede ser negativa.`);
        return;
      }
      if (item.cantidad_a_recibir > item.cantidad_pendiente) {
        this.mostrarError(`La cantidad a recibir de ${item.nombre_material} no puede superar el saldo pendiente (${item.cantidad_pendiente} ${item.unidad_medida}).`);
        return;
      }
    }

    const itemsAEnviar = this.recepcionItems.filter(it => it.cantidad_a_recibir > 0);
    if (!itemsAEnviar.length) {
      this.mostrarError('Ingrese una cantidad mayor a 0 en al menos un material.');
      return;
    }

    this.procesandoAccion = true;
    const payload = {
      observaciones: this.observacionesRecepcion.trim() || undefined,
      detalles: itemsAEnviar.map(it => ({
        id_material: it.id_material,
        cantidad_recibida: Number(it.cantidad_a_recibir),
        precio_unitario: it.precio_unitario
      }))
    };

    this.comprasSvc.registrarRecepcion(this.ordenSeleccionada.id_orden_compra, payload).subscribe({
      next: res => {
        this.procesandoAccion = false;
        this.cerrarModales();
        this.mostrarExito(res.message || 'Recepción confirmada e inventario actualizado.');
        this.cargarOrdenes();
      },
      error: err => {
        this.procesandoAccion = false;
        this.mostrarError(this.extraerError(err, 'Error al registrar recepción de materiales.'));
      }
    });
  }

  // ── Modal Cancelar Orden ───────────────────────────────────────────────────
  abrirModalCancelar(orden: OrdenCompra): void {
    this.ordenSeleccionada = orden;
    this.motivoCancelacion = '';
    this.modalActivo = 'cancelar';
    this.cdr.detectChanges();
  }

  confirmarCancelacion(): void {
    if (!this.ordenSeleccionada) return;
    this.procesandoAccion = true;
    this.comprasSvc.cambiarEstado(
      this.ordenSeleccionada.id_orden_compra,
      'CANCELADA',
      this.motivoCancelacion.trim() || undefined
    ).subscribe({
      next: res => {
        this.procesandoAccion = false;
        this.cerrarModales();
        this.mostrarExito(res.message || 'Orden de compra cancelada.');
        this.cargarOrdenes();
      },
      error: err => {
        this.procesandoAccion = false;
        this.mostrarError(this.extraerError(err, 'Error al cancelar la orden.'));
      }
    });
  }

  cerrarModales(): void {
    this.modalActivo = null;
    this.ordenSeleccionada = undefined;
    this.error = '';
    this.cdr.detectChanges();
  }

  // ── Helpers de visualización ───────────────────────────────────────────────
  badgeClase(estado: EstadoOrdenCompra): string {
    switch (estado) {
      case 'BORRADOR': return 'badge-borrador';
      case 'PENDIENTE_APROBACION': return 'badge-pendiente';
      case 'APROBADA': return 'badge-aprobada';
      case 'RECIBIDA_PARCIAL': return 'badge-parcial';
      case 'RECIBIDA': return 'badge-recibida';
      case 'RECHAZADA': return 'badge-rechazada';
      case 'CANCELADA': return 'badge-cancelada';
      default: return 'badge-default';
    }
  }

  badgeEtiqueta(estado: EstadoOrdenCompra): string {
    switch (estado) {
      case 'BORRADOR': return 'Borrador';
      case 'PENDIENTE_APROBACION': return 'Pendiente Aprobación';
      case 'APROBADA': return 'Aprobada';
      case 'RECIBIDA_PARCIAL': return 'Recibida Parcial';
      case 'RECIBIDA': return 'Recibida Total';
      case 'RECHAZADA': return 'Rechazada';
      case 'CANCELADA': return 'Cancelada';
      default: return estado;
    }
  }

  calcularProgresoOrden(orden: OrdenCompra): number {
    if (!orden.detalles || !orden.detalles.length) return 0;
    const totalSolicitado = orden.detalles.reduce((acc, d) => acc + d.cantidad_solicitada, 0);
    const totalRecibido = orden.detalles.reduce((acc, d) => acc + d.cantidad_recibida, 0);
    if (totalSolicitado === 0) return 0;
    return Math.min(100, Math.round((totalRecibido / totalSolicitado) * 100));
  }

  // ── Mensajería ─────────────────────────────────────────────────────────────
  private extraerError(err: any, fallback: string): string {
    if (err?.status === 401) return 'Sesión expirada. Inicie sesión nuevamente.';
    if (err?.status === 403) return 'No cuenta con los permisos necesarios para esta acción.';
    if (err?.error?.detail) return err.error.detail;
    if (err?.error?.message) return err.error.message;
    return fallback;
  }

  private mostrarError(msg: string): void {
    this.error = msg;
    setTimeout(() => { this.error = ''; this.cdr.detectChanges(); }, 6000);
  }

  private mostrarExito(msg: string): void {
    this.exito = msg;
    setTimeout(() => { this.exito = ''; this.cdr.detectChanges(); }, 4500);
  }
}
