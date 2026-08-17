"""
工具模块 — 定义 Agent 可用的工具（schema + 实现）。

本文件分两部分，缺一不可：
  1. TOOLS      —— 工具 schema（给 LLM 看的「说明书」，告诉它有哪些工具、怎么用）
  2. TOOL_IMPL  —— 工具实现（真正执行工具的函数，agent.py 会调用）

新增一个工具只需两步：
  1. 在 TOOLS 里加一个 schema
  2. 在 TOOL_IMPL 里加一个实现函数

schema 写法参考 ex06 的 GOOD schema 标准：
  - description 写「何时用」而非「做什么」
  - type 精确（string 就是 string，number 就是 number）
  - required 明确标注必填参数
"""

import json


# ============================================
# 第一部分：工具 Schema（给 LLM 看的「说明书」）
# ============================================
# 每个 schema 的结构是固定的，照抄骨架填内容即可：
#
#   {
#       "type": "function",            # 固定写法，不要改
#       "function": {
#           "name": "工具名",          # 唯一标识，LLM 靠它区分工具
#           "description": "何时用",    # 关键！写「何时用」而非「做什么」
#           "parameters": {
#               "type": "object",      # 固定写法：参数整体是一个对象
#               "properties": {        # 有哪些参数，每个参数一个条目
#                   "参数名": {
#                       "type": "string",     # 参数类型
#                       "description": "..."   # 该参数该填什么
#                   }
#               },
#               "required": ["参数名"]  # 哪些参数必填
#           }
#       }
#   }

TOOLS = [
    # ========== 工具 1：计算器 ==========
    # 提示：接受一个算术表达式（如 "19*42-8"），返回计算结果
    {
        "type": "function",
        "function": {
            "name": "calculator",             
            "description": "当用户想你提问算数计算问题时,或者需要进行算数计算问题时调用此方法,例如问你俄罗斯占地面积是美国的多少倍?",       
            "parameters": {
                "type": "object",
                "properties": {
                    "arithmetic_expression":{
                        "type":"string",
                        "description":"需要计算的算式,例如'19*42-8'"
                    }
                },
                "required": ["arithmetic_expression"]       #填必填参数名
            }
        }
    },

    # ========== 工具 2：天气查询 ==========
    # 提示：接受一个城市名（如「北京」），返回天气信息（可用模拟数据）
    {
        "type": "function",
        "function": {
            "name": "get_weather",              
            "description": "当用户想你询问某地的天气状况时使用,例如问你'今天北京的天气怎么样?'",       
            "parameters": {
                "type": "object",
                "properties": {
                    "city":{
                        "type":"string",
                        "description":"用户需要查询天气的地址,如'北京'"
                    }
                },
                "required": ["city"]       
            }
        }
    },

    # ========== 工具 3：文件读取 ==========
    # 提示：接受一个文件路径，返回文件内容
    {
        "type": "function",
        "function": {
            "name": "read_file",              
            "description": "当用户提问需要查看一个文件时调用该工具,例如:'我想查看file.txt文件的内容'",       
            "parameters": {
                "type": "object",
                "properties": {
                    "path":{
                        "type":"string", 
                        "description":"用户提供的文件路径"
                    }
                },
                "required": ["path"]       # TODO: 填必填参数名
            }
        }
    },

    # ========== 工具 4：搜索模拟 ==========
    # 提示：接受一个问题,返回搜索结果
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "当用户询问你需要上网搜索的问题时调用此工具,例如用户问:'2026年世界杯冠军是哪个国家?'",
            "parameters": {
                "type": "object",
                "properties": {
                    "question":{
                        "type":"string",
                        "description":"填写需要联网搜索的问题的关键词,如:'2026年世界杯'"
                    }
                },
                "required": ["question"]
            }
        }
    },

    # ========== 工具 5：当前时间查询 ==========
    # 提示：返回当前时间告知LLM
    {
        "type": "function",
        "function": {
            "name": "get_current_time",            
            "description": "当用户询问有关当前时间的问题时调用,可以让你知道当前时间",      
            "parameters": {
                "type": "object",
                "properties": { },
                "required": []      
            }
        }
    }
]


# ============================================
# 第二部分：工具实现（真正执行的函数）
# ============================================
# 当 LLM 决定调用某工具时，agent.py 会：
#   1. 用 json.loads 解析 LLM 传来的参数（得到一个 dict）
#   2. 查 TOOL_IMPL 字典，用工具名找到对应的函数
#   3. 把参数字典传给函数，拿到返回的字符串
#
# 所以有两个约定必须遵守：
#   - 每个实现函数的签名是  fn(args: dict) -> str
#   - TOOL_IMPL 的 key 必须和上面 TOOLS 里的 name 完全一致！

# 实现要点（参考 ex05「error 是 data 不是 exception」）：
#   - 成功 → 返回结果字符串
#   - 失败 → 不要 raise，而是返回 error dict 字符串，让 LLM 自己决定怎么办：
#       json.dumps({"error": "...", "retry_hint": "..."}, ensure_ascii=False)


