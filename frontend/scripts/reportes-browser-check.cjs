/* Prueba local con Edge/Chromium iniciado en --remote-debugging-port=9223.
 * Todos los endpoints API y WebSocket se sustituyen por fixtures sintéticos.
 * No requiere cuenta real, base de datos, proveedor IA ni correo.
 * ng serve --host 127.0.0.1 --port 4201; node scripts/reportes-browser-check.cjs
 */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const output = path.resolve('.angular/reportes-preview');
fs.mkdirSync(output, { recursive: true });
const catalog = {
  id_empresa: 7,
  acciones: ['Visualizar_reportes', 'Exportar_reportes', 'Enviar_reportes', 'Programar_reportes'],
  obras: [{ id_obra: 9, nombre: 'Residencial Alameda', codigo: 'ALM' }],
  reportes: [
    {
      id: 'stock',
      titulo: 'Stock de materiales',
      descripcion: 'Existencias actuales de los almacenes de tu empresa.',
      fechas: false,
      requiere_obra: false,
    },
    {
      id: 'incidencias',
      titulo: 'Incidencias',
      descripcion: 'Incidencias registradas en las obras autorizadas.',
      fechas: true,
      requiere_obra: false,
    },
    {
      id: 'comparativo_costos',
      titulo: 'Comparativo de costos',
      descripcion: 'Comparación de presupuesto y ejecución por obra.',
      fechas: false,
      requiere_obra: true,
    },
  ],
};
const execution = {
  id: 'fixture-execution',
  estado: 'LISTO',
  created_at: '2026-10-04T18:00:00Z',
  solicitud: { reporte: 'stock', filtros: {} },
  resultado: {
    titulo: 'Stock de materiales',
    corte: '2026-10-04T18:00:00Z',
    solicitud: { reporte: 'stock', filtros: {} },
    resumen: { materiales: 3, bajo_minimo: 1 },
    advertencias: ['Existencias actuales; no se estima demanda futura.'],
    recomendaciones: [{ material: 'Cemento', recomendacion: 'Revisar stock bajo el mínimo.' }],
    columnas: [
      { campo: 'nombre', titulo: 'Material', tipo: 'text' },
      { campo: 'cantidad', titulo: 'Stock actual', tipo: 'number' },
      { campo: 'unidad', titulo: 'Unidad', tipo: 'text' },
    ],
    filas: [
      { nombre: 'Cemento Portland', cantidad: '128.00', unidad: 'Bolsa' },
      { nombre: 'Acero corrugado', cantidad: '62.00', unidad: 'Barra' },
      { nombre: 'Arena fina', cantidad: '18.50', unidad: 'm³' },
    ],
  },
};
let generated = false;
const requests = [];
const errors = [];
let schedule;
(async () => {
  const targets = await (await fetch('http://127.0.0.1:9223/json/list')).json();
  const ws = new WebSocket(targets.find((t) => t.type === 'page').webSocketDebuggerUrl);
  await new Promise((resolve) => ws.addEventListener('open', resolve, { once: true }));
  let serial = 0;
  const pending = new Map();
  const send = (method, params = {}) =>
    new Promise((resolve, reject) => {
      const id = ++serial;
      pending.set(id, { resolve, reject });
      ws.send(JSON.stringify({ id, method, params }));
    });
  ws.addEventListener('message', async (event) => {
    const data = JSON.parse(event.data);
    if (data.id) {
      const item = pending.get(data.id);
      pending.delete(data.id);
      if (data.error) item.reject(data.error);
      else item.resolve(data.result);
      return;
    }
    if (data.method === 'Runtime.exceptionThrown')
      errors.push(
        data.params.exceptionDetails.text +
          ' ' +
          (data.params.exceptionDetails.exception?.description || ''),
      );
    if (data.method !== 'Fetch.requestPaused') return;
    const request = data.params.request;
    const pathname = new URL(request.url).pathname;
    requests.push({ pathname, method: request.method });
    let body = {};
    let status = 200;
    if (pathname.endsWith('/proyectos/')) body = { success: true, data: [{ id_obra: 9, id_empresa: 7, nombre: 'Residencial Alameda', codigo: 'ALM', estado: 'PLANIFICACION' }] };
    else if (pathname.endsWith('/materiales')) body = { success: true, data: [], pagination: { total: 0 } };
    else if (pathname.endsWith('/proveedores')) body = { success: true, data: [], pagination: { total: 0 } };
    else if (pathname.endsWith('/empresas/')) body = { success: true, data: [{ id_empresa: 7, nombre_empresa: 'Constructora Alameda' }, { id_empresa: 8, nombre_empresa: 'Constructora Norte' }] };
    else if (pathname.endsWith('/catalogo')) body = catalog;
    else if (pathname.endsWith('/destinatarios'))
      body = [
        { id_usuario: 2, nombre: 'María López' },
        { id_usuario: 3, nombre: 'Carlos Rivera' },
      ];
    else if (pathname.endsWith('/ejecuciones') && request.method === 'POST') {
      generated = true;
      body = execution;
    } else if (pathname.endsWith('/ejecuciones')) body = generated ? [execution] : [];
    else if (pathname.endsWith('/fixture-execution')) body = execution;
    else if (pathname.endsWith('/envios'))
      body = request.method === 'GET' ? [] : { estado: 'PENDIENTE' };
    else if (pathname.endsWith('/programaciones') && request.method === 'POST') {
      schedule = {
        id: 'fixture-schedule',
        habilitada: true,
        estado: 'ACTIVA',
        next_run: '2026-10-05T12:00:00Z',
        configuracion: JSON.parse(request.postData),
      };
      body = schedule;
    } else if (pathname.endsWith('/programaciones')) body = schedule ? [schedule] : [];
    else if (pathname.endsWith('/ai/consulta')) {
      generated = true;
      body = {
        estado: 'ready',
        conversacion: 'fixture-conversation',
        mensaje: 'Listo',
        respuesta: 'Hay 3 materiales registrados. Uno está por debajo del stock mínimo.',
        ejecucion: execution,
      };
    } else if (pathname.endsWith('/crm/consulta'))
      body = { success: true, respuesta: 'Hay dos prospectos en negociación.' };
    else if (pathname.includes('/notificaciones')) body = { success: true, data: [] };
    else if (pathname.endsWith('/interpretar'))
      body = {
        estado: 'ready',
        mensaje: 'Filtros preparados.',
        conversacion: 'fixture-conversation',
        solicitud: execution.solicitud,
      };
    else {
      status = 404;
      body = { detail: 'Endpoint no incluido en esta prueba local.' };
    }
    await send('Fetch.fulfillRequest', {
      requestId: data.params.requestId,
      responseCode: request.method === 'OPTIONS' ? 204 : status,
      responseHeaders: [
        { name: 'Content-Type', value: 'application/json' },
        { name: 'Access-Control-Allow-Origin', value: '*' },
        { name: 'Access-Control-Allow-Headers', value: '*' },
        { name: 'Access-Control-Allow-Methods', value: '*' },
      ],
      body: Buffer.from(request.method === 'OPTIONS' ? '' : JSON.stringify(body)).toString(
        'base64',
      ),
    });
  });
  const evaluate = async (expression) => {
    const result = await send('Runtime.evaluate', {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
    return result.result.value;
  };
  const wait = async (expression) => {
    const until = Date.now() + 15000;
    while (Date.now() < until) {
      if (await evaluate(expression)) return;
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
    throw new Error('Tiempo agotado: ' + expression);
  };
  const click = async (text) => {
    await evaluate(
      `Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === ${JSON.stringify(text)}).click()`,
    );
  };
  const screenshot = async (name) => {
    const image = await send('Page.captureScreenshot');
    fs.writeFileSync(path.join(output, name + '.png'), Buffer.from(image.data, 'base64'));
  };
  await send('Runtime.enable');
  await send('Page.enable');
  await send('Fetch.enable', {
    patterns: [{ urlPattern: '*127.0.0.1:5000*', requestStage: 'Request' }],
  });
  await send('Page.addScriptToEvaluateOnNewDocument', {
    source: `localStorage.setItem('token','fixture.' + btoa(JSON.stringify({exp:4102444800})) + '.fixture'); localStorage.setItem('usuario', JSON.stringify({nro_usuario:1,id_empresa:7,nombre_empresa:'Constructora Alameda',nombre_rol:'ADMINISTRADOR',nombre_completo:'Usuario de prueba',permisos:['Visualizar_reportes','Exportar_reportes','Enviar_reportes','Programar_reportes','Visualizar_clientes']})); localStorage.setItem('empresa_seleccionada',JSON.stringify({id_empresa:7,nombre_empresa:'Constructora Alameda'})); window.WebSocket = class {close(){} send(){}};`,
  });
  await send('Emulation.setDeviceMetricsOverride', {
    width: 1366,
    height: 900,
    deviceScaleFactor: 1,
    mobile: false,
  });
  await send('Page.navigate', { url: 'http://127.0.0.1:4201/reportes' });
  await wait(
    `document.querySelector('.generate') && !document.querySelector('.generate').disabled`,
  );
  await screenshot('desktop-empty');
  assert.ok(!requests.some(request => request.pathname.endsWith('/auth/contexto')), 'No debe existir dependencia de un endpoint nuevo');
  assert.ok(!requests.some(request => request.pathname.endsWith('/destinatarios') || request.pathname.endsWith('/programaciones') || request.pathname.endsWith('/ejecuciones')), 'No cargar pestañas auxiliares antes de necesitarlas');
  await evaluate(`document.querySelector('.hamburger-btn').click()`);
  await wait(`document.querySelector('aside.is-collapsed')`);
  assert.equal(await evaluate(`document.querySelector('aside').getBoundingClientRect().width`), 68);
  await screenshot('desktop-sidebar-icons');
  await evaluate(`document.querySelector('.hamburger-btn').click()`);
  await evaluate(`document.querySelector('[aria-label="Seleccionar obra"]').click()`);
  await wait(`document.querySelector('[data-work-selector] select option[value="9"]')`);
  await evaluate(`(() => { const select = document.querySelector('[data-work-selector] select'); select.value='9'; select.dispatchEvent(new Event('change',{bubbles:true})); })()`);
  await wait(`document.querySelector('[data-work-selector] button').textContent.includes('Residencial')`);

  await evaluate(`document.querySelector('.generate').click()`);
  await wait(`document.querySelector('.result table')`);
  await screenshot('desktop-result');
  assert.equal(await evaluate(`document.querySelectorAll('.result tbody tr').length`), 3);
  await wait(`document.querySelector('.recipients input')`);
  await evaluate(`document.querySelector('.recipients input').click()`);
  await click('Enviar reporte');
  await wait(`document.querySelector('.notice')?.textContent.includes('Solicitud de envío')`);
  await evaluate(`document.querySelector('.schedule-form').open = true`);
  await click('Guardar programación');
  await wait(`document.querySelector('.job h3')?.textContent.includes('Stock')`);
  assert.equal(schedule.configuracion.destinatarios[0], 2);
  await click('Generar reporte');
  await evaluate(`document.querySelector('.launcher').click()`);
  await wait(`document.querySelector('#assistant-input')`);
  await evaluate(
    `const input = document.querySelector('#assistant-input'); input.value='reporte de stock'; input.dispatchEvent(new Event('input',{bubbles:true}));`,
  );
  await evaluate(
    `document.querySelector('.composer').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))`,
  );
  await wait(`document.querySelector('.report-actions')`);
  await screenshot('desktop-chat');
  await evaluate(`document.querySelector('[title="Modo Oscuro"]').click()`);
  await new Promise((resolve) => setTimeout(resolve, 400));
  await screenshot('desktop-dark');
  await send('Emulation.setDeviceMetricsOverride', {
    width: 390,
    height: 844,
    deviceScaleFactor: 1,
    mobile: true,
  });
  await new Promise((resolve) => setTimeout(resolve, 400));
  await screenshot('mobile-chat');
  const bounds = await evaluate(
    `JSON.stringify({width:innerWidth,panel:document.querySelector('.assistant').getBoundingClientRect().toJSON()})`,
  );
  const measured = JSON.parse(bounds);
  assert.ok(measured.panel.left >= 0 && measured.panel.right <= measured.width);
  assert.ok(measured.panel.top >= 72, 'El asistente queda oculto detrás de la cabecera');
  await evaluate(`document.querySelector('.assistant .icon-button').click()`);
  await evaluate(`document.querySelector('[title="Modo Oscuro"]').click()`);
  await new Promise((resolve) => setTimeout(resolve, 400));
  await screenshot('mobile-result');
  assert.ok(
    await evaluate(`document.documentElement.scrollWidth <= innerWidth`),
    'La página desborda el ancho móvil',
  );
  await evaluate(`document.querySelector('.hamburger-btn').click()`);
  await wait(`document.querySelector('.sidebar-open')`);
  await screenshot('mobile-sidebar');
  await evaluate(`document.querySelector('.sidebar-backdrop').click()`);
  await send('Emulation.setDeviceMetricsOverride', { width: 1366, height: 900, deviceScaleFactor: 1, mobile: false });
  await evaluate(`(() => { const input = document.querySelector('.search-box input'); input.value='reporte de stock'; input.dispatchEvent(new Event('input',{bubbles:true})); document.querySelector('.search-btn').click(); })()`);
  await wait(`document.querySelector('.assistant.quick-mode .message:not(.user)')`);
  await screenshot('desktop-quick-query');
  await evaluate(`document.querySelector('[aria-label="Abrir conversación completa"]').click()`);
  await wait(`document.querySelector('.assistant:not(.quick-mode)')`);
  await evaluate(`document.querySelector('.assistant [aria-label="Cerrar asistente"]').click()`);
  await evaluate(`document.querySelector('[aria-label="INTELIGENCIA ARTIFICIAL"]').click()`);
  await evaluate(`document.querySelector('a[aria-label="Asistente Inteligente"]').click()`);
  await wait(`document.querySelector('.assistant.module-mode')`);
  assert.equal(await evaluate(`document.querySelectorAll('app-asistente').length`), 1);
  assert.equal(await evaluate(`document.querySelector('.launcher') === null`), true);
  await screenshot('desktop-assistant-workspace');
  await evaluate(`document.querySelector('a[aria-label="Dashboard"]').click()`);
  await wait(`document.querySelector('app-panel')?.textContent.includes('Residencial Alameda')`);
  assert.ok(await evaluate(`document.querySelector('app-panel').textContent.includes('Constructora Alameda')`));
  await screenshot('desktop-dashboard');
  assert.equal(errors.length, 0, errors.join('\n'));
  assert.ok(requests.some((r) => r.pathname.endsWith('/ai/consulta')));
  console.log(
    JSON.stringify({
      status: 'OK',
      requests: requests.length,
      screenshots: output,
      runtimeErrors: errors.length,
    }),
  );
  await send('Browser.close');
  ws.close();
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
