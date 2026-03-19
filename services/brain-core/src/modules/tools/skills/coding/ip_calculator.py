"""IP 子网计算器 — CIDR/子网掩码计算"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import ipaddress


class IpSchema(SkillSchema):
    cidr: str = Field(description="IP地址/CIDR，如: 192.168.1.0/24 或 10.0.0.1/16")


class IpCalculatorSkill(BaseSkill):
    name = "ip_calculator"
    description = "IP 子网计算: 网络地址、广播地址、主机范围、子网掩码"
    category = "coding"
    args_schema = IpSchema
    tags = ["IP", "子网", "CIDR", "网络", "network"]

    async def execute(self, **kwargs: Any) -> str:
        cidr = kwargs["cidr"].strip()
        try:
            net = ipaddress.ip_network(cidr, strict=False)
        except ValueError as e:
            return f"无效的 CIDR: {cidr}\n错误: {e}"

        hosts = list(net.hosts())
        first_host = str(hosts[0]) if hosts else "N/A"
        last_host = str(hosts[-1]) if hosts else "N/A"

        return (
            f"IP 子网计算 [{cidr}]:\n"
            f"  网络地址: {net.network_address}\n"
            f"  广播地址: {net.broadcast_address}\n"
            f"  子网掩码: {net.netmask}\n"
            f"  反掩码:   {net.hostmask}\n"
            f"  CIDR:     /{net.prefixlen}\n"
            f"  主机范围: {first_host} - {last_host}\n"
            f"  可用主机: {net.num_addresses - 2 if net.num_addresses > 2 else net.num_addresses}\n"
            f"  总地址数: {net.num_addresses}\n"
            f"  私有网络: {'是' if net.is_private else '否'}"
        )
