import { CommonModule } from '@angular/common';
import { Component, DestroyRef, HostListener, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { forkJoin } from 'rxjs';
import { EmptyStateComponent } from '../../components/ui/empty-state';
import { StatusBadgeComponent } from '../../components/ui/status-badge';
import { AuthService } from '../../services/auth';
import {
  CheckoutFlowService,
  ComprobantePago,
  PagoDetalle,
  PagoEmpresa,
  PagosService,
  PlanPago,
} from '../../services/pagos';
import { PlanSuscripcion, SuscripcionEmpresa, SuscripcionService } from '../../services/suscripcion';

interface PlanVista extends PlanPago {
  prestaciones: string[];
  limite_usuarios?: number;
  limite_obras?: number;
  consultas_ia_mes?: number;
}

@Component({
  standalone: true,
  selector: 'app-pagos',
  imports: [CommonModule, FormsModule, RouterLink, EmptyStateComponent, StatusBadgeComponent],
  templateUrl: './pagos.html',
  styleUrl: './pagos.css',
})
export class PagosComponent implements OnInit {
  private pagosApi = inject(PagosService);
  private suscripcionesApi = inject(SuscripcionService);
  private checkoutFlow = inject(CheckoutFlowService);
  private auth = inject(AuthService);
  private destroyRef = inject(DestroyRef);

  readonly esGlobal = this.auth.obtenerRolNormalizado() === 'ADMINISTRADOR';
  planes = signal<PlanVista[]>([]);
  suscripcion = signal<SuscripcionEmpresa | null>(null);
  historial = signal<PagoEmpresa[]>([]);
  comprobante = signal<ComprobantePago | null>(null);
  pagoConsultado = signal<PagoDetalle | null>(null);
  cargando = signal(true);
  cargandoComprobante = signal(false);
  procesandoPlan = signal<string | null>(null);
  verificando = signal(false);
  consultando = signal(false);
  error = signal('');
  mensaje = signal('');
  idConsulta: number | null = null;
  private checkoutKeys = new Map<string, string>();

  ngOnInit(): void {
    if (this.esGlobal) {
      this.cargando.set(false);
      return;
    }
    this.cargarEmpresa();
  }

  cargarEmpresa(): void {
    this.cargando.set(true);
    this.error.set('');
    forkJoin({
      comerciales: this.pagosApi.planes(),
      catalogo: this.suscripcionesApi.planes(),
      suscripcion: this.suscripcionesApi.propia(),
      historial: this.pagosApi.miEmpresa(),
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: ({ comerciales, catalogo, suscripcion, historial }) => {
        this.planes.set(this.combinarPlanes(comerciales.data, catalogo.data));
        this.suscripcion.set(suscripcion.data);
        this.historial.set(historial.data);
        this.cargando.set(false);
      },
      error: error => {
        this.error.set(this.errorTexto(error, 'No se pudo cargar la información de pagos.'));
        this.cargando.set(false);
      },
    });
  }

  private combinarPlanes(comerciales: PlanPago[], catalogo: PlanSuscripcion[]): PlanVista[] {
    return comerciales.map(plan => {
      const capacidades = catalogo.find(item => item.codigo === plan.codigo);
      return {
        ...plan,
        prestaciones: capacidades?.prestaciones || [],
        limite_usuarios: capacidades?.limite_usuarios,
        limite_obras: capacidades?.limite_obras,
        consultas_ia_mes: capacidades?.consultas_ia_mes,
      };
    });
  }

  iniciarPago(plan: PlanVista): void {
    if (this.esGlobal || this.procesandoPlan()) return;
    this.procesandoPlan.set(plan.codigo);
    this.error.set('');
    this.mensaje.set('');
    const clave = this.checkoutKeys.get(plan.codigo) || this.pagosApi.nuevaClaveIdempotencia();
    this.checkoutKeys.set(plan.codigo, clave);
    this.pagosApi.iniciarCheckout(plan.codigo, clave)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: respuesta => {
          this.procesandoPlan.set(null);
          if (!respuesta.data.checkout_url) {
            this.error.set('Stripe no devolvió una URL de pago. Consulte el intento en su historial.');
            return;
          }
          this.checkoutFlow.redirigir(respuesta.data.id_pago, respuesta.data.checkout_url);
        },
        error: error => {
          this.procesandoPlan.set(null);
          this.error.set(this.errorTexto(error, 'No se pudo iniciar el pago. Intente nuevamente.'));
        },
      });
  }

  etiquetaAccion(plan: PlanVista): string {
    const actual = this.suscripcion();
    if (!actual?.codigo_plan || actual.estado_efectivo === 'CANCELADA') return 'Contratar';
    return actual.codigo_plan === plan.codigo ? 'Renovar' : 'Pagar';
  }

  esPlanActual(plan: PlanVista): boolean {
    return this.suscripcion()?.codigo_plan === plan.codigo;
  }

  buscarPago(preservarMensaje = false): void {
    const id = Number(this.idConsulta);
    if (!Number.isInteger(id) || id <= 0 || this.consultando()) {
      this.error.set('Ingrese un ID de pago válido.');
      return;
    }
    this.consultando.set(true);
    this.error.set('');
    if (!preservarMensaje) this.mensaje.set('');
    this.comprobante.set(null);
    this.pagosApi.pago(id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: respuesta => {
        this.pagoConsultado.set(respuesta.data);
        this.consultando.set(false);
      },
      error: error => {
        this.pagoConsultado.set(null);
        this.consultando.set(false);
        this.error.set(this.errorTexto(error, 'No se encontró el pago solicitado.'));
      },
    });
  }

  verificarPago(): void {
    const pago = this.pagoConsultado();
    if (!this.esGlobal || !pago || pago.estado !== 'PENDIENTE' || this.verificando()) return;
    this.verificando.set(true);
    this.error.set('');
    this.mensaje.set('');
    this.pagosApi.verificar(pago.id_pago).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: respuesta => {
        this.verificando.set(false);
        this.mensaje.set(respuesta.data.estado === 'CONFIRMADO'
          ? 'Stripe confirmó el pago. La suscripción fue actualizada por el backend.'
          : `Stripe mantiene el pago en estado ${respuesta.data.estado}.`);
        this.buscarPago(true);
      },
      error: error => {
        this.verificando.set(false);
        this.error.set(this.errorTexto(error, 'Stripe todavía no confirma este pago.'));
      },
    });
  }

  verComprobante(idPago: number): void {
    if (this.cargandoComprobante()) return;
    this.cargandoComprobante.set(true);
    this.error.set('');
    this.pagosApi.comprobante(idPago).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: respuesta => {
        this.comprobante.set(respuesta.data);
        this.cargandoComprobante.set(false);
      },
      error: error => {
        this.cargandoComprobante.set(false);
        this.error.set(this.errorTexto(error, 'No se pudo cargar el comprobante.'));
      },
    });
  }

  cerrarComprobante(): void {
    this.comprobante.set(null);
  }

  @HostListener('document:keydown.escape')
  cerrarConEscape(): void {
    if (this.comprobante()) this.cerrarComprobante();
  }

  dinero(montoMenor: number, moneda: string): string {
    return new Intl.NumberFormat('es-BO', {
      style: 'currency', currency: moneda, minimumFractionDigits: 2,
    }).format(montoMenor / 100);
  }

  fecha(valor: string | null | undefined): string {
    if (!valor) return 'No disponible';
    return new Intl.DateTimeFormat('es-BO', {
      dateStyle: 'medium', timeStyle: 'short', timeZone: 'America/La_Paz',
    }).format(new Date(valor));
  }

  private errorTexto(error: { error?: { detail?: unknown } }, defecto: string): string {
    return typeof error.error?.detail === 'string' ? error.error.detail : defecto;
  }
}
