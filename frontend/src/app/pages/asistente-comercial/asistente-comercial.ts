import {
  ChangeDetectorRef,
  Component,
  DestroyRef,
  ElementRef,
  HostListener,
  Input,
  OnDestroy,
  OnInit,
  ViewChild,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  AsistenteComercialService,
  EmpresaComercial,
  EstiloAcabadoInfo,
  MensajeComercialPersistido,
  SesionChatComercial,
  UnidadComercial,
} from '../../services/asistente-comercial.service';
import { AuthService } from '../../services/auth';
import { ContextoOperativo } from '../../services/contexto-operativo';
import { AsistenteService } from '../../services/asistente.service';

export type MensajeComercialChat = MensajeComercialPersistido;

interface SpeechRecognitionInstance {
  lang: string;
  interimResults: boolean;
  onresult: ((event: { results: { transcript: string }[][] }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}

@Component({
  selector: 'app-asistente-comercial',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './asistente-comercial.html',
})
export class AsistenteComercialComponent implements OnInit, OnDestroy {
  private comercialService = inject(AsistenteComercialService);
  private authService = inject(AuthService);
  private contexto = inject(ContextoOperativo);
  readonly ui = inject(AsistenteService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);
  private destroyRef = inject(DestroyRef);

  @Input() embedded = false;
  @Input() autoOpen = false;
  @Input() moduleMode = false;

  @ViewChild('chatScroll') chatScroll?: ElementRef<HTMLElement>;
  @ViewChild('chatInput') chatInput?: ElementRef<HTMLTextAreaElement>;
  @ViewChild('planoFileInput') planoFileInput?: ElementRef<HTMLInputElement>;

  abierto = false;
  modoRutaDedicada = false;

  empresas: EmpresaComercial[] = [];
  empresaActiva: EmpresaComercial | null = null;
  empresaRefSeleccionada: string | number = '';
  empresaFijaPorSesion = false;

  cargandoCatalogo = false;
  procesando = false;
  recalculandoEstilo = false;
  enviandoContacto = false;
  escuchandoVoz = false;
  mensajeError: string | null = null;

  resumenInventario = { total_unidades: 0, unidades_disponibles: 0, total_modelos: 0 };
  unidadesCatalogo: UnidadComercial[] = [];
  estilosAcabado: EstiloAcabadoInfo[] = [];
  preguntasSugeridas: string[] = [];

  private recognition?: SpeechRecognitionInstance;
  private ultimaEmpresaContexto: number | null = null;

  private get sesion(): SesionChatComercial {
    return this.comercialService.obtenerSesion(this.empresaRefSeleccionada || 'default');
  }

  get conversacionId(): string | null {
    return this.sesion.conversacionId;
  }
  set conversacionId(val: string | null) {
    this.sesion.conversacionId = val;
  }

  get mensajes(): MensajeComercialChat[] {
    return this.sesion.mensajes;
  }
  set mensajes(val: MensajeComercialChat[]) {
    this.sesion.mensajes = val;
  }

  get mensajeInput(): string {
    return this.sesion.mensajeInput;
  }
  set mensajeInput(val: string) {
    this.sesion.mensajeInput = val;
  }

  get archivoPlano(): File | null {
    return this.sesion.archivoPlano;
  }
  set archivoPlano(val: File | null) {
    this.sesion.archivoPlano = val;
  }

  get previewPlanoUrl(): string | null {
    return this.sesion.previewPlanoUrl;
  }
  set previewPlanoUrl(val: string | null) {
    this.sesion.previewPlanoUrl = val;
  }

  get estiloPlanoSeleccionado(): string {
    return this.sesion.estiloPlanoSeleccionado;
  }
  set estiloPlanoSeleccionado(val: string) {
    this.sesion.estiloPlanoSeleccionado = val;
  }

  get unidadesSeleccionadasComparar(): number[] {
    return this.sesion.unidadesSeleccionadasComparar;
  }
  set unidadesSeleccionadasComparar(val: number[]) {
    this.sesion.unidadesSeleccionadasComparar = val;
  }

  get unidadesInteresContacto(): number[] {
    return this.sesion.unidadesInteresContacto;
  }
  set unidadesInteresContacto(val: number[]) {
    this.sesion.unidadesInteresContacto = val;
  }

  get formContacto() {
    return this.sesion.formContacto;
  }

  ngOnInit(): void {
    const url = this.router.url || '';
    if (!this.embedded && url.startsWith('/asistente-comercial')) {
      this.ui.openComercial(undefined, 'chat');
      this.router.navigate(['/panel']);
      return;
    }

    this.modoRutaDedicada = url.startsWith('/comercial');
    if (this.modoRutaDedicada || this.autoOpen || this.moduleMode) {
      this.abierto = true;
    }

    const usuario = this.authService.obtenerUsuario();
    const idActiva = this.authService.obtenerIdEmpresaActiva();
    this.ultimaEmpresaContexto = idActiva ? Number(idActiva) : null;

    if (usuario && usuario.nombre_rol !== 'ADMINISTRADOR' && usuario.id_empresa) {
      this.empresaFijaPorSesion = true;
      this.empresaRefSeleccionada = Number(usuario.id_empresa);
    } else if (this.comercialService.empresaRefActiva) {
      this.empresaRefSeleccionada = this.comercialService.empresaRefActiva;
    } else if (idActiva) {
      this.empresaRefSeleccionada = Number(idActiva);
    }

    const paramEmpresa = this.route.snapshot?.paramMap?.get('empresa');
    if (paramEmpresa && !this.empresaFijaPorSesion) {
      this.empresaRefSeleccionada = paramEmpresa;
    }

    if (this.empresaRefSeleccionada) {
      this.comercialService.empresaRefActiva = this.empresaRefSeleccionada;
    }

    this.authService.usuario$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((user) => {
      this.quitarPlanoAdjunto();
      this.mensajeError = null;
      if (user && user.nombre_rol !== 'ADMINISTRADOR' && user.id_empresa) {
        this.empresaFijaPorSesion = true;
        this.empresaRefSeleccionada = Number(user.id_empresa);
        this.comercialService.empresaRefActiva = this.empresaRefSeleccionada;
      } else {
        this.empresaFijaPorSesion = false;
        const idActiva = this.authService.obtenerIdEmpresaActiva();
        if (idActiva) {
          this.empresaRefSeleccionada = Number(idActiva);
          this.comercialService.empresaRefActiva = this.empresaRefSeleccionada;
        }
      }
      this.cargarEmpresasDisponibles();
      this.cdr.markForCheck();
    });

    this.contexto.operativo$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      const idEmpresaContexto = this.authService.obtenerIdEmpresaActiva();
      const idNum = idEmpresaContexto ? Number(idEmpresaContexto) : null;
      if (idNum && idNum !== this.ultimaEmpresaContexto) {
        this.ultimaEmpresaContexto = idNum;
        this.cambiarEmpresa(idNum);
      }
    });

    this.cargarEmpresasDisponibles();
    if (this.mensajes.length > 0) {
      this.scrollBottom();
    }
  }

