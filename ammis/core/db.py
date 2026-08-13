"""Lightweight DB helper for AMMIS.

Provides a small API to persist ingested candle data into Postgres/TimescaleDB
if `psycopg` is installed and connection info is provided via env vars.

This module is defensive: if DB client isn't available or connection fails,
methods fall back to in-memory storage so the rest of the system remains usable
for demos and local testing.
"""
from __future__ import annotations

import os
from typing import List, Dict, Any

try:
    import psycopg
except Exception:
    psycopg = None


class DBClient:
    def __init__(self):
        self._conn = None
        self.in_memory: Dict[str, List[Dict[str, Any]]] = {}

    def connect(self):
        if psycopg is None:
            return False
        try:
            self._conn = psycopg.connect(
                host=os.getenv("AMMIS_DB_HOST", "localhost"),
                port=int(os.getenv("AMMIS_DB_PORT", "5432")),
                dbname=os.getenv("AMMIS_DB_NAME", "ammis"),
                user=os.getenv("AMMIS_DB_USER", "postgres"),
                password=os.getenv("AMMIS_DB_PASSWORD", "postgres"),
            )
            self._conn.autocommit = True
            return True
        except Exception:
            self._conn = None
            return False

    def save_candles(self, symbol: str, rows: List[Dict[str, Any]]) -> int:
        """Save a list of candle dicts to market_candles table. Returns rows inserted or stored in-memory."""
        if self._conn is None:
            ok = self.connect()
            if not ok:
                # store in-memory
                self.in_memory.setdefault(symbol, []).extend(rows)
                return len(rows)

        # write to DB using psycopg execute many
        cols = ["time", "symbol", "open", "high", "low", "close", "volume"]
        with self._conn.cursor() as cur:
            args_str = ",".join(["(%s,%s,%s,%s,%s,%s,%s)" for _ in rows])
            flat = []
            for r in rows:
                flat.append(r.get("time"))
                flat.append(symbol)
                flat.append(r.get("open"))
                flat.append(r.get("high"))
                flat.append(r.get("low"))
                flat.append(r.get("close"))
                flat.append(r.get("volume", 0))
            sql = f"INSERT INTO market_candles (time, symbol, open, high, low, close, volume) VALUES {args_str} ON CONFLICT DO NOTHING"
            try:
                cur.execute(sql, tuple(flat))
                return len(rows)
            except Exception:
                # fallback to in-memory
                self.in_memory.setdefault(symbol, []).extend(rows)
                return len(rows)

    def save_model_scores(self, scores: Dict[str, float]) -> bool:
        """Persist per-model EMA loss scores. Returns True on success.

        If DB is available, upsert into `ammis_model_weights`. Otherwise write
        a fallback JSON file in the repo root: `.ammis_model_weights.json`.
        """
        import json
        from pathlib import Path

        if self._conn is None:
            if not self.connect():
                # fallback to file
                try:
                    p = Path(__file__).resolve().parents[2] / ".ammis_model_weights.json"
                    p.write_text(json.dumps(scores))
                    return True
                except Exception:
                    return False

        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ammis_model_weights (
                        model TEXT PRIMARY KEY,
                        ema_loss DOUBLE PRECISION,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
                    )
                    """
                )
                for model, loss in scores.items():
                    cur.execute(
                        "INSERT INTO ammis_model_weights (model, ema_loss) VALUES (%s, %s) ON CONFLICT (model) DO UPDATE SET ema_loss = EXCLUDED.ema_loss, updated_at = now()",
                        (model, float(loss)),
                    )
            return True
        except Exception:
            try:
                p = Path(__file__).resolve().parents[2] / ".ammis_model_weights.json"
                p.write_text(json.dumps(scores))
                return True
            except Exception:
                return False

    def load_model_scores(self) -> Dict[str, float]:
        """Load persisted model EMA loss scores from DB or fallback file."""
        import json
        from pathlib import Path

        if self._conn is None:
            if not self.connect():
                try:
                    p = Path(__file__).resolve().parents[2] / ".ammis_model_weights.json"
                    if p.exists():
                        return json.loads(p.read_text())
                    return {}
                except Exception:
                    return {}

        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "SELECT model, ema_loss FROM ammis_model_weights"
                )
                rows = cur.fetchall()
                return {r[0]: float(r[1]) for r in rows}
        except Exception:
            try:
                p = Path(__file__).resolve().parents[2] / ".ammis_model_weights.json"
                if p.exists():
                    return json.loads(p.read_text())
                return {}
            except Exception:
                return {}

        # write to DB using psycopg execute many
        cols = ["time", "symbol", "open", "high", "low", "close", "volume"]
        with self._conn.cursor() as cur:
            args_str = ",".join(["(%s,%s,%s,%s,%s,%s,%s)" for _ in rows])
            flat = []
            for r in rows:
                flat.append(r.get("time"))
                flat.append(symbol)
                flat.append(r.get("open"))
                flat.append(r.get("high"))
                flat.append(r.get("low"))
                flat.append(r.get("close"))
                flat.append(r.get("volume", 0))
            sql = f"INSERT INTO market_candles (time, symbol, open, high, low, close, volume) VALUES {args_str} ON CONFLICT DO NOTHING"
            try:
                cur.execute(sql, tuple(flat))
                return len(rows)
            except Exception:
                # fallback to in-memory
                self.in_memory.setdefault(symbol, []).extend(rows)
                return len(rows)


_db_client = DBClient()


def save_candles(symbol: str, rows: List[Dict[str, Any]]) -> int:
    return _db_client.save_candles(symbol, rows)


def connect() -> bool:
    return _db_client.connect()


def migrations_applied() -> bool:
    """Return True if the migrations table exists and has at least one entry.

    Falls back to checking the marker file if DB isn't available.
    """
    try:
        if psycopg is None:
            return False
        # ensure connection
        if _db_client._conn is None:
            if not _db_client.connect():
                # check marker file fallback
                from pathlib import Path

                marker = Path(__file__).resolve().parents[2] / ".ammis_migrations_applied"
                return marker.exists()

        with _db_client._conn.cursor() as cur:
            # check for table existence
            cur.execute("SELECT to_regclass('public.ammis_migrations')")
            tbl = cur.fetchone()[0]
            if not tbl:
                return False
            cur.execute("SELECT count(*) FROM ammis_migrations")
            cnt = cur.fetchone()[0]
            return cnt > 0
    except Exception:
        try:
            from pathlib import Path

            marker = Path(__file__).resolve().parents[2] / ".ammis_migrations_applied"
            return marker.exists()
        except Exception:
            return False
