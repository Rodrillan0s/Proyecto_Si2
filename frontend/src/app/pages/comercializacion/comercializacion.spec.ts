import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi, describe, it, expect, beforeEach } from 'vitest';

import { ComercializacionComponent } from './comercializacion';
import { ComercializacionService, ResumenComercial, UnidadComercial } from '../../services/comercializacion.service';
import { ProyectosService } from '../../services/proyectos';
import { CrmService, ClienteCRM } from '../../services/crm.service';
import { AuthService } from '../../services/auth';
import { ContextoOperativo } from '../../services/contexto-operativo';

describe('CU31 — ComercializacionComponent (Frontend)', () => {
  let component: ComercializacionComponent;
  let fixture: ComponentFixture<ComercializacionComponent>;

  let mockComercializacionService: any;
  let mockProyectosService: any;
  let mockCrmService: any;
  let mockAuthService: any;
  let mockContextoOperativo: any;

  const mockResumen: ResumenComercial = {
    total_unidades: 2,
    total_publicadas: 1,
    total_no_publicadas: 1,
    por_estado_comercial: {
      DISPONIBLE: 1,
      RESERVADA: 1,
      VENDIDA: 0,
      NO_DISPONIBLE: 0
    },
    disponibles_efectivas: 1,
    kpis_financieros: {
      valor_inventario_disponible: 85000,
      valor_inventario_reservado: 95000,
      valor_inventario_vendido: 0
    }
  };

  const mockUnidades: UnidadComercial[] = [
    {
      id_unidad: 101,
      id_obra: 1,
      nombre_obra: 'Torre Mirador',
      codigo_obra: 'TM',
      id_estructura: 2,
      nombre_estructura: 'Piso 10',
      codigo: 'DPTO-1001',
      tipo_unidad: 'DEPARTAMENTO',
      superficie: 85.5,
      estado_constructivo: 'EN_CONSTRUCCION',
      publicado_comercial: true,
      precio_venta: 85000,
      moneda_comercial: 'BOB',
      descripcion_comercial: 'Hermosa vista y acabados de lujo',
      estado_comercial: 'DISPONIBLE',
      disponible_efectiva: true,
      total_fotos: 2,
      foto_principal: '/api/comercializacion/unidades/101/fotos/1/archivo'
    },
    {
      id_unidad: 102,
      id_obra: 1,
      nombre_obra: 'Torre Mirador',
      codigo_obra: 'TM',
      id_estructura: 2,
      nombre_estructura: 'Piso 10',
      codigo: 'DPTO-1002',
      tipo_unidad: 'DEPARTAMENTO',
      superficie: 90.0,
      estado_constructivo: 'FINALIZADO',
      publicado_comercial: false,
      precio_venta: 95000,
      moneda_comercial: 'BOB',
      descripcion_comercial: null,
      estado_comercial: 'RESERVADA',
      disponible_efectiva: false,
      total_fotos: 0,
      foto_principal: null
    }
  ];

  const mockCliente: ClienteCRM = {
    id_cliente: 42,
    id_empresa: 1,
    id_persona: 10,
    nombre_completo: 'Carlos Montaño',
    ci: '1234567-LP',
    telefono: '77788990',
    email: 'carlos@example.com',
    tipo_cliente: 'CLIENTE',
    estado: 'ACTIVO',
    origen: 'REFERIDO',
    created_at: '2026-11-20T10:00:00Z',
    updated_at: '2026-11-20T10:00:00Z'
  };

  beforeEach(async () => {
    mockComercializacionService = {
      listarUnidades: vi.fn().mockReturnValue(of({ data: mockUnidades, total: 2, page: 1, limit: 15 })),
      obtenerResumen: vi.fn().mockReturnValue(of(mockResumen)),
      cambiarPublicacion: vi.fn().mockReturnValue(of({ mensaje: 'Publicación actualizada' })),
      actualizarComercializacion: vi.fn().mockReturnValue(of({ ...mockUnidades[0], precio_venta: 95000, publicado_comercial: true })),
      registrarReserva: vi.fn().mockReturnValue(of({ mensaje: 'Reserva registrada', id_cliente_unidad: 55, estado_comercial: 'RESERVADA' })),
      cancelarReserva: vi.fn().mockReturnValue(of({ mensaje: 'Reserva cancelada', estado_comercial: 'DISPONIBLE' })),
      confirmarVenta: vi.fn().mockReturnValue(of({ mensaje: 'Venta confirmada', estado_comercial: 'VENDIDA' })),
      cambiarEstado: vi.fn().mockReturnValue(of({ mensaje: 'Estado cambiado' })),
      listarFotografias: vi.fn().mockReturnValue(of({ fotografias: [] })),
      listarHistorial: vi.fn().mockReturnValue(of({
        historial: [
          {
            id_historial: 1,
            id_unidad: 101,
            tipo_evento: 'PUBLICACION',
            estado_anterior: 'DISPONIBLE',
            estado_nuevo: 'DISPONIBLE',
            precio_venta: 85000,
            fecha: '2026-11-22T10:00:00Z',
            usuario_registro: 'Admin User'
          }
        ]
      })),
      obtenerUrlFotografia: vi.fn().mockReturnValue('/api/comercializacion/unidades/101/fotos/1/archivo')
    };

    mockProyectosService = {
      listarProyectos: vi.fn().mockReturnValue(of({
        data: [{ id_obra: 1, nombre: 'Torre Mirador' }]
      }))
    };

    mockCrmService = {
      listarClientes: vi.fn().mockReturnValue(of({ data: [mockCliente], total: 1 }))
    };

    mockAuthService = {
      usuario: { nombre: 'Test User', rol: 'ADMINISTRADOR_EMPRESA', id_empresa: 1 },
      hasRole: vi.fn().mockReturnValue(true),
      hasPermission: vi.fn().mockReturnValue(true)
    };

    mockContextoOperativo = {
      idEmpresa: 1,
      idObraSeleccionada: 1
    };

    await TestBed.configureTestingModule({
      imports: [ComercializacionComponent],
      providers: [
        { provide: ComercializacionService, useValue: mockComercializacionService },
        { provide: ProyectosService, useValue: mockProyectosService },
        { provide: CrmService, useValue: mockCrmService },
        { provide: AuthService, useValue: mockAuthService },
        { provide: ContextoOperativo, useValue: mockContextoOperativo }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ComercializacionComponent);
    component = fixture.componentInstance;
  });

  // PRUEBA 1: Carga/listado y filtros
  it('1. Carga inicial, listado de unidades, resumen de KPIs y aplicación de filtros', () => {
    fixture.detectChanges();

    expect(component.unidades.length).toBe(2);
    expect(component.total).toBe(2);
    expect(component.resumen).toBeTruthy();
    expect(component.resumen?.por_estado_comercial.DISPONIBLE).toBe(1);
    expect(component.resumen?.por_estado_comercial.RESERVADA).toBe(1);
    expect(component.obras.length).toBe(1);

    // Aplicar filtro por estado comercial
    component.filtroEstadoComercial = 'DISPONIBLE';
    component.cambiarFiltro();

    expect(mockComercializacionService.listarUnidades).toHaveBeenCalledWith(
      expect.objectContaining({
        estado_comercial: 'DISPONIBLE',
        page: 1,
        limit: 15
      })
    );
  });

  // PRUEBA 2: Reserva exitosa y actualización de estado
  it('2. Registrar reserva exitosa con cliente CRM y actualización a RESERVADA', () => {
    fixture.detectChanges();

    const unidadDisponible = { ...mockUnidades[0] };
    component.abrirModalReserva(unidadDisponible);

    expect(component.mostrarModalReserva).toBe(true);
    expect(component.unidadSeleccionada?.id_unidad).toBe(101);
    expect(mockCrmService.listarClientes).toHaveBeenCalled();

    // Seleccionar cliente y configurar monto
    component.seleccionarClienteReserva(mockCliente);
    component.formReserva.monto_reserva = 1500;
    component.formReserva.observaciones = 'Reserva acordada por 15 días';

    component.confirmarReserva();

    expect(mockComercializacionService.registrarReserva).toHaveBeenCalledWith(
      101,
      expect.objectContaining({
        id_cliente: 42,
        monto_reserva: 1500,
        observaciones: 'Reserva acordada por 15 días'
      })
    );

    expect(component.mostrarModalReserva).toBe(false);
    expect(component.mensajeExito).toContain('registrada exitosamente');
  });

  // PRUEBA 3: Edición comercial e historial cronológico
  it('3. Edición comercial de precio/publicación y consulta de historial comercial', () => {
    fixture.detectChanges();

    const unidad = { ...mockUnidades[0] };

    // HU143: Edición
    component.abrirModalEditar(unidad);
    expect(component.mostrarModalEditar).toBe(true);
    component.formEdicion.precio_venta = 95000;
    component.formEdicion.publicado_comercial = true;
    component.guardarEdicion();

    expect(mockComercializacionService.actualizarComercializacion).toHaveBeenCalledWith(
      101,
      expect.objectContaining({
        precio_venta: 95000,
        publicado_comercial: true
      })
    );
    expect(component.mostrarModalEditar).toBe(false);

    // HU146: Historial
    component.abrirModalHistorial(unidad);
    expect(component.mostrarModalHistorial).toBe(true);
    expect(mockComercializacionService.listarHistorial).toHaveBeenCalledWith(101, undefined, 100);
    expect(component.historialEventos.length).toBe(1);
    expect(component.historialEventos[0].tipo_evento).toBe('PUBLICACION');
  });
});
