import { Component, OnInit, inject, ChangeDetectorRef, NgZone, PLATFORM_ID, OnDestroy } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { ProyectosService, Proyecto } from '../../../services/proyectos';
import { AuthService } from '../../../services/auth';
import { environment } from '../../../../environments/environment';

export interface UsuarioEmpresa {
  nro_usuario: number;
  nombre_completo: string;
  nombre_rol: string;
}

@Component({
  selector: 'app-proyecto-detalle',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './proyecto-detalle.html',
  styleUrl: './proyecto-detalle.css'
})
export class ProyectoDetalleComponent implements OnInit, OnDestroy {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private proyectosService = inject(ProyectosService);
  private authService = inject(AuthService);
  private http = inject(HttpClient);
  private cdr = inject(ChangeDetectorRef);
  private ngZone = inject(NgZone);
  private platformId = inject(PLATFORM_ID);
  private apiUrl = environment.apiUrl;

  proyecto: Proyecto | null = null;
  idObra: number = 0;
  usuariosDisponibles: UsuarioEmpresa[] = [];
  idUsuarioSeleccionado: number | undefined;

  cargando: boolean = false;
  procesandoAccion: boolean = false;
  mensajeError: string = '';
  mensajeExito: string = '';

  private mapa: any = null;

  ngOnInit() {
    this.route.paramMap.subscribe(params => {
      const idStr = params.get('id');
      if (idStr) {
        this.idObra = Number(idStr);
        this.cargarProyecto();
      } else {
        this.router.navigate(['/proyectos']);
      }
    });
  }

  ngOnDestroy() {
    this.destruirMapa();
  }

  cargarProyecto() {
    this.cargando = true;
    this.mensajeError = '';

    this.proyectosService.obtenerProyectoDetalle(this.idObra).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res.success) {
            this.proyecto = res.data;
            this.cargarUsuariosEmpresa();
            this.iniciarMapaDetalle();
          } else {
            this.mostrarError('No se pudo cargar el detalle del proyecto.');
          }
          this.cargando = false;
          this.cdr.detectChanges();
        });
      },
      error: (err) => {
        this.ngZone.run(() => {
          this.mostrarError(err.error?.detail || 'Error de conexión al cargar la obra.');
          this.cargando = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  private iniciarMapaDetalle() {
    if (!isPlatformBrowser(this.platformId)) return;

    setTimeout(async () => {
      try {
        const L = await import('leaflet');
        this.destruirMapa();

        const contenedor = document.getElementById('mapa-detalle-proyecto');
        if (!contenedor) return;

        const lat = this.proyecto?.latitud ? Number(this.proyecto.latitud) : -17.7833;
        const lng = this.proyecto?.longitud ? Number(this.proyecto.longitud) : -63.1821;

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

        this.mapa = L.map('mapa-detalle-proyecto').setView([lat, lng], 14);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; OpenStreetMap contributors'
        }).addTo(this.mapa);

        const marker = L.marker([lat, lng]).addTo(this.mapa);
        marker.bindPopup(`<b>${this.proyecto?.nombre || 'Obra'}</b><br>${this.proyecto?.ubicacion || 'Santa Cruz'}`).openPopup();

        setTimeout(() => {
          this.mapa?.invalidateSize();
        }, 200);

      } catch (err) {
        console.error('Error al inicializar mapa en detalle:', err);
      }
    }, 200);
  }

  private destruirMapa() {
    if (this.mapa) {
      this.mapa.remove();
      this.mapa = null;
    }
  }

  cargarUsuariosEmpresa() {
    this.http.get<{ success: boolean; data: UsuarioEmpresa[] }>(`${this.apiUrl}/api/usuarios/`).subscribe({
      next: (res) => {
        if (res.success) {
          const idsAsignados = this.proyecto?.responsables?.map(r => r.id_usuario) || [];
          // Filtrar exclusivamente usuarios pertenecientes al rol 'JEFE DE OBRA'
          this.usuariosDisponibles = (res.data || []).filter(u => 
            u.nombre_rol === 'JEFE DE OBRA' && !idsAsignados.includes(u.nro_usuario)
          );
        }
      }
    });
  }

  cambiarEstado(nuevoEstado: string) {
    if (!this.proyecto || this.procesandoAccion) return;

    this.procesandoAccion = true;
    this.mensajeError = '';

    this.proyectosService.actualizarEstadoProyecto(this.idObra, nuevoEstado).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          this.procesandoAccion = false;
          if (res.success) {
            this.mostrarExito('Estado actualizado correctamente.');
            this.cargarProyecto();
          } else {
            this.mostrarError(res.message || 'Error al cambiar de estado.');
          }
        });
      },
      error: (err) => {
        this.ngZone.run(() => {
          this.procesandoAccion = false;
          this.mostrarError(err.error?.detail || 'Error al actualizar el estado de la obra.');
        });
      }
    });
  }

  asignarResponsable() {
    if (!this.idUsuarioSeleccionado || this.procesandoAccion) return;

    this.procesandoAccion = true;
    this.mensajeError = '';

    this.proyectosService.asignarResponsable(this.idObra, Number(this.idUsuarioSeleccionado)).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          this.procesandoAccion = false;
          if (res.success) {
            this.mostrarExito('Responsable asignado correctamente.');
            this.idUsuarioSeleccionado = undefined;
            this.cargarProyecto();
          } else {
            this.mostrarError(res.message || 'Error al asignar responsable.');
          }
        });
      },
      error: (err) => {
        this.ngZone.run(() => {
          this.procesandoAccion = false;
          this.mostrarError(err.error?.detail || 'Error al asignar responsable en el backend.');
        });
      }
    });
  }

  retirarResponsable(idUsuario: number) {
    if (this.procesandoAccion) return;

    if (confirm('¿Está seguro de que desea retirar a este responsable del proyecto?')) {
      this.procesandoAccion = true;
      this.mensajeError = '';

      this.proyectosService.retirarResponsable(this.idObra, idUsuario).subscribe({
        next: (res) => {
          this.ngZone.run(() => {
            this.procesandoAccion = false;
            if (res.success) {
              this.mostrarExito('Responsable retirado correctamente.');
              this.cargarProyecto();
            } else {
              this.mostrarError(res.message || 'Error al retirar responsable.');
            }
          });
        },
        error: (err) => {
          this.ngZone.run(() => {
            this.procesandoAccion = false;
            this.mostrarError(err.error?.detail || 'Error al retirar responsable en el backend.');
          });
        }
      });
    }
  }

  volverAProyectos() {
    this.router.navigate(['/proyectos']);
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
