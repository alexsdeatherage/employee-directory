from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app import schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.EmployeeRead])
def list_employees():
    return []

@router.post("/", response_model=schemas.EmployeeRead)
def create_employee(payload: schemas.EmployeeCreate):
    return {}

@router.get("/search")
def search_employees(q: str):
    return {"q": q}

@router.get("/{employee_id}", response_model=schemas.EmployeeRead)
def get_employee(employee_id: int):
    raise HTTPException(status_code=404, detail="Not found")

@router.put("/{employee_id}", response_model=schemas.EmployeeRead)
def update_employee(employee_id: int, payload: schemas.EmployeeCreate):
    return {}

@router.delete("/{employee_id}")
def delete_employee(employee_id: int):
    return {"result": "deactivated"}