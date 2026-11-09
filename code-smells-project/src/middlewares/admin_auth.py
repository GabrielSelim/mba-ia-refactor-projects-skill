"""Proteção das rotas administrativas por token configurado no ambiente."""
import hmac
import logging
from functools import wraps

from flask import current_app, request

from src.errors import ForbiddenError

logger = logging.getLogger(__name__)


def require_admin_token(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN", "")
        given = request.headers.get("X-Admin-Token", "")
        if not expected or not hmac.compare_digest(given, expected):
            logger.warning("admin_access_denied path=%s ip=%s", request.path, request.remote_addr)
            raise ForbiddenError("Acesso administrativo negado")
        logger.info("admin_access path=%s ip=%s", request.path, request.remote_addr)
        return view(*args, **kwargs)

    return wrapper
