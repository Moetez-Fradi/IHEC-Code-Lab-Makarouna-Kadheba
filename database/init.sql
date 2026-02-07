-- Initialize TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create hypertable for historical_prices (after table creation)
-- This will be executed by SQLAlchemy migration
-- SELECT create_hypertable('historical_prices', 'date', if_not_exists => TRUE);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_historical_prices_stock_date ON historical_prices(stock_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_sentiments_stock_date ON sentiments(stock_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_anomalies_detected_at ON anomalies(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_stock_target_date ON predictions(stock_id, target_date);
