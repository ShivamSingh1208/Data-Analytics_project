ROLE_METRICS = {
    "ADMIN": (
        "Headcount", "Attendance", "Attrition",
        "Employer cost", "Overtime", "Task completion",
    ),
    "HR": (
        "Headcount", "Attendance", "Attrition", "Task completion",
    ),
    "MANAGER": (
        "Headcount", "Attendance", "Task completion",
    ),
    "EXECUTIVE": (
        "Headcount", "Attendance", "Attrition",
        "Employer cost", "Overtime", "Task completion",
    ),
}

METRIC_COLUMNS = {
    "Headcount": ("headcount_end", 5, "Employees"),
    "Attendance": ("attendance_rate_pct", 5, "%"),
    "Attrition": ("attrition_rate_pct", 10, "%"),
    "Employer cost": ("employer_cost", 5, "Currency"),
    "Overtime": ("overtime_share_pct", 5, "%"),
    "Task completion": ("task_completion_pct", 5, "%"),
}


def get_allowed_metrics(role):
    if not isinstance(role, str) or not role.strip():
        raise ValueError("Unsupported role.")

    normalized = role.strip().upper()
    if normalized not in ROLE_METRICS:
        raise ValueError("Unsupported role.")
    return ROLE_METRICS[normalized]
