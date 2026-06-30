import requests
import pandas as pd
from datetime import datetime
from config import BINANCE_API_URL, SYMBOL, KLINE_COLUMNS
from cache import get_cache, set_cache, fallback_from_db
import logging

logger = logging.getLogger(__name__)

INTERVAL_MAP = {
    "15m": "15m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d"
}

def fetch_klines(interval: str, limit: int = 200) -> pd.DataFrame:
    params = {
        "symbol": SYMBOL,
        "interval": interval,
        "limit": limit
    }
    try:
        resp = requests.get(BINANCE_API_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        df = pd.DataFrame(data, columns=KLINE_COLUMNS)
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col])
        return df
    except Exception as e:
        logger.error(f"فشل جلب {interval}: {e}")
        return pd.DataFrame()

def get_price_data() -> dict:
    cache_key = "price_data"
    cached = get_cache(cache_key)
    if cached:
        return cached

    data = {}
    success = True
    for tf, interval in INTERVAL_MAP.items():
        df = fetch_klines(interval)
        if not df.empty:
            data[tf] = df.to_dict(orient="records")
        else:
            success = False
            break

    if success:
        set_cache(cache_key, data, ttl=300)
        return data
    else:
        fallback = fallback_from_db(cache_key)
        if fallback:
            return fallback
        else:
            raise RuntimeError("لا توجد بيانات سوق متاحة حالياً")

