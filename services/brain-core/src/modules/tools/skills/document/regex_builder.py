"""正则表达式构建器 — 常用正则库 + 解释器"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import re

COMMON_PATTERNS = {
    "email": (r'[\w.+-]+@[\w-]+\.[\w.]+', "邮箱地址"),
    "phone_cn": (r'1[3-9]\d{9}', "中国手机号"),
    "url": (r'https?://[^\s<>"{}|\\^`\[\]]+', "URL 链接"),
    "ip": (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', "IPv4 地址"),
    "date": (r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', "日期 YYYY-MM-DD"),
    "time": (r'\d{1,2}:\d{2}(?::\d{2})?', "时间 HH:MM"),
    "chinese": (r'[\u4e00-\u9fff]+', "中文字符"),
    "number": (r'-?\d+\.?\d*', "数字(含小数/负数)"),
    "hex_color": (r'#[0-9a-fA-F]{3,8}', "HEX 颜色"),
    "id_card": (r'\d{17}[\dXx]', "身份证号"),
}


class RegexSchema(SkillSchema):
    action: str = Field(description="操作: list(列表)/test(测试)/extract(提取)")
    pattern: str = Field(default="", description="正则表达式或预设名称")
    text: str = Field(default="", description="测试文本(test/extract时需要)")


class RegexBuilderSkill(BaseSkill):
    name = "regex_builder"
    description = "正则表达式工具: 常用正则库、测试、文本提取"
    category = "document"
    args_schema = RegexSchema
    tags = ["正则", "regex", "提取", "匹配"]

    async def execute(self, **kwargs: Any) -> str:
        action = kwargs.get("action", "list")
        pattern = kwargs.get("pattern", "").strip()
        text = kwargs.get("text", "")

        if action == "list":
            lines = ["常用正则表达式库:"]
            for name, (pat, desc) in COMMON_PATTERNS.items():
                lines.append(f"  {name}: {desc}\n    {pat}")
            return "\n".join(lines)

        # 获取正则
        if pattern in COMMON_PATTERNS:
            regex_str = COMMON_PATTERNS[pattern][0]
        else:
            regex_str = pattern

        if not regex_str:
            return "请指定正则表达式或预设名称"

        try:
            compiled = re.compile(regex_str)
        except re.error as e:
            return f"正则表达式错误: {e}"

        if action == "test":
            if not text:
                return "请提供测试文本"
            matches = compiled.findall(text)
            if matches:
                return f"匹配结果 ({len(matches)} 个):\n  " + "\n  ".join(str(m) for m in matches[:20])
            return "未匹配到任何内容"

        if action == "extract":
            if not text:
                return "请提供文本"
            matches = compiled.findall(text)
            return f"提取结果 ({len(matches)} 个):\n" + "\n".join(f"  {i+1}. {m}" for i, m in enumerate(matches[:30]))

        return "不支持的操作: list/test/extract"
