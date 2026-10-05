"""Barrera compartida. Una lease expirada exige intervención, no libera escritores."""
import threading
import time
from contextlib import contextmanager
from app.repos import backup_repos as repo
from .settings import Settings, BackupError


@contextmanager
def writer(kind):
    if not Settings.load().enabled:
        yield
        return
    identifier = repo.enter_writer(kind)
    stop = threading.Event()
    failed = []
    def renew():
        while not stop.wait(20):
            try:
                repo.renew_writer(identifier)
            except Exception as exc:
                failed.append(exc)
                break
    thread = threading.Thread(target=renew, daemon=True)
    thread.start()
    completed = False
    try:
        yield
        completed = True
    finally:
        stop.set()
        thread.join(timeout=6)
        if completed and not failed:
            repo.leave_writer(identifier)
        # En error del request también terminó el escritor; si control disponible limpiarlo.
        elif not failed:
            repo.leave_writer(identifier)


def drain(owner, reason, beat=lambda: None, timeout=180):
    repo.barrier(owner, True, reason)
    deadline = time.monotonic()+timeout
    while repo.active_writers():
        beat()
        if time.monotonic() >= deadline:
            raise BackupError('Hay escritores activos o interrumpidos. El sistema permanece en mantenimiento para revisión.', 'BACKUP_DRAIN_TIMEOUT')
        time.sleep(1)


class MaintenanceMiddleware:
    """ASGI para no mantener contexto/cursor durante el streaming de una respuesta."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        import asyncio
        from fastapi.responses import JSONResponse
        if scope['type'] != 'http' or scope.get('method') in {'OPTIONS', 'HEAD'} or not Settings.load().enabled:
            return await self.app(scope, receive, send)
        path = scope.get('path', '')
        # El plano de control sigue disponible. No tiene writes al negocio.
        if path.startswith('/api/backup/'):
            return await self.app(scope, receive, send)
        identifier = None
        renew_task = None
        try:
            # Durante promoción se bloquean también lecturas y login: no abrir pools.
            state = await asyncio.to_thread(repo.control)
            if state['mantenimiento']:
                raise BackupError('Sistema en mantenimiento: '+(state['motivo'] or 'restauración'), 'BACKUP_MAINTENANCE', 503)
            # Registrar todas las requests: varios GET heredados llaman funciones con escrituras.
            identifier = await asyncio.to_thread(repo.enter_writer, 'HTTP')
        except BackupError as exc:
            response = JSONResponse(status_code=exc.status, content={'detail': str(exc), 'code': exc.code})
            return await response(scope, receive, send)
        async def renew():
            while True:
                await asyncio.sleep(20)
                await asyncio.to_thread(repo.renew_writer, identifier)
        renew_task = asyncio.create_task(renew())
        try:
            await self.app(scope, receive, send)
        finally:
            renew_task.cancel()
            try:
                await renew_task
            except asyncio.CancelledError:
                pass
            await asyncio.to_thread(repo.leave_writer, identifier)
