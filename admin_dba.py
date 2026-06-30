"""DBA Tool — bd_core_mobile.db
Uso: python admin_dba.py [comando]

Comandos:
  tables                    Lista tablas con registros
  schema [tabla]            Muestra schema de tabla(s)
  query "SQL"               Ejecuta SQL directo
  clientes                  Lista clientes
  creditos [--semaforo]     Lista creditos con semaforo
  outbox                    Muestra cola sync pendiente
  log                       Ultimos 20 sync log
  promote <solicitud_id>    Promueve solicitud a nucleo
  push                      Procesa outbox pendiente
  pull                      Trae Firestore a SQLite
  import <tabla> <json>     Importa registros desde JSON
  export <tabla>            Exporta tabla a JSON
  --help                    Este mensaje
"""
import argparse, json, sqlite3, os, sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "bd_core_mobile.db"


def get_conn():
    if not DB_PATH.exists():
        print(f"ERROR: DB no encontrada en {DB_PATH}")
        sys.exit(1)
    return sqlite3.connect(str(DB_PATH))


def cmd_tables():
    conn = get_conn()
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    print(f"{'Tabla':40s} {'Registros':>10s}")
    print("-" * 52)
    for (name,) in rows:
        cnt = conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
        print(f"{name:40s} {cnt:>10d}")
    conn.close()


