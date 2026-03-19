"""计算器工具 — 安全执行数学表达式"""

import ast
import math
import operator
from typing import Any

from pydantic import BaseModel, Field
from ..tool_registry import BaseTool


class CalculatorArgs(BaseModel):
    expression: str = Field(description="数学表达式，如 '2 + 3 * 4' 或 'sqrt(16) + pi'")


# 安全的数学运算符和函数
SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

SAFE_FUNCS = {
    "abs": abs, "round": round, "min": min, "max": max,
    "sqrt": math.sqrt, "log": math.log, "log2": math.log2, "log10": math.log10,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "ceil": math.ceil, "floor": math.floor,
    "pi": math.pi, "e": math.e,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"不支持的常量类型: {type(node.value)}")
    elif isinstance(node, ast.BinOp):
        op = SAFE_OPS.get(type(node.op))
        if not op:
            raise ValueError(f"不支持的运算符: {type(node.op).__name__}")
        return op(_safe_eval(node.left), _safe_eval(node.right))
    elif isinstance(node, ast.UnaryOp):
        op = SAFE_OPS.get(type(node.op))
        if not op:
            raise ValueError(f"不支持的一元运算符: {type(node.op).__name__}")
        return op(_safe_eval(node.operand))
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in SAFE_FUNCS:
            func = SAFE_FUNCS[node.func.id]
            args = [_safe_eval(a) for a in node.args]
            return func(*args)
        raise ValueError(f"不支持的函数: {ast.dump(node.func)}")
    elif isinstance(node, ast.Name):
        if node.id in SAFE_FUNCS:
            val = SAFE_FUNCS[node.id]
            if isinstance(val, (int, float)):
                return val
        raise ValueError(f"未知变量: {node.id}")
    raise ValueError(f"不支持的表达式: {ast.dump(node)}")


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "安全计算数学表达式。支持四则运算、幂运算、sqrt/log/sin/cos/pi/e 等。输入数学表达式字符串。"
    args_schema = CalculatorArgs

    async def execute(self, **kwargs: Any) -> str:
        expr = kwargs.get("expression", "")
        try:
            tree = ast.parse(expr, mode="eval")
            result = _safe_eval(tree)
            if isinstance(result, float) and result == int(result):
                result = int(result)
            return f"{expr} = {result}"
        except Exception as e:
            return f"计算错误: {e}"
