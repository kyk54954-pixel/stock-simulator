import os
from pathlib import Path
from dotenv import load_dotenv
BASE_DIR=Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')
class Config:
    SECRET_KEY=os.getenv('SECRET_KEY','change-this-secret-key')
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', f"sqlite:///{BASE_DIR / 'database.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    SESSION_COOKIE_HTTPONLY=True
    SESSION_COOKIE_SAMESITE='Lax'
    INITIAL_CASH=float(os.getenv('INITIAL_CASH','100000'))
    NEWS_API_KEY=os.getenv('NEWS_API_KEY','')
    FINNHUB_API_KEY=os.getenv('FINNHUB_API_KEY','')
    OPENAI_API_KEY=os.getenv('OPENAI_API_KEY','')
