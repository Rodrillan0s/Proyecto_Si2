import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService, PermisoNombre } from '../services/auth';

export const roleGuard: CanActivateFn = (route) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const usuario = authService.obtenerUsuario();

  if (!usuario || authService.tokenExpirado()) {
    authService.cerrarSesion();
    return router.createUrlTree(['/login']);
  }

  // 1. Verificación por permisos específicos (Prioridad Máxima)
  const permisosRequeridos = route.data['permissions'] as PermisoNombre[] | undefined;
  if (permisosRequeridos && permisosRequeridos.length > 0) {
    const tienePermiso = authService.hasAnyPermission(permisosRequeridos);
    if (!tienePermiso) {
      // Si no tiene permiso, lo enviamos al dashboard permitido
      return router.createUrlTree(['/panel']);
    }
  }

  // 2. Verificación por roles (Compatibilidad hacia atrás)
  const rolesPermitidos = route.data['roles'] as string[] | undefined;
  if (rolesPermitidos && rolesPermitidos.length > 0) {
    const rolNormalizado = authService.obtenerRolNormalizado();
    const rolOriginal = usuario.nombre_rol;
    const tieneRol = rolesPermitidos.some(r => {
      const rNorm = r.replace(/\s+/g, '_').normalize('NFD').replace(/[\u0300-\u036f]/g, '');
      return r === rolOriginal || rNorm === rolNormalizado;
    });
    if (!tieneRol) {
      return router.createUrlTree(['/panel']);
    }
  }

  return true;
};
