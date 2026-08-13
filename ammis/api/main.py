from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

from ammis.models.probabilities import ModelVote, ConfidenceResult
from ammis.engines.market_math.aggregator import aggregate_votes
from ammis.core import db as dbcore

# optional Prometheus metrics
try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

    REQ_COUNTER = Counter("ammis_requests_total", "Total HTTP requests", ["path", "method"])
    REQ_LATENCY = Histogram("ammis_request_latency_seconds", "Request latency", ["path"])
    METRICS_ENABLED = True
except Exception:
    REQ_COUNTER = None
    REQ_LATENCY = None
    METRICS_ENABLED = False


app = FastAPI(title="AMMIS API", version="0.1.0")


class IngestRequest(BaseModel):
    symbol: str
    data: List[Dict]  # list of OHLCV-like dicts; placeholder


class ComputeRequest(BaseModel):
    symbol: str
    models: List[str] = ["mock_model"]
    threshold: float = 80.0


@app.on_event("startup")
def startup_event():
    app.state.data_store = {}
    # Optionally run DB migrations at startup when environment requests it.
    import os

    run_mig = os.getenv("AMMIS_RUN_MIGRATIONS", "0")
    if run_mig == "1":
        try:
            from ammis.core.db_migrate import run_migrations

            # run migrations synchronously on startup
            run_migrations()
        except Exception as exc:
            # log but don't crash the app startup — user can inspect logs
            print(f"DB migration failed or skipped: {exc}")


# allow CORS during development so the frontend can call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request, call_next):
    path = request.url.path
    method = request.method
    if METRICS_ENABLED:
        REQ_COUNTER.labels(path=path, method=method).inc()
        with REQ_LATENCY.labels(path=path).time():
            response = await call_next(request)
    else:
        response = await call_next(request)
    return response


@app.get("/health")
def health() -> dict:
    # report migrations status using DB-based migration table when possible
    try:
        migrations_applied = dbcore.migrations_applied()
    except Exception:
        migrations_applied = False
    return {"status": "ok", "migrations_applied": migrations_applied}


@app.get("/metrics")
def metrics() -> Response:
    if not METRICS_ENABLED:
        raise HTTPException(status_code=501, detail="prometheus_client not installed")
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.get("/")
def ui_root():
    # serve a small static page for quick browser testing
    from pathlib import Path

    p = Path(__file__).resolve().parent / "static" / "index.html"
    if not p.exists():
        raise HTTPException(status_code=404, detail="UI not found")
    return Response(content=p.read_text(), media_type="text/html")


@app.post("/ingest")
def ingest(req: IngestRequest) -> dict:
    # Basic in-memory ingest placeholder
    app.state.data_store[req.symbol] = req.data
    # attempt to persist to DB; fall back to in-memory storage inside db helper
    try:
        rows_written = dbcore.save_candles(req.symbol, req.data)
    except Exception:
        rows_written = 0
    return {"symbol": req.symbol, "rows": len(req.data), "db_rows": rows_written}


@app.post("/compute_probabilities")
def compute_probabilities(req: ComputeRequest) -> ConfidenceResult:
    # Mock model votes: each model returns a random-ish vote based on symbol hash
    votes: List[ModelVote] = []
    # deterministic pseudo-randomness for reproducibility in this stub
    base = sum(ord(c) for c in req.symbol) % 100
    for i, m in enumerate(req.models):
        # simple heuristic: alternate buy/sell/hold
        action = ["BUY", "SELL", "HOLD"][i % 3]
        confidence = float((base + i * 7) % 100)
        votes.append(ModelVote(model=m, action=action, confidence=confidence))

    result = aggregate_votes(votes, threshold=req.threshold)
    return result

