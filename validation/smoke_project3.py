"""Smoke test dos 22 endpoints originais do task-manager-api.

Uso: python smoke_project3.py <base_url>
Imprime status HTTP e chaves de primeiro nível; rodado antes (baseline) e depois da refatoração.
"""
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1].rstrip("/")


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status, raw = resp.status, resp.read()
    except urllib.error.HTTPError as err:
        status, raw = err.code, err.read()
    try:
        payload = json.loads(raw or b"null")
    except ValueError:
        payload = raw.decode(errors="replace")[:60]
    if isinstance(payload, dict):
        shape = sorted(payload.keys())
    elif isinstance(payload, list):
        shape = f"list[{len(payload)}] " + (str(sorted(payload[0].keys())) if payload and isinstance(payload[0], dict) else "")
    else:
        shape = repr(payload)
    print(f"{method:6} {path:34} -> {status}  {shape}")
    return status, payload


def new_id(payload):
    return payload.get("id") if isinstance(payload, dict) else None


call("GET", "/")
call("GET", "/health")

# Tasks
call("GET", "/tasks")
call("GET", "/tasks/1")
call("GET", "/tasks/9999")
_, task = call("POST", "/tasks", {"title": "Nova task smoke", "description": "criada pelo smoke", "priority": 2,
                                  "user_id": 1, "category_id": 1, "due_date": "2026-12-01", "tags": ["a", "b"]})
tid = new_id(task) or 9999
call("POST", "/tasks", {"title": "ab"})
call("POST", "/tasks", {"title": "Prioridade texto", "priority": "alta"})
call("PUT", f"/tasks/{tid}", {"status": "done", "priority": 1})
call("PUT", f"/tasks/{tid}", {"status": "invalido"})
call("GET", "/tasks/search?q=API")
call("GET", "/tasks/search?priority=abc")
call("GET", "/tasks/stats")
call("DELETE", f"/tasks/{tid}")

# Users
call("GET", "/users")
call("GET", "/users/1")
_, user = call("POST", "/users", {"name": "Smoke User", "email": "smoke@teste.com", "password": "segura123"})
uid = new_id(user) or 9999
call("POST", "/users", {"name": "Dup", "email": "smoke@teste.com", "password": "segura123"})
call("PUT", f"/users/{uid}", {"name": "Smoke User 2"})
call("GET", "/users/1/tasks")
call("POST", "/login", {"email": "joao@email.com", "password": "1234"})
call("POST", "/login", {"email": "joao@email.com", "password": "errada"})
call("DELETE", f"/users/{uid}")

# Reports & categories
call("GET", "/reports/summary")
call("GET", "/reports/user/1")
call("GET", "/categories")
_, cat = call("POST", "/categories", {"name": "QA", "description": "Qualidade", "color": "#123456"})
cid = new_id(cat) or 9999
call("PUT", f"/categories/{cid}", {"name": "QA 2"})
call("PUT", f"/categories/{cid}", None)
call("DELETE", f"/categories/{cid}")
