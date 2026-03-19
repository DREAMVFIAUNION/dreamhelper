"""代码执行节点 — Python 代码安全沙箱执行（复用现有沙箱）"""

import types
from typing import Any

from ..base_node import BaseNode
from ..types import NodeData, NodeDescriptor


def _make_safe_module(name: str, allowed: dict[str, Any]) -> types.ModuleType:
    """构造只暴露指定函数的代理模块，阻断 __builtins__ 逃逸链"""
    mod = types.ModuleType(name)
    for k, v in allowed.items():
        setattr(mod, k, v)
    return mod


class CodeNode(BaseNode):
    def descriptor(self) -> NodeDescriptor:
        return NodeDescriptor(
            type="code",
            name="Python 代码",
            description="在安全沙箱中执行 Python 代码",
            category="skill",
            icon="Code",
            color="#F59E0B",
            inputs=["input"],
            outputs=["output"],
            config_schema={
                "code": {
                    "type": "code", "label": "Python 代码",
                    "default": "# input_data 变量包含上游数据\n# 将结果赋值给 result 变量\nresult = input_data",
                    "language": "python",
                },
                "timeout": {"type": "number", "label": "超时 (秒)", "default": 10, "min": 1, "max": 60},
            },
        )

    async def execute(self, input_data: NodeData, config: dict[str, Any]) -> NodeData:
        import asyncio
        import json

        code = config.get("code", "")
        timeout = min(max(int(config.get("timeout", 10)), 1), 60)

        if not code.strip():
            return input_data

        # 构建安全执行环境
        safe_globals = {
            "__builtins__": {
                "len": len, "range": range, "enumerate": enumerate,
                "str": str, "int": int, "float": float, "bool": bool,
                "list": list, "dict": dict, "tuple": tuple, "set": set,
                "min": min, "max": max, "sum": sum, "abs": abs, "round": round,
                "sorted": sorted, "reversed": reversed, "zip": zip, "map": map, "filter": filter,
                "isinstance": isinstance, "type": type,
                "print": lambda *args, **kwargs: None,  # 静默 print
                "True": True, "False": False, "None": None,
            },
            "json": _make_safe_module("json", {
                "loads": __import__("json").loads,
                "dumps": __import__("json").dumps,
                "JSONDecodeError": __import__("json").JSONDecodeError,
            }),
            "math": _make_safe_module("math", {
                "pi": __import__("math").pi, "e": __import__("math").e,
                "sqrt": __import__("math").sqrt, "sin": __import__("math").sin,
                "cos": __import__("math").cos, "tan": __import__("math").tan,
                "log": __import__("math").log, "log10": __import__("math").log10,
                "ceil": __import__("math").ceil, "floor": __import__("math").floor,
                "pow": __import__("math").pow, "factorial": __import__("math").factorial,
                "gcd": __import__("math").gcd, "isnan": __import__("math").isnan,
                "isinf": __import__("math").isinf, "fabs": __import__("math").fabs,
            }),
            "re": _make_safe_module("re", {
                "compile": __import__("re").compile, "match": __import__("re").match,
                "search": __import__("re").search, "findall": __import__("re").findall,
                "sub": __import__("re").sub, "split": __import__("re").split,
                "Pattern": __import__("re").Pattern,
            }),
            "datetime": _make_safe_module("datetime", {
                "datetime": __import__("datetime").datetime,
                "date": __import__("datetime").date,
                "time": __import__("datetime").time,
                "timedelta": __import__("datetime").timedelta,
                "timezone": __import__("datetime").timezone,
            }),
        }

        safe_locals: dict[str, Any] = {
            "input_data": input_data.items,
            "metadata": input_data.metadata,
            "result": None,
        }

        try:
            exec_code = compile(code, "<workflow_code>", "exec")
            await asyncio.wait_for(
                asyncio.get_running_loop().run_in_executor(
                    None, exec, exec_code, safe_globals, safe_locals
                ),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"代码执行超时 ({timeout}秒)")
        except Exception as e:
            raise RuntimeError(f"代码执行错误: {type(e).__name__}: {e}")

        result = safe_locals.get("result")
        if isinstance(result, list):
            items = [r if isinstance(r, dict) else {"value": r} for r in result]
        elif isinstance(result, dict):
            items = [result]
        elif result is not None:
            items = [{"value": result}]
        else:
            items = input_data.items

        return NodeData(items=items)
