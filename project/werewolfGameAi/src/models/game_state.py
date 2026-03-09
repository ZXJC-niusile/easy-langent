"""
游戏状态类定义
用于 LangGraph 的状态管理
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from .enums import GamePhase, Role
from .player import Player


@dataclass
class NightAction:
    """夜晚行动记录"""

    actor_id: int  # 行动者 ID
    action_type: str  # 行动类型（kill/check/save/poison）
    target_id: Optional[int] = None  # 目标 ID
    result: Optional[str] = None  # 行动结果
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DayDiscussion:
    """白天发言记录"""

    round_number: int  # 第几天
    speaker_id: int  # 发言者 ID
    speech_text: str  # 发言内容
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class VoteRecord:
    """投票记录"""

    round_number: int  # 第几天
    voter_id: int  # 投票者 ID
    vote_target: Optional[int]  # 投票目标（可以是 None 表示弃票）
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class GameState:
    """
    游戏状态类
    用于 LangGraph StateGraph 的状态管理
    """

    # 游戏基础信息
    current_phase: GamePhase = GamePhase.NOT_STARTED  # 当前阶段
    current_round: int = 0  # 当前回合数（第几天）
    game_log: list[str] = field(default_factory=list)  # 游戏日志

    # 玩家信息
    players: dict[int, Player] = field(default_factory=dict)  # 所有玩家
    alive_players: list[int] = field(default_factory=list)  # 存活玩家 ID 列表
    werewolf_players: list[int] = field(default_factory=list)  # 狼人玩家 ID 列表

    # 夜晚行动
    night_actions: list[NightAction] = field(default_factory=list)  # 夜晚行动记录
    night_kill_target: Optional[int] = None  # 狼人击杀目标
    seer_check_target: Optional[int] = None  # 预言家查验目标
    seer_check_result: Optional[Role] = None  # 预言家查验结果
    witch_used_save: bool = False  # 女巫是否使用解药
    witch_used_poison: bool = False  # 女巫是否使用毒药
    witch_save_target: Optional[int] = None  # 女巫救的目标
    witch_poison_target: Optional[int] = None  # 女巫毒的目标

    # 白天流程
    discussion_order: list[int] = field(default_factory=list)  # 发言顺序
    current_speaker_index: int = 0  # 当前发言者索引
    day_discussions: list[DayDiscussion] = field(default_factory=list)  # 发言记录
    vote_records: list[VoteRecord] = field(default_factory=list)  # 投票记录
    vote_eliminated: Optional[int] = None  # 被投票放逐的玩家

    # 死亡信息
    deaths_this_night: list[int] = field(default_factory=list)  # 今晚死亡玩家
    deaths_today: list[int] = field(default_factory=list)  # 今天死亡玩家
    eliminated_players: list[int] = field(default_factory=list)  # 被放逐玩家

    # 游戏结束信息
    winner: Optional[str] = None  # 获胜阵营
    game_end_reason: Optional[str] = None  # 游戏结束原因

    def add_player(self, player: Player):
        """添加玩家"""
        self.players[player.player_id] = player
        if player.is_alive:
            self.alive_players.append(player.player_id)
        if player.role == Role.WEREWOLF:
            self.werewolf_players.append(player.player_id)

    def get_player(self, player_id: int) -> Optional[Player]:
        """获取玩家"""
        return self.players.get(player_id)

    def get_alive_player(self, player_id: int) -> Optional[Player]:
        """获取存活玩家"""
        player = self.players.get(player_id)
        if player and player.is_alive:
            return player
        return None

    def remove_player(self, player_id: int):
        """移除玩家（死亡或放逐）"""
        if player_id in self.alive_players:
            self.alive_players.remove(player_id)
        if player_id in self.werewolf_players:
            self.werewolf_players.remove(player_id)
        player = self.players.get(player_id)
        if player:
            player.eliminate()

    def add_game_log(self, message: str):
        """添加游戏日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.game_log.append(f"[{timestamp}] {message}")

    def get_werewolf_team(self) -> list[Player]:
        """获取狼人团队"""
        return [
            self.players[wid] for wid in self.werewolf_players if wid in self.alive_players
        ]

    def to_dict(self) -> dict:
        """转换为字典（用于日志）"""
        return {
            "current_phase": self.current_phase.value,
            "current_round": self.current_round,
            "alive_players": self.alive_players,
            "werewolf_players": self.werewolf_players,
            "deaths_this_night": self.deaths_this_night,
            "eliminated_players": self.eliminated_players,
            "winner": self.winner,
            "game_end_reason": self.game_end_reason,
        }