# 模拟天气数据（供工具 2 查表用，按需修改）
# _WEATHER_DATA = {"北京": {"weather": "晴", "temperature": 25}, ...}

_WEATHER_DATA = {
    "北京": {"weather": "晴", "temperature": 30}, 
    "上海": {"weather": "多云", "temperature": 27}, 
    "纽约": {"weather": "阴", "temperature": 22}, 
    "东京": {"weather": "雨", "temperature": 20}, 
    "悉尼": {"weather": "晴", "temperature": 35}
}

def _calculator(args: dict) -> str:
    """计算器：执行算术表达式。"""
    # 1. 取表达式参数  2. 计算  3. 成功返回 str，失败返回 error dict
    expr = args.get("arithmetic_expression", "")
    if not expr:    #过滤无参数情况
        return json.dumps(
            {
                "error":"缺少城市参数",
                "retry_hint":"重新提取城市参数",
                "category": "transient"
            },
            ensure_ascii=False
        )
    allowed = set("0123456789+-*/(). ")   #白名单过滤非法表达式
    if not all(ch in allowed for ch in expr):
        return json.dumps(
            {
                "error":"表达式含有非法数字符",
                "allowed":"表达式只能含有'0123456789+-*/.() '这些字符",
                "retry_hint":"重新获取算式"
            },
            ensure_ascii=False
        )

    try:
        return str(eval(expr))
    except Exception as e:    #过滤表达式语法
        return json.dumps(
            {
                "error":f"计算失败:{e}",
                "retry_hint":"检查表达式语法"
            },
            ensure_ascii=False
        )



def _get_weather(args: dict) -> str:
    """天气查询：返回城市天气。"""
    # TODO: 1. 取城市名参数  2. 查模拟数据表  3. 查不到返回 error dict
    city = args.get("city", "")
    if not city:
        return json.dumps(
            {
                "error":"缺少表达式参数",
                "retry_hint":"重新提取表达式参数",
                "category": "transient"
            },
            ensure_ascii=False
        )
    if city in _WEATHER_DATA:
        return json.dumps(_WEATHER_DATA[city], ensure_ascii=False)
    return json.dumps(
        {
            "error":"当前工具查不到该地天气",
            "retry_hint":"告诉用户请求换一个地址查询"
        },
        ensure_ascii=False
    )
        


def _read_file(args: dict) -> str:
    """文件读取：返回文件内容。"""
    # TODO: 1. 取文件路径参数  2. 读文件（编码 utf-8）  3. 文件不存在返回 error dict
    path = args.get("path", "")
    if not path:
        return json.dumps(
            {
                "error":"缺少文件路径参数",
                "retry_hint":"重新提取文件路径参数",
                "category": "transient"
            },
            ensure_ascii=False
        )
    from config import MAX_FILE_CHARS   #最大阈值
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()  # 一次性读取全部文本
        if len(content) > MAX_FILE_CHARS:
              content = content[:MAX_FILE_CHARS] + "\n...(文件过长，已截断，只显示前 2000 字)"

        return content
      
    except Exception as e:
        return json.dumps(
            {
                "error": f"读取失败: {e}", "retry_hint": "检查路径或权限"
            }, 
            ensure_ascii=False
        )

_MOCK_SEARCH = {
    "2026年世界杯冠军": "2026 年世界杯冠军是西班牙队。",
    "天气": "请改用 get_weather 工具查询具体城市天气。",
}

def _web_search(args: dict) -> str:
    """联网搜索：返回模拟搜索结果。"""
    # TODO: 1. 取 question 参数  2. 返回模拟搜索结果  3. 无参数时返回 error dict
    # 提示：
    #   成功 → return json.dumps({"question":..., "result":"模拟结果"}, ensure_ascii=False)
    #   失败（无参数）→ return json.dumps({"error":"...", "retry_hint":"..."}, ensure_ascii=False)
    # 注意：本地无真实联网，返回「模拟结果」即可，重点是让 LLM 知道"已经搜过了"
    question = args.get("question", "")
    if not question:
        return json.dumps({
            "error":"缺少关键词无法查询",
            "retry_hint":"重新提取关键词"
            },  
            ensure_ascii=False
        )
    if question in _MOCK_SEARCH:
        return _MOCK_SEARCH[question]
    print(f"日志: 没有{question}相关的搜索结果")
    return json.dumps(
        {
            "error":f"没有{question}相关的搜索结果",
            "retry_hint":"换个关键词试试"
        },
        ensure_ascii=False
    )


def _get_current_time(args: dict) -> str:
    """当前时间查询：返回系统当前时间（无参数工具，args 用不到但保持签名统一）。"""
    from datetime import datetime
    return json.dumps({"current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, ensure_ascii=False)



# 工具名 → 实现函数 的映射
# key 必须和 TOOLS 里的 name 完全一致，否则 agent.py 找不到工具会报错
TOOL_IMPL = {
    "calculator": _calculator,
    "get_weather": _get_weather,
    "read_file": _read_file,
    "web_search": _web_search,
    "get_current_time": _get_current_time,
}
