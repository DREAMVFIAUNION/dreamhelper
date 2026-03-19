"""单位转换技能 — 长度/重量/温度/面积/体积/速度"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema

_CONVERSIONS = {
    "length": {
        "m": 1, "km": 1000, "cm": 0.01, "mm": 0.001, "um": 1e-6,
        "mile": 1609.344, "yard": 0.9144, "foot": 0.3048, "ft": 0.3048, "inch": 0.0254,
        "li": 500, "zhang": 3.333, "chi": 0.333, "cun": 0.0333,
    },
    "weight": {
        "kg": 1, "g": 0.001, "mg": 1e-6, "t": 1000, "ton": 1000,
        "lb": 0.453592, "oz": 0.0283495,
        "jin": 0.5, "liang": 0.05,
    },
    "area": {
        "m2": 1, "km2": 1e6, "cm2": 1e-4, "ha": 1e4, "acre": 4046.86,
        "mu": 666.667, "sqft": 0.0929, "sqmi": 2.59e6,
    },
    "volume": {
        "l": 1, "ml": 0.001, "m3": 1000, "cm3": 0.001,
        "gallon": 3.78541, "quart": 0.946353, "pint": 0.473176, "cup": 0.236588,
    },
    "speed": {
        "m/s": 1, "km/h": 0.277778, "mph": 0.44704, "knot": 0.514444,
    },
}


def _convert_temp(value: float, from_u: str, to_u: str) -> float:
    f, t = from_u.lower(), to_u.lower()
    # 先转为 Celsius
    if f in ("f", "fahrenheit"):
        c = (value - 32) * 5 / 9
    elif f in ("k", "kelvin"):
        c = value - 273.15
    else:
        c = value
    # 再转为目标
    if t in ("f", "fahrenheit"):
        return c * 9 / 5 + 32
    elif t in ("k", "kelvin"):
        return c + 273.15
    return c


class UnitConvertSchema(SkillSchema):
    value: float = Field(description="要转换的数值")
    from_unit: str = Field(description="源单位，如 km, lb, celsius")
    to_unit: str = Field(description="目标单位，如 mile, kg, fahrenheit")


class UnitConverterSkill(BaseSkill):
    name = "unit_converter"
    description = "单位转换：长度/重量/温度/面积/体积/速度，支持中英制"
    category = "daily"
    args_schema = UnitConvertSchema
    tags = ["单位", "转换", "unit", "convert"]

    async def execute(self, **kwargs: Any) -> str:
        value = float(kwargs["value"])
        from_u = kwargs["from_unit"].lower().strip()
        to_u = kwargs["to_unit"].lower().strip()

        # 温度特殊处理
        temp_units = {"c", "celsius", "f", "fahrenheit", "k", "kelvin"}
        if from_u in temp_units and to_u in temp_units:
            result = _convert_temp(value, from_u, to_u)
            return f"{value} {from_u} = {result:.2f} {to_u}"

        # 通用转换
        for cat, units in _CONVERSIONS.items():
            if from_u in units and to_u in units:
                base = value * units[from_u]
                result = base / units[to_u]
                return f"{value} {from_u} = {result:.6g} {to_u}"

        return f"不支持的转换: {from_u} → {to_u}"
