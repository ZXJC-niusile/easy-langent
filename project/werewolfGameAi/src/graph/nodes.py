"""
LangGraph 工作流节点定义
每个节点对应游戏的一个阶段或行动
"""

import asyncio
from typing import Any
from models.game_state import GameState, NightAction, DayDiscussion, VoteRecord
from models.enums import GamePhase, Role
from datetime import datetime


class GameNodes:
    """游戏节点类"""

    def __init__(self, agent_manager=None):
        """
        初始化节点

        Args:
            agent_manager: Agent 管理器，用于调用各角色 AI
        """
        self.agent_manager = agent_manager

    async def start_game(self, state: GameState) -> dict[str, Any]:
        """游戏开始节点"""
        state.add_game_log("游戏开始！")
        state.current_round = 1
        state.current_phase = GamePhase.NIGHT_START
        return {"current_phase": GamePhase.NIGHT_START}

    async def night_werewolf_action(self, state: GameState) -> dict[str, Any]:
        """
        夜晚狼人行动节点
        狼人讨论并选择击杀目标
        """
        state.add_game_log(f"第 {state.current_round} 夜 - 狼人行动阶段")

        if not self.agent_manager:
            # 测试模式，跳过 AI 调用
            state.night_kill_target = None
            return {}

        # 获取存活的狼人
        werewolves = state.get_werewolf_team()
        if not werewolves:
            return {}

        # 狼人讨论（简化为第一个狼人决策）
        kill_target = await self.agent_manager.werewolf_choose_target(
            werewolves, state.alive_players
        )

        state.night_kill_target = kill_target
        state.night_actions.append(
            NightAction(
                actor_id=werewolves[0].player_id,
                action_type="kill",
                target_id=kill_target,
                result=f"选择击杀 {kill_target}",
            )
        )

        state.add_game_log(f"狼人选择击杀目标：玩家{kill_target}" if kill_target else "狼人未选择击杀目标")
        return {"night_kill_target": kill_target}

    async def night_seer_action(self, state: GameState) -> dict[str, Any]:
        """
        夜晚预言家行动节点
        预言家选择查验目标
        """
        state.add_game_log(f"第 {state.current_round} 夜 - 预言家行动阶段")

        if not self.agent_manager:
            state.seer_check_target = None
            state.seer_check_result = None
            return {}

        # 获取预言家
        seer_player = None
        for pid in state.alive_players:
            player = state.get_player(pid)
            if player and player.role == Role.SEER:
                seer_player = player
                break

        if not seer_player:
            return {}

        # 预言家选择查验目标
        check_target = await self.agent_manager.seer_choose_target(
            seer_player, state.alive_players
        )

        if check_target:
            target_player = state.get_player(check_target)
            check_result = target_player.role if target_player else None

            state.seer_check_target = check_target
            state.seer_check_result = check_result

            # 更新被查验玩家的状态
            if target_player:
                target_player.checked_by_seer = True
                target_player.seer_result = check_result

            state.night_actions.append(
                NightAction(
                    actor_id=seer_player.player_id,
                    action_type="check",
                    target_id=check_target,
                    result=f"查验结果：{check_result.value if check_result else '未知'}",
                )
            )

            state.add_game_log(f"预言家查验玩家{check_target}，结果为：{check_result.value if check_result else '未知'}")

        return {
            "seer_check_target": check_target if check_target else None,
            "seer_check_result": check_result if check_result else None,
        }

    async def night_witch_action(self, state: GameState) -> dict[str, Any]:
        """
        夜晚女巫行动节点
        女巫选择是否使用解药或毒药
        """
        state.add_game_log(f"第 {state.current_round} 夜 - 女巫行动阶段")

        if not self.agent_manager:
            return {}

        # 获取女巫
        witch_player = None
        for pid in state.alive_players:
            player = state.get_player(pid)
            if player and player.role == Role.WITCH:
                witch_player = player
                break

        if not witch_player:
            return {}

        # 告知女巫今晚的死亡信息
        death_info = state.night_kill_target

        # 女巫决策
        save_target, poison_target = await self.agent_manager.witch_make_decision(
            witch_player, death_info, state.alive_players
        )

        # 记录女巫行动
        if save_target and not state.witch_used_save:
            state.witch_save_target = save_target
            state.witch_used_save = True
            state.night_actions.append(
                NightAction(
                    actor_id=witch_player.player_id,
                    action_type="save",
                    target_id=save_target,
                    result="使用解药",
                )
            )
            state.add_game_log(f"女巫使用解药救了玩家{save_target}")

        if poison_target and not state.witch_used_poison:
            state.witch_poison_target = poison_target
            state.witch_used_poison = True
            state.night_actions.append(
                NightAction(
                    actor_id=witch_player.player_id,
                    action_type="poison",
                    target_id=poison_target,
                    result="使用毒药",
                )
            )
            state.add_game_log(f"女巫使用毒药毒了玩家{poison_target}")

        return {}

    async def night_end(self, state: GameState) -> dict[str, Any]:
        """
        夜晚结束节点
        结算夜晚行动，计算死亡玩家
        """
        state.add_game_log("夜晚结束，结算死亡信息")

        deaths = []

        # 计算狼人击杀（如果没有被救）
        if state.night_kill_target:
            killed_player = state.get_player(state.night_kill_target)
            if killed_player and killed_player.is_alive:
                # 检查是否被女巫救
                if state.witch_save_target != state.night_kill_target:
                    deaths.append(state.night_kill_target)

        # 计算女巫毒药
        if state.witch_poison_target:
            poisoned_player = state.get_player(state.witch_poison_target)
            if poisoned_player and poisoned_player.is_alive:
                deaths.append(state.witch_poison_target)

        # 去重
        deaths = list(set(deaths))

        # 标记死亡
        for player_id in deaths:
            state.remove_player(player_id)

        state.deaths_this_night = deaths
        state.deaths_today = deaths.copy()

        state.add_game_log(f"昨晚死亡玩家：{deaths if deaths else '无人死亡'}")

        # 进入白天
        state.current_phase = GamePhase.DAY_START

        return {
            "deaths_this_night": deaths,
            "current_phase": GamePhase.DAY_START,
        }

    async def day_start(self, state: GameState) -> dict[str, Any]:
        """白天开始节点"""
        state.add_game_log(f"第 {state.current_round} 天开始")

        # 公布昨晚信息
        if state.deaths_this_night:
            death_names = [
                str(state.get_player(pid)) for pid in state.deaths_this_night
            ]
            state.add_game_log(f"昨晚死亡的玩家：{', '.join(death_names)}")
        else:
            state.add_game_log("昨晚是平安夜")

        # 准备发言顺序（按玩家 ID 排序）
        state.discussion_order = sorted(state.alive_players)
        state.current_speaker_index = 0

        state.current_phase = GamePhase.DAY_DISCUSSION

        return {"current_phase": GamePhase.DAY_DISCUSSION}

    async def day_discussion(self, state: GameState) -> dict[str, Any]:
        """
        白天讨论节点
        按顺序让每个存活玩家发言
        """
        state.add_game_log(f"第 {state.current_round} 天 - 讨论阶段")

        if not self.agent_manager:
            # 测试模式，跳过发言
            state.current_phase = GamePhase.DAY_VOTING
            return {"current_phase": GamePhase.DAY_VOTING}

        # 按顺序让每个玩家发言
        for speaker_id in state.discussion_order:
            speaker = state.get_alive_player(speaker_id)
            if not speaker:
                continue

            # 获取发言内容
            speech = await self.agent_manager.get_day_speech(
                speaker, state, state.current_round
            )

            # 记录发言
            discussion = DayDiscussion(
                round_number=state.current_round,
                speaker_id=speaker_id,
                speech_text=speech,
            )
            state.day_discussions.append(discussion)

            # 添加到所有玩家的记忆
            for pid in state.alive_players:
                player = state.get_player(pid)
                if player:
                    player.add_memory(
                        f"第{state.current_round}天，{speaker.name}说：{speech[:100]}..."
                    )

            state.add_game_log(f"玩家{speaker_id}({speaker.role.value})发言：{speech[:50]}...")

        state.current_phase = GamePhase.DAY_VOTING

        return {"current_phase": GamePhase.DAY_VOTING}

    async def day_voting(self, state: GameState) -> dict[str, Any]:
        """
        白天投票节点
        所有存活玩家投票
        """
        state.add_game_log(f"第 {state.current_round} 天 - 投票阶段")

        if not self.agent_manager:
            state.current_phase = GamePhase.DAY_END
            return {"current_phase": GamePhase.DAY_END}

        vote_counts = {}  # 统计每个目标的票数

        # 每个玩家投票
        for voter_id in state.alive_players:
            voter = state.get_player(voter_id)
            if not voter:
                continue

            # 获取投票目标
            vote_target = await self.agent_manager.get_vote_target(
                voter, state, state.current_round
            )

            # 记录投票
            vote_record = VoteRecord(
                round_number=state.current_round,
                voter_id=voter_id,
                vote_target=vote_target,
            )
            state.vote_records.append(vote_record)

            # 统计票数
            if vote_target is not None:
                vote_counts[vote_target] = vote_counts.get(vote_target, 0) + 1

            state.add_game_log(
                f"玩家{voter_id}投票给：{vote_target if vote_target else '弃票'}"
            )

        # 计算被放逐的玩家（票数最多者）
        eliminated = None
        if vote_counts:
            max_votes = max(vote_counts.values())
            # 找出所有得票最多的玩家
            top_candidates = [k for k, v in vote_counts.items() if v == max_votes]

            if len(top_candidates) == 1:
                eliminated = top_candidates[0]
            else:
                state.add_game_log(f"平票：{top_candidates}，无人被放逐")

        # 处理被放逐
        if eliminated is not None:
            state.remove_player(eliminated)
            state.eliminated_players.append(eliminated)
            state.vote_eliminated = eliminated
            state.add_game_log(f"玩家{eliminated}被投票放逐")

            # 检查猎人技能
            eliminated_player = state.get_player(eliminated)
            if (
                eliminated_player
                and eliminated_player.role == Role.HUNTER
                and not eliminated_player.hunter_triggered
            ):
                # 猎人发动技能
                hunter_target = await self.agent_manager.hunter_use_skill(
                    eliminated_player, state.alive_players
                )
                if hunter_target:
                    state.remove_player(hunter_target)
                    state.deaths_today.append(hunter_target)
                    eliminated_player.hunter_triggered = True
                    state.add_game_log(f"猎人发动技能，带走了玩家{hunter_target}")

        state.current_phase = GamePhase.DAY_END

        return {
            "vote_eliminated": eliminated,
            "current_phase": GamePhase.DAY_END,
        }

    async def day_end(self, state: GameState) -> dict[str, Any]:
        """白天结束节点"""
        state.add_game_log(f"第 {state.current_round} 天结束")

        # 检查游戏是否结束
        game_over, winner, reason = self.check_game_end(state)

        if game_over:
            state.winner = winner
            state.game_end_reason = reason
            state.current_phase = GamePhase.GAME_OVER
            state.add_game_log(f"游戏结束！获胜方：{winner}，原因：{reason}")
        else:
            # 进入下一夜
            state.current_round += 1
            state.current_phase = GamePhase.NIGHT_START
            # 重置夜晚状态
            state.night_kill_target = None
            state.seer_check_target = None
            state.seer_check_result = None
            state.witch_save_target = None
            state.witch_poison_target = None
            state.deaths_this_night = []
            state.vote_eliminated = None
            state.add_game_log(f"进入第 {state.current_round} 夜")

        return {
            "winner": winner,
            "game_end_reason": reason,
            "current_phase": state.current_phase,
        }

    def check_game_end(self, state: GameState) -> tuple[bool, str | None, str | None]:
        """
        检查游戏是否结束

        Returns:
            (game_over, winner, reason)
        """
        # 检查狼人是否全灭
        alive_werewolves = [
            wid for wid in state.werewolf_players if wid in state.alive_players
        ]

        if not alive_werewolves:
            return True, "好人阵营", "所有狼人被淘汰"

        # 检查狼人是否达到胜利条件（狼人数量 >= 好人数量）
        good_players_count = len(state.alive_players) - len(alive_werewolves)
        if len(alive_werewolves) >= good_players_count:
            return True, "狼人阵营", "狼人数量达到或超过好人"

        return False, None, None
