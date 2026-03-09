"""
白天规则
"""

from typing import Optional, Dict, List
from models.game_state import GameState


class DayRules:
    """白天规则类"""

    @staticmethod
    def get_discussion_order(state: GameState) -> List[int]:
        """
        获取发言顺序

        Args:
            state: 游戏状态

        Returns:
            发言顺序（玩家 ID 列表）
        """
        # 默认按玩家 ID 排序
        return sorted(state.alive_players)

    @staticmethod
    def calculate_votes(
        state: GameState, votes: Dict[int, Optional[int]]
    ) -> Dict[int, int]:
        """
        计算票数

        Args:
            state: 游戏状态
            votes: 投票记录 {voter_id: vote_target}

        Returns:
            票数统计 {target_id: vote_count}
        """
        vote_counts = {}

        for voter_id, vote_target in votes.items():
            # 只有存活玩家可以投票
            if voter_id not in state.alive_players:
                continue

            # 统计票数
            if vote_target is not None:
                vote_counts[vote_target] = vote_counts.get(vote_target, 0) + 1

        return vote_counts

    @staticmethod
    def determine_eliminated(
        vote_counts: Dict[int, int],
    ) -> tuple[Optional[int], str]:
        """
        确定被放逐的玩家

        Args:
            vote_counts: 票数统计

        Returns:
            (被放逐的玩家 ID，结果说明)
        """
        if not vote_counts:
            return None, "无人获得票数"

        # 找出最高票
        max_votes = max(vote_counts.values())

        # 找出所有得票最多的玩家
        top_candidates = [k for k, v in vote_counts.items() if v == max_votes]

        if len(top_candidates) == 1:
            return top_candidates[0], f"以{max_votes}票被放逐"
        else:
            return None, f"平票：{top_candidates}，无人被放逐"

    @staticmethod
    def validate_vote(
        state: GameState, voter_id: int, vote_target: Optional[int]
    ) -> tuple[bool, str]:
        """
        验证投票是否合法

        Args:
            state: 游戏状态
            voter_id: 投票者 ID
            vote_target: 投票目标

        Returns:
            (是否合法，错误信息)
        """
        # 只有存活玩家可以投票
        if voter_id not in state.alive_players:
            return False, "只有存活玩家可以投票"

        # 可以弃票（vote_target 为 None）
        if vote_target is None:
            return True, ""

        # 不能投给自己
        if vote_target == voter_id:
            return False, "不能投票给自己"

        # 必须投给存活玩家
        if vote_target not in state.alive_players:
            return False, "只能投票给存活玩家"

        return True, ""

    @staticmethod
    def handle_hunter_skill(
        state: GameState, hunter_id: int, target_id: Optional[int]
    ) -> tuple[bool, str]:
        """
        处理猎人技能

        Args:
            state: 游戏状态
            hunter_id: 猎人 ID
            target_id: 带走的目标

        Returns:
            (是否成功，结果说明)
        """
        hunter = state.get_player(hunter_id)

        if not hunter:
            return False, "猎人不存在"

        if hunter.role.name != "HUNTER":
            return False, "不是猎人"

        if not hunter.is_alive:
            return False, "猎人已死亡"

        if target_id is None:
            return True, "猎人选择放弃技能"

        if target_id not in state.alive_players:
            return False, "目标必须存活"

        if target_id == hunter_id:
            return False, "不能带走自己"

        return True, f"猎人带走了玩家{target_id}"
