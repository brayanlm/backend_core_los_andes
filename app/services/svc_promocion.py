"""Puente deshabilitado: no hay core bancario en modo Firebase."""
def promover(db):
    return {"status": "ok", "message": "Promocion deshabilitada (modo Firebase)"}

def listar_outbox(db):
    return []
