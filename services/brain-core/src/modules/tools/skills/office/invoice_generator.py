"""发票/报价单生成器 — 文本格式发票"""

from typing import Any
from datetime import datetime
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema


class InvoiceSchema(SkillSchema):
    items: str = Field(description="项目列表，格式: 名称|数量|单价，多个用分号分隔")
    client: str = Field(default="客户", description="客户名称")
    tax_rate: float = Field(default=0, description="税率百分比(默认0)")


class InvoiceGeneratorSkill(BaseSkill):
    name = "invoice_generator"
    description = "生成文本格式发票/报价单"
    category = "office"
    args_schema = InvoiceSchema
    tags = ["发票", "报价", "invoice", "账单"]

    async def execute(self, **kwargs: Any) -> str:
        raw = kwargs["items"].strip()
        client = kwargs.get("client", "客户")
        tax_rate = float(kwargs.get("tax_rate", 0))

        entries = []
        for item in raw.split(";"):
            parts = [p.strip() for p in item.strip().split("|")]
            if len(parts) != 3:
                continue
            name = parts[0]
            try:
                qty = float(parts[1])
                price = float(parts[2])
            except ValueError:
                continue
            entries.append((name, qty, price))

        if not entries:
            return "请输入项目，格式: 名称|数量|单价;名称|数量|单价"

        now = datetime.now().strftime("%Y-%m-%d")
        inv_no = f"INV-{datetime.now().strftime('%Y%m%d%H%M')}"

        lines = [
            "╔═══════════════════════════════════╗",
            f"         发 票 / 报 价 单",
            "╚═══════════════════════════════════╝",
            f"编号: {inv_no}        日期: {now}",
            f"客户: {client}",
            "───────────────────────────────────",
            f"{'项目':<12} {'数量':>6} {'单价':>8} {'小计':>8}",
            "───────────────────────────────────",
        ]

        subtotal = 0
        for name, qty, price in entries:
            total = qty * price
            subtotal += total
            lines.append(f"{name:<12} {qty:>6.0f} {price:>8.2f} {total:>8.2f}")

        tax = subtotal * tax_rate / 100
        grand = subtotal + tax

        lines.append("───────────────────────────────────")
        lines.append(f"{'小计':>28} {subtotal:>8.2f}")
        if tax_rate > 0:
            lines.append(f"{'税额':>26}({tax_rate:.0f}%) {tax:>8.2f}")
        lines.append(f"{'总计':>28} {grand:>8.2f}")

        return "\n".join(lines)
