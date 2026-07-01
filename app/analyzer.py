import numpy as np
import pandas as pd
import requests
from .cache import get_cache, set_cache, fallback_from_db

def fetch_live_market_data(coin_id="bitcoin"):
    """
    مجاناً CoinGecko API جلب بيانات الأسعار التاريخية والحالية لعملة معينة من
    """
    try:
        # ديناميكياً coin_id تم تعديل الرابط ليتغير حسب الـ
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=30"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            prices = [item[1] for item in data["prices"]]
            return prices
        return None
    except Exception:
        return None

def calculate_rsi(prices, period=14):
    if len(prices) < period:
        return 50.0
    df = pd.DataFrame(prices, columns=["price"])
    delta = df["price"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    latest_rsi = rsi.iloc[-1]
    return float(latest_rsi) if not np.isnan(latest_rsi) else 50.0

def analyze_technical_indicators(coin_id="bitcoin"):
    # الكاش يتغير اسمه حسب العملة لعدم اختلاط البيانات
    cache_key = f"technical_metrics_{coin_id}"
    cached_data = get_cache(cache_key)
    if cached_data:
        return cached_data

    prices = fetch_live_market_data(coin_id)
    if prices is None:
        return fallback_from_db(cache_key) or {
            "rsi": 55.0,
            "current_price": 0.0,
            "status": "fallback"
        }

    current_price = prices[-1]
    rsi_value = calculate_rsi(prices)

    metrics = {
        "rsi": round(rsi_value, 2),
        "current_price": round(current_price, 2),
        "status": "live"
    }
    set_cache(cache_key, metrics, expire=600)
    return metrics

def generate_trading_decision(coin_id="bitcoin"):
    try:
        indicators = analyze_technical_indicators(coin_id)
    except Exception:
        indicators = {"rsi": 50, "current_price": 0, "status": "error"}

    rsi = indicators.get("rsi", 50)
    current_price = indicators.get("current_price", 0)

    if rsi <= 30:
        decision = "BUY"
        confidence = "HIGH (Oversold)"
    elif rsi >= 70:
        decision = "SELL"
        confidence = "HIGH (Overbought)"
    elif 30 < rsi < 45:
        decision = "ACCUMULATE"
        confidence = "MEDIUM"
    elif 55 < rsi < 70:
        decision = "REDUCE"
        confidence = "MEDIUM"
    else:
        decision = "HOLD"
        confidence = "NEUTRAL"

    # تحديد اتجاه السوق بناءً على الـ RSI الحالي
    if rsi > 55:
        market_trend = "صعودي (Bullish)"
    elif rsi < 45:
        market_trend = "هبوطي (Bearish)"
    else:
        market_trend = "مستقر (Sideways)"

    return {
        "asset": coin_id.upper(),
        "current_price": current_price,
        "rsi": rsi,
        "decision": decision,
        "confidence": confidence,
        "market_trend": market_trend
    }
