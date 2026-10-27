import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, DestroyRef, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Observable, combineLatest, finalize } from 'rxjs';
import { DashboardCardComponent } from '../../components/ui/dashboard-card';
import { PageHeaderComponent } from '../../components/ui/page-header';
import { AuthService } from '../../services/auth';
import { ContextoOperativo } from '../../services/contexto-operativo';
import { ApiResponse, CategoriaCosto, ControlCostosService, ResumenFinalControl, ResumenManoObra } from '../../services/control-costos.service';
import { LecturasVigentes } from '../../services/lecturas';
import { Proyecto, ProyectosService } from '../../services/proyectos';

@Component({
  selector: 'app-gastos-operativos',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, PageHeaderComponent, DashboardCardComponent],
  templateUrl: './gastos-operativos.html',
  styleUrl: '../control-costos/control-costos.css',
})
export class GastosOperativosComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly contexto = inject(ContextoOperativo);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly proyectosService = inject(ProyectosService);
  private readonly service = inject(ControlCostosService);
  private readonly destroy = inject(DestroyRef);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly reads = new LecturasVigentes(this.destroy);
  private version = 0;
  private idRuta = 0;
  proyectos: Proyecto[] = [];
  idObra = 0;
  resumen: ResumenFinalControl | null = null;
  manoObra: ResumenManoObra = { trabajadores: [], jornadas: [] };
  tab: 'final' | 'mano-obra' = 'final';
  cargando = false;
  cargandoObras = false;
  guardando = false;
  error = '';
  exito = '';
  aviso = '';
  salario = { id_usuario: 0, salario_diario: 0, fecha_vigencia: this.hoy() };
  jornada = { id_usuario: 0, fecha: this.hoy(), dias_trabajados: 1 };
  readonly categorias: CategoriaCosto[] = ['MATERIAL', 'MANO_OBRA', 'EQUIPO', 'SUBCONTRATO', 'OTRO'];
  get contextoCompatible() {
    if (this.auth.obtenerRolNormalizado?.() === 'ADMINISTRADOR') {
      return !!this.auth.obtenerIdEmpresaActiva();
    }
    return this.auth.obtenerIdEmpresaActiva() === Number(this.auth.obtenerUsuario()?.id_empresa);
  }
  puede(permiso: string) { return this.auth.hasPermission(permiso); }
  obra() { return this.proyectos.find(p => p.id_obra === this.idObra); }
  private hoy() { return new Intl.DateTimeFormat('sv-SE', { timeZone: 'America/La_Paz' }).format(new Date()); }

  ngOnInit() {
    this.contexto.protegerEscritura(() => this.guardando, this.destroy);
    combineLatest([this.route.paramMap, this.contexto.operativo$]).pipe(takeUntilDestroyed(this.destroy)).subscribe(([params]) => {
      this.version++;
      this.reads.cancelar();
      this.idRuta = Number(params.get('id')) || 0;
      this.idObra = this.idRuta || this.contexto.obra?.id_obra || 0;
      this.proyectos = [];
      this.limpiar();
      if (!this.contextoCompatible || !this.puede('Visualizar_control_costos')) return;
      this.cargandoObras = true;
      this.proyectosService.listarProyectos().pipe(
        finalize(() => { this.cargandoObras = false; this.cdr.markForCheck(); }), this.reads.reemplazar('obras'),
      ).subscribe({
        next: response => {
          this.proyectos = (response.data || []).filter(p => p.id_obra && Number(p.id_empresa) === this.auth.obtenerIdEmpresaActiva());
          if (this.idObra && !this.obra()) { this.idObra = 0; this.error = 'La obra no existe o no pertenece a la empresa de la sesión.'; }
          else this.cargar();
          this.cdr.markForCheck();
        },
        error: error => { this.error = this.mensaje(error); this.cdr.markForCheck(); },
      });
    });
  }

  cambiarObra(id: number) {
    const obra = this.proyectos.find(p => p.id_obra === Number(id));
    if (!obra || !this.contextoCompatible || !this.contexto.confirmarCambio()) return;
    if (this.idRuta) { void this.router.navigate(['/proyectos', obra.id_obra, 'gastos-finales']); return; }
    this.contexto.seleccionar(obra);
  }

  private limpiar() {
    this.resumen = null;
    this.manoObra = { trabajadores: [], jornadas: [] };
    this.error = ''; this.exito = ''; this.aviso = ''; this.cargando = false;
    this.salario = { id_usuario: 0, salario_diario: 0, fecha_vigencia: this.hoy() };
    this.jornada = { id_usuario: 0, fecha: this.hoy(), dias_trabajados: 1 };
  }

  cambiarTab(tab: 'final' | 'mano-obra') { this.tab = tab; this.cargar(); }
  cargar() {
    const lectura = this.reads.reemplazar<ApiResponse<ResumenFinalControl | ResumenManoObra>>('datos');
    this.resumen = null; this.manoObra = { trabajadores: [], jornadas: [] };
    this.error = ''; this.aviso = '';
    if (!this.idObra || !this.obra() || !this.contextoCompatible || !this.puede('Visualizar_control_costos')) return;
    if (this.tab === 'final' && this.obra()?.estado_obra !== 'FINALIZADO') {
      this.aviso = 'El resumen final estará disponible cuando se finalice la obra. Puedes registrar salarios y jornadas en Mano de obra.';
      return;
    }
    this.cargando = true;
    const request = this.tab === 'final' ? this.service.resumenFinal(this.idObra) : this.service.manoObra(this.idObra);
    (request as Observable<ApiResponse<ResumenFinalControl | ResumenManoObra>>).pipe(
      finalize(() => { this.cargando = false; this.cdr.markForCheck(); }), lectura,
    ).subscribe({
      next: response => {
        if (this.tab === 'final') this.resumen = response.data as ResumenFinalControl;
        else this.manoObra = response.data as ResumenManoObra;
        this.cdr.markForCheck();
      },
      error: error => { this.error = this.mensaje(error); this.cdr.markForCheck(); },
    });
  }

  guardarSalario() {
    if (!this.autorizaEscritura()) return;
    if (!this.manoObra.trabajadores.some(t => t.id_usuario === Number(this.salario.id_usuario)) || !Number.isFinite(this.salario.salario_diario) || this.salario.salario_diario <= 0 || !this.salario.fecha_vigencia) {
      this.error = 'Selecciona un trabajador asignado, un salario positivo y una fecha de vigencia.'; return;
    }
    this.escribir(this.service.registrarSalario(this.idObra, Number(this.salario.id_usuario), {
      salario_diario: this.salario.salario_diario, fecha_vigencia: this.salario.fecha_vigencia,
    }), 'Salario registrado.');
  }
  guardarJornada() {
    if (!this.autorizaEscritura()) return;
    if (this.obra()?.estado_obra === 'FINALIZADO') { this.error = 'No se pueden modificar jornadas de una obra finalizada.'; return; }
    if (!this.manoObra.trabajadores.some(t => t.id_usuario === Number(this.jornada.id_usuario)) || !Number.isFinite(this.jornada.dias_trabajados) || this.jornada.dias_trabajados < 0 || this.jornada.dias_trabajados > 1 || !this.jornada.fecha) {
      this.error = 'Selecciona un trabajador asignado, una fecha y una fracción de jornada entre 0 y 1.'; return;
    }
    this.escribir(this.service.registrarJornada(this.idObra, { ...this.jornada, id_usuario: Number(this.jornada.id_usuario) }), 'Jornada registrada.');
  }
  private autorizaEscritura() {
    return !this.guardando && !!this.obra() && this.contextoCompatible && this.puede('Visualizar_control_costos') && this.puede('Modificar_obras');
  }
  private escribir(request: Observable<unknown>, mensaje: string) {
    const version = this.version;
    this.guardando = true; this.error = ''; this.exito = '';
    request.pipe(takeUntilDestroyed(this.destroy), finalize(() => { this.guardando = false; this.cdr.markForCheck(); })).subscribe({
      next: () => { if (version === this.version) { this.exito = mensaje; this.cargar(); } },
      error: error => { if (version === this.version) { this.error = this.mensaje(error); this.cdr.markForCheck(); } },
    });
  }
  dinero(value: number | undefined) {
    return new Intl.NumberFormat('es-BO', { style: 'currency', currency: this.resumen?.linea_base.moneda || this.obra()?.moneda || 'BOB' }).format(value || 0);
  }
  private mensaje(error: { status?: number; error?: { detail?: unknown } }) {
    if (typeof error.error?.detail === 'string') return error.error.detail;
    if (error.status === 0) return 'No se pudo conectar con el servidor. Intenta nuevamente.';
    if (error.status === 403) return 'No tienes autorización para esta operación.';
    if (error.status === 404) return 'No se encontró la obra o su línea base. Revisa Control de costos.';
    return 'No se pudo completar la operación. Revisa los datos e intenta nuevamente.';
  }
}
