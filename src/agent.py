import json
import os
from datetime import datetime
from openai import OpenAI
from tools import TOOLS_SCHEMA, TOOL_DISPATCHER

class ExpenseReActAgent:
    def __init__(self, max_steps: int = 5):
        self.client = OpenAI(
            base_url=os.getenv("LLM_BASE_URL", "http://host.containers.internal:11434/v1"),
            api_key=os.getenv("LLM_API_KEY", "ollama"),
        )
        self.model = os.getenv("LLM_MODEL", "qwen2.5:7b")
        self.max_steps = max_steps
        self.history = []  # 短期對話記憶 (Session Memory)

    def _build_system_prompt(self) -> str:
        today = datetime.now().strftime("%Y-%m-%d (%A)")
        return f"""你是一個「個人記帳與預算超支診斷智慧代理系統」，請全程使用繁體中文回答。
今天系統日期為：{today}。

【執行規則】
1. 消費分類只能從這六個裡面選一個：「餐飲、交通、娛樂、學習、生活、其他」。
2. 如果使用者一句話包含多筆消費（例如吃火鍋又搭計程車），請拆成多次呼叫 `record_expense`。
3. 拿到工具回傳的 JSON 結果（Observation）後，請**直接根據數據生成最終回覆**，不要重複呼叫已經執行過的工具。
4. 所有金額加總、預算使用率與日均額度，必須 100% 照抄工具回傳的數字，絕對不可自己心算。
5. 若工具回傳 `WARNING_80%` 或 `RED_ALERT`，請列出 `top3_expenses` 並告知 `daily_allowance`（每日可用額度）。"""

    def run(self, user_input: str) -> str:
        print("\n" + "=" * 60)
        print(f"[User Input] {user_input}")
        print("=" * 60)

        # 保留最近 5 輪對話記憶
        recent_history = self.history[-10:]
        messages = [{"role": "system", "content": self._build_system_prompt()}] + recent_history + [
            {"role": "user", "content": user_input}
        ]

        for step in range(1, self.max_steps + 1):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                temperature=0.1,
            )
            msg = response.choices[0].message
            messages.append(msg)

            # 印出 Agent 決策與思考軌跡
            thought_text = msg.content.strip() if msg.content else "(決定直接呼叫工具執行任務)"
            print(f"\n--- Step {step} ---")
            print(f"[Decision / Thought] {thought_text}")

            # 若沒有 Tool Calls，代表推理完成，輸出最終結果
            if not msg.tool_calls:
                final_answer = msg.content or "任務已完成。"
                print(f"\n[Final Output]\n{final_answer}")
                print("=" * 60 + "\n")

                # 更新短期記憶
                self.history.append({"role": "user", "content": user_input})
                self.history.append({"role": "assistant", "content": final_answer})
                return final_answer

            # 依序執行本輪所有的 Tool Calls
            for tc in msg.tool_calls:
                func_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                print(f"[Tool Call] {func_name}({json.dumps(args, ensure_ascii=False)})")

                func = TOOL_DISPATCHER.get(func_name)
                if func:
                    observation = func(**args)
                else:
                    observation = json.dumps({"status": "error", "message": f"未知工具: {func_name}"}, ensure_ascii=False)

                print(f"[Observation] {observation}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": observation,
                })

        fallback = "已達最大推理步驟上限（Loop Control 終止），請簡化指令後再試。"
        print(f"\n[Final Output] {fallback}")
        return fallback