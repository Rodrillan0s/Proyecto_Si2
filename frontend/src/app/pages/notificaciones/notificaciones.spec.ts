import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject, of } from 'rxjs';
import { NotificacionesComponent } from './notificaciones';
import { NotificacionesService, Notificacion } from '../../services/notificaciones';
import { AuthService } from '../../services/auth';
import { ProyectosService } from '../../services/proyectos';

describe('NotificacionesComponent', () => {
  let component: NotificacionesComponent;
  let fixture: ComponentFixture<NotificacionesComponent>;
  let notis$: BehaviorSubject<Notificacion[]>;

  beforeEach(async () => {
    notis$ = new BehaviorSubject<Notificacion[]>([
      {
        id_notificacion: 1,
        tipo_alerta: 'INCIDENCIA',
        tipo_referencia: 'INCIDENCIA',
        titulo: 'Nueva Incidencia',
        cuerpo: 'Falla eléctrica',
        leida: false,
        fecha: new Date(),
        nro_emergencia: 7,
      },
      {
        id_notificacion: 2,
        tipo_alerta: 'AVANCE_OBRA',
        tipo_referencia: 'AVANCE_OBRA',
        titulo: 'Avance registrado',
        cuerpo: '50% completado',
        leida: true,
        fecha: new Date(),
      },
    ]);

    await TestBed.configureTestingModule({
      imports: [NotificacionesComponent],
      providers: [
        {
          provide: NotificacionesService,
          useValue: {
            notificaciones$: notis$.asObservable(),
            cargando$: of(false),
            error$: of(null),
            cargarHistorial: () => {},
            marcarUnaComoLeida: () => {},
            marcarComoLeidas: () => {},
            obtenerConfiguracionAlertas: () => of({
              success: true,
              id_empresa: 1,
              id_obra: null,
              nombre_obra: null,
              migracion_pendiente: false,
              roles_disponibles: ['ADMINISTRADOR_EMPRESA', 'JEFE DE OBRA'],
              data: [],
            }),
            guardarConfiguracionAlertas: () => of({
              success: true,
              id_empresa: 1,
              id_obra: null,
              nombre_obra: null,
              migracion_pendiente: false,
              roles_disponibles: ['ADMINISTRADOR_EMPRESA', 'JEFE DE OBRA'],
              data: [],
            }),
          },
        },
        {
          provide: AuthService,
          useValue: {
            obtenerRolNormalizado: () => 'ADMINISTRADOR_EMPRESA',
            obtenerEmpresaActiva: () => null,
          },
        },
        {
          provide: ProyectosService,
          useValue: {
            listarProyectos: () => of({ success: true, data: [] }),
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(NotificacionesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create and allow alert configuration for ADMINISTRADOR_EMPRESA', () => {
    expect(component).toBeTruthy();
    expect(component.puedeConfigurarAlertas).toBe(true);
    expect(component.totalNoLeidas).toBe(1);
  });

  it('filtra correctamente entre no leídas y leídas', () => {
    component.cambiarFiltro('NO_LEIDAS');
    expect(component.grupos[0].notificaciones.length).toBe(1);
    expect(component.grupos[0].notificaciones[0].id_notificacion).toBe(1);

    component.cambiarFiltro('LEIDAS');
    expect(component.grupos[0].notificaciones.length).toBe(1);
    expect(component.grupos[0].notificaciones[0].id_notificacion).toBe(2);
  });
});
