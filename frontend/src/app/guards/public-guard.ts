import { CanActivateFn, Router } from '@angular/router';
import { inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { AuthService } from '../services/auth';

export const publicGuard: CanActivateFn = (route, state) => {
  const platformId = inject(PLATFORM_ID);

  if (!isPlatformBrowser(platformId)) {
    return true;
  }

  const authService = inject(AuthService);
  const router = inject(Router);

  const usuario = authService.obtenerUsuario();
  const tokenExpirado = authService.tokenExpirado();

  if (usuario && !tokenExpirado) {
    const destino = usuario.nombre_rol === 'CLIENTE' ? '/main_cliente' : '/panel';
    router.navigate([destino]);
    return false;
  }

  return true;
};