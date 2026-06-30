import os

API_KEY = os.getenv("API_KEY", "tradepilot-mvp-key-123")
BINANCE_API_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "BTCUSDT"
TTL_PRICE = 300
TTL_TA = 300
TTL_DECISION = 300
DB_PATH = "cache.db"

KLINE_COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume",
    "close_time", "quote_asset_volume", "number_of_trades",
    "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
]
