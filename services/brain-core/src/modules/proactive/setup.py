"""主动唤醒系统初始化（Phase 4）"""

from .scheduler import get_scheduler, ScheduledTask, TaskType
from .rule_engine import get_proactive_engine


def register_proactive_tasks():
    """注册所有主动唤醒定时任务"""
    scheduler = get_scheduler()
    engine = get_proactive_engine()

    # 1. 每 5 分钟检查空闲用户并主动问候
    scheduler.register(ScheduledTask(
        task_id="idle_greeting",
        name="空闲用户问候",
        task_type=TaskType.INTERVAL,
        interval_seconds=300,
        callback=engine.check_and_greet,
        description="每5分钟检查空闲用户，发送主动问候",
    ))

    # 2. 每日早间简报 08:30
    scheduler.register(ScheduledTask(
        task_id="morning_brief",
        name="早间简报",
        task_type=TaskType.CRON,
        cron_expr="08:30",
        callback=engine.morning_brief,
        description="每天 08:30 发送早间问候",
    ))

    # 3. 每日晚间关怀 22:00
    scheduler.register(ScheduledTask(
        task_id="evening_summary",
        name="晚间关怀",
        task_type=TaskType.CRON,
        cron_expr="22:00",
        callback=engine.evening_summary,
        description="每天 22:00 发送晚间关怀",
    ))
