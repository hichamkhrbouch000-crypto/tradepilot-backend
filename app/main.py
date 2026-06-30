from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
import os
from .analyzer import generate_trading_decision, analyze_technical_indicators

# قراءة مفتاح الأمان من متغيرات بيئة ريلواي لحماية المسارات الخاصة
API_KEY = os.getenv("API_KEY", "tradepilot-mvp-key-123")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="TradePilot Core API",
    description="المحرك الخلفي الذكي لـ TradePilot وتحليل أسواق الكريبتو والمؤشرات الفنية.",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if not api_key or api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="مفتاح الـ X-API-KEY غير صحيح أو مفقود. يرجى تمرير API key صالح في الـ Headers."
        )
    return api_key

@app.get("/")
@limiter.limit("10/minute")
def read_root(request: Request):
    return {
        "status": "online",
        "message": "النظام يعمل بكفاءة. مرحباً بك في المحرك البرمجي لـ TradePilot.",
        "endpoints_available": ["/api/v1/public-decision", "/api/v1/decision", "/api/v1/metrics"]
    }

# --- المسار العام الجديد الخاص بمنصة بلوجر (آمن وبدون قيود API_KEY) ---
@app.get("/api/v1/public-decision")
@limiter.limit("30/minute")
def get_public_decision(request: Request):
    """
    مسار عام مخصص لمنصة بلوجر يجلب البيانات الحية بأمان ودون كشف الـ API_KEY للزوار
    """
    try:
        decision_data = generate_trading_decision()
        return {
            "success": True,
            "data": decision_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"حدث خطأ أثناء معالجة البيانات العامة: {str(e)}"
        )

# --- المسارات الخاصة المحمية بكلمة السر الخاصة بك ---
@app.get("/api/v1/decision")
@limiter.limit("5/minute")
def get_decision(request: Request, token: str = Depends(verify_api_key)):
    try:
        decision_data = generate_trading_decision()
        return {
            "success": True,
            "data": decision_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"حدث خطأ أثناء معالجة القرار: {str(e)}"
        )

@app.get("/api/v1/metrics")
@limiter.limit("5/minute")
def get_metrics(request: Request, token: str = Depends(verify_api_key)):
    try:
        metrics_data = analyze_technical_indicators()
        return {
            "success": True,
            "metrics": metrics_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"حدث خطأ أثناء جلب المؤشرات الفنية: {str(e)}"
        )
