"""
LLM 工厂模块
根据配置创建 LangChain ChatOpenAI 实例
"""

from langchain_openai import ChatOpenAI
from .config import LLMConfig


def create_llm(config: LLMConfig | None = None) -> ChatOpenAI:
    """
    创建 LLM 实例

    Args:
        config: LLM 配置，如果为 None 则使用默认配置

    Returns:
        ChatOpenAI 实例
    """
    if config is None:
        config = LLMConfig()

    # 创建 ChatOpenAI 实例
    llm = ChatOpenAI(
        base_url=config.base_url,
        api_key=config.api_key,
        model=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        timeout=config.timeout,
        max_retries=config.max_retries,
    )

    return llm


def create_llm_with_params(
    base_url: str | None = None,
    api_key: str | None = None,
    model_name: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> ChatOpenAI:
    """
    使用自定义参数创建 LLM 实例

    Args:
        base_url: API 基础 URL
        api_key: API 密钥
        model_name: 模型名称
        temperature: 温度参数
        max_tokens: 最大 token 数

    Returns:
        ChatOpenAI 实例
    """
    import os

    config = LLMConfig(
        base_url=base_url or os.getenv("LLM_BASE_URL"),
        api_key=api_key or os.getenv("LLM_API_KEY"),
        model_name=model_name or os.getenv("LLM_MODEL_NAME"),
        temperature=temperature or float(os.getenv("LLM_TEMPERATURE", "0.7")),
        max_tokens=max_tokens or int(os.getenv("LLM_MAX_TOKENS", "2048")),
    )

    return create_llm(config)