  ngOnDestroy(): void {
    this.detenerVoz();
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.abierto && !this.embedded) {
      this.cerrarBurbuja();
    }
  }

  abrirBurbuja(textoInicial?: string): void {
    this.abierto = true;
    if (textoInicial) {
      this.mensajeInput = textoInicial;
    }
    this.cdr.markForCheck();
    this.scrollBottom();
    setTimeout(() => this.chatInput?.nativeElement?.focus(), 60);
  }

  cerrarBurbuja(): void {
    this.detenerVoz();
    if (this.embedded) {
      this.ui.close();
      return;
    }
    this.abierto = false;
    this.cdr.markForCheck();
  }

  toggleBurbuja(): void {
    if (this.abierto) {
      this.cerrarBurbuja();
    } else {
      this.abrirBurbuja();
    }
  }

  limpiarConversacionActual(): void {
    if (!this.empresaRefSeleccionada || this.procesando) return;
    this.comercialService.reiniciarSesion(this.empresaRefSeleccionada);
    this.mensajeError = null;
    this.cdr.markForCheck();
  }

  cargarEmpresasDisponibles(): void {
    if (this.comercialService.empresasCache.length > 0) {
      this.empresas = this.comercialService.empresasCache;
      if (!this.empresaRefSeleccionada && this.empresas.length > 0) {
        const conUnidades = this.empresas.find((e) => e.total_unidades > 0) || this.empresas[0];
        this.empresaRefSeleccionada = conUnidades.id_empresa;
        this.comercialService.empresaRefActiva = this.empresaRefSeleccionada;
      }
      if (this.empresaRefSeleccionada) {
        this.cargarCatalogoEmpresa(this.empresaRefSeleccionada);
      }
      return;
    }

    this.cargandoCatalogo = true;
    this.comercialService.listarEmpresas().subscribe({
      next: (res) => {
        this.empresas = res?.data || [];
        this.comercialService.empresasCache = this.empresas;
        if (!this.empresaRefSeleccionada && this.empresas.length > 0) {
          const conUnidades = this.empresas.find((e) => e.total_unidades > 0) || this.empresas[0];
          this.empresaRefSeleccionada = conUnidades.id_empresa;
          this.comercialService.empresaRefActiva = this.empresaRefSeleccionada;
        }
        if (this.empresaRefSeleccionada) {
          this.cargarCatalogoEmpresa(this.empresaRefSeleccionada);
        } else {
          this.cargandoCatalogo = false;
          this.cdr.markForCheck();
        }
      },
      error: () => {
        this.cargandoCatalogo = false;
        this.mensajeError = 'No se pudo conectar con el catálogo de constructoras.';
        this.cdr.markForCheck();
      },
    });
  }

  cambiarEmpresa(nuevaRef: string | number): void {
    if (!nuevaRef) return;
    this.empresaRefSeleccionada = nuevaRef;
    this.comercialService.empresaRefActiva = nuevaRef;
    this.mensajeError = null;
    this.cargarCatalogoEmpresa(nuevaRef);
    this.scrollBottom();
  }

  private aplicarDatosCatalogo(d: any): void {
    this.empresaActiva = d.empresa;
    this.resumenInventario = d.resumen_inventario || {
      total_unidades: 0,
      unidades_disponibles: 0,
      total_modelos: 0,
    };
    this.unidadesCatalogo = d.unidades_destacadas || [];
    this.estilosAcabado = d.estilos_acabado || [];
    this.preguntasSugeridas = d.preguntas_sugeridas || [
      '¿Qué departamentos o viviendas tienen disponibles actualmente?',
      'Tengo un presupuesto de 85.000 USD, ¿qué opciones me recomiendan?',
      'Compárame las mejores unidades disponibles en relación precio y superficie',
      '¿Cuánto cuesta construir 110 m² en estilo Minimalista vs Lujo?',
      'Quiero que un asesor comercial me contacte para agendar una visita',
    ];
  }

  cargarCatalogoEmpresa(empresaRef: string | number): void {
    this.mensajeError = null;
    const sesionEmpresa = this.comercialService.obtenerSesion(empresaRef);
    if (sesionEmpresa.catalogo) {
      this.cargandoCatalogo = false;
      this.aplicarDatosCatalogo(sesionEmpresa.catalogo);
      this.cdr.markForCheck();
      return;
    }

    this.cargandoCatalogo = true;
    this.comercialService.obtenerCatalogo(empresaRef).subscribe({
      next: (res: any) => {
        this.cargandoCatalogo = false;
        const d = res?.data || res || {};
        sesionEmpresa.catalogo = d;
        this.aplicarDatosCatalogo(d);
        this.cdr.markForCheck();
      },
      error: (err: any) => {
        this.cargandoCatalogo = false;
        this.mensajeError = err?.error?.detail || 'No se pudo cargar el portafolio inmobiliario.';
        this.cdr.markForCheck();
      },
    });
  }

  onEnterKey(event: Event): void {
    const kb = event as KeyboardEvent;
    if (!kb.shiftKey && !kb.isComposing) {
      kb.preventDefault();
      this.enviarAccionPrincipal();
    }
  }

  enviarAccionPrincipal(textoForzado?: string): void {
    if (this.procesando || !this.empresaRefSeleccionada) return;
    if (this.archivoPlano && !textoForzado) {
      this.enviarPlanoEnChat();
      return;
    }
    this.enviarMensajeTexto(textoForzado);
  }

  enviarMensajeTexto(textoForzado?: string): void {
    const texto = (textoForzado ?? this.mensajeInput).trim();
    if (!texto || this.procesando || !this.empresaRefSeleccionada) return;

    const empresaRef = this.empresaRefSeleccionada;
    const sesionTarget = this.comercialService.obtenerSesion(empresaRef);

    this.mensajeError = null;
    this.procesando = true;
    if (!textoForzado) {
      sesionTarget.mensajeInput = '';
    }

    sesionTarget.mensajes.push({
      id: 'u-' + Date.now(),
      rol: 'user',
      texto,
      fecha: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    });
    this.scrollBottom();

    const payload: any = {
      mensaje: texto,
      conversacion_id: sesionTarget.conversacionId,
      moneda: 'USD',
      ids_unidades_comparar:
        sesionTarget.unidadesSeleccionadasComparar.length >= 2
          ? sesionTarget.unidadesSeleccionadasComparar
          : undefined,
    };

    this.comercialService.enviarConsultaChat(empresaRef, payload).subscribe({
      next: (res) => {
        this.procesando = false;
        sesionTarget.conversacionId = res.conversacion_id || sesionTarget.conversacionId;
        const recomendadas: UnidadComercial[] = res.unidades_recomendadas || [];

        const sugerenciasSeguimiento = this.generarSugerenciasSeguimiento(
          res.intencion,
          recomendadas,
          !!res.comparativa,
          !!res.estimacion_costo,
          !!res.registro_crm,
        );

        sesionTarget.mensajes.push({
          id: 'a-' + Date.now(),
          rol: 'assistant',
          texto: res.respuesta || res.resumen_estructurado,
          intencion: res.intencion,
          unidades: recomendadas.slice(0, 4),
          comparativa: res.comparativa || null,
          estimacionCosto: res.estimacion_costo || null,
          registroCrm: res.registro_crm || null,
          requiereContacto: !!res.requiere_datos_contacto,
          mostrarFormularioContacto: !!res.requiere_datos_contacto,
          sugerencias: sugerenciasSeguimiento,
          fecha: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        });
        this.scrollBottom();
      },
      error: (err) => {
        this.procesando = false;
        this.mensajeError = err?.error?.detail || 'Ocurrió un error al consultar el asistente comercial.';
        this.cdr.markForCheck();
      },
    });
  }

  abrirSelectorPlano(): void {
    this.planoFileInput?.nativeElement?.click();
  }

  onPlanoSeleccionado(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];
    if (file.size > 10 * 1024 * 1024) {
      this.mensajeError = 'El plano supera el límite máximo de 10 MB.';
      return;
    }
    this.archivoPlano = file;
    this.mensajeError = null;
    const reader = new FileReader();
    reader.onload = () => {
      this.previewPlanoUrl = reader.result as string;
      this.cdr.markForCheck();
    };
    reader.readAsDataURL(file);
    input.value = '';
  }

  quitarPlanoAdjunto(): void {
    this.archivoPlano = null;
    this.previewPlanoUrl = null;
    this.cdr.markForCheck();
  }

  enviarPlanoEnChat(): void {
    if (!this.archivoPlano || !this.empresaRefSeleccionada || this.procesando) return;
    const empresaRef = this.empresaRefSeleccionada;
    const sesionTarget = this.comercialService.obtenerSesion(empresaRef);
    const archivo = this.archivoPlano;
    const preview = this.previewPlanoUrl;
    const estilo = this.estiloPlanoSeleccionado || 'MINIMALISTA';
    const notaUsuario =
      this.mensajeInput.trim() ||
      `Analizar este plano arquitectónico y estimar su costo constructivo en estilo ${estilo}.`;

    this.procesando = true;
    this.mensajeError = null;
    sesionTarget.mensajeInput = '';
    sesionTarget.archivoPlano = null;
    sesionTarget.previewPlanoUrl = null;

    sesionTarget.mensajes.push({
      id: 'u-plano-' + Date.now(),
      rol: 'user',
      texto: notaUsuario,
      planoPreviewUrl: preview,
      planoNombre: archivo.name,
      estiloPlano: estilo,
      fecha: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    });
    this.scrollBottom();

    this.comercialService
      .analizarPlano(empresaRef, archivo, {
        mensaje: notaUsuario,
        moneda: 'USD',
        estilo_preferido: estilo,
        conversacion_id: sesionTarget.conversacionId,
      })
      .subscribe({
        next: (res: any) => {
          this.procesando = false;
          sesionTarget.conversacionId = res.conversacion_id || sesionTarget.conversacionId;
          sesionTarget.mensajes.push({
            id: 'a-plano-' + Date.now(),
            rol: 'assistant',
            texto: res.respuesta,
            intencion: 'analizar_plano',
            lecturaPlano: res.lectura_plano || null,
            estimacionCosto: res.estimacion_costo || null,
            unidades: (res.unidades_similares_disponibles || []).slice(0, 3),
            sugerencias: [
              'Compárame las unidades similares a mi plano',
              'Quiero agendar una revisión técnica de mi plano con un asesor',
            ],
            fecha: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          });
          this.scrollBottom();
        },
        error: (err: any) => {
          this.procesando = false;
          this.mensajeError =
            err?.error?.detail || 'No se pudo procesar la imagen del plano. Usa formato PNG, JPG o WEBP.';
          this.cdr.markForCheck();
        },
      });
  }

  cambiarEstiloEnMensaje(msg: MensajeComercialChat, nuevoEstilo: string): void {
    if (!msg.estimacionCosto || this.recalculandoEstilo || !this.empresaRefSeleccionada) return;
    const params = msg.estimacionCosto.parametros_entrada || {};
    this.recalculandoEstilo = true;
    this.comercialService
      .estimarCosto(this.empresaRefSeleccionada, {
        superficie_m2: Number(params.superficie_m2 || 95),
        tipo_inmueble: params.tipo_inmueble || 'DEPARTAMENTO',
        estilo_acabado: nuevoEstilo,
        cantidad_plantas: Number(params.cantidad_plantas || 1),
        dormitorios: Number(params.dormitorios || 2),
        banos: Number(params.banos || 2),
        moneda: 'USD',
        incluir_parqueo: true,
        incluir_baulera: false,
        incluir_domotica: nuevoEstilo === 'LUJO',
      })
      .subscribe({
        next: (res: any) => {
          this.recalculandoEstilo = false;
          if (res?.estimacion) {
            msg.estimacionCosto = res.estimacion;
          }
          this.cdr.markForCheck();
        },
        error: () => {
          this.recalculandoEstilo = false;
          this.cdr.markForCheck();
        },
      });
  }

  toggleCompararUnidad(idUnidad: number): void {
    const lista = this.unidadesSeleccionadasComparar;
    const idx = lista.indexOf(idUnidad);
    if (idx >= 0) {
      lista.splice(idx, 1);
    } else {
      if (lista.length >= 4) {
        lista.shift();
      }
      lista.push(idUnidad);
    }
    this.cdr.markForCheck();
  }

  estaSeleccionadaComparar(idUnidad: number): boolean {
    return this.unidadesSeleccionadasComparar.includes(idUnidad);
  }

  compararUnidadesSeleccionadasEnChat(): void {
    if (this.unidadesSeleccionadasComparar.length < 2) return;
    const codigos = this.unidadesCatalogo
      .filter((u) => this.unidadesSeleccionadasComparar.includes(u.id_unidad))
      .map((u) => u.codigo_unidad);
    const label = codigos.length >= 2 ? codigos.join(', ') : 'las unidades seleccionadas';
    this.enviarMensajeTexto(`Compárame lado a lado ${label} en precio, superficie y disponibilidad.`);
  }

  abrirTarjetaContactoEnChat(idUnidad?: number, codigoUnidad?: string): void {
    if (idUnidad && !this.unidadesInteresContacto.includes(idUnidad)) {
      this.unidadesInteresContacto.push(idUnidad);
    }
    if (codigoUnidad && !this.formContacto.notas.includes(codigoUnidad)) {
      this.formContacto.notas = this.formContacto.notas
        ? `${this.formContacto.notas} | Interés en ${codigoUnidad}`
        : `Interesado en unidad ${codigoUnidad}`;
    }

    const ultimoMsg = this.mensajes[this.mensajes.length - 1];
    if (ultimoMsg && ultimoMsg.rol === 'assistant' && !ultimoMsg.registroCrm) {
      ultimoMsg.mostrarFormularioContacto = true;
      this.scrollBottom();
      return;
    }

    this.mensajes.push({
      id: 'a-contacto-' + Date.now(),
      rol: 'assistant',
      texto:
        'Completa tus datos de contacto aquí mismo para registrar tu solicitud en el CRM comercial y asignarte un asesor:',
      intencion: 'solicitar_contacto',
      mostrarFormularioContacto: true,
      fecha: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    });
    this.scrollBottom();
  }

  enviarContactoDesdeTarjeta(msg: MensajeComercialChat): void {
    if (!this.empresaRefSeleccionada || this.enviandoContacto) return;
    if (!this.formContacto.nombre_completo.trim()) {
      this.mensajeError = 'Ingresa tu nombre completo para registrar el contacto.';
      return;
    }
    if (!this.formContacto.telefono.trim() && !this.formContacto.email.trim()) {
      this.mensajeError = 'Ingresa un teléfono/WhatsApp o correo electrónico.';
      return;
    }

    this.mensajeError = null;
    this.enviandoContacto = true;

    this.comercialService
      .solicitarContacto(this.empresaRefSeleccionada, {
        ...this.formContacto,
        unidades_interes: this.unidadesInteresContacto,
      })
      .subscribe({
        next: (res) => {
          this.enviandoContacto = false;
          msg.mostrarFormularioContacto = false;
          msg.requiereContacto = false;
          msg.registroCrm = res.registro_crm;
          this.scrollBottom();
        },
        error: (err) => {
          this.enviandoContacto = false;
          this.mensajeError = err?.error?.detail || 'No se pudo registrar la solicitud de contacto.';
          this.cdr.markForCheck();
        },
      });
  }

  toggleDictadoVoz(): void {
    if (this.procesando) return;
    if (this.escuchandoVoz) {
      this.detenerVoz();
      return;
    }

    const win = window as unknown as {
      SpeechRecognition?: new () => SpeechRecognitionInstance;
      webkitSpeechRecognition?: new () => SpeechRecognitionInstance;
    };
    const SpeechConstructor = win.SpeechRecognition ?? win.webkitSpeechRecognition;
    if (!SpeechConstructor) {
      this.mensajeError = 'El dictado por voz no está disponible en este navegador. Escribe tu consulta.';
      this.cdr.markForCheck();
      return;
    }

    try {
      const rec = new SpeechConstructor();
      this.recognition = rec;
      rec.lang = 'es-BO';
      rec.interimResults = false;
      rec.onresult = (event) => {
        const transcript = event.results?.[0]?.[0]?.transcript || '';
        if (transcript) {
          this.mensajeInput = transcript.slice(0, 1500);
          this.cdr.markForCheck();
        }
      };
      rec.onerror = () => {
        this.escuchandoVoz = false;
        this.cdr.markForCheck();
      };
      rec.onend = () => {
        this.escuchandoVoz = false;
        this.cdr.markForCheck();
      };
      rec.start();
      this.escuchandoVoz = true;
      this.cdr.markForCheck();
    } catch {
      this.escuchandoVoz = false;
      this.cdr.markForCheck();
    }
  }

  private detenerVoz(): void {
    try {
      this.recognition?.stop();
    } catch {
      // Ignore stop errors
    }
    this.recognition = undefined;
    this.escuchandoVoz = false;
  }

  etiquetaIntencion(intencion?: string): string {
    switch (intencion) {
      case 'buscar_unidades':
        return 'Catálogo Inmobiliario';
      case 'recomendar_presupuesto':
        return 'Recomendación a Medida';
      case 'comparar_unidades':
        return 'Comparativa Lado a Lado';
      case 'analizar_plano':
        return 'Lectura de Planos & Costos';
      case 'estimar_costo':
        return 'Estimación Paramétrica por Estilo';
      case 'solicitar_contacto':
        return 'Contacto Comercial CRM';
      default:
        return 'Asistente Comercial';
    }
  }

  private generarSugerenciasSeguimiento(
    intencion?: string,
    unidades: UnidadComercial[] = [],
    tieneComparativa = false,
    tieneEstimacion = false,
    tieneCrm = false,
  ): string[] {
    const chips: string[] = [];
    if (unidades.length >= 2 && !tieneComparativa) {
      chips.push('Compárame las opciones recomendadas lado a lado');
    }
    if (!tieneEstimacion) {
      chips.push('¿Cuánto cuesta construir 110 m² en estilo Minimalista vs Lujo?');
    }
    if (!tieneCrm) {
      chips.push('Quiero que un asesor comercial me contacte');
    }
    return chips.slice(0, 3);
  }

  private scrollBottom(): void {
    this.cdr.markForCheck();
    setTimeout(() => {
      const el = this.chatScroll?.nativeElement;
      if (el) {
        el.scrollTop = el.scrollHeight;
      }
    }, 60);
  }
}
