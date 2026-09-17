import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, DestroyRef, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject, debounceTime, distinctUntilChanged } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  Apu,
  ApuComponente,
  ApusService,
  CategoriaApu,
  RecursoEquipo,
  RecursoManoObra,
  RecursoMaterial,
  TipoRecursoApu,
  UnidadMedida
} from '../../services/apus.service';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-apus',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './apus.html',
  styleUrl: './apus.css'
})
export class ApusComponent implements OnInit {
  private apusSvc = inject(ApusService);
  private auth = inject(AuthService);
  private cdr = inject(ChangeDetectorRef);
  private destroyRef = inject(DestroyRef);

  // Navegación principal
  pestanaActiva: 'catalogo_base' | 'mis_apus' = 'catalogo_base';

  // Filtros
  categorias: CategoriaApu[] = [];
  categoriaSeleccionadaId: number | null = null;
  qBusqueda = '';
  soloVigentes = true;
  private busqueda$ = new Subject<string>();

  // Estados de carga
  cargando = false;
  guardando = false;
  mensajeExito = '';
  mensajeError = '';

  // Listados
  apusBase: Apu[] = [];
  misApus: Apu[] = [];

  // Detalle / Editor de APU
  modalDetalleAbierto = false;
  apuSeleccionado: Apu | null = null;
  esModoLectura = false;
  pestanaDetalle: 'materiales' | 'mano_obra' | 'equipos' | 'factores' = 'materiales';

  // Factores editables en hoja de cálculo en vivo
  factores = {
    porcentaje_gastos_generales: 8.0,
    monto_gastos_generales: 0.0,
    porcentaje_utilidad: 15.0,
    monto_utilidad: 0.0,
    porcentaje_impuestos: 3.09,
    monto_impuestos: 0.0,
    costo_materiales: 0.0,
    costo_mano_obra: 0.0,
    costo_equipos: 0.0,
    costo_directo: 0.0,
    precio_unitario: 0.0
  };

  // Modales adicionales
  modalCrearAbierto = false;
  modalCopiarAbierto = false;
  modalComponenteAbierto = false;
  editandoComponente = false;
  componenteSeleccionadoId?: number;
  apuBaseACopiar: Apu | null = null;

  // Formulario Crear APU
  formCrear = {
    nombre: '',
    descripcion: '',
    id_categoria: null as number | null,
    id_unidad_medida: null as number | null,
    rendimiento_base: 1.0,
    porcentaje_gastos_generales: 8.0,
    porcentaje_utilidad: 15.0,
    porcentaje_impuestos: 3.09
  };

  // Formulario Componente
  formComp = {
    tipo_recurso: 'MATERIAL' as TipoRecursoApu,
    id_recurso: null as number | null,
    id_material: null as number | null,
    id_mano_obra: null as number | null,
    id_equipo: null as number | null,
    descripcion_recurso: '',
    id_unidad_medida: null as number | null,
    rendimiento: 1.0,
    precio_unitario: 0.0,
    subtotal: 0.0
  };

  // Catálogos para selectores
  materialesDisponibles: RecursoMaterial[] = [];
  manoObraDisponible: RecursoManoObra[] = [];
  equiposDisponibles: RecursoEquipo[] = [];
  unidadesMedida: UnidadMedida[] = [];

  ngOnInit(): void {
    this.cargarCategorias();
    this.cargarUnidadesMedida();
    this.cargarRecursosEmpresa();
    this.cargarDatosVista();

    // Búsqueda reactiva con debounce
    this.busqueda$.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe(texto => {
      this.qBusqueda = texto;
      this.cargarDatosVista();
    });
  }

  onBuscar(valor: string): void {
    this.busqueda$.next(valor);
  }

  cambiarPestana(pestana: 'catalogo_base' | 'mis_apus'): void {
    this.pestanaActiva = pestana;
    this.cargarDatosVista();
  }

  seleccionarCategoria(idCat: number | null): void {
    this.categoriaSeleccionadaId = idCat;
    this.cargarDatosVista();
  }

