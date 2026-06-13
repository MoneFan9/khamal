import socket
import sys

print("[2024-05-20 10:00:00] INFO: Booting worker with pid: 123")
print("[2024-05-20 10:00:01] DEBUG: Checking port availability...")

port = 8000
# Create a dummy listener to occupy the port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind(('127.0.0.1', port))
    s.listen(1)

    # Try to bind again to the same port in another socket
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2.bind(('127.0.0.1', port))
except OSError as e:
    print(f"[2024-05-20 10:00:01] ERROR: [Errno {e.errno}] {e.strerror}", file=sys.stderr)
    print(f"[2024-05-20 10:00:01] CRITICAL: Failed to bind to port {port}.", file=sys.stderr)
    sys.exit(1)
finally:
    s.close()
    print("[2024-05-20 10:00:01] INFO: Shutting down...")
