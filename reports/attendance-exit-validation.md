# Attendance Exit-Month Validation

## Result
PASS — no attendance-after-exit-month violations were found in the cleaned attendance dataset.

- Clean attendance rows checked: 7,339
- Violations found: 0
- Rejected attendance rows in the ETL report: 4
- Rejection reason: attendance month ends after employee exit month

## Method
The cleaned attendance data was joined to employee exit dates using employee_id. The attendance period-end month was compared with the employee exit month. Rows with an attendance month later than the exit month were counted as violations.

## Limitation
This validates the month-based rule only. It does not independently verify every attendance field or establish why the original records were present.
