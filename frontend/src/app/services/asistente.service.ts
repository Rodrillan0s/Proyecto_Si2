import { Injectable, signal } from '@angular/core';

export const ASSISTANT_PERMISSIONS = ['Visualizar_reportes', 'Visualizar_clientes', 'Visualizar_obras',
  'Visualizar_materiales', 'Visualizar_proveedores', 'Visualizar_ordenes_compra',
  'Visualizar_equipos_maquinaria', 'Visualizar_ordenes_trabajo', 'Visualizar_estimaciones',
  'Visualizar_usuarios', 'Visualizar_mano_obra'];

/** Estado de presentación del asistente compartido por el shell autenticado. */
@Injectable({ providedIn: 'root' })
export class AsistenteService {
  readonly opened = signal(false);
  readonly draft = signal<string | null>(null);
  readonly mode = signal<'quick' | 'chat' | 'module'>('chat');
  readonly submissions = signal(0);
  open(text?: string, mode: 'quick' | 'chat' | 'module' = 'chat') {
    this.mode.set(mode);
    if (text !== undefined) this.draft.set(text);
    this.opened.set(true);
  }
  quick(text: string) { this.open(text, 'quick'); if (text.trim()) this.submissions.update(value => value + 1); }
  close() {
    this.opened.set(false);
  }
}
