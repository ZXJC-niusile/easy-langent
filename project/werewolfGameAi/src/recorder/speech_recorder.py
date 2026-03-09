"""
发言记录器
结构化存储每个 AI 智能体的发言内容
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class SpeechRecorder:
    """发言记录器类"""

    def __init__(self, log_dir: str = "logs"):
        """
        初始化发言记录器

        Args:
            log_dir: 日志目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.speech_file = self.log_dir / "speeches.json"
        self.records: list[dict] = []

    def record_speech(
        self,
        player_id: int,
        player_name: str,
        role: str,
        speech_text: str,
        round_number: int,
        phase: str = "day_discussion",
    ):
        """
        记录发言

        Args:
            player_id: 玩家 ID
            player_name: 玩家名称
            role: 角色
            speech_text: 发言内容
            round_number: 回合数
            phase: 阶段（day_discussion/night_action 等）
        """
        record = {
            "player_id": player_id,
            "player_name": player_name,
            "role": role,
            "speech_text": speech_text,
            "timestamp": datetime.now().isoformat(),
            "round_number": round_number,
            "phase": phase,
        }
        self.records.append(record)

    def get_speeches(
        self,
        player_id: Optional[int] = None,
        round_number: Optional[int] = None,
        phase: Optional[str] = None,
    ) -> list[dict]:
        """
        查询发言记录

        Args:
            player_id: 玩家 ID（可选）
            round_number: 回合数（可选）
            phase: 阶段（可选）

        Returns:
            符合条件的发言记录列表
        """
        results = self.records

        if player_id is not None:
            results = [r for r in results if r["player_id"] == player_id]

        if round_number is not None:
            results = [r for r in results if r["round_number"] == round_number]

        if phase is not None:
            results = [r for r in results if r["phase"] == phase]

        return results

    def get_speeches_by_round(self, round_number: int) -> list[dict]:
        """获取指定回合的所有发言"""
        return self.get_speeches(round_number=round_number)

    def get_player_speeches(self, player_id: int) -> list[dict]:
        """获取指定玩家的所有发言"""
        return self.get_speeches(player_id=player_id)

    def save_to_file(self):
        """保存到 JSON 文件"""
        with open(self.speech_file, "w", encoding="utf-8") as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)

    def load_from_file(self):
        """从 JSON 文件加载"""
        if self.speech_file.exists():
            with open(self.speech_file, "r", encoding="utf-8") as f:
                self.records = json.load(f)

    def clear(self):
        """清空记录"""
        self.records = []

    def export_markdown(self, output_path: Optional[str] = None) -> str:
        """
        导出为 Markdown 格式

        Args:
            output_path: 输出路径（可选）

        Returns:
            Markdown 内容
        """
        md_lines = ["# 狼人杀对局发言记录\n"]

        # 按回合分组
        rounds = {}
        for record in self.records:
            rnd = record["round_number"]
            if rnd not in rounds:
                rounds[rnd] = []
            rounds[rnd].append(record)

        for rnd in sorted(rounds.keys()):
            md_lines.append(f"## 第{rnd}天\n")
            speeches = rounds[rnd]
            for speech in speeches:
                time_str = speech["timestamp"][11:19]
                md_lines.append(
                    f"### [{time_str}] 玩家{speech['player_id']} ({speech['role']})\n"
                )
                md_lines.append(f"{speech['speech_text']}\n")
            md_lines.append("")

        content = "\n".join(md_lines)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

        return content
