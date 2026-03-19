"""记账技能 — 简易收支记录与统计"""

from typing import Any, Dict, List
from datetime import datetime, timezone, timedelta

from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema

CST = timezone(timedelta(hours=8))

_records: Dict[str, List[dict]] = {}


class ExpenseSchema(SkillSchema):
    action: str = Field(description="操作: 'add'(记一笔), 'list'(列表), 'summary'(统计), 'clear'(清空)")
    amount: float = Field(default=0, description="金额 (正=收入, 负=支出)")
    category: str = Field(default="其他", description="分类: 餐饮/交通/购物/娱乐/工资/其他")
    note: str = Field(default="", description="备注")
    user_id: str = Field(default="default", description="用户ID")


class ExpenseTrackerSkill(BaseSkill):
    name = "expense_tracker"
    description = "简易记账：记录收支、查看明细、分类统计"
    category = "office"
    args_schema = ExpenseSchema
    tags = ["记账", "支出", "收入", "expense", "finance"]

    async def execute(self, **kwargs: Any) -> str:
        action = kwargs.get("action", "list")
        uid = kwargs.get("user_id", "default")
        if uid not in _records:
            _records[uid] = []

        records = _records[uid]

        if action == "add":
            amount = float(kwargs.get("amount", 0))
            if amount == 0:
                return "金额不能为0"
            record = {
                "amount": amount,
                "category": kwargs.get("category", "其他"),
                "note": kwargs.get("note", ""),
                "time": datetime.now(CST).strftime("%m-%d %H:%M"),
                "type": "收入" if amount > 0 else "支出",
            }
            records.append(record)
            return f"已记录 {record['type']}: ¥{abs(amount):.2f} [{record['category']}] {record['note']}"

        elif action == "list":
            if not records:
                return "暂无记录"
            lines = ["收支记录:"]
            for i, r in enumerate(records[-20:], 1):
                sign = "+" if r["amount"] > 0 else "-"
                lines.append(f"  {i}. {r['time']} {sign}¥{abs(r['amount']):.2f} [{r['category']}] {r['note']}")
            return "\n".join(lines)

        elif action == "summary":
            if not records:
                return "暂无记录"
            income = sum(r["amount"] for r in records if r["amount"] > 0)
            expense = sum(abs(r["amount"]) for r in records if r["amount"] < 0)
            balance = income - expense

            cats: Dict[str, float] = {}
            for r in records:
                if r["amount"] < 0:
                    cats[r["category"]] = cats.get(r["category"], 0) + abs(r["amount"])

            lines = [
                "收支统计:",
                f"  总收入: ¥{income:.2f}",
                f"  总支出: ¥{expense:.2f}",
                f"  结余:   ¥{balance:.2f}",
                f"  记录数: {len(records)} 笔",
            ]
            if cats:
                lines.append("\n支出分类:")
                for cat, total in sorted(cats.items(), key=lambda x: -x[1]):
                    pct = total / expense * 100 if expense > 0 else 0
                    lines.append(f"  {cat}: ¥{total:.2f} ({pct:.0f}%)")
            return "\n".join(lines)

        elif action == "clear":
            count = len(records)
            _records[uid] = []
            return f"已清空 {count} 条记录"

        return f"未知操作: {action}"
