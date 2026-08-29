import { Component, Input, OnInit, inject, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EstructuraService, EstructuraNodo } from '../../../services/estructura';
import { AuthService } from '../../../services/auth';

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

  // Tipos sugeridos para la obra según especificación
  tiposDisponibles: string[] = [
    'Sector',
    'Etapa',
    'Bloque',
    'Torre',
    'Nivel',
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
  modoEdicion: boolean = false;
  menuAbiertoId: number | null = null;

  // Nodo en formulario
  elementoForm: Partial<EstructuraNodo> = {};
  padreSeleccionado: EstructuraNodo | null = null;
  nodoAEliminar: EstructuraNodo | null = null;
  nodoDetalle: EstructuraNodo | null = null;

  ngOnInit() {
    if (this.idObra) {
      this.cargarEstructura();
    }
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
