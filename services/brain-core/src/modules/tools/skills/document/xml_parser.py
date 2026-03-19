"""XML 解析器 — 简易 XML 解析与查询"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import xml.etree.ElementTree as ET


class XmlSchema(SkillSchema):
    xml: str = Field(description="XML 文本")
    xpath: str = Field(default="", description="XPath 查询(可选)，如: .//item")


class XmlParserSkill(BaseSkill):
    name = "xml_parser"
    description = "解析 XML 数据，支持 XPath 查询"
    category = "document"
    args_schema = XmlSchema
    tags = ["XML", "解析", "XPath", "数据"]

    async def execute(self, **kwargs: Any) -> str:
        xml_text = kwargs["xml"].strip()
        xpath = kwargs.get("xpath", "").strip()

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            return f"XML 解析失败: {e}"

        if xpath:
            try:
                elements = root.findall(xpath)
            except Exception as e:
                return f"XPath 查询错误: {e}"
            if not elements:
                return f"XPath '{xpath}' 未匹配到任何元素"
            lines = [f"XPath 查询结果 ({len(elements)} 个):"]
            for el in elements[:20]:
                attrs = " ".join(f'{k}="{v}"' for k, v in el.attrib.items())
                text = (el.text or "").strip()[:80]
                lines.append(f"  <{el.tag}{' ' + attrs if attrs else ''}> {text}")
            return "\n".join(lines)

        # 概览
        def count_elements(el: ET.Element) -> int:
            return 1 + sum(count_elements(c) for c in el)

        total = count_elements(root)
        children = [c.tag for c in root]
        unique_tags = set()

        def collect_tags(el: ET.Element) -> None:
            unique_tags.add(el.tag)
            for c in el:
                collect_tags(c)

        collect_tags(root)

        return (
            f"XML 解析结果:\n"
            f"  根元素: <{root.tag}>\n"
            f"  总元素数: {total}\n"
            f"  唯一标签: {len(unique_tags)} ({', '.join(list(unique_tags)[:10])})\n"
            f"  直接子元素: {len(children)} ({', '.join(children[:8])})"
        )
