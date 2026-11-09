"""Fluxo dos casos de uso de produtos."""
import logging

from src.controllers.validators import float_opcional, validar_produto
from src.database import get_db
from src.errors import NotFoundError
from src.models.produto_model import ProdutoModel

logger = logging.getLogger(__name__)


def _model():
    return ProdutoModel(get_db())


def _obter_ou_404(model, produto_id):
    produto = model.buscar_por_id(produto_id)
    if produto is None:
        raise NotFoundError("Produto não encontrado")
    return produto


def listar():
    produtos = _model().listar()
    logger.info("produtos_listados total=%s", len(produtos))
    return {"dados": produtos, "sucesso": True}, 200


def buscar(produto_id):
    return {"dados": _obter_ou_404(_model(), produto_id), "sucesso": True}, 200


def criar(dados):
    produto = validar_produto(dados)
    produto_id = _model().criar(**produto)
    logger.info("produto_criado id=%s", produto_id)
    return {"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}, 201


def atualizar(produto_id, dados):
    model = _model()
    _obter_ou_404(model, produto_id)
    model.atualizar(produto_id, **validar_produto(dados))
    return {"sucesso": True, "mensagem": "Produto atualizado"}, 200


def deletar(produto_id):
    model = _model()
    _obter_ou_404(model, produto_id)
    model.deletar(produto_id)
    logger.info("produto_deletado id=%s", produto_id)
    return {"sucesso": True, "mensagem": "Produto deletado"}, 200


def pesquisar(args):
    resultados = _model().pesquisar(
        termo=args.get("q", ""),
        categoria=args.get("categoria") or None,
        preco_min=float_opcional(args.get("preco_min"), "preco_min"),
        preco_max=float_opcional(args.get("preco_max"), "preco_max"),
    )
    return {"dados": resultados, "total": len(resultados), "sucesso": True}, 200
