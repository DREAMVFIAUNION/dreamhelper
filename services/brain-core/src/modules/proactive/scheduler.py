"""定时任务调度器 — asyncio 原生实现（Phase 4）

支持:
- Cron 表达式定时任务
- 间隔执行任务
- 一次性延迟任务
- 任务注册/取消/列表
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Awaitable, Optional, Dict, List


class TaskType(str, Enum):
    INTERVAL = "interval"   # 固定间隔
    CRON = "cron"           # Cron 表达式（简化版）
    ONCE = "once"           # 一次性


@dataclass
class ScheduledTask:
    task_id: str
    name: str
    task_type: TaskType
    callback: Callable[[], Awaitable[None]]
    interval_seconds: float = 0       # INTERVAL 类型使用
    cron_expr: str = ""               # CRON 类型使用（简化: "HH:MM" 每日执行）
    delay_seconds: float = 0          # ONCE 类型使用
    enabled: bool = True
    last_run: float = 0
    run_count: int = 0
    description: str = ""
    _handle: Optional[asyncio.Task] = field(default=None, repr=False)


def _parse_daily_cron(cron_expr: str) -> tuple[int, int]:
    """解析简化 cron: 'HH:MM' → (hour, minute)"""
    parts = cron_expr.strip().split(":")
    return int(parts[0]), int(parts[1])


def _seconds_until(hour: int, minute: int) -> float:
    """计算距离下一个 HH:MM 的秒数"""
    import datetime
    now = datetime.datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
    return (target - now).total_seconds()


class Scheduler:
    """异步定时任务调度器"""

    def __init__(self):
        self._tasks: Dict[str, ScheduledTask] = {}
        self._running = False

    def register(self, task: ScheduledTask):
        """注册任务（支持热注册：scheduler 已运行时自动启动新任务）"""
        self._tasks[task.task_id] = task
        if self._running and task.enabled:
            task._handle = asyncio.create_task(self._run_task(task))
            print(f"  ⏰ Registered task: {task.name} ({task.task_type.value}) [auto-started]")
        else:
            print(f"  ⏰ Registered task: {task.name} ({task.task_type.value})")

    def unregister(self, task_id: str):
        """取消任务"""
        task = self._tasks.pop(task_id, None)
        if task and task._handle:
            task._handle.cancel()

    def enable(self, task_id: str):
        self._tasks[task_id].enabled = True

    def disable(self, task_id: str):
        self._tasks[task_id].enabled = False

    async def start(self):
        """启动所有任务"""
        self._running = True
        for task in self._tasks.values():
            if task.enabled:
                task._handle = asyncio.create_task(self._run_task(task))
        print(f"  ✓ Scheduler started with {len(self._tasks)} tasks")

    async def stop(self):
        """停止所有任务"""
        self._running = False
        for task in self._tasks.values():
            if task._handle:
                task._handle.cancel()
                task._handle = None
        print("  ✓ Scheduler stopped")

    async def _run_task(self, task: ScheduledTask):
        """执行单个任务的调度循环"""
        try:
            if task.task_type == TaskType.INTERVAL:
                # 首次延迟一小段避免启动时全部同时执行
                await asyncio.sleep(min(task.interval_seconds, 5))
                while self._running and task.enabled:
                    await self._execute(task)
                    await asyncio.sleep(task.interval_seconds)

            elif task.task_type == TaskType.CRON:
                hour, minute = _parse_daily_cron(task.cron_expr)
                while self._running and task.enabled:
                    wait = _seconds_until(hour, minute)
                    await asyncio.sleep(wait)
                    if self._running and task.enabled:
                        await self._execute(task)
                    # 执行后等 61 秒避免同一分钟重复触发
                    await asyncio.sleep(61)

            elif task.task_type == TaskType.ONCE:
                await asyncio.sleep(task.delay_seconds)
                if self._running and task.enabled:
                    await self._execute(task)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"  ⚠ Task {task.name} error: {e}")

    async def _execute(self, task: ScheduledTask):
        """执行任务回调"""
        try:
            await task.callback()
            task.last_run = time.time()
            task.run_count += 1
        except Exception as e:
            print(f"  ⚠ Task {task.name} callback error: {e}")

    def list_tasks(self) -> List[dict]:
        return [
            {
                "task_id": t.task_id,
                "name": t.name,
                "type": t.task_type.value,
                "enabled": t.enabled,
                "last_run": t.last_run,
                "run_count": t.run_count,
                "description": t.description,
            }
            for t in self._tasks.values()
        ]


# 全局单例
_scheduler: Optional[Scheduler] = None


def get_scheduler() -> Scheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler
