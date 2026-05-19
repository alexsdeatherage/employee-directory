from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import difflib

from app import schemas, models
from app.database import get_db
from app.routes.employee_filters import apply_employee_filters

router = APIRouter()


@router.get("/employee-lookup", response_model=schemas.MCPToolResponse)
def employee_lookup(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Stub MCP tool endpoint that accepts a natural language query `q` and returns structured employee results.

    Behavior (stub):
    - Performs a simple rule-based parsing: looks for status keywords and uses substring search across name/email/department/job_title.
    - Computes a simple `match_score` using exact/startswith/contains and a difflib similarity on names.
    - Never returns sensitive fields.
    """
    q_str = q.strip()
    if not q_str:
        raise HTTPException(status_code=400, detail="q must be a non-empty string")

    # Basic rule: if query contains "inactive", search for inactive, else default to active
    status = "active"
    if "inactive" in q_str.lower():
        status = "inactive"

    # Build base query and apply status filter
    query = db.query(models.Employee)
    query = apply_employee_filters(query, models, None, status, None, None)

    # Simple substring search across selected fields
    pattern = f"%{q_str}%"
    candidates = query.filter(
        models.Employee.first_name.ilike(pattern)
        | models.Employee.last_name.ilike(pattern)
        | models.Employee.email.ilike(pattern)
        | models.Employee.department.ilike(pattern)
        | models.Employee.job_title.ilike(pattern)
    ).limit(100).all()

    def score_emp(emp: models.Employee) -> float:
        score = 0.0
        ql = q_str.lower()
        fname = (emp.first_name or "").lower()
        lname = (emp.last_name or "").lower()
        email = (emp.email or "").lower()
        dept = (emp.department or "").lower()
        job = (emp.job_title or "").lower()

        if fname == ql or lname == ql or email == ql:
            score += 1.0
        if fname.startswith(ql) or lname.startswith(ql) or email.startswith(ql):
            score += 0.6
        if ql in fname or ql in lname or ql in email or ql in dept or ql in job:
            score += 0.2

        # fuzzy name similarity
        best = 0.0
        for nc in [fname, lname, f"{fname} {lname}".strip()]:
            if not nc:
                continue
            r = difflib.SequenceMatcher(None, ql, nc).ratio()
            if r > best:
                best = r
        score += best * 0.5
        return min(score, 1.0)

    results = []
    for emp in candidates:
        results.append(
            {
                "id": emp.id,
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "email": emp.email,
                "department": emp.department,
                "job_title": emp.job_title,
                "status": emp.status,
                "hire_date": emp.hire_date,
                "match_score": round(score_emp(emp), 3),
            }
        )

    # sort by match_score desc
    results.sort(key=lambda r: r["match_score"], reverse=True)

    summary = f"Found {len(results)} employees matching query"

    return {
        "tool": {"name": "employee-lookup", "version": "v1", "description": "Lookup employees by natural language"},
        "request_id": None,
        "query": q_str,
        "total": len(results),
        "results": results,
        "summary": summary,
        "confidence": 0.6,
        "notes": ["Stub parser: rule-based matching and basic fuzzy scoring"]
    }
