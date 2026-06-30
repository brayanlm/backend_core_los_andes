from app.database.session import SessionLocal
from app.models.mdl_all import CarteraDiaria, Asesor, SolicitudCredito
from datetime import date

db = SessionLocal()
today = date.today().isoformat()
print("=== Cartera para hoy " + today + " ===")
items = db.query(CarteraDiaria).filter(CarteraDiaria.fecha_asignacion == today).all()
print(f"Total items: {len(items)}")
for i in items:
    asesor = db.query(Asesor).filter(Asesor.id == i.asesor_id).first()
    asesor_name = f"{asesor.nombres} {asesor.apellidos} ({asesor.codigo_empleado})" if asesor else "???"
    print(f"  id={i.id} asesor={asesor_name} fecha={i.fecha_asignacion} gestion={i.tipo_gestion}")

print("\n=== Asesores en cr_asesor ===")
for a in db.query(Asesor).all():
    print(f"  id={a.id} cod={a.codigo_empleado} name={a.nombres} {a.apellidos}")

db.close()
