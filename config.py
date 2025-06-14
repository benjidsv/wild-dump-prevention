import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key")
    UPLOAD_FOLDER = os.path.join("app", "static", "uploads")

    # PostgreSQL URI (dev default)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/wdp_db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevConfig(Config):
    DEBUG = True

class ProdConfig(Config):
    DEBUG = False
