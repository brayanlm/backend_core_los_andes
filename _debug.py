from app.database.session import SessionLocal
from app.models.mdl_all import CarteraDiaria, Asesor, SolicitudCredito, Cliente
from datetime import date

db = SessionLocal()
today = date.today().isoformat()
print("TODAY:", today)
print("=== CarteraDiaria ALL ===")
items = db.query(CarteraDiaria).all()
print(f"Total items: {len(items)}")
for i in items:
    print(f"  id={i.id} asesor_id={i.asesor_id} fecha={i.fecha_asignacion} gest={i.tipo_gestion}")

print(f"\n=== CarteraDiaria for {today} ===")
items_today = db.query(CarteraDiaria).filter(CarteraDiaria.fecha_asignacion == today).all()
print(f"Items: {len(items_today)}")
for i in items_today:
    print(f"  id={i.id} asesor_id={i.asesor_id} gest={i.tipo_gestion}")

print("\n=== SolicitudCredito ===")
sols = db.query(SolicitudCredito).all()
for s in sols:
    a = db.query(Asesor).filter(Asesor.id == s.asesor_id).first()
    if a:
        aname = f"{a.nombres} {a.apellidos} (cod={a.codigo_empleado})"
    else:
        aname = "NO_ASESOR"
    print(f"  id={s.id[:12]} asesor_id={s.asesor_id} asesor={aname} estado={s.estado}")

print("\n=== Asesores ===")
for a in db.query(Asesor).all():
    print(f"  id={a.id} cod={a.codigo_empleado} name={a.nombres} {a.apellidos}")

db.close()
