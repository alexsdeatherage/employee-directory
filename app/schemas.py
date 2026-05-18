from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    department: Optional[str]
    job_title: Optional[str]
    status: Optional[str] = "active"
    hire_date: Optional[date]
    dob: Optional[date]
    ssn: Optional[str]
    compensation: Optional[float]

class EmployeeRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    department: Optional[str]
    job_title: Optional[str]
    status: Optional[str]
    hire_date: Optional[date]

    class Config:
        orm_mode = True