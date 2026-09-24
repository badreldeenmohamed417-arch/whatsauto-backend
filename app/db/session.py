import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Use DATABASE_URL from environment if available (for Postgres on Vercel)
# If not available, fallback to SQLite. If running on Vercel, use /tmp since root is read-only.
is_vercel = os.environ.get("VERCEL") == "1"
default_sqlite = "sqlite:////tmp/sql_app.db" if is_vercel else "sqlite:///./sql_app.db"
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", default_sqlite)

# check_same_thread is only needed for SQLite
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
