import subprocess
import threading
import sys

# Color codes
RED = "\033[0;31m"
GREEN = "\033[0;32m"
NC = "\033[0m"

procs = [
    ("mcp-server", RED, [sys.executable, "-u", "mcp_server.py"]),
    ("fastapi", GREEN, [sys.executable, "-m", "uvicorn", "main:app", "--reload"]),
]

def stream_output(prefix, color, proc):
    for line in iter(proc.stdout.readline, b''):
        print(f"{color}[{prefix}] {line.decode().rstrip()}{NC}", flush=True)

threads = []
processes = []
for prefix, color, cmd in procs:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    t = threading.Thread(target=stream_output, args=(prefix, color, proc))
    t.daemon = True
    t.start()
    threads.append(t)
    processes.append(proc)

try:
    for proc in processes:
        proc.wait()
except KeyboardInterrupt:
    for proc in processes:
        proc.terminate() 