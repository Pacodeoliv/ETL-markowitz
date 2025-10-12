from datetime import datetime

# --- Configurações Gerais ---
TICKERS = [
    "AAPL", "MSFT", "JPM", "PG", "XOM",
    "MGLU3.SA", "PETR4.SA"
]
START_DATE = "2020-01-01"
END_DATE = datetime.now().strftime('%Y-%m-%d')

# --- Configurações do Azure ---
RAW_CONTAINER_NAME = "raw"
PROCESSED_CONTAINER_NAME = "processed"
RAW_BLOB_NAME = "raw_stock_prices.parquet"
WEIGHTS_BLOB_NAME = "optimized_weights.parquet"
PERFORMANCE_BLOB_NAME = "portfolio_performance.parquet"