def cmd_schema(args):
    conn = get_conn()
    tables = [args.tabla] if args.tabla else [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    for t in tables:
        print(f"\n=== {t} ===")
        for cid, name, ctype, notnull, default, pk in conn.execute(f'PRAGMA table_info("{t}")'):
            print(f"  {name:30s} {ctype:15s} {'PK' if pk else ''} {'NOT NULL' if notnull else ''} {'default '+str(default) if default else ''}")
        for fk in conn.execute(f'PRAGMA foreign_key_list("{t}")'):
            print(f"  FK: {fk[3]} -> {fk[2]}({fk[4]})")
    conn.close()


def cmd_clientes():
    conn = get_conn()
    rows = conn.execute("""SELECT c.numero_documento, c.nombres, c.apellidos,
        c.telefono, c.calificacion_sbs
        FROM cr_cliente c ORDER BY c.apellidos""").fetchall()
    print(f"{'Documento':12s} {'Nombres':30s} {'Telefono':12s} {'SBS':6s}")
    print("-" * 62)
    for doc, nom, ape, tel, sbs in rows:
        doc = doc or "-"
        nom = nom or ""
        ape = ape or ""
        tel = tel or "-"
        sbs = sbs or "-"
        print(f"{doc:12s} {(nom+' '+ape)[:30]:30s} {tel:12s} {sbs:6s}")
    conn.close()


def cmd_creditos(args):
    conn = get_conn()
    rows = conn.execute("""SELECT cr.id, cr.monto, cr.plazo_meses, cr.tasa, cr.estado,
        cr.dias_mora, cr.destino, cl.nombres, cl.apellidos
        FROM cr_credito cr LEFT JOIN cr_cliente cl ON cl.id = cr.cliente_id
        ORDER BY cr.dias_mora DESC""").fetchall()
    print(f"{'ID':38s} {'Monto':>8s} {'Plazo':>6s} {'Tasa':>6s} {'Estado':12s} {'Mora':>5s} {'Semaforo':10s} {'Cliente':22s}")
    print("-" * 109)
    for id_, monto, plazo, tasa, estado, mora, destino, nom, ape in rows:
        mora = mora or 0
        if mora <= 5:
            sem = "VERDE"
        elif mora <= 30:
            sem = "AMARILLO"
        else:
            sem = "ROJO"
        if args.semaforo and args.semaforo.upper() != sem:
            continue
        id_short = id_[:36] + ".." if len(id_) > 36 else id_
        nom = (nom or "") + " " + (ape or "")
        print(f"{id_short:38s} {monto:>8.0f} {plazo:>6d} {tasa:>6.2f} {(estado or '-'):12s} {mora:>5d} {sem:10s} {nom[:22]:22s}")
    conn.close()


def cmd_outbox():
    conn = get_conn()
    pendientes = conn.execute(
        "SELECT id, entidad, operacion, intentos, error_msg, created_at FROM cr_sync_outbox WHERE estado='pendiente' ORDER BY created_at"
    ).fetchall()
    if pendientes:
        print(f"{'ID':38s} {'Entidad':20s} {'Op':10s} {'Intentos':>8s} {'Error':30s}")
        print("-" * 108)
        for id_, ent, op, intentos, err, _ in pendientes:
            id_short = id_[:36] + ".." if len(id_) > 36 else id_
            err = (err or "")[:28]
            print(f"{id_short:38s} {ent[:20]:20s} {op[:10]:10s} {str(intentos):>8s} {err:30s}")
        print(f"\nTotal pendientes: {len(pendientes)}")
    else:
        print("No hay registros pendientes en outbox")
    conn.close()


def cmd_log():
    conn = get_conn()
    rows = conn.execute(
        "SELECT tipo, registros, resultado, detalle, created_at FROM cr_sync_log ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    print(f"{'Tipo':12s} {'Regs':>5s} {'Resultado':12s} {'Detalle':40s} {'Fecha':20s}")
    print("-" * 91)
    for tipo, regs, res, det, fecha in rows:
        det = (det or "")[:38]
        fecha = (fecha or "")[:19]
        print(f"{tipo[:10]:12s} {str(regs or ''):>5s} {(res or '')[:12]:12s} {det:40s} {fecha:20s}")
    conn.close()


def cmd_query(args):
    sql = args.tabla or args.sql  # "query" almacena el SQL en tabla por orden posicional
    if not sql:
        print("ERROR: Proporciona una consulta SQL. Ej: query \"SELECT * FROM cr_credito\"")
        return
    conn = get_conn()
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description] if cursor.description else []
        if cols:
            print(" | ".join(f"{c:20s}" for c in cols))
            print("-" * (len(cols) * 22))
            for r in rows:
                vals = [str(r[c]) if isinstance(r, dict) else str(i) for c, i in zip(cols, r)]
                print(" | ".join(f"{v[:20]:20s}" for v in vals))
        print(f"\n{len(rows)} filas")
    except Exception as e:
        print(f"ERROR: {e}")
    conn.close()


def _get_session():
    sys.path.insert(0, str(Path(__file__).parent))
    from app.database.session import SessionLocal
    return SessionLocal()


def cmd_promote(args):
    if not args.solicitud_id:
        print("ERROR: Usa: admin_dba.py promote <solicitud_id>")
        return
    from app.sync.sync_service import promover_solicitud
    db = _get_session()
    try:
        result = promover_solicitud(db, args.solicitud_id)
        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()


def cmd_push():
    from app.sync.sync_service import push_outbox, pull_all
    db = _get_session()
    try:
        print("Pull:", json.dumps(pull_all(db), default=str))
        print("Push:", json.dumps(push_outbox(db), default=str))
    finally:
        db.close()


def cmd_pull():
    from app.sync.sync_service import pull_all
    db = _get_session()
    try:
        result = pull_all(db)
        print(json.dumps(result, default=str))
    finally:
        db.close()


def cmd_import(args):
    conn = get_conn()
    try:
        data = json.loads(args.json_data)
        if isinstance(data, dict):
            data = [data]
        cols = list(data[0].keys())
        placeholders = ",".join("?" * len(cols))
        col_names = ",".join(cols)
        for row in data:
            values = [row.get(c) for c in cols]
            conn.execute(f'INSERT OR REPLACE INTO "{args.tabla}" ({col_names}) VALUES ({placeholders})', values)
        conn.commit()
        print(f"{len(data)} registros importados en {args.tabla}")
    except Exception as e:
        print(f"ERROR: {e}")
    conn.close()


def cmd_export(args):
    conn = get_conn()
    rows = conn.execute(f'SELECT * FROM "{args.tabla}"').fetchall()
    cols = [desc[0] for desc in conn.description]
    data = [dict(zip(cols, r)) for r in rows]
    print(json.dumps(data, indent=2, default=str))
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="DBA Tool - bd_core_mobile.db", add_help=False)
    parser.add_argument("comando", nargs="?", default="tables",
                        help="tables|schema|query|clientes|creditos|outbox|log|promote|push|pull|import|export")
    parser.add_argument("--semaforo", "-s", help="Filtrar creditos por semaforo: VERDE|AMARILLO|ROJO")
    parser.add_argument("tabla", nargs="?", default=None, help="Nombre de tabla")
    parser.add_argument("json_data", nargs="?", default=None, help="JSON data (para import)")
    parser.add_argument("sql", nargs="?", default=None, help="SQL query")
    parser.add_argument("solicitud_id", nargs="?", default=None, help="ID de solicitud para promover")
    parser.add_argument("--help", action="store_true", help="Mostrar ayuda")
    args, _ = parser.parse_known_args()

    if args.help or args.comando in ("-h", "--help"):
        print(__doc__)
        return

    cmds = {
        "tables": lambda: cmd_tables(),
        "schema": lambda: cmd_schema(args),
        "query": lambda: cmd_query(args),
        "clientes": lambda: cmd_clientes(),
        "creditos": lambda: cmd_creditos(args),
        "outbox": lambda: cmd_outbox(),
        "log": lambda: cmd_log(),
        "promote": lambda: cmd_promote(args),
        "push": lambda: cmd_push(),
        "pull": lambda: cmd_pull(),
        "import": lambda: cmd_import(args),
        "export": lambda: cmd_export(args),
    }

    fn = cmds.get(args.comando)
    if fn:
        fn()
    else:
        print(f"Comando desconocido: {args.comando}")
        print("Usa --help para ver comandos disponibles")


if __name__ == "__main__":
    main()
