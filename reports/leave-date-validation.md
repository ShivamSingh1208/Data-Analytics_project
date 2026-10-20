# Leave-Date Validation Findings

## Current ETL result
PASS — the current cleaned leave dataset contains no reversed date ranges.

- Cleaned leave rows: 3,439
- Rejected leave rows with reversed dates: 2
- Reversed date ranges remaining in cleaned output: 0
- Rule: `start_date` must be less than or equal to `end_date`.

## Source-data findings

| Leave request | Employee | Start date | End date | Status |
|---|---|---|---|---|
| LR-000025 | EMP-0006 | 2026-02-20 | 2026-02-19 | Rejected |
| LR-002286 | EMP-0489 | 2026-03-24 | 2026-03-23 | Approved |

Both reversed date ranges are present in the rejected output, with the reason `start_date is after end_date`. These records originated in the source data; the ETL preserves them in the rejected output rather than silently correcting them.

## Recommended follow-up
- Ask the data owner to confirm the authoritative dates for both requests.
- Prioritize the request marked Approved because its date range is invalid.
- Keep the source records unchanged until corrections are authorized.

## Limitation
This check validates date ordering only. It does not establish whether the leave statuses or dates are otherwise correct.