  toggleSoloVigentes(): void {
    this.soloVigentes = !this.soloVigentes;
    if (this.pestanaActiva === 'mis_apus') {
      this.cargarMisApus();
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Cargas de Datos
  // ─────────────────────────────────────────────────────────────────────────

  cargarCategorias(): void {
    this.apusSvc.listarCategorias().subscribe({
      next: res => {
        this.categorias = res.data || [];
        this.cdr.markForCheck();
      }
    });
  }

  cargarUnidadesMedida(): void {
    this.apusSvc.recursosUnidadesMedida().subscribe({
      next: res => {
        this.unidadesMedida = res.data || [];
        this.cdr.markForCheck();
      }
    });
  }

  cargarRecursosEmpresa(): void {
    this.apusSvc.recursosMateriales().subscribe({
      next: res => { this.materialesDisponibles = res.data || []; this.cdr.markForCheck(); }
    });
    this.apusSvc.recursosManoObra().subscribe({
      next: res => { this.manoObraDisponible = res.data || []; this.cdr.markForCheck(); }
    });
    this.apusSvc.recursosEquipos().subscribe({
      next: res => { this.equiposDisponibles = res.data || []; this.cdr.markForCheck(); }
    });
  }

  cargarDatosVista(): void {
    if (this.pestanaActiva === 'catalogo_base') {
      this.cargarCatalogoBase();
    } else {
      this.cargarMisApus();
    }
  }

  cargarCatalogoBase(): void {
    this.cargando = true;
    this.apusSvc.listarBase(this.categoriaSeleccionadaId || undefined, this.qBusqueda).subscribe({
      next: res => {
        this.apusBase = res.data || [];
        this.cargando = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.cargando = false;
        this.mostrarError('Error al cargar catálogo base.');
        this.cdr.markForCheck();
      }
    });
  }

  cargarMisApus(): void {
    this.cargando = true;
    this.apusSvc.listarMisApus(
      this.categoriaSeleccionadaId || undefined,
      this.soloVigentes,
      this.qBusqueda
    ).subscribe({
      next: res => {
        this.misApus = res.data || [];
        this.cargando = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.cargando = false;
        this.mostrarError('Error al cargar mis APUs.');
        this.cdr.markForCheck();
      }
    });
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Operaciones Catálogo Base
  // ─────────────────────────────────────────────────────────────────────────

  abrirCopiarApuBase(apu: Apu): void {
    this.apuBaseACopiar = apu;
    this.modalCopiarAbierto = true;
  }

  confirmarCopiarApuBase(): void {
    if (!this.apuBaseACopiar || this.guardando) return;
    this.guardando = true;

    this.apusSvc.copiarBase(this.apuBaseACopiar.id_apu).subscribe({
      next: res => {
        this.guardando = false;
        this.modalCopiarAbierto = false;
        this.mostrarExito(res.message || 'APU copiado a su empresa exitosamente.');
        this.pestanaActiva = 'mis_apus';
        this.cargarMisApus();
        this.cargarCategorias();
        // Abrir inmediatamente el nuevo APU para revisión y parametrización
        if (res.data?.id_apu) {
          this.abrirDetalleApu(res.data.id_apu, false);
        }
      },
      error: err => {
        this.guardando = false;
        this.mostrarError(err.error?.detail || 'Error al copiar APU base.');
        this.cdr.markForCheck();
      }
    });
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Operaciones Mis APUs (Empresa)
  // ─────────────────────────────────────────────────────────────────────────

  abrirCrearModal(): void {
    this.formCrear = {
      nombre: '',
      descripcion: '',
      id_categoria: this.categoriaSeleccionadaId || (this.categorias.length > 0 ? this.categorias[0].id_categoria : null),
      id_unidad_medida: this.unidadesMedida.length > 0 ? this.unidadesMedida[0].id_unidad_medida : null,
      rendimiento_base: 1.0,
      porcentaje_gastos_generales: 8.0,
      porcentaje_utilidad: 15.0,
      porcentaje_impuestos: 3.09
    };
    this.modalCrearAbierto = true;
  }

  guardarNuevoApu(): void {
    if (!this.formCrear.nombre.trim()) {
      this.mostrarError('El nombre del APU es obligatorio.');
      return;
    }
    if (!this.formCrear.id_categoria) {
      this.mostrarError('Seleccione una categoría.');
      return;
    }
    if (!this.formCrear.id_unidad_medida) {
      this.mostrarError('Seleccione una unidad de medida.');
      return;
    }

    this.guardando = true;
    this.apusSvc.crearApu(this.formCrear).subscribe({
      next: res => {
        this.guardando = false;
        this.modalCrearAbierto = false;
        this.mostrarExito('APU creado exitosamente.');
        this.cargarMisApus();
        this.cargarCategorias();
        if (res.data?.id_apu) {
          this.abrirDetalleApu(res.data.id_apu, false);
        }
      },
      error: err => {
        this.guardando = false;
        this.mostrarError(err.error?.detail || 'Error al crear APU.');
        this.cdr.markForCheck();
      }
    });
  }

  abrirDetalleApu(idApu: number, modoLectura = false): void {
    this.cargando = true;
    this.esModoLectura = modoLectura;
    this.pestanaDetalle = 'materiales';

    this.apusSvc.obtenerDetalle(idApu).subscribe({
      next: res => {
        this.apuSeleccionado = res.data;
        this.sincronizarFactores();
        this.cargando = false;
        this.modalDetalleAbierto = true;
        this.cdr.markForCheck();
      },
      error: err => {
        this.cargando = false;
        this.mostrarError(err.error?.detail || 'Error al cargar detalle del APU.');
        this.cdr.markForCheck();
      }
    });
  }

  cerrarModalDetalle(): void {
    this.modalDetalleAbierto = false;
    this.apuSeleccionado = null;
    this.cargarMisApus();
  }

  sincronizarFactores(): void {
    if (!this.apuSeleccionado) return;
    this.factores.porcentaje_gastos_generales = Number(this.apuSeleccionado.porcentaje_gastos_generales || 8.0);
    this.factores.porcentaje_utilidad = Number(this.apuSeleccionado.porcentaje_utilidad || 15.0);
    this.factores.porcentaje_impuestos = Number(this.apuSeleccionado.porcentaje_impuestos || 3.09);
    this.calcularTotalesEnVivo();
  }

  calcularTotalesEnVivo(): void {
    if (!this.apuSeleccionado) return;

    const mat = (this.apuSeleccionado.materiales || []).reduce((acc, c) => acc + Number(c.subtotal || 0), 0);
    const mo = (this.apuSeleccionado.mano_obra || []).reduce((acc, c) => acc + Number(c.subtotal || 0), 0);
    const eq = (this.apuSeleccionado.equipos || []).reduce((acc, c) => acc + Number(c.subtotal || 0), 0);

    const cd = Math.round((mat + mo + eq) * 100) / 100;
    const gg = Math.round(cd * (this.factores.porcentaje_gastos_generales / 100) * 100) / 100;
    const ut = Math.round((cd + gg) * (this.factores.porcentaje_utilidad / 100) * 100) / 100;
    const it = Math.round((cd + gg + ut) * (this.factores.porcentaje_impuestos / 100) * 100) / 100;
    const pu = Math.round((cd + gg + ut + it) * 100) / 100;

    this.factores.costo_materiales = mat;
    this.factores.costo_mano_obra = mo;
    this.factores.costo_equipos = eq;
    this.factores.costo_directo = cd;
    this.factores.monto_gastos_generales = gg;
    this.factores.monto_utilidad = ut;
    this.factores.monto_impuestos = it;
    this.factores.precio_unitario = pu;
  }

  guardarCambiosFactores(): void {
    if (!this.apuSeleccionado || this.guardando) return;
    this.guardando = true;

    const payload = {
      nombre: this.apuSeleccionado.nombre,
      descripcion: this.apuSeleccionado.descripcion,
      id_categoria: this.apuSeleccionado.id_categoria,
      id_unidad_medida: this.apuSeleccionado.id_unidad_medida,
      rendimiento_base: this.apuSeleccionado.rendimiento_base,
      porcentaje_gastos_generales: this.factores.porcentaje_gastos_generales,
      porcentaje_utilidad: this.factores.porcentaje_utilidad,
      porcentaje_impuestos: this.factores.porcentaje_impuestos
    };

    this.apusSvc.actualizarApu(this.apuSeleccionado.id_apu, payload).subscribe({
      next: res => {
        this.guardando = false;
        this.apuSeleccionado = res.data;
        this.sincronizarFactores();
        this.mostrarExito('Factores y datos de APU guardados correctamente.');
        this.cdr.markForCheck();
      },
      error: err => {
        this.guardando = false;
        this.mostrarError(err.error?.detail || 'Error al guardar factores.');
        this.cdr.markForCheck();
      }
    });
  }

  versionarApuActual(): void {
    if (!this.apuSeleccionado || this.guardando) return;
    if (!confirm(`¿Desea generar una nueva versión (v${(this.apuSeleccionado.version || 1) + 1}) de este APU? La versión actual quedará archivada como histórico.`)) {
      return;
    }

    this.guardando = true;
    this.apusSvc.versionarApu(this.apuSeleccionado.id_apu).subscribe({
      next: res => {
        this.guardando = false;
        this.apuSeleccionado = res.data;
        this.sincronizarFactores();
        this.mostrarExito(res.message || 'Nueva versión generada.');
        this.cargarMisApus();
        this.cdr.markForCheck();
      },
      error: err => {
        this.guardando = false;
        this.mostrarError(err.error?.detail || 'Error al versionar APU.');
        this.cdr.markForCheck();
      }
    });
  }

  duplicarApu(apu: Apu): void {
    if (this.guardando) return;
    this.guardando = true;

    this.apusSvc.duplicarApu(apu.id_apu).subscribe({
      next: res => {
        this.guardando = false;
        this.mostrarExito(res.message || 'APU duplicado exitosamente.');
        this.cargarMisApus();
        if (res.data?.id_apu) {
          this.abrirDetalleApu(res.data.id_apu, false);
        }
      },
      error: err => {
        this.guardando = false;
        this.mostrarError(err.error?.detail || 'Error al duplicar APU.');
        this.cdr.markForCheck();
      }
    });
  }

  toggleEstadoApu(apu: Apu, event: Event): void {
    event.stopPropagation();
    const nuevoEstado = apu.estado === 'ACTIVO' ? 'INACTIVO' : 'ACTIVO';
    this.apusSvc.cambiarEstado(apu.id_apu, nuevoEstado).subscribe({
      next: () => {
        apu.estado = nuevoEstado;
        this.mostrarExito(`APU ${nuevoEstado.toLowerCase()} con éxito.`);
        this.cdr.markForCheck();
      },
      error: err => {
        this.mostrarError(err.error?.detail || 'Error al cambiar estado.');
      }
    });
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Gestión de Componentes (Insumos)
  // ─────────────────────────────────────────────────────────────────────────

  abrirAgregarComponente(tipo: TipoRecursoApu): void {
    this.editandoComponente = false;
    this.componenteSeleccionadoId = undefined;

    // Determinar unidad de medida por defecto
    let umDefecto: number | null = null;
    if (tipo === 'MANO_OBRA' || tipo === 'EQUIPO') {
      const umHr = this.unidadesMedida.find(u => u.abreviatura.toLowerCase() === 'hr');
      if (umHr) umDefecto = umHr.id_unidad_medida;
    }

    this.formComp = {
      tipo_recurso: tipo,
      id_recurso: null,
      id_material: null,
      id_mano_obra: null,
      id_equipo: null,
      descripcion_recurso: '',
      id_unidad_medida: umDefecto,
      rendimiento: 1.0,
      precio_unitario: 0.0,
      subtotal: 0.0
    };
    this.modalComponenteAbierto = true;
  }

  abrirEditarComponente(comp: ApuComponente): void {
    this.editandoComponente = true;
    this.componenteSeleccionadoId = comp.id_componente;

    this.formComp = {
      tipo_recurso: comp.tipo_recurso,
      id_recurso: comp.id_recurso || null,
      id_material: comp.id_material || null,
      id_mano_obra: comp.id_mano_obra || null,
      id_equipo: comp.id_equipo || null,
      descripcion_recurso: comp.descripcion_recurso,
      id_unidad_medida: comp.id_unidad_medida,
      rendimiento: comp.rendimiento,
      precio_unitario: comp.precio_unitario,
      subtotal: comp.subtotal
    };
    this.modalComponenteAbierto = true;
  }

  alSeleccionarRecurso(event: Event): void {
    const select = event.target as HTMLSelectElement;
    const id = Number(select.value);
    if (!id) return;

    if (this.formComp.tipo_recurso === 'MATERIAL') {
      const mat = this.materialesDisponibles.find(m => m.id_material === id);
      if (mat) {
        this.formComp.id_material = mat.id_material;
        this.formComp.descripcion_recurso = mat.nombre_material;
        this.formComp.precio_unitario = Number(mat.precio || 0);
        this.formComp.id_unidad_medida = mat.id_unidad_medida;
        this.recalcularSubtotalFormComp();
      }
    } else if (this.formComp.tipo_recurso === 'MANO_OBRA') {
      const mo = this.manoObraDisponible.find(m => m.id_mano_obra === id);
      if (mo) {
        this.formComp.id_mano_obra = mo.id_mano_obra;
        this.formComp.descripcion_recurso = mo.nombre;
        this.formComp.precio_unitario = Number(mo.costo_unitario || 0);
        this.formComp.id_unidad_medida = mo.id_unidad_medida;
        this.recalcularSubtotalFormComp();
      }
    } else if (this.formComp.tipo_recurso === 'EQUIPO') {
      const eq = this.equiposDisponibles.find(e => e.id_equipo === id);
      if (eq) {
        this.formComp.id_equipo = eq.id_equipo;
        this.formComp.descripcion_recurso = eq.nombre;
        this.formComp.precio_unitario = Number(eq.costo_unitario || 0);
        this.formComp.id_unidad_medida = eq.id_unidad_medida;
        this.recalcularSubtotalFormComp();
      }
    }
  }

  recalcularSubtotalFormComp(): void {
    const rend = Number(this.formComp.rendimiento || 0);
    const pu = Number(this.formComp.precio_unitario || 0);
    this.formComp.subtotal = Math.round(rend * pu * 100) / 100;
  }

  guardarComponente(): void {
    if (!this.apuSeleccionado || this.guardando) return;
    if (!this.formComp.descripcion_recurso.trim()) {
      this.mostrarError('La descripción del recurso es obligatoria.');
      return;
    }
    if (!this.formComp.id_unidad_medida) {
      this.mostrarError('Seleccione una unidad de medida para el componente.');
      return;
    }

    this.guardando = true;
    this.recalcularSubtotalFormComp();

    if (this.editandoComponente && this.componenteSeleccionadoId) {
      this.apusSvc.actualizarComponente(this.apuSeleccionado.id_apu, this.componenteSeleccionadoId, this.formComp).subscribe({
        next: res => {
          this.guardando = false;
          this.modalComponenteAbierto = false;
          this.apuSeleccionado = res.apu;
          this.sincronizarFactores();
          this.mostrarExito('Componente actualizado.');
          this.cdr.markForCheck();
        },
        error: err => {
          this.guardando = false;
          this.mostrarError(err.error?.detail || 'Error al actualizar componente.');
          this.cdr.markForCheck();
        }
      });
    } else {
      this.apusSvc.agregarComponente(this.apuSeleccionado.id_apu, this.formComp).subscribe({
        next: res => {
          this.guardando = false;
          this.modalComponenteAbierto = false;
          this.apuSeleccionado = res.apu;
          this.sincronizarFactores();
          this.mostrarExito('Componente agregado al APU.');
          this.cdr.markForCheck();
        },
        error: err => {
          this.guardando = false;
          this.mostrarError(err.error?.detail || 'Error al agregar componente.');
          this.cdr.markForCheck();
        }
      });
    }
  }

  eliminarComponente(comp: ApuComponente): void {
    if (!this.apuSeleccionado || !comp.id_componente || this.guardando) return;
    if (!confirm(`¿Eliminar '${comp.descripcion_recurso}' del APU?`)) return;

    this.guardando = true;
    this.apusSvc.eliminarComponente(this.apuSeleccionado.id_apu, comp.id_componente).subscribe({
      next: res => {
        this.guardando = false;
        this.apuSeleccionado = res.apu;
        this.sincronizarFactores();
        this.mostrarExito('Componente eliminado.');
        this.cdr.markForCheck();
      },
      error: err => {
        this.guardando = false;
        this.mostrarError(err.error?.detail || 'Error al eliminar componente.');
        this.cdr.markForCheck();
      }
    });
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Utilidades UI
  // ─────────────────────────────────────────────────────────────────────────

  private mostrarExito(msg: string): void {
    this.mensajeExito = msg;
    setTimeout(() => { this.mensajeExito = ''; this.cdr.markForCheck(); }, 4000);
  }

  private mostrarError(msg: string): void {
    this.mensajeError = msg;
    setTimeout(() => { this.mensajeError = ''; this.cdr.markForCheck(); }, 5000);
  }
}
