"""
LLM 配置管理类
从环境变量或 YAML 配置文件加载 LLM 配置
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


@dataclass
class LLMConfig:
    """LLM 配置类"""

    base_url: str = field(
        default_factory=lambda: os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    )
    api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    model_name: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL_NAME", "gpt-3.5-turbo")
    )
    temperature: float = field(
        default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.7"))
    )
    max_tokens: int = field(
        default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "2048"))
    )
    timeout: Optional[int] = field(
        default_factory=lambda: int(os.getenv("LLM_TIMEOUT", "60"))
        if os.getenv("LLM_TIMEOUT")
        else None
    )
    max_retries: int = field(
        default_factory=lambda: int(os.getenv("LLM_MAX_RETRIES", "3"))
    )

    def __post_init__(self):
        """验证配置"""
        if not self.api_key:
            raise ValueError(
                "LLM API Key 未设置，请在 .env 文件中配置 LLM_API_KEY 环境变量"
            )

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "LLMConfig":
        """从 YAML 配置文件加载配置"""
        import yaml

        with open(yaml_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        return cls(
            base_url=config_data.get("base_url", os.getenv("LLM_BASE_URL")),
            api_key=config_data.get("api_key", os.getenv("LLM_API_KEY")),
            model_name=config_data.get("model_name", os.getenv("LLM_MODEL_NAME")),
            temperature=config_data.get("temperature", 0.7),
            max_tokens=config_data.get("max_tokens", 2048),
            timeout=config_data.get("timeout"),
            max_retries=config_data.get("max_retries", 3),
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "base_url": self.base_url,
            "api_key": self.api_key[:8] + "..." if self.api_key else "",  # 隐藏密钥
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }

    def __str__(self) -> str:
        return (
            f"LLMConfig(model={self.model_name}, base_url={self.base_url}, "
            f"temperature={self.temperature}, max_tokens={self.max_tokens})"
        )
