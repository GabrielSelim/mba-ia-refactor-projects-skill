"""Emissão e verificação de token assinado (itsdangerous, já incluído no Flask)."""
from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

_SALT = "task-manager-auth"


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=_SALT)


def issue_token(user):
    return _serializer().dumps({"uid": user.id, "role": user.role})


def verify_token(token):
    """Retorna o payload do token ou None se inválido/expirado."""
    try:
        return _serializer().loads(token, max_age=current_app.config["TOKEN_MAX_AGE_SECONDS"])
    except (BadSignature, SignatureExpired):
        return None
