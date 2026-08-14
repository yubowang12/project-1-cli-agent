# 🤖 命令行 AI 助手 (Project #1)

一个基于 **ReAct 模式** 的命令行 AI Agent，本地运行（Ollama + qwen2.5:7b），零成本。

## 架构

LLM 不直接回答所有问题，而是通过「想 → 调工具 → 看结果 → 再想」的循环完成任务。

```
用户输入
   │
   ▼
┌──────────────────────────────────────────────┐
│              ReAct 循环（agent.py）            │
│                                               │
│   LLM 思考（Reason）：我该回答还是调工具？      │
│         │                                     │
│         ▼                                     │
│     要调工具吗？                               │
│      │            │                           │
│    是 │            │ 否                        │
│      ▼            ▼                           │
│  调工具           输出最终回答 ──► 结束         │
│  (tools.py)                                   │
│      │                                         │
│      ▼                                         │
│  拿到工具结果                                  │
│      │                                         │
│      └──► 结果喂回 LLM，继续下一轮思考          │
└──────────────────────────────────────────────┘
```

核心：**Agent = LLM（脑） + Tools（手） + ReAct Loop（心跳）**

## 工具列表

| 工具 | 功能 | 参数 |
|------|------|------|
| `calculator` | 算术运算（+ - * / 括号） | `expression` |
| `get_weather` | 查询城市天气（模拟数据） | `city` |
| `read_file` | 读取本地文件内容 | `filepath` |

## 快速开始

```bash
# 1. 拉取模型（4.7 GB，只需一次）
ollama pull qwen2.5:7b

# 2. 运行
python main.py
```

## 使用示例

```
🧑 > 计算 (19*42) - 8 的结果
🤖 > 790

🧑 > 北京现在天气怎么样？
🤖 > 北京现在是晴天，气温 25°C

🧑 > 帮我读一下 README.md 的内容
🤖 > ...（返回文件内容摘要）
```

## 项目结构

```
project-1-cli-agent/
├── agent.py          # Agent 核心（ReAct 循环）
├── tools.py          # 工具定义 + 实现
├── main.py           # CLI 入口
├── config.py         # 配置（模型、max_iter 等）
└── README.md         # 本文档
```

## 扩展新工具

只需两步，`agent.py` 会自动识别新工具：

1. 在 `tools.py` 的 `TOOLS` 里加一个 schema
2. 在 `TOOL_IMPL` 里加一个实现函数

```python
# 示例：加一个「当前时间」工具
TOOLS.append({
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "查询当前时间时使用",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }
})

from datetime import datetime
TOOL_IMPL["get_current_time"] = lambda args: str(datetime.now())
```

## 技术栈

- Python + OpenAI SDK（Ollama 兼容接口）
- 模型：`qwen2.5:7b`（本地，Ollama）
- 模式：ReAct（Reasoning + Acting）

## 核心设计原则

- **tool error 是 data 不是 exception**：工具出错时返回 error dict，让 LLM 自己决定重试还是放弃
- **description 写「何时用」而非「做什么」**：工具边界清晰，LLM 才不选错
- **max_iter 安全网**：防止工具结果不好时 LLM 无限调用
