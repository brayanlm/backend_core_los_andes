import subprocess, sys, time
p = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
)
start = time.time()
while time.time() - start < 25:
    line = p.stdout.readline()
    if line:
        print(line, end="", flush=True)
    if "Uvicorn running" in line or "Application startup complete" in line:
        break
    time.sleep(0.1)
else:
    print("\n[TIMEOUT 25s] No se completo el startup")
    p.kill()
    p.wait()
