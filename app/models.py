from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, Float
from app.database import Base
from datetime import datetime

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    department = Column(String, index=True)
    job_title = Column(String, index=True)
    status = Column(String, default="active")
    hire_date = Column(Date, nullable=True)
    dob = Column(Date, nullable=True)
    ssn = Column(String, nullable=True)
    compensation = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)