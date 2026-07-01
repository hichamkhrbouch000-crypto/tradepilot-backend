import numpy as np
import pandas as pd
import requests
from .cache import get_cache, set_cache, fallback_from_db

def fetch_live_market_data(coin_id="bitcoin"):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=30"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            prices = [item[1] for item in data["prices"]]
            return prices
        return None
    except Exception:
        return None

def calculate_indicators(prices):
    if len(prices) < 26:
        return 50.0, 0.0, "NEUTRAL"
    
    df = pd.DataFrame(prices, columns=["price"])
    
    # 1. حساب الـ RSI
    delta = df["price"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-10)
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # 2. حساب الـ MACD لمعرفة زخم الحيتان
    df['ema12'] = df['price'].ewm(span=12, adjust=False).mean()
    df['ema26'] = df['price'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    latest_rsi = df['rsi'].iloc[-1]
    latest_macd = df['macd'].iloc[-1]
    latest_signal = df['signal'].iloc[-1]
    
    # استراتيجية مدمجة لاتخاذ قرار قوي
    if latest_rsi <= 35 and latest_macd > latest_signal:
        decision = "BUY"
    elif latest_rsi >= 65 and latest_macd < latest_signal:
        decision = "SELL"
    elif 35 < latest_rsi < 45:
        decision = "ACCUMULATE"
    else:
        decision = "HOLD"
        
    return float(latest_rsi), float(latest_macd - latest_signal), decision

def generate_trading_decision(coin_id="bitcoin"):
    cache_key = f"technical_metrics_{coin_id}"
    prices = fetch_live_market_data(coin_id)
    
    if prices is None:
        return fallback_from_db(cache_key) or {
            "asset": coin_id.upper(), "current_price": 0, "rsi": 50,
            "decision": "HOLD", "confidence": "NEUTRAL", "market_trend": "مستقر"
        }

    current_price = prices[-1]
    rsi_value, macd_diff, decision = calculate_indicators(prices)

    if decision in ["BUY", "SELL"]:
        confidence = "HIGH (Whale Entry Confirmation)"
    else:
        confidence = "MEDIUM (Market Scanning)"

    if rsi_value > 55:
        market_trend = "صعودي (Bullish Trend)"
    elif rsi_value < 45:
        market_trend = "هبوطي (Bearish Trend)"
    else:
        market_trend = "مستقر وعرضي (Sideways)"

    metrics = {
        "asset": coin_id.upper(),
        "current_price": round(current_price, 2),
        "rsi": round(rsi_value, 2),
        "decision": decision,
        "confidence": confidence,
        "market_trend": market_trend
    }
    set_cache(cache_key, metrics, expire=300)
    return metrics
