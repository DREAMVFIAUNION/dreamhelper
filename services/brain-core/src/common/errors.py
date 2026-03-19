"""统一错误码体系 — 全局 ErrorCode + 结构化异常（代码审计 P1）

错误码规范:
- ERR_AUTH_xxx: 认证/授权
- ERR_INPUT_xxx: 输入校验
- ERR_LLM_xxx: LLM 调用
- ERR_RAG_xxx: RAG 检索
- ERR_AGENT_xxx: Agent 执行
- ERR_SKILL_xxx: 技能执行
- ERR_VISION_xxx: 视觉分析
- ERR_BROWSER_xxx: 浏览器操作
- ERR_INTERNAL_xxx: 内部错误
"""

from enum import Enum
from typing import Any, Optional


class ErrorCode(str, Enum):
    # 认证
    AUTH_INVALID_TOKEN = "ERR_AUTH_001"
    AUTH_EXPIRED = "ERR_AUTH_002"
    AUTH_FORBIDDEN = "ERR_AUTH_003"

    # 输入校验
    INPUT_MISSING_FIELD = "ERR_INPUT_001"
    INPUT_INVALID_FORMAT = "ERR_INPUT_002"
    INPUT_TOO_LARGE = "ERR_INPUT_003"
    INPUT_UNSAFE_URL = "ERR_INPUT_004"

    # LLM
    LLM_PROVIDER_ERROR = "ERR_LLM_001"
    LLM_RATE_LIMITED = "ERR_LLM_002"
    LLM_TIMEOUT = "ERR_LLM_003"
    LLM_CONTEXT_OVERFLOW = "ERR_LLM_004"

    # RAG
    RAG_RETRIEVAL_FAILED = "ERR_RAG_001"
    RAG_INDEX_ERROR = "ERR_RAG_002"

    # Agent
    AGENT_NOT_FOUND = "ERR_AGENT_001"
    AGENT_EXECUTION_FAILED = "ERR_AGENT_002"
    AGENT_TIMEOUT = "ERR_AGENT_003"

    # 技能
    SKILL_NOT_FOUND = "ERR_SKILL_001"
    SKILL_PARAM_INVALID = "ERR_SKILL_002"
    SKILL_EXEC_FAILED = "ERR_SKILL_003"

    # Vision
    VISION_IMAGE_TOO_LARGE = "ERR_VISION_001"
    VISION_UNSUPPORTED_FORMAT = "ERR_VISION_002"
    VISION_ANALYSIS_FAILED = "ERR_VISION_003"

    # Browser
    BROWSER_UNSAFE_URL = "ERR_BROWSER_001"
    BROWSER_TIMEOUT = "ERR_BROWSER_002"
    BROWSER_NOT_AVAILABLE = "ERR_BROWSER_003"

    # 内部
    INTERNAL_ERROR = "ERR_INTERNAL_001"
    INTERNAL_SERVICE_UNAVAILABLE = "ERR_INTERNAL_002"


class AppError(Exception):
    """统一业务异常基类"""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        detail: Optional[Any] = None,
        status_code: int = 400,
    ):
        self.code = code
        self.message = message
        self.detail = detail
        self.status_code = status_code
        super().__init__(message)

    def to_dict(self) -> dict:
        result = {
            "error": True,
            "code": self.code.value,
            "message": self.message,
        }
        if self.detail is not None:
            result["detail"] = self.detail
        return result


class AuthError(AppError):
    def __init__(self, message: str = "认证失败", code: ErrorCode = ErrorCode.AUTH_INVALID_TOKEN):
        super().__init__(code=code, message=message, status_code=401)


class InputError(AppError):
    def __init__(self, message: str, code: ErrorCode = ErrorCode.INPUT_INVALID_FORMAT, detail: Any = None):
        super().__init__(code=code, message=message, detail=detail, status_code=422)


class LLMError(AppError):
    def __init__(self, message: str, code: ErrorCode = ErrorCode.LLM_PROVIDER_ERROR):
        super().__init__(code=code, message=message, status_code=502)


class AgentError(AppError):
    def __init__(self, message: str, code: ErrorCode = ErrorCode.AGENT_EXECUTION_FAILED):
        super().__init__(code=code, message=message, status_code=500)


class SkillError(AppError):
    def __init__(self, message: str, code: ErrorCode = ErrorCode.SKILL_EXEC_FAILED):
        super().__init__(code=code, message=message, status_code=400)
