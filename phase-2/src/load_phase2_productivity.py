from pathlib import Path
import os

import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / " data"

def source_file(pattern):
    matches = list(DATA.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one file matching {pattern!r}; "
            f"found {len(matches)}"
        )
    return matches[0]

def read_csv(pattern):
    df = pd.read_csv(source_file(pattern), low_memory=False)
    df.columns = df.columns.str.strip()
    return df

def clean_text(value):
    if pd.isna(value):
        return None
    value = str(value).strip()
    return value or None

def clean_date(value):
    if pd.isna(value) or str(value).strip() == "":
        return None
    return pd.to_datetime(value, errors="raise").date()

def clean_int(value):
    if pd.isna(value) or str(value).strip() == "":
        return None
    return int(value)

def clean_number(value):
    if pd.isna(value) or str(value).strip() == "":
        return None
    return float(value)

def records(df, columns, converters):
    missing = set(columns) - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing expected columns: {sorted(missing)}")

    result = []
    for row in df[columns].to_dict("records"):
        result.append({
            col: converters.get(col, clean_text)(value)
            for col, value in row.items()
        })
    return result

def main():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set. Load .env first.")

    teams = read_csv("*dim_team.csv")
    sprints = read_csv("*dim_sprint.csv")
    tasks = read_csv("*fact_task.csv")

    if teams["team_id"].duplicated().any():
        raise RuntimeError("Duplicate team_id values in source.")
    if sprints["sprint_id"].duplicated().any():
        raise RuntimeError("Duplicate sprint_id values in source.")
    if tasks["task_id"].duplicated().any():
        raise RuntimeError("Duplicate task_id values in source.")

    valid_statuses = {"Done", "In Progress", "Blocked", "To Do", "Cancelled"}
    statuses = set(tasks["status"].dropna().astype(str).str.strip())
    if statuses - valid_statuses:
        raise RuntimeError(f"Unexpected task statuses: {statuses - valid_statuses}")

    team_ids = set(teams["team_id"].astype(str).str.strip())
    sprint_ids = set(sprints["sprint_id"].astype(str).str.strip())

    unknown_teams = set(tasks["team_id"].astype(str).str.strip()) - team_ids
    unknown_sprints = set(tasks["sprint_id"].astype(str).str.strip()) - sprint_ids
    if unknown_teams or unknown_sprints:
        raise RuntimeError(
            f"Unknown team IDs: {sorted(unknown_teams)[:10]}; "
            f"unknown sprint IDs: {sorted(unknown_sprints)[:10]}"
        )

    team_columns = [
        "team_id", "team_name", "department_id",
        "team_lead_employee_id", "active_members",
        "planning_cadence", "board_tool",
    ]
    sprint_columns = [
        "sprint_id", "sprint_name", "start_date",
        "end_date", "working_days", "financial_year",
    ]
    task_columns = [
        "task_id", "team_id", "sprint_id", "assignee_employee_id",
        "task_type", "priority", "story_points", "created_date",
        "started_date", "due_date", "completed_date", "status",
        "reopened_count", "cycle_time_days",
        "is_overdue_at_cutoff", "completed_on_time",
    ]

    team_rows = records(teams, team_columns, {
        "active_members": clean_int,
    })
    sprint_rows = records(sprints, sprint_columns, {
        "start_date": clean_date,
        "end_date": clean_date,
        "working_days": clean_int,
    })
    task_rows = records(tasks, task_columns, {
        "story_points": clean_number,
        "created_date": clean_date,
        "started_date": clean_date,
        "due_date": clean_date,
        "completed_date": clean_date,
        "reopened_count": clean_int,
        "cycle_time_days": clean_number,
    })

    invalid_cycle_time_count = 0
    for row in task_rows:
        if row["reopened_count"] is None or row["reopened_count"] < 0:
            raise RuntimeError("Task has missing or negative reopened_count.")

        # Keep the task, but exclude invalid cycle time from cycle-time metrics.
        if row["cycle_time_days"] is not None and row["cycle_time_days"] < 0:
            row["cycle_time_days"] = None
            invalid_cycle_time_count += 1

        for flag in ("is_overdue_at_cutoff", "completed_on_time"):
            value = row[flag]
            if value is not None and value not in {"Y", "N"}:
                raise RuntimeError(f"Unexpected {flag} value: {value!r}")

    engine = create_engine(url)

    with engine.begin() as conn:
        counts = conn.execute(text("""
            SELECT
              (SELECT COUNT(*) FROM dw.dim_team),
              (SELECT COUNT(*) FROM dw.dim_sprint),
              (SELECT COUNT(*) FROM dw.fact_task)
        """)).one()

        if any(counts):
            raise RuntimeError(
                "At least one target table already contains data "
                f"(dim_team={counts[0]}, dim_sprint={counts[1]}, "
                f"fact_task={counts[2]}). Stopping without inserting."
            )

        conn.execute(text("""
            INSERT INTO dw.dim_team (
                team_id, team_name, department_id, team_lead_employee_id,
                active_members, planning_cadence, board_tool
            ) VALUES (
                :team_id, :team_name, :department_id, :team_lead_employee_id,
                :active_members, :planning_cadence, :board_tool
            )
        """), team_rows)

        conn.execute(text("""
            INSERT INTO dw.dim_sprint (
                sprint_id, sprint_name, start_date, end_date,
                working_days, financial_year
            ) VALUES (
                :sprint_id, :sprint_name, :start_date, :end_date,
                :working_days, :financial_year
            )
        """), sprint_rows)

        insert_task = text("""
            INSERT INTO dw.fact_task (
                task_id, team_id, sprint_id, assignee_employee_id,
                task_type, priority, story_points, created_date,
                started_date, due_date, completed_date, status,
                reopened_count, cycle_time_days,
                is_overdue_at_cutoff, completed_on_time
            ) VALUES (
                :task_id, :team_id, :sprint_id, :assignee_employee_id,
                :task_type, :priority, :story_points, :created_date,
                :started_date, :due_date, :completed_date, :status,
                :reopened_count, :cycle_time_days,
                :is_overdue_at_cutoff, :completed_on_time
            )
        """)

        batch_size = 2000
        for start in range(0, len(task_rows), batch_size):
            conn.execute(insert_task, task_rows[start:start + batch_size])

    print("Productivity data loaded successfully.")
    print(f"Teams loaded: {len(team_rows)}")
    print(f"Sprints loaded: {len(sprint_rows)}")
    print(f"Tasks loaded: {len(task_rows)}")
    print(f"Invalid cycle-time values set to NULL: {invalid_cycle_time_count}")

    engine.dispose()

if __name__ == "__main__":
    main()
