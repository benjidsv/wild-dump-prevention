from app.extensions import database
from datetime import datetime

class Image(database.Model):
    __tablename__ = "image"
    id = database.Column(database.Integer, primary_key=True)
    path = database.Column(database.String(200))
    label = database.Column(database.String(10))  # full or empty
    timestamp = database.Column(database.DateTime, default=datetime.utcnow)  # ✅ New
    label_manual = database.Column(database.Boolean, default=False)  # FALSE = auto/rules
    timestamp_manual = database.Column(database.Boolean, default=False)
    location_manual = database.Column(database.Boolean, default=False)

    # FK vers Location (une seule location par image)
    location_id = database.Column(database.Integer, database.ForeignKey("location.id", ondelete="CASCADE"), nullable=False)
    location = database.relationship("Location", back_populates="images")

    # FK vers User
    user_id = database.Column(database.Integer, database.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)


class User(database.Model):
    __tablename__ = "user"
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(200))
    mail = database.Column(database.String(200))
    password = database.Column(database.String(300))
    is_admin = database.Column(database.Boolean, default=False)
    is_superadmin = database.Column(database.Boolean, default=False)

    images = database.relationship("Image", backref="user", lazy=True, cascade="all, delete-orphan", passive_deletes=True)

class Location(database.Model):
    __tablename__ = "location"
    id = database.Column(database.Integer, primary_key=True)
    address = database.Column(database.String(200))
    longitude = database.Column(database.Float)
    latitude  = database.Column(database.Float)

    # 1 location ➜ plusieurs images
    images = database.relationship("Image", back_populates="location", lazy=True, cascade="all, delete-orphan", passive_deletes=True)

    

