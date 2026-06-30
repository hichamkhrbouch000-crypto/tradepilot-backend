import pandas as pd
import numpy as np
import ta
from cache import get_cache, set_cache, fallback_from_db
from data_collector import get_price_data
import logging

logger = logging.getLogger(__name__)

def calculate_indicators(df_records: list) -> pd.DataFrame:
    df = pd.DataFrame(df_records)
    if df.empty or len(df) < 30:
        return pd.DataFrame()
    
    # حساب المؤشرات الفنية الأساسية
    df["rsi"] = ta.momentum.rsi(df["close"], window=14)
    macd = ta.trend.MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    
    bollinger = ta.volatility.BollingerBands(df["close"], window=20, window_dev=2)
    df["bb_high"] = bollinger.bollinger_hband()
    df["bb_low"] = bollinger.bollinger_lband()
    
    df["ema_50"] = ta.trend.ema_indicator(df["close"], window=50)
    df["ema_200"] = ta.trend.ema_indicator(df["close"], window=200)
    
    return df

def analyze_technical_indicators() -> dict:
    cache_key = "ta_analysis"
    cached = get_cache(cache_key)
    if cached:
        return cached

    market_data = get_price_data()
    analysis_results = {}
    
    for tf, records in market_data.items():
        df_analyzed = calculate_indicators(records)
        if not df_analyzed.empty:
            last_row = df_analyzed.iloc[-1]
            analysis_results[tf] = {
                "close": float(last_row["close"]),
                "rsi": float(last_row["rsi"]) if not np.isnan(last_row["rsi"]) else 50.0,
                "macd": float(last_row["macd"]) if not np.isnan(last_row["macd"]) else 0.0,
                "macd_signal": float(last_row["macd_signal"]) if not np.isnan(last_row["macd_signal"]) else 0.0,
                "bb_high": float(last_row["bb_high"]) if not np.isnan(last_row["bb_high"]) else float(last_row["close"]),
                "bb_low": float(last_row["bb_low"]) if not np.isnan(last_row["bb_low"]) else float(last_row["close"]),
                "ema_50": float(last_row["ema_50"]) if not np.isnan(last_row["ema_50"]) else float(last_row["close"]),
                "ema_200": float(last_row["ema_200"]) if not np.isnan(last_row["ema_200"]) else float(last_row["close"]),
            }
            
    if analysis_results:
        set_cache(cache_key, analysis_results, ttl=300)
        return analysis_results
    else:
        fallback = fallback_from_db(cache_key)
        if fallback:
            return fallback
        raise RuntimeError("فشل معالجة التحليل الفني")

def generate_trading_decision() -> dict:
    cache_key = "trading_decision"
    cached = get_cache(cache_key)
    if cached:
        return cached

    ta_data = analyze_technical_indicators()
    
    # دمج وتحليل الإشارات عبر الأطر الزمنية المختلفة (Multi-Timeframe Logic)
    m15 = ta_data.get("15m", {})
    h1 = ta_data.get("1h", {})
    h4 = ta_data.get("4h", {})
    
    if not m15 or not h1:
        raise RuntimeError("بيانات الأطر الزمنية غير مكتملة")
        
    score = 0
    reasons = []
    
    # 1. فحص الزخم عبر RSI
    if m15["rsi"] < 30:
        score += 2
        reasons.append("تشبع بيعي على إطار 15 دقيقة (RSI < 30)")
    elif m15["rsi"] > 70:
        score -= 2
        reasons.append("تشبع شرائي على إطار 15 دقيقة (RSI > 70)")
        
    if h1["rsi"] < 35:
        score += 1
        reasons.append("زخم هابط ضعيف على إطار الساعة يقترب من القاع")
    elif h1["rsi"] > 65:
        score -= 1
        reasons.append("زخم صاعد مفرط على إطار الساعة يقترب من القمة")

    # 2. فحص تقاطعات MACD
    if m15["macd"] > m15["macd_signal"]:
        score += 1
        reasons.append("تقاطع إيجابي للـ MACD على إطار 15 دقيقة")
    else:
        score -= 1
        reasons.append("تقاطع سلبي للـ MACD على إطار 15 دقيقة")

    # 3. فحص الاتجاه العام عبر المتوسطات المتحركة (EMA)
    if h1["close"] > h1["ema_50"]:
        score += 1
        if h1["ema_50"] > h1["ema_200"]:
            score += 1
            reasons.append("الاتجاه العام صاعد ومستقر (السعر فوق EMA 50 و 200)")
    else:
        score -= 1
        reasons.append("الاتجاه العام تحت الضغط (السعر تحت EMA 50)")

    # اتخاذ القرار النهائي بناءً على النقاط المجمعة
    if score >= 3:
        decision = "BUY"
    elif score <= -3:
        decision = "SELL"
    else:
        decision = "HOLD"
        
    result = {
        "pair": "BTCUSDT",
        "decision": decision,
        "score": score,
        "current_price": m15["close"],
        "reasons": reasons,
        "indicators_snapshot": {
            "15m_rsi": m15["rsi"],
            "1h_rsi": h1["rsi"],
            "4h_rsi": h4.get("rsi", 50.0)
        }
    }
    
    set_cache(cache_key, result, ttl=300)
    return result

