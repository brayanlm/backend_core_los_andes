def get_by_codigo(db, codigo_empleado: str) -> dict | None:
    docs = (
        db.collection("asesores")
        .where("codigo_empleado", "==", codigo_empleado)
        .limit(1)
        .stream()
    )
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        return data
    return None


def get_by_id(db, asesor_id: str) -> dict | None:
    doc = db.collection("asesores").document(asesor_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    data["id"] = doc.id
    return data
