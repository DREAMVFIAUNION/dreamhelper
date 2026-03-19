"""代码智能分析提示词模板

用于三脑融合时，将 GitNexus 知识图谱数据注入到 LLM prompt 中。
"""

# ── 代码架构分析 System Prompt 片段 ──────────────────

CODE_INTEL_SYSTEM_PROMPT = """## 代码知识图谱上下文
你可以访问代码知识图谱，了解代码架构、调用链、依赖关系和执行流。
以下是与用户问题相关的代码智能数据:

{code_intel_data}

请结合以上代码架构信息回答用户的问题。如果信息不足，可以建议用户提供更多上下文。"""

# ── 影响分析 Prompt ──────────────────────────────

IMPACT_ANALYSIS_PROMPT = """分析以下代码变更的影响范围:

目标符号: {target}
分析方向: {direction}

知识图谱影响分析结果:
{impact_data}

请用中文总结:
1. 直接受影响的代码（d=1，一定会受影响）
2. 间接受影响的代码（d=2，可能受影响）
3. 建议的测试范围
4. 风险等级评估"""

# ── 代码问答增强 Prompt ──────────────────────────

CODE_QA_ENHANCEMENT = """[代码架构上下文]
以下信息来自代码知识图谱的自动分析:

{graph_context}

请结合以上架构信息回答用户的代码问题。
注意: 知识图谱数据可能不完整，请标明不确定的部分。"""

# ── 变更检测 Prompt ──────────────────────────────

CHANGE_DETECTION_PROMPT = """以下是当前未提交的代码变更及其影响分析:

{changes_data}

请总结:
1. 变更了哪些符号/函数
2. 影响了哪些执行流
3. 是否有潜在风险
4. 建议的 commit message"""

# ── 丘脑路由关键词 ──────────────────────────────

CODE_ANALYSIS_KEYWORDS = [
    "代码分析", "调用链", "依赖关系", "重构", "影响范围",
    "函数关系", "代码架构", "爆炸半径", "调用图", "符号",
    "执行流", "知识图谱", "代码结构", "模块依赖",
    "call chain", "dependency", "refactor", "impact",
    "blast radius", "call graph", "symbol", "architecture",
    "who calls", "what calls", "code structure",
]
