import { ChangeDetectorRef, Component, Input, OnDestroy, OnInit, ViewChild, ElementRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';

import { IncidenciaEvidencia, IncidenciasService } from '../../../services/incidencias';

const TIPOS_ADMITIDOS = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
const TAMANO_MAXIMO_BYTES = 10 * 1024 * 1024; // 10 MB (límite documentado en el backend)

interface EvidenciaConVista extends IncidenciaEvidencia {
  urlVista?: string;
  cargandoVista?: boolean;
  errorVista?: boolean;
}

@Component({
  selector: 'app-incidencia-evidencias',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './incidencia-evidencias.html',
})
export class IncidenciaEvidenciasComponent implements OnInit, OnDestroy {
  private incidenciasService = inject(IncidenciasService);
  private cdr = inject(ChangeDetectorRef);

  @Input({ required: true }) idIncidencia!: number;
  @Input() puedeAdjuntar = false;

  @ViewChild('inputArchivo') inputArchivo?: ElementRef<HTMLInputElement>;

  evidencias: EvidenciaConVista[] = [];
  cargando = false;
  subiendo = false;
  error = '';

  /** HU73: evidencia mostrada en el visor modal (null = visor cerrado). */
  evidenciaEnVisor: EvidenciaConVista | null = null;

  private urlsCreadas: string[] = [];

  ngOnInit(): void {
    this.cargar();
  }

  ngOnDestroy(): void {
    this.urlsCreadas.forEach((url) => URL.revokeObjectURL(url));
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    this.incidenciasService.listarEvidencias(this.idIncidencia).subscribe({
      next: (res) => {
        this.cargando = false;
        this.evidencias = res.data || [];
        this.evidencias.forEach((ev) => this.cargarVistaPrevia(ev));
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.cargando = false;
        this.error = err?.error?.detail || 'No se pudieron cargar las evidencias.';
        this.cdr.detectChanges();
      },
    });
  }

  /** Las fotos no son públicas: se descargan por el endpoint autenticado y se
   * muestran como blob local (nunca una URL directa a backend/uploads). El
   * mismo blob se reutiliza para la miniatura y para el visor (HU73): no se
   * vuelve a pedir el archivo al backend si ya está cargado en memoria. */
  private cargarVistaPrevia(ev: EvidenciaConVista): void {
    ev.cargandoVista = true;
    ev.errorVista = false;
    this.incidenciasService.descargarEvidencia(this.idIncidencia, ev.id_evidencia).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        this.urlsCreadas.push(url);
        ev.urlVista = url;
        ev.cargandoVista = false;
        this.cdr.detectChanges();
      },
      error: () => {
        ev.cargandoVista = false;
        ev.errorVista = true;
        this.cdr.detectChanges();
      },
    });
  }

  /** HU73: clic en la miniatura abre el visor en vez de descargar. Si la
   * vista previa aún no cargó (o falló), se reintenta al abrir el visor. */
  abrirVisor(ev: EvidenciaConVista): void {
    this.evidenciaEnVisor = ev;
    if (!ev.urlVista && !ev.cargandoVista) {
      this.cargarVistaPrevia(ev);
    }
  }

  cerrarVisor(): void {
    this.evidenciaEnVisor = null;
  }

  seleccionarArchivo(): void {
    this.inputArchivo?.nativeElement.click();
  }

  onArchivoSeleccionado(event: Event): void {
    const input = event.target as HTMLInputElement;
    const archivo = input.files?.[0];
    input.value = '';
    if (!archivo) return;

    if (!TIPOS_ADMITIDOS.includes(archivo.type)) {
      this.error = 'Solo se permiten fotografías en formato JPEG, PNG, WEBP o GIF.';
      return;
    }
    if (archivo.size > TAMANO_MAXIMO_BYTES) {
      this.error = 'La fotografía supera el tamaño máximo permitido (10 MB).';
      return;
    }

    this.error = '';
    this.subiendo = true;
    this.incidenciasService.subirEvidencia(this.idIncidencia, archivo).subscribe({
      next: () => {
        this.subiendo = false;
        this.cargar();
      },
      error: (err) => {
        this.subiendo = false;
        this.error = err?.error?.detail || 'No se pudo adjuntar la fotografía.';
      },
    });
  }

  descargar(ev: EvidenciaConVista): void {
    if (!ev.urlVista) return;
    const a = document.createElement('a');
    a.href = ev.urlVista;
    a.download = ev.nombre_archivo;
    a.click();
  }

  trackByEvidencia(_index: number, item: IncidenciaEvidencia): number {
    return item.id_evidencia;
  }

  formatearTamano(bytes?: number | null): string {
    if (!bytes) return '';
    const kb = bytes / 1024;
    return kb < 1024 ? `${kb.toFixed(0)} KB` : `${(kb / 1024).toFixed(1)} MB`;
  }
}
