import { Injectable, inject, PLATFORM_ID } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { isPlatformBrowser } from '@angular/common'; 
import { BehaviorSubject, Observable } from 'rxjs';
import { environment } from '../../environments/environment';


export type PermisoNombre =
  | 'Visualizar_usuarios'
  | 'Registrar_usuarios'
  | 'Modificar_usuarios'
  | 'Eliminar_usuarios'
  | 'Visualizar_obras'
  | 'Registrar_obras'
  | 'Modificar_obras'
  | 'Eliminar_obras'
  | 'Visualizar_empresa'
  | 'Registrar_empresa'
  | 'Modificar_empresa'
  | 'Eliminar_empresa'
  | 'Visualizar_inventario'
  | 'Registrar_inventario'
  | 'Modificar_inventario'
  | 'Eliminar_inventario'
  | 'Visualizar_materiales'
  | 'Registrar_materiales'
  | 'Modificar_materiales'
  | 'Desactivar_materiales'
  | 'Visualizar_proveedores'
  | 'Registrar_proveedores'
  | 'Modificar_proveedores';

export const PERMISOS_OFICIALES: PermisoNombre[] = [
  'Visualizar_usuarios', 'Registrar_usuarios', 'Modificar_usuarios', 'Eliminar_usuarios',
  'Visualizar_obras', 'Registrar_obras', 'Modificar_obras', 'Eliminar_obras',
  'Visualizar_empresa', 'Registrar_empresa', 'Modificar_empresa', 'Eliminar_empresa',
  'Visualizar_inventario', 'Registrar_inventario', 'Modificar_inventario', 'Eliminar_inventario',
  'Visualizar_materiales', 'Registrar_materiales', 'Modificar_materiales', 'Desactivar_materiales',
  'Visualizar_proveedores', 'Registrar_proveedores', 'Modificar_proveedores'
];

