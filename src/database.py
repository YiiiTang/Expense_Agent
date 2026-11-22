import os
import sqlite3

DB_PATH = os.getenv("DB_PATH", "/app/data/finance.db")

def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """初始化 expenses 與 budgets 資料表"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                item TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                category TEXT PRIMARY KEY,
                monthly_limit REAL NOT NULL
            )
        """)
        # 預設初始化六大分類預算（若尚無設定）
        default_budgets = [
            ("餐飲", 6000.0),
            ("交通", 2000.0),
            ("娛樂", 3000.0),
            ("學習", 2000.0),
            ("生活", 3000.0),
            ("其他", 2000.0),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO budgets (category, monthly_limit) VALUES (?, ?)",
            default_budgets,
        )
        conn.commit()