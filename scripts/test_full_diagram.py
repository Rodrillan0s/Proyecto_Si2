import csv
import random
import math
from collections import defaultdict

# 1. Load schema
tables = {}
fks = []
edges = []

with open('docs/diagramas/schema_dump.tsv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter='\t')
    for row in reader:
        if not row or len(row) < 4:
            continue
        table = row[1].strip('"')
        if table in ('tabla', '<USER_REQUEST>'):
            continue
        attr = row[3].strip('"') if len(row) > 3 else ''
        tipo = row[4].strip('"') if len(row) > 4 else ''
        pk = (row[8].strip('"') if len(row) > 8 else '') == 'PK'
        fk = (row[9].strip('"') if len(row) > 9 else '') == 'FK'
        ref_table = row[10].strip('"') if len(row) > 10 else ''
        ref_attr = row[11].strip('"') if len(row) > 11 else ''

        if table not in tables:
            tables[table] = []
        tables[table].append({
            'attr': attr,
            'tipo': tipo,
            'pk': pk,
            'fk': fk,
            'ref_table': ref_table,
            'ref_attr': ref_attr
        })
        if fk and ref_table and ref_table != table:
            fks.append((table, attr, ref_table, ref_attr))
            edges.append((table, ref_table))

print(f"Total tables: {len(tables)}, Total FK edges: {len(edges)}")

