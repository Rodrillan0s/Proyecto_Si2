import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { describe, it, expect, afterEach } from 'vitest';
import { ConfiguracionPlanesComponent } from './configuracion-planes';
import { AuthService } from '../../services/auth';

describe('Configuración de planes', () => {
  let http: HttpTestingController;
  const plan={codigo:'BASICO',version:1,nombre:'Básico',descripcion:'Para comenzar',prestaciones:[],modulos:['crm','reportes'],
    limite_usuarios:5,limite_obras:2,consultas_ia_mes:0,nivel_reportes:'OPERATIVOS',exportar_reportes:false,automatizar_reportes:false};
  const impacto={empresas:[{id_empresa:3,nombre_empresa:'La Roca',usuarios_activos:2,obras_activas:3}],total_empresas:1,
    empresas_sobre_cupo:[],modulos_retirados:[{codigo:'crm',nombre:'CRM y clientes'}],confirmacion:'a'.repeat(64),mensaje:'Se conservan los datos.'};
  function crear() {
    TestBed.configureTestingModule({imports:[ConfiguracionPlanesComponent],providers:[provideHttpClient(),provideHttpClientTesting(),provideRouter([]),
      {provide:AuthService,useValue:{obtenerRolNormalizado:()=>'ADMINISTRADOR'}}]});
    const fixture=TestBed.createComponent(ConfiguracionPlanesComponent);
    http=TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    http.expectOne(r=>r.url.endsWith('/planes')).flush({data:[plan]});
    http.expectOne(r=>r.url.endsWith('/configuracion/modulos')).flush({data:[{codigo:'crm',nombre:'CRM y clientes'},{codigo:'reportes',nombre:'Reportes'},{codigo:'ia',nombre:'Asistente IA'}]});
    http.expectOne(r=>r.url.endsWith('/BASICO/historial')).flush({data:[]});
    fixture.detectChanges();
    return fixture;
  }
  afterEach(()=>{http.verify();TestBed.resetTestingModule();});

  it('previsualiza empresas y módulos retirados sin guardar automáticamente',()=>{
    const f=crear();
    f.componentInstance.alternar('crm',false);
    f.componentInstance.revisar();
    const req=http.expectOne(r=>r.url.endsWith('/previsualizar'));
    expect(req.request.body.modulos).not.toContain('crm');
    req.flush({data:impacto});
    f.detectChanges();
    expect(f.nativeElement.textContent).toContain('La Roca');
    expect(f.nativeElement.textContent).toContain('CRM y clientes');
    f.componentInstance.guardar();
    http.expectNone(r=>r.method==='PUT');
  });

  it('envía la confirmación revisada y recarga historial al guardar',()=>{
    const f=crear();
    f.componentInstance.revisar();http.expectOne(r=>r.url.endsWith('/previsualizar')).flush({data:impacto});
    f.componentInstance.confirmado=true;f.componentInstance.guardar();
    const req=http.expectOne(r=>r.method==='PUT');
    expect(req.request.body.confirmacion).toBe(impacto.confirmacion);
    expect(req.request.body.version).toBe(1);
    req.flush({data:{...plan,version:2}});
    http.expectOne(r=>r.url.endsWith('/historial')).flush({data:[]});
    expect(f.componentInstance.form.version).toBe(2);
    expect(f.componentInstance.impacto()).toBeNull();
  });

  it('invalida la revisión cuando se modifica el borrador',()=>{
    const f=crear();
    f.componentInstance.revisar();http.expectOne(r=>r.url.endsWith('/previsualizar')).flush({data:impacto});
    f.componentInstance.confirmado=true;
    f.componentInstance.alternar('ia',true);
    expect(f.componentInstance.form.consultas_ia_mes).toBe(500);
    expect(f.componentInstance.impacto()).toBeNull();
    expect(f.componentInstance.confirmado).toBe(false);
    f.componentInstance.guardar();http.expectNone(r=>r.method==='PUT');
  });

  it('un conflicto conserva el borrador y exige revisar nuevamente',()=>{
    const f=crear();
    f.componentInstance.form.limite_usuarios=8;
    f.componentInstance.revisar();http.expectOne(r=>r.url.endsWith('/previsualizar')).flush({data:impacto});
    f.componentInstance.confirmado=true;f.componentInstance.guardar();
    http.expectOne(r=>r.method==='PUT').flush({detail:'El plan cambió. Recargue.'},{status:409,statusText:'Conflict'});
    expect(f.componentInstance.form.limite_usuarios).toBe(8);
    expect(f.componentInstance.error()).toContain('El plan cambió');
    expect(f.componentInstance.impacto()).toBeNull();
  });

  it('retirar Reportes desactiva todas sus capacidades dependientes',()=>{
    const f=crear();
    f.componentInstance.form.exportar_reportes=true;f.componentInstance.form.automatizar_reportes=true;
    f.componentInstance.alternar('reportes',false);
    expect(f.componentInstance.form.nivel_reportes).toBe('NINGUNO');
    expect(f.componentInstance.form.exportar_reportes).toBe(false);
    expect(f.componentInstance.form.automatizar_reportes).toBe(false);
  });
  it('presenta errores de validación del servidor como texto comprensible',()=>{
    const f=crear();
    f.componentInstance.form.limite_obras=1.5;
    f.componentInstance.revisar();
    http.expectOne(r=>r.url.endsWith('/previsualizar')).flush({detail:[{loc:['body','limite_obras'],msg:'Invalid integer'}]},{status:422,statusText:'Unprocessable Entity'});
    expect(f.componentInstance.error()).toContain('números enteros');
    expect(f.componentInstance.error()).not.toContain('[object Object]');
  });
});
