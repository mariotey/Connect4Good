from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql://postgres:password@localhost:5432/Connect4Good"
engine = create_engine(DB_URL)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False) # expire_on_commit=False is used to prevent the session from being closed after a commit

def check_db_connection():
    try:
        engine.connect()
        return True
    except:
        return False