from datetime import datetime, timezone


def listar_por_asesor(db, asesor_id: str, fecha) -> list[dict]:
    fecha_str = fecha.isoformat() if hasattr(fecha, "isoformat") else str(fecha)
    docs = (
        db.collection("cartera_diaria")
        .where("asesor_id", "==", asesor_id)
        .where("fecha_asignacion", "==", fecha_str)
        .stream()
    )
    result = []
    for d in docs:
        c = d.to_dict()
        cli_doc = db.collection("clientes").document(c.get("cliente_id", "")).get()
        cli = cli_doc.to_dict() if cli_doc.exists else {}
        result.append({
            "id": d.id,
            "cliente_id": c.get("cliente_id", ""),
            "cliente_nombre": f"{cli.get('nombres', '')} {cli.get('apellidos', '')}",
            "documento": cli.get("numero_documento", ""),
            "tipo_gestion": c.get("tipo_gestion", ""),
            "prioridad": c.get("prioridad", "normal"),
            "score_prioridad": c.get("score_prioridad", 0),
            "monto_credito": float(c.get("monto_credito", 0) or 0),
            "estado_visita": c.get("estado_visita", "pendiente"),
            "orden_manual": c.get("orden_manual"),
            "lat": c.get("lat"),
            "lng": c.get("lng"),
        })
    result.sort(key=lambda x: x["score_prioridad"], reverse=True)
    return result


def marcar_visita(db, asesor_id: str, cartera_id: str, data: dict) -> bool:
    doc_ref = db.collection("cartera_diaria").document(cartera_id)
    doc = doc_ref.get()
    if not doc.exists or doc.to_dict().get("asesor_id") != asesor_id:
        return False
    estado = "visitado" if data["resultado"] == "visitado" else data["resultado"]
    doc_ref.update({
        "estado_visita": estado,
        "resultado_visita": data["resultado"],
        "observacion_visita": data.get("observacion", ""),
        "timestamp_visita": datetime.now(timezone.utc).isoformat(),
        "lat_visita": data.get("lat"),
        "lng_visita": data.get("lng"),
    })
    return True
