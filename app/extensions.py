from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_socketio import SocketIO

database = SQLAlchemy()
csrf = CSRFProtect()
socketio = SocketIO(cors_allowed_origins="*")