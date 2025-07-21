# db.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

DATABASE_URL = "postgresql://tempestwashco:npg_x7uo0vYgfkcw@ep-late-math-a42sboit.us-east-1.pg.koyeb.app/koyebdb?sslmode=require"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()  # ✅ use this everywhere


def init_db():
    """Initialize the database schema."""
    try:
        from models.blog import BlogPost  # 👈 make sure models are imported before calling create_all
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Database initialization failed: {e}")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
