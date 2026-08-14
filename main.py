"""
CLI 入口 — 命令行交互式 AI 助手。

用法：
    python main.py

命令：
    help  — 查看可用工具
    quit  — 退出（也可以用 exit 或 Ctrl+C）
"""

from agent import run_agent
from tools import TOOLS


def print_help():
    """打印可用工具列表"""
    # TODO: 遍历 TOOLS，打印每个工具的 name 和 description
    # 提示：TOOLS 是列表，每一项 t["function"] 里有 "name" 和 "description" 两个字段
    # 示例输出：
    #   • calculator: 当用户想你提问算数计算问题时...
    print("用户你好,以下是可调用工具:")
    count = 1
    for t in TOOLS:
        print(f"工具{count}: 名称: {t['function']['name']}, 作用: {t['function']['description']}")
        count += 1
    


def main():
    print("=" * 50)
    print("🤖 命令行 AI 助手 (Project #1)")
    print("=" * 50)
    print("输入 'help' 查看工具，输入 'quit' 退出\n")

    history = []   # 多轮对话历史（每轮往里面追加消息）

    # ============================================
    # 主循环：反复读取用户输入
    # ============================================
    while True:
        # ---- 第 1 步：读输入 ----
        # TODO: user_input = input("\n🧑 > ").strip()
        #   提示：用 try/except 包住 input，
        #   捕获 KeyboardInterrupt / EOFError（用户按 Ctrl+C / Ctrl+D）
        #   捕获后打印"再见"并 break
        try:
            user_input = input("\n用户 > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("🤖 > 再见")
            break

        # ---- 第 2 步：处理特殊命令 ----
        # TODO:
        #   - 空输入（if not user_input）→ continue
        #   - "quit" / "exit" → print 再见后 break
        #   - "help" → 调 print_help() 后 continue
        if not user_input:
            continue
        if user_input.lower() in ["quit", "exit"]:
            print("🤖 > 再见")
            break
        if user_input.lower() == "help":
            print_help()
            continue

        # ---- 第 3 步：正常问题 ----
        # TODO:
        #   a. history.append({"role": "user", "content": user_input})
        #   b. response = run_agent(user_input, history)
        #   c. print(f"🤖 > {response}")
        #
        # ⚠️ 注意：不要在这里再 append 一条 assistant 消息！
        #   run_agent 内部已经帮你把 assistant + tool 消息都 append 进 history 了，
        #   如果这里再 append 一条 {"role":"assistant", ...}，
        #   最终回答会在 history 里出现两次（重复），下一轮 LLM 会看到两条一样的话。
        history.append(
            {"role":"user", "content":user_input}
        )
        response = run_agent(user_input, history)

        print(f"🤖 > {response}")



if __name__ == "__main__":
    main()
