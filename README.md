# Adaptive Mathematical Market Intelligence System (AMMIS)

AMMIS replaces the standalone trading bot with a **multi-layer decision engine** that outputs **probabilities** (not direct buy/sell signals) and then applies **risk-aware execution**.

## Architecture (high level)
1. **Market Data Engine** (multi-timeframe candles, global session features, event proximity)
2. **Mathematics Engine** (chaos, fractals, wave analysis, Fourier/wavelets, HMM regimes, Bayesian updates, Monte Carlo, information theory)
3. **Classical Feature Strategies** (trend, breakout, mean reversion, structure, liquidity zones) — as features/probability votes
4. **AI/ML Layer** (classify market type/regime and quantify uncertainty)
5. **Confidence Engine** (calibrated weighted probability aggregation; thresholded action)
6. **Risk Engine** (limits, fractional Kelly, volatility-adjusted sizing/stops, drawdown/exposure constraints)
7. **Self-learning** (post-trade evaluation; update model weights)
8. **Execution Layer** (broker API abstraction; paper trading first)

## Repo status
This repository was empty; it is now scaffolded from scratch in a phase-driven approach.

## Next steps
See `TODO.md`.

## Borrowing from Kronos

Kronos (https://github.com/shiyu-coder/Kronos) provides several features you can re-use in AMMIS:

- **Tokenizer / Quantizer**: Kronos converts continuous OHLCV K-line data into hierarchical discrete tokens. You can borrow the tokenizer code or use the pretrained tokenizer to discretize inputs before feeding them to downstream models.
- **Predictor wrapper**: Kronos exposes a `KronosPredictor` that bundles preprocessing, normalization, sampling (`T`, `top_p`, `sample_count`) and postprocessing. Wrapping that into an adapter reduces integration work.
- **Batch prediction utilities**: Use `predict_batch` for efficient parallel forecasting of multiple series.
- **Finetuning scripts**: The `finetune/` folder contains end-to-end examples for adapting the tokenizer and predictor to your own dataset.
- **Backtesting examples**: Kronos provides simple backtesting pipelines and visualization scripts you can adapt for AMMIS's backtest scaffolding.

Quick example (adapter pattern): see `ammis/engines/kronos_adapter.py` for a minimal adapter that loads Kronos when available and falls back to a mock predictor.

How to integrate quickly:

1. Install Kronos dependencies (see Kronos `requirements.txt`) or pip-install from the GitHub repo.
2. Create an adapter (like `ammis.engines.kronos_adapter.KronosAdapter`).
3. Use the adapter in your model-serving path: pull data from the ingest store, call `predict()` or `predict_batch()`, then convert forecasts into probability votes for the AMMIS aggregator.

Example code snippet:

```python
from ammis.engines.kronos_adapter import KronosAdapter
adapter = KronosAdapter()
adapter.load(model_name="NeoQuasar/Kronos-small")
pred_df = adapter.predict(df=my_ohlcv_df, pred_len=120)
```

When borrowing code from Kronos, respect the MIT license and keep attribution in your repo.

### Installing Kronos for real predictions

To use the real Kronos predictor (not the mock), install Kronos into your Python environment. Example (recommended: inside the project's venv):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# install Kronos from GitHub
bash scripts/install_kronos.sh
```

After installation, in your Python code:

```python
from ammis.engines.kronos_adapter import KronosAdapter
adapter = KronosAdapter()
adapter.load(model_name="NeoQuasar/Kronos-small")
pred_df = adapter.predict(df=my_ohlcv_df, pred_len=120)
```

Frontend dev (Vite)

```bash
cd frontend
npm install
npm run dev
```

If Vite runs on a different port, either configure a proxy in `vite.config.ts` or allow CORS as above.

DB migrations

The project includes an automated migration runner that applies `infrastructure/timescale_schema.sql`.

- To run migrations manually (after activating your venv):

```bash
python3 scripts/run_migrations.py
```

- When running with Docker Compose the backend service is configured to run migrations automatically before starting if `AMMIS_RUN_MIGRATIONS` is set to `1` (this is already set in the provided `docker-compose.yml`).


## Running locally with Docker Compose (example)

Start all services (backend, TimescaleDB, Redis, Prometheus, Grafana):

```bash
docker compose up --build
```

After the stack starts:
- Backend: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

Disable automatic migrations with Compose override

If you want to disable automatic migrations when using Docker Compose, use the provided override file which sets `AMMIS_RUN_MIGRATIONS=0`:

```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml up --build
```




