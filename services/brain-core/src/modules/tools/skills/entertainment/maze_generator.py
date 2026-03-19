"""迷宫生成器 — DFS 生成 + BFS 求解"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import random
from collections import deque


class MazeSchema(SkillSchema):
    width: int = Field(default=11, description="宽度(奇数, 7-21)")
    height: int = Field(default=11, description="高度(奇数, 7-21)")
    solve: bool = Field(default=True, description="是否显示解法路径")


class MazeGeneratorSkill(BaseSkill):
    name = "maze_generator"
    description = "DFS 迷宫生成 + BFS 求解，ASCII 可视化"
    category = "entertainment"
    args_schema = MazeSchema
    tags = ["迷宫", "maze", "生成", "求解", "游戏"]

    async def execute(self, **kwargs: Any) -> str:
        w = min(21, max(7, int(kwargs.get("width", 11)))) | 1
        h = min(21, max(7, int(kwargs.get("height", 11)))) | 1
        do_solve = kwargs.get("solve", True)

        # 初始化网格 (1=墙, 0=路)
        grid = [[1] * w for _ in range(h)]

        # DFS 生成
        def carve(x: int, y: int) -> None:
            grid[y][x] = 0
            dirs = [(0, -2), (0, 2), (-2, 0), (2, 0)]
            random.shuffle(dirs)
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] == 1:
                    grid[y + dy // 2][x + dx // 2] = 0
                    carve(nx, ny)

        import sys
        old_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(max(old_limit, w * h + 100))
        carve(1, 1)
        sys.setrecursionlimit(old_limit)

        # 入口和出口
        start = (1, 0)
        end = (w - 2, h - 1)
        grid[0][1] = 0
        grid[h - 1][w - 2] = 0

        # BFS 求解
        path_set: set[tuple[int, int]] = set()
        if do_solve:
            visited: set[tuple[int, int]] = set()
            parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
            queue: deque[tuple[int, int]] = deque([start])
            visited.add(start)
            found = False
            while queue and not found:
                cx, cy = queue.popleft()
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited and grid[ny][nx] == 0:
                        visited.add((nx, ny))
                        parent[(nx, ny)] = (cx, cy)
                        queue.append((nx, ny))
                        if (nx, ny) == end:
                            found = True
                            break
            if found:
                pos: tuple[int, int] | None = end
                while pos is not None:
                    path_set.add(pos)
                    pos = parent.get(pos)

        # 渲染
        lines = []
        for y in range(h):
            row = ""
            for x in range(w):
                if (x, y) == start:
                    row += "S"
                elif (x, y) == end:
                    row += "E"
                elif (x, y) in path_set:
                    row += "·"
                elif grid[y][x] == 1:
                    row += "█"
                else:
                    row += " "
            lines.append(row)

        maze_str = "\n".join(lines)
        return f"迷宫 ({w}x{h}){'  [含解法路径]' if do_solve and path_set else ''}:\n{maze_str}"
