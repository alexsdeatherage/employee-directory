from datetime import date


def apply_employee_filters(query, models, department=None, status=None, hired_after=None, hired_before=None):
    if status is None:
        query = query.filter(models.Employee.status == "active")
        query = query.filter(models.Employee.is_active.is_(True))
    else:
        query = query.filter(models.Employee.status == status)

    if department:
        query = query.filter(models.Employee.department == department)

    if hired_after:
        query = query.filter(models.Employee.hire_date >= hired_after)

    if hired_before:
        query = query.filter(models.Employee.hire_date <= hired_before)

    return query


def validate_hire_date_range(hired_after: date | None, hired_before: date | None):
    if hired_after and hired_before and hired_after > hired_before:
        raise ValueError("hired_after cannot be later than hired_before")