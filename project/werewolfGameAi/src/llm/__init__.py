"""
LLM 配置模块
支持所有 OpenAI 兼容接口的模型（DeepSeek/OpenAI/Moonshot/OneAPI 等）
"""

from .config import LLMConfig
from .factory import create_llm

__all__ = ["LLMConfig", "create_llm"]
