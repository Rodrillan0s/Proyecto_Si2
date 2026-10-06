"""Verifica las restricciones preparadas y el flujo con datos locales aislados."""
import re
import sqlite3
from pathlib import Path

import pytest


@pytest.fixture
def tabla():
    sql = (Path(__file__).parents[1] / 'database' / 'migration_cu19_validacion.sql').read_text(encoding='utf-8')
    estado = re.search(r'ADD CONSTRAINT chk_incidencia_estado CHECK \((.*?)\);', sql, re.S).group(1)
    fechas = re.search(r'ADD CONSTRAINT chk_incidencia_fechas_estado CHECK \((.*?)\);', sql, re.S).group(1)
    db = sqlite3.connect(':memory:')
    db.execute(f'CREATE TABLE incidencia (estado TEXT CHECK ({estado}), fecha_inicio_atencion TEXT, fecha_fin_atencion TEXT, id_responsable INTEGER CHECK(id_responsable=14), CHECK ({fechas}))')
    yield db
    db.close()


def test_restricciones_admiten_flujo_y_rechazo(tabla):
    tabla.execute("INSERT INTO incidencia VALUES ('ABIERTA',NULL,NULL,14)")
    for estado, inicio, fin in [
        ('ASIGNADA',None,None), ('EN_PROCESO','2026-10-02 10:00',None),
        ('PENDIENTE_VALIDACION','2026-10-02 10:00','2026-10-02 11:00'),
        ('EN_PROCESO','2026-10-02 10:00',None),
        ('PENDIENTE_VALIDACION','2026-10-02 10:00','2026-10-02 12:00'),
        ('RESUELTA','2026-10-02 10:00','2026-10-02 12:00'),
        ('CERRADA','2026-10-02 10:00','2026-10-02 12:00'),
    ]:
        tabla.execute('UPDATE incidencia SET estado=?,fecha_inicio_atencion=?,fecha_fin_atencion=?', (estado,inicio,fin))
        assert tabla.execute('SELECT id_responsable FROM incidencia').fetchone() == (14,)


@pytest.mark.parametrize('estado,inicio,fin', [
    ('PENDIENTE_VALIDACION',None,None), ('PENDIENTE_VALIDACION','inicio',None),
    ('EN_PROCESO','inicio','fin'), ('RESUELTA','inicio',None), ('DESCONOCIDO',None,None),
])
def test_restricciones_rechazan_fechas_incoherentes(tabla, estado, inicio, fin):
    with pytest.raises(sqlite3.IntegrityError):
        tabla.execute('INSERT INTO incidencia VALUES (?,?,?,14)', (estado,inicio,fin))
