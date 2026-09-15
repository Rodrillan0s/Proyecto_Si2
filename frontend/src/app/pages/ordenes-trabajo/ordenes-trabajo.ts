import {
  Component,
  OnInit,
  inject,
  ChangeDetectorRef,
  NgZone,
  PLATFORM_ID,
  OnDestroy,
  DestroyRef
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import {
  OrdenesTrabajoService,
  OrdenTrabajo
} from '../../services/ordenes-trabajo';

import { AuthService } from '../../services/auth';

import { OrdenTrabajoEstructuraComponent } from './estructura/orden-trabajo-estructura/orden-trabajo-estructura';

import { OrdenTrabajoResponsablesComponent } from './responsables/orden-trabajo-responsables/orden-trabajo-responsables';

@Component({
  selector: 'app-ordenes-trabajo',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    OrdenTrabajoEstructuraComponent,
    OrdenTrabajoResponsablesComponent
  ],
  templateUrl: './ordenes-trabajo.html',
  styleUrl: './ordenes-trabajo.css'
})
export class OrdenesTrabajoComponent implements OnInit, OnDestroy {

  private ordenesTrabajoService = inject(OrdenesTrabajoService);
  private authService = inject(AuthService);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);
  private ngZone = inject(NgZone);
  private platformId = inject(PLATFORM_ID);
  private destroyRef = inject(DestroyRef);

  ordenes: OrdenTrabajo[] = [];
  ordenesFiltradas: OrdenTrabajo[] = [];
  empresaActiva: any = null;

  ordenSeleccionada: OrdenTrabajo | null = null;

  mostrarResponsables = false;

  busqueda = '';
  filtroEstado = '';
  filtroTipo = '';

  cargando = false;
  guardando = false;

  mensajeError = '';
  mensajeExito = '';

  mostrarModal = false;
  modoEdicion = false;

  estadisticas = {
    total: 0,
    pendientes: 0,
    enProceso: 0,
    finalizadas: 0
  };

  private timeoutMensajes: any;

  ngOnInit(): void {
    this.authService.empresaActiva$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((empresa) => {
        this.empresaActiva = empresa;
        this.cargarDatos();
      });
  }

  ngOnDestroy(): void {
    if (this.timeoutMensajes) {
      clearTimeout(this.timeoutMensajes);
    }
  }

  esVistaGlobal(): boolean {
    return this.authService.esVistaGlobal();
  }

  cargarDatos(): void {
    this.cargando = true;
    this.mensajeError = '';
    const idEmpresa = this.authService.obtenerIdEmpresaActiva() || undefined;

    this.ordenesTrabajoService.listarOrdenesTrabajo(idEmpresa).subscribe({
      next: (respuesta) => {
        this.ngZone.run(() => {
          this.ordenes = respuesta.data || [];
          this.aplicarFiltros();
          this.calcularEstadisticas();
          this.cargando = false;
          this.cdr.detectChanges();
        });
      },

      error: (error) => {
        this.ngZone.run(() => {
          console.error(
            'Error al cargar órdenes de trabajo:',
            error
          );

          this.ordenes = [];
          this.ordenesFiltradas = [];
          this.cargando = false;

          this.mostrarError(
            error?.error?.detail ||
            error?.error?.message ||
            'No se pudieron cargar las órdenes de trabajo.'
          );

          this.cdr.detectChanges();
        });
      }
    });
  }

  aplicarFiltros(): void {
    const texto = this.busqueda.trim().toLowerCase();

    this.ordenesFiltradas = this.ordenes.filter((orden) => {

      const coincideBusqueda =
        !texto ||
        String(orden.orden_nro).includes(texto) ||
        String(orden.id_obra).includes(texto) ||
        (orden.codigo || '').toLowerCase().includes(texto) ||
        (orden.nombre || '').toLowerCase().includes(texto) ||
        (orden.nombre_empresa || '').toLowerCase().includes(texto) ||
        (orden.tipo_trab || '').toLowerCase().includes(texto);

      const coincideEstado =
        !this.filtroEstado ||
        orden.estado === this.filtroEstado;

      const coincideTipo =
        !this.filtroTipo ||
        orden.tipo_trab === this.filtroTipo;

      return coincideBusqueda &&
        coincideEstado &&
        coincideTipo;
    });
  }

  calcularEstadisticas(): void {
    this.estadisticas.total = this.ordenes.length;

    this.estadisticas.pendientes = this.ordenes.filter(
      orden => orden.estado === 'PENDIENTE'
    ).length;

    this.estadisticas.enProceso = this.ordenes.filter(
      orden =>
        orden.estado === 'EN_PROCESO' ||
        orden.estado === 'EN PROCESO'
    ).length;

    this.estadisticas.finalizadas = this.ordenes.filter(
      orden =>
        orden.estado === 'FINALIZADO' ||
        orden.estado === 'FINALIZADA' ||
        orden.estado === 'COMPLETADO' ||
        orden.estado === 'COMPLETADA'
    ).length;
  }

  obtenerTiposTrabajo(): string[] {
    return [...new Set(
      this.ordenes
        .map(orden => orden.tipo_trab)
        .filter(
          (tipo): tipo is string => !!tipo
        )
    )];
  }

  obtenerEstados(): string[] {
    return [...new Set(
      this.ordenes
        .map(orden => orden.estado)
        .filter(
          (estado): estado is string => !!estado
        )
    )];
  }

  abrirModalNuevo(): void {
    this.modoEdicion = false;
    this.ordenSeleccionada = null;

    this.mensajeError = '';
    this.mensajeExito = '';

    this.mostrarModal = true;
  }

  abrirModalEditar(orden: OrdenTrabajo): void {
    this.modoEdicion = true;
    this.ordenSeleccionada = orden;

    this.mensajeError = '';
    this.mensajeExito = '';

    this.mostrarModal = true;
  }

  cerrarModal(): void {
    if (this.guardando) {
      return;
    }

    this.mostrarModal = false;
    this.ordenSeleccionada = null;
    this.mensajeError = '';
  }

  ordenGuardada(): void {
    this.mostrarModal = false;
    this.ordenSeleccionada = null;

    this.mostrarExito(
      'Orden de trabajo guardada correctamente.'
    );

    this.cargarDatos();
  }

  abrirResponsables(orden: OrdenTrabajo): void {
    this.ordenSeleccionada = orden;
    this.mostrarResponsables = true;
  }

  cerrarResponsables(): void {
    this.mostrarResponsables = false;
    this.ordenSeleccionada = null;
  }

  eliminarOrden(orden: OrdenTrabajo): void {

    if (orden.estado === 'CANCELADO') {
      return;
    }

    const confirmar = window.confirm(
      `¿Está seguro de cancelar la orden de trabajo OT-${orden.orden_nro}?`
    );

    if (!confirmar) {
      return;
    }

    this.guardando = true;
    this.mensajeError = '';

    this.ordenesTrabajoService
      .eliminarOrdenTrabajo(orden.orden_nro)
      .subscribe({

        next: () => {
          this.ngZone.run(() => {
            this.guardando = false;

            this.mostrarExito(
              'Orden de trabajo cancelada correctamente.'
            );

            this.cargarDatos();
          });
        },

        error: (error) => {
          this.ngZone.run(() => {
            this.guardando = false;

            this.mostrarError(
              error?.error?.detail ||
              error?.error?.message ||
              'No se pudo cancelar la orden de trabajo.'
            );

            this.cdr.detectChanges();
          });
        }
      });
  }

  cambiarEstado(
    orden: OrdenTrabajo,
    nuevoEstado: string
  ): void {

    if (
      !nuevoEstado ||
      orden.estado === nuevoEstado
    ) {
      return;
    }

    this.guardando = true;
    this.mensajeError = '';

    this.ordenesTrabajoService
      .actualizarEstado(
        orden.orden_nro,
        { estado: nuevoEstado }
      )
      .subscribe({

        next: () => {
          this.ngZone.run(() => {
            this.guardando = false;

            this.mostrarExito(
              'Estado de la orden actualizado correctamente.'
            );

            this.cargarDatos();
          });
        },

        error: (error) => {
          this.ngZone.run(() => {
            this.guardando = false;

            this.mostrarError(
              error?.error?.detail ||
              error?.error?.message ||
              'No se pudo actualizar el estado de la orden.'
            );

            this.cdr.detectChanges();
          });
        }
      });
  }

  verOrden(orden: OrdenTrabajo): void {
    this.ordenSeleccionada = orden;
  }

  limpiarFiltros(): void {
    this.busqueda = '';
    this.filtroEstado = '';
    this.filtroTipo = '';

    this.aplicarFiltros();
  }

  obtenerClaseEstado(estado?: string): string {
    switch (estado) {

      case 'PENDIENTE':
        return 'status-pending';

      case 'EN_PROCESO':
      case 'EN PROCESO':
        return 'status-progress';

      case 'FINALIZADO':
      case 'FINALIZADA':
      case 'COMPLETADO':
      case 'COMPLETADA':
        return 'status-completed';

      case 'CANCELADO':
        return 'status-cancelled';

      default:
        return 'status-default';
    }
  }

  obtenerTextoEstado(estado?: string): string {
    switch (estado) {

      case 'PENDIENTE':
        return 'Pendiente';

      case 'EN_PROCESO':
      case 'EN PROCESO':
        return 'En proceso';

      case 'FINALIZADO':
      case 'FINALIZADA':
        return 'Finalizado';

      case 'COMPLETADO':
      case 'COMPLETADA':
        return 'Completado';

      case 'CANCELADO':
        return 'Cancelado';

      default:
        return estado || 'Sin estado';
    }
  }

  mostrarError(mensaje: string): void {
    this.mensajeError = mensaje;
    this.mensajeExito = '';

    this.iniciarTimeoutMensaje();
  }

  mostrarExito(mensaje: string): void {
    this.mensajeExito = mensaje;
    this.mensajeError = '';

    this.iniciarTimeoutMensaje();
  }

  private iniciarTimeoutMensaje(): void {

    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    if (this.timeoutMensajes) {
      clearTimeout(this.timeoutMensajes);
    }

    this.timeoutMensajes = setTimeout(() => {
      this.ngZone.run(() => {
        this.mensajeError = '';
        this.mensajeExito = '';

        this.cdr.detectChanges();
      });
    }, 5000);
  }

  esRolAutorizado(): boolean {
    return true;
  }
}