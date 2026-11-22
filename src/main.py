import sys
from dotenv import load_dotenv
from database import init_db
from agent import ExpenseReActAgent


def create_agent(max_steps: int = 5) -> ExpenseReActAgent:
    """共用初始化流程：設定編碼、載入環境變數、初始化資料庫與 Agent"""
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    load_dotenv()
    init_db()
    return ExpenseReActAgent(max_steps=max_steps)


def main():
    agent = create_agent(max_steps=5)

    print("=" * 60)
    print("個人記帳與預算超支診斷 Agent 已啟動（手動輸入模式）")
    print("支援分類：餐飲、交通、娛樂、學習、生活、其他")
    print("輸入 'exit' 或 'quit' 離開程式")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n請輸入指令 > ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                print("已結束記帳助手。")
                break
            agent.run(user_input)
        except KeyboardInterrupt:
            print("\n偵測到中斷訊號，已結束程式。")
            break
        except EOFError:
            print("\n[錯誤] 無法讀取標準輸入（EOF）。若透過容器執行，請務必加上 -it 參數。")
            break


if __name__ == "__main__":
    main()