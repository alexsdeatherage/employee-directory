from contextlib import asynccontextmanager
import uuid
from typing import List

from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import init_db, get_db
from app.routes import employees
from app.routes import reports
from app.routes import mcp
from app import schemas


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Employee Directory API", lifespan=lifespan)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


def _format_validation_error(request: Request, exc: RequestValidationError):
    errors = [
        {"loc": [str(x) for x in e.get("loc", [])], "msg": e.get("msg"), "type": e.get("type")} for e in exc.errors()
    ]
    payload = {
        "error": {
            "code": "invalid_input",
            "message": "Validation failed",
            "details": errors,
            "request_id": getattr(request.state, "request_id", None),
        }
    }
    return JSONResponse(status_code=422, content=payload)


def _format_http_error(request: Request, exc: StarletteHTTPException):
    payload = {
        "error": {
            "code": "http_error",
            "message": exc.detail,
            "request_id": getattr(request.state, "request_id", None),
        }
    }
    return JSONResponse(status_code=exc.status_code or 500, content=payload)


def _format_unhandled_error(request: Request, exc: Exception):
    payload = {
        "error": {
            "code": "internal_error",
            "message": "Internal server error",
            "request_id": getattr(request.state, "request_id", None),
        }
    }
    return JSONResponse(status_code=500, content=payload)


app.add_exception_handler(RequestValidationError, _format_validation_error)
app.add_exception_handler(StarletteHTTPException, _format_http_error)
app.add_exception_handler(Exception, _format_unhandled_error)


# Mount routers under /v1 for versioning
app.include_router(employees.router, prefix="/v1/employees", tags=["employees"])
app.include_router(reports.router, prefix="/v1/reports", tags=["reports"])
app.include_router(mcp.router, prefix="/mcp/tools", tags=["mcp_tools"])


@app.get("/v1/health/db")
def health_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"database": "ok"}
    except Exception as e:
        return {"database": "error", "detail": str(e)}