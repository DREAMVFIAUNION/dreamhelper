"""看板管理 — 简单任务看板 (待办/进行中/完成)"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema

_board: dict[str, list[str]] = {"todo": [], "doing": [], "done": []}

COLUMN_LABELS = {"todo": "📋 待办", "doing": "🔄 进行中", "done": "✅ 完成"}


class KanbanSchema(SkillSchema):
    action: str = Field(description="操作: add(添加)/move(移动)/view(查看)/clear(清空)")
    task: str = Field(default="", description="任务名称")
    target: str = Field(default="todo", description="目标列: todo/doing/done")


class KanbanBoardSkill(BaseSkill):
    name = "kanban_board"
    description = "看板任务管理: 添加、移动、查看任务"
    category = "office"
    args_schema = KanbanSchema
    tags = ["看板", "kanban", "任务", "管理"]

    async def execute(self, **kwargs: Any) -> str:
        action = kwargs.get("action", "view")
        task = kwargs.get("task", "").strip()
        target = kwargs.get("target", "todo")

        if action == "view":
            lines = ["═══ 看板 ═══"]
            for col, items in _board.items():
                label = COLUMN_LABELS.get(col, col)
                lines.append(f"\n{label} ({len(items)})")
                if items:
                    for i, t in enumerate(items, 1):
                        lines.append(f"  {i}. {t}")
                else:
                    lines.append("  (空)")
            total = sum(len(v) for v in _board.values())
            lines.append(f"\n共 {total} 个任务")
            return "\n".join(lines)

        if action == "add":
            if not task:
                return "请指定任务名称"
            _board.setdefault(target, []).append(task)
            return f"已添加 [{task}] 到 {COLUMN_LABELS.get(target, target)}"

        if action == "move":
            if not task:
                return "请指定任务名称"
            if target not in _board:
                return f"无效列: {target}，可用: todo/doing/done"
            for col, items in _board.items():
                if task in items:
                    items.remove(task)
                    _board[target].append(task)
                    return f"已移动 [{task}] → {COLUMN_LABELS.get(target, target)}"
            return f"未找到任务 [{task}]"

        if action == "clear":
            total = sum(len(v) for v in _board.values())
            for v in _board.values():
                v.clear()
            return f"已清空看板 ({total} 个任务)"

        return "不支持的操作: add/move/view/clear"
