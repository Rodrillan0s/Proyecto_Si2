import { Component, Input, OnInit, inject, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EstructuraService, EstructuraNodo } from '../../../services/estructura';
import { AuthService } from '../../../services/auth';
import {
  UnidadesService, UnidadConstruccion, UnidadAmbiente, UnidadCaracteristica,
  ModeloUnidad, UnidadPersonalizacion, UnidadMaterial, MaterialDisponible
} from '../../../services/unidades';

@Component({
  selector: 'app-proyecto-estructura',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './proyecto-estructura.html',
  styleUrl: './proyecto-estructura.css'
})
export class ProyectoEstructuraComponent implements OnInit {
  @Input() idObra!: number;
  @Input() nombreProyecto?: string;
  @Input() codigoProyecto?: string;

  private estructuraService = inject(EstructuraService);
  private authService = inject(AuthService);
  private unidadesService = inject(UnidadesService);
  private cdr = inject(ChangeDetectorRef);
  private ngZone = inject(NgZone);

  nodosPlanos: EstructuraNodo[] = [];
  arbol: EstructuraNodo[] = [];

  // Modo de visualización: 'arbol' o 'tarjetas'
  vistaModo: 'arbol' | 'tarjetas' = 'arbol';

  // Navegación jerárquica en modo tarjetas (Breadcrumbs)
  rutaNavegacion: EstructuraNodo[] = [];

  // Métricas resumidas de la estructura
  resumenTipos: { tipo: string; cantidad: number }[] = [];

  unidades: UnidadConstruccion[] = [];
  unidadesPorEstructura = new Map<number, UnidadConstruccion>();
  modelos: ModeloUnidad[] = [];
  materialesDisponibles: MaterialDisponible[] = [];
  tiposUnidad = ['VIVIENDA', 'DEPARTAMENTO', 'LOCAL', 'LOTE', 'OFICINA', 'OTRO'];
  estadosUnidad = ['PLANIFICADO', 'EN_CONSTRUCCION', 'FINALIZADO', 'SUSPENDIDO'];

  // Tipos sugeridos para la obra según especificación
  tiposDisponibles: string[] = [
    'Sector',
    'Etapa',
    'Bloque',
    'Torre',
    'Nivel',
    'Lote',
    'Área',
    'Ambiente',
    'Otro'
  ];

  cargando: boolean = false;
  guardando: boolean = false;
  mensajeError: string = '';
  mensajeExito: string = '';

  // Control de Drawer (Panel Lateral) y Modales
  mostrarPanelLateral: boolean = false;
  mostrarModalEliminar: boolean = false;
  mostrarModalDetalle: boolean = false;
  mostrarPanelUnidad: boolean = false;
  mostrarDetalleUnidad: boolean = false;
  mostrarModalModelo: boolean = false;
  modoEdicion: boolean = false;
  menuAbiertoId: number | null = null;

  // Nodo en formulario
  elementoForm: Partial<EstructuraNodo> = {};
  padreSeleccionado: EstructuraNodo | null = null;
  nodoAEliminar: EstructuraNodo | null = null;
  nodoDetalle: EstructuraNodo | null = null;

  unidadForm: Partial<UnidadConstruccion> = this.nuevaUnidadForm();
  unidadDetalle: UnidadConstruccion | null = null;
  editandoUnidad = false;
  editandoModelo = false;
  guardandoModelo = false;
  modeloForm: ModeloUnidad = this.nuevoModeloForm();
  personalizacionForm: UnidadPersonalizacion = { tipo: 'OTRO', descripcion: '' };
  estadoObservacion = '';
  materialForm: UnidadMaterial = { id_material: 0, cantidad: 1 };

  ngOnInit() {
    if (this.idObra) {
      this.cargarEstructura();
      this.cargarUnidades();
      this.cargarModelos();
      this.cargarMaterialesDisponibles();
    }
  }

  private nuevaUnidadForm(): Partial<UnidadConstruccion> {
    return {
      nombre: '', descripcion: '', tipo_unidad: 'VIVIENDA',
      superficie: 0, cantidad_plantas: 0, estado: 'PLANIFICADO',
      id_modelo: null, id_padre: null, ambientes: [], caracteristicas: []
    };
  }

