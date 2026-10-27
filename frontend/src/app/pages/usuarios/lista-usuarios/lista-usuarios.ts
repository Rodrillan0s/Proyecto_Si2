import { Component, OnInit, inject, ChangeDetectorRef, NgZone, DestroyRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment';
import { AuthService } from '../../../services/auth';
import { EmpresaService } from '../../../services/empresa';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { firstValueFrom } from 'rxjs';

export interface Empresa {
  id_empresa: number;
  nombre_empresa: string;
  nit?: string | null;
  estado: string;
}

export interface Usuario {
  nro_usuario?: number;
  ci: string;
  nombre_usuario: string;
  estado: string;
  id_empresa?: number | null;
  nombre_empresa?: string; 
  nombre_completo: string;
  correo: string;
  telefono: string;
  direccion: string;
  nombre_rol?: string; 
  nro_rol: number;     
  password?: string;
}

export interface FilaGrupoUsuario {
  ci: string;
  nombre_completo: string;
  nombre_usuario: string;
  correo: string;
  telefono: string;
  direccion: string;
  nro_rol: number;
  password_temporal: string;
  estado_registro: 'PENDIENTE' | 'CREANDO' | 'EXITO' | 'ERROR';
  error_detalle?: string;
}

export interface RespuestaApiUsuarios {
  success: boolean;
  message: string;
  data: Usuario[];
}

export interface RespuestaApiEmpresas {
  success: boolean;
  message: string;
  data: Empresa[];
}

@Component({
  selector: 'app-lista-usuarios',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './lista-usuarios.html'
})
export class ListaUsuariosComponent implements OnInit {
  
  private http = inject(HttpClient);
  private cdr = inject(ChangeDetectorRef);
  private authService = inject(AuthService);
  private ngZone = inject(NgZone);
  private apiUrl = environment.apiUrl;
  private destroyRef = inject(DestroyRef);
  private empresaService = inject(EmpresaService);

  // --- VARIABLES DE DATOS ---
  usuarios: Usuario[] = [];
  usuariosFiltrados: Usuario[] = [];
  empresas: Empresa[] = []; 
  
  // --- VARIABLES PARA EL FILTRO Y BUSQUEDA ---
  filtroEmpresa: string = '';
  busquedaTexto: string = '';

  cargando: boolean = false;
  mensajeError: string = '';

  mostrarModal: boolean = false;
  modoEdicion: boolean = false;
  
  usuarioForm: Usuario = this.inicializarUsuario();

  totalUsuarios: number = 0;
  usuariosActivos: number = 0;
  usuariosInactivos: number = 0;
  empresaActiva: any = null;

  // --- ASISTENTE DE CREACION DE GRUPO DE USUARIOS ---
  mostrarModalGrupo: boolean = false;
  idEmpresaGrupo: number | null = null;
  filasGrupo: FilaGrupoUsuario[] = [];
  grupoProcesando: boolean = false;
  grupoCompletado: boolean = false;
  grupoIndiceActual: number = 0;
  grupoResumenExitosos: FilaGrupoUsuario[] = [];
  grupoResumenErrores: FilaGrupoUsuario[] = [];
  copiadoExitoso: boolean = false;
  errorValidacionGrupo: string = '';

  rolesDisponibles = [
    { id: 1, nombre: 'ADMINISTRADOR' },
    { id: 2, nombre: 'CLIENTE' },
    { id: 3, nombre: 'ADMINISTRADOR_EMPRESA' },
    { id: 4, nombre: 'JEFE DE OBRA' },
    { id: 5, nombre: 'ELECTRICO' },
    { id: 6, nombre: 'PLOMERO' },
    { id: 7, nombre: 'MAESTROALBAÑIL' },
    { id: 8, nombre: 'ALBAÑIL' }
  ];

  hasPermission(permiso: string): boolean {
    return this.authService.hasPermission(permiso);
  }

  esAdministradorSistema(): boolean {
    return this.authService.obtenerRolNormalizado() === 'ADMINISTRADOR';
  }

  rolesVisibles() {
    return this.esAdministradorSistema() ? this.rolesDisponibles : this.rolesDisponibles.filter(rol => ![1, 2].includes(rol.id));
  }

  rolesGrupo() {
    if (this.esAdministradorSistema()) {
      return this.rolesDisponibles.filter(r => [3, 4, 5, 6, 7, 8].includes(r.id));
    }
    // Para ADMINISTRADOR_EMPRESA solo roles operativos de obra
    return this.rolesDisponibles.filter(r => [4, 5, 6, 7, 8].includes(r.id));
  }

  async ngOnInit() {
    this.cargando = true;
    
    this.authService.empresaActiva$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(emp => {
        this.empresaActiva = emp;
        if (emp && emp.id_empresa) {
          this.filtroEmpresa = String(emp.id_empresa);
        } else {
          this.filtroEmpresa = '';
        }
        this.aplicarFiltro();
      });
    
    if (this.authService.obtenerToken()) {
      if (this.esAdministradorSistema()) this.cargarEmpresas();
      this.cargarUsuarios();
    } else {
      this.cargando = false;
      this.mensajeError = 'No se pudo iniciar sesión correctamente. Por favor, recarga la página.';
    }
  }

  // --- LÓGICA DE FILTRADO Y MÉTRICAS ---
  
  aplicarFiltro() {
    let list = [...this.usuarios];

    if (this.filtroEmpresa) {
      const idBuscado = Number(this.filtroEmpresa);
      list = list.filter(u => u.id_empresa === idBuscado);
    }

    if (this.busquedaTexto.trim()) {
      const q = this.busquedaTexto.trim().toLowerCase();
      list = list.filter(u =>
        (u.nombre_completo && u.nombre_completo.toLowerCase().includes(q)) ||
        (u.nombre_usuario && u.nombre_usuario.toLowerCase().includes(q)) ||
        (u.ci && u.ci.toLowerCase().includes(q)) ||
        (u.correo && u.correo.toLowerCase().includes(q)) ||
        (u.nombre_rol && u.nombre_rol.toLowerCase().includes(q)) ||
        (u.nombre_empresa && u.nombre_empresa.toLowerCase().includes(q))
      );
    }

    this.usuariosFiltrados = list;
    this.actualizarMetricas();
  }

  aplicarFiltros() {
    this.aplicarFiltro();
  }

  actualizarMetricas() {
    this.totalUsuarios = this.usuariosFiltrados.length;
    this.usuariosActivos = this.usuariosFiltrados.filter(u => u.estado === 'ACTIVO').length;
    this.usuariosInactivos = this.usuariosFiltrados.filter(u => u.estado === 'INACTIVO').length;
  }

  obtenerIniciales(nombre: string): string {
    if (!nombre) return 'XX';
    const partes = nombre.trim().split(' ');
    if (partes.length >= 2) {
      return (partes[0][0] + partes[1][0]).toUpperCase();
    }
    return nombre.substring(0, 2).toUpperCase();
  }

  getRolBadgeClass(rol?: string): string {
    const r = (rol || '').toUpperCase();
    if (r.includes('ADMINISTRADOR_EMPRESA')) {
      return 'bg-amber-100 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-300/60 dark:border-amber-700/60';
    }
    if (r.includes('ADMINISTRADOR')) {
      return 'bg-purple-100 dark:bg-purple-950/40 text-purple-800 dark:text-purple-300 border border-purple-300/60 dark:border-purple-700/60';
    }
    if (r.includes('JEFE')) {
      return 'bg-blue-100 dark:bg-blue-950/40 text-blue-800 dark:text-blue-300 border border-blue-300/60 dark:border-blue-700/60';
    }
    if (r.includes('ELECTRICO')) {
      return 'bg-yellow-100 dark:bg-yellow-950/40 text-yellow-800 dark:text-yellow-300 border border-yellow-300/60 dark:border-yellow-700/60';
    }
    if (r.includes('PLOMERO')) {
      return 'bg-cyan-100 dark:bg-cyan-950/40 text-cyan-800 dark:text-cyan-300 border border-cyan-300/60 dark:border-cyan-700/60';
    }
    if (r.includes('ALBA')) {
      return 'bg-emerald-100 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-300/60 dark:border-emerald-700/60';
    }
    return 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-300 border border-slate-300 dark:border-slate-700';
  }

  inicializarUsuario(): Usuario {
    const idEmpresaActiva = this.authService.obtenerIdEmpresaActiva();
    return {
      ci: '', nombre_usuario: '', nombre_completo: '', correo: '',
      telefono: '', direccion: '', estado: 'ACTIVO', nro_rol: 4, 
      id_empresa: idEmpresaActiva || null 
    };
  }

  // --- MÉTODOS DE RED ---

  cargarEmpresas() {
    this.empresaService.listarEmpresas()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          this.ngZone.run(() => {
            if (res && res.success) {
              this.empresas = (res.data || []).filter(e => e.estado === 'ACTIVO') as any;
            }
            this.cdr.detectChanges();
          });
        },
        error: (err) => console.error('Error cargando empresas:', err)
      });
  }

  cargarUsuarios() {
    this.cargando = true;
    this.mensajeError = '';
    
    this.http.get<RespuestaApiUsuarios>(`${this.apiUrl}/api/usuarios/`).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res.success) {
            this.usuarios = [...res.data]; 
            this.aplicarFiltros();
          } else {
            this.mensajeError = res.message || 'Error al obtener datos.';
          }
          this.cargando = false;
          this.cdr.detectChanges(); 
        });
      },
      error: () => {
        this.ngZone.run(() => {
          this.mensajeError = 'Error de conexión al cargar los usuarios.';
          this.cargando = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  guardarUsuario() {
    if (!this.usuarioForm.ci || !this.usuarioForm.nombre_completo || !this.usuarioForm.nombre_usuario) {
      alert('Por favor complete todos los campos obligatorios.');
      return;
    }

    this.cargando = true;

    if (this.modoEdicion) {
      this.http.put(`${this.apiUrl}/api/usuarios/${this.usuarioForm.nro_usuario}`, this.usuarioForm).subscribe({
        next: () => {
          this.ngZone.run(() => {
            this.cerrarModal();
            this.cargarUsuarios();
          });
        },
        error: (err) => {
          this.ngZone.run(() => {
            alert(err?.error?.detail || 'Error al actualizar el usuario.');
            this.cargando = false;
            this.cdr.detectChanges();
          });
        }
      });
    } else {
      if (!this.usuarioForm.password) {
        alert('La contraseña es obligatoria para usuarios nuevos.');
        this.cargando = false;
        return;
      }

      this.http.post(`${this.apiUrl}/api/usuarios/`, this.usuarioForm).subscribe({
        next: () => {
          this.ngZone.run(() => {
            this.cerrarModal();
            this.cargarUsuarios();
          });
        },
        error: (err) => {
          this.ngZone.run(() => {
            alert(err?.error?.detail || 'Error al crear el usuario. Verifique los datos.');
            this.cargando = false;
            this.cdr.detectChanges();
          });
        }
      });
    }
  }

  eliminarUsuario(id?: number) {
    if (!id) return;
    if (confirm('¿Está seguro que desea eliminar a este usuario?')) {
      this.http.delete(`${this.apiUrl}/api/usuarios/${id}`).subscribe({
        next: () => {
          this.ngZone.run(() => {
            this.cargarUsuarios();
          });
        },
        error: () => alert('Error al eliminar el usuario.')
      });
    }
  }

  // --- CONTROL DEL MODAL INDIVIDUAL ---

  abrirModalNuevo() {
    this.modoEdicion = false;
    this.usuarioForm = this.inicializarUsuario();
    this.mostrarModal = true;
  }

  abrirModalEditar(usuario: Usuario) {
    this.modoEdicion = true;
    this.usuarioForm = { ...usuario, password: '' }; 
    this.mostrarModal = true;
  }

  cerrarModal() {
    this.mostrarModal = false;
  }

  // =========================================================================
  // GESTION DE REGISTRO EN GRUPO (ALTA MASIVA PARA EMPRESA)
  // =========================================================================

  generarPasswordSegura(): string {
    const mayus = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
    const minus = 'abcdefghijkmnpqrstuvwxyz';
    const nums = '23456789';
    const syms = '!@#$%&*';
    const todos = mayus + minus + nums + syms;
    
    const chars = [
      mayus[Math.floor(Math.random() * mayus.length)],
      mayus[Math.floor(Math.random() * mayus.length)],
      minus[Math.floor(Math.random() * minus.length)],
      minus[Math.floor(Math.random() * minus.length)],
      nums[Math.floor(Math.random() * nums.length)],
      nums[Math.floor(Math.random() * nums.length)],
      syms[Math.floor(Math.random() * syms.length)],
      syms[Math.floor(Math.random() * syms.length)],
      todos[Math.floor(Math.random() * todos.length)],
      todos[Math.floor(Math.random() * todos.length)]
    ];
    return chars.sort(() => Math.random() - 0.5).join('');
  }

  crearFilaVacia(): FilaGrupoUsuario {
    return {
      ci: '',
      nombre_completo: '',
      nombre_usuario: '',
      correo: '',
      telefono: '',
      direccion: '',
      nro_rol: 4, // Jefe de Obra por defecto
      password_temporal: this.generarPasswordSegura(),
      estado_registro: 'PENDIENTE'
    };
  }

  abrirModalGrupo() {
    this.mostrarModalGrupo = true;
    this.grupoCompletado = false;
    this.grupoProcesando = false;
    this.grupoResumenExitosos = [];
    this.grupoResumenErrores = [];
    this.errorValidacionGrupo = '';
    this.copiadoExitoso = false;

    if (this.esAdministradorSistema()) {
      this.idEmpresaGrupo = this.empresaActiva?.id_empresa || (this.empresas.length > 0 ? this.empresas[0].id_empresa : null);
    } else {
      this.idEmpresaGrupo = this.authService.obtenerIdEmpresaActiva();
    }

    this.filasGrupo = [
      this.crearFilaVacia(),
      this.crearFilaVacia()
    ];
  }

  cerrarModalGrupo() {
    if (this.grupoProcesando) return;
    this.mostrarModalGrupo = false;
    this.filasGrupo = [];
    this.grupoCompletado = false;
  }

  agregarFilaGrupo() {
    this.filasGrupo.push(this.crearFilaVacia());
  }

  duplicarFilaGrupo(index: number) {
    const orig = this.filasGrupo[index];
    this.filasGrupo.splice(index + 1, 0, {
      ...orig,
      ci: '',
      nombre_usuario: '',
      correo: '',
      password_temporal: this.generarPasswordSegura(),
      estado_registro: 'PENDIENTE'
    });
  }

  eliminarFilaGrupo(index: number) {
    if (this.filasGrupo.length > 1) {
      this.filasGrupo.splice(index, 1);
    }
  }

  regenerarPasswordFila(fila: FilaGrupoUsuario) {
    fila.password_temporal = this.generarPasswordSegura();
  }

  sugerirUsername(fila: FilaGrupoUsuario) {
    if (fila.nombre_completo && !fila.nombre_usuario) {
      const clean = fila.nombre_completo
        .toLowerCase()
        .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9\s]/g, '')
        .trim()
        .split(/\s+/);
      if (clean.length >= 2) {
        fila.nombre_usuario = `${clean[0]}.${clean[1]}`;
      } else if (clean.length === 1 && clean[0]) {
        fila.nombre_usuario = clean[0];
      }
    }
  }

  validarGrupo(): boolean {
    this.errorValidacionGrupo = '';
    if (!this.idEmpresaGrupo) {
      this.errorValidacionGrupo = 'Debe seleccionar una empresa destino para el grupo.';
      return false;
    }
    if (this.filasGrupo.length === 0) {
      this.errorValidacionGrupo = 'Debe agregar al menos un usuario al grupo.';
      return false;
    }

    const cis = new Set<string>();
    const users = new Set<string>();
    const emails = new Set<string>();

    for (let i = 0; i < this.filasGrupo.length; i++) {
      const f = this.filasGrupo[i];
      const nro = i + 1;
      if (!f.ci.trim()) {
        this.errorValidacionGrupo = `Fila #${nro}: El Carnet (CI) es obligatorio.`;
        return false;
      }
      if (!f.nombre_completo.trim()) {
        this.errorValidacionGrupo = `Fila #${nro}: El Nombre Completo es obligatorio.`;
        return false;
      }
      if (!f.nombre_usuario.trim()) {
        this.errorValidacionGrupo = `Fila #${nro}: El Usuario (Login) es obligatorio.`;
        return false;
      }
      if (!f.nro_rol) {
        this.errorValidacionGrupo = `Fila #${nro}: Debe seleccionar un rol.`;
        return false;
      }

      const ciNorm = f.ci.trim().toUpperCase();
      if (cis.has(ciNorm)) {
        this.errorValidacionGrupo = `Fila #${nro}: CI "${f.ci}" duplicado en el grupo.`;
        return false;
      }
      cis.add(ciNorm);

      const userNorm = f.nombre_usuario.trim().toUpperCase();
      if (users.has(userNorm)) {
        this.errorValidacionGrupo = `Fila #${nro}: Usuario "${f.nombre_usuario}" duplicado en el grupo.`;
        return false;
      }
      users.add(userNorm);

      if (f.correo?.trim()) {
        const mailNorm = f.correo.trim().toLowerCase();
        if (emails.has(mailNorm)) {
          this.errorValidacionGrupo = `Fila #${nro}: Correo "${f.correo}" duplicado en el grupo.`;
          return false;
        }
        emails.add(mailNorm);
      }

      const existenteCI = this.usuarios.find(u => (u.ci || '').toUpperCase() === ciNorm);
      if (existenteCI) {
        this.errorValidacionGrupo = `Fila #${nro}: El CI "${f.ci}" ya existe en el sistema (${existenteCI.nombre_completo}).`;
        return false;
      }
      const existenteUser = this.usuarios.find(u => (u.nombre_usuario || '').toUpperCase() === userNorm);
      if (existenteUser) {
        this.errorValidacionGrupo = `Fila #${nro}: El usuario "${f.nombre_usuario}" ya existe en el sistema.`;
        return false;
      }
    }
    return true;
  }

  async procesarRegistroGrupo() {
    if (!this.validarGrupo()) return;

    this.grupoProcesando = true;
    this.grupoIndiceActual = 0;
    this.grupoResumenExitosos = [];
    this.grupoResumenErrores = [];

    for (let i = 0; i < this.filasGrupo.length; i++) {
      const f = this.filasGrupo[i];
      this.grupoIndiceActual = i + 1;
      f.estado_registro = 'CREANDO';
      this.cdr.detectChanges();

      const payload = {
        ci: f.ci.trim(),
        nombre_completo: f.nombre_completo.trim().toUpperCase(),
        nombre_usuario: f.nombre_usuario.trim().toUpperCase(),
        correo: f.correo?.trim() || null,
        telefono: f.telefono?.trim() || null,
        direccion: f.direccion?.trim() || null,
        nro_rol: Number(f.nro_rol),
        id_empresa: Number(this.idEmpresaGrupo),
        password: f.password_temporal,
        estado: 'ACTIVO'
      };

      try {
        await firstValueFrom(this.http.post<any>(`${this.apiUrl}/api/usuarios/`, payload));
        f.estado_registro = 'EXITO';
        this.grupoResumenExitosos.push(f);
      } catch (err: any) {
        f.estado_registro = 'ERROR';
        f.error_detalle = err?.error?.detail || 'Error al registrar usuario en la base de datos';
        this.grupoResumenErrores.push(f);
      }
      this.cdr.detectChanges();
    }

    this.grupoProcesando = false;
    this.grupoCompletado = true;
    this.cargarUsuarios();
    this.cdr.detectChanges();
  }

  obtenerNombreEmpresaGrupo(): string {
    const emp = this.empresas.find(e => e.id_empresa === this.idEmpresaGrupo);
    return emp ? emp.nombre_empresa : (this.empresaActiva?.nombre_empresa || 'Empresa seleccionada');
  }

  obtenerNombreRol(idRol: number): string {
    const rolObj = this.rolesDisponibles.find(r => r.id === Number(idRol));
    return rolObj ? rolObj.nombre : 'Operativo';
  }

  copiarCredencialesTexto() {
    const lineas: string[] = [];
    lineas.push(`CREDENCIALES TEMPORALES - EMPRESA: ${this.obtenerNombreEmpresaGrupo().toUpperCase()}`);
    lineas.push(`Fecha de alta: ${new Date().toLocaleDateString()}`);
    lineas.push('----------------------------------------------------------------------');
    this.grupoResumenExitosos.forEach(u => {
      const rolNombre = this.obtenerNombreRol(u.nro_rol);
      lineas.push(`• ${u.nombre_completo} (${rolNombre})`);
      lineas.push(`  Usuario: ${u.nombre_usuario} | CI: ${u.ci}`);
      lineas.push(`  Contraseña temporal: ${u.password_temporal}`);
      lineas.push('');
    });
    lineas.push('----------------------------------------------------------------------');
    lineas.push('Nota: Por seguridad, se recomienda cambiar la contraseña en el primer inicio de sesión.');

    const texto = lineas.join('\n');
    navigator.clipboard.writeText(texto).then(() => {
      this.copiadoExitoso = true;
      setTimeout(() => {
        this.copiadoExitoso = false;
        this.cdr.detectChanges();
      }, 3000);
      this.cdr.detectChanges();
    });
  }

  descargarCredenciales() {
    const lineas: string[] = [];
    lineas.push(`CREDENCIALES TEMPORALES - ${this.obtenerNombreEmpresaGrupo()}`);
    lineas.push('======================================================================');
    this.grupoResumenExitosos.forEach(u => {
      const rolNombre = this.obtenerNombreRol(u.nro_rol);
      lineas.push(`Nombre: ${u.nombre_completo}`);
      lineas.push(`Rol: ${rolNombre}`);
      lineas.push(`CI: ${u.ci}`);
      lineas.push(`Usuario: ${u.nombre_usuario}`);
      lineas.push(`Contraseña Temporal: ${u.password_temporal}`);
      lineas.push('----------------------------------------------------------------------');
    });

    const blob = new Blob([lineas.join('\n')], { type: 'text/plain;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `credenciales_grupo_${this.obtenerNombreEmpresaGrupo().replace(/\s+/g, '_')}_${Date.now()}.txt`;
    a.click();
    window.URL.revokeObjectURL(url);
  }
}
