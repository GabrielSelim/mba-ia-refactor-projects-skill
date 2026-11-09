"""Configuração da aplicação lida do ambiente (sem segredos no código)."""
import os
import secrets


def _bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    """Valores com defaults seguros para desenvolvimento."""

    # Em dev, sem SECRET_KEY definida, gera uma chave aleatória a cada boot.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _bool(os.environ.get("FLASK_DEBUG"), default=False)
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
    # Rotas /admin/* ficam desabilitadas (403) enquanto ADMIN_TOKEN não for configurado.
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
    APP_VERSION = "1.0.0"
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