export const MAPA_PERMISOS_POR_ROL: Record<string, PermisoNombre[]> = {
  'ADMINISTRADOR': [...PERMISOS_OFICIALES],
  'ADMINISTRADOR_EMPRESA': [
    'Visualizar_usuarios', 'Registrar_usuarios', 'Modificar_usuarios', 'Eliminar_usuarios',
    'Visualizar_obras', 'Registrar_obras', 'Modificar_obras', 'Eliminar_obras',
    'Visualizar_empresa', 'Registrar_empresa', 'Modificar_empresa',
    'Visualizar_inventario', 'Registrar_inventario', 'Modificar_inventario', 'Eliminar_inventario',
    'Visualizar_materiales', 'Registrar_materiales', 'Modificar_materiales', 'Desactivar_materiales',
    'Visualizar_proveedores', 'Registrar_proveedores', 'Modificar_proveedores'
  ],
  'JEFE_DE_OBRA': [
    'Visualizar_obras', 'Registrar_obras', 'Modificar_obras',
    'Visualizar_inventario', 'Modificar_inventario',
    'Visualizar_materiales',
    'Visualizar_proveedores'
  ],
  'SUPERVISOR_OBRA': [
    'Visualizar_obras', 'Modificar_obras',
    'Visualizar_inventario',
    'Visualizar_materiales'
  ],
  'CLIENTE': [
    'Visualizar_obras'
  ],
  'ELECTRICO': [
    'Visualizar_obras',
    'Visualizar_inventario',
    'Visualizar_materiales'
  ],
  'PLOMERO': [
    'Visualizar_obras',
    'Visualizar_inventario',
    'Visualizar_materiales'
  ],
  'MAESTRO_ALBANIL': [
    'Visualizar_obras',
    'Visualizar_inventario',
    'Visualizar_materiales'
  ],
  'ALBANIL': [
    'Visualizar_obras',
    'Visualizar_inventario',
    'Visualizar_materiales'
  ]
};

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;
  private platformId = inject(PLATFORM_ID); 

  iniciarSesion(credenciales: any) {
    return this.http.post<any>(`${this.apiUrl}/api/auth/login`, credenciales);
  }

  registrarUsuario(datos: any) {
    return this.http.post<any>(`${this.apiUrl}/api/auth/register`, datos);
  }

  guardarSesion(token: string, usuario: any) {
    if (isPlatformBrowser(this.platformId)) {
      localStorage.setItem('token', token);
      localStorage.setItem('usuario', JSON.stringify(usuario));
    }
  }

  obtenerToken(): string | null {
    if (isPlatformBrowser(this.platformId)) {
      return localStorage.getItem('token');
    }
    return null;
  }

  obtenerUsuario() {
    if (!isPlatformBrowser(this.platformId)) {
      return null;
    }

    const usuarioString = localStorage.getItem('usuario');
    return usuarioString ? JSON.parse(usuarioString) : null;
  }

  private empresaSeleccionadaSubject = new BehaviorSubject<any>(null);
  public empresaSeleccionada$: Observable<any> = this.empresaSeleccionadaSubject.asObservable();
  public empresaActiva$: Observable<any> = this.empresaSeleccionadaSubject.asObservable();

  cerrarSesion() {
    if (isPlatformBrowser(this.platformId)) {
      localStorage.clear();
    }
    this.empresaSeleccionadaSubject.next(null);
  }

  seleccionarEmpresa(empresa: any) {
    if (isPlatformBrowser(this.platformId)) {
      if (empresa) {
        localStorage.setItem('empresa_seleccionada', JSON.stringify(empresa));
      } else {
        localStorage.removeItem('empresa_seleccionada');
      }
    }
    this.empresaSeleccionadaSubject.next(empresa);
  }

  seleccionarEmpresaActiva(empresa: any) {
    this.seleccionarEmpresa(empresa);
  }

  obtenerEmpresaSeleccionada(): any {
    if (this.empresaSeleccionadaSubject.value) {
      return this.empresaSeleccionadaSubject.value;
    }
    if (isPlatformBrowser(this.platformId)) {
      const raw = localStorage.getItem('empresa_seleccionada');
      if (raw) {
        try {
          const parsed = JSON.parse(raw);
          this.empresaSeleccionadaSubject.next(parsed);
          return parsed;
        } catch {
          return null;
        }
      }
    }
    return null;
  }

  obtenerEmpresaActiva(): any {
    return this.obtenerEmpresaSeleccionada();
  }

  obtenerIdEmpresaActiva(): number | null {
    const rol = this.obtenerRolNormalizado();
    if (rol === 'ADMINISTRADOR') {
      const e = this.obtenerEmpresaActiva();
      return e?.id_empresa ? Number(e.id_empresa) : null;
    }
    const u = this.obtenerUsuario();
    return u?.id_empresa ? Number(u.id_empresa) : null;
  }

  esVistaGlobal(): boolean {
    const rol = this.obtenerRolNormalizado();
    return rol === 'ADMINISTRADOR' && this.obtenerIdEmpresaActiva() === null;
  }

  obtenerNombreEmpresaActiva(): string {
    const rol = this.obtenerRolNormalizado();
    if (rol === 'ADMINISTRADOR') {
      const e = this.obtenerEmpresaActiva();
      return e ? e.nombre_empresa : 'Vista Global (Todas)';
    }
    const u = this.obtenerUsuario();
    return u?.nombre_empresa || 'Mi Empresa';
  }

  limpiarEmpresaSeleccionada() {
    this.seleccionarEmpresa(null);
  }

  tokenExpirado(): boolean {
    const token = this.obtenerToken();
    if (!token) return true;

    try {
      const payloadBase64 = token.split('.')[1];
      const payloadDecodificado = JSON.parse(atob(payloadBase64));
      const tiempoExpiracion = payloadDecodificado.exp * 1000;
      const tiempoActual = Date.now();
      return tiempoActual >= tiempoExpiracion;
    } catch (error) {
      return true; 
    }
  }

  /**
   * Normaliza nombres de roles (maneja espacios, guiones bajos y acentos)
   */
  obtenerRolNormalizado(): string {
    const usuario = this.obtenerUsuario();
    if (!usuario || !usuario.nombre_rol) return '';

    let rol = String(usuario.nombre_rol).trim().toUpperCase();
    rol = rol.replace(/\s+/g, '_');
    rol = rol.normalize('NFD').replace(/[\u0300-\u036f]/g, ''); // remueve acentos (ej. ALBAÑIL -> ALBANIL)
    rol = rol.replace('MAESTROALBANIL', 'MAESTRO_ALBANIL');
    rol = rol.replace('SUPERVISOR', 'SUPERVISOR_OBRA');
    if (rol === 'SUPERVISOR_OBRA_OBRA') rol = 'SUPERVISOR_OBRA';
    return rol;
  }

  /**
   * Retorna la lista de permisos efectivos del usuario actual
   */
  obtenerPermisosUsuario(): PermisoNombre[] {
    const usuario = this.obtenerUsuario();
    if (!usuario) return [];

    // Si el usuario en sesión ya tiene el arreglo explícito de permisos
    if (Array.isArray(usuario.permisos) && usuario.permisos.length > 0) {
      return usuario.permisos as PermisoNombre[];
    }

    const rol = this.obtenerRolNormalizado();
    if (rol === 'ADMINISTRADOR') {
      return [...PERMISOS_OFICIALES];
    }

    return MAPA_PERMISOS_POR_ROL[rol] || [];
  }

  /**
   * Verifica si el usuario actual posee un permiso específico
   */
  hasPermission(permiso: PermisoNombre | string): boolean {
    const usuario = this.obtenerUsuario();
    if (!usuario) return false;

    const rol = this.obtenerRolNormalizado();
    if (rol === 'ADMINISTRADOR') return true;

    const permisos = this.obtenerPermisosUsuario();
    return permisos.includes(permiso as PermisoNombre);
  }

  /**
   * Verifica si el usuario actual posee al menos uno de los permisos dados
   */
  hasAnyPermission(permisos: (PermisoNombre | string)[]): boolean {
    if (!permisos || permisos.length === 0) return true;
    return permisos.some(p => this.hasPermission(p));
  }

  /**
   * Verifica si el usuario actual posee todos los permisos dados
   */
  hasAllPermissions(permisos: (PermisoNombre | string)[]): boolean {
    if (!permisos || permisos.length === 0) return true;
    return permisos.every(p => this.hasPermission(p));
  }
}
