import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth';

export const roleGuard: CanActivateFn = (route) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const usuario = authService.obtenerUsuario();
  const rolesPermitidos = route.data['roles'] as string[] | undefined;

  if (usuario && (!rolesPermitidos || rolesPermitidos.includes(usuario.nombre_rol))) {
    return true;
  }

  return router.createUrlTree([usuario?.nombre_rol === 'CLIENTE' ? '/main_cliente' : '/panel']);
};
