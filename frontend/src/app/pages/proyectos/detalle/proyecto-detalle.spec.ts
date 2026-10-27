import { ChangeDetectorRef, NgZone, PLATFORM_ID } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { of, Subject, throwError } from 'rxjs';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ProyectoDetalleComponent } from './proyecto-detalle';
import { ProyectosService, Proyecto, PersonalObra, ApiResponseSimple } from '../../../services/proyectos';
import { AuthService } from '../../../services/auth';

describe('Personal en el detalle del proyecto', () => {
  const jhon: PersonalObra = {
    id_usuario: 14, username: 'JHON JONES', nombre_completo: 'JHON JONES',
    nombre_rol: 'ELECTRICO', estado: 'ACTIVO'
  };
  let component: ProyectoDetalleComponent;
  let proyectos: { listarPersonal: ReturnType<typeof vi.fn>; candidatosPersonal: ReturnType<typeof vi.fn>; asignarPersonal: ReturnType<typeof vi.fn>; actualizarEstadoProyecto: ReturnType<typeof vi.fn> };
  let auth: { obtenerUsuario: ReturnType<typeof vi.fn>; hasPermission: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    proyectos = {
      listarPersonal: vi.fn(() => of({ success: true, data: [] })),
      candidatosPersonal: vi.fn(() => of({ success: true, data: [jhon] })),
      asignarPersonal: vi.fn(() => of({ success: true, message: 'Personal asignado correctamente.' })),
      actualizarEstadoProyecto: vi.fn(() => of({ success: true, message: 'Estado actualizado' }))
    };
    auth = { obtenerUsuario: vi.fn(() => ({ nombre_rol: 'ADMINISTRADOR_EMPRESA' })), hasPermission: vi.fn(() => true) };
    TestBed.configureTestingModule({ providers: [
      { provide: ProyectosService, useValue: proyectos },
      { provide: AuthService, useValue: auth },
      { provide: ActivatedRoute, useValue: {} },
      { provide: Router, useValue: { navigate: vi.fn() } },
      { provide: HttpClient, useValue: {} },
      { provide: ChangeDetectorRef, useValue: { detectChanges: vi.fn() } },
      { provide: NgZone, useValue: { run: (fn: () => void) => fn() } },
      { provide: PLATFORM_ID, useValue: 'browser' }
    ] });
    component = TestBed.runInInjectionContext(() => new ProyectoDetalleComponent());
    component.idObra = 8;
    vi.spyOn(component, 'mostrarExito').mockImplementation(() => {});
    vi.spyOn(component, 'mostrarError').mockImplementation(() => {});
  });

  it('finaliza mediante el servicio existente y permite abrir CU32 después del éxito', () => {
    component.proyecto = { id_obra: 8, estado_obra: 'ACTIVO' } as Proyecto;
    vi.spyOn(component, 'cargarProyecto').mockImplementation(() => {});
    component.cambiarEstado('FINALIZADO');
    expect(proyectos.actualizarEstadoProyecto).toHaveBeenCalledWith(8, 'FINALIZADO');
    expect(component.proyecto.estado_obra).toBe('FINALIZADO');
    expect(component.puedeConsultarResumenFinal()).toBe(true);
    component.irAResumenFinal();
    expect(TestBed.inject(Router).navigate).toHaveBeenCalledWith(['/control-costos'], {
      queryParams: { id_obra: 8, final: 'true' }
    });
  });

  it('no marca la obra finalizada cuando el backend revierte el cierre', () => {
    component.proyecto = { id_obra: 8, estado_obra: 'ACTIVO' } as Proyecto;
    proyectos.actualizarEstadoProyecto.mockReturnValue(throwError(() => ({ status: 404,
      error: { detail: 'La obra no tiene una linea base ACTIVA.' } })));
    component.cambiarEstado('FINALIZADO');
    expect(component.proyecto.estado_obra).toBe('ACTIVO');
    expect(component.puedeConsultarResumenFinal()).toBe(false);
    expect(component.mostrarError).toHaveBeenCalledWith('La obra no tiene una linea base ACTIVA.');
  });

  it('no ofrece navegación financiera sin el permiso existente', () => {
    component.proyecto = { id_obra: 8, estado_obra: 'FINALIZADO' } as Proyecto;
    auth.hasPermission.mockReturnValue(false);
    component.irAResumenFinal();
    expect(TestBed.inject(Router).navigate).not.toHaveBeenCalled();
  });

  it('consulta personal y candidatos de la obra para el administrador', () => {
    component.cargarPersonal();
    expect(proyectos.listarPersonal).toHaveBeenCalledWith(8);
    expect(proyectos.candidatosPersonal).toHaveBeenCalledWith(8);
    expect(component.candidatosPersonal).toEqual([jhon]);
  });

  it('asigna y actualiza los listados sin cambiar la selección del jefe', () => {
    component.idUsuarioSeleccionado = 20;
    component.idPersonalSeleccionado = 14;
    proyectos.listarPersonal.mockReturnValue(of({ success: true, data: [jhon] }));
    proyectos.candidatosPersonal.mockReturnValue(of({ success: true, data: [] }));
    component.asignarPersonal();
    expect(proyectos.asignarPersonal).toHaveBeenCalledWith(8, 14);
    expect(component.personalObra).toEqual([jhon]);
    expect(component.candidatosPersonal).toEqual([]);
    expect(component.idPersonalSeleccionado).toBeUndefined();
    expect(component.idUsuarioSeleccionado).toBe(20);
  });

  it('bloquea el doble envío mientras la asignación está pendiente', () => {
    const pending = new Subject<ApiResponseSimple>();
    proyectos.asignarPersonal.mockReturnValue(pending);
    component.idPersonalSeleccionado = 14;
    component.asignarPersonal();
    component.asignarPersonal();
    expect(proyectos.asignarPersonal).toHaveBeenCalledTimes(1);
    pending.next({ success: true, message: 'Asignado' });
    pending.complete();
    expect(component.procesandoAccion).toBe(false);
  });

  it('muestra el rechazo del backend y conserva la selección', () => {
    proyectos.asignarPersonal.mockReturnValue(throwError(() => ({ error: { detail: 'Empresa incorrecta' } })));
    component.idPersonalSeleccionado = 14;
    component.asignarPersonal();
    expect(component.mostrarError).toHaveBeenCalledWith('Empresa incorrecta');
    expect(component.idPersonalSeleccionado).toBe(14);
    expect(component.procesandoAccion).toBe(false);
  });

  it('distingue errores de carga de una lista vacía', () => {
    proyectos.listarPersonal.mockReturnValue(throwError(() => ({ error: { detail: 'Sin acceso' } })));
    proyectos.candidatosPersonal.mockReturnValue(throwError(() => ({ error: { detail: 'Sin permiso' } })));
    component.cargarPersonal();
    expect(component.errorPersonal).toBe('Sin acceso');
    expect(component.errorCandidatosPersonal).toBe('Sin permiso');
    expect(component.cargandoPersonal).toBe(false);
    expect(component.cargandoCandidatosPersonal).toBe(false);
  });

  it('consulta solo el listado para un trabajador', () => {
    auth.obtenerUsuario.mockReturnValue({ nombre_rol: 'ELECTRICO' });
    component.cargarPersonal();
    expect(proyectos.listarPersonal).toHaveBeenCalledWith(8);
    expect(proyectos.candidatosPersonal).not.toHaveBeenCalled();
  });
  it('abre el modal con candidatos actualizados y permite cancelar', () => {
    component.idPersonalSeleccionado = 14;
    component.abrirModalPersonal();
    expect(component.mostrarModalPersonal).toBe(true);
    expect(component.idPersonalSeleccionado).toBeUndefined();
    expect(proyectos.candidatosPersonal).toHaveBeenCalledWith(8);
    component.cerrarModalPersonal();
    expect(component.mostrarModalPersonal).toBe(false);
    expect(proyectos.asignarPersonal).not.toHaveBeenCalled();
  });

  it('cierra el modal solo cuando la asignaci?n resulta exitosa', () => {
    component.abrirModalPersonal();
    component.idPersonalSeleccionado = 14;
    proyectos.asignarPersonal.mockReturnValue(throwError(() => ({ error: { detail: 'Rechazado' } })));
    component.asignarPersonal();
    expect(component.mostrarModalPersonal).toBe(true);
    proyectos.asignarPersonal.mockReturnValue(of({ success: true, message: 'Asignado' }));
    component.asignarPersonal();
    expect(component.mostrarModalPersonal).toBe(false);
  });

});
