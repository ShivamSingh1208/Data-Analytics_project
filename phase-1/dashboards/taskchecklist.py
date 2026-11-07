
from pathlib import Path
import json
import sqlite3
import subprocess

root = Path.cwd()

def check_file(path):
    return (root / path).exists()

def docker_check(*args):
    result = subprocess.run(
        ["docker", "compose", *args],
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stdout.strip() or result.stderr.strip()

checks = [
    ("ETL pipeline code", check_file("src/etl_pipeline.py")),
    ("SQL schema", check_file("sql/schema.sql")),
    ("ETL quality report", check_file("logs/etl_quality_report.json")),
    ("Dashboard directory", check_file("dashboards")),
    ("Documentation directory", check_file("docs")),
    ("Superset metadata backup", check_file("superset_metadata_backup.db")),
    ("Superset home backup", check_file("superset_home_backup.tar.gz")),
]

print("\n=== PULSEIQ PROJECT CHECKLIST ===")
for name, passed in checks:
    print(f"[{'PASS' if passed else 'CHECK'}] {name}")

report_path = root / "logs/etl_quality_report.json"
if report_path.exists():
    try:
        report = json.loads(report_path.read_text())
        print("\n=== ETL REPORT ===")
        print(json.dumps(report, indent=2))
    except Exception as exc:
        print("Could not parse ETL report:", exc)

print("\n=== DOCKER SERVICES ===")
ok, output = docker_check("ps", "-a")
print(output)

backup = root / "superset_metadata_backup.db"
if backup.exists():
    print("\n=== SUPERSET BACKUP COUNTS ===")
    con = sqlite3.connect(backup)
    for table in ("dashboards", "slices", "dbs"):
        try:
            count = con.execute(
                f'SELECT COUNT(*) FROM "{table}"'
            ).fetchone()[0]
            print(f"{table}: {count}")
        except sqlite3.Error as exc:
            print(f"{table}: unable to check ({exc})")
    con.close()

print("\nNote: File existence alone does not prove a task is complete.")
print("Superset is complete only after it starts and its dashboards load.")
