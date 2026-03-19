"""日期时间工具 — 全球时间查询、时区转换、日期计算

支持全球 50+ 主要城市时区查询、多时区对比、日期加减和差值计算。
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field
from ..tool_registry import BaseTool


# ── 城市 → IANA 时区映射（50+ 主要城市）──────────────────
CITY_TIMEZONE_MAP: dict[str, str] = {
    # 中国
    "北京": "Asia/Shanghai", "上海": "Asia/Shanghai", "深圳": "Asia/Shanghai",
    "广州": "Asia/Shanghai", "成都": "Asia/Shanghai", "杭州": "Asia/Shanghai",
    "香港": "Asia/Hong_Kong", "台北": "Asia/Taipei",
    # 东亚
    "东京": "Asia/Tokyo", "大阪": "Asia/Tokyo",
    "首尔": "Asia/Seoul", "釜山": "Asia/Seoul",
    # 东南亚
    "新加坡": "Asia/Singapore", "曼谷": "Asia/Bangkok",
    "吉隆坡": "Asia/Kuala_Lumpur", "雅加达": "Asia/Jakarta",
    "马尼拉": "Asia/Manila", "河内": "Asia/Ho_Chi_Minh",
    "胡志明": "Asia/Ho_Chi_Minh",
    # 南亚/中亚
    "孟买": "Asia/Kolkata", "新德里": "Asia/Kolkata",
    "迪拜": "Asia/Dubai", "利雅得": "Asia/Riyadh",
    "伊斯坦布尔": "Europe/Istanbul", "卡拉奇": "Asia/Karachi",
    # 欧洲
    "伦敦": "Europe/London", "巴黎": "Europe/Paris",
    "柏林": "Europe/Berlin", "法兰克福": "Europe/Berlin",
    "阿姆斯特丹": "Europe/Amsterdam", "罗马": "Europe/Rome",
    "马德里": "Europe/Madrid", "苏黎世": "Europe/Zurich",
    "莫斯科": "Europe/Moscow", "华沙": "Europe/Warsaw",
    "维也纳": "Europe/Vienna", "布鲁塞尔": "Europe/Brussels",
    "赫尔辛基": "Europe/Helsinki", "斯德哥尔摩": "Europe/Stockholm",
    "雅典": "Europe/Athens", "都柏林": "Europe/Dublin",
    # 北美
    "纽约": "America/New_York", "洛杉矶": "America/Los_Angeles",
    "芝加哥": "America/Chicago", "旧金山": "America/Los_Angeles",
    "西雅图": "America/Los_Angeles", "休斯顿": "America/Chicago",
    "多伦多": "America/Toronto", "温哥华": "America/Vancouver",
    "华盛顿": "America/New_York", "波士顿": "America/New_York",
    "迈阿密": "America/New_York", "丹佛": "America/Denver",
    "墨西哥城": "America/Mexico_City",
    # 南美
    "圣保罗": "America/Sao_Paulo", "布宜诺斯艾利斯": "America/Argentina/Buenos_Aires",
    "里约": "America/Sao_Paulo", "利马": "America/Lima",
    "波哥大": "America/Bogota", "圣地亚哥": "America/Santiago",
    # 大洋洲
    "悉尼": "Australia/Sydney", "墨尔本": "Australia/Melbourne",
    "奥克兰": "Pacific/Auckland", "惠灵顿": "Pacific/Auckland",
    # 非洲
    "开罗": "Africa/Cairo", "约翰内斯堡": "Africa/Johannesburg",
    "拉各斯": "Africa/Lagos", "内罗毕": "Africa/Nairobi",
    "卡萨布兰卡": "Africa/Casablanca",
    # 英文别名
    "beijing": "Asia/Shanghai", "shanghai": "Asia/Shanghai", "shenzhen": "Asia/Shanghai",
    "tokyo": "Asia/Tokyo", "seoul": "Asia/Seoul", "singapore": "Asia/Singapore",
    "london": "Europe/London", "paris": "Europe/Paris", "berlin": "Europe/Berlin",
    "new york": "America/New_York", "los angeles": "America/Los_Angeles",
    "chicago": "America/Chicago", "san francisco": "America/Los_Angeles",
    "toronto": "America/Toronto", "sydney": "Australia/Sydney",
    "moscow": "Europe/Moscow", "dubai": "Asia/Dubai", "mumbai": "Asia/Kolkata",
    "hong kong": "Asia/Hong_Kong", "taipei": "Asia/Taipei",
}


def _resolve_timezone(tz_input: str) -> ZoneInfo | None:
    """解析时区: 支持城市名 / IANA 时区 / UTC±N"""
    if not tz_input:
        return None
    key = tz_input.strip().lower()
    # 城市名
    if key in CITY_TIMEZONE_MAP:
        return ZoneInfo(CITY_TIMEZONE_MAP[key])
    # IANA 时区名 (如 Asia/Shanghai)
    try:
        return ZoneInfo(tz_input.strip())
    except (KeyError, ValueError):
        pass
    # UTC±N 格式
    import re
    m = re.match(r"^utc([+-]?\d{1,2})(?::?(\d{2}))?$", key)
    if m:
        hours = int(m.group(1))
        mins = int(m.group(2) or 0)
        return timezone(timedelta(hours=hours, minutes=mins))
    return None


TZ_CN = ZoneInfo("Asia/Shanghai")


class DateTimeArgs(BaseModel):
    action: str = Field(
        description=(
            "操作类型: 'now'(当前时间), 'world'(全球多城市时间), "
            "'convert'(时区转换), 'add'(日期加减), 'weekday'(星期几), 'diff'(日期差)"
        )
    )
    timezone: str = Field(
        default="",
        description="时区: 城市名(如'东京','纽约') 或 IANA时区(如'America/New_York') 或 'UTC+8'",
    )
    cities: str = Field(
        default="",
        description="多城市逗号分隔(action=world时用), 如 '北京,东京,纽约,伦敦'",
    )
    time_str: str = Field(
        default="",
        description="源时间字符串 HH:MM 或 YYYY-MM-DD HH:MM (action=convert时用)",
    )
    from_tz: str = Field(default="", description="源时区(action=convert时用)")
    to_tz: str = Field(default="", description="目标时区(action=convert时用)")
    days: int = Field(default=0, description="加减天数 (action=add 时使用)")
    date1: str = Field(default="", description="日期1, 格式 YYYY-MM-DD")
    date2: str = Field(default="", description="日期2, 格式 YYYY-MM-DD")


class DateTimeTool(BaseTool):
    name = "datetime"
    description = (
        "全球日期时间工具。支持:\n"
        "- action=now: 获取当前时间(可指定timezone='东京')\n"
        "- action=world: 全球多城市时间对比(cities='北京,东京,纽约,伦敦')\n"
        "- action=convert: 时区转换(time_str='14:30', from_tz='北京', to_tz='纽约')\n"
        "- action=add: 日期加减(days=N, timezone可选)\n"
        "- action=weekday: 查询星期几(date1=YYYY-MM-DD)\n"
        "- action=diff: 计算日期差(date1=..., date2=...)"
    )
    args_schema = DateTimeArgs

    async def execute(self, **kwargs: Any) -> str:
        action = kwargs.get("action", "now")
        tz_str = kwargs.get("timezone", "")
        tz = _resolve_timezone(tz_str) or TZ_CN
        now = datetime.now(tz)

        if action == "now":
            tz_label = tz_str or "北京"
            return (
                f"🕐 {tz_label}当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')} "
                f"({self._weekday_cn(now)}, {self._tz_display(tz, now)})"
            )

        elif action == "world":
            cities_str = kwargs.get("cities", "北京,东京,纽约,伦敦")
            cities = [c.strip() for c in cities_str.split(",") if c.strip()]
            if not cities:
                cities = ["北京", "东京", "纽约", "伦敦"]
            lines = ["🌍 全球时间对比:"]
            utc_now = datetime.now(timezone.utc)
            for city in cities:
                city_tz = _resolve_timezone(city)
                if city_tz:
                    ct = utc_now.astimezone(city_tz)
                    lines.append(
                        f"  {city:　<6} {ct.strftime('%Y-%m-%d %H:%M:%S')} "
                        f"({self._weekday_cn(ct)}, {self._tz_display(city_tz, ct)})"
                    )
                else:
                    lines.append(f"  {city}: 未知时区")
            return "\n".join(lines)

        elif action == "convert":
            time_str = kwargs.get("time_str", "")
            from_tz_str = kwargs.get("from_tz", "") or "北京"
            to_tz_str = kwargs.get("to_tz", "")
            if not time_str or not to_tz_str:
                return "请提供 time_str(时间) 和 to_tz(目标时区)"
            from_tz = _resolve_timezone(from_tz_str)
            to_tz_obj = _resolve_timezone(to_tz_str)
            if not from_tz or not to_tz_obj:
                return f"无法解析时区: from={from_tz_str}, to={to_tz_str}"
            try:
                if len(time_str) <= 5:
                    # HH:MM 格式 — 用今天的日期
                    base = datetime.now(from_tz)
                    h, m = map(int, time_str.split(":"))
                    src_dt = base.replace(hour=h, minute=m, second=0, microsecond=0)
                else:
                    src_dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M").replace(tzinfo=from_tz)
                dst_dt = src_dt.astimezone(to_tz_obj)
                return (
                    f"🔄 时区转换:\n"
                    f"  {from_tz_str}: {src_dt.strftime('%Y-%m-%d %H:%M')} ({self._weekday_cn(src_dt)})\n"
                    f"  {to_tz_str}: {dst_dt.strftime('%Y-%m-%d %H:%M')} ({self._weekday_cn(dst_dt)})"
                )
            except (ValueError, TypeError) as e:
                return f"时间解析错误: {e}. 格式: HH:MM 或 YYYY-MM-DD HH:MM"

        elif action == "add":
            days = int(kwargs.get("days", 0))
            target = now + timedelta(days=days)
            direction = "后" if days >= 0 else "前"
            return f"{abs(days)}天{direction}: {target.strftime('%Y-%m-%d')} ({self._weekday_cn(target)})"

        elif action == "weekday":
            date_str = kwargs.get("date1", "")
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=TZ_CN)
                return f"{date_str} 是 {self._weekday_cn(dt)}"
            except ValueError:
                return f"日期格式错误: {date_str}，请使用 YYYY-MM-DD 格式"

        elif action == "diff":
            date1 = kwargs.get("date1", "")
            date2 = kwargs.get("date2", "")
            try:
                d1 = datetime.strptime(date1, "%Y-%m-%d")
                d2 = datetime.strptime(date2, "%Y-%m-%d")
                diff = abs((d2 - d1).days)
                return f"{date1} 到 {date2} 相差 {diff} 天"
            except ValueError:
                return "日期格式错误，请使用 YYYY-MM-DD 格式"

        return f"未知操作: {action}"

    @staticmethod
    def _weekday_cn(dt: datetime) -> str:
        names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        return names[dt.weekday()]

    @staticmethod
    def _tz_display(tz: Any, dt: datetime) -> str:
        """生成时区显示文本, 如 UTC+8"""
        offset = dt.utcoffset()
        if offset is None:
            return "UTC"
        total_seconds = int(offset.total_seconds())
        hours, remainder = divmod(abs(total_seconds), 3600)
        mins = remainder // 60
        sign = "+" if total_seconds >= 0 else "-"
        if mins:
            return f"UTC{sign}{hours}:{mins:02d}"
        return f"UTC{sign}{hours}"
