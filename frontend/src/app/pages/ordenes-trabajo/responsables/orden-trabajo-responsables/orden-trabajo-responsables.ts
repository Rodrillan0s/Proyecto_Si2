import {
  Component,
  EventEmitter,
  Input,
  Output,
  OnInit,
  inject,
  ChangeDetectorRef,
  NgZone
} from '@angular/core';

import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

import { environment } from '../../../../../environments/environment';
import { AuthService } from '../../../../services/auth';

import {
  OrdenesTrabajoService,
  OrdenTrabajo,
  ResponsableOrdenTrabajo
} from '../../../../services/ordenes-trabajo';

interface UsuarioDisponible {
  nro_usuario?: number;
  nombre_usuario: string;
  nombre_completo: string;
  correo: string;
  telefono: string;
  nro_rol: number;
  nombre_rol?: string;
  id_empresa?: number | null;
  nombre_empresa?: string;
  estado: string;
}

interface RespuestaApiUsuarios {
  success: boolean;
  message: string;
  data: UsuarioDisponible[];
}

@Component({
  selector: 'app-orden-trabajo-responsables',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './orden-trabajo-responsables.html',
  styleUrl: './orden-trabajo-responsables.css'
})
export class OrdenTrabajoResponsablesComponent implements OnInit {

  private http = inject(HttpClient);
  private authService = inject(AuthService);
  private ordenesTrabajoService = inject(OrdenesTrabajoService);
  private cdr = inject(ChangeDetectorRef);
  private ngZone = inject(NgZone);

  private apiUrl = environment.apiUrl;

  @Input() orden: OrdenTrabajo | null = null;

  @Output() cerrar = new EventEmitter<void>();

  responsables: ResponsableOrdenTrabajo[] = [];
  usuariosDisponibles: UsuarioDisponible[] = [];

  usuarioSeleccionado: number | null = null;

  cargando = false;
  asignando = false;

  mensajeError = '';
  mensajeExito = '';

  ngOnInit(): void {
  console.log('ORDEN RECIBIDA:', this.orden);

  if (!this.orden) {
    return;
  }

  console.log('ORDEN NRO:', this.orden.orden_nro);

  this.cargarResponsables();
  this.cargarUsuarios();
}

  cargarResponsables(): void {

    if (!this.orden) {
      return;
    }

    this.cargando = true;
    this.mensajeError = '';

    this.ordenesTrabajoService
      .listarResponsablesOrdenTrabajo(this.orden.orden_nro)
      .subscribe({

        next: (res) => {

          this.ngZone.run(() => {

        this.responsables = res.data || [];
            this.cargando = false;

            this.cdr.detectChanges();
          });
        },

        error: (error) => {

          this.ngZone.run(() => {

            this.cargando = false;

            this.mensajeError =
              error?.error?.detail ||
              error?.error?.message ||
              'No se pudieron cargar los responsables.';

            this.cdr.detectChanges();
          });
        }
      });
  }

  cargarUsuarios(): void {

    const token = this.authService.obtenerToken();

    const headers = {
      Authorization: `Bearer ${token}`
    };

    this.http
      .get<RespuestaApiUsuarios>(
        `${this.apiUrl}/api/usuarios/`,
        { headers }
      )
      .subscribe({

        next: (res) => {

          this.ngZone.run(() => {

            if (res.success) {

              this.usuariosDisponibles = res.data.filter(
                usuario => usuario.estado === 'ACTIVO'
              );

            } else {

              this.mensajeError =
                res.message ||
                'No se pudieron cargar los usuarios.';
            }

            this.cdr.detectChanges();
          });
        },

        error: (error) => {

          this.ngZone.run(() => {

            this.mensajeError =
              error?.error?.detail ||
              error?.error?.message ||
              'Error al cargar los usuarios disponibles.';

            this.cdr.detectChanges();
          });
        }
      });
  }

  asignarResponsable(): void {

    if (!this.orden) {
      return;
    }

    if (!this.usuarioSeleccionado) {
      this.mensajeError =
        'Debe seleccionar un usuario.';
      return;
    }

    const yaAsignado = this.responsables.some(
      responsable =>
        responsable.id_usuario === this.usuarioSeleccionado
    );

    if (yaAsignado) {
      this.mensajeError =
        'El usuario ya está asignado a esta orden de trabajo.';
      return;
    }

    this.asignando = true;
    this.mensajeError = '';
    this.mensajeExito = '';

    this.ordenesTrabajoService
      .asignarResponsableOrdenTrabajo(
        this.orden.orden_nro,
        this.usuarioSeleccionado
      )
      .subscribe({

        next: () => {

          this.ngZone.run(() => {

            this.asignando = false;
            this.usuarioSeleccionado = null;

            this.mensajeExito =
              'Responsable asignado correctamente.';

            this.cargarResponsables();

            this.cdr.detectChanges();
          });
        },

        error: (error) => {

          this.ngZone.run(() => {

            this.asignando = false;

            this.mensajeError =
              error?.error?.detail ||
              error?.error?.message ||
              'No se pudo asignar el responsable.';

            this.cdr.detectChanges();
          });
        }
      });
  }

  eliminarResponsable(
    responsable: ResponsableOrdenTrabajo
  ): void {

    if (!this.orden) {
      return;
    }

    const confirmar = window.confirm(
      `¿Está seguro de retirar a ${responsable.nombre_completo} de esta orden de trabajo?`
    );

    if (!confirmar) {
      return;
    }

    this.asignando = true;
    this.mensajeError = '';
    this.mensajeExito = '';

    this.ordenesTrabajoService
      .eliminarResponsableOrdenTrabajo(
        this.orden.orden_nro,
        responsable.id_usuario
      )
      .subscribe({

        next: () => {

          this.ngZone.run(() => {

            this.asignando = false;

            this.mensajeExito =
              'Responsable retirado correctamente.';

            this.cargarResponsables();

            this.cdr.detectChanges();
          });
        },

        error: (error) => {

          this.ngZone.run(() => {

            this.asignando = false;

            this.mensajeError =
              error?.error?.detail ||
              error?.error?.message ||
              'No se pudo retirar el responsable.';

            this.cdr.detectChanges();
          });
        }
      });
  }

  cerrarFormulario(): void {

    if (this.asignando) {
      return;
    }

    this.cerrar.emit();
  }
}