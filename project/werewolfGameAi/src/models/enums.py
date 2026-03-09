"""
枚举类型定义
"""

from enum import Enum, auto


class Role(Enum):
    """角色类型"""

    WEREWOLF = "werewolf"  # 狼人
    VILLAGER = "villager"  # 村民
    SEER = "seer"  # 预言家
    WITCH = "witch"  # 女巫
    HUNTER = "hunter"  # 猎人


class GamePhase(Enum):
    """游戏阶段"""

    NOT_STARTED = "not_started"  # 未开始
    NIGHT_START = "night_start"  # 夜晚开始
    NIGHT_WEREWOLF = "night_werewolf"  # 狼人行动
    NIGHT_SEER = "night_seer"  # 预言家行动
    NIGHT_WITCH = "night_witch"  # 女巫行动
    NIGHT_END = "night_end"  # 夜晚结束
    DAY_START = "day_start"  # 白天开始
    DAY_DISCUSSION = "day_discussion"  # 白天讨论
    DAY_VOTING = "day_voting"  # 白天投票
    DAY_END = "day_end"  # 白天结束
    GAME_OVER = "game_over"  # 游戏结束


class VoteResult(Enum):
    """投票结果"""

    SURVIVED = "survived"  # 存活
    ELIMINATED = "eliminated"  # 被放逐
    HUNTER_SKILL = "hunter_skill"  # 猎人发动技能
    NIGHT_DEATH = "night_death"  # 夜晚死亡
