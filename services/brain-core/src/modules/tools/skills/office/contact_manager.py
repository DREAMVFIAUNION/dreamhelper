"""联系人管理器 — vCard 生成与管理"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema

_contacts: list[dict] = []


class ContactSchema(SkillSchema):
    action: str = Field(description="操作: add(添加)/list(列表)/vcard(生成vCard)/clear(清空)")
    name: str = Field(default="", description="姓名")
    phone: str = Field(default="", description="电话")
    email: str = Field(default="", description="邮箱")
    company: str = Field(default="", description="公司(可选)")


class ContactManagerSkill(BaseSkill):
    name = "contact_manager"
    description = "联系人管理: 添加、列表、生成 vCard"
    category = "office"
    args_schema = ContactSchema
    tags = ["联系人", "vCard", "通讯录", "contact"]

    async def execute(self, **kwargs: Any) -> str:
        action = kwargs.get("action", "list")
        name = kwargs.get("name", "").strip()
        phone = kwargs.get("phone", "").strip()
        email = kwargs.get("email", "").strip()
        company = kwargs.get("company", "").strip()

        if action == "add":
            if not name:
                return "请指定联系人姓名"
            contact = {"name": name, "phone": phone, "email": email, "company": company}
            _contacts.append(contact)
            return f"已添加联系人: {name}\n  电话: {phone or '(无)'} | 邮箱: {email or '(无)'}"

        elif action == "list":
            if not _contacts:
                return "暂无联系人"
            lines = [f"联系人列表 ({len(_contacts)} 人):"]
            for i, c in enumerate(_contacts, 1):
                lines.append(f"  {i}. {c['name']} | {c['phone'] or '-'} | {c['email'] or '-'}")
            return "\n".join(lines)

        elif action == "vcard":
            target = None
            for c in _contacts:
                if c["name"] == name:
                    target = c
                    break
            if not target and name:
                target = {"name": name, "phone": phone, "email": email, "company": company}

            if not target:
                return "请指定联系人姓名"

            vcard = [
                "BEGIN:VCARD",
                "VERSION:3.0",
                f"FN:{target['name']}",
            ]
            if target.get("phone"):
                vcard.append(f"TEL:{target['phone']}")
            if target.get("email"):
                vcard.append(f"EMAIL:{target['email']}")
            if target.get("company"):
                vcard.append(f"ORG:{target['company']}")
            vcard.append("END:VCARD")

            return f"vCard:\n" + "\n".join(vcard)

        elif action == "clear":
            count = len(_contacts)
            _contacts.clear()
            return f"已清空 {count} 个联系人"

        return "不支持的操作: add/list/vcard/clear"
