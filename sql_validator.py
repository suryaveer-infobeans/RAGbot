SCHEMA = {
    "employees": {
        "employee_id", "first_name", "last_name", "email", "phone",
        "hire_date", "job_title", "department", "salary", "manager_id",
        "created_at", "updated_at"
    },
    "employee_addresses": {
        "address_id", "employee_id", "address_type", "street", "city",
        "state", "postal_code", "country"
    },
    "employee_projects": {
        "project_id", "employee_id", "project_name", "role",
        "start_date", "end_date"
    }
}


def validate_sql(sql: str):
    """Basic validation to catch hallucinated IDs/columns."""
    errors = []

    # crude check
    if " ea.id " in sql.lower():
        errors.append("employee_addresses has no column 'id', use employee_id")

    return len(errors) == 0, errors
