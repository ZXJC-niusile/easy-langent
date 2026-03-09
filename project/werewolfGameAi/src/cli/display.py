"""
显示管理器
负责格式化输出各种游戏信息
"""

import os
from typing import Optional, List
from models.game_state import GameState
from models.player import Player
from models.enums import Role


class DisplayManager:
    """显示管理器类"""

    def __init__(self, log_dir: str = "logs"):
        """初始化显示管理器"""
        from pathlib import Path
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.clear_screen = lambda: os.system("cls") if os.name == "nt" else os.system("clear")

    def clear(self):
        """清屏"""
        self.clear_screen()
        print("\n" * 2)

    def print_header(self, title: str):
        """
        打印标题

        Args:
            title: 标题文本
        """
        width = len(title) + 4
        print("=" * width)
        print(f"  {title}")
        print("=" * width)
        print()

    def print_section(self, section_name: str):
        """
        打印章节标题

        Args:
            section_name: 章节名称
        """
        print(f"\n--- {section_name} ---")

    def display_game_info(self, state: GameState):
        """
        显示游戏基本信息

        Args:
            state: 游戏状态
        """
        self.print_header("游戏信息")
        print(f"当前回合：第 {state.current_round} 天")
        print(f"当前阶段：{state.current_phase.value}")
        print(f"存活玩家数：{len(state.alive_players)}")
        print(f"狼人数量：{len(state.werewolf_players)}")

    def display_player_status(self, state: GameState, show_roles: bool = True):
        """
        显示玩家状态（上帝视角）

        Args:
            state: 游戏状态
            show_roles: 是否显示角色（上帝视角 always True）
        """
        self.print_header("玩家状态")

        # 表头
        print(f"{'ID':<5} {'姓名':<10} {'角色':<10} {'阵营':<10} {'状态':<8}")
        print("-" * 50)

        for pid in sorted(state.players.keys()):
            player = state.players[pid]
            role_display = player.role.value if show_roles else "?"
            team_display = player.team if show_roles else "?"
            status = "存活" if player.is_alive else "死亡"

            print(
                f"{player.player_id:<5} {player.name:<10} {role_display:<10} {team_display:<10} {status:<8}"
            )

    def display_alive_players(self, state: GameState):
        """显示存活玩家列表"""
        self.print_section("存活玩家")
        alive_names = []
        for pid in state.alive_players:
            player = state.get_player(pid)
            if player:
                alive_names.append(f"{player.name}({player.role.value})")
        print(", ".join(alive_names) if alive_names else "无")

    def display_deaths(self, state: GameState, phase: str = "night"):
        """
        显示死亡信息

        Args:
            state: 游戏状态
            phase: 阶段（night/day）
        """
        self.print_section("死亡信息")

        if phase == "night":
            deaths = state.deaths_this_night
            if deaths:
                death_names = [str(state.get_player(pid)) for pid in deaths]
                print(f"昨晚死亡：{', '.join(death_names)}")
            else:
                print("昨晚是平安夜")
        else:
            deaths = state.deaths_today
            eliminated = state.vote_eliminated

            if eliminated:
                print(f"被投票放逐：{state.get_player(eliminated)}")

            other_deaths = [d for d in deaths if d != eliminated]
            if other_deaths:
                death_names = [str(state.get_player(pid)) for pid in other_deaths]
                print(f"其他死亡：{', '.join(death_names)}")

    def display_discussions(self, state: GameState, round_number: Optional[int] = None):
        """
        显示发言记录

        Args:
            state: 游戏状态
            round_number: 回合数（可选，默认显示所有）
        """
        self.print_section("发言记录")

        discussions = state.day_discussions
        if round_number:
            discussions = [d for d in discussions if d.round_number == round_number]

        if not discussions:
            print("暂无发言记录")
            return

        current_round = -1
        for disc in discussions:
            if disc.round_number != current_round:
                current_round = disc.round_number
                print(f"\n【第{current_round}天】")

            speaker = state.get_player(disc.speaker_id)
            speaker_info = f"玩家{disc.speaker_id}"
            if speaker:
                speaker_info += f"({speaker.role.value})"

            print(f"{speaker_info}: {disc.speech_text}")

    def display_votes(self, state: GameState, round_number: Optional[int] = None):
        """
        显示投票记录

        Args:
            state: 游戏状态
            round_number: 回合数（可选）
        """
        self.print_section("投票记录")

        votes = state.vote_records
        if round_number:
            votes = [v for v in votes if v.round_number == round_number]

        if not votes:
            print("暂无投票记录")
            return

        # 统计票数
        vote_counts = {}
        for vote in votes:
            target = vote.vote_target
            vote_counts[target] = vote_counts.get(target, 0) + 1

        print("投票详情:")
        for vote in votes:
            voter = state.get_player(vote.voter_id)
            voter_name = voter.name if voter else str(vote.voter_id)
            target_name = (
                str(vote.vote_target) if vote.vote_target else "弃票"
            )
            print(f"  {voter_name} -> {target_name}")

        print("\n票数统计:")
        for target, count in sorted(vote_counts.items(), key=lambda x: -x[1]):
            target_name = f"玩家{target}" if target else "弃票"
            bar = "█" * count
            print(f"  {target_name:<10} {bar} ({count}票)")

    def display_night_actions(self, state: GameState, round_number: Optional[int] = None):
        """
        显示夜晚行动（上帝视角）

        Args:
            state: 游戏状态
            round_number: 回合数（可选）
        """
        self.print_section("夜晚行动")

        actions = state.night_actions
        if round_number:
            actions = [a for a in actions if a.timestamp.day == round_number]

        if not actions:
            print("暂无行动记录")
            return

        for action in actions:
            actor = state.get_player(action.actor_id)
            actor_name = actor.name if actor else str(action.actor_id)

            action_type_map = {
                "kill": "击杀",
                "check": "查验",
                "save": "解救",
                "poison": "毒杀",
            }
            action_cn = action_type_map.get(action.action_type, action.action_type)

            target_info = f"-> 玩家{action.target_id}" if action.target_id else ""
            print(f"{actor_name}({action.action_type}): {action_cn} {target_info}")
            if action.result:
                print(f"  结果：{action.result}")

    def display_game_over(self, state: GameState):
        """
        显示游戏结束信息

        Args:
            state: 游戏状态
        """
        self.print_header("游戏结束")
        print(f"获胜阵营：{state.winner}")
        print(f"结束原因：{state.game_end_reason}")
        print()

        # 最终玩家状态
        self.display_player_status(state, show_roles=True)

    def display_menu(self) -> str:
        """
        显示主菜单

        Returns:
            用户选择
        """
        print("\n" + "=" * 40)
        print("上帝视角菜单")
        print("=" * 40)
        print("1. 查看玩家状态")
        print("2. 查看发言记录")
        print("3. 查看投票记录")
        print("4. 查看夜晚行动")
        print("5. 查看游戏日志")
        print("6. 继续游戏")
        print("7. 退出游戏")
        print("=" * 40)

        choice = input("请选择 (1-7): ").strip()
        return choice
