"""
游戏查看器 - 上帝视角观测模式
用户只控制：开始、投票、下一轮
其余全部 AI 自动进行，带上帝旁白
"""

import asyncio
from typing import Optional
from langchain_openai import ChatOpenAI
from models.game_state import GameState, DayDiscussion, VoteRecord
from models.player import Player
from models.enums import Role, GamePhase
from llm import create_llm, LLMConfig
from agents import AgentManager
from agents.base_agent import SeerAgent
from graph import create_game_graph
from recorder import SpeechRecorder, ActionRecorder, GameLogger
from cli.display import DisplayManager


class GameViewer:
    """游戏查看器（上帝视角观测模式）"""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        log_level: str = "INFO",
        show_model_debug: bool = False,  # 是否显示模型调试信息
    ):
        """初始化游戏查看器"""
        if llm_config is None:
            llm_config = LLMConfig()
        self.llm = create_llm(llm_config)
        self.show_model_debug = show_model_debug  # 保存调试开关

        # 初始化组件
        self.agent_manager = AgentManager(self.llm)
        self.display = DisplayManager()
        self.speech_recorder = SpeechRecorder()
        self.action_recorder = ActionRecorder()
        self.logger = GameLogger(level=log_level)

        # 游戏状态
        self.state: Optional[GameState] = None
        self.graph = None

        # 玩家配置
        self.player_names = [
            "天狼", "星辰", "明月",  # 狼人
            "清风", "流水", "青山",  # 村民
            "先知", "灵巫", "猎手",  # 神职
        ]

    def setup_game(self):
        """设置游戏配置"""
        self.state = GameState()
        self._setup_default_players()
        
        # 显示随机分配结果
        print("\n" + "="*70)
        print("【系统】玩家身份分配完成（随机分配）")
        print("="*70)
        for player in self.state.players.values():
            print(f"  玩家{player.player_id} - {player.name} - {player.role.value}")
        print("="*70)

        # 注册所有玩家到 Agent Manager
        for player in self.state.players.values():
            self.agent_manager.register_player(player)

        # 设置狼人团队关系
        self.agent_manager.setup_werewolf_teams(self.state.werewolf_players)

        # 创建 LangGraph
        self.graph = create_game_graph(self.agent_manager)

        self.logger.info("游戏设置完成")

    def _setup_default_players(self):
        """设置默认玩家配置（随机分配身份）"""
        import random
        
        # 定义角色配置
        roles_list = (
            [Role.WEREWOLF] * 3 +      # 3 个狼人
            [Role.VILLAGER] * 3 +      # 3 个村民
            [Role.SEER] +              # 1 个预言家
            [Role.WITCH] +             # 1 个女巫
            [Role.HUNTER]              # 1 个猎人
        )
        
        # 随机打乱角色顺序
        random.shuffle(roles_list)
        
        # 为玩家分配随机后的角色
        for player_index in range(len(self.player_names)):
            player = Player(
                player_id=player_index + 1,
                name=self.player_names[player_index],
                role=roles_list[player_index],
            )
            self.state.add_player(player)

    async def run_game(self):
        """运行游戏（上帝视角观测模式）"""
        if not self.state:
            raise RuntimeError("请先调用 setup_game() 设置游戏")

        self.logger.info("游戏开始")
        
        # 显示初始玩家状态
        self.display.print_header("初始玩家状态")
        self.display.display_player_status(self.state)

        print("\n按回车键开始游戏...")
        await asyncio.get_event_loop().run_in_executor(None, input)

        # 游戏主循环
        try:
            while self.state.current_phase != GamePhase.GAME_OVER:
                current_phase = self.state.current_phase
                
                if current_phase in [GamePhase.NOT_STARTED, GamePhase.NIGHT_START]:
                    await self._night_start()
                elif current_phase == GamePhase.NIGHT_WEREWOLF:
                    await self._night_werewolf()
                elif current_phase == GamePhase.NIGHT_SEER:
                    await self._night_seer()
                elif current_phase == GamePhase.NIGHT_WITCH:
                    await self._night_witch()
                elif current_phase == GamePhase.NIGHT_END:
                    # 夜晚结束，自动进入白天
                    await self._day_start()
                elif current_phase == GamePhase.DAY_DISCUSSION:
                    await self._day_discussion()
                elif current_phase == GamePhase.DAY_VOTING:
                    # 等待用户确认开启投票
                    print("\n" + "="*60)
                    print("[上帝] 发言结束，是否开启投票？")
                    print("="*60)
                    print("[提示] 按回车键继续")
                    input()
                    await self._day_voting()
                elif current_phase == GamePhase.DAY_END:
                    # 检查游戏是否结束
                    game_over, winner, reason = self._check_game_end()
                    
                    if game_over:
                        self.state.winner = winner
                        self.state.game_end_reason = reason
                        self.state.current_phase = GamePhase.GAME_OVER
                        print("\n" + "="*60)
                        print("[上帝] 游戏结束")
                        print("="*60)
                        print(f"[获胜方] {winner}")
                        print(f"[原因] {reason}")
                    else:
                        # 等待用户确认进入下一轮
                        print("\n" + "="*60)
                        print("[上帝] 本轮结束，是否进入下一夜？")
                        print("="*60)
                        print("[提示] 按回车键继续，输入 q 退出")
                        choice = input().strip().lower()
                        if choice == 'q':
                            break
                        
                        # 进入下一夜
                        self.state.current_round += 1
                        self.state.current_phase = GamePhase.NIGHT_START
                        self.state.night_kill_target = None
                        self.state.seer_check_target = None
                        self.state.seer_check_result = None
                        self.state.witch_save_target = None
                        self.state.witch_poison_target = None
                        self.state.deaths_this_night = []
                        self.state.vote_eliminated = None
                        print(f"\n[系统] 进入第 {self.state.current_round} 夜")
                
                # 保存记录
                self.speech_recorder.save_to_file()
                self.action_recorder.save_to_file()

        except Exception as e:
            self.logger.error(f"游戏异常：{str(e)}")
            raise

        # 游戏结束
        self._handle_game_over()

    async def _night_start(self):
        """夜晚开始 - 上帝旁白"""
        print("\n" + "="*70)
        print("【上帝】天黑请闭眼")
        print("="*70)
        await asyncio.sleep(2)
        
        self.state.current_phase = GamePhase.NIGHT_WEREWOLF

    async def _night_werewolf(self):
        """狼人行动 - 上帝旁白 + AI 决策"""
        print("\n" + "-"*70)
        print("[上帝] 狼人请睁眼")
        print("-"*70)
        
        werewolves = self.state.get_werewolf_team()
        if not werewolves:
            print("[状态] 没有存活的狼人")
            self.state.current_phase = GamePhase.NIGHT_SEER
            return
        
        print(f"[信息] 存活狼人：{', '.join([f'{w.name}(玩家{w.player_id})' for w in werewolves])}")
        
        if self.agent_manager:
            print("[AI] 狼人正在讨论击杀目标...")
            await asyncio.sleep(2)
            
            # 显示模型思考过程（如果开启调试）
            if self.show_model_debug:
                print("\n" + "="*60)
                print("[模型思考] 狼人决策过程:")
                print("="*60)
            
            kill_target = await self.agent_manager.werewolf_choose_target(
                werewolves, self.state.alive_players, self.state.current_round,
                show_debug=self.show_model_debug
            )
            
            if self.show_model_debug:
                print("="*60)
            
            self.state.night_kill_target = kill_target
            
            target_player = self.state.get_player(kill_target) if kill_target else None
            print(f"[AI 决策] 狼人选择击杀：玩家{kill_target} ({target_player.name if target_player else '未知'})")
            
            # AI 思路 - 不暴露具体身份，只显示一般性分析
            if target_player:
                print("[AI 思路] 选择理由:")
                print("  - 该玩家可能是神职人员或威胁目标")
                print("  - 击杀可以削弱好人阵营")
        else:
            print("[测试模式] 跳过 AI 调用")
            self.state.night_kill_target = None
        
        print("[上帝] 狼人请闭眼")
        self.state.current_phase = GamePhase.NIGHT_SEER

    async def _night_seer(self):
        """预言家行动 - 上帝旁白 + AI 决策"""
        print("\n" + "-"*70)
        print("[上帝] 预言家请睁眼")
        print("-"*70)
        
        seer_player = None
        for pid in self.state.alive_players:
            player = self.state.get_player(pid)
            if player and player.role == Role.SEER:
                seer_player = player
                break
        
        if not seer_player:
            print("[状态] 预言家已死亡")
            print("[上帝] 预言家请闭眼")
            self.state.current_phase = GamePhase.NIGHT_WITCH
            return
        
        print(f"[信息] 预言家：{seer_player.name}(玩家{seer_player.player_id})")
        
        if self.agent_manager:
            print("[AI] 预言家正在思考查验目标...")
            await asyncio.sleep(2)
            
            check_target = await self.agent_manager.seer_choose_target(
                seer_player, self.state.alive_players, self.state.current_round
            )
            
            if check_target:
                target_player = self.state.get_player(check_target)
                check_result = target_player.role if target_player else None
                
                self.state.seer_check_target = check_target
                self.state.seer_check_result = check_result
                
                # 更新预言家的查验记录
                agent = self.agent_manager.agents.get(seer_player.player_id)
                if agent and isinstance(agent, SeerAgent):
                    agent.add_checked_record(check_target)
                
                # 记录重要事件 - 预言家查验
                result_text = "狼人" if check_result == Role.WEREWOLF else "好人"
                seer_player.add_important_event(
                    event_type="seer_check",
                    round_number=self.state.current_round,
                    details=f"查验玩家{check_target}({target_player.name})，结果为{result_text}"
                )
                
                print(f"[AI 决策] 预言家查验：玩家{check_target} ({target_player.name})")
                print(f"[AI 结果] {result_text}")
        
        print("[上帝] 预言家请闭眼")
        self.state.current_phase = GamePhase.NIGHT_WITCH

    async def _night_witch(self):
        """女巫行动 - 上帝旁白 + AI 决策"""
        print("\n" + "-"*70)
        print("[上帝] 女巫请睁眼")
        print("-"*70)
        
        witch_player = None
        for pid in self.state.alive_players:
            player = self.state.get_player(pid)
            if player and player.role == Role.WITCH:
                witch_player = player
                break
        
        if not witch_player:
            print("[状态] 女巫已死亡")
            print("[上帝] 女巫请闭眼")
            self.state.current_phase = GamePhase.NIGHT_END
            return
        
        print(f"[信息] 女巫：{witch_player.name}(玩家{witch_player.player_id})")
        
        if self.state.night_kill_target:
            killed_player = self.state.get_player(self.state.night_kill_target)
            print(f"[信息] 今晚狼刀目标：玩家{self.state.night_kill_target} ({killed_player.name})")
        
        if self.agent_manager:
            print("[AI] 女巫正在思考是否使用药剂...")
            await asyncio.sleep(2)
            
            # 显示 AI 分析过程 - 不暴露具体身份
            print("[AI 分析] 评估当前局势:")
            if self.state.night_kill_target:
                print(f"  - 今晚有玩家被击杀")
                print(f"  - 需要权衡是否暴露解药")
            
            if not self.state.witch_used_save:
                print(f"[AI 分析] 解药状态：可用")
                print(f"[AI 思考] 救人的利弊:")
                print(f"  - 利：保存好人数量，可能暴露女巫身份")
                print(f"  - 弊：暴露解药已用，成为狼人目标")
            
            if not self.state.witch_used_poison:
                print(f"[AI 分析] 毒药状态：可用")
                print(f"[AI 思考] 毒人的时机:")
                print(f"  - 需要找可疑的狼人目标")
                print(f"  - 避免误毒好人")
            
            await asyncio.sleep(2)
            
            save_target, poison_target = await self.agent_manager.witch_make_decision(
                witch_player, self.state.night_kill_target, self.state.alive_players, self.state.current_round
            )
            
            if save_target and not self.state.witch_used_save:
                self.state.witch_save_target = save_target
                self.state.witch_used_save = True
                saved_player = self.state.get_player(save_target)
                print(f"\n[AI 决策] 女巫使用解药：救了玩家{save_target} ({saved_player.name})")
                print(f"[AI 思路] 选择理由:")
                print(f"  - 该玩家可能是神职人员")
                print(f"  - 救他可以隐藏我的身份")
                
                # 记录重要事件 - 女巫救人（所有存活玩家都知道谁被救了）
                for pid in self.state.alive_players:
                    player = self.state.get_player(pid)
                    if player:
                        player.add_important_event(
                            event_type="witch_save",
                            round_number=self.state.current_round,
                            details=f"第{self.state.current_round}夜女巫使用解药救了玩家{save_target}({saved_player.name})"
                        )
            
            if poison_target and not self.state.witch_used_poison:
                self.state.witch_poison_target = poison_target
                self.state.witch_used_poison = True
                poisoned_player = self.state.get_player(poison_target)
                print(f"\n[AI 决策] 女巫使用毒药：毒了玩家{poison_target} ({poisoned_player.name})")
                print(f"[AI 思路] 选择理由:")
                print(f"  - 该玩家行为可疑")
                print(f"  - 可能是狼人，需要除掉")
                
                # 记录重要事件 - 女巫毒人
                for pid in self.state.alive_players:
                    player = self.state.get_player(pid)
                    if player:
                        player.add_important_event(
                            event_type="witch_poison",
                            round_number=self.state.current_round,
                            details=f"第{self.state.current_round}夜女巫使用毒药毒了玩家{poison_target}({poisoned_player.name})"
                        )
            
            if not save_target and not poison_target:
                print(f"\n[AI 决策] 女巫选择按兵不动")
                print(f"[AI 思路] 选择理由:")
                print(f"  - 局势不明朗，等待更好时机")
                print(f"  - 保留药剂到关键时刻")
                
            print(f"\n[完成] 女巫行动结束")
        else:
            print("[测试模式] 跳过 AI 调用")
        
        print("[上帝] 女巫请闭眼")
        print("\n[系统] 夜晚行动结束，即将进入白天...")
        await asyncio.sleep(1)
        self.state.current_phase = GamePhase.NIGHT_END

    async def _day_start(self):
        """白天开始 - 上帝旁白 + 结算夜晚"""
        print("\n" + "="*70)
        print("[上帝] 天亮了")
        print("="*70)
        
        # 结算夜晚死亡
        from rules.night_rules import NightRules
        
        print("\n[系统] 正在结算夜晚行动...")
        await asyncio.sleep(1)
        
        deaths = NightRules.resolve_night_actions(self.state)
        self.state.deaths_this_night = deaths
        
        for player_id in deaths:
            self.state.remove_player(player_id)
        
        if deaths:
            death_names = [
                f"玩家{pid} ({self.state.get_player(pid).name})" 
                for pid in deaths
            ]
            print(f"\n[上帝] 昨晚死亡的玩家：{', '.join(death_names)}")
            
            # AI 分析 - 不暴露具体身份，只分析局势影响
            if self.agent_manager:
                print("\n[AI 分析] 夜晚死亡分析:")
                for pid in deaths:
                    player = self.state.get_player(pid)
                    if player:
                        print(f"  - {player.name}(玩家{pid}) 出局")
                        print(f"    [分析] 该玩家的死亡会影响场上局势")
                        print(f"    [推测] 可能是神职人员或普通村民")
        else:
            print(f"\n[上帝] 昨晚是平安夜")
            if self.agent_manager:
                print("\n[AI 分析] 平安夜分析:")
                print("  - 女巫可能使用了解药")
                print("  - 或者狼人未选择击杀目标")
        
        print("\n[系统] 准备进入白天讨论阶段...")
        await asyncio.sleep(2)
        
        self.state.discussion_order = sorted(self.state.alive_players)
        self.state.current_phase = GamePhase.DAY_DISCUSSION

    async def _day_discussion(self):
        """白天讨论 - AI 自动发言"""
        print("\n" + "-"*70)
        print("[上帝] 现在开始轮流发言")
        print("-"*70)
        
        if not self.agent_manager:
            print("[测试模式] 跳过 AI 发言")
            self.state.current_phase = GamePhase.DAY_VOTING
            return
        
        print(f"[信息] 本回合共有 {len(self.state.discussion_order)} 位玩家存活")
        print(f"[系统] 每位玩家将进行{30}秒左右的发言\n")
        
        # 按顺序让每个玩家发言
        for idx, speaker_id in enumerate(self.state.discussion_order, 1):
            speaker = self.state.get_alive_player(speaker_id)
            if not speaker:
                continue
            
            print(f"\n{'='*60}")
            print(f"[{idx}/{len(self.state.discussion_order)}] 玩家{speaker_id} {speaker.name} 开始发言")
            print(f"{'='*60}")
            
            # 显示 AI 思考过程 - 不暴露具体身份
            if self.agent_manager:
                print(f"[AI 思考] {speaker.name}正在组织发言内容...")
                await asyncio.sleep(1)
                
                # 根据角色显示不同的思考 - 但不暴露具体身份
                if speaker.role == Role.WEREWOLF:
                    print(f"[AI 思路] 发言策略:")
                    print(f"  - 伪装成好人，融入好人阵营")
                    print(f"  - 分析其他玩家发言找破绽")
                    print(f"  - 避免被怀疑，引导局势")
                elif speaker.role == Role.SEER:
                    print(f"[AI 思路] 发言策略:")
                    print(f"  - 考虑是否透露身份信息")
                    print(f"  - 保护自己是关键")
                    print(f"  - 为好人提供有价值信息")
                elif speaker.role == Role.VILLAGER:
                    print(f"[AI 思路] 发言策略:")
                    print(f"  - 分析已知信息")
                    print(f"  - 找出逻辑矛盾点")
                    print(f"  - 为好人阵营贡献观点")
                else:  # 神职人员（女巫、猎人）
                    print(f"[AI 思路] 发言策略:")
                    print(f"  - 隐藏身份信息")
                    print(f"  - 观察场上形势")
                    print(f"  - 在关键时刻发挥作用")
            
            # 获取发言内容
            speech = await self.agent_manager.get_day_speech(
                speaker, self.state, self.state.current_round
            )
            
            print(f"\n[发言内容]:\n")
            # 逐字输出
            for char in speech:
                print(char, end='', flush=True)
                await asyncio.sleep(0.02)
            print()
            
            # 记录发言
            discussion = DayDiscussion(
                round_number=self.state.current_round,
                speaker_id=speaker_id,
                speech_text=speech,
            )
            self.state.day_discussions.append(discussion)
            
            # 添加到记忆
            for pid in self.state.alive_players:
                player = self.state.get_player(pid)
                if player:
                    player.add_memory(
                        f"第{self.state.current_round}天，{speaker.name}说：{speech[:100]}..."
                    )
            
            print(f"[完成] 玩家{speaker_id} 发言结束")
            await asyncio.sleep(0.5)
        
        print(f"\n[上帝] 所有玩家发言结束")
        self.state.current_phase = GamePhase.DAY_VOTING

    async def _day_voting(self):
        """投票放逐 - AI 自动投票"""
        print("\n" + "="*70)
        print("[上帝] 现在开始投票")
        print("="*70)
        
        if not self.agent_manager:
            print("[测试模式] 跳过 AI 投票")
            self.state.current_phase = GamePhase.DAY_END
            return
        
        vote_counts = {}
        
        # 每个玩家投票
        for idx, voter_id in enumerate(self.state.alive_players, 1):
            voter = self.state.get_player(voter_id)
            if not voter:
                continue
            
            print(f"\n[{idx}/{len(self.state.alive_players)}] 玩家{voter_id} ({voter.name}) 正在投票...")
            await asyncio.sleep(1)
            
            vote_target = await self.agent_manager.get_vote_target(
                voter, self.state, self.state.current_round
            )
            
            vote_record = VoteRecord(
                round_number=self.state.current_round,
                voter_id=voter_id,
                vote_target=vote_target,
            )
            self.state.vote_records.append(vote_record)
            
            target_name = f"玩家{vote_target}" if vote_target else "弃票"
            print(f"  -> 投票给：{target_name}")
            
            if vote_target is not None:
                vote_counts[vote_target] = vote_counts.get(vote_target, 0) + 1
        
        # 统计票数
        print(f"\n{'-'*60}")
        print("[上帝] 投票结果统计:")
        print(f"{'-'*60}")
        for target, count in sorted(vote_counts.items(), key=lambda x: -x[1]):
            target_player = self.state.get_player(target)
            print(f"  玩家{target} ({target_player.name if target_player else '未知'}): {count}票")
        
        # 计算被放逐的玩家
        eliminated = None
        if vote_counts:
            max_votes = max(vote_counts.values())
            top_candidates = [k for k, v in vote_counts.items() if v == max_votes]
            
            if len(top_candidates) == 1:
                eliminated = top_candidates[0]
        
        print(f"\n{'-'*60}")
        if eliminated:
            elim_player = self.state.get_player(eliminated)
            print(f"[上帝] 玩家{eliminated} ({elim_player.name}) 被放逐")
            
            # 记录重要事件 - 投票出局（所有存活玩家都要记录）
            for pid in self.state.alive_players:
                player = self.state.get_player(pid)
                if player:
                    player.add_important_event(
                        event_type="vote_eliminated",
                        round_number=self.state.current_round,
                        details=f"玩家{eliminated}({elim_player.name}) 在第{self.state.current_round}天被投票放逐"
                    )
            
            self.state.remove_player(eliminated)
            self.state.eliminated_players.append(eliminated)
            self.state.vote_eliminated = eliminated
            
            # 检查猎人技能
            if elim_player and elim_player.role == Role.HUNTER:
                print(f"[上帝] 猎人发动技能")
                await asyncio.sleep(1)
                hunter_target = await self.agent_manager.hunter_use_skill(
                    elim_player, self.state.alive_players
                )
                if hunter_target:
                    self.state.remove_player(hunter_target)
                    self.state.deaths_today.append(hunter_target)
                    hunter_player = self.state.get_player(hunter_target)
                    print(f"  -> 带走了玩家{hunter_target} ({hunter_player.name})")
        else:
            print(f"[上帝] 平票，无人被放逐")
        
        self.state.current_phase = GamePhase.DAY_END

    async def _next_round(self):
        """进入下一轮"""
        # 检查游戏是否结束
        game_over, winner, reason = self._check_game_end()
        
        if game_over:
            self.state.winner = winner
            self.state.game_end_reason = reason
            self.state.current_phase = GamePhase.GAME_OVER
            print(f"\n[上帝] 游戏结束")
            print(f"[获胜方] {winner}")
            print(f"[原因] {reason}")
        else:
            # 进入下一夜
            self.state.current_round += 1
            self.state.current_phase = GamePhase.NIGHT_START
            self.state.night_kill_target = None
            self.state.seer_check_target = None
            self.state.seer_check_result = None
            self.state.witch_save_target = None
            self.state.witch_poison_target = None
            self.state.deaths_this_night = []
            self.state.vote_eliminated = None
            print(f"\n[上帝] 进入第 {self.state.current_round} 夜")

    def _check_game_end(self):
        """检查游戏是否结束"""
        alive_werewolves = [
            wid for wid in self.state.werewolf_players 
            if wid in self.state.alive_players
        ]
        
        if not alive_werewolves:
            return True, "好人阵营", "所有狼人被淘汰"
        
        good_players_count = len(self.state.alive_players) - len(alive_werewolves)
        if len(alive_werewolves) >= good_players_count:
            return True, "狼人阵营", "狼人数量达到或超过好人"
        
        return False, None, None

    def _handle_game_over(self):
        """游戏结束"""
        self.display.print_header("游戏结束 - 最终状态")
        self.display.display_player_status(self.state)
        
        print(f"\n[获胜方] {self.state.winner}")
        print(f"[原因] {self.state.game_end_reason}")
        
        # 导出记录
        self._export_full_record()
        
        print("\n感谢观看！完整记录已保存到 logs/ 目录\n")

    def _export_full_record(self):
        """导出完整对局记录"""
        md_path = self.speech_recorder.export_markdown(
            str(self.display.log_dir / "speeches.md")
        )
        self.logger.export_json(
            str(self.display.log_dir / "game_log.json")
        )
        summary = self.action_recorder.export_summary()
        import json
        with open(self.display.log_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
