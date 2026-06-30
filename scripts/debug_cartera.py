"""Debug: test cartera repo directly."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.firebase_service import init_firebase
db = init_firebase()

from app.repositories.rep_cartera import listar_por_asesor

try:
    result = listar_por_asesor(db, "d3cf4b5a-701b-4723-a116-2edce32d6676", "2026-06-11")
    print(f"OK: {len(result)} items")
    for r in result[:3]:
        print(f"  {r['cliente_nombre']}")
except Exception as e:
    import traceback
    print(f"ERROR: {type(e).__name__}: {e}")
    traceback.print_exc()
