import { Component, ChangeDetectorRef, DestroyRef, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { AuthService } from '../../../services/auth';
import {
  AsignarResponsableResponse,
  EstadoIncidencia,
  Incidencia,
  IncidenciasService,
  OrdenesTrabajoMutationResponse,
} from '../../../services/incidencias';

import { PageHeaderComponent } from '../../../components/ui/page-header';
import { StatusBadgeComponent } from '../../../components/ui/status-badge';
import { ConfirmDialogComponent } from '../../../components/ui/confirm-dialog';

import { IncidenciaFormularioComponent } from '../formulario/incidencia-formulario';
import { IncidenciaAsignarResponsableComponent } from '../asignar-responsable/incidencia-asignar-responsable';
import { IncidenciaSeguimientoComponent } from '../seguimiento/incidencia-seguimiento';
import { IncidenciaEvidenciasComponent } from '../evidencias/incidencia-evidencias';
import { IncidenciaOrdenesTrabajoComponent } from '../ordenes-trabajo/incidencia-ordenes-trabajo';

/** Transiciones "lineales" gestionadas por el botón genérico de cambio de
 * estado. ABIERTA→ASIGNADA se realiza siempre a través de "Asignar
 * responsable" (HU71) y RESUELTA→CERRADA a través del botón dedicado
 * "Cerrar incidencia" (HU74, requiere el permiso Cerrar_incidencias).
 * Iniciar (→EN_PROCESO) y finalizar (→PENDIENTE_VALIDACION) la atención solo puede
 * hacerlo el responsable asignado; el backend lo vuelve a verificar. */
const SIGUIENTE_ESTADO: Partial<Record<EstadoIncidencia, EstadoIncidencia>> = {
  ASIGNADA: 'EN_PROCESO',
  EN_PROCESO: 'PENDIENTE_VALIDACION',
};

const TEXTO_ACCION_ESTADO: Partial<Record<EstadoIncidencia, string>> = {
  EN_PROCESO: 'Iniciar atención',
  PENDIENTE_VALIDACION: 'Finalizar atención',
};

@Component({
  selector: 'app-incidencia-detalle',
  standalone: true,
  imports: [
    CommonModule,
    PageHeaderComponent,
    StatusBadgeComponent,
    ConfirmDialogComponent,
    IncidenciaFormularioComponent,
    IncidenciaAsignarResponsableComponent,
    IncidenciaSeguimientoComponent,
    IncidenciaEvidenciasComponent,
    IncidenciaOrdenesTrabajoComponent,
  ],
  templateUrl: './incidencia-detalle.html',
  styleUrl: './incidencia-detalle.css',
})
export class IncidenciaDetalleComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private authService = inject(AuthService);
  private incidenciasService = inject(IncidenciasService);
  private cdr = inject(ChangeDetectorRef);
  private destroyRef = inject(DestroyRef);

  idIncidencia = 0;
  incidencia: Incidencia | null = null;

  cargando = true;
  error = '';
  exito = '';

  modal: 'editar' | 'asignar' | 'ordenes' | null = null;

  confirmando: 'estado' | 'cerrar' | null = null;
  estadoObjetivo: EstadoIncidencia | null = null;
  procesandoEstado = false;

  ngOnInit(): void {
    this.route.paramMap
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((params) => {
        const id = Number(params.get('id'));
        if (id) {
          this.idIncidencia = id;
          this.cargarDetalle();
        }
      });
  }

  cargarDetalle(): void {
    this.cargando = true;
    this.error = '';
    this.incidenciasService.obtener(this.idIncidencia).subscribe({
      next: (res) => {
        this.cargando = false;
        this.incidencia = res.data;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.cargando = false;
        this.incidencia = null;
        this.error = this.mensajeError(err, 'No se pudo cargar la incidencia.');
        this.cdr.detectChanges();
      },
    });
  }

  volver(): void {
    this.router.navigate([this.hasPermission('Visualizar_incidencias') ? '/incidencias' : '/incidencias/asignadas']);
  }

  hasPermission(permiso: string): boolean {
    return this.authService.hasPermission(permiso);
  }

  // ── Reglas de visibilidad de acciones (según permisos + estado actual) ──
  puedeEditar(): boolean {
    return this.hasPermission('Modificar_incidencias') && this.incidencia?.estado !== 'CERRADA';
  }

  puedeAsignar(): boolean {
    return this.hasPermission('Asignar_incidencias') && this.incidencia?.estado !== 'CERRADA';
  }

  puedeComentar(): boolean {
    return (this.hasPermission('Modificar_incidencias') || this.esResponsable()) && this.incidencia?.estado !== 'CERRADA';
  }

  puedeAdjuntarEvidencia(): boolean {
    return (this.hasPermission('Modificar_incidencias') || this.esResponsable()) && this.incidencia?.estado !== 'CERRADA';
  }

  puedeCerrar(): boolean {
    return this.hasPermission('Cerrar_incidencias') && this.incidencia?.estado === 'RESUELTA';
  }

  /** OT afectadas: mismo actor que asigna el responsable (Asignar_incidencias). */
  puedeSeleccionarOrdenes(): boolean {
    return this.hasPermission('Asignar_incidencias') && this.incidencia?.estado !== 'CERRADA';
  }

  esResponsable(): boolean {
    const usuario = this.authService.obtenerUsuario();
    const idResponsable = this.incidencia?.id_responsable;
    return !!usuario && idResponsable != null && Number(usuario.nro_usuario) === Number(idResponsable);
  }

  puedeValidar(): boolean {
    return this.incidencia?.estado === 'PENDIENTE_VALIDACION' && this.hasPermission('Modificar_incidencias');
  }

  siguienteEstado(): EstadoIncidencia | null {
    if (!this.incidencia || !this.esResponsable()) return null;
    return SIGUIENTE_ESTADO[this.incidencia.estado] || null;
  }

  textoSiguienteEstado(): string {
    const estado = this.siguienteEstado();
    return estado ? TEXTO_ACCION_ESTADO[estado] || `Marcar como ${estado}` : '';
  }

  etiquetaOrden(ordenNro: number): string {
    return 'OT-' + String(ordenNro).padStart(3, '0');
  }

  // ── Editar ────────────────────────────────────────────────────────────
  abrirEditar(): void {
    this.modal = 'editar';
  }

  cerrarModal(): void {
    this.modal = null;
  }

  incidenciaActualizada(): void {
    this.modal = null;
    this.mostrarExito('Incidencia actualizada exitosamente.');
    this.cargarDetalle();
  }

  // ── Asignar responsable (HU71) ───────────────────────────────────────
  abrirAsignar(): void {
    this.modal = 'asignar';
  }

  responsableAsignado(res: AsignarResponsableResponse): void {
    this.modal = null;
    this.mostrarExito(res.message || 'Responsable asignado exitosamente.');
    this.cargarDetalle();
  }

  // ── Órdenes de trabajo afectadas ─────────────────────────────────────
  abrirOrdenes(): void {
    this.modal = 'ordenes';
  }

  ordenesGuardadas(res: OrdenesTrabajoMutationResponse): void {
    this.modal = null;
    this.mostrarExito(res.message || 'Órdenes de trabajo afectadas actualizadas.');
    this.cargarDetalle();
  }

  // ── Cambio de estado (HU72) ──────────────────────────────────────────
  confirmarCambioEstado(estado: EstadoIncidencia): void {
    this.estadoObjetivo = estado;
    this.confirmando = 'estado';
  }

  // ── Cierre (HU74) ────────────────────────────────────────────────────
  confirmarCierre(): void {
    this.estadoObjetivo = 'CERRADA';
    this.confirmando = 'cerrar';
  }

  cancelarConfirmacion(): void {
    if (this.procesandoEstado) return;
    this.confirmando = null;
    this.estadoObjetivo = null;
  }

  ejecutarCambioEstado(): void {
    if (!this.estadoObjetivo || this.procesandoEstado) return;
    this.procesandoEstado = true;

    this.incidenciasService.cambiarEstado(this.idIncidencia, this.estadoObjetivo).subscribe({
      next: (res) => {
        this.procesandoEstado = false;
        this.confirmando = null;
        this.estadoObjetivo = null;
        this.mostrarExito(res.message || 'Estado actualizado exitosamente.');
        this.cargarDetalle();
      },
      error: (err) => {
        this.procesandoEstado = false;
        this.confirmando = null;
        this.estadoObjetivo = null;
        this.mostrarError(this.mensajeError(err, 'No se pudo actualizar el estado.'));
      },
    });
  }

  // ── Mensajes ─────────────────────────────────────────────────────────
  private mensajeError(err: any, fallback: string): string {
    if (err?.status === 401) return 'Tu sesión ha expirado. Vuelve a iniciar sesión.';
    if (err?.status === 403) return 'No tienes permisos para realizar esta acción.';
    if (err?.status === 404) return err?.error?.detail || 'La incidencia no existe o no pertenece a tu empresa.';
    if (err?.status >= 500) return 'Error interno del servidor. Intenta nuevamente.';
    return err?.error?.detail || err?.error?.message || fallback;
  }

  private mostrarError(mensaje: string): void {
    this.error = mensaje;
    setTimeout(() => { this.error = ''; this.cdr.detectChanges(); }, 6000);
  }

  private mostrarExito(mensaje: string): void {
    this.exito = mensaje;
    setTimeout(() => { this.exito = ''; this.cdr.detectChanges(); }, 4500);
  }
}
