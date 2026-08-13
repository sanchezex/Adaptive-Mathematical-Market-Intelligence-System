"""Database migration runner for AMMIS.

Applies SQL from `infrastructure/timescale_schema.sql` to the configured
Postgres/TimescaleDB instance. The runner will retry until the DB is ready
or a timeout is reached.

Configuration via environment variables:
- AMMIS_DB_HOST (default: localhost)
- AMMIS_DB_PORT (default: 5432)
- AMMIS_DB_NAME (default: ammis)
- AMMIS_DB_USER (default: postgres)
- AMMIS_DB_PASSWORD (default: postgres)
- AMMIS_DB_CONNECT_RETRIES (default: 30)
- AMMIS_DB_CONNECT_DELAY (seconds, default: 2)
"""
from __future__ import annotations

import os
import time
from pathlib import Path
import sqlparse
from typing import Optional

SQL_PATH = Path(__file__).resolve().parents[2] / "infrastructure" / "timescale_schema.sql"


def _get_conn_info() -> dict:
    return {
        "host": os.getenv("AMMIS_DB_HOST", "localhost"),
        "port": int(os.getenv("AMMIS_DB_PORT", "5432")),
        "dbname": os.getenv("AMMIS_DB_NAME", "ammis"),
        "user": os.getenv("AMMIS_DB_USER", "postgres"),
        "password": os.getenv("AMMIS_DB_PASSWORD", "postgres"),
    }


def apply_sql(conn, sql: str) -> None:
    # Use sqlparse to split into statements safely (handles semicolons in strings)
    try:
        stmts = [s.strip() for s in sqlparse.split(sql) if s.strip()]
    except Exception:
        # fallback to naive split
        stmts = [s.strip() for s in sql.split(";") if s.strip()]

    with conn.cursor() as cur:
        for s in stmts:
            cur.execute(s)


def run_migrations(retries: Optional[int] = None, delay: Optional[float] = None) -> None:
    conn_info = _get_conn_info()
    retries = int(retries or os.getenv("AMMIS_DB_CONNECT_RETRIES", "30"))
    delay = float(delay or os.getenv("AMMIS_DB_CONNECT_DELAY", "2"))

    try:
        import psycopg
    except Exception as e:
        raise RuntimeError("psycopg is required to run migrations. Install dependencies.") from e

    if not SQL_PATH.exists():
        raise FileNotFoundError(f"SQL schema file not found: {SQL_PATH}")

    sql = SQL_PATH.read_text()

    last_err = None
    for attempt in range(1, retries + 1):
        try:
            dsn = {
                "host": conn_info["host"],
                "port": conn_info["port"],
                "dbname": conn_info["dbname"],
                "user": conn_info["user"],
                "password": conn_info["password"],
            }
            conn = psycopg.connect(**dsn)
            conn.autocommit = True
            apply_sql(conn, sql)
            # create migrations table and record this migration
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS ammis_migrations (
                            id SERIAL PRIMARY KEY,
                            name TEXT NOT NULL,
                            applied_at TIMESTAMPTZ DEFAULT now()
                        )
                        """
                    )
                    cur.execute("INSERT INTO ammis_migrations (name) VALUES (%s)", (SQL_PATH.name,))
            except Exception:
                # If recording migration in DB fails, fall back to marker file for compatibility
                marker = Path(__file__).resolve().parents[2] / ".ammis_migrations_applied"
                try:
                    marker.write_text(f"applied\n")
                except Exception:
                    pass
            finally:
                conn.close()
            print("Migrations applied successfully")
            return
        except Exception as exc:
            last_err = exc
            print(f"Migration attempt {attempt}/{retries} failed: {exc}")
            time.sleep(delay)

    raise RuntimeError(f"Failed to apply migrations after {retries} attempts") from last_err


if __name__ == "__main__":
    run_migrations()
