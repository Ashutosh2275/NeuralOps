import socket

ports = [
    ("PostgreSQL", 5433),
    ("Redis", 6380),
    ("Prometheus", 9090),
    ("Loki", 3100),
    ("Ollama", 11434),
    ("Backend", 8000),
    ("Frontend", 5173),
]

for name, p in ports:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    res = s.connect_ex(('127.0.0.1', p))
    s.close()
    status = "OPEN" if res == 0 else "CLOSED"
    print(f"[{status}] {name} on port {p}")
