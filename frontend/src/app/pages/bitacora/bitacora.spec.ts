import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of, Subject, throwError } from 'rxjs';

import { AuthService } from '../../services/auth';
import { BitacoraService, RespuestaBitacora } from '../../services/bitacora.service';
import { BitacoraComponent } from './bitacora';

describe('BitacoraComponent', () => {
  let component: BitacoraComponent;
  let fixture: ComponentFixture<BitacoraComponent>;
  let obtenerBitacora: ReturnType<typeof vi.fn>;

  const registroAdmin = {
    id_bitacora: 1,
    id_usuario: 1,
    nombre: 'ADMINISTRADOR',
    modulo: 'ROLES Y PERMISOS',
    accion: 'MODIFICAR PERMISOS',
    descripcion: 'El administrador modificó los permisos del rol JEFE DE OBRA.',
    ip: '127.0.0.1',
    estado: 'EXITOSO',
    fecha: '2026-08-24',
    hora: '00:45:10'
  };

  const respuesta = (data = [] as (typeof registroAdmin)[]): RespuestaBitacora => ({
    success: true,
    data,
    pagination: {
      page: 1,
      limit: 20,
      total: data.length,
      total_pages: data.length > 0 ? 1 : 0
    }
  });

  beforeEach(async () => {
    obtenerBitacora = vi.fn().mockReturnValue(of(respuesta()));

    await TestBed.configureTestingModule({
      imports: [BitacoraComponent],
      providers: [
        {
          provide: AuthService,
          useValue: {
            obtenerUsuario: () => ({ nombre_rol: 'ADMINISTRADOR' }),
            tokenExpirado: () => false
          }
        },
        { provide: BitacoraService, useValue: { obtenerBitacora } },
        { provide: Router, useValue: { navigate: () => Promise.resolve(true) } }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(BitacoraComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('carga sin filtros una sola vez y finaliza loading', () => {
    expect(component).toBeTruthy();
    expect(obtenerBitacora).toHaveBeenCalledTimes(1);
    expect(component.loading).toBeFalsy();
    expect(component.error).toBe('');
  });

  it('finaliza loading y muestra el error genérico para errores no controlados', async () => {
    obtenerBitacora.mockReturnValue(throwError(() => new Error('fallo')));

    await component.cargarBitacora();

    expect(component.loading).toBeFalsy();
    expect(component.registros).toEqual([]);
    expect(component.pagination.total).toBe(0);
    expect(component.pagination.total_pages).toBe(0);
    expect(component.error).toBe('No fue posible cargar la bitácora.');
  });

  it('muestra el detalle seguro y finaliza loading ante un error 400', async () => {
    obtenerBitacora.mockReturnValue(throwError(() => ({
      status: 400,
      error: { detail: "El filtro 'fecha' debe tener formato YYYY-MM-DD." }
    })));

    await component.cargarBitacora();

    expect(component.loading).toBeFalsy();
    expect(component.registros).toEqual([]);
    expect(component.error).toBe("El filtro 'fecha' debe tener formato YYYY-MM-DD.");
  });

  it('busca ADMIN con fecha válida mediante una sola petición', async () => {
    obtenerBitacora.mockClear();
    obtenerBitacora.mockReturnValue(of(respuesta([registroAdmin])));
    component.fecha = '2026-08-24';
    component.usuario = 'ADMIN';
    component.accion = 'MODIFICAR PERMISOS';
    component.pagination.page = 3;

    component.buscar();
    await fixture.whenStable();

    expect(obtenerBitacora).toHaveBeenCalledTimes(1);
    expect(obtenerBitacora).toHaveBeenCalledWith({
      fecha: '2026-08-24',
      usuario: 'ADMIN',
      accion: 'MODIFICAR PERMISOS',
      page: 1,
      limit: 20
    });
    expect(component.registros).toEqual([registroAdmin]);
    expect(component.loading).toBeFalsy();
  });

  it('muestra estado vacío para HOMERO sin conservar resultados anteriores', async () => {
    component.registros = [registroAdmin];
    component.pagination = { page: 1, limit: 20, total: 1, total_pages: 1 };
    component.usuario = 'HOMERO';
    obtenerBitacora.mockClear();
    obtenerBitacora.mockReturnValue(of(respuesta()));

    component.buscar();
    await fixture.whenStable();

    expect(obtenerBitacora).toHaveBeenCalledTimes(1);
    expect(component.registros).toEqual([]);
    expect(component.pagination.total).toBe(0);
    expect(component.pagination.total_pages).toBe(0);
    expect(component.error).toBe('');
    expect(component.loading).toBeFalsy();
  });

  it('envía fecha y usuario combinados en una sola petición', async () => {
    obtenerBitacora.mockClear();
    obtenerBitacora.mockReturnValue(of(respuesta([registroAdmin])));
    component.fecha = '2026-08-24';
    component.usuario = 'ADMIN';

    component.buscar();
    await fixture.whenStable();

    expect(obtenerBitacora).toHaveBeenCalledTimes(1);
    expect(obtenerBitacora).toHaveBeenCalledWith(expect.objectContaining({
      fecha: '2026-08-24',
      usuario: 'ADMIN',
      page: 1
    }));
    expect(component.loading).toBeFalsy();
  });

  it.each(['232322-08-24', '2026-02-30', '1999-12-31', '2101-01-01'])(
    'no envía la fecha inválida %s al backend',
    async (fechaInvalida) => {
      obtenerBitacora.mockClear();
      component.fecha = fechaInvalida;

      await component.cargarBitacora();

      expect(obtenerBitacora).not.toHaveBeenCalled();
      expect(component.error).toBe('Seleccione una fecha válida.');
      expect(component.loading).toBeFalsy();
    }
  );

  it('limpia filtros con una sola petición y vuelve a todos los registros', async () => {
    obtenerBitacora.mockClear();
    obtenerBitacora.mockReturnValue(of(respuesta([registroAdmin])));
    component.fecha = '2026-08-24';
    component.usuario = 'ADMIN';
    component.accion = 'LOGIN';
    component.pagination.page = 2;

    component.limpiarFiltros();
    await fixture.whenStable();

    expect(obtenerBitacora).toHaveBeenCalledTimes(1);
    expect(obtenerBitacora).toHaveBeenCalledWith({
      fecha: '',
      usuario: '',
      accion: '',
      page: 1,
      limit: 20
    });
    expect(component.registros).toEqual([registroAdmin]);
    expect(component.loading).toBeFalsy();
  });

  it('bloquea acciones mientras carga sin cambiar filtros ni paginación', () => {
    const pendiente = new Subject<RespuestaBitacora>();
    obtenerBitacora.mockClear();
    obtenerBitacora.mockReturnValue(pendiente.asObservable());
    component.fecha = '2026-08-24';
    component.usuario = 'ADMIN';
    component.pagination.page = 2;

    void component.cargarBitacora();
    component.limpiarFiltros();
    component.buscar();

    expect(obtenerBitacora).toHaveBeenCalledTimes(1);
    expect(component.fecha).toBe('2026-08-24');
    expect(component.usuario).toBe('ADMIN');
    expect(component.pagination.page).toBe(2);

    pendiente.next(respuesta([registroAdmin]));
    pendiente.complete();
  });
});
