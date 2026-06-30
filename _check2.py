import requests, json

# Login as asesor 001
r = requests.post('http://localhost:8010/auth/login',
    json={'codigo_empleado': '001', 'password': 'asesor123'})
data = r.json()
token = data['access_token']
asesor = data['asesor']
print(f"Logged in as: {asesor['nombres']} {asesor['apellidos']} (id={asesor['id']})")

# Get cartera
r2 = requests.get('http://localhost:8010/cartera',
    params={'fecha': '2026-06-18'},
    headers={'Authorization': 'Bearer ' + token})
print(f"Cartera status: {r2.status_code}")
print(f"Cartera body: {r2.text}")

# Get cartera without fecha (should use today)
r3 = requests.get('http://localhost:8010/cartera',
    headers={'Authorization': 'Bearer ' + token})
print(f"\nCartera (sin fecha) status: {r3.status_code}")
print(f"Cartera (sin fecha) body: {r3.text}")
