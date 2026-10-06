import { ChangeDetectorRef, Component, inject, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  BackupArchive,
  BackupDownload,
  BackupJob,
  BackupRestore,
  BackupSchedule,
  BackupScope,
  BackupService,
  BackupStatus,
} from '../../services/backup';

@Component({
  selector: 'app-backup',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './backup.html',
  styleUrls: ['./backup.css', './backup-restore.css'],
})
export class BackupComponent implements OnInit, OnDestroy {
  private api = inject(BackupService);
  private cdr = inject(ChangeDetectorRef);
  private timer?: ReturnType<typeof setInterval>;
  private destroyed = false;
  private downloadExpiry?: ReturnType<typeof setTimeout>;
  private cancelDownloadWait?: () => void;
  descargaLista: BackupDownload | null = null;
  private refreshing = false;
  private requestKey: string | null = null;
  private requestScope: BackupScope | null = null;
  estado: BackupStatus | null = null;
  historial: BackupJob[] = [];
  restauraciones: BackupRestore[] = [];
  seleccion: BackupRestore | null = null;
  alcance: BackupScope = 'base_datos';
  programacion: BackupSchedule = {
    habilitada: false,
    alcance: 'base_datos',
    frecuencia: 'diario',
    hora: '02:00',
    zona_horaria: 'America/La_Paz',
    dia_semana: 0,
    dia_mes: 1,
    retencion_dias: 30,
  };
  proxima: string | null = null;
  pagina = 1;
  total = 0;
  filtro = '';
  cargando = false;
  ocupada = '';
  mensaje = '';
  error = false;
  confirmacion = '';
  identificador = '';
  password = '';
  importado: BackupArchive | null = null;

