"""安全计算器技能 — AST 安全求值，支持基本数学运算"""

import ast
import math
import operator
from typing import Any

from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema

_SAFE_OPS = {
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

_SAFE_FUNCS = {
    "abs": abs, "round": round, "int": int, "float": float,
    "sqrt": math.sqrt, "log": math.log, "log10": math.log10, "log2": math.log2,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "pi": math.pi, "e": math.e,
    "ceil": math.ceil, "floor": math.floor,
    "pow": pow, "max": max, "min": min,
}


def _safe_eval(expr: str) -> float:
    """AST 安全求值，仅允许数学运算"""
    tree = ast.parse(expr, mode="eval")

    def _eval(node: ast.expr) -> Any:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"不支持的常量: {node.value}")
        elif isinstance(node, ast.BinOp):
            op = _SAFE_OPS.get(type(node.op))
            if not op:
                raise ValueError(f"不支持的运算符: {type(node.op).__name__}")
            return op(_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            op = _SAFE_OPS.get(type(node.op))
            if not op:
                raise ValueError(f"不支持的运算符: {type(node.op).__name__}")
            return op(_eval(node.operand))
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _SAFE_FUNCS:
                func = _SAFE_FUNCS[node.func.id]
                if callable(func):
                    args = [_eval(a) for a in node.args]
                    return func(*args)
            raise ValueError(f"不支持的函数: {ast.dump(node.func)}")
        elif isinstance(node, ast.Name):
            if node.id in _SAFE_FUNCS:
                val = _SAFE_FUNCS[node.id]
                if not callable(val):
                    return val
            raise ValueError(f"不支持的变量: {node.id}")
        raise ValueError(f"不支持的表达式: {type(node).__name__}")

    return _eval(tree)


class CalcSchema(SkillSchema):
    expression: str = Field(description="数学表达式，如 '2+3*4' 或 'sqrt(144)'")


class CalculatorSkill(BaseSkill):
    name = "calculator"
    description = "安全计算器，支持加减乘除、幂运算、三角函数、对数等数学运算"
    category = "daily"
    args_schema = CalcSchema
    tags = ["计算", "数学", "math", "calc"]

    async def execute(self, **kwargs: Any) -> str:
        expr = kwargs.get("expression", "")
        if not expr:
            return "请输入数学表达式"
        try:
            result = _safe_eval(expr)
            if isinstance(result, float) and result == int(result):
                result = int(result)
            return f"{expr} = {result}"
        except Exception as e:
            return f"计算错误: {e}"
