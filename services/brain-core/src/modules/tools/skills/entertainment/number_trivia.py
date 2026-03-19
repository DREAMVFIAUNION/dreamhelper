"""数字趣闻 — 数学属性检测"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import math


class NumberSchema(SkillSchema):
    number: int = Field(description="要分析的数字")


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def _is_palindrome(n: int) -> bool:
    s = str(abs(n))
    return s == s[::-1]


def _is_perfect(n: int) -> bool:
    if n < 2:
        return False
    return sum(i for i in range(1, n) if n % i == 0) == n


def _fibonacci_check(n: int) -> bool:
    if n < 0:
        return False
    a = 5 * n * n + 4
    b = 5 * n * n - 4
    return math.isqrt(a) ** 2 == a or math.isqrt(b) ** 2 == b


def _factors(n: int) -> list[int]:
    n = abs(n)
    if n == 0:
        return []
    return [i for i in range(1, n + 1) if n % i == 0]


class NumberTriviaSkill(BaseSkill):
    name = "number_trivia"
    description = "数字趣闻: 质数检测、回文数、完美数、斐波那契等"
    category = "entertainment"
    args_schema = NumberSchema
    tags = ["数字", "数学", "质数", "trivia"]

    async def execute(self, **kwargs: Any) -> str:
        n = int(kwargs["number"])
        props = []

        if _is_prime(n):
            props.append("✓ 质数")
        if _is_palindrome(n):
            props.append("✓ 回文数")
        if _is_perfect(n):
            props.append("✓ 完美数")
        if _fibonacci_check(n):
            props.append("✓ 斐波那契数")
        if n > 0 and math.isqrt(n) ** 2 == n:
            props.append(f"✓ 完全平方数 ({math.isqrt(n)}²)")
        if n % 2 == 0:
            props.append("✓ 偶数")
        else:
            props.append("✓ 奇数")

        factors = _factors(n)
        binary = bin(n) if n >= 0 else f"-{bin(abs(n))}"
        hex_val = hex(n) if n >= 0 else f"-{hex(abs(n))}"

        lines = [
            f"数字分析 [{n}]:",
            f"  属性: {' | '.join(props)}",
            f"  因数: {', '.join(str(f) for f in factors[:15])}" + ("..." if len(factors) > 15 else ""),
            f"  二进制: {binary}",
            f"  十六进制: {hex_val}",
            f"  因数个数: {len(factors)}",
        ]

        return "\n".join(lines)
