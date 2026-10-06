import { ContextoOperativo } from '../../services/contexto-operativo';
import { REPORT_FAMILIES } from '../../layouts/admin-layout/navegacion';
import { Component, OnInit, OnDestroy, inject, ChangeDetectorRef, DestroyRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { interval } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AuthService } from '../../services/auth';
import { AsistenteService } from '../../services/asistente.service';
import { reportError, saveReportFile } from '../../services/reportes-ui';
import {
  ReportesService,
  ReportCatalog,
  ReportDefinition,
  ReportFilters,
  ReportRequest,
  ReportPresentation,
  Execution,
  Interpretation,
  Recipient,
  ReportSchedule,
  ReportDelivery,
} from '../../services/reportes.service';

@Component({
  selector: 'app-reportes',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './reportes.html',
  styleUrls: ['./reportes-results.css', './reportes.css', './reportes-personalizacion.css'],
})
export class ReportesComponent implements OnInit, OnDestroy {
  private contexto = inject(ContextoOperativo);
  family = '';
  auxiliaryError = '';
  auxiliaryLoading = false;
  private auxiliary = new Set<string>();
  private auxiliaryPending = new Map<string, Promise<void>>();
  get reportOptions() { return this.family ? this.catalog.reportes.filter(report => REPORT_FAMILIES[this.family]?.includes(report.id)) : this.catalog.reportes; }
  private navigationFilters() {
    if (!this.reportOptions.some(report => report.id === this.selected)) this.selected = this.reportOptions[0]?.id || '';
    const work = this.contexto.obra?.id_obra || Number(this.route?.snapshot.queryParamMap.get('id_obra'));
    if (work && this.catalog.obras.some(item => item.id_obra === work)) this.work = work;
  }
  changeTab(tab: 'generar' | 'historial' | 'programaciones') {
    this.tab = tab;
    if (tab !== 'generar') void this.loadAuxiliary(tab);
  }
  private loadAuxiliary(kind: 'historial' | 'programaciones' | 'destinatarios', force = false): Promise<void> {
    if ((!force && this.auxiliary.has(kind)) || this.needsCompany) return Promise.resolve();
    const pending = this.auxiliaryPending.get(kind); if (pending) return pending;
    const version = this.generation; this.auxiliaryLoading = true; this.auxiliaryError = '';
    const task = (async () => {
      try {
        if (kind === 'historial') { const data = await this.api.history(this.company); if (version === this.generation) this.history = data; }
        if (kind === 'programaciones' && this.can('Programar_reportes')) { const data = await this.api.schedules(this.company); if (version === this.generation) this.schedules = data; }
        if (kind === 'destinatarios' && this.can('Enviar_reportes')) { const data = await this.api.recipients(this.company); if (version === this.generation) this.recipients = data; }
        if (version === this.generation) this.auxiliary.add(kind);
      } catch (error) { if (version === this.generation) this.auxiliaryError = reportError(error); }
      finally { if (version === this.generation) { this.auxiliaryPending.delete(kind); this.auxiliaryLoading = this.auxiliaryPending.size > 0; this.cdr.markForCheck(); } }
    })();
    this.auxiliaryPending.set(kind, task); return task;
  }
  retryAuxiliary() { void this.loadAuxiliary(this.tab === 'generar' ? 'destinatarios' : this.tab, true); }
  prepareDelivery() { void this.loadAuxiliary('destinatarios'); }