  ngOnInit() {
    void this.actualizar(true);
    this.timer = setInterval(() => {
      void this.actualizar();
    }, 10000);
  }
  ngOnDestroy() {
    this.destroyed = true;
    clearInterval(this.timer);
    clearTimeout(this.downloadExpiry);
    this.cancelDownloadWait?.();
    this.descargaLista = null;
    this.password = '';
  }
  private paint() {
    if (!this.destroyed) this.cdr.markForCheck();
  }
  private notify(text: string, error = false) {
    this.mensaje = text;
    this.error = error;
    this.paint();
  }
  private async fail(error: any) {
    if (this.destroyed) return;
    let body = error?.error;
    if (body instanceof Blob) {
      try {
        body = JSON.parse(await body.text());
      } catch {
        body = null;
      }
    }
    const message =
      body?.code === 'BACKUP_REAUTH_FAILED'
        ? body.detail
        : error?.status === 401
          ? 'Tu sesión necesita renovarse. Inicia sesión para continuar.'
          : error?.status === 403
            ? 'Solo el administrador global puede acceder a las copias de respaldo.'
            : typeof body?.detail === 'string'
              ? body.detail
              : error?.status === 0
                ? 'No se pudo conectar. Si se está promoviendo una restauración, espera a que vuelvan los servicios.'
                : 'No se pudo completar la operación. Revisa los datos y vuelve a intentar.';
    this.notify(message, true);
  }
  async actualizar(inicial = false) {
    if (this.refreshing || this.destroyed) return;
    this.refreshing = true;
    this.cargando = inicial;
    try {
      const state = await this.api.estado();
      if (this.destroyed) return;
      this.estado = state;
      if (state.cola_disponible) {
        const [history, restores] = await Promise.all([
          this.api.historial(this.pagina, this.filtro),
          this.api.restauraciones(),
        ]);
        if (this.destroyed) return;
        this.historial = history.items;
        this.total = history.total;
        this.restauraciones = restores;
        if (this.seleccion)
          this.seleccion = restores.find((r) => r.id === this.seleccion?.id) ?? this.seleccion;
      }
      if (state.control_disponible) {
        if (inicial) {
          const schedule = await this.api.programacion();
          this.programacion = { ...schedule.configuracion };
          this.proxima = schedule.next_run;
          if (schedule.advertencias?.length) this.notify(schedule.advertencias.join(' '));
        }
      }
    } catch (error) {
      await this.fail(error);
    } finally {
      this.refreshing = false;
      this.cargando = false;
      this.paint();
    }
  }
  async crear() {
    if (this.ocupada || !this.estado?.configurado || this.estado.mantenimiento) return;
    this.ocupada = 'crear';
    if (this.requestScope !== this.alcance) this.requestKey = null;
    this.requestKey ??= crypto.randomUUID();
    this.requestScope = this.alcance;
    try {
      const job = await this.api.crear(this.alcance, this.requestKey);
      this.requestKey = null;
      this.pagina = 1;
      this.filtro = '';
      this.notify(
        `Copia en cola (job ${job.id}). El daemon Oracle la procesará y el historial mostrará su resultado.`,
      );
      await this.actualizar();
    } catch (error) {
      await this.fail(error);
    } finally {
      this.ocupada = '';
      this.paint();
    }
  }
  async descargar(job: BackupJob) {
    if (this.destroyed || this.ocupada || !this.estado?.descarga_habilitada || job.estado !== 'COMPLETADO') return;
    this.ocupada = job.id;
    clearTimeout(this.downloadExpiry);
    this.descargaLista = null;
    this.notify(`Preparando descarga del job ${job.id}…`);
    try {
      let result = await this.api.descargar(job.id);
      const deadline = Date.now() + 120000;
      let attempts = 0;
      while (!this.destroyed && (result.estado === 'PENDIENTE' || result.estado === 'PROCESANDO')) {
        if (++attempts > 60 || Date.now() >= deadline) {
          this.notify('El servicio sigue preparando la descarga. Vuelve a pulsar Descargar para consultar la misma solicitud.', true);
          return;
        }
        await this.waitDownload();
        if (this.destroyed) return;
        result = await this.api.descarga(result.id);
      }
      if (this.destroyed) return;
      if (result.estado === 'FALLIDO' || result.estado === 'EXPIRADO') {
        this.notify(result.error || 'No se pudo preparar la descarga. Inténtalo nuevamente.', true);
        return;
      }
      const remaining = Date.parse(result.expira_en ?? '') - Date.now();
      if (result.estado !== 'COMPLETADO' || result.job_id !== job.id || !result.url || !(remaining > 0)) {
        this.notify('No hay un enlace vigente para esta copia. Solicita la descarga nuevamente.', true);
        return;
      }
      this.descargaLista = result;
      this.downloadExpiry = setTimeout(() => { this.descargaLista = null; this.paint(); }, remaining);
      // Navegación directa: el HttpClient autenticado nunca envía el JWT a OCI.
      const link = document.createElement('a');
      link.href = result.url;
      link.download = result.nombre;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.referrerPolicy = 'no-referrer';
      document.body.appendChild(link);
      link.click();
      link.remove();
      this.notify('Descarga preparada. Si no se abrió, usa el enlace temporal que aparece debajo del historial.');
    } catch (error) {
      await this.fail(error);
    } finally {
      this.ocupada = '';
      this.paint();
    }
  }
  async guardar() {
    if (this.ocupada || !this.estado?.control_disponible) return;
    this.ocupada = 'guardar';
    try {
      const result = await this.api.guardar(this.programacion);
      this.programacion = { ...result.configuracion };
      this.proxima = result.next_run;
      this.notify(
        this.programacion.habilitada
          ? 'Programación guardada. Un scheduler externo debe encolar las ocurrencias para el daemon Oracle.'
          : 'Programación pausada.',
      );
    } catch (error) {
      await this.fail(error);
    } finally {
      this.ocupada = '';
      this.paint();
    }
  }
  async despachar() {
    if (this.ocupada || !this.estado?.configurado || this.estado.mantenimiento) return;
    this.ocupada = 'despachar';
    try {
      const result = await this.api.despachar();
      this.notify(result.encolado ? `Ejecución automática en cola (job ${result.trabajo?.id}).` : 'No hay una ejecución programada vencida.');
      await this.actualizar();
    } catch (error) {
      await this.fail(error);
    } finally {
      this.ocupada = '';
      this.paint();
    }
  }
  private waitDownload(): Promise<void> {
    return new Promise((resolve) => {
      const timer = setTimeout(() => { this.cancelDownloadWait = undefined; resolve(); }, 2000);
      this.cancelDownloadWait = () => { clearTimeout(timer); this.cancelDownloadWait = undefined; resolve(); };
    });
  }
  async validar(archivo: string) {
    if (this.ocupada || !this.estado?.restauracion_habilitada || this.estado.mantenimiento) return;
    this.ocupada = 'validar';
    try {
      this.seleccion = await this.api.validar(archivo);
      this.confirmacion = '';
      this.password = '';
      this.notify(
        'Ensayo en cola. Se comprobará una base temporal antes de pedir la confirmación.',
      );
      await this.actualizar();
    } catch (error) {
      await this.fail(error);
    } finally {
      this.ocupada = '';
      this.paint();
    }
  }
  async importar(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file || this.ocupada || !this.estado?.importacion_habilitada) return;
    if (!file.name.endsWith('.obratec')) {
      this.notify('Selecciona un paquete cifrado .obratec.', true);
      input.value = '';
      return;
    }
    this.ocupada = 'importar';
    try {
      this.importado = await this.api.importar(file);
      this.notify('Paquete autenticado e importado. Ya puedes solicitar su ensayo.');
    } catch (error) {
      await this.fail(error);
    } finally {
      this.ocupada = '';
      input.value = '';
      this.paint();
    }
  }
  async aplicar() {
    const selected = this.seleccion;
    if (
      !selected ||
      !this.estado?.restauracion_habilitada ||
      this.estado.mantenimiento ||
      this.ocupada ||
      selected.estado !== 'VALIDADA' ||
      this.confirmacion !== selected.confirmacion_requerida ||
      !this.identificador ||
      !this.password
    )
      return;
    this.ocupada = 'aplicar';
    try {
      const fresh = await this.api.reautenticar(this.identificador, this.password);
      this.password = '';
      this.seleccion = await this.api.aplicar(
        selected.id,
        this.confirmacion,
        selected.desafio,
        fresh.token,
      );
      this.notify(
        'Solicitud de restauración confirmada. Consulta el resultado del servicio Oracle.',
      );
    } catch (error) {
      await this.fail(error);
    } finally {
      this.password = '';
      this.ocupada = '';
      this.paint();
    }
  }
  cambiarPagina(delta: number) {
    this.pagina += delta;
    void this.actualizar();
  }
  filtrar() {
    this.pagina = 1;
    void this.actualizar();
  }
  elegirRestore(row: BackupRestore) {
    this.seleccion = row;
    this.confirmacion = '';
    this.password = '';
  }
  scope(value: BackupScope) {
    return 'Schema obras';
  }
  size(value: number | null) {
    if (value === null) return 'Sin tamaño registrado';
    return value < 1024 ** 2
      ? (value / 1024).toFixed(1) + ' KiB'
      : (value / 1024 ** 2).toFixed(1) + ' MiB';
  }
}
