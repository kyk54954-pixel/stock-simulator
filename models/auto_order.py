from datetime import datetime
from app import db


class AutoOrder(db.Model):
    """A one-time simulated order evaluated whenever its symbol refreshes."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    ticker = db.Column(db.String(16), nullable=False, index=True)
    action = db.Column(db.String(8), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    trigger = db.Column(db.String(8), nullable=False)
    target_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(12), nullable=False, default='ACTIVE', index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    executed_at = db.Column(db.DateTime)
    executed_price = db.Column(db.Float)
