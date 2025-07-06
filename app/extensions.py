from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

database = SQLAlchemy()
csrf = CSRFProtect()