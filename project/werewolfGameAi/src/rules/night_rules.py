"""
夜晚行动规则
"""

from typing import Optional, Tuple
from models.game_state import GameState
from models.enums import Role


class NightRules:
    """夜晚规则类"""

    @staticmethod
    def resolve_night_actions(state: GameState) -> list[int]:
        """
        结算夜晚行动

        Args:
            state: 游戏状态

        Returns:
            死亡玩家 ID 列表
        """
        deaths = []

        # 1. 处理狼人击杀
        if state.night_kill_target:
            killed_player = state.get_player(state.night_kill_target)
            if killed_player and killed_player.is_alive:
                # 检查是否被女巫救
                if state.witch_save_target != state.night_kill_target:
                    deaths.append(state.night_kill_target)

        # 2. 处理女巫毒药
        if state.witch_poison_target:
            poisoned_player = state.get_player(state.witch_poison_target)
            if poisoned_player and poisoned_player.is_alive:
                # 毒药无法被救
                deaths.append(state.witch_poison_target)

        # 去重
        deaths = list(set(deaths))

        return deaths

    @staticmethod
    def validate_werewolf_kill(
        state: GameState, target_id: int, werewolf_ids: list[int]
    ) -> bool:
        """
        验证狼人击杀目标是否合法

        Args:
            state: 游戏状态
            target_id: 击杀目标
            werewolf_ids: 狼人 ID 列表

        Returns:
            是否合法
        """
        # 不能击杀自己或狼队友
        if target_id in werewolf_ids:
            return False

        # 必须击杀存活玩家
        if target_id not in state.alive_players:
            return False

        return True

    @staticmethod
    def validate_seer_check(
        state: GameState, seer_id: int, target_id: int
    ) -> bool:
        """
        验证预言家查验是否合法

        Args:
            state: 游戏状态
            seer_id: 预言家 ID
            target_id: 查验目标

        Returns:
            是否合法
        """
        # 不能查验自己
        if target_id == seer_id:
            return False

        # 必须查验存活玩家
        if target_id not in state.alive_players:
            return False

        return True

    @staticmethod
    def validate_witch_action(
        state: GameState,
        witch_id: int,
        use_save: bool,
        save_target: Optional[int],
        use_poison: bool,
        poison_target: Optional[int],
    ) -> Tuple[bool, str]:
        """
        验证女巫行动是否合法

        Args:
            state: 游戏状态
            witch_id: 女巫 ID
            use_save: 是否使用解药
            save_target: 解救目标
            use_poison: 是否使用毒药
            poison_target: 毒杀目标

        Returns:
            (是否合法，错误信息)
        """
        # 两瓶药不能在同一晚使用
        if use_save and use_poison:
            return False, "解药和毒药不能在同一晚使用"

        # 检查解药使用
        if use_save:
            if state.witch_used_save:
                return False, "解药已使用过"
            if save_target and save_target not in state.alive_players:
                return False, "解救目标必须存活"
            # 注意：被狼刀的玩家在结算前还活着，所以这里不严格检查

        # 检查毒药使用
        if use_poison:
            if state.witch_used_poison:
                return False, "毒药已使用过"
            if poison_target and poison_target not in state.alive_players:
                return False, "毒杀目标必须存活"
            if poison_target == witch_id:
                return False, "不能毒杀自己"

        return True, ""

    @staticmethod
    def can_witch_save_self(
        state: GameState, witch_id: int, is_first_night: bool
    ) -> bool:
        """
        判断女巫是否可以自救

        Args:
            state: 游戏状态
            witch_id: 女巫 ID
            is_first_night: 是否是第一夜

        Returns:
            是否可以自救
        """
        # 标准规则：只有第一夜可以自救
        if not is_first_night:
            return False

        # 检查是否已经用过解药
        if state.witch_used_save:
            return False

        return True