  private api = inject(ReportesService);
  private auth = inject(AuthService);
  private cdr = inject(ChangeDetectorRef);
  private destroy = inject(DestroyRef);
  private route = inject(ActivatedRoute, { optional: true });
  readonly asistente = inject(AsistenteService);
  private router = inject(Router, { optional: true });
  catalog: ReportCatalog = { reportes: [], obras: [], acciones: [], id_empresa: 0 };
  selected = '';
  work: number | null = null;
  desde = '';
  hasta = '';
  estado = '';
  query = '';
  texto = '';
  busy = false;
  loading = false;
  error = '';
  notice = '';
  response?: Interpretation;
  execution?: Execution;
  tab: 'generar' | 'historial' | 'programaciones' = 'generar';
  advanced = false;
  history: Execution[] = [];
  recipients: Recipient[] = [];
  receiverIds: number[] = [];
  schedules: ReportSchedule[] = [];
  deliveries: ReportDelivery[] = [];
  frequency = 'diaria';
  hour = '08:00';
  timezone = 'America/La_Paz';
  day = 1;
  period = 'fijo';
  formato = 'pdf';
  page = 1;
  priority: ReportFilters['prioridad'] | '' = '';
  category: number | null = null;
  customTitle = '';
  orientation: 'vertical' | 'horizontal' = 'horizontal';
  sortField = '';
  sortOrder: 'asc' | 'desc' = 'asc';
  customColumns = false;
  selectedColumns: string[] = [];
  datePreset = 'todo';
  get columnChoices() {
    return this.definition?.campos?.length
      ? this.definition.campos
      : this.result?.solicitud.reporte === this.selected
        ? (this.result.columnas_disponibles ?? this.result.columnas)
        : [];
  }
  toggleColumn(field: string, enabled: boolean) {
    this.selectedColumns = enabled
      ? [...this.selectedColumns, field]
      : this.selectedColumns.filter((k) => k !== field);
  }
  enableColumns() {
    if (this.customColumns && !this.selectedColumns.length)
      this.selectedColumns = this.columnChoices.map((c) => c.campo);
  }
  moveColumn(field: string, direction: number) {
    const from = this.selectedColumns.indexOf(field),
      to = from + direction;
    if (from < 0 || to < 0 || to >= this.selectedColumns.length) return;
    [this.selectedColumns[from], this.selectedColumns[to]] = [
      this.selectedColumns[to],
      this.selectedColumns[from],
    ];
  }
  setPeriod() {
    const today = new Date();
    const start = new Date(today);
    const end = new Date(today);
    if (this.datePreset === 'todo') {
      this.desde = '';
      this.hasta = '';
      return;
    }
    if (this.datePreset === 'manual') return;
    if (this.datePreset === '7') start.setDate(start.getDate() - 6);
    if (this.datePreset === '30') start.setDate(start.getDate() - 29);
    if (this.datePreset === 'mes') start.setDate(1);
    if (this.datePreset === 'anterior') {
      start.setDate(1);
      start.setMonth(start.getMonth() - 1);
      end.setDate(0);
    }
    const iso = (value: Date) =>
      `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`;
    this.desde = iso(start);
    this.hasta = iso(end);
  }
  request(): ReportRequest {
    const presentation: ReportPresentation = {};
    if (this.customTitle.trim()) presentation.titulo = this.customTitle.trim();
    if (this.orientation !== 'horizontal') presentation.orientacion = this.orientation;
    if (this.customColumns) presentation.columnas = [...this.selectedColumns];
    if (this.sortField) {
      presentation.ordenar_por = this.sortField;
      presentation.orden = this.sortOrder;
    }
    return {
      reporte: this.selected,
      filtros: this.filters(),
      ...(Object.keys(presentation).length ? { presentacion: presentation } : {}),
    };
  }
  resetPresentation() {
    this.customTitle = '';
    this.orientation = 'horizontal';
    this.sortField = '';
    this.sortOrder = 'asc';
    this.customColumns = false;
    this.selectedColumns = [];
    this.datePreset = 'todo';
  }
  private company: number | null = null;
  private generation = 0;
  private conversation?: string;
  private sendKeys = new Map<string, string>();
  private routeId: string | null = null;
  get pages() {
    return Math.max(1, Math.ceil((this.result?.filas.length ?? 0) / 50));
  }
  get visibleRows() {
    return this.result?.filas.slice((this.page - 1) * 50, this.page * 50) ?? [];
  }
  get definition(): ReportDefinition | undefined {
    return this.catalog.reportes.find((r) => r.id === this.selected);
  }
  get result() {
    return this.execution?.resultado;
  }
  get companyName() {
    return this.auth.obtenerNombreEmpresaActiva?.() || 'Empresa activa';
  }
  get needsCompany() {
    return !this.company && this.auth.obtenerRolNormalizado?.() === 'ADMINISTRADOR';
  }
  get validation() {
    if (this.customColumns && !this.selectedColumns.length)
      return 'Selecciona al menos una columna.';
    if (this.customTitle.trim().length > 120) return 'El título admite hasta 120 caracteres.';
    if (!this.definition) return 'Selecciona un reporte.';
    if (this.definition.requiere_obra && !this.work)
      return 'Este reporte necesita una obra. Selecciónala para continuar.';
    if (this.definition.fechas && this.desde && this.hasta && this.desde > this.hasta)
      return 'La fecha inicial debe ser anterior o igual a la fecha final.';
    if (this.query.trim().length > 120) return 'La búsqueda admite hasta 120 caracteres.';
    if (
      this.selected === 'stock' &&
      this.category !== null &&
      (!Number.isInteger(+this.category) || +this.category < 1)
    )
      return 'La categoría debe ser un número entero positivo.';
    return '';
  }
  get scheduleValidation() {
    if (this.validation) return this.validation;
    if (!this.can('Enviar_reportes'))
      return 'Se necesita permiso de envío para crear una programación.';
    if (!this.receiverIds.length) return 'Selecciona al menos un destinatario.';
    if (this.receiverIds.length > 30) return 'Selecciona como máximo 30 destinatarios por envío.';
    if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(this.hour)) return 'Selecciona una hora válida.';
    if (
      this.frequency !== 'diaria' &&
      (!Number.isInteger(+this.day) ||
        +this.day < 1 ||
        +this.day > (this.frequency === 'semanal' ? 7 : 31))
    )
      return 'Revisa el día de la programación.';
    try {
      new Intl.DateTimeFormat('es', { timeZone: this.timezone }).format();
    } catch {
      return 'Escribe una zona horaria válida, por ejemplo America/La_Paz.';
    }
    return '';
  }
  can(action: string) {
    return this.catalog.acciones.includes(action);
  }
  reportTitle(id?: string) {
    return (
      this.catalog.reportes.find((r) => r.id === id)?.titulo ||
      id?.replaceAll('_', ' ') ||
      'Reporte'
    );
  }
  scheduleTitle(item: ReportSchedule) {
    return this.reportTitle(
      (item.configuracion['solicitud'] as ReportRequest | undefined)?.reporte,
    );
  }
  recipientName(id: number) {
    return this.recipients.find((r) => r.id_usuario === id)?.nombre || 'Destinatario autorizado';
  }
  status(value: string) {
    const labels: Record<string, string> = {
      LISTO: 'Listo',
      COMPLETADO: 'Completado',
      PENDIENTE: 'Pendiente',
      PROCESANDO: 'Procesando',
      GENERANDO: 'Generando',
      ENVIANDO: 'Enviando',
      ACEPTADO: 'Aceptado por Brevo',
      FALLIDO: 'Falló',
      INCIERTO: 'Resultado incierto',
      ACTIVA: 'Activa',
      PAUSADA: 'Pausada',
    };
    return labels[value] || value?.replaceAll('_', ' ').toLowerCase();
  }
  display(value: unknown): string {
    if (value === null || value === undefined) return '—';
    if (typeof value === 'object')
      return Object.entries(value)
        .map(([key, item]) => `${key.replaceAll('_', ' ')}: ${this.display(item)}`)
        .join(' · ');
    return String(value);
  }
  ngOnInit() {
    this.contexto.protegerEscritura(() => this.busy, this.destroy);
    this.contexto.proteger(() => this.receiverIds.length > 0, this.destroy);
    this.contexto.empresa$.pipe(takeUntilDestroyed(this.destroy)).subscribe(() => {
      this.company = this.auth.obtenerIdEmpresaActiva();
      this.generation++;
      this.auxiliary.clear(); this.auxiliaryPending.clear(); this.auxiliaryLoading = false; this.auxiliaryError = '';
      this.busy = false;
      this.loading = false;
      if (this.generation > 1) this.routeId = null;
      this.execution = undefined;
      this.response = undefined;
      this.conversation = undefined;
      this.sendKeys.clear();
      this.receiverIds = [];
      this.recipients = [];
      this.history = [];
      this.schedules = [];
      this.deliveries = [];
      this.catalog = { reportes: [], obras: [], acciones: [], id_empresa: 0 };
      this.selected = '';
      this.resetPresentation();
      this.work = null;
      this.texto = '';
      this.query = '';
      this.estado = '';
      this.priority = '';
      this.category = null;
      this.desde = '';
      this.hasta = '';
      this.period = 'fijo';
      this.error = '';
      this.notice = '';
      this.tab = 'generar';
      void this.load();
    });
    this.route?.queryParamMap.pipe(takeUntilDestroyed(this.destroy)).subscribe((params) => {
      const family = params.get('familia') || '';
      if (this.family !== family) { this.family = REPORT_FAMILIES[family] ? family : ''; if (!params.get('ejecucion')) this.changeReport(); }
      this.navigationFilters();
      this.routeId = params.get('ejecucion');
      if (this.routeId && this.catalog.reportes.length && !this.loading) this.open(this.routeId);
    });
    this.contexto.obra$.pipe(takeUntilDestroyed(this.destroy)).subscribe(obra => {
      const id = obra?.id_obra || null;
      if (id === this.work) return;
      this.work = id && this.catalog.obras.some(work => work.id_obra === id) ? id : null;
      this.changeReport(); this.cdr.markForCheck();
    });
    interval(15000)
      .pipe(takeUntilDestroyed(this.destroy))
      .subscribe(() => {
        if (
          !this.busy &&
          !this.loading &&
          document.visibilityState !== 'hidden' &&
          this.catalog.reportes.length &&
          (this.deliveries.some((d) => ['PENDIENTE', 'ENVIANDO'].includes(d.estado)) ||
            this.history.some((e) => ['PENDIENTE', 'PROCESANDO', 'GENERANDO'].includes(e.estado)))
        )
          void this.refreshPending();
      });
  }
  ngOnDestroy() {
    this.generation++;
  }
  async perform(action: () => Promise<void>) {
    if (this.busy || this.loading || this.needsCompany) return;
    this.busy = true;
    this.error = '';
    this.notice = '';
    const version = this.generation;
    try {
      await action();
    } catch (error) {
      if (version === this.generation) this.error = reportError(error);
    } finally {
      if (version === this.generation) {
        this.busy = false;
        this.cdr.markForCheck();
        if (this.routeId && this.execution?.id !== this.routeId) this.open(this.routeId);
      }
    }
  }
  async load() {
    if (this.loading || this.busy || this.needsCompany) return;
    const version = this.generation;
    this.loading = true;
    this.error = '';
    try {
      const catalog = await this.api.catalog(this.company);
      if (version !== this.generation) return;
      this.catalog = catalog;
      if (!catalog.reportes.some((r) => r.id === this.selected))
        this.selected = catalog.reportes[0]?.id ?? '';
      if (!catalog.obras.some((w) => w.id_obra === this.work)) this.work = null;
      this.navigationFilters();
      this.auxiliary.clear();
      if (this.tab !== 'generar') void this.loadAuxiliary(this.tab, true);
      if (this.execution) this.prepareDelivery();
    } catch (error) {
      if (version === this.generation) this.error = reportError(error);
    } finally {
      if (version === this.generation) {
        this.loading = false;
        this.cdr.markForCheck();
        if (this.routeId && this.execution?.id !== this.routeId && this.catalog.reportes.length)
          this.open(this.routeId);
      }
    }
  }
  private async refreshPending() {
    await this.perform(async () => {
      const version = this.generation;
      const history = await this.api.history(this.company);
      if (version !== this.generation) return;
      this.history = history;
      if (this.execution) {
        const execution = await this.api.execution(this.execution.id);
        if (version !== this.generation) return;
        this.execution = execution;
      this.prepareDelivery();
        if (this.can('Enviar_reportes')) {
          const deliveries = await this.api.deliveries(execution.id);
          if (version !== this.generation) return;
          this.deliveries = deliveries;
        }
      }
    });
  }
  filters(): ReportFilters {
    const filters: ReportFilters = {};
    if (this.work && this.selected !== 'stock') filters.id_obra = +this.work;
    if (this.definition?.fechas) {
      if (this.desde) filters.desde = this.desde;
      if (this.hasta) filters.hasta = this.hasta;
    }
    if (this.estado.trim()) filters.estado = this.estado.trim();
    if (this.query.trim()) filters.q = this.query.trim();
    if (this.selected === 'incidencias_criticas') filters.prioridad = 'CRITICA';
    else if (this.priority && this.selected === 'incidencias') filters.prioridad = this.priority;
    if (this.category && this.selected === 'stock') filters.id_categoria = +this.category;
    return filters;
  }
  private clearExecutionLink() {
    this.routeId = null;
    if (this.route?.snapshot.queryParamMap.has('ejecucion'))
      void this.router?.navigate([], {
        relativeTo: this.route,
        queryParams: { ejecucion: null },
        queryParamsHandling: 'merge',
        replaceUrl: true,
      });
  }
  changeReport() {
    if (this.catalog.reportes.length && !this.loading) {
      this.generation++; this.busy = false;
      this.auxiliary.clear(); this.auxiliaryPending.clear(); this.auxiliaryLoading = false;
    }
    this.resetPresentation();
    this.clearExecutionLink();
    this.response = undefined;
    this.execution = undefined;
    this.deliveries = [];
    this.page = 1;
    this.period = 'fijo';
    this.desde = '';
    this.hasta = '';
    this.estado = '';
    this.priority = '';
    this.category = null;
    this.query = '';
  }
  private applyRequest(request: ReportRequest) {
    this.resetPresentation();
    const p = request.presentacion;
    this.customTitle = p?.titulo ?? '';
    this.orientation = p?.orientacion ?? 'horizontal';
    this.sortField = p?.ordenar_por ?? '';
    this.sortOrder = p?.orden ?? 'asc';
    this.selectedColumns = [...(p?.columnas ?? [])];
    this.customColumns = !!this.selectedColumns.length;
    this.selected = request.reporte;
    const f = request.filtros;
    this.work = f.id_obra ?? null;
    this.desde = f.desde ?? '';
    this.hasta = f.hasta ?? '';
    this.datePreset = this.desde || this.hasta ? 'manual' : 'todo';
    this.estado = f.estado ?? '';
    this.priority = f.prioridad ?? '';
    this.category = f.id_categoria ?? null;
    this.query = f.q ?? '';
    this.period = 'fijo';
  }
  interpret() {
    if (!this.texto.trim()) return;
    void this.perform(async () => {
      const version = this.generation;
      const response = await this.api.interpret(this.texto.trim(), this.company, this.conversation);
      if (version !== this.generation) return;
      this.response = response;
      this.conversation = response.conversacion;
      this.execution = undefined;
      this.deliveries = [];
      if (response.solicitud) this.applyRequest(response.solicitud);
    });
  }
  choose(title: string) {
    const report = this.catalog.reportes.find((r) => r.titulo === title);
    if (report) {
      this.selected = report.id;
      this.changeReport();
    }
  }
  generate() {
    if (this.validation) {
      this.error = this.validation;
      return;
    }
    if (this.busy || this.loading) return;
    this.clearExecutionLink();
    void this.perform(async () => {
      const version = this.generation;
      const execution = await this.api.create(this.request(), this.company);
      if (version !== this.generation) return;
      this.execution = execution;
      this.prepareDelivery();
      this.page = 1;
      this.deliveries = [];
      this.response = undefined;
      const history = await this.api.history(this.company);
      if (version === this.generation) this.history = history;
    });
  }
  open(id: string) {
    if (this.busy || this.loading) return;
    this.routeId = null;
    void this.perform(async () => {
      const version = this.generation;
      const execution = await this.api.execution(id);
      if (version !== this.generation) return;
      this.execution = execution;
      this.prepareDelivery();
      this.page = 1;
      this.tab = 'generar';
      this.deliveries = [];
      const request = execution.resultado?.solicitud || execution.solicitud;
      if (request) this.applyRequest(request);
      if (this.can('Enviar_reportes')) {
        const deliveries = await this.api.deliveries(id);
        if (version === this.generation) this.deliveries = deliveries;
      }
    });
  }
  download(format: 'pdf' | 'xlsx') {
    void this.perform(async () => {
      if (!this.execution || !this.result) return;
      const version = this.generation;
      const file = await this.api.download(this.execution.id, format);
      if (version === this.generation) saveReportFile(file);
    });
  }
  toggleReceiver(id: number, event: Event) {
    this.receiverIds = (event.target as HTMLInputElement).checked
      ? [...new Set([...this.receiverIds, id])]
      : this.receiverIds.filter((value) => value !== id);
  }
  send() {
    if (!this.execution || !this.result || !this.receiverIds.length) return;
    if (this.receiverIds.length > 30) {
      this.error = 'Selecciona como máximo 30 destinatarios por envío.';
      return;
    }
    void this.perform(async () => {
      const version = this.generation;
      const id = this.execution!.id;
      const fingerprint = JSON.stringify([
        id,
        [...this.receiverIds].sort((a, b) => a - b),
        this.formato,
      ]);
      let key = this.sendKeys.get(fingerprint);
      if (!key) {
        key = crypto.randomUUID();
        this.sendKeys.set(fingerprint, key);
      }
      await this.api.send(id, [...this.receiverIds], [this.formato], key);
      if (version !== this.generation) return;
      this.notice =
        'Solicitud de envío registrada. Consulta su estado aquí; pendiente todavía no significa enviado.';
      const deliveries = await this.api.deliveries(id);
      if (version === this.generation) this.deliveries = deliveries;
    });
  }
  saveSchedule() {
    if (this.scheduleValidation) {
      this.error = this.scheduleValidation;
      return;
    }
    void this.perform(async () => {
      const version = this.generation;
      await this.api.schedule(
        {
          solicitud: this.request(),
          destinatarios: [...this.receiverIds],
          formatos: [this.formato],
          frecuencia: this.frequency,
          hora: this.hour,
          zona: this.timezone,
          dia: +this.day,
          periodo: this.period,
          habilitada: true,
        },
        this.company,
      );
      if (version !== this.generation) return;
      const schedules = await this.api.schedules(this.company);
      if (version !== this.generation) return;
      this.schedules = schedules;
      this.notice = 'Programación guardada. Los envíos se procesarán en el horario seleccionado.';
      this.tab = 'programaciones';
    });
  }
  pause(item: ReportSchedule) {
    void this.perform(async () => {
      const version = this.generation;
      await this.api.pause(item.id, !item.habilitada);
      if (version !== this.generation) return;
      const schedules = await this.api.schedules(this.company);
      if (version === this.generation) this.schedules = schedules;
    });
  }
  run(item: ReportSchedule) {
    if (!item.habilitada) return;
    void this.perform(async () => {
      const version = this.generation;
      await this.api.run(item.id);
      if (version !== this.generation) return;
      const history = await this.api.history(this.company);
      if (version !== this.generation) return;
      this.history = history;
      this.notice = 'Ejecución solicitada. Revisa su estado en Historial.';
    });
  }
}
