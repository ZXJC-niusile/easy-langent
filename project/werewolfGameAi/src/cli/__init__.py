"""
CLI 交互模块
提供命令行界面供用户以上帝视角观测游戏
"""

from .display import DisplayManager
from .game_viewer import GameViewer

__all__ = ["DisplayManager", "GameViewer"]
