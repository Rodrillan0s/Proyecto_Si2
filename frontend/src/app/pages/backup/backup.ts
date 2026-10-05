import { ChangeDetectorRef, Component, inject, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  BackupArchive,
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
  private refreshing = false;
  private requestKey: string | null = null;
  private requestScope: BackupScope | null = null;
  estado: BackupStatus | null = null;
  historial: BackupJob[] = [];
  restauraciones: BackupRestore[] = [];
  seleccion: BackupRestore | null = null;
  alcance: BackupScope = 'sistema_completo';
  programacion: BackupSchedule = {
    habilitada: false,
    alcance: 'sistema_completo',
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
      if (state.control_disponible) {
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
        if (inicial) {
          const schedule = await this.api.programacion();
          this.programacion = { ...schedule.configuracion };
          this.proxima = schedule.next_run;
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
        `Copia en cola (${job.id.slice(0, 8)}). El historial mostrará sus etapas y permitirá descargarla al terminar.`,
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
    if (this.ocupada) return;
    this.ocupada = job.id;
    try {
      const response = await this.api.descargar(job.id);
      if (!response.body) throw new Error('Archivo ausente');
      const name =
        /filename="?([^";]+)"?/.exec(response.headers.get('Content-Disposition') ?? '')?.[1] ??
        `obratec_${job.id}.obratec`;
      const url = URL.createObjectURL(response.body);
      const link = document.createElement('a');
      link.href = url;
      link.download = name;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      this.notify(
        'Copia cifrada descargada. Conserva su clave de recuperación en un depósito separado.',
      );
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
          ? 'Programación guardada. Su ejecución depende del worker; revisa el estado operativo.'
          : 'Programación pausada.',
      );
    } catch (error) {
      await this.fail(error);
    } finally {
      this.ocupada = '';
      this.paint();
    }
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
    if (!file || this.ocupada) return;
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
        'Restauración global confirmada. Se generará una copia preventiva, entrará en mantenimiento y tendrás que iniciar sesión al finalizar.',
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
    return value === 'sistema_completo' ? 'Sistema completo' : 'Base de datos';
  }
  size(value: number) {
    return value < 1024 ** 2
      ? (value / 1024).toFixed(1) + ' KiB'
      : (value / 1024 ** 2).toFixed(1) + ' MiB';
  }
}
