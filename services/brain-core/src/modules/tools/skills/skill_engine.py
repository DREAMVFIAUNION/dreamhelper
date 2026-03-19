"""
技能引擎 — 安全沙箱执行 + 技能注册 + 参数校验

安全限制:
- 执行超时: 10秒
- 输出限制: 10KB
- 禁止 import (技能必须纯函数)
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel


class SkillSchema(BaseModel):
    """技能输入参数 Schema 基类"""
    pass


class BaseSkill(ABC):
    """技能基类"""
    name: str
    description: str
    category: str  # daily, office, coding, document, entertainment
    args_schema: Type[SkillSchema]
    version: str = "1.0.0"
    tags: list[str] = []

    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        ...

    def to_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "tags": self.tags,
            "parameters": self.args_schema.model_json_schema(),
        }


EXECUTION_TIMEOUT = 10  # seconds
MAX_OUTPUT_LENGTH = 10_000  # chars


class SkillEngine:
    """全局技能引擎"""

    _skills: Dict[str, BaseSkill] = {}

    @classmethod
    def register(cls, skill: BaseSkill):
        cls._skills[skill.name] = skill

    @classmethod
    def get(cls, name: str) -> Optional[BaseSkill]:
        return cls._skills.get(name)

    @classmethod
    def list_skills(cls) -> List[dict]:
        return [s.to_schema() for s in cls._skills.values()]

    @classmethod
    def list_by_category(cls, category: str) -> List[dict]:
        return [s.to_schema() for s in cls._skills.values() if s.category == category]

    @classmethod
    def search(cls, query: str) -> List[dict]:
        q = query.lower()
        results = []
        for s in cls._skills.values():
            if q in s.name.lower() or q in s.description.lower() or any(q in t.lower() for t in s.tags):
                results.append(s.to_schema())
        return results

    @classmethod
    def categories(cls) -> Dict[str, int]:
        cats: Dict[str, int] = {}
        for s in cls._skills.values():
            cats[s.category] = cats.get(s.category, 0) + 1
        return cats

    @classmethod
    async def execute(cls, name: str, **kwargs: Any) -> dict:
        """安全执行技能 (带超时和输出限制)"""
        skill = cls._skills.get(name)
        if not skill:
            return {"success": False, "error": f"技能 '{name}' 不存在", "result": None}

        # 参数校验
        try:
            validated = skill.args_schema(**kwargs)
            params = validated.model_dump()
        except Exception as e:
            return {"success": False, "error": f"参数校验失败: {e}", "result": None}

        # 带超时执行
        try:
            result = await asyncio.wait_for(
                skill.execute(**params),
                timeout=EXECUTION_TIMEOUT,
            )

            # 输出截断
            if isinstance(result, str) and len(result) > MAX_OUTPUT_LENGTH:
                result = result[:MAX_OUTPUT_LENGTH] + "\n...(输出已截断)"

            return {"success": True, "error": None, "result": result, "skill": name}

        except asyncio.TimeoutError:
            return {"success": False, "error": f"执行超时 ({EXECUTION_TIMEOUT}s)", "result": None}
        except Exception as e:
            logging.getLogger(__name__).exception("Skill execution failed: %s", name)
            return {"success": False, "error": "技能执行失败", "result": None}
