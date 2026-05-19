from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date

class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    department: Optional[str] = None
    job_title: Optional[str] = None
    status: Optional[str] = "active"
    hire_date: Optional[date] = None
    dob: Optional[date] = None
    ssn: Optional[str] = None
    compensation: Optional[float] = None


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    status: Optional[str] = None
    hire_date: Optional[date] = None
    dob: Optional[date] = None
    ssn: Optional[str] = None
    compensation: Optional[float] = None


class EmployeeImportError(BaseModel):
    row: int
    email: Optional[EmailStr] = None
    message: str


class EmployeeImportSummary(BaseModel):
    total: int
    succeeded: int
    failed: int
    errors: List[EmployeeImportError]


class HeadcountRead(BaseModel):
    department: Optional[str] = None
    count: int

class EmployeeRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    department: Optional[str]
    job_title: Optional[str]
    status: Optional[str]
    hire_date: Optional[date]
    is_active: Optional[bool]

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    total: int
    results: List[EmployeeRead]


class ErrorDetail(BaseModel):
    loc: List[str]
    msg: str
    type: str | None = None


class ErrorResponse(BaseModel):
    error: dict


class MCPToolInfo(BaseModel):
    name: str
    version: str
    description: str


class MCPEmployee(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    department: Optional[str]
    job_title: Optional[str]
    status: Optional[str]
    hire_date: Optional[date]
    match_score: float


class MCPToolResponse(BaseModel):
    tool: MCPToolInfo
    request_id: Optional[str]
    query: str
    total: int
    results: List[MCPEmployee]
    summary: Optional[str] = None
    confidence: Optional[float] = None
    notes: Optional[List[str]] = None