  private nuevoModeloForm(): ModeloUnidad {
    return {
      nombre: '', descripcion: '', tipo_unidad: 'VIVIENDA',
      superficie_base: 0, cantidad_plantas_base: 0, caracteristicas: []
    };
  }

  cargarUnidades() {
    this.unidadesService.listar(this.idObra).subscribe({
      next: res => {
        if (!res?.success) {
          this.mostrarError((res as any)?.error || (res as any)?.message || 'No se pudieron cargar las unidades.');
          return;
        }
        this.unidades = res.data || [];
        this.unidadesPorEstructura = new Map(
          this.unidades.filter(u => u.id_estructura).map(u => [u.id_estructura!, u])
        );
        this.cdr.detectChanges();
      },
      error: err => this.mostrarError(err?.error?.detail || 'No se pudieron cargar las unidades.')
    });
  }

  cargarModelos() {
    this.unidadesService.listarModelos(this.idObra).subscribe({
      next: res => {
        if (!res?.success) {
          this.mostrarError((res as any)?.error || (res as any)?.message || 'No se pudieron cargar los modelos.');
          return;
        }
        this.modelos = res.data || [];
        this.cdr.detectChanges();
      },
      error: err => this.mostrarError(err?.error?.detail || 'No se pudieron cargar los modelos.')
    });
  }

  cargarMaterialesDisponibles() {
    this.unidadesService.listarMateriales(this.idObra).subscribe({
      next: res => {
        if (!res?.success) {
          this.materialesDisponibles = [];
          this.mostrarError((res as any)?.error || (res as any)?.message || 'No se pudieron cargar los materiales.');
          return;
        }
        this.materialesDisponibles = res.data || [];
      },
      error: () => { this.materialesDisponibles = []; }
    });
  }

  esUnidad(nodo: EstructuraNodo): boolean {
    return !!nodo.id_estructura && this.unidadesPorEstructura.has(nodo.id_estructura);
  }

  unidadDeNodo(nodo: EstructuraNodo): UnidadConstruccion | undefined {
    return nodo.id_estructura ? this.unidadesPorEstructura.get(nodo.id_estructura) : undefined;
  }

  puedeAgregarElemento(nodo: EstructuraNodo): boolean {
    return !this.esUnidad(nodo) && this.normalizarTipoEstructura(nodo.tipo) !== 'AMBIENTE';
  }

  puedeAgregarUnidad(nodo: EstructuraNodo): boolean {
    if (this.esUnidad(nodo)) return false;
    return ['NIVEL', 'LOTE', 'AREA', 'OTRO'].includes(
      this.normalizarTipoEstructura(nodo.tipo)
    );
  }

  puedeConvertirEnUnidad(nodo: EstructuraNodo): boolean {
    return !this.esUnidad(nodo)
      && this.normalizarTipoEstructura(nodo.tipo) !== 'AMBIENTE'
      && (!nodo.hijos || nodo.hijos.length === 0);
  }

