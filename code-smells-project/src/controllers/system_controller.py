"""Endpoints de sistema: índice, health check e operações administrativas."""
import logging

from flask import current_app

from src.controllers.validators import exigir_json
from src.database import get_db, transaction
from src.errors import ValidationError
from src.models.pedido_model import PedidoModel

logger = logging.getLogger(__name__)

TABELAS_RESET = ("itens_pedido", "pedidos", "produtos", "usuarios")


def index():
    return {
        "mensagem": "Bem-vindo à API da Loja",
        "versao": current_app.config["APP_VERSION"],
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    }, 200


def health():
    # Sem secret_key, caminho do banco ou flags internas na resposta.
    return {
        "status": "ok",
        "database": "connected",
        "counts": PedidoModel(get_db()).contagens(),
        "versao": current_app.config["APP_VERSION"],
    }, 200


def reset_db():
    conn = get_db()
    with transaction(conn):
        for tabela in TABELAS_RESET:
            conn.execute(f"DELETE FROM {tabela}")   # nomes fixos, não vêm do request
    logger.warning("banco_resetado")
    return {"mensagem": "Banco de dados resetado", "sucesso": True}, 200


def executar_query(dados):
    """Console de consulta administrativo: somente leitura (SELECT)."""
    sql = (exigir_json(dados).get("sql") or "").strip()
    if not sql:
        raise ValidationError("Query não informada")
    if not sql.upper().startswith("SELECT"):
        raise ValidationError("Somente consultas SELECT são permitidas")
    rows = get_db().execute(sql).fetchall()
    logger.info("admin_query executada")
    return {"dados": [dict(r) for r in rows], "sucesso": True}, 200
