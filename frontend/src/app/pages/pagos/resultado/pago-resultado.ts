import { CommonModule } from '@angular/common';
import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { StatusBadgeComponent } from '../../../components/ui/status-badge';
import { CheckoutFlowService, PagoDetalle, PagosService } from '../../../services/pagos';

@Component({
  standalone: true,
  selector: 'app-pago-resultado',
  imports: [CommonModule, RouterLink, StatusBadgeComponent],
  templateUrl: './pago-resultado.html',
  styleUrl: './pago-resultado.css',
})
export class PagoResultadoComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private pagosApi = inject(PagosService);
  private checkoutFlow = inject(CheckoutFlowService);
  private destroyRef = inject(DestroyRef);

  estadoRetorno = signal<'success' | 'cancel' | 'invalid'>('invalid');
  pago = signal<PagoDetalle | null>(null);
  cargando = signal(false);
  error = signal('');
  idPago = signal<number | null>(null);

  ngOnInit(): void {
    const status = this.route.snapshot.queryParamMap.get('status');
    if (status === 'cancel') {
      this.estadoRetorno.set('cancel');
      return;
    }
    if (status !== 'success') {
      this.estadoRetorno.set('invalid');
      return;
    }
    this.estadoRetorno.set('success');
    const queryId = Number(this.route.snapshot.queryParamMap.get('id_pago'));
    const id = Number.isInteger(queryId) && queryId > 0 ? queryId : this.checkoutFlow.ultimoPagoId();
    this.idPago.set(id);
    if (id) this.consultar();
  }

  consultar(): void {
    const id = this.idPago();
    if (!id || this.cargando()) return;
    this.cargando.set(true);
    this.error.set('');
    this.pagosApi.pago(id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: respuesta => {
        this.pago.set(respuesta.data);
        this.cargando.set(false);
      },
      error: error => {
        this.cargando.set(false);
        this.error.set(typeof error.error?.detail === 'string'
          ? error.error.detail : 'No se pudo consultar el estado del pago.');
      },
    });
  }

  actualizarEstado(): void {
    const id = this.idPago();
    if (!id || this.cargando()) return;
    this.cargando.set(true);
    this.error.set('');
    this.pagosApi.verificar(id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.cargando.set(false);
        this.consultar();
      },
      error: error => {
        this.cargando.set(false);
        this.error.set(typeof error.error?.detail === 'string'
          ? error.error.detail : 'No se pudo verificar el pago con Stripe.');
      },
    });
  }
}
