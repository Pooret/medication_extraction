# database.py
from sqlmodel import create_engine, Session
import os


# load env variables
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_password")
DB_HOST = os.getenv("DB_HOST", "your_rds_endpoint")
DB_NAME = os.getenv("DB_NAME", "medicationdb")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

def get_db():
    with Session(engine) as session:
        yield session