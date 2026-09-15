from datetime import datetime
from app import db
class Transaction(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False,index=True)
    ticker=db.Column(db.String(16),nullable=False,index=True)
    action=db.Column(db.String(8),nullable=False)
    price=db.Column(db.Float,nullable=False)
    quantity=db.Column(db.Integer,nullable=False)
    total=db.Column(db.Float,nullable=False)
    realized_profit=db.Column(db.Float,nullable=False,default=0)
    created_at=db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
