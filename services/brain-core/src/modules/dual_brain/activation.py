"""动态脑区激活 — 根据任务类型自动调整双脑权重"""

from enum import Enum


class TaskType(str, Enum):
    CODE = "code"
    CODE_ANALYSIS = "code_analysis"
    WRITING = "writing"
    ANALYSIS = "analysis"
    MATH = "math"
    QA = "qa"
    CREATIVE = "creative"
    CHAT = "chat"
    COMPLEX = "complex"
    EXPERT = "expert"


class BrainActivation:
    """
    动态脑区激活器

    类比人脑: 阅读数学题时，左脑前额叶和顶叶更活跃；
    欣赏音乐时，右脑颞叶更活跃。
    但两个半球始终在线，只是激活程度不同。
    """

    TASK_KEYWORDS = {
        TaskType.CODE: [
            "代码", "编程", "函数", "bug", "调试", "debug", "python", "javascript",
            "typescript", "api", "接口", "算法", "class", "def ", "import",
            "sql", "html", "css", "react", "vue", "实现一个", "写一个程序",
        ],
        TaskType.WRITING: [
            "写一篇", "文案", "翻译", "润色", "改写", "总结", "摘要",
            "文章", "诗", "故事", "邮件", "报告", "营销", "广告", "大纲",
        ],
        TaskType.ANALYSIS: [
            "分析", "对比", "评测", "优劣", "原因", "趋势", "方案对比",
            "选择哪个", "利弊", "可行性", "评估", "为什么", "推理",
        ],
        TaskType.MATH: [
            "计算", "算一下", "几", "多少", "等于", "求解", "方程",
            "概率", "统计", "微积分", "矩阵", "sqrt", "log",
        ],
        TaskType.CREATIVE: [
            "创意", "brainstorm", "头脑风暴", "想法", "灵感",
            "设计", "创新", "有什么好玩的", "有趣的",
        ],
        TaskType.QA: [
            "是什么", "什么是", "谁是", "哪个", "怎么回事",
            "什么时候", "在哪里", "多大", "多高", "定义",
        ],
        TaskType.EXPERT: [
            "架构", "设计模式", "性能优化", "分布式", "微服务",
            "深度学习", "机器学习", "神经网络", "安全审计",
            "系统设计", "高可用", "容器化", "kubernetes", "docker",
        ],
        TaskType.CODE_ANALYSIS: [
            "代码分析", "调用链", "依赖关系", "重构", "影响范围",
            "函数关系", "代码架构", "爆炸半径", "调用图", "执行流",
            "知识图谱", "代码结构", "模块依赖", "谁调用了", "被谁调用",
            "call chain", "blast radius", "impact analysis",
            "code structure", "dependency graph",
        ],
    }

    # 权重配置: (left_weight, right_weight)
    WEIGHT_MAP = {
        TaskType.CODE:     (0.65, 0.35),
        TaskType.WRITING:  (0.35, 0.65),
        TaskType.ANALYSIS: (0.55, 0.45),
        TaskType.MATH:     (0.75, 0.25),
        TaskType.QA:       (0.60, 0.40),
        TaskType.CREATIVE: (0.25, 0.75),
        TaskType.CHAT:     (0.40, 0.60),
        TaskType.COMPLEX:  (0.50, 0.50),
        TaskType.EXPERT:  (0.60, 0.40),
        TaskType.CODE_ANALYSIS: (0.70, 0.30),
    }

    # 融合策略映射 — 延迟导入避免循环
    STRATEGY_NAME_MAP = {
        TaskType.CODE:     "compete",
        TaskType.WRITING:  "complement",
        TaskType.ANALYSIS: "complement",
        TaskType.MATH:     "compete",
        TaskType.QA:       "compete",
        TaskType.CREATIVE: "weighted",
        TaskType.CHAT:     "weighted",
        TaskType.COMPLEX:  "debate",
        TaskType.EXPERT:  "debate",
        TaskType.CODE_ANALYSIS: "complement",
    }

    def detect_task_type(self, query: str) -> TaskType:
        """检测任务类型"""
        lower = query.lower()
        scores: dict[TaskType, int] = {}

        for task_type, keywords in self.TASK_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in lower)
            if score > 0:
                scores[task_type] = score

        if not scores:
            return TaskType.CHAT

        # 多类型命中 → COMPLEX
        high_score_types = [t for t, s in scores.items() if s >= 2]
        if len(high_score_types) >= 2:
            return TaskType.COMPLEX

        return max(scores, key=scores.get)  # type: ignore[arg-type]

    def get_weights(self, task_type: TaskType) -> tuple[float, float]:
        """获取脑区激活权重"""
        return self.WEIGHT_MAP.get(task_type, (0.50, 0.50))

    def get_fusion_strategy_name(self, task_type: TaskType) -> str:
        """获取融合策略名称（字符串，避免循环导入）"""
        return self.STRATEGY_NAME_MAP.get(task_type, "complement")

    # ── 小脑激活权重 ──
    CEREBELLUM_WEIGHT_MAP = {
        TaskType.CODE:     0.8,   # 代码任务 → 小脑高权重
        TaskType.MATH:     0.7,   # 数学任务 → 小脑较高权重
        TaskType.COMPLEX:  0.3,   # 复杂任务 → 小脑辅助校准
        TaskType.EXPERT:  0.5,   # 专家任务 → 小脑中等权重
        TaskType.CODE_ANALYSIS: 0.6,  # 代码分析 → 小脑参与架构校准
    }

    def get_cerebellum_weight(self, task_type: TaskType) -> float:
        """获取小脑激活权重（0 = 不参与）"""
        return self.CEREBELLUM_WEIGHT_MAP.get(task_type, 0.0)
