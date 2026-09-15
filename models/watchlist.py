from datetime import datetime
from app import db
class Watchlist(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False,index=True)
    ticker=db.Column(db.String(16),nullable=False,index=True)
    created_at=db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    __table_args__=(db.UniqueConstraint('user_id','ticker',name='uq_watch_user_ticker'),)
