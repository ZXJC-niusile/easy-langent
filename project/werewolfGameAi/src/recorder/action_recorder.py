"""
行动记录器
记录夜晚行动和投票结果
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class ActionRecorder:
    """行动记录器类"""

    def __init__(self, log_dir: str = "logs"):
        """
        初始化行动记录器

        Args:
            log_dir: 日志目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.action_file = self.log_dir / "actions.json"
        self.vote_file = self.log_dir / "votes.json"
        self.action_records: list[dict] = []
        self.vote_records: list[dict] = []

    def record_night_action(
        self,
        round_number: int,
        actor_id: int,
        action_type: str,
        target_id: Optional[int],
        result: str,
    ):
        """
        记录夜晚行动

        Args:
            round_number: 回合数
            actor_id: 行动者 ID
            action_type: 行动类型（kill/check/save/poison）
            target_id: 目标 ID
            result: 行动结果
        """
        record = {
            "round_number": round_number,
            "timestamp": datetime.now().isoformat(),
            "actor_id": actor_id,
            "action_type": action_type,
            "target_id": target_id,
            "result": result,
        }
        self.action_records.append(record)

    def record_vote(
        self,
        round_number: int,
        voter_id: int,
        vote_target: Optional[int],
        outcome: str = "",
    ):
        """
        记录投票

        Args:
            round_number: 回合数
            voter_id: 投票者 ID
            vote_target: 投票目标
            outcome: 结果（成功/失败/平票等）
        """
        record = {
            "round_number": round_number,
            "timestamp": datetime.now().isoformat(),
            "voter_id": voter_id,
            "vote_target": vote_target,
            "outcome": outcome,
        }
        self.vote_records.append(record)

    def get_night_actions(
        self, round_number: Optional[int] = None, action_type: Optional[str] = None
    ) -> list[dict]:
        """
        查询夜晚行动记录

        Args:
            round_number: 回合数（可选）
            action_type: 行动类型（可选）

        Returns:
            符合条件的行动记录列表
        """
        results = self.action_records

        if round_number is not None:
            results = [r for r in results if r["round_number"] == round_number]

        if action_type is not None:
            results = [r for r in results if r["action_type"] == action_type]

        return results

    def get_votes(self, round_number: Optional[int] = None) -> list[dict]:
        """
        查询投票记录

        Args:
            round_number: 回合数（可选）

        Returns:
            符合条件的投票记录列表
        """
        if round_number is not None:
            return [r for r in self.vote_records if r["round_number"] == round_number]
        return self.vote_records

    def save_to_file(self):
        """保存到 JSON 文件"""
        with open(self.action_file, "w", encoding="utf-8") as f:
            json.dump(self.action_records, f, ensure_ascii=False, indent=2)

        with open(self.vote_file, "w", encoding="utf-8") as f:
            json.dump(self.vote_records, f, ensure_ascii=False, indent=2)

    def load_from_file(self):
        """从 JSON 文件加载"""
        if self.action_file.exists():
            with open(self.action_file, "r", encoding="utf-8") as f:
                self.action_records = json.load(f)

        if self.vote_file.exists():
            with open(self.vote_file, "r", encoding="utf-8") as f:
                self.vote_records = json.load(f)

    def clear(self):
        """清空记录"""
        self.action_records = []
        self.vote_records = []

    def export_summary(self) -> dict:
        """
        导出对局摘要

        Returns:
            对局摘要字典
        """
        summary = {
            "total_rounds": max([r["round_number"] for r in self.action_records], default=0),
            "night_actions": len(self.action_records),
            "total_votes": len(self.vote_records),
            "actions_by_type": {},
            "votes_by_round": {},
        }

        # 统计行动类型
        for record in self.action_records:
            action_type = record["action_type"]
            summary["actions_by_type"][action_type] = (
                summary["actions_by_type"].get(action_type, 0) + 1
            )

        # 统计每轮投票数
        for record in self.vote_records:
            rnd = record["round_number"]
            summary["votes_by_round"][rnd] = (
                summary["votes_by_round"].get(rnd, 0) + 1
            )

        return summary
