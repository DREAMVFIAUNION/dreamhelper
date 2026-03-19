"""数独求解器 — 回溯法"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema


class SudokuSchema(SkillSchema):
    puzzle: str = Field(description="数独谜题，9行用换行分隔，0或.表示空格，如: 530070000\\n600195000\\n...")


class SudokuSolverSkill(BaseSkill):
    name = "sudoku_solver"
    description = "回溯法数独求解器"
    category = "entertainment"
    args_schema = SudokuSchema
    tags = ["数独", "sudoku", "求解", "游戏"]

    async def execute(self, **kwargs: Any) -> str:
        raw = kwargs["puzzle"].strip()
        lines = raw.replace(".", "0").split("\n")
        lines = [l.strip() for l in lines if l.strip()]

        if len(lines) != 9:
            return f"需要 9 行数据，当前 {len(lines)} 行"

        grid = []
        for line in lines:
            digits = [int(c) for c in line if c.isdigit()]
            if len(digits) != 9:
                return f"每行需要 9 个数字，发现: {line}"
            grid.append(digits)

        # 验证初始状态
        def is_valid(g: list[list[int]], r: int, c: int, num: int) -> bool:
            if num in g[r]:
                return False
            if any(g[i][c] == num for i in range(9)):
                return False
            br, bc = 3 * (r // 3), 3 * (c // 3)
            for i in range(br, br + 3):
                for j in range(bc, bc + 3):
                    if g[i][j] == num:
                        return False
            return True

        def solve(g: list[list[int]]) -> bool:
            for r in range(9):
                for c in range(9):
                    if g[r][c] == 0:
                        for num in range(1, 10):
                            if is_valid(g, r, c, num):
                                g[r][c] = num
                                if solve(g):
                                    return True
                                g[r][c] = 0
                        return False
            return True

        # 复制网格
        solution = [row[:] for row in grid]
        if not solve(solution):
            return "此数独无解"

        # 格式化输出
        lines_out = ["数独解法:"]
        for r in range(9):
            row_str = ""
            for c in range(9):
                if c > 0 and c % 3 == 0:
                    row_str += "│"
                row_str += str(solution[r][c])
            lines_out.append(f"  {row_str}")
            if r < 8 and (r + 1) % 3 == 0:
                lines_out.append("  ───┼───┼───")

        empty_count = sum(row.count(0) for row in grid)
        lines_out.append(f"\n  填入 {empty_count} 个空格")
        return "\n".join(lines_out)
