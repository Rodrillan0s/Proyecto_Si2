export function reportError(error: unknown): string {
  const response = error as { status?: number; error?: { detail?: unknown } };
  if (response.status === 0)
    return 'No hay conexión con el servidor. Revisa tu conexión y vuelve a intentar.';
  if (response.status === 401) return 'Tu sesión ha caducado. Inicia sesión nuevamente.';
  if (response.status === 403)
    return 'No tienes permiso para esta consulta. Verifica la empresa y tus accesos.';
  if (response.status === 404)
    return 'El recurso no está disponible. Actualiza la página o solicita revisar el servicio de reportes.';
  if (response.status && response.status >= 500)
    return 'El servicio no está disponible en este momento. Puedes volver a intentar más tarde.';
  return typeof response.error?.detail === 'string'
    ? response.error.detail
    : 'No se pudo completar la operación. Revisa los filtros y vuelve a intentar.';
}

export function saveReportFile(file: { bytes: Blob; name: string }) {
  const url = URL.createObjectURL(file.bytes);
  const link = document.createElement('a');
  link.href = url;
  link.download = file.name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
