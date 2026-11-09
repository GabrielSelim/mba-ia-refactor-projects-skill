"""Smoke test dos endpoints originais do code-smells-project.

Uso: python smoke_project1.py <base_url> [admin_token]
Imprime, para cada chamada, o status HTTP e as chaves de primeiro nível do JSON.
Rodado antes (baseline) e depois da refatoração; as saídas são comparadas.
"""
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1].rstrip("/")
ADMIN_TOKEN = sys.argv[2] if len(sys.argv) > 2 else None


def call(method, path, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status, raw = resp.status, resp.read()
    except urllib.error.HTTPError as err:
        status, raw = err.code, err.read()
    try:
        payload = json.loads(raw or b"null")
    except ValueError:
        payload = raw.decode(errors="replace")[:80]
    keys = sorted(payload.keys()) if isinstance(payload, dict) else type(payload).__name__
    print(f"{method:6} {path:32} -> {status}  {keys}")
    return status, payload


call("GET", "/")
call("GET", "/health")
call("GET", "/produtos")
call("GET", "/produtos/busca?q=Mouse&categoria=informatica")
call("GET", "/produtos/1")
call("GET", "/produtos/9999")
_, novo = call("POST", "/produtos", {"nome": "Produto Teste", "descricao": "smoke", "preco": 10.5,
                                     "estoque": 5, "categoria": "geral"})
pid = (novo.get("dados") or {}).get("id", 9999) if isinstance(novo, dict) else 9999
call("PUT", f"/produtos/{pid}", {"nome": "Produto Teste 2", "preco": 12.0, "estoque": 3, "categoria": "geral"})
call("POST", "/produtos", {"nome": "X"})
call("GET", "/usuarios")
call("GET", "/usuarios/1")
call("POST", "/usuarios", {"nome": "Smoke", "email": "smoke@teste.com", "senha": "smoke123"})
call("POST", "/login", {"email": "admin@loja.com", "senha": "admin123"})
call("POST", "/login", {"email": "admin@loja.com", "senha": "errada"})
call("POST", "/login", {"email": "' OR '1'='1' --", "senha": "x"})
call("POST", "/pedidos", {"usuario_id": 2, "itens": [{"produto_id": 1, "quantidade": 1},
                                                      {"produto_id": 2, "quantidade": 2}]})
call("POST", "/pedidos", {"usuario_id": 2, "itens": [{"produto_id": 1, "quantidade": 99999}]})
call("GET", "/pedidos")
call("GET", "/pedidos/usuario/2")
call("PUT", "/pedidos/1/status", {"status": "aprovado"})
call("PUT", "/pedidos/1/status", {"status": "invalido"})
call("GET", "/relatorios/vendas")
call("DELETE", f"/produtos/{pid}")
admin = {"X-Admin-Token": ADMIN_TOKEN} if ADMIN_TOKEN else {}
call("POST", "/admin/query", {"sql": "SELECT COUNT(*) AS n FROM produtos"})
if ADMIN_TOKEN:
    call("POST", "/admin/query", {"sql": "SELECT COUNT(*) AS n FROM produtos"}, admin)
    call("POST", "/admin/query", {"sql": "DELETE FROM produtos"}, admin)
call("POST", "/admin/reset-db", None, admin)