  private normalizarTipoEstructura(tipo?: string): string {
    return (tipo || '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .trim()
      .toUpperCase();
  }

  get convirtiendoNodo(): boolean {
    return !this.editandoUnidad && !!this.unidadForm.id_estructura;
  }

  cargarEstructura() {
    this.cargando = true;
    this.mensajeError = '';

    this.estructuraService.listarEstructura(this.idObra).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res && res.success) {
            this.nodosPlanos = res.data || [];
            
            // Reconstruir árbol manteniendo los estados de expansión si existían
            const expandidosPrevios = new Set(
              this.obtenerIdsExpandidos(this.arbol)
            );
            this.arbol = this.construirArbolConEstados(res.data || [], expandidosPrevios);

            // Calcular métricas resumidas
            this.calcularResumen();

            // Sincronizar breadcrumb si estaba en modo tarjetas
            this.sincronizarRutaNavegacion();
          } else {
            this.mostrarError(res.message || 'Error al cargar la estructura de la obra.');
          }
          this.cargando = false;
          this.cdr.detectChanges();
        });
      },
      error: (err) => {
        this.ngZone.run(() => {
          this.mostrarError(err?.error?.detail || 'Error de conexión al cargar la estructura.');
          this.cargando = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  private calcularResumen() {
    const conteo: { [tipo: string]: number } = {};
    for (const nodo of this.nodosPlanos) {
      conteo[nodo.tipo] = (conteo[nodo.tipo] || 0) + 1;
    }

    this.resumenTipos = Object.entries(conteo)
      .map(([tipo, cantidad]) => ({ tipo, cantidad }))
      .sort((a, b) => b.cantidad - a.cantidad);
  }

  private sincronizarRutaNavegacion() {
    if (this.rutaNavegacion.length === 0) return;

    const nuevaRuta: EstructuraNodo[] = [];
    for (const item of this.rutaNavegacion) {
      const actualizado = this.nodosPlanos.find(n => n.id_estructura === item.id_estructura);
      if (actualizado) {
        nuevaRuta.push(actualizado);
      } else {
        break;
      }
    }
    this.rutaNavegacion = nuevaRuta;
  }

  // --- NAVEGACIÓN EN MODO TARJETAS ---
  get nodosNivelActual(): EstructuraNodo[] {
    if (this.rutaNavegacion.length === 0) {
      return this.arbol;
    }
    const actualId = this.rutaNavegacion[this.rutaNavegacion.length - 1].id_estructura;
    const actual = this.buscarNodoEnArbol(this.arbol, actualId!);
    return actual && actual.hijos ? actual.hijos : [];
  }

  get nodoActual(): EstructuraNodo | null {
    if (this.rutaNavegacion.length === 0) return null;
    return this.rutaNavegacion[this.rutaNavegacion.length - 1];
  }

  entrarNivel(nodo: EstructuraNodo) {
    this.rutaNavegacion.push(nodo);
  }

  subirNivel() {
    if (this.rutaNavegacion.length > 0) {
      this.rutaNavegacion.pop();
    }
  }

  irANivel(indice: number) {
    if (indice === -1) {
      this.rutaNavegacion = [];
    } else {
      this.rutaNavegacion = this.rutaNavegacion.slice(0, indice + 1);
    }
  }

  private buscarNodoEnArbol(nodos: EstructuraNodo[], id: number): EstructuraNodo | null {
    for (const n of nodos) {
      if (n.id_estructura === id) return n;
      if (n.hijos && n.hijos.length > 0) {
        const encontrado = this.buscarNodoEnArbol(n.hijos, id);
        if (encontrado) return encontrado;
      }
    }
    return null;
  }

  // --- NAVEGACIÓN EN MODO ÁRBOL ---
  private obtenerIdsExpandidos(nodos: EstructuraNodo[]): number[] {
    let ids: number[] = [];
    for (const n of nodos) {
      if (n.expandido && n.id_estructura) {
        ids.push(n.id_estructura);
      }
      if (n.hijos && n.hijos.length > 0) {
        ids = ids.concat(this.obtenerIdsExpandidos(n.hijos));
      }
    }
    return ids;
  }

  private construirArbolConEstados(nodos: EstructuraNodo[], expandidosPrevios: Set<number>): EstructuraNodo[] {
    const mapa: { [key: number]: EstructuraNodo } = {};
    const arbol: EstructuraNodo[] = [];

    for (const nodo of nodos) {
      if (nodo.id_estructura) {
        mapa[nodo.id_estructura] = {
          ...nodo,
          hijos: [],
          expandido: expandidosPrevios.size > 0 
            ? expandidosPrevios.has(nodo.id_estructura) 
            : true
        };
      }
    }

    for (const nodo of nodos) {
      if (!nodo.id_estructura) continue;
      const actual = mapa[nodo.id_estructura];
      if (nodo.id_padre && mapa[nodo.id_padre]) {
        mapa[nodo.id_padre].hijos!.push(actual);
      } else {
        arbol.push(actual);
      }
    }

    return arbol;
  }

  toggleExpandir(nodo: EstructuraNodo) {
    nodo.expandido = !nodo.expandido;
  }

  expandirTodo() {
    this.recorrerArbol(this.arbol, (n) => n.expandido = true);
  }

  contraerTodo() {
    this.recorrerArbol(this.arbol, (n) => n.expandido = false);
  }

  private recorrerArbol(nodos: EstructuraNodo[], accion: (n: EstructuraNodo) => void) {
    for (const n of nodos) {
      accion(n);
      if (n.hijos && n.hijos.length > 0) {
        this.recorrerArbol(n.hijos, accion);
      }
    }
  }

  // --- CONTROL DE MENÚ CONTEXTUAL ⋮ ---
  toggleMenu(id: number, event: Event) {
    event.stopPropagation();
    this.menuAbiertoId = this.menuAbiertoId === id ? null : id;
  }

  cerrarMenu() {
    this.menuAbiertoId = null;
  }

  // --- CREAR Y EDITAR (DRAWER LATERAL) ---
  abrirModalNuevo(padre?: EstructuraNodo) {
    if (padre && !this.puedeAgregarElemento(padre)) {
      this.mostrarError('Este nodo es una hoja y no permite agregar elementos dentro.');
      this.cerrarMenu();
      return;
    }
    this.modoEdicion = false;
    this.padreSeleccionado = padre || null;
    this.elementoForm = {
      id_obra: this.idObra,
      id_padre: padre ? padre.id_estructura : null,
      nombre: '',
      tipo: padre ? this.sugerirTipoHijo(padre.tipo) : 'Sector',
      descripcion: ''
    };
    this.mostrarPanelLateral = true;
    this.cerrarMenu();
  }

  sugerirTipoHijo(tipoPadre: string): string {
    switch (tipoPadre) {
      case 'Torre': return 'Nivel';
      case 'Bloque': return 'Nivel';
      case 'Nivel': return 'Ambiente';
      case 'Área': return 'Ambiente';
      case 'Etapa': return 'Sector';
      case 'Sector': return 'Bloque';
      default: return 'Sector';
    }
  }

  abrirModalEditar(nodo: EstructuraNodo) {
    this.modoEdicion = true;
    this.padreSeleccionado = nodo.id_padre 
      ? (this.nodosPlanos.find(n => n.id_estructura === nodo.id_padre) || null) 
      : null;
    this.elementoForm = {
      id_estructura: nodo.id_estructura,
      id_obra: nodo.id_obra,
      id_padre: nodo.id_padre,
      nombre: nodo.nombre,
      tipo: nodo.tipo,
      descripcion: nodo.descripcion,
      orden: nodo.orden
    };
    this.mostrarPanelLateral = true;
    this.cerrarMenu();
  }

  cerrarPanelLateral() {
    this.mostrarPanelLateral = false;
    this.elementoForm = {};
    this.padreSeleccionado = null;
    this.guardando = false;
  }

  guardarElemento() {
    const nombre = (this.elementoForm.nombre || '').trim();
    if (!nombre) {
      this.mostrarError('El nombre del elemento es obligatorio.');
      return;
    }

    this.guardando = true;

    if (this.modoEdicion && this.elementoForm.id_estructura) {
      this.estructuraService.actualizarElemento(this.idObra, this.elementoForm.id_estructura, this.elementoForm).subscribe({
        next: (res) => {
          this.ngZone.run(() => {
            this.guardando = false;
            if (res.success) {
              this.cerrarPanelLateral();
              this.mostrarExito('Elemento actualizado correctamente.');
              this.cargarEstructura();
            } else {
              this.mostrarError(res.message || 'Error al actualizar el elemento.');
            }
          });
        },
        error: (err) => {
          this.ngZone.run(() => {
            this.guardando = false;
            this.mostrarError(err?.error?.detail || 'Error al actualizar el elemento.');
          });
        }
      });
    } else {
      this.estructuraService.crearElemento(this.idObra, this.elementoForm).subscribe({
        next: (res) => {
          this.ngZone.run(() => {
            this.guardando = false;
            if (res.success) {
              this.cerrarPanelLateral();
              this.mostrarExito('Elemento agregado exitosamente.');
              this.cargarEstructura();
            } else {
              this.mostrarError(res.message || 'Error al crear el elemento.');
            }
          });
        },
        error: (err) => {
          this.ngZone.run(() => {
            this.guardando = false;
            this.mostrarError(err?.error?.detail || 'Error al crear el elemento.');
          });
        }
      });
    }
  }

  // --- VER DETALLES ---
  verDetalles(nodo: EstructuraNodo) {
    this.nodoDetalle = nodo;
    this.mostrarModalDetalle = true;
    this.cerrarMenu();
  }

  cerrarModalDetalle() {
    this.mostrarModalDetalle = false;
    this.nodoDetalle = null;
  }

  // --- ELIMINACIÓN RESPONSABLE ---
  confirmarEliminar(nodo: EstructuraNodo) {
    this.nodoAEliminar = nodo;
    this.mostrarModalEliminar = true;
    this.cerrarMenu();
  }

  cerrarModalEliminar() {
    this.mostrarModalEliminar = false;
    this.nodoAEliminar = null;
  }

  contarDescendientes(nodo: EstructuraNodo): number {
    if (!nodo.hijos || nodo.hijos.length === 0) return 0;
    let total = nodo.hijos.length;
    for (const h of nodo.hijos) {
      total += this.contarDescendientes(h);
    }
    return total;
  }

  ejecutarEliminacion() {
    if (!this.nodoAEliminar || !this.nodoAEliminar.id_estructura) return;

    if (this.esUnidad(this.nodoAEliminar)) {
      this.ejecutarEliminacionUnidad(this.nodoAEliminar);
      return;
    }

    this.guardando = true;
    this.estructuraService.eliminarElemento(this.idObra, this.nodoAEliminar.id_estructura).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          this.guardando = false;
          if (res.success) {
            this.cerrarModalEliminar();
            this.mostrarExito('Elemento eliminado exitosamente.');
            this.cargarEstructura();
          } else {
            this.mostrarError(res.message || 'Error al eliminar el elemento.');
          }
        });
      },
      error: (err) => {
        this.ngZone.run(() => {
          this.guardando = false;
          this.mostrarError(err?.error?.detail || 'Error al eliminar el elemento.');
        });
      }
    });
  }

  reordenar(nodo: EstructuraNodo, direccion: 'UP' | 'DOWN') {
    if (!nodo.id_estructura) return;

    this.estructuraService.reordenarElemento(this.idObra, nodo.id_estructura, direccion).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res.success) {
            this.cargarEstructura();
          } else {
            this.mostrarError(res.message || 'No se pudo reordenar el elemento.');
          }
        });
      },
      error: (err) => {
        this.ngZone.run(() => {
          this.mostrarError(err?.error?.detail || 'Error al reordenar el elemento.');
        });
      }
    });
  }

  // --- CU12: UNIDADES DE CONSTRUCCIÓN ---
  abrirUnidadNueva(padre?: EstructuraNodo) {
    if (!padre || !this.puedeAgregarUnidad(padre)) {
      this.mostrarError('Este tipo de nodo no permite agregar unidades dentro.');
      this.cerrarMenu();
      return;
    }
    this.editandoUnidad = false;
    this.unidadForm = this.nuevaUnidadForm();
    this.unidadForm.id_padre = padre?.id_estructura || null;
    this.mostrarPanelUnidad = true;
    this.cerrarMenu();
  }

  convertirNodoEnUnidad(nodo: EstructuraNodo) {
    if (this.esUnidad(nodo)) {
      this.verUnidad(nodo);
      return;
    }
    if (!this.puedeConvertirEnUnidad(nodo)) {
      this.mostrarError('Solo se puede convertir en unidad un nodo sin elementos dentro y que no sea Ambiente.');
      this.cerrarMenu();
      return;
    }
    this.editandoUnidad = false;
    this.unidadForm = {
      ...this.nuevaUnidadForm(), id_estructura: nodo.id_estructura,
      id_padre: nodo.id_padre, nombre: nodo.nombre, descripcion: nodo.descripcion || ''
    };
    this.mostrarPanelUnidad = true;
    this.cerrarMenu();
  }

  editarUnidad() {
    if (!this.unidadDetalle) return;
    this.editandoUnidad = true;
    this.unidadForm = {
      ...this.unidadDetalle,
      ambientes: (this.unidadDetalle.ambientes || []).map(a => ({ ...a })),
      caracteristicas: (this.unidadDetalle.caracteristicas || []).map(c => ({ ...c }))
    };
    this.mostrarDetalleUnidad = false;
    this.mostrarPanelUnidad = true;
  }

  cerrarPanelUnidad() {
    this.mostrarPanelUnidad = false;
    this.editandoUnidad = false;
    this.guardando = false;
    this.unidadForm = this.nuevaUnidadForm();
  }

  agregarAmbiente() {
    this.unidadForm.ambientes = [...(this.unidadForm.ambientes || []), { nombre: '', cantidad: 1 }];
  }

  quitarAmbiente(indice: number) {
    this.unidadForm.ambientes = (this.unidadForm.ambientes || []).filter((_, i) => i !== indice);
  }

  agregarCaracteristica() {
    this.unidadForm.caracteristicas = [...(this.unidadForm.caracteristicas || []), { nombre: '', valor: '' }];
  }

  quitarCaracteristica(indice: number) {
    this.unidadForm.caracteristicas = (this.unidadForm.caracteristicas || []).filter((_, i) => i !== indice);
  }

  aplicarModelo() {
    const modelo = this.modelos.find(m => m.id_modelo === Number(this.unidadForm.id_modelo));
    if (!modelo) return;
    this.unidadForm.tipo_unidad = modelo.tipo_unidad;
    this.unidadForm.superficie = modelo.superficie_base ?? 0;
    this.unidadForm.cantidad_plantas = modelo.cantidad_plantas_base ?? 0;
    this.unidadForm.caracteristicas = (modelo.caracteristicas || []).map(c => ({ ...c }));
  }

  guardarUnidad() {
    const nombre = (this.unidadForm.nombre || '').trim();
    if (!nombre) { this.mostrarError('El nombre de la unidad es obligatorio.'); return; }
    if ((this.unidadForm.superficie ?? 0) < 0) { this.mostrarError('La superficie no puede ser negativa.'); return; }
    if ((this.unidadForm.cantidad_plantas ?? 0) < 0) { this.mostrarError('La cantidad de plantas no puede ser negativa.'); return; }
    for (const ambiente of this.unidadForm.ambientes || []) {
      if (!ambiente.nombre.trim() || ambiente.cantidad <= 0) {
        this.mostrarError('Cada ambiente debe tener nombre y una cantidad mayor que cero.'); return;
      }
    }
    for (const caracteristica of this.unidadForm.caracteristicas || []) {
      if (!caracteristica.nombre.trim() || !caracteristica.valor.trim()) {
        this.mostrarError('Cada característica debe tener nombre y valor.'); return;
      }
    }
    this.guardando = true;
    const request = this.editandoUnidad && this.unidadForm.id_unidad
      ? this.unidadesService.actualizar(this.idObra, this.unidadForm.id_unidad, this.unidadForm)
      : this.unidadesService.crear(this.idObra, {
          ...this.unidadForm,
          tipo_estructura: this.unidadForm.tipo_unidad === 'OTRO'
            ? 'Unidad' : this.formatearEtiqueta(this.unidadForm.tipo_unidad || 'Unidad')
        } as any);
    const eraEdicion = this.editandoUnidad;
    request.subscribe({
      next: res => {
        this.guardando = false;
        if (res.success) {
          this.cerrarPanelUnidad();
          this.mostrarExito(eraEdicion ? 'Unidad actualizada.' : 'Unidad registrada exitosamente.');
          this.cargarEstructura();
          this.cargarUnidades();
        } else this.mostrarError(res.error || res.message || 'No se pudo guardar la unidad.');
      },
      error: err => { this.guardando = false; this.mostrarError(err?.error?.detail || 'No se pudo guardar la unidad.'); }
    });
  }

  verUnidad(nodo: EstructuraNodo) {
    const resumen = this.unidadDeNodo(nodo);
    if (!resumen?.id_unidad) return;
    this.unidadesService.obtener(this.idObra, resumen.id_unidad).subscribe({
      next: res => {
        if (!res?.success) {
          this.mostrarError(res?.error || res?.message || 'No se pudo consultar la unidad.');
          return;
        }
        this.unidadDetalle = res.data;
        this.mostrarDetalleUnidad = true;
        this.cerrarMenu();
        this.cdr.detectChanges();
      },
      error: err => this.mostrarError(err?.error?.detail || 'No se pudo consultar la unidad.')
    });
  }

  cerrarDetalleUnidad() {
    this.mostrarDetalleUnidad = false;
    this.unidadDetalle = null;
    this.personalizacionForm = { tipo: 'OTRO', descripcion: '' };
    this.estadoObservacion = '';
    this.materialForm = { id_material: 0, cantidad: 1 };
  }

  cambiarEstadoUnidad(estado: string) {
    if (!this.unidadDetalle?.id_unidad) return;
    this.unidadesService.cambiarEstado(
      this.idObra, this.unidadDetalle.id_unidad, estado, this.estadoObservacion
    ).subscribe({
      next: res => {
        if (!res?.success) {
          this.mostrarError(res?.error || res?.message || 'No se pudo actualizar el estado.');
          return;
        }
        this.mostrarExito('Estado actualizado.');
        this.recargarDetalleUnidad();
        this.cargarUnidades();
      },
      error: err => this.mostrarError(err?.error?.detail || 'No se pudo actualizar el estado.')
    });
  }

  agregarPersonalizacion() {
    if (!this.unidadDetalle?.id_unidad || !this.personalizacionForm.descripcion.trim()) return;
    this.unidadesService.agregarPersonalizacion(
      this.idObra, this.unidadDetalle.id_unidad, this.personalizacionForm
    ).subscribe({
      next: res => {
        if (!res?.success) {
          this.mostrarError(res?.error || res?.message || 'No se pudo registrar la personalización.');
          return;
        }
        this.personalizacionForm = { tipo: 'OTRO', descripcion: '' };
        this.mostrarExito('Personalización registrada.'); this.recargarDetalleUnidad();
      },
      error: err => this.mostrarError(err?.error?.detail || 'No se pudo registrar la personalización.')
    });
  }

  eliminarPersonalizacion(id?: number) {
    if (!id || !this.unidadDetalle?.id_unidad) return;
    this.unidadesService.eliminarPersonalizacion(this.idObra, this.unidadDetalle.id_unidad, id).subscribe({
      next: res => {
        if (!res?.success) {
          this.mostrarError(res?.error || res?.message || 'No se pudo eliminar la personalización.');
          return;
        }
        this.mostrarExito('Personalización eliminada.');
        this.recargarDetalleUnidad();
      },
      error: err => this.mostrarError(err?.error?.detail || 'No se pudo eliminar la personalización.')
    });
  }

  private recargarDetalleUnidad() {
    if (!this.unidadDetalle?.id_unidad) return;
    this.unidadesService.obtener(this.idObra, this.unidadDetalle.id_unidad).subscribe({
      next: res => {
        if (!res?.success) {
          this.mostrarError((res as any)?.error || (res as any)?.message || 'No se pudo recargar la unidad.');
          return;
        }
        this.unidadDetalle = res.data;
        this.cdr.detectChanges();
      },
      error: err => this.mostrarError(err?.error?.detail || 'No se pudo recargar la unidad.')
    });
  }

  abrirNuevoModelo() {
    this.editandoModelo = false;
    this.modeloForm = this.nuevoModeloForm();
    this.mostrarModalModelo = true;
  }

  editarModeloSeleccionado() {
    const modelo = this.modelos.find(item => item.id_modelo === Number(this.unidadForm.id_modelo));
    if (!modelo) {
      this.mostrarError('Seleccione un modelo para editar.');
      return;
    }
    this.editandoModelo = true;
    this.modeloForm = {
      ...modelo,
      caracteristicas: (modelo.caracteristicas || []).map(caracteristica => ({ ...caracteristica }))
    };
    this.mostrarModalModelo = true;
  }

  cerrarModalModelo() {
    this.mostrarModalModelo = false;
    this.editandoModelo = false;
    this.guardandoModelo = false;
    this.modeloForm = this.nuevoModeloForm();
  }

  agregarCaracteristicaModelo() {
    this.modeloForm.caracteristicas = [...(this.modeloForm.caracteristicas || []), { nombre: '', valor: '' }];
  }

  quitarCaracteristicaModelo(indice: number) {
    this.modeloForm.caracteristicas = (this.modeloForm.caracteristicas || []).filter((_, i) => i !== indice);
  }

  guardarModelo() {
    if (!this.modeloForm.nombre.trim()) { this.mostrarError('El nombre del modelo es obligatorio.'); return; }
    if (this.guardandoModelo) return;
    this.guardandoModelo = true;
    const idModelo = this.modeloForm.id_modelo;
    const request = this.editandoModelo && idModelo
      ? this.unidadesService.actualizarModelo(this.idObra, idModelo, this.modeloForm)
      : this.unidadesService.crearModelo(this.idObra, this.modeloForm);
    request.subscribe({
      next: res => {
        this.guardandoModelo = false;
        if (!res?.success) {
          this.mostrarError(res?.error || res?.message || 'No se pudo guardar el modelo.');
          return;
        }
        this.mostrarModalModelo = false;
        this.cargarModelos();
        this.unidadForm.id_modelo = res.id_modelo || idModelo || null;
        this.mostrarExito(this.editandoModelo ? 'Modelo actualizado exitosamente.' : 'Modelo creado exitosamente.');
        this.editandoModelo = false;
      },
      error: err => {
        this.guardandoModelo = false;
        this.mostrarError(err?.error?.detail || 'No se pudo guardar el modelo.');
      }
    });
  }

  private ejecutarEliminacionUnidad(nodo: EstructuraNodo) {
    const unidad = this.unidadDeNodo(nodo);
    if (!unidad?.id_unidad) {
      this.mostrarError('No se pudo identificar la unidad que se desea eliminar.');
      return;
    }

    this.guardando = true;
    this.unidadesService.eliminar(this.idObra, unidad.id_unidad).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          this.guardando = false;
          if (res.success) {
            this.cerrarModalEliminar();
            this.cerrarDetalleUnidad();
            this.mostrarExito('Unidad eliminada exitosamente.');
            this.cargarUnidades();
            this.cargarEstructura();
          } else {
            this.mostrarError(res.error || res.message || 'No se pudo eliminar la unidad.');
          }
        });
      },
      error: (err) => {
        this.ngZone.run(() => {
          this.guardando = false;
          this.mostrarError(err?.error?.detail || 'No se pudo eliminar la unidad.');
        });
      }
    });
  }

  agregarMaterialUnidad() {
    if (!this.unidadDetalle || !this.materialForm.id_material || this.materialForm.cantidad <= 0) return;
    const materiales = [...(this.unidadDetalle.materiales || []), { ...this.materialForm }];
    this.guardarMateriales(materiales);
  }

  quitarMaterialUnidad(indice: number) {
    if (!this.unidadDetalle) return;
    this.guardarMateriales((this.unidadDetalle.materiales || []).filter((_, i) => i !== indice));
  }

  private guardarMateriales(materiales: UnidadMaterial[]) {
    if (!this.unidadDetalle?.id_unidad) return;
    const payload = materiales.map(({ id_material, cantidad, unidad_medida, uso_ubicacion, acabado, observacion }) =>
      ({ id_material, cantidad, unidad_medida, uso_ubicacion, acabado, observacion }));
    this.unidadesService.guardarMateriales(this.idObra, this.unidadDetalle.id_unidad, payload).subscribe({
      next: res => {
        if (!res?.success) {
          this.mostrarError(res?.error || res?.message || 'No se pudieron asociar los materiales.');
          return;
        }
        this.materialForm = { id_material: 0, cantidad: 1 };
        this.mostrarExito('Materiales actualizados.');
        this.recargarDetalleUnidad();
      },
      error: err => this.mostrarError(err?.error?.detail || 'No se pudieron asociar los materiales.')
    });
  }

  formatearEtiqueta(valor: string): string {
    return valor.toLowerCase().replace(/_/g, ' ').replace(/\b\w/g, letra => letra.toUpperCase());
  }

  esRolAutorizado(): boolean {
    const rol = this.authService.obtenerUsuario()?.nombre_rol;
    return rol === 'ADMINISTRADOR' || rol === 'ADMINISTRADOR_EMPRESA' || rol === 'JEFE DE OBRA';
  }

  mostrarError(msg: string) {
    this.mensajeError = msg;
    setTimeout(() => {
      this.mensajeError = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  mostrarExito(msg: string) {
    this.mensajeExito = msg;
    setTimeout(() => {
      this.mensajeExito = '';
      this.cdr.detectChanges();
    }, 4000);
  }
}
