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



# 工具名 → 实现函数 的映射
# key 必须和 TOOLS 里的 name 完全一致，否则 agent.py 找不到工具会报错
TOOL_IMPL = {
    # "工具名": _calculator,   # TODO: 取消注释，key 换成你在 TOOLS 里填的 name
    "calculator":lambda args: _calculator(args),
    # "工具名": _get_weather,  # TODO: 取消注释，key 换成你在 TOOLS 里填的 name
    "get_weather":lambda args:_get_weather(args),
    # "工具名": _read_file,    # TODO: 取消注释，key 换成你在 TOOLS 里填的 name
    "read_file":lambda args:_read_file(args)
}
