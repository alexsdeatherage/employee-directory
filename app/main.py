from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import init_db, get_db
from app.routes import employees
from app.routes import reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Employee Directory API", lifespan=lifespan)

app.include_router(employees.router, prefix="/employees", tags=["employees"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"database": "ok"}
    except Exception as e:
        return {"database": "error", "detail": str(e)}