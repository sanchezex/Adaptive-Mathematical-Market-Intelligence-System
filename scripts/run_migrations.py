#!/usr/bin/env python3
"""CLI entry to run DB migrations for AMMIS.

This script prefers Alembic if available; otherwise falls back to the
legacy SQL runner which uses `infrastructure/timescale_schema.sql` and
records into `ammis_migrations`.
"""
import sys
from pathlib import Path

try:
    # if alembic is installed, use our alembic runner
    from ammis.scripts.alembic_runner import main as alembic_runner
except Exception:
    alembic_runner = None

if alembic_runner:
    if __name__ == '__main__':
        alembic_runner(sys.argv[1:] if len(sys.argv) > 1 else ['upgrade', 'head'])
else:
    try:
        import sqlparse
    except Exception:
        print("Missing dependency: 'sqlparse'. Install project requirements:")
        print("  python3 -m pip install -r requirements.txt")
        sys.exit(2)

    from ammis.core.db_migrate import run_migrations

    def main():
        script = Path(__file__).resolve().parents[1] / "infrastructure" / "timescale_schema.sql"
        sql_text = script.read_text(encoding="utf-8")
        stmts = [s.strip() for s in sqlparse.split(sql_text) if s.strip()]
        run_migrations(stmts)

    if __name__ == '__main__':
        main()
