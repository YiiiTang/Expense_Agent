import calendar
import json
from datetime import datetime
from typing import Optional
from database import get_connection

VALID_CATEGORIES = {"餐飲", "交通", "娛樂", "學習", "生活", "其他"}

def record_expense(date: str, item: str, amount: float, category: str) -> str:
    """工具 1：寫入單筆消費紀錄"""
    try:
        datetime.strptime(date, "%Y-%m-%d")
        if amount <= 0:
            return json.dumps({"status": "error", "message": "消費金額必須大於 0"}, ensure_ascii=False)
        if category not in VALID_CATEGORIES:
            return json.dumps(
                {"status": "error", "message": f"無效類別 '{category}'，僅支援：{list(VALID_CATEGORIES)}"},
                ensure_ascii=False,
            )

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO expenses (date, item, amount, category) VALUES (?, ?, ?, ?)",
                (date, item, float(amount), category),
            )
            expense_id = cursor.lastrowid
            conn.commit()

        return json.dumps(
            {
                "status": "success",
                "expense_id": expense_id,
                "data": {"date": date, "item": item, "amount": float(amount), "category": category},
            },
            ensure_ascii=False,
        )
    except ValueError:
        return json.dumps({"status": "error", "message": "日期格式錯誤，必須為 YYYY-MM-DD"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"資料庫寫入異常: {str(e)}"}, ensure_ascii=False)


def query_expenses(start_date: str, end_date: str, category: Optional[str] = None) -> str:
    """工具 2：依時間區間與類別查詢消費明細與總和"""
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")

        with get_connection() as conn:
            cursor = conn.cursor()
            if category and category != "全部":
                cursor.execute(
                    "SELECT id, date, item, amount, category FROM expenses WHERE date BETWEEN ? AND ? AND category = ? ORDER BY date DESC",
                    (start_date, end_date, category),
                )
            else:
                cursor.execute(
                    "SELECT id, date, item, amount, category FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date DESC",
                    (start_date, end_date),
                )
            rows = [dict(row) for row in cursor.fetchall()]

        total = sum(r["amount"] for r in rows)
        return json.dumps(
            {
                "status": "success",
                "count": len(rows),
                "total_amount": round(total, 2),
                "records": rows,
            },
            ensure_ascii=False,
        )
    except ValueError:
        return json.dumps({"status": "error", "message": "日期格式錯誤，必須為 YYYY-MM-DD"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"查詢失敗: {str(e)}"}, ensure_ascii=False)


def diagnose_budget_status(month: str, category: str) -> str:
    """工具 3：計算預算使用率、燈號狀態、Top 3 高額消費與月底前剩餘日均額度"""
    try:
        year, mon = map(int, month.split("-"))
        if category not in VALID_CATEGORIES:
            return json.dumps({"status": "error", "message": f"無效類別 '{category}'"}, ensure_ascii=False)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT monthly_limit FROM budgets WHERE category = ?", (category,))
            row = cursor.fetchone()
            if not row:
                return json.dumps({"status": "error", "message": f"尚未設定 {category} 預算"}, ensure_ascii=False)
            limit = row["monthly_limit"]

            cursor.execute(
                "SELECT item, amount, date FROM expenses WHERE strftime('%Y-%m', date) = ? AND category = ? ORDER BY amount DESC",
                (month, category),
            )
            expenses = [dict(r) for r in cursor.fetchall()]

        spent = sum(e["amount"] for e in expenses)
        rate = (spent / limit * 100) if limit > 0 else 0.0
        remain = limit - spent

        if rate >= 100:
            light = "RED_ALERT (>=100%)"
        elif rate >= 80:
            light = "WARNING_80% (80%~99%)"
        else:
            light = "GREEN_OK (<80%)"

        # 計算當月剩餘天數（若查詢非當月則以該月總天數估算）
        now = datetime.now()
        last_day = calendar.monthrange(year, mon)[1]
        if now.year == year and now.month == mon:
            days_left = max(1, last_day - now.day + 1)
        else:
            days_left = last_day

        daily_allowance = round(max(0.0, remain) / days_left, 1)
        top3 = [{"item": e["item"], "amount": e["amount"], "date": e["date"]} for e in expenses[:3]]

        return json.dumps(
            {
                "status": "success",
                "month": month,
                "category": category,
                "limit": limit,
                "spent": round(spent, 2),
                "usage_rate": f"{rate:.1f}%",
                "alert_status": light,
                "remain": round(remain, 2),
                "days_left": days_left,
                "daily_allowance": daily_allowance,
                "top3_expenses": top3,
            },
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": f"診斷運算錯誤: {str(e)}"}, ensure_ascii=False)


def set_category_budget(category: str, monthly_limit: float) -> str:
    """工具 4：設定或更新類別月度預算上限"""
    try:
        if category not in VALID_CATEGORIES:
            return json.dumps({"status": "error", "message": f"無效類別 '{category}'"}, ensure_ascii=False)
        if monthly_limit <= 0:
            return json.dumps({"status": "error", "message": "預算上限必須大於 0"}, ensure_ascii=False)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO budgets (category, monthly_limit) VALUES (?, ?) ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit",
                (category, float(monthly_limit)),
            )
            conn.commit()

        return json.dumps(
            {"status": "success", "category": category, "new_monthly_limit": float(monthly_limit)},
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": f"預算設定失敗: {str(e)}"}, ensure_ascii=False)


# 供 LLM Function Calling 使用的 Tool Schema
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "record_expense",
            "description": "將單筆消費紀錄寫入本地財務資料庫。若使用者一次提到多筆消費，請拆分為多次呼叫。",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "消費日期，格式 YYYY-MM-DD"},
                    "item": {"type": "string", "description": "消費品項名稱"},
                    "amount": {"type": "number", "description": "消費金額（正數）"},
                    "category": {
                        "type": "string",
                        "enum": ["餐飲", "交通", "娛樂", "學習", "生活", "其他"],
                        "description": "消費分類",
                    },
                },
                "required": ["date", "item", "amount", "category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_expenses",
            "description": "依日期區間與類別查詢歷史消費明細、筆數與總金額。",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "起始日期 YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "結束日期 YYYY-MM-DD"},
                    "category": {"type": "string", "description": "篩選類別（餐飲/交通/娛樂/學習/生活/其他/全部）"},
                },
                "required": ["start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "diagnose_budget_status",
            "description": "計算特定月份與類別的預算使用率、預警燈號、Top 3 高額消費與剩餘日均額度。",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "查詢月份，格式 YYYY-MM"},
                    "category": {
                        "type": "string",
                        "enum": ["餐飲", "交通", "娛樂", "學習", "生活", "其他"],
                        "description": "預算類別",
                    },
                },
                "required": ["month", "category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_category_budget",
            "description": "設定或更新指定類別的每月預算上限。",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["餐飲", "交通", "娛樂", "學習", "生活", "其他"],
                        "description": "預算類別",
                    },
                    "monthly_limit": {"type": "number", "description": "每月預算上限金額（正數）"},
                },
                "required": ["category", "monthly_limit"],
            },
        },
    },
]

TOOL_DISPATCHER = {
    "record_expense": record_expense,
    "query_expenses": query_expenses,
    "diagnose_budget_status": diagnose_budget_status,
    "set_category_budget": set_category_budget,
}