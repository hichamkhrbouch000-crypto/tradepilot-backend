import numpy as np
import pandas as pd
import requests
from .cache import get_cache, set_cache, fallback_from_db

def fetch_live_market_data(coin_id="bitcoin", timeframe="1d"):
    """
    جلب البيانات ديناميكياً وتحديد حجم البيانات بناءً على وقت الشمعة
    """
    try:
        if timeframe in ["1m", "5m", "15m", "30m"]:
            days = "1"      
        elif timeframe in ["1h", "4h"]:
            days = "7"      
        else:
            days = "30"     
            
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            prices = [item[1] for item in data["prices"]]
            
            if timeframe == "1m" and len(prices) > 20: return prices[-20:]
            if timeframe == "5m" and len(prices) > 50: return prices[-50:]
            if timeframe == "15m" and len(prices) > 100: return prices[-100:]
            if timeframe == "30m" and len(prices) > 150: return prices[-150:]
            if timeframe == "1h" and len(prices) > 168: return prices[-168:]
            if timeframe == "4h" and len(prices) > 42: return prices[-42:]
            
            return prices
        return None
    except Exception:
        return None

def calculate_indicators(prices):
    if len(prices) < 26:
        return 50.0, 0.0, "NEUTRAL"
    
    df = pd.DataFrame(prices, columns=["price"])
    
    # حساب الـ RSI
    delta = df["price"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-10)
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # حساب الـ MACD
    df['ema12'] = df['price'].ewm(span=12, adjust=False).mean()
    df['ema26'] = df['price'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    latest_rsi = df['rsi'].iloc[-1]
    latest_macd = df['macd'].iloc[-1]
    latest_signal = df['signal'].iloc[-1]
    
    if latest_rsi <= 35 and latest_macd > latest_signal:
        decision = "BUY"
    elif latest_rsi >= 65 and latest_macd < latest_signal:
        decision = "SELL"
    elif 35 < latest_rsi < 45:
        decision = "ACCUMULATE"
    else:
        decision = "HOLD"
        
    return float(latest_rsi), float(latest_macd - latest_signal), decision

def generate_trading_decision(coin_id="bitcoin", timeframe="1d"):
    cache_key = f"technical_metrics_{coin_id}_{timeframe}"
    prices = fetch_live_market_data(coin_id, timeframe)
    
    if prices is None:
        return fallback_from_db(cache_key) or {
            "asset": coin_id.upper(), "current_price": 0, "rsi": 50,
            "decision": "HOLD", "confidence": "NEUTRAL", "market_trend": "مستقر"
        }

    current_price = prices[-1]
    rsi_value, macd_diff, decision = calculate_indicators(prices)

    confidence = f"HIGH ({timeframe.upper()} Frame Match)" if decision in ["BUY", "SELL"] else f"MEDIUM ({timeframe.upper()} Scan)"

    if rsi_value > 55:
        market_trend = "صعودي (Bullish)"
    elif rsi_value < 45:
        market_trend = "هبوطي (Bearish)"
    else:
        market_trend = "مستقر/عرضي (Sideways)"

    metrics = {
        "asset": coin_id.upper(),
        "current_price": round(current_price, 2),
        "rsi": round(rsi_value, 2),
        "decision": decision,
        "confidence": confidence,
        "market_trend": market_trend
    }
    expire_time = 30 if timeframe in ["1m", "5m", "15m"] else 300
    set_cache(cache_key, metrics, expire=expire_time)
    return metrics
