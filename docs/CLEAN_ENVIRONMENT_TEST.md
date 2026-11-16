# PulseIQ — Clean Python Environment Test

Review date: 16 November 2026

## Purpose

Validate that the pinned Python dependency set can be installed into
a separate Python environment and that the project's automated tests
and Python compilation checks work without relying on the existing
`.report-venv` environment.

## Environment

- Python: 3.12
- Separate environment: `/tmp/pulseiq-clean-env`
- Dependencies: `requirements-lock.txt`
- Dependency lock: 73 pinned package entries

## Results

| Check | Result |
|---|---|
| Install pinned dependencies | Passed |
| Full automated test suite | 45 passed |
| Python compilation | Passed |
| Monthly report builder help command | Passed |

## Scope limitation

This test validates the Python dependency environment and automated
test suite. It does not prove that a completely new machine can
recreate the populated PostgreSQL warehouse, Superset dashboards,
Docker volumes, macOS LaunchAgents, or original source datasets.

The PostgreSQL backup and restore procedure and scheduled local jobs
were tested separately on the existing Mac environment. They have
not been independently recreated on a clean machine.

## Release status

Clean Python environment validation passed.

Full clean-machine operations validation remains outstanding.
