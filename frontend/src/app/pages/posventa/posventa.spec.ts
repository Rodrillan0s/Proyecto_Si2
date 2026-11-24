import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AuthService } from '../../services/auth';
import { PosventaService } from '../../services/posventa.service';
import { PosventaComponent } from './posventa';

describe('PosventaComponent (CU42)', () => {
  afterEach(() => TestBed.resetTestingModule());

  function crear(rol: string) {
    const api = {
      catalogos: vi.fn(() => of({
        success: true,
        data: {
          categorias: ['ESTRUCTURAL', 'INSTALACION_ELECTRICA', 'OTRO'],
          estados: ['REGISTRADA', 'CLASIFICADA', 'ASIGNADA', 'EN_ATENCION', 'RESUELTA', 'CERRADA'],
        },
      })),
      listarGarantias: vi.fn(() => of({
        success: true,
        data: [{
          id_garantia: 1, id_empresa: 3, id_unidad: 101, unidad_codigo: 'U-101',
          codigo: 'GAR-101', tipo_garantia: 'Instalaciones', descripcion: 'Cobertura',
          fecha_inicio: '2026-11-01', fecha_fin: null, observaciones: null, creado_en: '2026-11-01T00:00:00Z',
        }],
      })),
      listarSolicitudes: vi.fn(() => of({
        success: true,
        data: [{
          id_solicitud_posventa: 11, id_empresa: 3, id_unidad: 101, unidad_codigo: 'U-101',
          id_cliente: 700, id_garantia: null, titulo: 'Falla eléctrica', descripcion: 'No enciende',
          categoria: null, estado: 'REGISTRADA', id_responsable: null,
          creado_en: '2026-11-24T00:00:00Z', actualizado_en: '2026-11-24T00:00:00Z',
        }],
      })),
      obtenerSolicitud: vi.fn(() => of({
        success: true,
        data: {
          id_solicitud_posventa: 11, id_empresa: 3, id_unidad: 101, id_cliente: 700, id_garantia: null,
          titulo: 'Falla eléctrica', descripcion: 'No enciende', categoria: null, estado: 'REGISTRADA',
          id_responsable: null, creado_en: '2026-11-24T00:00:00Z', actualizado_en: '2026-11-24T00:00:00Z',
          seguimiento: [{ id_seguimiento: 1, id_solicitud_posventa: 11, id_usuario: 30, accion: 'REGISTRO', estado_anterior: null, estado_nuevo: 'REGISTRADA', observacion: 'Registrada', creado_en: '2026-11-24T00:00:00Z' }],
        },
      })),
      registrarGarantia: vi.fn(() => of({ success: true, data: {} })),
      registrarSolicitud: vi.fn(() => of({ success: true, data: {} })),
      clasificarSolicitud: vi.fn(() => of({ success: true, data: {} })),
      asignarResponsable: vi.fn(() => of({ success: true, data: {} })),
      gestionarAtencion: vi.fn(() => of({ success: true, data: { id_solicitud_posventa: 11, estado: 'EN_ATENCION', seguimiento: [] } })),
      historialUnidad: vi.fn(() => of({
        success: true,
        data: {
          unidad: { id_unidad: 101, unidad_codigo: 'U-101', unidad_nombre: 'Dpto 101', id_obra: 10, obra_nombre: 'Torre A', id_empresa: 3 },
          garantias: [],
          solicitudes: [],
        },
      })),
    };

    TestBed.configureTestingModule({
      imports: [PosventaComponent],
      providers: [
        { provide: AuthService, useValue: { obtenerRolNormalizado: () => rol } },
        { provide: PosventaService, useValue: api },
      ],
    });
    const fixture = TestBed.createComponent(PosventaComponent);
    fixture.detectChanges();
    return { fixture, component: fixture.componentInstance, api };
  }

  it('carga catálogos, garantías y solicitudes para ADMINISTRADOR_EMPRESA', () => {
    const { fixture, component } = crear('ADMINISTRADOR_EMPRESA');
    expect(component.esGestion).toBe(true);
    expect(fixture.nativeElement.textContent).toContain('Falla eléctrica');
  });

  it('permite a CLIENTE registrar una solicitud sin garantía obligatoria', () => {
    const { component, api } = crear('CLIENTE');
    expect(component.esCliente).toBe(true);
    component.nuevaSolicitud = { id_unidad: 101, id_garantia: null, titulo: 'Puerta desajustada', descripcion: 'Roza al cerrar' };
    component.crearSolicitud();
    expect(api.registrarSolicitud).toHaveBeenCalledWith({
      id_unidad: 101,
      id_garantia: null,
      titulo: 'Puerta desajustada',
      descripcion: 'Roza al cerrar',
    });
  });

  it('permite clasificar, asignar y consultar historial por unidad', () => {
    const { component, api } = crear('ADMINISTRADOR_EMPRESA');
    component.verSeguimiento(component.solicitudes()[0]);
    component.categoriaSeleccionada = 'INSTALACION_ELECTRICA';
    component.clasificar();
    expect(api.clasificarSolicitud).toHaveBeenCalledWith(11, { categoria: 'INSTALACION_ELECTRICA', observacion: undefined });

    component.idResponsableAsignar = 40;
    component.asignar();
    expect(api.asignarResponsable).toHaveBeenCalledWith(11, { id_responsable: 40, observacion: undefined });

    component.idUnidadHistorial = 101;
    component.consultarHistorialUnidad();
    expect(api.historialUnidad).toHaveBeenCalledWith(101);
  });
});
