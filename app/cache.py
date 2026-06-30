import json
import sqlite3
import os

# قراءة مسار قاعدة البيانات من متغيرات البيئة مباشرة، وإذا لم تكن موجودة يتم إنشاء ملف محلي بأمان
DB_PATH = os.getenv("DATABASE_URL", "tradepilot_cache.db")

def init_db():
    """تهيئة قاعدة البيانات للكاش إذا لم تكن موجودة."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT,
            expire INTEGER
        )
    """)
    conn.commit()
    conn.close()

# تشغيل التهيئة تلقائياً عند استدعاء الملف
init_db()

def get_cache(key: str):
    """جلب البيانات من الكاش بناءً على المفتاح."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        import time
        current_time = int(time.time())
        
        cursor.execute("SELECT value, expire FROM cache WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        if row:
            value, expire = row
            if expire == 0 or expire > current_time:
                return json.loads(value)
            else:
                # حذف الكاش المنتهي الصلاحية
                cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
        return None
    except Exception:
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def set_cache(key: str, value: dict, expire: int = 0):
    """حفظ البيانات في الكاش مع تحديد وقت الصلاحية بالثواني."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        import time
        
        expire_time = int(time.time()) + expire if expire > 0 else 0
        value_str = json.dumps(value)
        
        cursor.execute("""
            INSERT OR REPLACE INTO cache (key, value, expire)
            VALUES (?, ?, ?)
        """, (key, value_str, expire_time))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def fallback_from_db(key: str):
    """دالة احتياطية لجلب البيانات القديمة حتى لو انتهت صلاحيتها في حال حدوث خطأ في السيرفر."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM cache WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return {}
    except Exception:
        return {}
    finally:
        if 'conn' in locals():
            conn.close()
