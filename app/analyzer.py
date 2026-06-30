import numpy as np
import pandas as pd
# تعديل المسار هنا ليصبح نسبياً وصحيحاً داخل مجلد app
from .cache import get_cache, set_cache, fallback_from_db

def analyze_technical_indicators():
    """
    جلب المؤشرات الفنية الحالية وتحليلها.
    """
    # محاولة جلب البيانات من الكاش أولاً
    cached_data = get_cache("technical_metrics")
    if cached_data:
        return cached_data

    # بيانات افتراضية للمؤشرات الفنية في حال عدم وجود كاش
    metrics = {
        "rsi": 58.5,
        "macd": {"line": 120.5, "signal": 95.2, "histogram": 25.3},
        "moving_averages": {"ema_20": 64200, "sma_50": 62100},
        "bollinger_bands": {"upper": 66000, "middle": 63500, "lower": 61000}
    }
    
    # حفظ البيانات في الكاش لمدة 5 دقائق
    set_cache("technical_metrics", metrics, expire=300)
    return metrics

def generate_trading_decision():
    """
    بناءً على المؤشرات الفنية، يتم اتخاذ قرار التداول (شراء، بيع، أو انتظار).
    """
    try:
        indicators = analyze_technical_indicators()
    except Exception:
        indicators = fallback_from_db("technical_metrics")

    rsi = indicators.get("rsi", 50)
    macd_hist = indicators.get("macd", {}).get("histogram", 0)
    
    # منطق اتخاذ القرار البرمجي
    if rsi < 30 and macd_hist > 0:
        decision = "BUY"
        confidence = "HIGH"
    elif rsi > 70 and macd_hist < 0:
        decision = "SELL"
        confidence = "HIGH"
    elif 45 <= rsi <= 65:
        decision = "HOLD"
        confidence = "MEDIUM"
    else:
        decision = "HOLD"
        confidence = "LOW"
        
    return {
        "decision": decision,
        "confidence": confidence,
        "target_entry": indicators.get("moving_averages", {}).get("ema_20", 0),
        "timestamp": "active"
    }
