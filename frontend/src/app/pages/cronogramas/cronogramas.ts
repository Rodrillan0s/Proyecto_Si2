import { Component, DestroyRef, HostListener, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { skip } from 'rxjs';
import { CronogramaService, Cronograma, PlanDraft, ActividadPlan } from '../../services/cronograma.service';
import { ProyectosService, Proyecto } from '../../services/proyectos';
import { AuthService } from '../../services/auth';
import { ContextoOperativo } from '../../services/contexto-operativo';
import { LecturasVigentes } from '../../services/lecturas';

@Component({ selector: 'app-cronogramas', imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './cronogramas.html', styleUrl: './cronogramas.css' })
export class CronogramasComponent implements OnInit {
  private api = inject(CronogramaService);
  private proyectos = inject(ProyectosService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private destroy = inject(DestroyRef);
  private contexto = inject(ContextoOperativo);
  private reads = new LecturasVigentes(this.destroy);
  auth = inject(AuthService);
  idObra = 0;
  obra = signal('');
  obras = signal<Proyecto[]>([]);
  planes = signal<Cronograma[]>([]);
  actual = signal<Cronograma | null>(null);
  cargando = signal(false);
  guardando = signal(false);
  error = signal('');
  mensaje = signal('');
  editor = signal(false);
  borrador: PlanDraft = this.vacio();
  editId: number | null = null;
  desde = ''; hasta = ''; corte = this.hoy(); soloRetrasos = false;
  get puedeCrear() { return this.auth.hasPermission('Registrar_cronograma'); }
  get puedeCabecera() { return this.editId === null ? this.puedeCrear : this.auth.hasPermission('Modificar_cronograma'); }
  get puedePlanificar() { return this.auth.hasPermission('Planificar_cronograma'); }

  ngOnInit() {
    this.contexto.proteger(() => this.editor(), this.destroy);
    this.contexto.protegerEscritura(() => this.guardando(), this.destroy);
    this.auth.empresaActiva$.pipe(skip(1), takeUntilDestroyed(this.destroy)).subscribe(() => {
      this.reads.cancelar(); this.editor.set(false); this.actual.set(null); this.planes.set([]);
      this.router.navigate(['/cronogramas']);
      if (!this.idObra) this.cargarObras();
    });
    this.route.paramMap.pipe(takeUntilDestroyed(this.destroy)).subscribe(params => {
      this.reads.cancelar(); this.idObra = Number(params.get('id') || 0);
      this.actual.set(null); this.planes.set([]); this.editor.set(false);
      if (this.idObra) this.cargar(); else this.cargarObras();
    });
  }
  hoy() { return new Intl.DateTimeFormat('sv-SE', { timeZone: 'America/La_Paz' }).format(new Date()); }
  vacio(): PlanDraft { return { nombre: '', descripcion: '', fecha_inicio: this.hoy(), fecha_fin: this.hoy(), actividades: [] }; }
  salir() { return !this.guardando() && (!this.editor() || window.confirm('¿Descartar los cambios del cronograma?')); }
  @HostListener('window:beforeunload', ['$event']) antesSalir(event: BeforeUnloadEvent) {
    if (this.editor() || this.guardando()) { event.preventDefault(); event.returnValue = ''; }
  }
  cargarObras() {
    this.cargando.set(true); this.error.set('');
    this.proyectos.listarProyectos().pipe(this.reads.reemplazar('obras')).subscribe({
      next: r => { const empresa = this.auth.obtenerIdEmpresaActiva(); this.obras.set(r.data.filter(p => !empresa || Number(p.id_empresa) === empresa)); this.cargando.set(false); },
      error: e => this.fallo(e),
    });
  }
  elegirObra(id: string) { if (id) this.router.navigate(['/proyectos', id, 'cronogramas']); }
  cargar(seleccionar?: number) {
    this.cargando.set(true); this.error.set('');
    this.api.listarCronogramas(this.idObra).pipe(this.reads.reemplazar('lista')).subscribe({
      next: r => { this.planes.set(r.data); this.obra.set(r.obra?.nombre || `Obra ${this.idObra}`); this.cargando.set(false);
        const id = seleccionar || r.data[0]?.id_cronograma; if (id) this.abrir(id); else this.actual.set(null); },
      error: e => this.fallo(e),
    });
  }
  abrir(id: number) {
    if (this.editor() && !this.salir()) return;
    const anterior = this.actual();
    this.editor.set(false); this.cargando.set(true); this.error.set(''); this.actual.set(null);
    const filtros: Record<string, string> = {};
    if (this.desde) filtros['desde'] = this.desde;
    if (this.hasta) filtros['hasta'] = this.hasta;
    if (this.corte) filtros['corte'] = this.corte;
    this.api.obtener(this.idObra, id, filtros).pipe(this.reads.reemplazar('detalle')).subscribe({
      next: r => { this.actual.set(r.data); this.cargando.set(false); }, error: e => {
        if (anterior?.id_cronograma === id) this.actual.set(anterior);
        this.fallo(e);
      },
    });
  }
  filtrar() { const id = this.actual()?.id_cronograma; if (id) this.abrir(id); }
  nuevo() {
    if (this.editor() && !this.salir()) return;
    this.borrador = this.vacio(); this.editId = null; this.error.set(''); this.mensaje.set(''); this.editor.set(true);
  }
  editar() {
    const plan = this.actual(); if (!plan) return;
    this.borrador = structuredClone(plan); this.editId = plan.id_cronograma; this.error.set(''); this.mensaje.set(''); this.editor.set(true);
  }
  agregar(tipo: 'ACTIVIDAD' | 'HITO') {
    this.borrador.actividades.push({ clave: crypto.randomUUID(), nombre: '', descripcion: '', tipo,
      fecha_inicio: this.borrador.fecha_inicio, fecha_fin: this.borrador.fecha_inicio,
      inicio_real: null, fin_real: null, avance: 0, dependencias: [] });
  }
  quitar(a: ActividadPlan) {
    if (this.borrador.actividades.some(x => x.dependencias.includes(a.clave))) {
      this.error.set('Quite primero las dependencias que apuntan a esta actividad.'); return;
    }
    this.borrador.actividades = this.borrador.actividades.filter(x => x !== a);
  }
  alternarPredecesora(a: ActividadPlan, clave: string, seleccionada: boolean) {
    a.dependencias = seleccionada
      ? [...new Set([...a.dependencias, clave])]
      : a.dependencias.filter(predecesora => predecesora !== clave);
  }
  cambiarFechaPrevista(a: ActividadPlan, campo: 'fecha_inicio' | 'fecha_fin', fecha: string) {
    a[campo] = fecha;
    if (a.tipo === 'HITO') { a.fecha_inicio = fecha; a.fecha_fin = fecha; }
  }
  cancelar() { if (this.salir()) { this.editor.set(false); this.error.set(''); } }
  guardar() {
    this.guardando.set(true); this.error.set('');
    this.api.guardar(this.idObra, this.editId, this.borrador, !this.puedeCabecera).pipe(takeUntilDestroyed(this.destroy)).subscribe({
      next: r => { this.guardando.set(false); this.editor.set(false); this.mensaje.set('Cronograma guardado.'); this.cargar(r.data.id_cronograma); },
      error: e => this.fallo(e),
    });
  }
  eliminar() {
    const plan = this.actual(); if (!plan || !window.confirm(`¿Eliminar «${plan.nombre}» y todas sus actividades?`)) return;
    this.guardando.set(true); this.error.set('');
    this.api.eliminar(this.idObra, plan).pipe(takeUntilDestroyed(this.destroy)).subscribe({
      next: () => { this.guardando.set(false); this.actual.set(null); this.mensaje.set('Cronograma eliminado.'); this.cargar(); }, error: e => this.fallo(e),
    });
  }
  nombreDependencias(a: ActividadPlan) {
    return a.dependencias.map(k => this.actual()?.actividades.find(x => x.clave === k)?.nombre || k).join(', ') || 'Sin dependencias';
  }
  visibles() { return (this.actual()?.programadas || []).filter(a => !this.soloRetrasos || (a.dias_retraso || 0) > 0 || a.inicio_retrasado); }
  fallo(e: any) {
    const detail = e.error?.detail;
    this.error.set(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(x => `${x.loc?.slice(1).join('.')}: ${x.msg}`).join(' · ') : 'No se pudo completar la operación. Comprueba la conexión e intenta de nuevo.');
    this.cargando.set(false); this.guardando.set(false);
  }
}
