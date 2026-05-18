from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import init_db, get_db
from app.routes import employees

app = FastAPI(title="Employee Directory API")


@app.on_event("startup")
def on_startup():
	init_db()


# Register routers
app.include_router(employees.router, prefix="/employees", tags=["employees"])


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
	try:
		db.execute(text("SELECT 1"))
		return {"database": "ok"}
	except Exception as e:
		return {"database": "error", "detail": str(e)}