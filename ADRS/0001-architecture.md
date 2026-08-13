Title: Architecture overview and rationale
Date: 2026-08-13
Status: proposed

Decision: Use modular layered architecture with probability outputs and a confidence aggregator.

Context:
- AMMIS aims to separate forecasting (probability generation) from risk and execution.
- Reuse of Kronos tokenizer and predictor is beneficial for probabilistic market forecasts.

Consequences:
- Easier testing of individual components.
- Allows multiple model votes to be aggregated and calibrated before executing trades.
