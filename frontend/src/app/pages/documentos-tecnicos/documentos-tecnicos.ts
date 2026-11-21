import { CommonModule } from '@angular/common';
import {
  ChangeDetectorRef,
  Component,
  DestroyRef,
  OnInit,
  inject
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize } from 'rxjs';
import { jsPDF } from 'jspdf';

import { AuthService } from '../../services/auth';
import {
  DocumentosTecnicosService,
  DocumentoTecnico,
  VersionDocumento
} from '../../services/documentos-tecnicos';

interface DocumentoForm {
  nombre: string;
  tipo_documento: string;
  descripcion: string;
  contenido_documento: string;
  observaciones: string;
}

@Component({
  selector: 'app-documentos-tecnicos',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './documentos-tecnicos.html'
})
export class DocumentosTecnicosComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private service = inject(DocumentosTecnicosService);
  private auth = inject(AuthService);
  private cdr = inject(ChangeDetectorRef);
  private destroyRef = inject(DestroyRef);

  idObra = 0;

  documentos: DocumentoTecnico[] = [];
  historialVersiones: VersionDocumento[] = [];

  documentoSeleccionado?: DocumentoTecnico;

  cargando = false;
  cargandoHistorial = false;
  guardando = false;

  mensajeError = '';
  mensajeExito = '';

  modal: 'nuevo' | 'version' | 'historial' | null = null;

  archivoSeleccionado?: File;

  form: DocumentoForm = this.formularioVacio();

  tiposDocumento = [
    'PLANO_ARQUITECTONICO',
    'PLANO_ESTRUCTURAL',
    'PLANO_ELECTRICO',
    'PLANO_SANITARIO',
    'PLANO_HIDRAULICO',
    'MEMORIA_DESCRIPTIVA',
    'ESPECIFICACION_TECNICA',
    'OTRO'
  ];

  get documentosActivos(): number {
    return this.documentos.filter(
      documento => documento.estado === 'ACTIVO'
    ).length;
  }

  get totalVersiones(): number {
    return this.documentos.reduce(
      (total, documento) => total + (documento.version_actual || 1),
      0
    );
  }

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));

    if (!id || Number.isNaN(id)) {
      this.mostrarError('No se pudo identificar la obra.');
      return;
    }

    this.idObra = id;
    this.cargarDocumentos();
  }

  formularioVacio(): DocumentoForm {
    return {
      nombre: '',
      tipo_documento: 'PLANO_ARQUITECTONICO',
      descripcion: '',
      contenido_documento: '',
      observaciones: ''
    };
  }

  tienePermiso(permiso: string): boolean {
    return true;
  }

  cargarDocumentos(): void {
    this.cargando = true;
    this.mensajeError = '';

    this.service.listarPorObra(this.idObra)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => {
          this.cargando = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: (res: any) => {
          this.documentos = res?.data || [];
        },
        error: (error) => {
          this.mostrarError(
            error?.error?.detail || 'No se pudieron cargar los documentos.'
          );
        }
      });
  }

  abrirNuevo(): void {
    this.form = this.formularioVacio();
    this.archivoSeleccionado = undefined;
    this.documentoSeleccionado = undefined;
    this.mensajeError = '';
    this.mensajeExito = '';
    this.modal = 'nuevo';
  }

  abrirNuevaVersion(documento: DocumentoTecnico): void {
    this.documentoSeleccionado = documento;
    this.form = this.formularioVacio();
    this.form.nombre = documento.nombre;
    this.form.tipo_documento = documento.tipo_documento;
    this.form.descripcion = documento.descripcion || '';
    this.archivoSeleccionado = undefined;
    this.mensajeError = '';
    this.mensajeExito = '';
    this.modal = 'version';
  }

  seleccionarArchivo(event: Event): void {
    const input = event.target as HTMLInputElement;
    const archivo = input.files?.[0];

    if (!archivo) {
      this.archivoSeleccionado = undefined;
      return;
    }

    if (
      archivo.type !== 'application/pdf' &&
      !archivo.name.toLowerCase().endsWith('.pdf')
    ) {
      this.mostrarError('Solo se permiten archivos PDF.');
      input.value = '';
      this.archivoSeleccionado = undefined;
      return;
    }

    if (archivo.size > 15 * 1024 * 1024) {
      this.mostrarError('El archivo no puede superar los 15 MB.');
      input.value = '';
      this.archivoSeleccionado = undefined;
      return;
    }

    this.archivoSeleccionado = archivo;
    this.mensajeError = '';
  }

  private generarPDF(): File {
    const pdf = new jsPDF();

    const margen = 15;
    const anchoPagina = pdf.internal.pageSize.getWidth();
    const altoPagina = pdf.internal.pageSize.getHeight();
    const anchoTexto = anchoPagina - margen * 2;

    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(16);
    pdf.text(this.form.nombre, margen, 20, {
      maxWidth: anchoTexto
    });

    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(10);

    pdf.text(
      `Tipo de documento: ${this.form.tipo_documento.replaceAll('_', ' ')}`,
      margen,
      32,
      { maxWidth: anchoTexto }
    );

    if (this.form.descripcion) {
      pdf.text('Descripción:', margen, 43);
      const descripcion = pdf.splitTextToSize(
        this.form.descripcion,
        anchoTexto
      );
      pdf.text(descripcion, margen, 49);
    }

    let posicionY = 65;

    pdf.setFont('helvetica', 'bold');
    pdf.text('Contenido del documento:', margen, posicionY);

    pdf.setFont('helvetica', 'normal');
    posicionY += 8;

    const contenido = pdf.splitTextToSize(
      this.form.contenido_documento || 'Sin contenido registrado.',
      anchoTexto
    );

    contenido.forEach((linea: string) => {
      if (posicionY > altoPagina - 20) {
        pdf.addPage();
        posicionY = 20;
      }

      pdf.text(linea, margen, posicionY);
      posicionY += 6;
    });

    if (this.form.observaciones) {
      if (posicionY > altoPagina - 35) {
        pdf.addPage();
        posicionY = 20;
      }

      posicionY += 8;

      pdf.setFont('helvetica', 'bold');
      pdf.text('Observaciones:', margen, posicionY);

      pdf.setFont('helvetica', 'normal');
      posicionY += 7;

      const observaciones = pdf.splitTextToSize(
        this.form.observaciones,
        anchoTexto
      );

      observaciones.forEach((linea: string) => {
        if (posicionY > altoPagina - 20) {
          pdf.addPage();
          posicionY = 20;
        }

        pdf.text(linea, margen, posicionY);
        posicionY += 6;
      });
    }

    const blob = pdf.output('blob');

    return new File(
      [blob],
      `${this.form.nombre.replace(/[^a-zA-Z0-9-_]/g, '_')}.pdf`,
      { type: 'application/pdf' }
    );
  }

  guardarDocumento(): void {
    if (!this.form.nombre.trim()) {
      this.mostrarError('El nombre del documento es obligatorio.');
      return;
    }

    if (!this.form.tipo_documento) {
      this.mostrarError('Selecciona el tipo de documento.');
      return;
    }

    if (!this.form.contenido_documento.trim()) {
      this.mostrarError('El contenido del documento es obligatorio.');
      return;
    }

    const archivo = this.archivoSeleccionado || this.generarPDF();

    const datos = new FormData();
    datos.append('id_obra', String(this.idObra));
    datos.append('nombre', this.form.nombre.trim());
    datos.append('tipo_documento', this.form.tipo_documento);
    datos.append('descripcion', this.form.descripcion.trim());
    datos.append(
      'contenido_documento',
      this.form.contenido_documento.trim()
    );
    datos.append('observaciones', this.form.observaciones.trim());
    datos.append('archivo', archivo);

    this.guardando = true;
    this.mensajeError = '';

    this.service.registrar(datos)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => {
          this.guardando = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: () => {
          this.cerrarModal();
          this.mostrarExito('Documento técnico registrado correctamente.');
          this.cargarDocumentos();
        },
        error: (error) => {
          this.mostrarError(
            error?.error?.detail || 'No se pudo registrar el documento.'
          );
        }
      });
  }

  guardarVersion(): void {
    if (!this.documentoSeleccionado) {
      this.mostrarError('No se seleccionó ningún documento.');
      return;
    }

    if (!this.form.contenido_documento.trim()) {
      this.mostrarError('El contenido del documento es obligatorio.');
      return;
    }

    const archivo = this.archivoSeleccionado || this.generarPDF();

    const datos = new FormData();
    datos.append('nombre', this.form.nombre.trim());
    datos.append('tipo_documento', this.form.tipo_documento);
    datos.append('descripcion', this.form.descripcion.trim());
    datos.append(
      'contenido_documento',
      this.form.contenido_documento.trim()
    );
    datos.append('observaciones', this.form.observaciones.trim());
    datos.append('archivo', archivo);

    this.guardando = true;
    this.mensajeError = '';

    this.service.crearVersion(this.documentoSeleccionado.id_documento, datos)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => {
          this.guardando = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: () => {
          this.cerrarModal();
          this.mostrarExito('Nueva versión registrada correctamente.');
          this.cargarDocumentos();
        },
        error: (error) => {
          this.mostrarError(
            error?.error?.detail || 'No se pudo registrar la nueva versión.'
          );
        }
      });
  }

  abrirHistorial(documento: DocumentoTecnico): void {
  this.documentoSeleccionado = documento;
  this.historialVersiones = [];
  this.cargandoHistorial = true;
  this.mensajeError = '';
  this.modal = 'historial';

  this.service.historial(documento.id_documento)
    .pipe(
      takeUntilDestroyed(this.destroyRef),
      finalize(() => {
        this.cargandoHistorial = false;
        this.cdr.detectChanges();
      })
    )
    .subscribe({
      next: (res) => {
        this.historialVersiones = res.data?.versiones || [];
      },
      error: (error) => {
        this.mostrarError(
          error?.error?.detail || 'No se pudo cargar el historial.'
        );
      }
    });
}

 descargarDocumento(documento: DocumentoTecnico): void {
  this.service.historial(documento.id_documento)
    .pipe(takeUntilDestroyed(this.destroyRef))
    .subscribe({
      next: (res) => {
        const versiones = res.data?.versiones || [];

        const versionActual = versiones.find(
          version => version.numero_version === documento.version_actual
        );

        if (!versionActual) {
          this.mostrarError(
            'No se encontró la versión vigente del documento.'
          );
          return;
        }

        this.descargarArchivo(documento.id_documento, versionActual);
      },
      error: (error) => {
        this.mostrarError(
          error?.error?.detail || 'No se pudo obtener la versión del documento.'
        );
      }
    });
}

  descargar(version: VersionDocumento): void {
    if (!this.documentoSeleccionado) {
      this.mostrarError('No se seleccionó ningún documento.');
      return;
    }

    this.descargarArchivo(
      this.documentoSeleccionado.id_documento,
      version
    );
  }

  private descargarArchivo(
    idDocumento: number,
    version: VersionDocumento
  ): void {
    this.service.descargar(
      idDocumento,
      version.id_version
    )
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (archivo: Blob) => {
          const url = window.URL.createObjectURL(archivo);
          const enlace = document.createElement('a');

          enlace.href = url;
          enlace.download =
            version.nombre_archivo || `documento-version-${version.numero_version}.pdf`;

          document.body.appendChild(enlace);
          enlace.click();
          document.body.removeChild(enlace);

          window.URL.revokeObjectURL(url);
        },
        error: (error) => {
          this.mostrarError(
            error?.error?.detail || 'No se pudo descargar el archivo.'
          );
        }
      });
  }

  cambiarEstado(documento: DocumentoTecnico): void {
    const nuevoEstado =
      documento.estado === 'ACTIVO' ? 'INACTIVO' : 'ACTIVO';

    this.service.cambiarEstado(
      documento.id_documento,
      nuevoEstado
    )
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.mostrarExito(
            nuevoEstado === 'ACTIVO'
              ? 'Documento activado correctamente.'
              : 'Documento desactivado correctamente.'
          );

          this.cargarDocumentos();
        },
        error: (error) => {
          this.mostrarError(
            error?.error?.detail || 'No se pudo cambiar el estado del documento.'
          );
        }
      });
  }

  cerrarModal(): void {
    this.modal = null;
    this.documentoSeleccionado = undefined;
    this.historialVersiones = [];
    this.archivoSeleccionado = undefined;
    this.form = this.formularioVacio();
    this.mensajeError = '';
  }

  volver(): void {
    this.router.navigate(['/obras', this.idObra]);
  }

  tamanoArchivo(bytes: number): string {
    if (!bytes) {
      return '0 KB';
    }

    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }

    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }

  private mostrarError(mensaje: string): void {
    this.mensajeError = mensaje;
    this.mensajeExito = '';
    this.cdr.detectChanges();
  }

  private mostrarExito(mensaje: string): void {
    this.mensajeExito = mensaje;
    this.mensajeError = '';
    this.cdr.detectChanges();
  }
}