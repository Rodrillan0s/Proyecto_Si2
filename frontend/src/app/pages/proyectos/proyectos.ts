import { Component, OnInit, inject, ChangeDetectorRef, NgZone, PLATFORM_ID, OnDestroy } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ProyectosService, Proyecto, TipoProyecto } from '../../services/proyectos';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-proyectos',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './proyectos.html',
  styleUrl: './proyectos.css'
})
export class ProyectosComponent implements OnInit, OnDestroy {
  private proyectosService = inject(ProyectosService);
  private authService = inject(AuthService);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);
  private ngZone = inject(NgZone);
  private platformId = inject(PLATFORM_ID);

  proyectos: Proyecto[] = [];
  proyectosFiltrados: Proyecto[] = [];
  tiposProyecto: TipoProyecto[] = [];

  // Filtros
  busqueda: string = '';
  filtroEstado: string = '';
  filtroTipo: string = '';

  // Estado del UI
  cargando: boolean = false;
  guardando: boolean = false;
  mensajeError: string = '';
  mensajeExito: string = '';
  mostrarModal: boolean = false;
  modoEdicion: boolean = false;

  // Formulario estructurado según la especificación exacta de HU30
  proyectoForm: Proyecto = this.inicializarFormulario();

  // Leaflet Map
  private mapa: any = null;
  private marcador: any = null;

  // Estadísticas
  totalProyectos = 0;
  proyectosActivos = 0;
  proyectosPlanificacion = 0;

  ngOnInit() {
    this.cargarDatos();
  }

  ngOnDestroy() {
    this.destruirMapa();
  }

  inicializarFormulario(): Proyecto {
    return {
      codigo: '',
      nombre: '',
      id_tipo_obra: 1, // 1: Obras Civiles por defecto
      descripcion: '',
      moneda: 'BOB', // BOB por defecto
      valor_estimado: undefined,
      estado_obra: 'PLANIFICACION',
      fecha_inicio: new Date().toISOString().substring(0, 10),
      fecha_fin: '',
      ubicacion: '',
      zona: '',
      distrito: '',
      uv: '',
      manzana: '',
      latitud: -17.7833,
      longitud: -63.1821
    };
  }

  cargarDatos() {
    this.cargando = true;
    this.mensajeError = '';

    this.proyectosService.listarProyectos().subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res && res.success) {
            this.proyectos = res.data || [];
            this.aplicarFiltros();
            this.calcularEstadisticas();
          } else {
            this.mostrarError('Error al listar proyectos.');
          }
          this.cargando = false;
          this.cdr.detectChanges();
        });
      },
      error: () => {
        this.ngZone.run(() => {
          this.mostrarError('Error de conexión al cargar proyectos.');
          this.cargando = false;
          this.cdr.detectChanges();
        });
      }
    });

    this.proyectosService.obtenerTiposProyecto().subscribe({
      next: (res) => {
        if (res && res.success) {
          this.tiposProyecto = res.data || [];
        }
      }
    });
  }

  aplicarFiltros() {
    const q = this.busqueda.toLowerCase().trim();
    this.proyectosFiltrados = this.proyectos.filter(p => {
      const cumpleBusqueda = !q || 
        (p.nombre && p.nombre.toLowerCase().includes(q)) || 
        (p.codigo && p.codigo.toLowerCase().includes(q)) || 
        (p.ubicacion && p.ubicacion.toLowerCase().includes(q)) ||
        (p.zona && p.zona.toLowerCase().includes(q));
      const cumpleEstado = !this.filtroEstado || p.estado_obra === this.filtroEstado;
      const cumpleTipo = !this.filtroTipo || p.id_tipo_obra === Number(this.filtroTipo);
      return cumpleBusqueda && cumpleEstado && cumpleTipo;
    });
  }

  calcularEstadisticas() {
    this.totalProyectos = this.proyectos.length;
    this.proyectosActivos = this.proyectos.filter(p => p.estado_obra === 'ACTIVO').length;
    this.proyectosPlanificacion = this.proyectos.filter(p => p.estado_obra === 'PLANIFICACION').length;
  }

  verProyecto(id?: number) {
    if (id) {
      this.router.navigate([`/proyectos/${id}`]);
    }
  }

  abrirModalNuevo() {
    this.modoEdicion = false;
    this.proyectoForm = this.inicializarFormulario();
    this.mostrarModal = true;

    // Obtener código con formato PYYYY-MM-NNNN
    this.proyectosService.obtenerSiguienteCodigo().subscribe({
      next: (res) => {
        if (res && res.success) {
          this.proyectoForm.codigo = res.codigo;
          this.cdr.detectChanges();
        }
      }
    });

    // Inicializar Leaflet centrado en Santa Cruz de la Sierra
    this.iniciarMapaConRetraso(-17.7833, -63.1821);
  }

  abrirModalEditar(p: Proyecto, event: Event) {
    event.stopPropagation();
    this.modoEdicion = true;
    this.proyectoForm = { 
      ...p,
      fecha_inicio: p.fecha_inicio ? p.fecha_inicio.substring(0, 10) : '',
      fecha_fin: p.fecha_fin ? p.fecha_fin.substring(0, 10) : ''
    };
    this.mostrarModal = true;

    const lat = this.proyectoForm.latitud ? Number(this.proyectoForm.latitud) : -17.7833;
    const lng = this.proyectoForm.longitud ? Number(this.proyectoForm.longitud) : -63.1821;
    this.iniciarMapaConRetraso(lat, lng);
  }

  cerrarModal() {
    this.destruirMapa();
    this.mostrarModal = false;
    this.guardando = false;
  }

  // --- MAPA INTERACTIVO LEAFLET ---
  private iniciarMapaConRetraso(lat: number, lng: number) {
    setTimeout(async () => {
      await this.inicializarMapaLeaflet(lat, lng);
    }, 250);
  }

  private async inicializarMapaLeaflet(latInicial: number, lngInicial: number) {
    if (!isPlatformBrowser(this.platformId)) return;

    this.destruirMapa();

    try {
      const L = await import('leaflet');

      const contenedor = document.getElementById('mapa-registro-proyecto');
      if (!contenedor) return;

      const iconDefault = L.icon({
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
      });
      L.Marker.prototype.options.icon = iconDefault;

      this.mapa = L.map('mapa-registro-proyecto').setView([latInicial, lngInicial], 13);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(this.mapa);

      this.marcador = L.marker([latInicial, lngInicial], { draggable: true }).addTo(this.mapa);
      this.marcador.bindPopup('Ubicación del Proyecto').openPopup();

      this.actualizarCoordenadas(latInicial, lngInicial);

      this.marcador.on('dragend', (e: any) => {
        const coords = e.target.getLatLng();
        this.actualizarCoordenadas(coords.lat, coords.lng);
      });

      this.mapa.on('click', (e: any) => {
        const coords = e.latlng;
        this.marcador.setLatLng(coords);
        this.actualizarCoordenadas(coords.lat, coords.lng);
      });

      setTimeout(() => {
        this.mapa?.invalidateSize();
      }, 200);

    } catch (err) {
      console.error('Error inicializando Leaflet:', err);
    }
  }

  private actualizarCoordenadas(lat: number, lng: number) {
    this.ngZone.run(() => {
      this.proyectoForm.latitud = Number(lat.toFixed(6));
      this.proyectoForm.longitud = Number(lng.toFixed(6));
      this.cdr.detectChanges();
    });
  }

  private destruirMapa() {
    if (this.mapa) {
      this.mapa.remove();
      this.mapa = null;
      this.marcador = null;
    }
  }

  guardarProyecto() {
    // Validaciones
    if (!this.proyectoForm.id_tipo_obra) {
      this.mostrarError('El tipo de proyecto es obligatorio.');
      return;
    }
    if (!this.proyectoForm.moneda) {
      this.mostrarError('La moneda es obligatoria.');
      return;
    }
    if (!this.proyectoForm.fecha_inicio) {
      this.mostrarError('La fecha de inicio es obligatoria.');
      return;
    }
    if (this.proyectoForm.fecha_fin && this.proyectoForm.fecha_fin < this.proyectoForm.fecha_inicio) {
      this.mostrarError('La fecha fin estimada no puede ser anterior a la fecha de inicio.');
      return;
    }
    if (this.proyectoForm.valor_estimado !== undefined && this.proyectoForm.valor_estimado !== null && this.proyectoForm.valor_estimado < 0) {
      this.mostrarError('El presupuesto inicial no puede ser un número negativo.');
      return;
    }

    // Auto-generar nombre si no existe
    if (!this.proyectoForm.nombre) {
      const tipoObj = this.tiposProyecto.find(t => t.id_tipo_obra === Number(this.proyectoForm.id_tipo_obra));
      const tipoNom = tipoObj?.nombre_obra || 'Proyecto';
      this.proyectoForm.nombre = `${tipoNom} ${this.proyectoForm.codigo}`;
    }

    this.guardando = true;

    if (!this.proyectoForm.fecha_fin) {
      this.proyectoForm.fecha_fin = '';
    }

    if (this.modoEdicion && this.proyectoForm.id_obra) {
      this.proyectosService.actualizarProyecto(this.proyectoForm.id_obra, this.proyectoForm).subscribe({
        next: (res) => {
          this.ngZone.run(() => {
            this.guardando = false;
            if (res.success) {
              this.cerrarModal();
              this.mostrarExito('Proyecto actualizado correctamente.');
              this.cargarDatos();
            } else {
              this.mostrarError(res.message || 'Error al actualizar el proyecto.');
            }
          });
        },
        error: (err) => {
          this.ngZone.run(() => {
            this.guardando = false;
            this.mostrarError(err.error?.detail || 'Error al actualizar el proyecto.');
          });
        }
      });
    } else {
      this.proyectosService.crearProyecto(this.proyectoForm).subscribe({
        next: (res) => {
          this.ngZone.run(() => {
            this.guardando = false;
            if (res.success) {
              this.cerrarModal();
              if (res.id_obra) {
                this.router.navigate([`/proyectos/${res.id_obra}`]);
              } else {
                this.mostrarExito('Proyecto creado exitosamente.');
                this.cargarDatos();
              }
            } else {
              this.mostrarError(res.message || 'Error al registrar el proyecto.');
            }
          });
        },
        error: (err) => {
          this.ngZone.run(() => {
            this.guardando = false;
            this.mostrarError(err.error?.detail || 'Error al crear el proyecto.');
          });
        }
      });
    }
  }

  esRolAutorizado(): boolean {
    const rol = this.authService.obtenerUsuario()?.nombre_rol;
    return rol === 'ADMINISTRADOR' || rol === 'ADMINISTRADOR_EMPRESA';
  }

  mostrarError(mensaje: string) {
    this.mensajeError = mensaje;
    setTimeout(() => {
      this.mensajeError = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  mostrarExito(mensaje: string) {
    this.mensajeExito = mensaje;
    setTimeout(() => {
      this.mensajeExito = '';
      this.cdr.detectChanges();
    }, 4000);
  }
}
