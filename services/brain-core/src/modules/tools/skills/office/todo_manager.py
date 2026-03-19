"""待办管理技能 — 内存 TODO 列表 CRUD"""

from typing import Any, Dict, List
from datetime import datetime, timezone, timedelta

from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema

CST = timezone(timedelta(hours=8))

# 内存存储 (按 user 隔离)
_todos: Dict[str, List[dict]] = {}
_counter: Dict[str, int] = {}


class TodoSchema(SkillSchema):
    action: str = Field(description="操作: 'add'(添加), 'list'(列表), 'done'(完成), 'delete'(删除), 'clear'(清空)")
    title: str = Field(default="", description="待办标题 (action=add)")
    priority: str = Field(default="medium", description="优先级: high/medium/low (action=add)")
    todo_id: int = Field(default=0, description="待办ID (action=done/delete)")
    user_id: str = Field(default="default", description="用户ID")


class TodoManagerSkill(BaseSkill):
    name = "todo_manager"
    description = "待办事项管理：添加、列表、标记完成、删除、清空"
    category = "office"
    args_schema = TodoSchema
    tags = ["待办", "TODO", "任务", "task"]

    async def execute(self, **kwargs: Any) -> str:
        action = kwargs.get("action", "list")
        uid = kwargs.get("user_id", "default")

        if uid not in _todos:
            _todos[uid] = []
            _counter[uid] = 0

        todos = _todos[uid]

        if action == "add":
            title = kwargs.get("title", "").strip()
            if not title:
                return "请提供待办标题"
            _counter[uid] += 1
            todo = {
                "id": _counter[uid],
                "title": title,
                "priority": kwargs.get("priority", "medium"),
                "done": False,
                "created": datetime.now(CST).strftime("%m-%d %H:%M"),
            }
            todos.append(todo)
            return f"已添加待办 #{todo['id']}: {title} [{todo['priority']}]"

        elif action == "list":
            if not todos:
                return "待办列表为空"
            lines = ["待办列表:"]
            priority_order = {"high": 0, "medium": 1, "low": 2}
            sorted_todos = sorted(todos, key=lambda t: (t["done"], priority_order.get(t["priority"], 1)))
            for t in sorted_todos:
                status = "✓" if t["done"] else "○"
                p = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(t["priority"], "")
                lines.append(f"  {status} #{t['id']} {p} {t['title']} ({t['created']})")
            done_count = sum(1 for t in todos if t["done"])
            lines.append(f"\n总计: {len(todos)} 项 | 已完成: {done_count}")
            return "\n".join(lines)

        elif action == "done":
            tid = int(kwargs.get("todo_id", 0))
            for t in todos:
                if t["id"] == tid:
                    t["done"] = True
                    return f"已完成: #{tid} {t['title']}"
            return f"未找到待办 #{tid}"

        elif action == "delete":
            tid = int(kwargs.get("todo_id", 0))
            for i, t in enumerate(todos):
                if t["id"] == tid:
                    removed = todos.pop(i)
                    return f"已删除: #{tid} {removed['title']}"
            return f"未找到待办 #{tid}"

        elif action == "clear":
            count = len(todos)
            _todos[uid] = []
            return f"已清空 {count} 项待办"

        return f"未知操作: {action}"
