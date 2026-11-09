"""Camada View: mapeia URL + método → controller e serializa a resposta JSON."""
from flask import Blueprint, jsonify, request

from src.controllers import pedido_controller, produto_controller, system_controller, usuario_controller
from src.middlewares.admin_auth import require_admin_token

bp = Blueprint("api", __name__)


def _json(result):
    body, status = result
    return jsonify(body), status


def _body():
    return request.get_json(silent=True)


# Produtos
bp.add_url_rule("/produtos", "listar_produtos", lambda: _json(produto_controller.listar()), methods=["GET"])
bp.add_url_rule("/produtos/busca", "buscar_produtos",
                lambda: _json(produto_controller.pesquisar(request.args)), methods=["GET"])
bp.add_url_rule("/produtos/<int:id>", "buscar_produto",
                lambda id: _json(produto_controller.buscar(id)), methods=["GET"])
bp.add_url_rule("/produtos", "criar_produto", lambda: _json(produto_controller.criar(_body())), methods=["POST"])
bp.add_url_rule("/produtos/<int:id>", "atualizar_produto",
                lambda id: _json(produto_controller.atualizar(id, _body())), methods=["PUT"])
bp.add_url_rule("/produtos/<int:id>", "deletar_produto",
                lambda id: _json(produto_controller.deletar(id)), methods=["DELETE"])

# Usuários e login
bp.add_url_rule("/usuarios", "listar_usuarios", lambda: _json(usuario_controller.listar()), methods=["GET"])
bp.add_url_rule("/usuarios/<int:id>", "buscar_usuario",
                lambda id: _json(usuario_controller.buscar(id)), methods=["GET"])
bp.add_url_rule("/usuarios", "criar_usuario", lambda: _json(usuario_controller.criar(_body())), methods=["POST"])
bp.add_url_rule("/login", "login", lambda: _json(usuario_controller.login(_body())), methods=["POST"])

# Pedidos e relatórios
bp.add_url_rule("/pedidos", "criar_pedido", lambda: _json(pedido_controller.criar(_body())), methods=["POST"])
bp.add_url_rule("/pedidos", "listar_todos_pedidos", lambda: _json(pedido_controller.listar_todos()), methods=["GET"])
bp.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario",
                lambda usuario_id: _json(pedido_controller.listar_por_usuario(usuario_id)), methods=["GET"])
bp.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido",
                lambda pedido_id: _json(pedido_controller.atualizar_status(pedido_id, _body())), methods=["PUT"])
bp.add_url_rule("/relatorios/vendas", "relatorio_vendas",
                lambda: _json(pedido_controller.relatorio_vendas()), methods=["GET"])

# Sistema
bp.add_url_rule("/", "index", lambda: _json(system_controller.index()), methods=["GET"])
bp.add_url_rule("/health", "health_check", lambda: _json(system_controller.health()), methods=["GET"])
bp.add_url_rule("/admin/reset-db", "reset_database",
                require_admin_token(lambda: _json(system_controller.reset_db())), methods=["POST"])
bp.add_url_rule("/admin/query", "executar_query",
                require_admin_token(lambda: _json(system_controller.executar_query(_body()))), methods=["POST"])
