import csv
import io
import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.routes.employee_filters import apply_employee_filters, validate_hire_date_range

router = APIRouter()


@router.get("", response_model=list[schemas.EmployeeRead])
def list_employees(
    department: str | None = None,
    employee_status: str | None = Query(None, alias="status"),
    hired_after: date | None = None,
    hired_before: date | None = None,
    db: Session = Depends(get_db),
):
    try:
        validate_hire_date_range(hired_after, hired_before)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    query = db.query(models.Employee)
    query = apply_employee_filters(query, models, department, employee_status, hired_after, hired_before)
    return query.order_by(models.Employee.id).all()


@router.post("/import", response_model=schemas.EmployeeImportSummary)
async def import_employees(request: Request, db: Session = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    raw_body = await request.body()
    rows = []

    if "application/json" in content_type:
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

        if not isinstance(payload, list):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="JSON import must be an array of employees")
        rows = payload
    elif "text/csv" in content_type or "application/csv" in content_type:
        decoded = raw_body.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))
        rows = list(reader)
    else:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Content-Type must be application/json or text/csv",
        )

    summary = {"total": len(rows), "succeeded": 0, "failed": 0, "errors": []}

    for index, row in enumerate(rows, start=1):
        try:
            normalized = _normalize_import_row(row)
            payload = schemas.EmployeeCreate(**normalized)
            employee_data = payload.model_dump(exclude_none=True)
            employee = db.query(models.Employee).filter(models.Employee.email == payload.email).first()

            if employee:
                updates = payload.model_dump(exclude_none=True)
                for key, value in updates.items():
                    setattr(employee, key, value)
                employee.is_active = True
            else:
                employee = models.Employee(**employee_data)
                db.add(employee)

            db.commit()
            summary["succeeded"] += 1
        except (ValidationError, ValueError) as exc:
            db.rollback()
            summary["failed"] += 1
            summary["errors"].append(
                {"row": index, "email": _safe_email(row), "message": str(exc)}
            )
        except Exception as exc:
            db.rollback()
            summary["failed"] += 1
            summary["errors"].append(
                {"row": index, "email": _safe_email(row), "message": str(exc)}
            )

    return summary


@router.get("/{employee_id}", response_model=schemas.EmployeeRead)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not employee or not employee.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


@router.post("", response_model=schemas.EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(payload: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Employee).filter(models.Employee.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    data = payload.model_dump()
    employee = models.Employee(**data)
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.put("/{employee_id}", response_model=schemas.EmployeeRead)
def update_employee(employee_id: int, payload: schemas.EmployeeUpdate, db: Session = Depends(get_db)):
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not employee or not employee.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(employee, key, value)
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not employee or not employee.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    employee.is_active = False
    employee.status = "inactive"
    db.add(employee)
    db.commit()
    return


def _normalize_import_row(row):
    normalized = {}
    for key, value in row.items():
        if value is None:
            normalized[key] = None
            continue
        if isinstance(value, str):
            stripped = value.strip()
            normalized[key] = stripped or None
        else:
            normalized[key] = value
    return normalized


def _safe_email(row):
    value = row.get("email") if isinstance(row, dict) else None
    if isinstance(value, str):
        return value.strip() or None
    return value
