# AMMIS - TODO

## 0. Confirm scope
- [x] Repo is empty; scaffold AMMIS from scratch.

## 1. Create core repository scaffold (Phase 0)
- [ ] Create Python backend package skeleton (FastAPI).
- [ ] Create project-level config (pyproject, requirements/lock strategy).
- [ ] Add database schema scaffolding (TimescaleDB hypertables placeholders).
- [ ] Add data models (pydantic) and interfaces.
- [ ] Add ML/math engine interfaces (probability outputs).
- [ ] Add basic calibration + confidence aggregator module.

## 2. Implement minimal runnable services (Phase 1)
- [ ] FastAPI app with endpoints:
  - upload/ingest placeholder
  - compute probabilities (mock)
  - health/status
- [ ] Stub risk engine + trade execution interface.

## 3. Add backtesting scaffold (Phase 2)
- [ ] Backtrader/vectorbt integration scaffolding.
- [ ] Basic historical replay runner producing PnL + confidence stats.

## 4. Add dashboard scaffold (Phase 3)
- [ ] React/TS app skeleton.
- [ ] Wire to backend endpoints.

## 5. DevOps scaffold (Phase 4)
- [ ] Docker compose for:
  - backend
  - postgres+timescaledb
  - redis
- [ ] Grafana/Prometheus placeholders.

## 6. Documentation
- [ ] README with architecture + run instructions.
- [ ] ADRs for design choices.

