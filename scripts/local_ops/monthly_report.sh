#!/bin/zsh
set -euo pipefail
umask 077

PROJECT="/Users/shivamsingh1208/ Python/pulseiq"
PYTHON="$PROJECT/.report-venv/bin/python3"

cd "$PROJECT"

set -a
source "$PROJECT/.env.phase4.local"
set +a

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is missing."
  exit 1
fi

REPORT_MONTH="${REPORT_MONTH:-$(date -v-1m +%Y-%m)}"

CHECK_RESULT=$("$PYTHON" - "$REPORT_MONTH" <<'PY'
import sys
from datetime import date
from sqlalchemy import create_engine, text
import os

month = sys.argv[1]
try:
    start = date.fromisoformat(month + "-01")
except ValueError:
    raise SystemExit("Invalid report month. Expected YYYY-MM.")

if len(month) != 7:
    raise SystemExit("Invalid report month. Expected YYYY-MM.")

end = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)

try:
    with engine.connect() as connection:
        count = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM dw.metric_pnl_monthly
                WHERE month_start >= :start
                  AND month_start < :end
            """),
            {"start": start, "end": end}
        ).scalar_one()
finally:
    engine.dispose()

if count == 0:
    print("NO_DATA")
else:
    print("DATA_AVAILABLE")
PY
)

if [[ "$CHECK_RESULT" == "NO_DATA" ]]; then
  echo "[$(date)] SKIPPED: no P&L data for $REPORT_MONTH."
  echo "No empty monthly reports were generated."
  exit 0
fi

if [[ "$CHECK_RESULT" != "DATA_AVAILABLE" ]]; then
  echo "Unexpected monthly data-check result."
  exit 1
fi

echo "[$(date)] Generating PulseIQ report for $REPORT_MONTH."

"$PYTHON" phase4/build_report.py \
  --month "$REPORT_MONTH" \
  --format both \
  --output-dir reports/monthly

PDF="reports/monthly/PulseIQ_Monthly_Report_${REPORT_MONTH}.pdf"
XLSX="reports/monthly/PulseIQ_Monthly_Report_${REPORT_MONTH}.xlsx"

test -s "$PDF"
test -s "$XLSX"

chmod 600 "$PDF" "$XLSX"

echo "[$(date)] PDF and Excel reports verified."
ls -lh "$PDF" "$XLSX"
echo "[$(date)] Monthly report job completed."
