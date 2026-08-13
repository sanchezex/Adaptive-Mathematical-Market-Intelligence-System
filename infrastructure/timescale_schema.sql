-- TimescaleDB schema placeholders for AMMIS
-- Create a sample hypertable for OHLCV candles

CREATE TABLE IF NOT EXISTS market_candles (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    PRIMARY KEY (time, symbol)
);

SELECT create_hypertable('market_candles', 'time', if_not_exists => TRUE);
