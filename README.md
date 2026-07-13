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

