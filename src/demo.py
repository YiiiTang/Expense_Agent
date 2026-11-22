from main import create_agent


def run_demo():
    agent = create_agent(max_steps=5)

    demo_prompts = [
        "幫我設定這個月餐飲預算為 3000 元",
        "幫我記今天晚餐吃火鍋 680 元、搭計程車 180 元、買資料夾 95 元，順便看這個月餐飲預算還夠嗎？",
    ]

    print("=" * 60)
    print("開始執行 Demo 測試腳本（重現多工具呼叫與預算診斷 Trace）")
    print("=" * 60)

    for prompt in demo_prompts:
        agent.run(prompt)


if __name__ == "__main__":
    run_demo()