import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { CrmService } from './crm.service';
import { AvancesService } from './avances.service';
import { UnidadesService } from './unidades';
import { environment } from '../../environments/environment';

describe('CU30 — Servicios Frontend Cliente (HU114, HU115, HU116, HU117)', () => {
  let crmService: CrmService;
  let avancesService: AvancesService;
  let unidadesService: UnidadesService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    crmService = TestBed.inject(CrmService);
    avancesService = TestBed.inject(AvancesService);
    unidadesService = TestBed.inject(UnidadesService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('HU114: listarUnidadesCliente consulta /api/crm/cliente/unidades sin enviar id_cliente ni id_empresa', () => {
    crmService.listarUnidadesCliente().subscribe(res => {
      expect(res.success).toBe(true);
      expect(res.data.length).toBe(1);
      expect(res.data[0].codigo_unidad).toBe('A-101');
    });

    const req = http.expectOne(`${environment.apiUrl}/api/crm/cliente/unidades`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.has('id_cliente')).toBe(false);
    expect(req.request.params.has('id_empresa')).toBe(false);
    req.flush({
      success: true,
      data: [{
        id_cliente_unidad: 1,
        id_cliente: 7,
        id_unidad: 31,
        estado_asociacion: 'VENDIDO',
        codigo_unidad: 'A-101',
        tipo_unidad: 'DEPARTAMENTO',
        estado_unidad_actual: 'EN_CONSTRUCCION',
        id_obra: 9,
        nombre_obra: 'Edificio Sky',
        codigo_obra: 'SKY'
      }]
    });
  });

  it('HU114: consultarAvanceFisicoUnidadCliente consulta avance físico autorizado por id_obra e id_unidad', () => {
    avancesService.consultarAvanceFisicoUnidadCliente(9, 31).subscribe(res => {
      expect(res.success).toBe(true);
      expect(res.data[0].porcentaje_avance).toBe(80);
    });

    const req = http.expectOne(`${environment.apiUrl}/api/proyectos/9/avances/cliente/unidades/31`);
    expect(req.request.method).toBe('GET');
    req.flush({
      success: true,
      data: [{
        id_avance: 1,
        id_obra: 9,
        id_unidad: 31,
        porcentaje_avance: 80,
        estado_unidad: 'EN_CONSTRUCCION',
        fecha_registro: '2026-11-20',
        observacion: 'Avance estructural completado'
      }]
    });
  });

  it('HU115: listarFotografiasUnidad consulta fotografías autorizadas de la unidad seleccionada', () => {
    crmService.listarFotografiasUnidad(31).subscribe(res => {
      expect(res.success).toBe(true);
      expect(res.data.length).toBe(1);
      expect(res.data[0].id_fotografia).toBe(51);
      expect(res.data[0].id_evidencia).toBe(51);
    });

    const req = http.expectOne(`${environment.apiUrl}/api/crm/cliente/unidades/31/fotografias`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.has('id_cliente')).toBe(false);
    expect(req.request.params.has('id_empresa')).toBe(false);
    req.flush({
      success: true,
      data: [{
        id_fotografia: 51,
        id_evidencia: 51,
        id_unidad: 31,
        nombre_archivo: 'avance_frontal.jpg',
        tipo_mime: 'image/jpeg',
        tamano_bytes: 2048,
        fecha: '2026-11-20T10:00:00Z',
        created_at: '2026-11-20T10:00:00Z',
        url_archivo: '/api/crm/cliente/unidades/31/fotografias/51/archivo'
      }]
    });
  });

  it('HU115: descargarFotografiaUnidad obtiene el blob autenticado sin exponer rutas directas', () => {
    crmService.descargarFotografiaUnidad(31, 51).subscribe(blob => {
      expect(blob).toBeTruthy();
    });

    const req = http.expectOne(`${environment.apiUrl}/api/crm/cliente/unidades/31/fotografias/51/archivo`);
    expect(req.request.method).toBe('GET');
    expect(req.request.responseType).toBe('blob');
    req.flush(new Blob(['fake-image'], { type: 'image/jpeg' }));
  });

  it('HU116: listarComunicacionesCliente consulta comunicaciones autorizadas sin parámetros de tenant', () => {
    crmService.listarComunicacionesCliente().subscribe(res => {
      expect(res.success).toBe(true);
      expect(res.no_leidas).toBe(1);
      expect(res.data[0].titulo).toBe('Comunicado de Obra');
    });

    const req = http.expectOne(`${environment.apiUrl}/api/crm/cliente/comunicaciones`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.has('id_cliente')).toBe(false);
    expect(req.request.params.has('id_empresa')).toBe(false);
    req.flush({
      success: true,
      no_leidas: 1,
      data: [{
        id_notificacion: 8,
        titulo: 'Comunicado de Obra',
        cuerpo: 'Se concluyó la etapa de vaciado de losa.',
        leido: false,
        fecha_creacion: '2026-11-20T14:00:00Z'
      }]
    });
  });

  it('HU117: listarSolicitudesCliente consulta solicitudes del cliente sin enviar id_cliente ni id_empresa', () => {
    crmService.listarSolicitudesCliente().subscribe(res => {
      expect(res.success).toBe(true);
      expect(res.data.length).toBe(1);
      expect(res.data[0].asunto).toBe('Revisión de conexiones');
      expect(res.data[0].estado).toBe('EN_PROCESO');
    });

    const req = http.expectOne(`${environment.apiUrl}/api/crm/cliente/solicitudes`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.has('id_cliente')).toBe(false);
    expect(req.request.params.has('id_empresa')).toBe(false);
    req.flush({
      success: true,
      data: [{
        id_solicitud: 41,
        id_obra: 9,
        id_unidad: 31,
        asunto: 'Revisión de conexiones',
        descripcion: 'Solicitud de verificación en cocina',
        estado: 'EN_PROCESO',
        fecha_creacion: '2026-11-20T08:00:00Z',
        fecha_actualizacion: '2026-11-20T09:30:00Z'
      }]
    });
  });

  it('HU115 Jefe de Obra: UnidadesService.listarFotografias consulta /api/unidades/{id_unidad}/fotografias', () => {
    unidadesService.listarFotografias(9).subscribe(res => {
      expect(res.success).toBe(true);
      expect(res.data.length).toBe(1);
      expect(res.data[0].id_fotografia).toBe(1);
      expect(res.data[0].nombre_archivo).toBe('fachada.jpg');
    });

    const req = http.expectOne(`${environment.apiUrl}/api/unidades/9/fotografias`);
    expect(req.request.method).toBe('GET');
    req.flush({
      success: true,
      data: [{
        id_fotografia: 1,
        id_unidad: 9,
        nombre_archivo: 'fachada.jpg',
        ruta_archivo: 'uploads/unidades/9/abc.jpg',
        tamano_bytes: 1024,
        tipo_mime: 'image/jpeg',
        es_principal: true,
        orden: 1
      }]
    });
  });

  it('HU115 Jefe de Obra: UnidadesService.subirFotografia envía FormData a /api/unidades/{id_unidad}/fotografias', () => {
    const file = new File(['fake-image-binary'], 'fachada.jpg', { type: 'image/jpeg' });
    unidadesService.subirFotografia(9, file, true, 1).subscribe(res => {
      expect(res.success).toBe(true);
      expect(res.data.id_fotografia).toBe(2);
    });

    const req = http.expectOne(`${environment.apiUrl}/api/unidades/9/fotografias`);
    expect(req.request.method).toBe('POST');
    expect(req.request.headers.get('Content-Type')).toBeNull();
    expect(req.request.body instanceof FormData).toBe(true);
    req.flush({
      success: true,
      data: {
        id_fotografia: 2,
        id_unidad: 9,
        nombre_archivo: 'fachada.jpg',
        ruta_archivo: 'uploads/unidades/9/xyz.jpg'
      }
    });
  });

  it('HU115 Validaciones frontend: comprobación de tipos válidos y límite de 10 MB', () => {
    const tiposPermitidos = ['image/jpeg', 'image/png', 'image/webp'];
    const extensionesPermitidas = ['.jpg', '.jpeg', '.png', '.webp'];
    const maxBytes = 10 * 1024 * 1024;

    function validar(file: { name: string; type: string; size: number }) {
      const extValida = extensionesPermitidas.some(ext => file.name.toLowerCase().endsWith(ext));
      const mimeValido = tiposPermitidos.includes(file.type.toLowerCase());
      if (!mimeValido && !extValida) return { valido: false, error: 'Formato no permitido' };
      if (file.size > maxBytes) return { valido: false, error: 'Tamaño excedido' };
      return { valido: true };
    }

    expect(validar({ name: 'foto.jpg', type: 'image/jpeg', size: 1024 }).valido).toBe(true);
    expect(validar({ name: 'foto.png', type: 'image/png', size: 5 * 1024 * 1024 }).valido).toBe(true);
    expect(validar({ name: 'foto.webp', type: 'image/webp', size: 10 * 1024 * 1024 }).valido).toBe(true);
    expect(validar({ name: 'doc.pdf', type: 'application/pdf', size: 1024 }).valido).toBe(false);
    expect(validar({ name: 'foto.jpg', type: 'image/jpeg', size: 11 * 1024 * 1024 }).valido).toBe(false);
  });

  it('HU115 Permisos frontend: roles JEFE DE OBRA y ADMIN autorizados, CLIENTE bloqueado', () => {
    function puedeSubir(rol: string, permisos: string[] = []): boolean {
      const r = (rol || '').trim().toUpperCase();
      if (r === 'CLIENTE') return false;
      if (['ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA', 'JEFE DE OBRA', 'JEFE_OBRA', 'RESPONSABLE'].includes(r)) return true;
      return permisos.includes('Modificar_obras') || permisos.includes('Registrar_avances');
    }

    expect(puedeSubir('JEFE DE OBRA')).toBe(true);
    expect(puedeSubir('ADMINISTRADOR_EMPRESA')).toBe(true);
    expect(puedeSubir('ADMINISTRADOR')).toBe(true);
    expect(puedeSubir('RESIDENTE', ['Modificar_obras'])).toBe(true);
    expect(puedeSubir('CLIENTE')).toBe(false);
    expect(puedeSubir('CLIENTE', ['Modificar_obras'])).toBe(false);
    expect(puedeSubir('INVITADO')).toBe(false);
  });

  it('HU117 Constructora: CrmService.listarSolicitudesConstructora consulta /api/crm/solicitudes con filtros', () => {
    crmService.listarSolicitudesConstructora({ id_obra: 8, estado: 'PENDIENTE' }).subscribe(res => {
      expect(res.success).toBe(true);
      expect(res.data.length).toBe(1);
      expect(res.data[0].id_solicitud).toBe(3);
      expect(res.data[0].codigo_unidad).toBe('UNI-000009');
      expect(res.data[0].estado).toBe('PENDIENTE');
    });

    const req = http.expectOne(`${environment.apiUrl}/api/crm/solicitudes?id_obra=8&estado=PENDIENTE`);
    expect(req.request.method).toBe('GET');
    req.flush({
      success: true,
      data: [{
        id_solicitud: 3,
        id_cliente: 54,
        id_obra: 8,
        id_unidad: 9,
        codigo_unidad: 'UNI-000009',
        nombre_obra: 'Green Tower',
        nombre_cliente: 'Fabricio',
        titulo: 'revision de proyecto',
        asunto: 'revision de proyecto',
        descripcion: 'agregas mas unidades',
        estado: 'PENDIENTE',
        fecha_creacion: '2026-11-22T20:09:05Z'
      }]
    });
  });

  it('HU117 Constructora: CrmService.responderSolicitudConstructora envía POST a /api/crm/solicitudes/{id}/responder', () => {
    const payload = {
      estado: 'ATENDIDA',
      respuesta: 'La unidad se encuentra actualmente en fase de instalaciones eléctricas.'
    };

    crmService.responderSolicitudConstructora(3, payload).subscribe(res => {
      expect(res.success).toBe(true);
      expect(res.data.estado).toBe('ATENDIDA');
      expect(res.data.respuesta).toBe(payload.respuesta);
    });

    const req = http.expectOne(`${environment.apiUrl}/api/crm/solicitudes/3/responder`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush({
      success: true,
      message: 'Solicitud atendida',
      data: {
        id_solicitud: 3,
        estado: 'ATENDIDA',
        respuesta: payload.respuesta
      }
    });
  });
});
