import json, urllib.request, urllib.error
import sys; sys.path.insert(0, '.')
from datetime import datetime, timezone
from app.core.cfg_config import settings
from app.core.firebase_service import init_firebase, get_firestore

init_firebase()
db = get_firestore()

# 1. Delete Carlos Ramirez (0001)
docs = db.collection('asesores').where('codigo_empleado', '==', '0001').stream()
for d in docs:
    db.collection('asesores').document(d.id).delete()
    print(f'Eliminado asesor 0001 (id: {d.id})')

# 2. Ensure user asesor (75223330) has all required fields
docs = db.collection('asesores').where('codigo_empleado', '==', '75223330').stream()
found = False
for d in docs:
    found = True
    data = d.to_dict()
    print(f'Asesor encontrado: {data.get("nombres")} {data.get("apellidos")}')
    updates = {}
    if not data.get('created_at'):
        updates['created_at'] = datetime.now(timezone.utc).isoformat()
    if not data.get('cod_asesor'):
        updates['cod_asesor'] = 'A' + str(data.get('codigo_empleado', ''))
    if not data.get('agencia_id'):
        updates['agencia_id'] = ''
    if updates:
        db.collection('asesores').document(d.id).update(updates)
        print(f'Campos agregados: {updates}')
    else:
        print('Todos los campos requeridos ya existen')

# 3. Test login with user's password
codigo = '75223330'
email = f'{codigo}@bancodelosandes.com'
url = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={settings.FIREBASE_WEB_API_KEY}'
body = json.dumps({'email': email, 'password': '123456', 'returnSecureToken': True}).encode()
req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    print(f'Login OK! Firebase uid: {data.get("localId")}')
except urllib.error.HTTPError as e:
    err = json.loads(e.read())
    msg = err.get('error', {}).get('message', '')
    if msg == 'INVALID_PASSWORD':
        print('Auth: usuario existe pero password incorrecto')
    elif msg == 'EMAIL_NOT_FOUND':
        print('Auth: USUARIO NO EXISTE en Firebase Auth — hay que crearlo')
    else:
        print(f'Auth: {msg}')
