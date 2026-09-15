from datetime import datetime
from app import db
class Portfolio(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False,index=True)
    ticker=db.Column(db.String(16),nullable=False,index=True)
    shares=db.Column(db.Integer,nullable=False)
    average_price=db.Column(db.Float,nullable=False)
    updated_at=db.Column(db.DateTime,nullable=False,default=datetime.utcnow,onupdate=datetime.utcnow)
    __table_args__=(db.UniqueConstraint('user_id','ticker',name='uq_user_ticker'),)
