import { Injectable, signal } from '@angular/core';

/** Estado de presentación del asistente compartido por el shell autenticado. */
@Injectable({ providedIn: 'root' })
export class AsistenteService {
  readonly opened = signal(false);
  readonly draft = signal<string | null>(null);
  open(text?: string) {
    if (text !== undefined) this.draft.set(text);
    this.opened.set(true);
  }
  close() {
    this.opened.set(false);
  }
}
