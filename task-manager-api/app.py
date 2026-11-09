"""Composition root + entry point: `python app.py`."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from services.notification_service import NotificationService
from utils.helpers import utc_now

APP_VERSION = '1.0'


def create_app(settings=Settings, **overrides):
    app = Flask(__name__)
    app.config.from_object(settings)
    app.config.update(overrides)

    logging.basicConfig(level=app.config['LOG_LEVEL'],
                        format='%(asctime)s %(levelname)s %(name)s: %(message)s')

    CORS(app, origins=app.config['CORS_ORIGINS'])
    db.init_app(app)
    app.extensions['notification_service'] = NotificationService.from_config(app.config)

    for blueprint in (task_bp, user_bp, report_bp, category_bp):
        app.register_blueprint(blueprint)
    register_error_handlers(app)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(utc_now())}

    @app.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': APP_VERSION}

    with app.app_context():
        db.create_all()

    return app


app = create_app()   # usado por `python app.py` e por seed.py

if __name__ == '__main__':
    app.run(debug=Settings.DEBUG, host=Settings.HOST, port=Settings.PORT)
