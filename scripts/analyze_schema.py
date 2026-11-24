import csv

tables = {}
fks = []

with open('schema_dump.tsv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter='\t')
    header = next(reader)
    print("Header:", header)
    for row in reader:
        if not row or len(row) < 4:
            continue
        schema = row[0].strip('"')
        table = row[1].strip('"')
        pos = row[2].strip('"') if len(row) > 2 else ''
        attr = row[3].strip('"') if len(row) > 3 else ''
        tipo = row[4].strip('"') if len(row) > 4 else ''
        pk = row[8].strip('"') if len(row) > 8 else ''
        fk = row[9].strip('"') if len(row) > 9 else ''
        ref_table = row[10].strip('"') if len(row) > 10 else ''
        ref_attr = row[11].strip('"') if len(row) > 11 else ''

        if table not in tables:
            tables[table] = []
        tables[table].append({
            'attr': attr,
            'tipo': tipo,
            'pk': pk == 'PK',
            'fk': fk == 'FK',
            'ref_table': ref_table,
            'ref_attr': ref_attr
        })
        if fk == 'FK' and ref_table:
            fks.append((table, attr, ref_table, ref_attr))

print(f"Total tables: {len(tables)}")
print(f"Total FKs: {len(fks)}")
for t in sorted(tables.keys()):
    print(f"- {t} ({len(tables[t])} cols)")

