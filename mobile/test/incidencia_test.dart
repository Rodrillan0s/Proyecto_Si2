// Pruebas CU19 — Gestión de incidencias (mobile).
// No requieren red: las peticiones se capturan con un adaptador falso sobre el
// ApiClient real (mismo interceptor que adjunta el Bearer token).
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:emergencias_vehiculares/services/api_client.dart';
import 'package:emergencias_vehiculares/services/auth_provider.dart';
import 'package:emergencias_vehiculares/screens/incidencia_detalle_screen.dart';
import 'package:emergencias_vehiculares/screens/incidencias_screen.dart';
import 'package:emergencias_vehiculares/screens/incidencia_form_screen.dart';
import 'package:emergencias_vehiculares/services/incidencia_service.dart';
import 'package:emergencias_vehiculares/widgets/incidencia_widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

class _Capturada {
  final String method;
  final String path;
  final Map<String, dynamic> query;
  final Map<String, dynamic> headers;
  final Object? data;

  _Capturada(RequestOptions o)
      : method = o.method,
        path = o.path,
        query = Map<String, dynamic>.from(o.queryParameters),
        headers = Map<String, dynamic>.from(o.headers),
        data = o.data;
}

class _AdaptadorFalso implements HttpClientAdapter {
  final List<_Capturada> peticiones = [];
  int status = 200;
  Object body = {'success': true, 'data': []};
  List<int>? bytes;

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    peticiones.add(_Capturada(options));
    if (requestStream != null) await requestStream.drain<void>();
    if (bytes != null) return ResponseBody.fromBytes(bytes!, status);
    return ResponseBody.fromString(jsonEncode(body), status, headers: {
      Headers.contentTypeHeader: ['application/json'],
    });
  }

  @override
  void close({bool force = false}) {}
}

/// Responde según la ruta (para pantallas que hacen varias peticiones).
class _AdaptadorRutas implements HttpClientAdapter {
  final Map<String, Object> rutas;

  _AdaptadorRutas(this.rutas);

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    final body = rutas[options.path];
    return ResponseBody.fromString(jsonEncode(body ?? {'detail': 'no encontrado'}), body == null ? 404 : 200, headers: {
      Headers.contentTypeHeader: ['application/json'],
    });
  }

  @override
  void close({bool force = false}) {}
}

