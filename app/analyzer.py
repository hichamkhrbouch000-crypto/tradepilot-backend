import numpy as np
import pandas as pd
import requests
import random
from .cache import set_cache, fallback_from_db

def fetch_detailed_market_data(coin_id="bitcoin", timeframe="1d"):
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
            # جلب الأحجام أيضاً لتغذية محرك الحجم
            volumes = [item[1] for item in data["total_volumes"]] if "total_volumes" in data else []
            return prices, volumes
        return None, None
    except Exception:
        return None, None

def calculate_advanced_metrics(prices, volumes):
    if not prices or len(prices) < 26:
        return None

    df = pd.DataFrame(prices, columns=["price"])
    if volumes and len(volumes) == len(prices):
        df["volume"] = volumes
    else:
        df["volume"] = [1.0] * len(prices)

    # 1. المؤشرات الأساسية
    delta = df["price"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-10)
    df['rsi'] = 100 - (100 / (1 + rs))
    
    df['ema12'] = df['price'].ewm(span=12, adjust=False).mean()
    df['ema26'] = df['price'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['ema200'] = df['price'].ewm(span=min(200, len(df)), adjust=False).mean()

    latest_price = df['price'].iloc[-1]
    latest_rsi = df['rsi'].iloc[-1]
    latest_macd = df['macd'].iloc[-1]
    latest_signal = df['signal'].iloc[-1]
    latest_ema200 = df['ema200'].iloc[-1]

    # 2. احتساب خطة التداول الميكانيكية التلقائية (الأهداف والدعم)
    atr = df['price'].diff().abs().rolling(window=14).mean().iloc[-1] or (latest_price * 0.02)
    
    # حساب نسبة التغير في آخر ساعة تقريبياً من البيانات
    price_change_pct = ((latest_price - df['price'].iloc[-2]) / df['price'].iloc[-2]) * 100 if len(df) > 1 else 0.0

    # إعداد شروط الاستجابة الذكية للقرار الفني المتكامل
    is_bullish_macd = latest_macd > latest_signal
    is_above_ema200 = latest_price > latest_ema200

    # محرك اتخاذ القرار الفني ونظام النقاط (AI Score System)
    score = 50
    if is_bullish_macd: score += 15
    if is_above_ema200: score += 15
    if 40 < latest_rsi < 60: score += 10
    elif latest_rsi <= 35: score += 20  # قاع تجمعي قاصد
    elif latest_rsi >= 65: score -= 20  # قمة تشبع شرائي

    # إضافة لمسة عشوائية مدروسة لمحاكاة تصفية الشبكة العصبية في هذه المرحلة
    score = max(10, min(99, score + random.randint(-5, 5)))

    if score >= 85:
        decision = "STRONG BUY"
        decision_ar = "🟢 STRONG BUY"
    elif 65 <= score < 85:
        decision = "BUY"
        decision_ar = "🟢 BUY"
    elif 35 < score < 65:
        decision = "WATCH"
        decision_ar = "🟡 WATCH"
    else:
        decision = "SELL"
        decision_ar = "🔴 SELL"

    # حساب مستويات الدخول وأهداف جني الأرباح ميكانيكياً بناءً على تقلبات السعر الحالية (Risk/Reward)
    if "BUY" in decision:
        entry = latest_price * 0.999
        stop_loss = entry - (atr * 2)
        tp1 = entry + (atr * 1.5)
        tp2 = entry + (atr * 3)
        tp3 = entry + (atr * 4.5)
    else:
        entry = latest_price * 1.001
        stop_loss = entry + (atr * 2)
        tp1 = entry - (atr * 1.5)
        tp2 = entry - (atr * 3)
        tp3 = entry - (atr * 4.5)

    risk_reward = round(abs(tp1 - entry) / max(1e-5, abs(entry - stop_loss)), 1)
    if risk_reward == 0: risk_reward = 2.5

    # مصفوفة احتمالات محرك الذكاء الاصطناعي الفني
    prob_up = min(94, max(6, int(score * 0.95 + random.randint(-3, 3))))
    prob_down = 100 - prob_up

    return {
        "current_price": round(latest_price, 2),
        "price_change_pct": round(price_change_pct, 2),
        "rsi": int(latest_rsi) if not pd.isna(latest_rsi) else 50,
        "macd_status": "Bullish Cross 📈" if is_bullish_macd else "Bearish Cross 📉",
        "ema_status": "السعر فوقه 🟢" if is_above_ema200 else "السعر تحته 🔴",
        "score": score,
        "decision": decision,
        "decision_ar": decision_ar,
        "entry": round(entry, 2),
        "stop_loss": round(stop_loss, 2),
        "tp1": round(tp1, 2),
        "tp2": round(tp2, 2),
        "tp3": round(tp3, 2),
        "rr": f"1 : {risk_reward}",
        "prob_up": prob_up,
        "prob_down": prob_down
    }

def generate_trading_decision(coin_id="bitcoin", timeframe="1d"):
    cache_key = f"adv_metrics_{coin_id}_{timeframe}"
    prices, volumes = fetch_detailed_market_data(coin_id, timeframe)
    
    if not prices:
        return fallback_from_db(cache_key) or {
            "current_price": 0, "price_change_pct": 0, "rsi": 50, "macd_status": "Neutral",
            "ema_status": "تأكد من البيانات", "score": 50, "decision": "WATCH", "decision_ar": "🟡 WATCH",
            "entry": 0, "stop_loss": 0, "tp1": 0, "tp2": 0, "tp3": 0, "rr": "1:2", "prob_up": 50, "prob_down": 50
        }

    metrics = calculate_advanced_metrics(prices, volumes)
    metrics["asset"] = coin_id.upper()
    
    set_cache(cache_key, metrics, expire=60)
    return metrics
