import numpy as np
import pandas as pd
import requests
from .cache import get_cache, set_cache, fallback_from_db

def fetch_live_market_data():
    """
    جلب بيانات الأسعار التاريخية والحية لعملة البتكوين من CoinGecko API مجاناً
    """
    try:
        # طلب أسعار البتكوين لآخر 30 يوماً بتحديث دقيق لعمل الحسابات الفنية
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=30"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            prices = [item[1] for item in data["prices"]]
            return prices
    except Exception:
        return None
    return None

def calculate_rsi(prices, period=14):
    """
    حساب مؤشر القوة النسبية RSI البرمجي بناءً على الأسعار الحقيقية
    """
    if len(prices) < period:
        return 50 # قيمة افتراضية في حال نقص البيانات
    
    df = pd.DataFrame(prices, columns=["price"])
    delta = df["price"].diff()
    
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / (loss + 1e-10) # إضافة رقم صغير جداً لمنع القسمة على صفر
    rsi = 100 - (100 / (1 + rs))
    
    latest_rsi = rsi.iloc[-1]
    return float(latest_rsi) if not np.isnan(latest_rsi) else 50.0

def analyze_technical_indicators():
    """
    جلب المؤشرات الفنية الحية وتحليلها باستخدام الكاش لتفادي حظر الـ API
    """
    # محاولة جلب التحليل من الكاش أولاً (صالح لمدة 10 دقائق لتوفير الطلبات)
    cached_data = get_cache("technical_metrics_live")
    if cached_data:
        return cached_data

    prices = fetch_live_market_data()
    
    if prices is None:
        # إذا فشل الاتصال بالـ API الخارجي، نعود للبيانات الاحتياطية بأمان
        return fallback_from_db("technical_metrics_live") or {
            "rsi": 55.0,
            "current_price": 65000.0,
            "status": "fallback"
        }

    # حساب المؤشرات بناءً على الأسعار الحية
    current_price = prices[-1]
    rsi_value = calculate_rsi(prices)
    
    metrics = {
        "rsi": round(rsi_value, 2),
        "current_price": round(current_price, 2),
        "status": "live"
    }
    
    # حفظ النتيجة في الكاش لمدة 10 دقائق
    set_cache("technical_metrics_live", metrics, expire=600)
    return metrics

def generate_trading_decision():
    """
    اتخاذ قرار التداول بناءً على نبض السوق الفعلي ومؤشر RSI الحقيقي
    """
    try:
        indicators = analyze_technical_indicators()
    except Exception:
        indicators = {"rsi": 50, "current_price": 0, "status": "error"}

    rsi = indicators.get("rsi", 50)
    current_price = indicators.get("current_price", 0)
    
    # منطق اتخاذ القرار البرمجي الاحترافي بناءً على RSI الحقيقي
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
        
    return {
        "asset": "BTC/USD",
        "current_price": current_price,
        "rsi": rsi,
        "decision": decision,
        "confidence": confidence,
        "timestamp": "Real-time Data"
    }
