import csv

fks = []
fks_no_empresa = []

with open('docs/diagramas/schema_dump.tsv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter='\t')
    for row in reader:
        if not row or len(row) < 4:
            continue
        table = row[1].strip('"')
        if table in ('tabla', '<USER_REQUEST>'):
            continue
        attr = row[3].strip('"') if len(row) > 3 else ''
        fk = (row[9].strip('"') if len(row) > 9 else '') == 'FK'
        ref_table = row[10].strip('"') if len(row) > 10 else ''
        if fk and ref_table and ref_table != table:
            fks.append((table, attr, ref_table))
            if ref_table != 't_empresa':
                fks_no_empresa.append((table, attr, ref_table))

print(f"Total FKs: {len(fks)}")
print(f"FKs to t_empresa (multi-tenant): {len(fks) - len(fks_no_empresa)}")
print(f"Domain / Business FKs: {len(fks_no_empresa)}")

