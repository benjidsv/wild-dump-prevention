from app.extensions import db
from datetime import datetime

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(200))
    label = db.Column(db.String(10))  # full or empty
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # ✅ New
    location = db.Column(db.String(100))
    is_manual = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    features = db.relationship("Feature", backref="image", uselist=False)

class Feature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'), nullable=False)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    file_size = db.Column(db.Integer)
    avg_r = db.Column(db.Integer)
    avg_g = db.Column(db.Integer)
    avg_b = db.Column(db.Integer)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    mail = db.Column(db.String(200))
    password = db.Column(db.String(300))
    is_admin = db.Column(db.Boolean, default=False)
    

    images = db.relationship("Image", backref="user", lazy=True)

