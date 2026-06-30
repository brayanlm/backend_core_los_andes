import sqlite3
conn = sqlite3.connect(r'D:\DAM\app_banco_los_andes\backend_core_los_andes\data\bd_core_mobile.db')
conn.row_factory = sqlite3.Row

# Check existing tables
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print('=== TABLAS EN bd_core_mobile ===')
for t in tables:
    name = t['name']
    cnt = conn.execute(f'SELECT COUNT(*) as c FROM [{name}]').fetchone()['c']
    print(f'  {name}: {cnt} rows')

# Show schemas for client-facing tables
for tbl in ['cr_cliente', 'cr_cuenta_ahorro', 'cr_movimiento', 'cr_tarjeta', 'cr_credito', 'cr_solicitud_credito', 'cr_notificacion', 'dcliente', 'dsolicitud']:
    cols = conn.execute(f'PRAGMA table_info({tbl})').fetchall()
    print(f'\n=== {tbl} columns ===')
    for c in cols:
        nn = 'NOT NULL' if c['notnull'] else ''
        pk = 'PK' if c['pk'] else ''
        print(f'  {c["name"]} ({c["type"]}) {nn} {pk}')

# Show some sample data from key tables
print('\n=== cr_cliente sample (first 2) ===')
for r in conn.execute('SELECT id, numero_documento, nombres, apellidos, telefono FROM cr_cliente LIMIT 2').fetchall():
    print(dict(r))

print('\n=== cr_cuenta_ahorro sample ===')
for r in conn.execute('SELECT * FROM cr_cuenta_ahorro LIMIT 5').fetchall():
    print(dict(r))

print('\n=== cr_movimiento sample ===')
for r in conn.execute('SELECT * FROM cr_movimiento LIMIT 5').fetchall():
    print(dict(r))

print('\n=== cr_tarjeta sample ===')
for r in conn.execute('SELECT * FROM cr_tarjeta LIMIT 5').fetchall():
    print(dict(r))

conn.close()
