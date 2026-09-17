import { Component, Input, OnInit, OnChanges, SimpleChanges, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs';
import { AuthService } from '../../../services/auth';
import {
  PresupuestosService, Presupuesto, PartidaPresupuesto, Apu, ApuComponente,
  PresupuestoConsolidado, CostoEjecutado, ComparativaPresupuesto
} from '../../../services/presupuestos.service';
import { MaterialsService, UnidadMedida } from '../../../services/materials.service';

@Component({
  selector: 'app-proyecto-presupuesto',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './proyecto-presupuesto.html',
  styleUrl: './proyecto-presupuesto.css'
})
export class ProyectoPresupuestoComponent implements OnInit, OnChanges {
  @Input() idObra: number = 0;
  @Input() nombreProyecto: string = '';
  @Input() codigoProyecto: string = '';

  private service = inject(PresupuestosService);
  private matService = inject(MaterialsService);
  private auth = inject(AuthService);
  private cdr = inject(ChangeDetectorRef);

  // Vistas internas
  vistaActiva: 'partidas' | 'consolidado' | 'comparativa' | 'apus' = 'partidas';

  // Datos
  presupuestos: Presupuesto[] = [];
  presupuestoActivo?: Presupuesto;
  consolidado?: PresupuestoConsolidado;
  comparativa?: ComparativaPresupuesto;
  costosEjecutados: CostoEjecutado[] = [];
  apus: Apu[] = [];
  unidades: UnidadMedida[] = [];

  // Loadings
  cargando: boolean = false;
  guardando: boolean = false;
  error: string = '';
  exito: string = '';

  // Modales
  modalPresupuestoAbierto = false;
  modalPartidaAbierto = false;
  modalApuAbierto = false;
  modalCostoAbierto = false;

  // Formularios
  formPresupuesto: Partial<Presupuesto> = this.formularioPresupuestoVacio();
  formPartida: any = this.formularioPartidaVacio();
  formCosto: any = this.formularioCostoVacio();
  formApu: any = { codigo: '', nombre: '', descripcion: '', id_unidad_medida: 0 };
  formComponenteApu: any = { tipo_recurso: 'MATERIAL', descripcion_recurso: '', id_unidad_medida: 0, cantidad: 1, precio_unitario: 0 };
  apuSeleccionadoDetalle?: Apu;

  ngOnInit() {
    this.cargarCatalogos();
    if (this.idObra) {
      this.cargarPresupuestos();
    }
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['idObra'] && !changes['idObra'].isFirstChange() && this.idObra) {
      this.cargarPresupuestos();
    }
  }

  formularioPresupuestoVacio(): Partial<Presupuesto> {
    return {
      codigo: '',
      nombre: 'Presupuesto Base',
      descripcion: '',
      superficie_m2: null,
      tipo_suelo: '',
      costo_m2_estimado: null,
      monto_estimado_inicial: null,
      observaciones: ''
    };
  }

  formularioPartidaVacio(): any {
    return {
      codigo: '',
      nombre: '',
      descripcion: '',
      id_unidad_medida: 0,
      cantidad: 1,
      precio_unitario: 0,
      id_apu: null,
      orden: (this.presupuestoActivo?.partidas?.length || 0) + 1
    };
  }

  formularioCostoVacio(): any {
    return {
      id_partida: null,
      codigo_costo: '',
      descripcion: '',
      tipo_recurso: 'MATERIAL',
      origen_costo: 'REGISTRO_MANUAL',
      id_unidad_medida: null,
      cantidad: 1,
      costo_unitario: 0,
      fecha: new Date().toISOString().slice(0, 10),
      observacion: ''
    };
  }

  cargarCatalogos() {
    this.matService.unidadesMedida().subscribe({
      next: res => { this.unidades = res.data || []; this.cdr.detectChanges(); },
      error: () => {}
    });
  }

  cargarPresupuestos() {
    this.cargando = true;
    this.error = '';
    this.service.listarPresupuestos(this.idObra)
      .pipe(finalize(() => { this.cargando = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: res => {
          this.presupuestos = res.data || [];
          if (this.presupuestos.length > 0) {
            // Seleccionar por defecto el vigente o el más reciente
            const vigente = this.presupuestos.find(p => p.es_vigente);
            this.seleccionarPresupuesto(vigente || this.presupuestos[0]);
          } else {
            this.presupuestoActivo = undefined;
          }
          this.cdr.detectChanges();
        },
        error: err => this.mostrarError(err?.error?.detail || 'Error al cargar los presupuestos de la obra.')
      });
  }

  onCambiarPresupuesto(id: any) {
    const numId = Number(id);
    const encontrado = this.presupuestos.find(p => p.id_presupuesto === numId);
    if (encontrado) {
      this.seleccionarPresupuesto(encontrado);
    }
  }

  seleccionarPresupuesto(p: Presupuesto) {
    this.cargando = true;
    this.service.obtenerPresupuesto(this.idObra, p.id_presupuesto)
      .pipe(finalize(() => { this.cargando = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: res => {
          this.presupuestoActivo = res.data;
          if (this.vistaActiva === 'consolidado') this.cargarConsolidado();
          if (this.vistaActiva === 'comparativa') this.cargarComparativa();
          this.cdr.detectChanges();
        },
        error: err => this.mostrarError(err?.error?.detail || 'No se pudo cargar el detalle del presupuesto.')
      });
  }

  cambiarVista(vista: 'partidas' | 'consolidado' | 'comparativa' | 'apus') {
    this.vistaActiva = vista;
    if (vista === 'consolidado' && this.presupuestoActivo) {
      this.cargarConsolidado();
    } else if (vista === 'comparativa') {
      this.cargarComparativa();
      this.cargarCostosEjecutados();
    } else if (vista === 'apus') {
      this.cargarApus();
    }
  }

  // ─── HU58: CONSOLIDADO Y APROBACIÓN ───
  cargarConsolidado() {
    if (!this.presupuestoActivo) return;
    this.cargando = true;
    this.service.obtenerConsolidado(this.idObra, this.presupuestoActivo.id_presupuesto)
      .pipe(finalize(() => { this.cargando = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: res => {
          this.consolidado = res.data;
          this.cdr.detectChanges();
        },
        error: err => this.mostrarError(err?.error?.detail || 'Error al obtener el presupuesto consolidado.')
      });
  }

  aprobarLineaBase() {
    if (!this.presupuestoActivo || this.guardando) return;
    if (!confirm(`¿Confirma que desea aprobar la versión ${this.presupuestoActivo.version} como Línea Base Vigente? Esto congelará el presupuesto y no permitirá modificaciones directas a sus partidas.`)) {
      return;
    }
    this.guardando = true;
    this.service.aprobarLineaBase(this.idObra, this.presupuestoActivo.id_presupuesto)
      .pipe(finalize(() => { this.guardando = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: res => {
          this.mostrarExito(res.message || 'Presupuesto aprobado como Línea Base con éxito.');
          this.cargarPresupuestos();
        },
        error: err => this.mostrarError(err?.error?.detail || 'No se pudo aprobar el presupuesto.')
      });
  }

  crearNuevaVersion() {
    if (!this.presupuestoActivo || this.guardando) return;
    const nuevoNombre = prompt('Ingrese el nombre o descripción para la nueva versión:', `${this.presupuestoActivo.nombre} (v${this.presupuestoActivo.version + 1})`);
    if (nuevoNombre === null) return;

    this.guardando = true;
    this.service.versionarPresupuesto(this.idObra, this.presupuestoActivo.id_presupuesto, { nombre: nuevoNombre })
      .pipe(finalize(() => { this.guardando = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: res => {
          this.mostrarExito(res.message || 'Nueva versión creada exitosamente en borrador.');
          this.cargarPresupuestos();
        },
        error: err => this.mostrarError(err?.error?.detail || 'No se pudo crear la nueva versión.')
      });
  }

  // ─── HU54 & HU57: PARTIDAS Y ASOCIACIÓN APU ───
  abrirNuevaPartida() {
    this.formPartida = this.formularioPartidaVacio();
    this.cargarApus();
    this.modalPartidaAbierto = true;
  }

  guardarPartida() {
    if (!this.presupuestoActivo || this.guardando) return;
    if (!this.formPartida.codigo || !this.formPartida.nombre) {
      this.mostrarError('Código y nombre de la partida son obligatorios.');
      return;
    }

    this.guardando = true;
    const payload = {
      codigo: this.formPartida.codigo.trim(),
      nombre: this.formPartida.nombre.trim(),
      descripcion: this.formPartida.descripcion?.trim() || null,
      id_unidad_medida: +this.formPartida.id_unidad_medida || 1,
      cantidad: +this.formPartida.cantidad || 1,
      precio_unitario: +this.formPartida.precio_unitario || 0,
      id_apu: this.formPartida.id_apu ? +this.formPartida.id_apu : null,
      orden: +this.formPartida.orden || 1
    };

    this.service.crearPartida(this.idObra, this.presupuestoActivo.id_presupuesto, payload)
      .pipe(finalize(() => { this.guardando = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: () => {
          this.modalPartidaAbierto = false;
          this.mostrarExito('Partida agregada correctamente.');
          this.seleccionarPresupuesto(this.presupuestoActivo!);
        },
        error: err => this.mostrarError(err?.error?.detail || 'Error al registrar la partida.')
      });
  }

  alSeleccionarApuEnPartida(idApu: any) {
    if (!idApu) return;
    const apu = this.apus.find(a => a.id_apu === +idApu);
    if (apu) {
      this.formPartida.id_unidad_medida = apu.id_unidad_medida;
      this.formPartida.precio_unitario = apu.costo_unitario_total;
    }
  }

  eliminarPartida(partida: PartidaPresupuesto) {
    if (!this.presupuestoActivo || this.guardando) return;
    if (!confirm(`¿Eliminar la partida ${partida.codigo} - ${partida.nombre}?`)) return;

    this.guardando = true;
    this.service.eliminarPartida(this.idObra, this.presupuestoActivo.id_presupuesto, partida.id_partida)
      .pipe(finalize(() => { this.guardando = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: () => {
          this.mostrarExito('Partida eliminada.');
          this.seleccionarPresupuesto(this.presupuestoActivo!);
        },
        error: err => this.mostrarError(err?.error?.detail || 'No se pudo eliminar la partida.')
      });
  }

  // ─── HU55 & HU56: APUS Y RECETAS ───
  cargarApus() {
    this.service.listarApus(this.idObra)
      .subscribe({
        next: res => { this.apus = res.data || []; this.cdr.detectChanges(); },
        error: () => {}
      });
  }

  abrirDetalleApu(apu: Apu) {
    this.service.obtenerApu(apu.id_apu).subscribe({
      next: res => {
        this.apuSeleccionadoDetalle = res.data;
        this.cdr.detectChanges();
      }
    });
  }

  abrirNuevoApu() {
    this.formApu = { codigo: '', nombre: '', descripcion: '', id_unidad_medida: this.unidades[0]?.id_unidad_medida || 1 };
    this.modalApuAbierto = true;
  }

  guardarApu() {
    if (!this.formApu.codigo || !this.formApu.nombre || this.guardando) return;
    this.guardando = true;
    this.service.crearApu({ ...this.formApu, id_obra: this.idObra })
      .pipe(finalize(() => { this.guardando = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: res => {
          this.modalApuAbierto = false;
          this.mostrarExito('APU creado exitosamente.');
          this.cargarApus();
          this.abrirDetalleApu({ ...this.formApu, id_apu: res.id_apu, costo_unitario_total: 0, estado: 'ACTIVO', id_empresa: 0, rendimiento_base: 1 });
        },
        error: err => this.mostrarError(err?.error?.detail || 'No se pudo crear el APU.')
      });
  }

  agregarComponente() {
    if (!this.apuSeleccionadoDetalle || this.guardando) return;
    if (!this.formComponenteApu.descripcion_recurso || !this.formComponenteApu.id_unidad_medida) {
      this.mostrarError('Complete la descripción y unidad del componente.');
      return;
    }
    this.guardando = true;
    this.service.agregarComponenteApu(this.apuSeleccionadoDetalle.id_apu, this.formComponenteApu)
      .pipe(finalize(() => { this.guardando = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: () => {
          this.formComponenteApu = { tipo_recurso: 'MATERIAL', descripcion_recurso: '', id_unidad_medida: 0, cantidad: 1, precio_unitario: 0 };
          this.mostrarExito('Componente incorporado al APU.');
          this.abrirDetalleApu(this.apuSeleccionadoDetalle!);
          this.cargarApus();
        },
        error: err => this.mostrarError(err?.error?.detail || 'Error al agregar componente.')
      });
  }

  eliminarComponente(c: ApuComponente) {
    if (!this.apuSeleccionadoDetalle || this.guardando) return;
    this.guardando = true;
    this.service.eliminarComponenteApu(this.apuSeleccionadoDetalle.id_apu, c.id_componente)
      .pipe(finalize(() => { this.guardando = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: () => {
          this.abrirDetalleApu(this.apuSeleccionadoDetalle!);
          this.cargarApus();
        },
        error: err => this.mostrarError(err?.error?.detail || 'Error al eliminar componente.')
      });
  }

  // ─── HU59 & HU60: COSTOS EJECUTADOS Y COMPARATIVA ───
  cargarComparativa() {
    this.cargando = true;
    this.service.obtenerComparativa(this.idObra, this.presupuestoActivo?.id_presupuesto)
      .pipe(finalize(() => { this.cargando = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: res => {
          this.comparativa = res.data;
          this.cdr.detectChanges();
        },
        error: err => this.mostrarError(err?.error?.detail || 'Error al cargar la comparativa de costos.')
      });
  }

  cargarCostosEjecutados() {
    this.service.listarCostosEjecutados(this.idObra)
      .subscribe({
        next: res => {
          this.costosEjecutados = res.data?.costos || [];
          this.cdr.detectChanges();
        },
        error: () => {}
      });
  }

  abrirNuevoCosto() {
    this.formCosto = this.formularioCostoVacio();
    this.modalCostoAbierto = true;
  }

  guardarCosto() {
    if (!this.formCosto.descripcion || this.guardando) return;
    this.guardando = true;
    this.service.registrarCostoEjecutado(this.idObra, this.formCosto)
      .pipe(finalize(() => { this.guardando = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: () => {
          this.modalCostoAbierto = false;
          this.mostrarExito('Costo ejecutado registrado.');
          this.cargarComparativa();
          this.cargarCostosEjecutados();
        },
        error: err => this.mostrarError(err?.error?.detail || 'Error al registrar costo ejecutado.')
      });
  }

  eliminarCosto(c: CostoEjecutado) {
    if (!confirm(`¿Eliminar el registro de costo '${c.descripcion}'?`)) return;
    this.service.eliminarCostoEjecutado(this.idObra, c.id_costo_ejecutado)
      .subscribe({
        next: () => {
          this.mostrarExito('Costo eliminado.');
          this.cargarComparativa();
          this.cargarCostosEjecutados();
        },
        error: err => this.mostrarError(err?.error?.detail || 'No se pudo eliminar el costo.')
      });
  }

  // Permisos y utilidades
  puedeModificar(): boolean {
    return this.auth.hasPermission('Modificar_presupuesto') && this.presupuestoActivo?.estado !== 'APROBADO' && this.presupuestoActivo?.estado !== 'CERRADO';
  }

  puedeAprobar(): boolean {
    return this.auth.hasPermission('Aprobar_presupuesto') && this.presupuestoActivo?.estado !== 'APROBADO';
  }

  puedeRegistrarCosto(): boolean {
    return this.auth.hasPermission('Registrar_costo_ejecutado') || this.auth.hasPermission('Modificar_presupuesto');
  }

  mostrarError(msg: string) {
    this.error = msg;
    setTimeout(() => this.error = '', 5000);
  }

  mostrarExito(msg: string) {
    this.exito = msg;
    setTimeout(() => this.exito = '', 4500);
  }
}
