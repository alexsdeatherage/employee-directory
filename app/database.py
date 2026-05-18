import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback to a local sqlite URL for safety if DATABASE_URL not set
    DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Import models so that Base.metadata knows about them
    # Models import Base from this module already; ensure they are imported
    try:
        import app.models  # noqa: F401
    except Exception:
        pass
    Base.metadata.create_all(bind=engine)
