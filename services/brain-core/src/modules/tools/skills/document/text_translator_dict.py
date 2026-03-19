"""简易词典翻译 — 内置常用中英词汇"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import re

# 内置常用词典 (精简版)
DICT_EN_CN = {
    "hello": "你好", "world": "世界", "computer": "计算机", "program": "程序",
    "function": "函数", "variable": "变量", "class": "类", "object": "对象",
    "string": "字符串", "number": "数字", "array": "数组", "list": "列表",
    "dictionary": "字典", "database": "数据库", "server": "服务器", "client": "客户端",
    "network": "网络", "internet": "互联网", "algorithm": "算法", "data": "数据",
    "file": "文件", "folder": "文件夹", "memory": "内存", "process": "进程",
    "thread": "线程", "error": "错误", "exception": "异常", "debug": "调试",
    "test": "测试", "deploy": "部署", "build": "构建", "compile": "编译",
    "interface": "接口", "module": "模块", "package": "包", "library": "库",
    "framework": "框架", "api": "接口", "request": "请求", "response": "响应",
    "user": "用户", "admin": "管理员", "login": "登录", "password": "密码",
    "token": "令牌", "session": "会话", "cookie": "Cookie", "cache": "缓存",
    "queue": "队列", "stack": "栈", "tree": "树", "graph": "图",
    "search": "搜索", "sort": "排序", "filter": "过滤", "map": "映射",
    "reduce": "归约", "merge": "合并", "split": "分割", "parse": "解析",
    "render": "渲染", "component": "组件", "state": "状态", "props": "属性",
    "event": "事件", "handler": "处理器", "callback": "回调", "promise": "Promise",
    "async": "异步", "sync": "同步", "stream": "流", "buffer": "缓冲区",
}

DICT_CN_EN = {v: k for k, v in DICT_EN_CN.items()}


class TranslatorSchema(SkillSchema):
    text: str = Field(description="要翻译的文本(单词或短语)")
    direction: str = Field(default="auto", description="方向: en2cn/cn2en/auto")


class TextTranslatorDictSkill(BaseSkill):
    name = "text_translator_dict"
    description = "简易中英词典: 查询常用技术词汇翻译"
    category = "document"
    args_schema = TranslatorSchema
    tags = ["翻译", "词典", "中英", "translate"]

    async def execute(self, **kwargs: Any) -> str:
        text = kwargs["text"].strip().lower()
        direction = kwargs.get("direction", "auto")

        if direction == "auto":
            if re.search(r'[\u4e00-\u9fff]', text):
                direction = "cn2en"
            else:
                direction = "en2cn"

        if direction == "en2cn":
            words = re.findall(r'[a-zA-Z]+', text)
            results = []
            for w in words:
                wl = w.lower()
                if wl in DICT_EN_CN:
                    results.append(f"  {w} → {DICT_EN_CN[wl]}")
                else:
                    results.append(f"  {w} → [未收录]")
            if not results:
                return "未找到可翻译的英文单词"
            return f"英→中翻译:\n" + "\n".join(results)
        else:
            chars = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
            results = []
            for c in chars:
                if c in DICT_CN_EN:
                    results.append(f"  {c} → {DICT_CN_EN[c]}")
                else:
                    results.append(f"  {c} → [未收录]")
            if not results:
                return "未找到可翻译的中文词汇"
            return f"中→英翻译:\n" + "\n".join(results)
