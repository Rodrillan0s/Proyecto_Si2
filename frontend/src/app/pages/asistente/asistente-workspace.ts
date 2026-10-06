import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { AsistenteService } from '../../services/asistente.service';
@Component({
  standalone: true,
  template: `<header style="margin-bottom:16px"><h1 style="font-size:24px;font-weight:700">Asistente Inteligente</h1><p>Consulta proyectos, reportes y clientes según tus permisos.</p><button style="margin-top:8px;color:#b45309" (click)="ui.open(undefined, 'module')">Abrir conversación</button></header>`,
})
export class AsistenteWorkspace implements OnInit, OnDestroy {
  readonly ui = inject(AsistenteService);
  ngOnInit() { this.ui.open(undefined, 'module'); }
  ngOnDestroy() { this.ui.close(); this.ui.mode.set('chat'); }
}
