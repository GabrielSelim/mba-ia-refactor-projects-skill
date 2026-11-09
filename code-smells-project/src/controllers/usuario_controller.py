"""Fluxo dos casos de uso de usuários e login."""
import logging

from src.controllers.validators import exigir_json
from src.database import get_db
from src.errors import NotFoundError, UnauthorizedError, ValidationError
from src.models.usuario_model import UsuarioModel

logger = logging.getLogger(__name__)


def _model():
    return UsuarioModel(get_db())


def listar():
    return {"dados": _model().listar(), "sucesso": True}, 200


def buscar(usuario_id):
    usuario = _model().buscar_por_id(usuario_id)
    if usuario is None:
        raise NotFoundError("Usuário não encontrado")
    return {"dados": usuario, "sucesso": True}, 200


def criar(dados):
    dados = exigir_json(dados)
    nome, email, senha = dados.get("nome", ""), dados.get("email", ""), dados.get("senha", "")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    usuario_id = _model().criar(nome, email, senha)
    logger.info("usuario_criado id=%s", usuario_id)
    return {"dados": {"id": usuario_id}, "sucesso": True}, 201


def login(dados):
    dados = exigir_json(dados)
    email, senha = dados.get("email", ""), dados.get("senha", "")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    usuario = _model().autenticar(email, senha)
    if usuario is None:
        logger.info("login_falhou")
        raise UnauthorizedError("Email ou senha inválidos")
    logger.info("login_ok usuario=%s", usuario["id"])
    return {"dados": usuario, "sucesso": True, "mensagem": "Login OK"}, 200
