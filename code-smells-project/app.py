"""Entry point: `python app.py` sobe a API usando a configuração do ambiente."""
from src.app import create_app
from src.config.settings import Settings

app = create_app()

if __name__ == "__main__":
    app.logger.info("Servidor iniciado em http://%s:%s", Settings.HOST, Settings.PORT)
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
