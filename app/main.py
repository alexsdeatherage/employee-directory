from fastapi import FastAPI
from app.routers import employees, reports, mcp

app = FastAPI(title="Employee Directory API")
app.include_router(employees.router, prefix="/v1/employees", tags=["employees"])
app.include_router(reports.router, prefix="/v1/reports", tags=["reports"])
app.include_router(mcp.router, prefix="/v1/mcp", tags=["mcp"])