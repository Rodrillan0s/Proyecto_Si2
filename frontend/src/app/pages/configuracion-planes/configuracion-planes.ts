import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ConfiguracionPlan, HistorialPlan, ImpactoPlan, ModuloPlan, PlanSuscripcion, SuscripcionService } from '../../services/suscripcion';

@Component({ standalone: true, selector: 'app-configuracion-planes', imports: [CommonModule, FormsModule, RouterLink], templateUrl: './configuracion-planes.html' })
export class ConfiguracionPlanesComponent implements OnInit {
  private api=inject(SuscripcionService);
  private destroy=inject(DestroyRef);
  planes=signal<PlanSuscripcion[]>([]);
  modulos=signal<ModuloPlan[]>([]);
  historial=signal<HistorialPlan[]>([]);
  impacto=signal<ImpactoPlan | null>(null);
  cargando=signal(true);
  trabajando=signal(false);
  cargandoHistorial=signal(false);
  error=signal('');
  errorHistorial=signal('');
  mensaje=signal('');
  codigo='';
  confirmado=false;
  private historialVersion=0;
  form: ConfiguracionPlan={ version:1,nombre:'',descripcion:'',modulos:[],limite_usuarios:5,limite_obras:2,
    consultas_ia_mes:0,nivel_reportes:'OPERATIVOS',exportar_reportes:false,automatizar_reportes:false };

  ngOnInit() { this.cargar(); }
  cargar() {
    if (this.trabajando()) return;
    this.cargando.set(true); this.error.set('');
    forkJoin({ planes:this.api.planes(),modulos:this.api.modulos() }).pipe(takeUntilDestroyed(this.destroy)).subscribe({
      next: res => { this.planes.set(res.planes.data); this.modulos.set(res.modulos.data); this.cargando.set(false); this.elegir(this.codigo || res.planes.data[0]?.codigo || ''); },
      error: err => { this.cargando.set(false); this.error.set(this.errorTexto(err,'No se pudo cargar la configuración de planes.')); },
    });
  }
  elegir(codigo: string) {
    if (this.trabajando()) return;
    const plan=this.planes().find(p => p.codigo===codigo);
    if (!plan) return;
    this.codigo=codigo; this.error.set(''); this.mensaje.set(''); this.cambio();
    this.form={ version:plan.version || 1,nombre:plan.nombre,descripcion:plan.descripcion,modulos:[...(plan.modulos || [])],
      limite_usuarios:plan.limite_usuarios || 1,limite_obras:plan.limite_obras || 1,consultas_ia_mes:plan.consultas_ia_mes || 0,
      nivel_reportes:plan.nivel_reportes as ConfiguracionPlan['nivel_reportes'],exportar_reportes:!!plan.exportar_reportes,automatizar_reportes:!!plan.automatizar_reportes };
    this.cargarHistorial();
  }
  cambio() { this.impacto.set(null); this.confirmado=false; }
  private errorTexto(error: { status?: number; error?: { detail?: unknown } }, defecto: string) {
    return typeof error.error?.detail==='string' ? error.error.detail
      : error.status===422 ? 'Revise los datos. Los cupos deben ser números enteros dentro de los rangos indicados.' : defecto;
  }
  tiene(modulo: string) { return this.form.modulos.includes(modulo); }
  alternar(modulo: string, habilitar: boolean) {
    this.form.modulos=habilitar ? [...new Set([...this.form.modulos,modulo])] : this.form.modulos.filter(m => m!==modulo);
    if (modulo==='ia') this.form.consultas_ia_mes=habilitar ? this.form.consultas_ia_mes || 500 : 0;
    if (modulo==='reportes') {
      if (!habilitar) { this.form.nivel_reportes='NINGUNO'; this.form.exportar_reportes=false; this.form.automatizar_reportes=false; }
      else if (this.form.nivel_reportes==='NINGUNO') this.form.nivel_reportes='OPERATIVOS';
    }
    this.cambio();
  }
  cambiarReportes() {
    if (this.form.nivel_reportes==='NINGUNO') { this.form.exportar_reportes=false; this.form.automatizar_reportes=false; }
    if (!this.form.exportar_reportes) this.form.automatizar_reportes=false;
    this.cambio();
  }
  revisar() {
    if (this.trabajando() || !this.codigo) return;
    this.cambio(); this.trabajando.set(true); this.error.set(''); this.mensaje.set('');
    this.api.previsualizarPlan(this.codigo,this.form).pipe(takeUntilDestroyed(this.destroy)).subscribe({
      next: res => { this.impacto.set(res.data); this.trabajando.set(false); },
      error: err => { this.error.set(this.errorTexto(err,'No se pudo calcular el impacto.')); this.trabajando.set(false); },
    });
  }
  guardar() {
    const impacto=this.impacto();
    if (!impacto || !this.confirmado || this.trabajando()) return;
    this.trabajando.set(true); this.error.set('');
    this.api.configurarPlan(this.codigo,this.form,impacto.confirmacion).pipe(takeUntilDestroyed(this.destroy)).subscribe({
      next: res => {
        this.planes.update(planes => planes.map(p => p.codigo===res.data.codigo ? res.data : p));
        this.trabajando.set(false); this.elegir(res.data.codigo);
        this.mensaje.set('Plan actualizado. La configuración se aplica a todas sus empresas y el cambio quedó registrado.');
      },
      error: err => { this.trabajando.set(false); this.cambio(); this.error.set(this.errorTexto(err,'No se pudo guardar el plan.')); },
    });
  }
  cargarHistorial() {
    const codigo=this.codigo;
    const revision=++this.historialVersion;
    this.historial.set([]); this.errorHistorial.set(''); this.cargandoHistorial.set(true);
    this.api.historialPlan(codigo).pipe(takeUntilDestroyed(this.destroy)).subscribe({
      next: res => { if (codigo===this.codigo && revision===this.historialVersion) { this.historial.set(res.data); this.cargandoHistorial.set(false); } },
      error: () => { if (codigo===this.codigo && revision===this.historialVersion) { this.errorHistorial.set('No se pudo cargar el historial.'); this.cargandoHistorial.set(false); } },
    });
  }
  nombres(modulos: string[] | undefined) { return (modulos || []).map(m => this.modulos().find(item => item.codigo===m)?.nombre || m).join(', ') || 'Ninguno'; }
}
