"""全球天气工具 — Open-Meteo API (完全免费, 零 API Key)

数据源:
  - 天气: https://api.open-meteo.com/v1/forecast
  - 地理编码: https://geocoding-api.open-meteo.com/v1/search
"""

import logging
from typing import Any

import httpx
from pydantic import BaseModel, Field
from ..tool_registry import BaseTool

_HEADERS = {
    "User-Agent": "DreamHelper/3.4 (weather-tool)",
    "Accept": "application/json",
}

# WMO 天气代码 → 中文描述
WMO_CODES: dict[int, str] = {
    0: "晴天☀️", 1: "大部晴朗🌤", 2: "多云⛅", 3: "阴天☁️",
    45: "雾🌫", 48: "霜雾🌫",
    51: "小毛毛雨🌦", 53: "毛毛雨🌦", 55: "大毛毛雨🌧",
    56: "冻毛毛雨🌧", 57: "冻雨🌧",
    61: "小雨🌧", 63: "中雨🌧", 65: "大雨🌧",
    66: "冻小雨🌧", 67: "冻大雨🌧",
    71: "小雪🌨", 73: "中雪🌨", 75: "大雪🌨",
    77: "雪粒❄️",
    80: "阵雨🌦", 81: "中阵雨🌦", 82: "大阵雨⛈",
    85: "小阵雪🌨", 86: "大阵雪🌨",
    95: "雷暴⛈", 96: "雷暴+小冰雹⛈", 99: "雷暴+大冰雹⛈",
}


class WeatherArgs(BaseModel):
    action: str = Field(
        default="current",
        description="操作: 'current'(当前天气), 'forecast'(7天预报), 'hourly'(24h逐时)",
    )
    city: str = Field(default="", description="城市名(中文或英文), 如 '深圳', 'Tokyo', 'New York'")
    lat: float = Field(default=0.0, description="纬度(可选, 与lon一起使用替代city)")
    lon: float = Field(default=0.0, description="经度(可选)")


class WeatherTool(BaseTool):
    name = "weather"
    description = (
        "全球天气查询工具(免费无Key)。支持:\n"
        "- action=current: 当前天气(温度/湿度/风速/天气状况)\n"
        "- action=forecast: 7天天气预报\n"
        "- action=hourly: 未来24小时逐时天气\n"
        "输入城市名如 city='深圳' 或经纬度 lat=22.54, lon=114.06"
    )
    args_schema = WeatherArgs

    async def execute(self, **kwargs: Any) -> str:
        action = kwargs.get("action", "current")
        city = kwargs.get("city", "")
        lat = float(kwargs.get("lat", 0))
        lon = float(kwargs.get("lon", 0))

        # 如果指定城市名，先做地理编码
        if city and (lat == 0 and lon == 0):
            geo = await self._geocode(city)
            if not geo:
                return f"❌ 找不到城市: {city}"
            lat, lon, city = geo["lat"], geo["lon"], geo["name"]

        if lat == 0 and lon == 0:
            return "请提供城市名(city)或经纬度(lat/lon)"

        try:
            if action == "current":
                return await self._current(city, lat, lon)
            elif action == "forecast":
                return await self._forecast(city, lat, lon)
            elif action == "hourly":
                return await self._hourly(city, lat, lon)
            else:
                return f"未知操作: {action}"
        except Exception as e:
            logging.getLogger(__name__).exception("Weather query failed")
            return "❌ 天气查询失败"

    async def _geocode(self, city: str) -> dict | None:
        """城市名 → 经纬度"""
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": city, "count": 1, "language": "zh", "format": "json"}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params, headers=_HEADERS)
            resp.raise_for_status()
            data = resp.json()
        results = data.get("results", [])
        if not results:
            return None
        r = results[0]
        return {
            "lat": r["latitude"],
            "lon": r["longitude"],
            "name": r.get("name", city),
            "country": r.get("country", ""),
            "admin": r.get("admin1", ""),
        }

    async def _current(self, city: str, lat: float, lon: float) -> str:
        """当前天气"""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                       "weather_code,wind_speed_10m,wind_direction_10m,"
                       "precipitation,uv_index",
            "timezone": "auto",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params, headers=_HEADERS)
            resp.raise_for_status()
            data = resp.json()

        c = data.get("current", {})
        wmo = int(c.get("weather_code", 0))
        weather_desc = WMO_CODES.get(wmo, f"代码{wmo}")

        return (
            f"🌤 {city} 当前天气:\n"
            f"  天气: {weather_desc}\n"
            f"  温度: {c.get('temperature_2m', '?')}°C (体感 {c.get('apparent_temperature', '?')}°C)\n"
            f"  湿度: {c.get('relative_humidity_2m', '?')}%\n"
            f"  风速: {c.get('wind_speed_10m', '?')} km/h\n"
            f"  降水: {c.get('precipitation', 0)} mm\n"
            f"  紫外线指数: {c.get('uv_index', '?')}"
        )

    async def _forecast(self, city: str, lat: float, lon: float) -> str:
        """7天预报"""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat, "longitude": lon,
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                     "precipitation_sum,wind_speed_10m_max,uv_index_max",
            "timezone": "auto",
            "forecast_days": 7,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params, headers=_HEADERS)
            resp.raise_for_status()
            data = resp.json()

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        lines = [f"📅 {city} 7天天气预报:"]
        for i, date in enumerate(dates):
            wmo = int(daily["weather_code"][i])
            desc = WMO_CODES.get(wmo, f"代码{wmo}")
            t_max = daily["temperature_2m_max"][i]
            t_min = daily["temperature_2m_min"][i]
            precip = daily["precipitation_sum"][i]
            lines.append(
                f"  {date} {desc}  {t_min}~{t_max}°C  降水{precip}mm"
            )
        return "\n".join(lines)

    async def _hourly(self, city: str, lat: float, lon: float) -> str:
        """24小时逐时"""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat, "longitude": lon,
            "hourly": "temperature_2m,weather_code,precipitation_probability",
            "timezone": "auto",
            "forecast_hours": 24,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params, headers=_HEADERS)
            resp.raise_for_status()
            data = resp.json()

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        lines = [f"⏱ {city} 未来24小时天气:"]
        for i, t in enumerate(times[:24]):
            hour = t.split("T")[1] if "T" in t else t
            wmo = int(hourly["weather_code"][i])
            desc = WMO_CODES.get(wmo, "?")
            temp = hourly["temperature_2m"][i]
            rain = hourly.get("precipitation_probability", [0] * 24)[i]
            lines.append(f"  {hour} {desc} {temp}°C 降水概率{rain}%")
        return "\n".join(lines)
