"""邮件模板生成器 — 常用商务邮件模板"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema

TEMPLATES = {
    "meeting": "会议邀请",
    "follow_up": "跟进邮件",
    "thank_you": "感谢信",
    "apology": "致歉信",
    "introduction": "自我介绍",
    "leave": "请假申请",
    "resignation": "离职通知",
    "feedback": "反馈请求",
}


class EmailSchema(SkillSchema):
    template: str = Field(description=f"模板类型: {', '.join(TEMPLATES.keys())}")
    recipient: str = Field(default="收件人", description="收件人称呼")
    sender: str = Field(default="发件人", description="发件人名称")
    details: str = Field(default="", description="补充细节(可选)")


class EmailTemplateSkill(BaseSkill):
    name = "email_template"
    description = "生成商务邮件模板: 会议邀请、跟进、感谢、致歉等"
    category = "office"
    args_schema = EmailSchema
    tags = ["邮件", "模板", "email", "商务"]

    async def execute(self, **kwargs: Any) -> str:
        tpl = kwargs["template"].lower()
        to = kwargs.get("recipient", "收件人")
        fr = kwargs.get("sender", "发件人")
        details = kwargs.get("details", "")

        if tpl not in TEMPLATES:
            return f"可用模板: {', '.join(f'{k}({v})' for k, v in TEMPLATES.items())}"

        bodies = {
            "meeting": f"主题: 会议邀请\n\n{to}，您好：\n\n诚邀您参加以下会议：\n  时间: [待定]\n  地点: [待定]\n  议题: {details or '[待定]'}\n\n请确认是否能出席。\n\n此致\n{fr}",
            "follow_up": f"主题: 跟进 - {details or '上次沟通'}\n\n{to}，您好：\n\n关于我们上次讨论的事项，想跟您确认一下进展。{details}\n\n期待您的回复。\n\n此致\n{fr}",
            "thank_you": f"主题: 感谢\n\n{to}，您好：\n\n非常感谢您的{details or '帮助与支持'}。您的付出让工作进展顺利。\n\n再次表示衷心的感谢。\n\n此致\n{fr}",
            "apology": f"主题: 致歉\n\n{to}，您好：\n\n对于{details or '给您带来的不便'}，我深表歉意。我将采取措施确保类似情况不再发生。\n\n敬请谅解。\n\n此致\n{fr}",
            "introduction": f"主题: 自我介绍\n\n{to}，您好：\n\n我是{fr}。{details or '很高兴认识您，期待与您合作。'}\n\n如有任何问题，请随时联系我。\n\n此致\n{fr}",
            "leave": f"主题: 请假申请\n\n{to}，您好：\n\n因{details or '个人原因'}，特此申请请假。\n  请假时间: [待定]\n\n期间工作已做好安排，请批准。\n\n此致\n{fr}",
            "resignation": f"主题: 离职通知\n\n{to}，您好：\n\n经过慎重考虑，我决定辞去当前职位。{details}\n\n感谢公司期间给予的机会和支持。\n\n此致\n{fr}",
            "feedback": f"主题: 反馈请求\n\n{to}，您好：\n\n希望能获得您关于{details or '近期项目'}的反馈意见，以便我们持续改进。\n\n感谢您抽出时间。\n\n此致\n{fr}",
        }

        return f"邮件模板 [{TEMPLATES[tpl]}]:\n\n{bodies[tpl]}"
