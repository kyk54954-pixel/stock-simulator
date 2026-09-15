from datetime import datetime
from app import db
from config import Config
class User(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(80),unique=True,nullable=False,index=True)
    email=db.Column(db.String(160),unique=True,nullable=False,index=True)
    password_hash=db.Column(db.String(255),nullable=False)
    cash=db.Column(db.Float,nullable=False,default=Config.INITIAL_CASH)
    initial_cash=db.Column(db.Float,nullable=False,default=Config.INITIAL_CASH)
    created_at=db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    portfolios=db.relationship('Portfolio',backref='user',lazy=True,cascade='all, delete-orphan')
    transactions=db.relationship('Transaction',backref='user',lazy=True,cascade='all, delete-orphan')
