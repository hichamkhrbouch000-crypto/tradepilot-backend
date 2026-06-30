import time
import json
import sqlite3
import threading
from typing import Any, Optional
from config import DB_PATH

_in_memory_cache = {}
_lock = threading.Lock()

def get_cache(key: str) -> Optional[Any]:
    with _lock:
        entry = _in_memory_cache.get(key)
        if entry and time.time() < entry["expire"]:
            return entry["value"]
    return None

def set_cache(key: str, value: Any, ttl: int = 300):
    with _lock:
        _in_memory_cache[key] = {
            "value": value,
            "expire": time.time() + ttl
        }
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS cache
                     (key TEXT PRIMARY KEY, value TEXT, expire REAL)''')
        c.execute('''INSERT OR REPLACE INTO cache VALUES (?, ?, ?)''',
                  (key, json.dumps(value), time.time() + ttl))
        conn.commit()
        conn.close()
    except Exception:
        pass

def fallback_from_db(key: str) -> Optional[Any]:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT value, expire FROM cache WHERE key=?", (key,))
        row = c.fetchone()
        conn.close()
        if row:
            value, expire = row
            if time.time() < expire:
                return json.loads(value)
    except Exception:
        pass
    return None

