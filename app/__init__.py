from flask import Flask
from config import DevConfig
from app.extensions import db

def create_app(config_class=DevConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    return app
