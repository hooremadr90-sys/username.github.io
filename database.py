from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Farm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Crop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    stage = db.Column(db.String(50), default='Growing')
    quantity = db.Column(db.Integer, default=0)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Monitoring(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float)
    ph = db.Column(db.Float)
    ec = db.Column(db.Float)
    water_level = db.Column(db.Integer)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SaleRecord(db.Model):  # For charts (manual entry or mock)
    id = db.Column(db.Integer, primary_key=True)
    crop_name = db.Column(db.String(100))
    quantity_sold = db.Column(db.Integer)
    revenue = db.Column(db.Float)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'))