from fastapi import FastAPI
from app.routers import employees, reports, mcp
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./dev.db"  # replace with env var in production
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

app = FastAPI(title="Employee Directory API")
app.include_router(employees.router, prefix="/v1/employees", tags=["employees"])
app.include_router(reports.router, prefix="/v1/reports", tags=["reports"])
app.include_router(mcp.router, prefix="/v1/mcp", tags=["mcp"])