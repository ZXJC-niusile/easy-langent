"""
提示词模板模块
"""

from .role_prompts import get_role_system_prompt, ROLE_PROMPTS
from .action_prompts import get_action_prompt, ACTION_PROMPTS

__all__ = [
    "get_role_system_prompt",
    "ROLE_PROMPTS",
    "get_action_prompt",
    "ACTION_PROMPTS",
]
