from flask import Flask
from flask_cors import CORS


def create_app() -> Flask:
    app = Flask(__name__)

    # Enable CORS (customize origins in config later if needed)
    CORS(app)

    # Register blueprints
    from .api import register_blueprints

    register_blueprints(app)

    # Health root
    @app.route("/")
    def root():
        return {"status": "ok", "service": "DynamicDo API"}

    return app


