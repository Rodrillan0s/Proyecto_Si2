import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { NotificacionesService } from './notificaciones';
import { AuthService } from './auth';

describe('NotificacionesService', () => {
  let service: NotificacionesService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        {
          provide: AuthService,
          useValue: {
            obtenerToken: () => 'fake-jwt-token',
            tokenExpirado: () => false,
          },
        },
      ],
    });
    service = TestBed.inject(NotificacionesService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('solicita configuración de alertas con id_obra opcional', () => {
    service.obtenerConfiguracionAlertas(12).subscribe((res) => {
      expect(res.success).toBe(true);
      expect(res.id_obra).toBe(12);
    });

    const req = httpMock.expectOne((r) => r.url.endsWith('/api/ws/configuracion-alertas') && r.params.get('id_obra') === '12');
    expect(req.request.method).toBe('GET');
    req.flush({
      success: true,
      id_empresa: 1,
      id_obra: 12,
      nombre_obra: 'Torre A',
      migracion_pendiente: false,
      roles_disponibles: ['ADMINISTRADOR_EMPRESA', 'JEFE DE OBRA'],
      data: [],
    });
  });

  it('envía PUT para guardar configuración de alertas', () => {
    service.guardarConfiguracionAlertas({
      id_obra: null,
      configuraciones: [{ tipo_evento: 'INCIDENCIA', activo: false, roles_destino: ['JEFE DE OBRA'] }],
    }).subscribe((res) => {
      expect(res.success).toBe(true);
    });

    const req = httpMock.expectOne((r) => r.url.endsWith('/api/ws/configuracion-alertas'));
    expect(req.request.method).toBe('PUT');
    expect(req.request.body.configuraciones[0].tipo_evento).toBe('INCIDENCIA');
    req.flush({
      success: true,
      id_empresa: 1,
      id_obra: null,
      nombre_obra: null,
      migracion_pendiente: false,
      roles_disponibles: ['ADMINISTRADOR_EMPRESA', 'JEFE DE OBRA'],
      data: [],
    });
  });
});