AuthProvider _auth(String rol) => AuthProvider()..loginExitoso({'nombre_rol': rol, 'id_empresa': '1'});

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  for (final rol in ['ELECTRICO', 'PLOMERO', 'MAESTROALBAÑIL', 'ALBAÑIL']) {
    testWidgets('$rol abre registro con obras permitidas sin responsable ni OT', (tester) async {
      FlutterSecureStorage.setMockInitialValues({'auth_token':'t', 'nro_usuario':'14'});
      ApiClient.dio.httpClientAdapter = _AdaptadorRutas({
        '/api/incidencias/': {'success':true, 'data':[], 'pagination':{'total_pages':0}},
        '/api/incidencias/obras-registro': {'success':true, 'data':[
          {'id_obra':5, 'codigo':'GT', 'nombre':'Green Tower'}
        ]},
        '/api/proyectos/5/unidades/': {'data':[]},
      });
      await tester.binding.setSurfaceSize(const Size(420, 1600));
      final auth = _auth(rol);
      expect(PermisosIncidencia.puedeRegistrar(auth), isTrue);
      for (final permiso in [PermisosIncidencia.visualizar, PermisosIncidencia.asignar,
        PermisosIncidencia.modificar, PermisosIncidencia.cerrar]) {
        expect(PermisosIncidencia.tiene(auth, permiso), isFalse);
      }
      await tester.pumpWidget(ChangeNotifierProvider<AuthProvider>.value(
        value:auth, child:const MaterialApp(home:IncidenciasScreen())));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Registrar incidencia'));
      await tester.pumpAndSettle();
      expect(find.text('PROYECTO / OBRA *'), findsOneWidget);
      expect(find.textContaining('Responsable'), findsNothing);
      expect(find.textContaining('Orden de trabajo'), findsNothing);
      await tester.tap(find.byType(DropdownButtonFormField<int>).first);
      await tester.pumpAndSettle();
      await tester.tap(find.text('GT · Green Tower').last);
      await tester.pumpAndSettle();
      expect(find.text('GT · Green Tower'), findsOneWidget);
      await tester.pumpWidget(const SizedBox());
      await tester.binding.setSurfaceSize(null);
    });
  }

  testWidgets('Unidad de Green Tower se selecciona y se limpia al cambiar de obra', (tester) async {
    FlutterSecureStorage.setMockInitialValues({'auth_token': 't', 'nro_usuario': '14'});
    ApiClient.dio.httpClientAdapter = _AdaptadorRutas({
      '/api/incidencias/obras-registro': {'success': true, 'data': [
        {'id_obra': 5, 'codigo': 'GT', 'nombre': 'Green Tower'},
        {'id_obra': 6, 'codigo': 'OTRA', 'nombre': 'Otra obra'},
      ]},
      '/api/proyectos/5/unidades/': {'data': [
        {'id_unidad': 7, 'codigo': 'UNI-000007', 'nombre': 'Unidad siete'},
      ]},
      '/api/proyectos/6/unidades/': {'data': []},
    });
    await tester.binding.setSurfaceSize(const Size(420, 1600));
    await tester.pumpWidget(ChangeNotifierProvider<AuthProvider>.value(
      value: _auth('ELECTRICO'), child: const MaterialApp(home: IncidenciaFormScreen(idObraInicial: 5))));
    await tester.pumpAndSettle();
    expect(find.text('UNIDAD'), findsOneWidget);
    await tester.tap(find.byType(DropdownButtonFormField<int?>));
    await tester.pumpAndSettle();
    await tester.tap(find.textContaining('UNI-000007').last);
    await tester.pumpAndSettle();
    expect(find.textContaining('UNI-000007'), findsOneWidget);
    await tester.tap(find.byType(DropdownButtonFormField<int>));
    await tester.pumpAndSettle();
    await tester.tap(find.textContaining('Otra obra').last);
    await tester.pumpAndSettle();
    expect(find.textContaining('UNI-000007'), findsNothing);
    expect(find.text('Sin unidades disponibles'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
    await tester.binding.setSurfaceSize(null);
  });

  // ── Permisos por rol (réplica de obras.t_rol_permiso) ──────────────────────
  group('PermisosIncidencia', () {
    test('JEFE DE OBRA: visualiza, registra, modifica y asigna; no cierra', () {
      final a = _auth('JEFE DE OBRA');
      expect(PermisosIncidencia.tiene(a, PermisosIncidencia.visualizar), isTrue);
      expect(PermisosIncidencia.tiene(a, PermisosIncidencia.registrar), isTrue);
      expect(PermisosIncidencia.tiene(a, PermisosIncidencia.modificar), isTrue);
      expect(PermisosIncidencia.tiene(a, PermisosIncidencia.asignar), isTrue);
      expect(PermisosIncidencia.tiene(a, PermisosIncidencia.cerrar), isFalse);
    });

    test('ADMINISTRADOR_EMPRESA tiene los 5 permisos', () {
      final a = _auth('ADMINISTRADOR_EMPRESA');
      for (final p in [
        PermisosIncidencia.visualizar,
        PermisosIncidencia.registrar,
        PermisosIncidencia.modificar,
        PermisosIncidencia.asignar,
        PermisosIncidencia.cerrar,
      ]) {
        expect(PermisosIncidencia.tiene(a, p), isTrue, reason: p);
      }
    });

    test('ADMINISTRADOR global: bypass igual que exigir_permiso', () {
      expect(PermisosIncidencia.tiene(_auth('ADMINISTRADOR'), PermisosIncidencia.cerrar), isTrue);
    });

    test('Oficios y CLIENTE no tienen permisos de incidencias', () {
      for (final rol in ['ELECTRICO', 'PLOMERO', 'ALBAÑIL', 'MAESTROALBAÑIL', 'CLIENTE']) {
        expect(PermisosIncidencia.tiene(_auth(rol), PermisosIncidencia.visualizar), isFalse, reason: rol);
      }
    });

    test('esResponsable compara con el usuario autenticado', () {
      expect(PermisosIncidencia.esResponsable({'id_responsable': 13}, 13), isTrue);
      expect(PermisosIncidencia.esResponsable({'id_responsable': 13}, 6), isFalse);
      expect(PermisosIncidencia.esResponsable({'id_responsable': null}, 13), isFalse);
      expect(PermisosIncidencia.esResponsable({'id_responsable': 13}, null), isFalse);
    });

    test('usuarioActual lee nro_usuario guardado al iniciar sesión', () async {
      FlutterSecureStorage.setMockInitialValues({'nro_usuario': '13'});
      expect(await PermisosIncidencia.usuarioActual(), 13);
    });
  });

  // ── Utilidades ─────────────────────────────────────────────────────────────
  group('Utilidades', () {
    test('etiquetaOrden', () {
      expect(IncidenciaService.etiquetaOrden(1), 'OT-001');
      expect(IncidenciaService.etiquetaOrden(1234), 'OT-1234');
    });

    test('tipoMimeImagen solo devuelve tipos aceptados por el backend', () {
      expect(IncidenciaService.tipoMimeImagen('a.PNG'), 'image/png');
      expect(IncidenciaService.tipoMimeImagen('a.webp'), 'image/webp');
      expect(IncidenciaService.tipoMimeImagen('a.jpg'), 'image/jpeg');
      expect(IncidenciaService.tipoMimeImagen('a.heic'), 'image/jpeg');
    });

    test('formatearFechaHora', () {
      expect(formatearFechaHora(null, vacio: 'Pendiente'), 'Pendiente');
      expect(formatearFechaHora('2026-09-01', conHora: false), '01/09/2026');
      final local = DateTime.parse('2026-09-30T22:19:53.707972-04:00').toLocal();
      expect(
        formatearFechaHora('2026-09-30T22:19:53.707972-04:00'),
        '${local.day.toString().padLeft(2, '0')}/${local.month.toString().padLeft(2, '0')}/${local.year} '
        '${local.hour.toString().padLeft(2, '0')}:${local.minute.toString().padLeft(2, '0')}',
      );
    });

    test('mensajeError para 401/403/404/409/500', () async {
      DioException err(int status, [Object? data]) => DioException(
            requestOptions: RequestOptions(path: '/x'),
            type: DioExceptionType.badResponse,
            response: Response(requestOptions: RequestOptions(path: '/x'), statusCode: status, data: data),
          );
      expect(await IncidenciaService.mensajeError(err(401)), contains('sesión'));
      expect(await IncidenciaService.mensajeError(err(403, {'detail': 'Solo el responsable asignado puede iniciar'})),
          contains('responsable'));
      expect(await IncidenciaService.mensajeError(err(404)), contains('no existe'));
      expect(await IncidenciaService.mensajeError(err(409)), contains('cambió de estado'));
      expect(await IncidenciaService.mensajeError(err(500, {'detail': 'traza interna'})), contains('servidor'));
    });
  });

  // ── Contratos HTTP (rutas, payloads, token) ────────────────────────────────
  group('Contratos con backend', () {
    late _AdaptadorFalso adaptador;
    final service = IncidenciaService();

    setUp(() {
      FlutterSecureStorage.setMockInitialValues({'auth_token': 'tkn-123'});
      adaptador = _AdaptadorFalso();
      ApiClient.dio.httpClientAdapter = adaptador;
    });

    test('listar: GET /api/incidencias/ con filtros, token automático y sin id_empresa', () async {
      adaptador.body = {
        'success': true,
        'data': [
          {'id_incidencia': 1, 'titulo': 'T'}
        ],
        'pagination': {'page': 1, 'limit': 20, 'total': 1, 'total_pages': 1},
      };
      final res = await service.listar(estado: 'ABIERTA', prioridad: 'ALTA', busqueda: '  fuga ', idObra: 8);
      final p = adaptador.peticiones.single;
      expect(p.method, 'GET');
      expect(p.path, '/api/incidencias/');
      expect(p.query, {'page': 1, 'limit': 20, 'id_obra': 8, 'prioridad': 'ALTA', 'estado': 'ABIERTA', 'busqueda': 'fuga'});
      expect(p.headers['Authorization'], 'Bearer tkn-123');
      expect(p.query.containsKey('id_empresa'), isFalse);
      expect((res['data'] as List).length, 1);
      expect((res['pagination'] as Map)['total'], 1);
    });

    test('listar asignadas envia solo el responsable y conserva paginacion', () async {
      adaptador.body = {'success': true, 'data': [], 'pagination': {'page': 2, 'total_pages': 3}};
      await service.listar(idResponsable: 14, page: 2);
      expect(adaptador.peticiones.last.query['id_responsable'], 14);
      expect(adaptador.peticiones.last.query['page'], 2);
      expect(adaptador.peticiones.last.query.containsKey('id_empresa'), isFalse);
    });

    test('registrar: POST con campos reales y sin estado/fechas/id_empresa', () async {
      adaptador.status = 201;
      adaptador.body = {'success': true, 'id_incidencia': 9, 'message': 'ok'};
      await service.registrar(
        idObra: 8,
        titulo: ' Fuga ',
        descripcion: ' Agua ',
        prioridad: 'CRITICA',
        ubicacion: '  ',
      );
      final p = adaptador.peticiones.single;
      expect(p.method, 'POST');
      expect(p.path, '/api/incidencias/');
      expect(p.data, {
        'id_obra': 8,
        'id_unidad': null,
        'titulo': 'Fuga',
        'descripcion': 'Agua',
        'prioridad': 'CRITICA',
        'ubicacion': null,
      });
    });

    test('registrar envia el ID real de UNI-000007 en Green Tower', () async {
      adaptador.status = 201;
      adaptador.body = {'success': true, 'id_incidencia': 21};
      await service.registrar(
        idObra: 8, idUnidad: 7, titulo: 'Falla',
        descripcion: 'Segundo piso', prioridad: 'ALTA',
      );
      final p = adaptador.peticiones.single;
      expect(p.path, '/api/incidencias/');
      expect((p.data as Map)['id_obra'], 8);
      expect((p.data as Map)['id_unidad'], 7);
    });

    test('actualizar: PUT /api/incidencias/{id}', () async {
      await service.actualizar(3, titulo: 'T', descripcion: 'D', prioridad: 'BAJA', ubicacion: 'Eje B');
      final p = adaptador.peticiones.single;
      expect(p.method, 'PUT');
      expect(p.path, '/api/incidencias/3');
      expect(p.data, {'titulo': 'T', 'descripcion': 'D', 'prioridad': 'BAJA', 'ubicacion': 'Eje B'});
    });

    test('asignarResponsable: PATCH /{id}/responsable', () async {
      await service.asignarResponsable(3, 13);
      expect(adaptador.peticiones.single.method, 'PATCH');
      expect(adaptador.peticiones.single.path, '/api/incidencias/3/responsable');
      expect(adaptador.peticiones.single.data, {'id_responsable': 13});
    });

    test('cambiarEstado: PATCH /{id}/estado sin fechas (las genera el servidor)', () async {
      await service.cambiarEstado(3, 'EN_PROCESO', observacion: '  ');
      expect(adaptador.peticiones.single.path, '/api/incidencias/3/estado');
      expect(adaptador.peticiones.single.data, {'estado': 'EN_PROCESO'});

      await service.cambiarEstado(3, 'PENDIENTE_VALIDACION', observacion: 'Sellado');
      expect(adaptador.peticiones.last.data, {'estado': 'PENDIENTE_VALIDACION', 'observacion': 'Sellado'});
    });

    test('OT afectadas: rutas de CU19 (no /api/ordenes-trabajo)', () async {
      await service.listarOrdenesTrabajoDisponibles(3);
      await service.actualizarOrdenesTrabajo(3, [1, 4]);
      expect(adaptador.peticiones[0].path, '/api/incidencias/3/ordenes-trabajo/disponibles');
      expect(adaptador.peticiones[1].method, 'PUT');
      expect(adaptador.peticiones[1].path, '/api/incidencias/3/ordenes-trabajo');
      expect(adaptador.peticiones[1].data, {'ordenes': [1, 4]});
    });

    test('seguimiento: GET y POST', () async {
      await service.listarSeguimiento(3);
      await service.registrarSeguimiento(3, ' Avance ');
      expect(adaptador.peticiones[0].path, '/api/incidencias/3/seguimiento');
      expect(adaptador.peticiones[1].method, 'POST');
      expect(adaptador.peticiones[1].data, {'observacion': 'Avance'});
    });

    test('subirEvidencia: multipart con campo archivo y tipo de imagen', () async {
      adaptador.status = 201;
      adaptador.body = {'success': true, 'id_evidencia': 5, 'message': 'ok'};
      await service.subirEvidencia(3, bytes: Uint8List.fromList([1, 2, 3]), nombreArchivo: 'foto.png');
      final p = adaptador.peticiones.single;
      expect(p.path, '/api/incidencias/3/evidencias');
      expect(p.data, isA<FormData>());
      final archivo = (p.data as FormData).files.single;
      expect(archivo.key, 'archivo');
      expect(archivo.value.filename, 'foto.png');
      expect(archivo.value.contentType.toString(), 'image/png');
      expect(p.headers['Authorization'], 'Bearer tkn-123');
    });

    test('descargarEvidencia: endpoint autenticado y bytes', () async {
      adaptador.bytes = [137, 80, 78, 71];
      final bytes = await service.descargarEvidencia(3, 5);
      expect(adaptador.peticiones.single.path, '/api/incidencias/3/evidencias/5/archivo');
      expect(adaptador.peticiones.single.headers['Authorization'], 'Bearer tkn-123');
      expect(bytes, [137, 80, 78, 71]);
    });

    test('errores HTTP se traducen a IncidenciaException con statusCode', () async {
      adaptador.status = 403;
      adaptador.body = {'detail': 'Solo el responsable asignado puede iniciar la atención de la incidencia.'};
      await expectLater(
        service.cambiarEstado(3, 'EN_PROCESO'),
        throwsA(isA<IncidenciaException>()
            .having((e) => e.statusCode, 'status', 403)
            .having((e) => e.mensaje, 'mensaje', contains('responsable'))),
      );
    });
  });

  // ── Detalle: acciones visibles según estado / permisos / responsable ───────
  group('IncidenciaDetalleScreen', () {
    Map<String, dynamic> detalle(String estado, {int? responsable = 13}) => {
          'id_incidencia': 3,
          'id_obra': 8,
          'obra_codigo': 'P-08',
          'obra_nombre': 'Green Tower',
          'id_usuario_registro': 6,
          'usuario_registro_nombre': 'Jefe',
          'id_responsable': responsable,
          'responsable_nombre': responsable == null ? null : 'Responsable',
          'titulo': 'Filtración de agua',
          'descripcion': 'Pared del Bloque 1',
          'prioridad': 'ALTA',
          'estado': estado,
          'ubicacion': 'Bloque 1',
          'created_at': '2026-09-30T10:00:00-04:00',
          'updated_at': '2026-09-30T10:00:00-04:00',
          'fecha_inicio_atencion': estado == 'EN_PROCESO' || estado == 'RESUELTA' ? '2026-09-30T11:00:00-04:00' : null,
          'fecha_fin_atencion': estado == 'RESUELTA' ? '2026-09-30T12:00:00-04:00' : null,
          'ordenes_trabajo': [
            {'orden_nro': 1, 'tipo_trab': 'Instalación sanitaria', 'estado': 'PENDIENTE', 'fecha_vinculo': '2026-09-30T10:05:00-04:00'},
          ],
        };

    Future<void> abrir(WidgetTester tester, {required String rol, required int nroUsuario, required Map<String, dynamic> inc}) async {
      FlutterSecureStorage.setMockInitialValues({'auth_token': 't', 'nro_usuario': '$nroUsuario'});
      ApiClient.dio.httpClientAdapter = _AdaptadorRutas({
        '/api/incidencias/3': {'success': true, 'data': inc},
        '/api/incidencias/3/seguimiento': {'success': true, 'data': []},
        '/api/incidencias/3/evidencias': {'success': true, 'data': []},
      });
      await tester.binding.setSurfaceSize(const Size(420, 2400));
      await tester.pumpWidget(ChangeNotifierProvider<AuthProvider>.value(
        value: _auth(rol),
        child: const MaterialApp(home: IncidenciaDetalleScreen(idIncidencia: 3)),
      ));
      // Las peticiones nacen en la zona de reloj simulado de testWidgets: se
      // avanza ese reloj hasta que la pantalla termine de cargar.
      for (var i = 0; i < 20 && find.text('Información general'.toUpperCase()).evaluate().isEmpty; i++) {
        await tester.pump(const Duration(milliseconds: 50));
        await tester.pump();
      }
      for (var i = 0; i < 5; i++) {
        await tester.pump();
      }
      expect(find.text('INFORMACIÓN GENERAL'), findsOneWidget, reason: 'el detalle debe haberse cargado');
    }

    testWidgets('Registrador ve ABIERTA sin responsable y sin acciones administrativas', (tester) async {
      final inc = detalle('ABIERTA', responsable:null)
        ..['id_usuario_registro'] = 14
        ..['usuario_registro_nombre'] = 'JHON JONES';
      await abrir(tester, rol:'ELECTRICO', nroUsuario:14, inc:inc);
      expect(find.text('JHON JONES'), findsOneWidget);
      expect(find.text('Sin asignar'), findsOneWidget);
      expect(find.text('Adjuntar'), findsOneWidget);
      for (final accion in ['Iniciar atención', 'Finalizar atención', 'Asignar responsable',
        'Reasignar responsable', 'Aprobar resolución', 'Cerrar incidencia']) {
        expect(find.text(accion), findsNothing);
      }
    });

    testWidgets('ELECTRICO responsable atiende sin permisos generales', (tester) async {
      await abrir(tester, rol: 'ELECTRICO', nroUsuario: 13, inc: detalle('ASIGNADA'));
      expect(find.text('Iniciar atención'), findsOneWidget);
      expect(find.text('Adjuntar'), findsOneWidget);
      expect(find.text('Reasignar responsable'), findsNothing);
      expect(find.byTooltip('Editar'), findsNothing);
      expect(find.text('Cerrar incidencia'), findsNothing);
      await tester.pumpWidget(const SizedBox.shrink());
      await abrir(tester, rol: 'ELECTRICO', nroUsuario: 13, inc: detalle('EN_PROCESO'));
      expect(find.text('Finalizar atención'), findsOneWidget);
    });

    testWidgets('Trabajador ajeno no ve acciones de atención', (tester) async {
      await abrir(tester, rol: 'PLOMERO', nroUsuario: 99, inc: detalle('ASIGNADA'));
      expect(find.text('Iniciar atención'), findsNothing);
      expect(find.text('Adjuntar'), findsNothing);
      expect(find.text('Reasignar responsable'), findsNothing);
    });

    for (final rol in ['ELECTRICO', 'PLOMERO', 'MAESTROALBAÑIL', 'ALBAÑIL']) {
      testWidgets('$rol registrador adjunta con Carlos responsable sin atender', (tester) async {
        for (final estado in ['ABIERTA', 'ASIGNADA', 'EN_PROCESO', 'PENDIENTE_VALIDACION', 'RESUELTA', 'CERRADA']) {
          await abrir(tester, rol: rol, nroUsuario: 6,
              inc: detalle(estado, responsable: estado == 'ABIERTA' ? null : 13));
          expect(find.text('Adjuntar'), estado == 'CERRADA' ? findsNothing : findsOneWidget);
          for (final accion in ['Iniciar atención', 'Finalizar atención', 'Asignar responsable',
            'Reasignar responsable', 'Aprobar resolución', 'Cerrar incidencia']) {
            expect(find.text(accion), findsNothing);
          }
          expect(find.byTooltip('Editar'), findsNothing);
          await tester.pumpWidget(const SizedBox.shrink());
        }
      });
    }

    testWidgets('Responsable con ASIGNADA ve "Iniciar atención"', (tester) async {
      await abrir(tester, rol: 'JEFE DE OBRA', nroUsuario: 13, inc: detalle('ASIGNADA'));
      expect(find.text('Iniciar atención'), findsOneWidget);
      expect(find.text('Filtración de agua'), findsOneWidget);
      expect(find.textContaining('OT-001'), findsOneWidget);
      expect(find.text('Bloque 1'), findsOneWidget);
    });

    testWidgets('No responsable con ASIGNADA no ve iniciar, ve aviso', (tester) async {
      await abrir(tester, rol: 'JEFE DE OBRA', nroUsuario: 6, inc: detalle('ASIGNADA'));
      expect(find.text('Iniciar atención'), findsNothing);
      expect(find.textContaining('Solo el responsable asignado puede iniciar'), findsOneWidget);
      expect(find.text('Reasignar responsable'), findsOneWidget);
    });

    testWidgets('Responsable con EN_PROCESO ve "Finalizar atención"', (tester) async {
      await abrir(tester, rol: 'JEFE DE OBRA', nroUsuario: 13, inc: detalle('EN_PROCESO'));
      expect(find.text('Finalizar atención'), findsOneWidget);
    });

    testWidgets('Pendiente: trabajador no valida; jefe y supervisor validan', (tester) async {
      await abrir(tester, rol: 'ELECTRICO', nroUsuario: 13, inc: detalle('PENDIENTE_VALIDACION'));
      expect(find.text('Validar resoluci\u00f3n'), findsNothing);
      expect(find.text('Finalizar atenci\u00f3n'), findsNothing);
      for (final rol in ['JEFE DE OBRA', 'SUPERVISOR']) {
        await abrir(tester, rol: rol, nroUsuario: 2, inc: detalle('PENDIENTE_VALIDACION'));
        expect(find.text('Validar resoluci\u00f3n'), findsOneWidget);
        expect(find.text('Aprobar resoluci\u00f3n'), findsOneWidget);
        expect(find.text('Rechazar resoluci\u00f3n'), findsOneWidget);
      }
    });

    testWidgets('RESUELTA: JEFE DE OBRA no cierra; ADMINISTRADOR_EMPRESA sí', (tester) async {
      await abrir(tester, rol: 'JEFE DE OBRA', nroUsuario: 13, inc: detalle('RESUELTA'));
      expect(find.text('Cerrar incidencia'), findsNothing);
      await abrir(tester, rol: 'ADMINISTRADOR_EMPRESA', nroUsuario: 2, inc: detalle('RESUELTA'));
      expect(find.text('Cerrar incidencia'), findsOneWidget);
    });

    testWidgets('CERRADA: sin acciones de edición', (tester) async {
      await abrir(tester, rol: 'ADMINISTRADOR_EMPRESA', nroUsuario: 2, inc: detalle('CERRADA'));
      expect(find.byTooltip('Editar'), findsNothing);
      expect(find.text('Adjuntar'), findsNothing);
      expect(find.text('Cerrar incidencia'), findsNothing);
      expect(find.text('Reasignar responsable'), findsNothing);
    });
  });

  // ── Widgets ────────────────────────────────────────────────────────────────
  testWidgets('IncidenciaChip muestra etiquetas legibles', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: Row(children: [IncidenciaChip.estado('EN_PROCESO'), IncidenciaChip.prioridad('CRITICA')]),
      ),
    ));
    expect(find.text('En proceso'), findsOneWidget);
    expect(find.text('Crítica'), findsOneWidget);
  });
}
