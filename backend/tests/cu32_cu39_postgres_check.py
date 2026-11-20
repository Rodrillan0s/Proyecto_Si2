"""Pruebas CU32/CU39 solo en el PostgreSQL desechable ya designado.

No crea clúster, no copia datos ni migra la base de Config. Reutiliza el
destino local y la marca de seguridad del ejecutor CU29.
"""
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cu29_postgres_check import STATE, connect_test


def main():
    settings = json.loads(STATE.read_text(encoding='utf-8'))
    connection = connect_test(settings)
    if '--describe' in sys.argv:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT table_name,column_name,data_type,is_nullable,column_default
                FROM information_schema.columns WHERE table_schema='obras'
                AND table_name IN ('t_estimacion','t_estimacion_analisis_precio_unitario',
                    't_analisis_precio_unitario','t_control_costo_obra','t_costo_ejecutado')
                ORDER BY table_name,ordinal_position""")
            for row in cursor.fetchall():
                print(row)
        connection.close()
        return 0
    connection.close()
    os.environ['CU29_TEST_SETTINGS'] = json.dumps(settings)
    import pytest
    return pytest.main(['-q', '-p', 'no:cacheprovider', 'tests/test_cu32_cu39_postgres.py', '--tb=short'])


if __name__ == '__main__':
    raise SystemExit(main())
