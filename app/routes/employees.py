import csv
import io
import json
import difflib
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, case, desc

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



@router.get("/search", response_model=schemas.SearchResponse)
def search_employees(
    q: str = Query(..., min_length=1),
    department: str | None = None,
    employee_status: str | None = Query(None, alias="status"),
    hired_after: date | None = None,
    hired_before: date | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    try:
        validate_hire_date_range(hired_after, hired_before)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    q_stripped = q.strip()
    if not q_stripped:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="q must be a non-empty string")

    query = db.query(models.Employee)

    # build text search conditions across several fields
    pattern_contains = f"%{q_stripped}%"
    pattern_starts = f"{q_stripped}%"
    search_condition = or_(
        models.Employee.first_name.ilike(pattern_contains),
        models.Employee.last_name.ilike(pattern_contains),
        models.Employee.email.ilike(pattern_contains),
        models.Employee.department.ilike(pattern_contains),
        models.Employee.job_title.ilike(pattern_contains),
    )

    # query = query.filter(search_condition)
    query = apply_employee_filters(query, models, department, employee_status, hired_after, hired_before)

    # compute a SQL-level relevance score (exact > starts-with > contains)
    q_lower = q_stripped.lower()
    score_parts = []
    for field in (models.Employee.first_name, models.Employee.last_name, models.Employee.email, models.Employee.department, models.Employee.job_title):
        score_parts.append(case(((func.lower(field) == q_lower), 100), else_=0))
        score_parts.append(case((field.ilike(pattern_starts), 50), else_=0))
    query_no_filter = query
    query = query.filter(search_condition)
    score_parts.append(case((field.ilike(pattern_contains), 10), else_=0))

    total_score = None
    for part in score_parts:
        total_score = part if total_score is None else (total_score + part)

    # Try DB-level ranking first; if it raises or returns no results, fall back to Python fuzzy ranking
    results = []
    try:
        if total_score is not None:
            query = query.order_by(desc(total_score), models.Employee.id)
        results = query.offset(offset).limit(limit).all()
        total = query.order_by(None).count()
        if results:
            return {"total": total, "results": results}
    except Exception:
        # ignore DB-level errors and fall back to Python fuzzy matching
        results = []

    # Fallback: select candidate rows (using filters only) and compute fuzzy similarity in Python
    candidates_query = db.query(models.Employee)
    candidates_query = apply_employee_filters(candidates_query, models, department, employee_status, hired_after, hired_before)
    base_candidates = candidates_query.order_by(models.Employee.id).limit(200).all()

    def compute_score(emp: models.Employee) -> float:
        score = 0.0
        fname = (emp.first_name or "").strip()
        lname = (emp.last_name or "").strip()
        email = (emp.email or "").strip()
        dept = (emp.department or "").strip()
        job = (emp.job_title or "").strip()

        # exact matches
        if fname.lower() == q_lower or lname.lower() == q_lower or email.lower() == q_lower:
            score += 100
        # starts-with
        if fname.lower().startswith(q_lower) or lname.lower().startswith(q_lower) or email.lower().startswith(q_lower):
            score += 50
        # contains
        if q_lower in fname.lower() or q_lower in lname.lower() or q_lower in email.lower() or q_lower in dept.lower() or q_lower in job.lower():
            score += 10

        # fuzzy name similarity using difflib
        name_candidates = [fname, lname, f"{fname} {lname}".strip()]
        best = 0.0
        for nc in name_candidates:
            if not nc:
                continue
            r = difflib.SequenceMatcher(None, q_lower, nc.lower()).ratio()
            if r > best:
                best = r
        score += best * 30.0
        return score

    scored = [(compute_score(emp), emp) for emp in base_candidates]
    scored.sort(key=lambda x: x[0], reverse=True)
    # only consider entries with positive score as matches
    matched = [t for t in scored if t[0] > 0]
    total_matches = len(matched)
    sliced = [emp for _, emp in matched[offset: offset + limit]]
    return {"total": total_matches, "results": sliced}


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
