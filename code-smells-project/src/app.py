"""Composition root: monta a aplicação (config, banco, serviços, rotas e erros)."""
import logging

from flask import Flask
from flask_cors import CORS

from src import database
from src.config.settings import Settings
from src.middlewares.error_handler import register_error_handlers
from src.services.notification_service import NotificationService
from src.views.routes import bp as api_bp


def create_app(settings=Settings, **overrides):
    app = Flask(__name__)
    app.config.from_object(settings)
    app.config.update(overrides)

    logging.basicConfig(level=app.config["LOG_LEVEL"],
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    CORS(app, origins=app.config["CORS_ORIGINS"])
    database.init_app(app)
    app.extensions["notification_service"] = NotificationService()

    app.register_blueprint(api_bp)
    register_error_handlers(app)
    return app
