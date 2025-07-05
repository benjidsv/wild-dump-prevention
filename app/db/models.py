from app.extensions import db
from datetime import datetime

class Image(db.Model):
    __tablename__ = "image"
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(200))
    label = db.Column(db.String(10))  # full or empty
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # ✅ New
    label_manual = db.Column(db.Boolean, default=False)  # FALSE = auto/rules
    timestamp_manual = db.Column(db.Boolean, default=False)
    location_manual = db.Column(db.Boolean, default=False)

    # FK vers Location (une seule location par image)
    location_id = db.Column(db.Integer, db.ForeignKey("location.id", ondelete="CASCADE"), nullable=False)
    location = db.relationship("Location", back_populates="images")

    # FK vers User
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    mail = db.Column(db.String(200))
    password = db.Column(db.String(300))
    is_admin = db.Column(db.Boolean, default=False)
    

    images = db.relationship("Image", backref="user", lazy=True, cascade="all, delete-orphan", passive_deletes=True)

class Location(db.Model):
    __tablename__ = "location"
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(200))
    longitude = db.Column(db.Float)
    latitude  = db.Column(db.Float)

    # 1 location ➜ plusieurs images
    images = db.relationship("Image", back_populates="location", lazy=True, cascade="all, delete-orphan", passive_deletes=True)

    

