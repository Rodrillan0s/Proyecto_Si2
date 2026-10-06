import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router } from '@angular/router';
import { of } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { IncidenciaDetalleComponent } from './incidencia-detalle';
import { AuthService } from '../../../services/auth';
import { Incidencia, IncidenciasService } from '../../../services/incidencias';

// Se prueba la autorizaci?n visible sin iniciar peticiones de componentes hijos.
describe('CU19 atenci?n del responsable', () => {
  let component: IncidenciaDetalleComponent;
  let permisos: Set<string>;
  beforeEach(() => {
    permisos = new Set();
    TestBed.configureTestingModule({providers: [
      {provide: AuthService, useValue: {
        hasPermission: (p: string) => permisos.has(p),
        obtenerUsuario: () => ({nro_usuario: 14})
      }},
      {provide: ActivatedRoute, useValue: {paramMap: of(new Map())}},
      {provide: Router, useValue: {navigate: vi.fn()}},
      {provide: IncidenciasService, useValue: {}}
    ]});
    component = TestBed.createComponent(IncidenciaDetalleComponent).componentInstance;
    component.incidencia = {id_incidencia: 10, id_responsable: 14, estado: 'ASIGNADA'} as Incidencia;
  });

  it('Jhon inicia y aporta sin permisos administrativos', () => {
    expect(component.siguienteEstado()).toBe('EN_PROCESO');
    expect(component.puedeComentar()).toBe(true);
    expect(component.puedeAdjuntarEvidencia()).toBe(true);
    expect(component.puedeEditar()).toBe(false);
    expect(component.puedeAsignar()).toBe(false);
    expect(component.puedeSeleccionarOrdenes()).toBe(false);
  });
  it('Jhon finaliza y no cierra', () => {
    component.incidencia!.estado = 'EN_PROCESO';
    expect(component.siguienteEstado()).toBe('PENDIENTE_VALIDACION');
    expect(component.textoSiguienteEstado()).toBe('Finalizar atención');
    component.incidencia!.estado = 'PENDIENTE_VALIDACION';
    expect(component.puedeValidar()).toBe(false);
    expect(component.siguienteEstado()).toBeNull();
    component.incidencia!.estado = 'RESUELTA';
    expect(component.puedeCerrar()).toBe(false);
  });
  it('jefe y supervisor validan usando el permiso existente', () => {
    component.incidencia!.estado = 'PENDIENTE_VALIDACION';
    permisos.add('Modificar_incidencias');
    expect(component.puedeValidar()).toBe(true);
    component.incidencia!.estado = 'RESUELTA';
    expect(component.puedeValidar()).toBe(false);
    expect(component.siguienteEstado()).toBeNull();
  });
  it('un trabajador ajeno no atiende ni aporta', () => {
    component.incidencia!.id_responsable = 15;
    expect(component.siguienteEstado()).toBeNull();
    expect(component.puedeComentar()).toBe(false);
    expect(component.puedeAdjuntarEvidencia()).toBe(false);
  });
  it('los permisos administrativos conservan sus capacidades', () => {
    component.incidencia!.id_responsable = 15;
    permisos.add('Modificar_incidencias');
    permisos.add('Asignar_incidencias');
    permisos.add('Cerrar_incidencias');
    expect(component.puedeEditar()).toBe(true);
    expect(component.puedeAsignar()).toBe(true);
    expect(component.puedeComentar()).toBe(true);
    expect(component.puedeAdjuntarEvidencia()).toBe(true);
    expect(component.siguienteEstado()).toBeNull();
    component.incidencia!.estado = 'RESUELTA';
    expect(component.puedeCerrar()).toBe(true);
  });
});
