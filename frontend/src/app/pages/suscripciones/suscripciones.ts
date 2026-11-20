import { Component, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AuthService } from '../../services/auth';
import { AsignacionSuscripcion, PlanSuscripcion, SuscripcionEmpresa, SuscripcionService } from '../../services/suscripcion';

@Component({
  standalone: true,
  selector: 'app-suscripciones',
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './suscripciones.html',
})
export class SuscripcionesComponent implements OnInit {
  private service = inject(SuscripcionService);
  private destroyRef = inject(DestroyRef);
  esGlobal = inject(AuthService).obtenerRolNormalizado() === 'ADMINISTRADOR';
  planes = signal<PlanSuscripcion[]>([]);
  empresas = signal<SuscripcionEmpresa[]>([]);
  propia = signal<SuscripcionEmpresa | null>(null);
  cargando = signal(true);
  guardando = signal(false);
  error = signal('');
  mensaje = signal('');
  seleccionada: SuscripcionEmpresa | null = null;
  form: AsignacionSuscripcion = { codigo_plan: 'BASICO', estado: 'ACTIVA', fecha_inicio: '', fecha_fin: null };

  nombrePlan(empresa: SuscripcionEmpresa): string {
    return empresa.nombre_plan?.trim()
      || this.planes().find(plan => plan.codigo === empresa.codigo_plan)?.nombre
      || empresa.codigo_plan || 'Sin plan asignado';
  }

  etiquetaPlan(empresa: SuscripcionEmpresa | null): string {
    return empresa && ['ACTIVA', 'GRACIA'].includes(empresa.estado_efectivo) ? 'Plan vigente' : 'Plan asignado';
  }

  ngOnInit() {
    forkJoin({ planes: this.service.planes(), suscripciones: this.esGlobal ? this.service.empresas() : this.service.propia() })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: ({ planes, suscripciones }) => {
          this.planes.set(planes.data);
          if (this.esGlobal) this.empresas.set(suscripciones.data as SuscripcionEmpresa[]);
          else this.propia.set(suscripciones.data as SuscripcionEmpresa);
          this.cargando.set(false);
        },
        error: err => { this.error.set(err?.error?.detail || 'No se pudieron cargar las suscripciones.'); this.cargando.set(false); },
      });
  }

  editar(empresa: SuscripcionEmpresa) {
    this.seleccionada = empresa;
    this.error.set('');
    this.mensaje.set('');
    const fecha = new Intl.DateTimeFormat('sv-SE', { timeZone: 'America/La_Paz' }).format(new Date());
    this.form = { codigo_plan: empresa.codigo_plan || 'BASICO', estado: empresa.estado || 'ACTIVA',
      fecha_inicio: empresa.fecha_inicio || fecha, fecha_fin: empresa.fecha_fin };
  }

  guardar() {
    if (!this.seleccionada || this.guardando()) return;
    if (this.form.fecha_fin && this.form.fecha_fin < this.form.fecha_inicio) {
      this.error.set('La fecha de fin no puede ser anterior al inicio.'); return;
    }
    this.guardando.set(true);
    this.error.set('');
    this.mensaje.set('');
    this.service.guardar(this.seleccionada.id_empresa, { ...this.form, fecha_fin: this.form.fecha_fin || null })
      .pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
        next: res => {
          this.empresas.update(empresas => empresas.map(e => e.id_empresa === res.data.id_empresa ? res.data : e));
          this.seleccionada = null;
          this.guardando.set(false);
          this.mensaje.set('Suscripción actualizada para todos los usuarios de la empresa.');
        },
        error: err => { this.guardando.set(false); this.error.set(err?.error?.detail || 'No se pudo guardar la suscripción.'); },
      });
  }
}
