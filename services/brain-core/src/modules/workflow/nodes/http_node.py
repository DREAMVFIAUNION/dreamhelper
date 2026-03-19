"""HTTP 请求节点 — 发送 HTTP 请求到外部 API"""

from typing import Any

from ..base_node import BaseNode
from ..types import NodeData, NodeDescriptor


class HttpNode(BaseNode):
    def descriptor(self) -> NodeDescriptor:
        return NodeDescriptor(
            type="http",
            name="HTTP 请求",
            description="发送 HTTP 请求（GET/POST/PUT/DELETE）",
            category="skill",
            icon="Globe",
            color="#F59E0B",
            inputs=["input"],
            outputs=["output"],
            config_schema={
                "url": {"type": "string", "label": "URL", "default": "", "placeholder": "https://api.example.com/data"},
                "method": {"type": "select", "label": "方法", "default": "GET", "options": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                "headers": {"type": "json", "label": "请求头 (JSON)", "default": "{}"},
                "body": {"type": "textarea", "label": "请求体", "default": "", "placeholder": "支持 {{input}} 模板"},
                "timeout": {"type": "number", "label": "超时 (秒)", "default": 30},
            },
        )

    async def execute(self, input_data: NodeData, config: dict[str, Any]) -> NodeData:
        import httpx
        import json

        url = config.get("url", "")
        if not url:
            raise ValueError("URL 不能为空")

        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        if isinstance(headers, str):
            headers = json.loads(headers)
        body_template = config.get("body", "")
        timeout = config.get("timeout", 30)

        # 模板注入
        input_text = ""
        if input_data.items:
            input_text = json.dumps(input_data.items, ensure_ascii=False, default=str)
        url = url.replace("{{input}}", input_text)
        body_str = body_template.replace("{{input}}", input_text) if body_template else ""

        async with httpx.AsyncClient(timeout=float(timeout)) as client:
            kwargs: dict[str, Any] = {"method": method, "url": url, "headers": headers}
            if body_str and method in ("POST", "PUT", "PATCH"):
                try:
                    kwargs["json"] = json.loads(body_str)
                except json.JSONDecodeError:
                    kwargs["content"] = body_str

            resp = await client.request(**kwargs)

        # 解析响应
        try:
            resp_data = resp.json()
        except Exception:
            resp_data = resp.text

        return NodeData(
            items=[{"status": resp.status_code, "data": resp_data}],
            metadata={"url": url, "method": method, "status": resp.status_code},
        )
