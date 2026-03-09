"""
胜利条件判定
"""

from typing import Tuple, Optional
from models.game_state import GameState


class WinCondition:
    """胜利条件判定类"""

    @staticmethod
    def check_game_end(state: GameState) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        检查游戏是否结束

        Args:
            state: 游戏状态

        Returns:
            (游戏是否结束，获胜阵营，结束原因)
        """
        # 获取存活狼人数量
        alive_werewolves = [
            wid for wid in state.werewolf_players
            if wid in state.alive_players
        ]

        # 获取好人数量（存活玩家 - 狼人）
        good_players_count = len(state.alive_players) - len(alive_werewolves)

        # 条件 1：狼人全灭 -> 好人胜利
        if len(alive_werewolves) == 0:
            return True, "好人阵营", "所有狼人被淘汰"

        # 条件 2：狼人数量 >= 好人数量 -> 狼人胜利
        if len(alive_werewolves) >= good_players_count:
            return True, "狼人阵营", "狼人数量达到或超过好人"

        # 条件 3：只剩 1 狼 1 好，且女巫无药 -> 根据具体规则判定
        # 这里采用标准规则：继续游戏

        return False, None, None

    @staticmethod
    def get_winning_players(state: GameState, winner: str) -> list[int]:
        """
        获取获胜玩家列表

        Args:
            state: 游戏状态
            winner: 获胜阵营名称

        Returns:
            获胜玩家 ID 列表
        """
        if winner == "狼人阵营":
            return [
                wid for wid in state.werewolf_players
                if wid in state.alive_players
            ]
        elif winner == "好人阵营":
            return state.alive_players.copy()
        else:
            return []

    @staticmethod
    def should_game_continue(state: GameState) -> bool:
        """
        判断游戏是否应该继续

        Args:
            state: 游戏状态

        Returns:
            是否继续
        """
        game_over, _, _ = WinCondition.check_game_end(state)
        return not game_over
