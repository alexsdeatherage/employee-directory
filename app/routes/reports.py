from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.routes.employee_filters import apply_employee_filters, validate_hire_date_range

router = APIRouter()


@router.get("/headcount", response_model=list[schemas.HeadcountRead])
def headcount_report(

    department: str | None = None,
    employee_status: str | None = Query(None, alias="status"),
    hired_after: date | None = None,
    hired_before: date | None = None,
    db: Session = Depends(get_db),
):
    try:
        validate_hire_date_range(hired_after, hired_before)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    query = db.query(
        models.Employee.department.label("department"),
        func.count(models.Employee.id).label("count"),
    )
    query = apply_employee_filters(query, models, department, employee_status, hired_after, hired_before)
    rows = query.group_by(models.Employee.department).order_by(models.Employee.department).all()
    return [{"department": department, "count": count} for department, count in rows]