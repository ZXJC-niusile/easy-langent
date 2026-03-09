"""
Agent 管理器
统一管理所有角色的 AI 智能体
"""

import asyncio
from typing import Dict, Optional
from langchain_openai import ChatOpenAI
from models.player import Player
from models.enums import Role
from models.game_state import GameState
from prompts import get_action_prompt
from agents.base_agent import (
    BaseAgent,
    WerewolfAgent,
    SeerAgent,
    VillagerAgent,
    WitchAgent,
    HunterAgent,
)


class AgentManager:
    """Agent 管理器类"""

    def __init__(self, llm: ChatOpenAI):
        """
        初始化 Agent 管理器

        Args:
            llm: LLM 实例
        """
        self.llm = llm
        self.agents: Dict[int, BaseAgent] = {}
        self.werewolf_teams: Dict[int, list[int]] = {}  # 狼人 ID -> 狼队友 ID 列表

    def register_player(self, player: Player):
        """
        注册玩家，创建对应的 Agent

        Args:
            player: 玩家对象
        """
        if player.role == Role.WEREWOLF:
            agent = WerewolfAgent(player, self.llm, [])
        elif player.role == Role.SEER:
            agent = SeerAgent(player, self.llm)
        elif player.role == Role.WITCH:
            agent = WitchAgent(player, self.llm)
        elif player.role == Role.HUNTER:
            agent = HunterAgent(player, self.llm)
        else:  # VILLAGER
            agent = VillagerAgent(player, self.llm)

        self.agents[player.player_id] = agent

    def setup_werewolf_teams(self, werewolf_ids: list[int]):
        """
        设置狼人团队关系

        Args:
            werewolf_ids: 所有狼人 ID 列表
        """
        for wid in werewolf_ids:
            teammates = [x for x in werewolf_ids if x != wid]
            self.werewolf_teams[wid] = teammates
            if wid in self.agents and isinstance(
                self.agents[wid], WerewolfAgent
            ):
                self.agents[wid].teammate_ids = teammates

    async def werewolf_choose_target(
        self, werewolves: list[Player], alive_players: list[int], round_number: int = 1, show_debug: bool = False
    ) -> Optional[int]:
        """
        狼人选择击杀目标

        Args:
            werewolves: 存活狼人列表
            alive_players: 存活玩家 ID 列表
            round_number: 当前回合数
            show_debug: 是否显示调试信息

        Returns:
            选择的击杀目标 ID
        """
        if not werewolves:
            return None

        # 使用第一个狼人作为代表决策
        lead_werewolf = werewolves[0]
        agent = self.agents.get(lead_werewolf.player_id)
        if not agent or not isinstance(agent, WerewolfAgent):
            return None

        # 准备提示词 - 确保信息准确
        teammate_ids = [w.player_id for w in werewolves if w.player_id != lead_werewolf.player_id]
        teammate_names = ", ".join([str(tid) for tid in teammate_ids]) or "无"
        
        # 排除狼人的可击杀目标
        non_werewolf_alive = [p for p in alive_players if p not in [w.player_id for w in werewolves]]
        
        prompt = get_action_prompt(
            "werewolf_choose_target",
            player_id=lead_werewolf.player_id,
            werewolf_teammates=teammate_names,
            alive_players=", ".join(map(str, non_werewolf_alive)),
            round_number=round_number,
        )

        response = await agent.invoke_json(prompt, show_debug=show_debug)
        target_id = response.get("target_id")
        
        # 显示投票理由（如果有）
        if show_debug and response.get("reason"):
            print(f"\n[决策理由] {response['reason']}")

        # 验证目标是否合法
        if target_id and target_id in alive_players and target_id not in [
            w.player_id for w in werewolves
        ]:
            return target_id

        # 默认选择随机目标
        valid_targets = [p for p in alive_players if p not in [w.player_id for w in werewolves]]
        return valid_targets[0] if valid_targets else None

    async def seer_choose_target(
        self, seer: Player, alive_players: list[int], round_number: int = 1
    ) -> Optional[int]:
        """
        预言家选择查验目标

        Args:
            seer: 预言家玩家
            alive_players: 存活玩家 ID 列表
            round_number: 当前回合数

        Returns:
            查验目标 ID
        """
        agent = self.agents.get(seer.player_id)
        if not agent or not isinstance(agent, SeerAgent):
            return None

        # 获取已查验的玩家列表（从 SeerAgent 中获取）
        checked_ids = agent.checked_players if hasattr(agent, 'checked_players') else []
        previous_checks = f"已查验玩家：{', '.join(map(str, checked_ids))}" if checked_ids else "尚未查验任何玩家"
        
        # 排除已查验过的玩家和自己
        unchecked_alive = [p for p in alive_players if p != seer.player_id and p not in checked_ids]
        
        prompt = get_action_prompt(
            "seer_choose_target",
            player_id=seer.player_id,
            alive_players=", ".join(map(str, unchecked_alive)),
            round_number=round_number,
            previous_checks=previous_checks,
        )

        response = await agent.invoke_json(prompt)
        target_id = response.get("target_id")

        # 验证目标
        if target_id and target_id in alive_players and target_id != seer.player_id:
            return target_id

        # 默认选择
        valid_targets = [p for p in alive_players if p != seer.player_id]
        return valid_targets[0] if valid_targets else None

    async def witch_make_decision(
        self, witch: Player, death_info: Optional[int], alive_players: list[int], round_number: int = 1
    ) -> tuple[Optional[int], Optional[int]]:
        """
        女巫决策（救谁/毒谁）

        Args:
            witch: 女巫玩家
            death_info: 死亡信息（被狼人击杀的玩家 ID）
            alive_players: 存活玩家 ID 列表
            round_number: 当前回合数

        Returns:
            (救的目标，毒的目标)
        """
        agent = self.agents.get(witch.player_id)
        if not agent or not isinstance(agent, WitchAgent):
            return None, None

        has_save = not agent.has_save_potion
        has_poison = not agent.has_poison_potion
        
        # 提供准确的死亡信息
        death_target_str = f"玩家{death_info}" if death_info else "未知（可能是平安夜）"
        
        prompt = get_action_prompt(
            "witch_make_decision",
            player_id=witch.player_id,
            alive_players=", ".join(map(str, alive_players)),
            death_info=death_target_str,
            has_save_potion="是" if has_save else "否",
            has_poison_potion="是" if has_poison else "否",
            round_number=round_number,
        )

        response = await agent.invoke_json(prompt)

        save_target = response.get("save_target")
        poison_target = response.get("poison_target")
        use_save = response.get("use_save", False)
        use_poison = response.get("use_poison", False)

        # 验证目标
        final_save = None
        final_poison = None

        if use_save and save_target and save_target in alive_players:
            final_save = save_target

        if use_poison and poison_target and poison_target in alive_players:
            final_poison = poison_target

        return final_save, final_poison

    async def get_day_speech(
        self, speaker: Player, state: GameState, round_number: int
    ) -> str:
        """
        获取白天发言内容

        Args:
            speaker: 发言玩家
            state: 游戏状态
            round_number: 当前回合数

        Returns:
            发言内容
        """
        agent = self.agents.get(speaker.player_id)
        if not agent:
            return "（暂无发言）"

        # 获取记忆（增加到 10 条）
        memories = "\n".join(agent.get_memories(10))
        
        # 获取重要事件记录
        important_events = agent.player.get_important_events() if hasattr(agent.player, 'get_important_events') else "无重要事件记录"
        
        deaths = (
            ", ".join([str(pid) for pid in state.deaths_this_night])
            if state.deaths_this_night
            else "无人死亡"
        )

        prompt = get_action_prompt(
            "day_speech",
            player_id=speaker.player_id,
            player_name=speaker.name,
            role=speaker.role.value,
            team=speaker.team,
            round_number=round_number,
            deaths_last_night=deaths,
            alive_players=", ".join(map(str, state.alive_players)),
            memories=memories or "无特别记忆",
            important_events=important_events,
        )

        speech = await agent.invoke(prompt)
        return speech[:500]  # 限制 500 字符，确保发言完整不截断

    async def get_vote_target(
        self, voter: Player, state: GameState, round_number: int
    ) -> Optional[int]:
        """
        获取投票目标

        Args:
            voter: 投票玩家
            state: 游戏状态
            round_number: 当前回合数

        Returns:
            投票目标 ID
        """
        agent = self.agents.get(voter.player_id)
        if not agent:
            return None

        # 获取最近的发言记录（更完整）
        discussions = "\n".join(
            [
                f"玩家{d.speaker_id} 发言：{d.speech_text[:150]}..."
                for d in state.day_discussions[-min(5, len(state.day_discussions)):]
            ]
        )
        
        # 获取重要事件记录
        important_events = agent.player.get_important_events() if hasattr(agent.player, 'get_important_events') else "无重要事件记录"

        prompt = get_action_prompt(
            "vote_target",
            player_id=voter.player_id,
            role=voter.role.value,
            team=voter.team,
            round_number=round_number,
            alive_players=", ".join(map(str, state.alive_players)),
            discussions=discussions or "无发言记录",
            important_events=important_events,
        )

        response = await agent.invoke_json(prompt)
        vote_target = response.get("vote_target")

        # 验证目标 - 确保是存活玩家
        if vote_target and vote_target in state.alive_players:
            return vote_target
        
        # 如果没有有效目标，随机选择一个非自己以外的玩家
        # 这样可以避免 AI 因为无法决定而弃票
        valid_targets = [p for p in state.alive_players if p != voter.player_id]
        if valid_targets:
            import random
            return random.choice(valid_targets)
        
        return None

        return None  # 可以弃票

    async def hunter_use_skill(
        self, hunter: Player, alive_players: list[int]
    ) -> Optional[int]:
        """
        猎人发动技能

        Args:
            hunter: 猎人玩家
            alive_players: 存活玩家 ID 列表

        Returns:
            带走的目标 ID
        """
        agent = self.agents.get(hunter.player_id)
        if not agent or not isinstance(agent, HunterAgent):
            return None

        prompt = get_action_prompt(
            "hunter_skill",
            alive_players=", ".join(map(str, alive_players)),
            suspects="根据场上判断",
        )

        response = await agent.invoke_json(prompt)
        use_skill = response.get("use_skill", True)
        target_id = response.get("target_id")

        if use_skill and target_id and target_id in alive_players:
            return target_id

        return None
