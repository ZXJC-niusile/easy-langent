"""
游戏日志记录器
负责输出和保存游戏日志
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class GameLogger:
    """游戏日志记录器"""

    def __init__(self, log_dir: str = "logs", level: str = "INFO"):
        """
        初始化游戏日志记录器

        Args:
            log_dir: 日志目录
            level: 日志级别
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 创建 logger
        self.logger = logging.getLogger("WerewolfGame")
        self.logger.setLevel(getattr(logging, level.upper()))

        # 清除已有的 handlers
        self.logger.handlers = []

        # 文件 handler
        log_file = self.log_dir / f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # 控制台 handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        self.game_log_file = log_file
        self.messages: list[dict] = []

    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
        self._add_message("info", message)

    def debug(self, message: str):
        """记录调试日志"""
        self.logger.debug(message)
        self._add_message("debug", message)

    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)
        self._add_message("warning", message)

    def error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)
        self._add_message("error", message)

    def _add_message(self, level: str, message: str):
        """添加消息到内存列表"""
        self.messages.append(
            {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message,
            }
        )

    def log_game_event(self, event_type: str, details: dict):
        """
        记录游戏事件

        Args:
            event_type: 事件类型
            details: 事件详情
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details,
        }
        self.messages.append(event)
        self.logger.info(f"[{event_type}] {json.dumps(details, ensure_ascii=False)}")

    def get_messages(
        self,
        level: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> list[dict]:
        """
        获取日志消息

        Args:
            level: 日志级别过滤
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            消息列表
        """
        results = self.messages

        if level:
            results = [m for m in results if m.get("level") == level]

        if start_time:
            results = [
                m for m in results if m.get("timestamp", "") >= start_time
            ]

        if end_time:
            results = [
                m for m in results if m.get("timestamp", "") <= end_time
            ]

        return results

    def export_json(self, output_path: Optional[str] = None) -> str:
        """
        导出为 JSON

        Args:
            output_path: 输出路径（可选）

        Returns:
            JSON 内容
        """
        content = json.dumps(self.messages, ensure_ascii=False, indent=2)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

        return content

    def get_log_file_path(self) -> str:
        """获取日志文件路径"""
        return str(self.game_log_file)
