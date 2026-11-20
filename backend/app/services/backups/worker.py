"""Entrada legacy bloqueada. No reclama ni ejecuta trabajos del nuevo pipeline."""
from .settings import BackupError


def tick():
    raise BackupError('Motor legacy retirado; utilizar public.backup_jobs y el daemon Oracle.', 'BACKUP_LEGACY_RETIRED', 410)
