import {
  ChangeDetectorRef,
  Component,
  DestroyRef,
  ElementRef,
  HostListener,
  OnDestroy,
  OnInit,
  ViewChild,
  effect,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AuthService } from '../../services/auth';
import { AsistenteService } from '../../services/asistente.service';
import {
  Execution,
  Interpretation,
  ReportCatalog,
  ReportesService,
  Work,
} from '../../services/reportes.service';
import { reportError, saveReportFile } from '../../services/reportes-ui';

interface Message {
  author: 'user' | 'assistant';
  text: string;
  query?: string;
  execution?: Execution;
  choices?: string[];
  works?: Work[];
  request?: Interpretation['solicitud'];
  topic?: string;
  executions?: Execution[];
}
interface Recognition {
  lang: string;
  interimResults: boolean;
  onresult: ((event: { results: { transcript: string }[][] }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}

@Component({
  selector: 'app-asistente',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './asistente.html',
  styleUrl: './asistente.css',
})
export class AsistenteComponent implements OnInit, OnDestroy {
  readonly ui = inject(AsistenteService);
  private auth = inject(AuthService);
  private api = inject(ReportesService);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);
  private destroy = inject(DestroyRef);
  @ViewChild('input') input?: ElementRef<HTMLTextAreaElement>;
  @ViewChild('log') log?: ElementRef<HTMLElement>;
  @ViewChild('launcher') launcher?: ElementRef<HTMLButtonElement>;
  messages: Message[] = [];
  text = '';
  error = '';
  busy = false;
  listening = false;
  voicePending = false;
  catalog?: ReportCatalog;
  private company: number | null = null;
  private version = 0;
  private conversation?: string;
  private loaded = false;
  historyFilter = 'todos';
  private voiceVersion = 0;
  private recognition?: Recognition;
  private recorder?: MediaRecorder;
  private stream?: MediaStream;
  private timer?: ReturnType<typeof setTimeout>;
  get available() {
    return (
      this.auth.hasPermission('Visualizar_reportes') ||
      this.auth.hasPermission('Visualizar_clientes')
    );
  }
  get canReports() {
    return this.auth.hasPermission('Visualizar_reportes');
  }
  get canCRM() {
    return this.auth.hasPermission('Visualizar_clientes');
  }
  get companyName() {
    return this.needsCompany ? 'Selecciona una empresa' : this.auth.obtenerNombreEmpresaActiva();
  }
  get needsCompany() {
    return !this.company && this.auth.obtenerRolNormalizado() === 'ADMINISTRADOR';
  }
  get suggestions() {
    const reports = this.catalog?.reportes ?? [];
    return [
      ...(reports.some((r) => r.id === 'saldo_comercial')
        ? ['¿Cuáles son las obras que han generado ganancias?']
        : []),
      ...reports.slice(0, 2).map((r) => r.titulo),
      ...(this.canCRM ? ['¿Cuántos prospectos están en negociación?'] : []),
    ];
  }
  get visibleMessages() {
    return this.historyFilter === 'todos'
      ? this.messages
      : this.messages.filter((m) => m.topic === this.historyFilter);
  }
  topicLabel(topic?: string) {
    return topic === 'crm'
      ? 'Clientes y ventas'
      : topic === 'finanzas'
        ? 'Finanzas'
        : 'Reportes y proyectos';
  }
  constructor() {
    effect(() => {
      const opened = this.ui.opened();
      const draft = this.ui.draft();
      if (draft !== null) {
        this.text = draft.slice(0, 2000);
        this.ui.draft.set(null);
      }
      if (opened) {
        if (!this.loaded && this.canReports && !this.needsCompany) void this.loadCatalog();
        setTimeout(() => this.input?.nativeElement.focus());
      } else this.cancelVoice();
    });
  }
  ngOnInit() {
    this.auth.empresaActiva$.pipe(takeUntilDestroyed(this.destroy)).subscribe(() => {
      this.version++;
      this.company = this.auth.obtenerIdEmpresaActiva();
      this.messages = [];
      this.text = '';
      this.error = '';
      this.busy = false;
      this.catalog = undefined;
      this.loaded = false;
      this.conversation = undefined;
      this.cancelVoice();
      this.ui.draft.set(null);
      this.historyFilter = 'todos';
      if (this.ui.opened() && this.canReports && !this.needsCompany) void this.loadCatalog();
      this.cdr.markForCheck();
    });
  }
  ngOnDestroy() {
    this.version++;
    this.cancelVoice();
    this.ui.close();
  }
  private async loadCatalog() {
    this.loaded = true;
    const version = this.version;
    try {
      const catalog = await this.api.catalog(this.company);
      if (version === this.version) this.catalog = catalog;
    } catch (error) {
      if (version === this.version) {
        this.loaded = false;
        this.error = reportError(error);
      }
    }
    this.cdr.markForCheck();
  }
  close() {
    this.ui.close();
    this.launcher?.nativeElement.focus();
  }
  onEnter(event: Event) {
    const key = event as KeyboardEvent;
    if (!key.shiftKey && !key.isComposing) {
      key.preventDefault();
      void this.send();
    }
  }
  @HostListener('document:keydown.escape') onEscape() {
    if (this.ui.opened()) this.close();
  }
  async send(text = this.text) {
    text = text.trim();
    if (!text || this.busy || this.listening || this.voicePending || this.needsCompany) return;
    if (text.length > 2000) {
      this.error = 'La consulta debe tener hasta 2.000 caracteres.';
      return;
    }
    const version = this.version;
    this.busy = true;
    this.error = '';
    this.text = '';
    this.historyFilter = 'todos';
    const userMessage: Message = { author: 'user', text };
    this.messages.push(userMessage);
    this.update();
    try {
      const response = await this.api.assistant(text, this.company, this.conversation);
      if (version !== this.version) return;
      this.conversation = response.conversacion;
      userMessage.topic = response.tema || 'reportes';
      this.messages.push({
        author: 'assistant',
        text: response.respuesta || response.mensaje,
        query: text,
        execution: response.ejecucion,
        choices: response.opciones,
        works: response.obras,
        request: response.solicitud,
        topic: response.tema || 'reportes',
        executions: response.ejecuciones ?? (response.ejecucion ? [response.ejecucion] : []),
      });
    } catch (error) {
      if (version === this.version) {
        this.error = reportError(error);
        this.text = text;
      }
    } finally {
      if (version === this.version) {
        this.busy = false;
        this.update();
      }
    }
  }
  async selectWork(message: Message, work: Work) {
    if (!message.request) {
      await this.send((message.query || 'Reporte de avance') + ' de la obra ' + work.nombre);
      return;
    }
    if (this.busy) return;
    const version = this.version;
    this.busy = true;
    this.error = '';
    try {
      const response = await this.api.assistant(work.nombre, this.company, this.conversation, {
        ...message.request,
        filtros: { ...message.request.filtros, id_obra: work.id_obra },
      });
      if (version === this.version) {
        this.conversation = response.conversacion;
        this.messages.push(
          { author: 'user', text: work.nombre, topic: response.tema || 'reportes' },
          {
            author: 'assistant',
            text: response.respuesta || response.mensaje,
            execution: response.ejecucion,
            executions: response.ejecuciones,
            choices: response.opciones,
            works: response.obras,
            request: response.solicitud,
            topic: response.tema || 'reportes',
          },
        );
        message.works = [];
      }
    } catch (error) {
      if (version === this.version) this.error = reportError(error);
    } finally {
      if (version === this.version) {
        this.busy = false;
        this.update();
      }
    }
  }
  async view(execution: Execution) {
    await this.router.navigate(['/reportes'], { queryParams: { ejecucion: execution.id } });
    this.close();
  }
  async download(execution: Execution, format: 'pdf' | 'xlsx') {
    if (this.busy) return;
    const version = this.version;
    this.busy = true;
    this.error = '';
    try {
      const file = await this.api.download(execution.id, format);
      if (version === this.version) saveReportFile(file);
    } catch (error) {
      if (version === this.version) this.error = reportError(error);
    } finally {
      if (version === this.version) {
        this.busy = false;
        this.cdr.markForCheck();
      }
    }
  }
  private update() {
    this.cdr.markForCheck();
    setTimeout(() => {
      const log = this.log?.nativeElement;
      if (log) log.scrollTop = log.scrollHeight;
    });
  }
  async voice() {
    if (this.busy || this.voicePending || this.needsCompany) return;
    if (this.listening) {
      this.recognition?.stop();
      this.finishRecording();
      return;
    }
    this.error = '';
    const version = ++this.voiceVersion;
    const constructors = window as unknown as {
      SpeechRecognition?: new () => Recognition;
      webkitSpeechRecognition?: new () => Recognition;
    };
    const Constructor = constructors.SpeechRecognition ?? constructors.webkitSpeechRecognition;
    if (Constructor) {
      const recognition = new Constructor();
      this.recognition = recognition;
      recognition.lang = 'es-BO';
      recognition.interimResults = false;
      recognition.onresult = (event) => {
        if (version === this.voiceVersion) {
          this.text = event.results[0][0].transcript.slice(0, 2000);
          this.cdr.markForCheck();
        }
      };
      recognition.onerror = () => {
        if (version === this.voiceVersion) {
          this.error = 'Revisa el permiso del micrófono o escribe tu consulta.';
          this.cancelVoice();
          this.cdr.markForCheck();
        }
      };
      recognition.onend = () => {
        if (version === this.voiceVersion) {
          this.listening = false;
          clearTimeout(this.timer);
          this.cdr.markForCheck();
        }
      };
      try {
        recognition.start();
        this.listening = true;
        this.timer = setTimeout(() => recognition.stop(), 60000);
      } catch {
        this.error = 'No se pudo iniciar el micrófono. Puedes escribir tu consulta.';
      }
    } else {
      this.voicePending = true;
      this.cdr.markForCheck();
      try {
        if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined')
          throw new Error('unavailable');
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        if (version !== this.voiceVersion) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        this.stream = stream;
        const recorder = new MediaRecorder(stream);
        this.recorder = recorder;
        const chunks: BlobPart[] = [];
        recorder.ondataavailable = (event) => {
          if (event.data.size) chunks.push(event.data);
        };
        recorder.onstop = async () => {
          stream.getTracks().forEach((track) => track.stop());
          if (version !== this.voiceVersion) return;
          const blob = new Blob(chunks, { type: recorder.mimeType || 'audio/webm' });
          this.voicePending = true;
          this.cdr.markForCheck();
          try {
            if (blob.size > 5 * 1024 * 1024) {
              this.error = 'La grabación supera 5 MB. Graba una consulta más corta.';
              return;
            }
            const response = await this.api.transcribe(blob, this.company);
            if (version === this.voiceVersion) this.text = response.texto.slice(0, 2000);
          } catch (error) {
            if (version === this.voiceVersion) this.error = reportError(error);
          } finally {
            if (version === this.voiceVersion) {
              this.voicePending = false;
              this.cdr.markForCheck();
            }
          }
        };
        recorder.start();
        this.listening = true;
        this.voicePending = false;
        this.timer = setTimeout(() => this.finishRecording(), 60000);
      } catch {
        if (version === this.voiceVersion) {
          this.cancelVoice();
          this.error = 'El micrófono no está disponible. Puedes escribir tu consulta.';
        }
      }
    }
    this.cdr.markForCheck();
  }
  private finishRecording() {
    clearTimeout(this.timer);
    if (this.recorder?.state === 'recording') this.recorder.stop();
    this.listening = false;
    this.cdr.markForCheck();
  }
  private cancelVoice() {
    this.voiceVersion++;
    clearTimeout(this.timer);
    try {
      this.recognition?.stop();
    } catch {
      /* El navegador puede haber terminado la captura. */
    }
    this.recognition = undefined;
    if (this.recorder?.state === 'recording') this.recorder.stop();
    this.stream?.getTracks().forEach((track) => track.stop());
    this.recorder = undefined;
    this.stream = undefined;
    this.listening = false;
    this.voicePending = false;
  }
}
