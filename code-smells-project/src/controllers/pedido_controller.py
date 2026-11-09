"""Fluxo dos casos de uso de pedidos e relatório de vendas."""
import logging

from flask import current_app

from src.controllers.validators import exigir_json, validar_itens_pedido
from src.database import get_db
from src.errors import ValidationError
from src.models.pedido_model import STATUS_APROVADO, STATUS_CANCELADO, STATUS_VALIDOS, PedidoModel

logger = logging.getLogger(__name__)


def _model():
    return PedidoModel(get_db())


def _notifications():
    # Serviço injetado pelo composition root (src/app.py).
    return current_app.extensions["notification_service"]


def criar(dados):
    dados = exigir_json(dados)
    usuario_id = dados.get("usuario_id")
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    itens = validar_itens_pedido(dados.get("itens", []))

    resultado = _model().criar(usuario_id, itens)
    _notifications().notify_order_created(resultado["pedido_id"], usuario_id)
    return {"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}, 201


def listar_todos():
    return {"dados": _model().listar_todos(), "sucesso": True}, 200


def listar_por_usuario(usuario_id):
    return {"dados": _model().listar_por_usuario(usuario_id), "sucesso": True}, 200


def atualizar_status(pedido_id, dados):
    dados = exigir_json(dados)
    novo_status = dados.get("status", "")
    if novo_status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido")
    _model().atualizar_status(pedido_id, novo_status)
    if novo_status in (STATUS_APROVADO, STATUS_CANCELADO):
        _notifications().notify_order_status(pedido_id, novo_status)
    return {"sucesso": True, "mensagem": "Status atualizado"}, 200


def relatorio_vendas():
    return {"dados": _model().relatorio_vendas(), "sucesso": True}, 200
