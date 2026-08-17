"""
Agent 核心 — ReAct 循环（Reasoning + Acting）。

流程：LLM 想 → 决定调工具 → 执行工具 → 看结果 → 再想... 直到没有 tool_calls。
这是整个 Agent 的「心跳」，参考 ex03/ex04 的核心循环。

ReAct 一轮的完整流程：
  1. 调用 LLM（带上 tools 和 messages）
  2. LLM 决定：直接回答（无 tool_calls）还是调用工具（有 tool_calls）
  3. 如果调用工具 → 执行工具 → 结果追加回 messages → 回到第 1 步
  4. 如果不调用 → 输出最终回答，结束循环

3 个最容易踩的坑（实现时务必注意）：
  1. 忘记把 assistant response 加回 messages → 下轮 LLM 看不到自己说过的话
  2. tool message 没带 tool_call_id → LLM 无法把结果和调用配对，会报错
  3. 没设 max_iter → 工具结果不好时 LLM 会无限调用，烧钱
"""

import json

from openai import OpenAI

import config
from tools import TOOLS, TOOL_IMPL


# ============================================
# 全局 client（启动时创建一次，之后复用）
# ============================================
client = OpenAI(base_url=config.BASE_URL, api_key=config.API_KEY)


# ============================================
# run_agent — Agent 核心入口
# ============================================
def run_agent(user_input: str, messages: list = None) -> str:
    """
    ReAct Agent：接收用户输入，返回最终回答。

    Args:
        user_input: 用户本轮输入
        messages: 多轮对话历史（可选，默认 None 表示新对话）

    Returns:
        最终回答文本（字符串）
    """
    # 1. 初始化 messages
    # TODO: 如果 messages 是 None，初始化为 [{"role": "user", "content": user_input}]
    if messages is None:
        messages = [{"role": "user", "content": user_input}]

    # 2. ReAct 循环（最多 config.MAX_ITER 轮）
    for step in range(config.MAX_ITER):
        # ---- 第 1 步：调用 LLM ----
        # TODO: 调用 client.chat.completions.create，参数：
        #   model=config.MODEL
        #   tools=TOOLS
        #   messages=messages
        #   max_tokens=config.MAX_TOKENS
        #   temperature=config.TEMPERATURE
        # 然后取 msg = response.choices[0].message
        response = client.chat.completions.create(
            model=config.MODEL,
            tools=TOOLS,
            messages=messages,
            max_tokens=config.MAX_TOKENS,
            temperature=config.TEMPERATURE
        )

        # ---- 第 2 步：把 assistant 回复追加回 messages ----
        # TODO: messages.append(...)
        #   role = "assistant"
        #   必须同时保留 content 和 tool_calls 两个字段！
        #   （坑 1：漏了这条，下轮 LLM 就看不到自己上轮说过的话）
        msg = response.choices[0].message
        messages.append(
            {"role":"assistant", "content":msg.content, "tool_calls":msg.tool_calls}
        )

        # ---- 第 3 步：判断是否结束 ----
        # TODO: 如果 msg.tool_calls 为空（没有要调的工具）→ return msg.content
        #   说明 LLM 认为任务完成，这是最终回答
        if not msg.tool_calls:
            return msg.content

        # ---- 第 4 步：遍历执行工具 ----
        # TODO: 遍历 msg.tool_calls，对每个 tc（tool call）：
        #   a. 解析参数：  args = json.loads(tc.function.arguments)
        #   b. 执行工具：  obs = TOOL_IMPL[tc.function.name](args)
        #   c. 追加结果：  messages.append({
        #                       "role": "tool",
        #                       "tool_call_id": tc.id,   # ← 必须带！否则无法配对（坑 2）
        #                       "content": obs
        #                   })
        #
        # 注意：a、b 两步可能出错（如 LLM 传的参数格式不对），
        #   要用 try/except 包住，出错时返回 error dict 字符串，
        #   而不是让程序崩溃（error 是 data 不是 exception，参考 ex05）
        for tc in msg.tool_calls:
            print(f"日志: 工具调用: {tc.function.name}")
            try:
                args = json.loads(tc.function.arguments)
                obs = TOOL_IMPL[tc.function.name](args)
                messages.append(
                    {"role":"tool", "content":obs, "tool_call_id":tc.id}
                )
                print(f"日志: 工具调用返回值: {obs}")
            except Exception as e:
                obs = json.dumps({"error":str(e), "retry_hint":"检查调用参数"}, ensure_ascii=False)
                messages.append(
                    {"role":"tool", "content":obs, "tool_call_id":tc.id}
                )

    # 3. 安全网：循环跑满 MAX_ITER 还没 break 出来（坑 3 的防线）
    # TODO: return 一个提示语，告诉用户「达到最大迭代次数，任务未完成」
    return "达到最大迭代次数,任务未完成"
