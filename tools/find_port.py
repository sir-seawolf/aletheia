"""Prints the first free TCP port starting from argv[1] (default 8000)."""
import socket
import sys

start = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
for port in range(start, start + 10):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        s.close()
        print(port)
        sys.exit(0)
    except OSError:
        pass
sys.exit(1)
