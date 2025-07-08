from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_babel import Babel

babel = Babel()
database = SQLAlchemy()
csrf = CSRFProtect()