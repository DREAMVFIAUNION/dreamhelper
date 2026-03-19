"""石头剪刀布技能"""

import random

from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill

CHOICES = ["rock", "paper", "scissors"]
CN_MAP = {"rock": "石头 🪨", "paper": "布 📄", "scissors": "剪刀 ✂️"}
WIN_MAP = {"rock": "scissors", "paper": "rock", "scissors": "paper"}


class RockPaperScissorsArgs(BaseModel):
    choice: str = Field(..., description="你的选择: rock/paper/scissors (石头/布/剪刀)")
    rounds: int = Field(1, description="对战轮数 (1-10)")


class RockPaperScissorsSkill(BaseSkill):
    name = "rock_paper_scissors"
    description = "石头剪刀布 — 和 AI 对战"
    category = "entertainment"
    tags = ["石头剪刀布", "猜拳", "游戏", "娱乐"]
    args_schema = RockPaperScissorsArgs

    async def execute(self, **kwargs) -> str:
        args = RockPaperScissorsArgs(**kwargs)
        rounds = max(1, min(10, args.rounds))

        user_choice = args.choice.lower().strip()
        if user_choice in ("石头", "拳"):
            user_choice = "rock"
        elif user_choice in ("布", "包"):
            user_choice = "paper"
        elif user_choice in ("剪刀", "剪"):
            user_choice = "scissors"

        if user_choice not in CHOICES:
            return f"无效选择: {args.choice}，请选择 rock/paper/scissors"

        results = []
        wins = losses = draws = 0

        for i in range(rounds):
            ai = random.choice(CHOICES)
            if user_choice == ai:
                outcome = "平局"
                draws += 1
            elif WIN_MAP[user_choice] == ai:
                outcome = "你赢了!"
                wins += 1
            else:
                outcome = "AI 赢了"
                losses += 1

            if rounds > 1:
                results.append(f"  第{i+1}轮: {CN_MAP[user_choice]} vs {CN_MAP[ai]} → {outcome}")
            else:
                results.append(f"你: {CN_MAP[user_choice]}  vs  AI: {CN_MAP[ai]}")
                results.append(f"结果: {outcome}")

        lines = ["✊✋✌️ 石头剪刀布", ""]
        lines.extend(results)

        if rounds > 1:
            lines.append("")
            lines.append(f"战绩: {wins}胜 {losses}负 {draws}平")
            if wins > losses:
                lines.append("🎉 你赢了!")
            elif losses > wins:
                lines.append("🤖 AI 赢了!")
            else:
                lines.append("🤝 平局!")

        return "\n".join(lines)
