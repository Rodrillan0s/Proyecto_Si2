import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { AsistenteService } from '../../services/asistente.service';
import { SuscripcionService } from '../../services/suscripcion';
@Component({
  standalone: true,
  template: `<header style="margin-bottom:16px"><h1 style="font-size:24px;font-weight:700">Asistente Inteligente</h1>
    @if (suscripcion.iaPermitida) { <p>Consulta proyectos, reportes y clientes según tus permisos.</p><button style="margin-top:8px;color:#b45309" (click)="ui.open(undefined, 'module')">Abrir conversación</button> }
    @else { <p>El asistente de IA está disponible con una suscripción Empresarial activa.</p> }
    </header>`,
})
export class AsistenteWorkspace implements OnInit, OnDestroy {
  readonly ui = inject(AsistenteService);
  readonly suscripcion = inject(SuscripcionService);
  ngOnInit() { if (this.suscripcion.iaPermitida) this.ui.open(undefined, 'module'); }
  ngOnDestroy() { this.ui.close(); this.ui.mode.set('chat'); }
}
