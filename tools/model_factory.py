"""多模型工厂

根据 config.LLM_PROVIDER 环境变量，创建对应的 LLM 实例。
支持智谱 GLM、Anthropic Claude、OpenAI 三种提供商。
"""

import importlib
import os

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI


def _get_config():
    """每次调用时重新加载 config，确保读取最新的环境变量"""
    import config
    importlib.reload(config)
    return config


def create_llm(temperature: float = 0.1, max_tokens: int = 16384) -> BaseChatModel:
    cfg = _get_config()

    if cfg.LLM_PROVIDER == "zhipu":
        return ChatOpenAI(
            model=cfg.ZHIPU_MODEL,
            api_key=cfg.ZHIPU_API_KEY,
            base_url=cfg.ZHIPU_API_BASE,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    elif cfg.LLM_PROVIDER == "claude":
        # 优先使用 Anthropic 原生接口，如果 API Key 为空则走 OpenAI 兼容代理
        if cfg.ANTHROPIC_API_KEY:
            try:
                from langchain_anthropic import ChatAnthropic
            except ImportError:
                raise ImportError("使用 Claude 需要 langchain-anthropic，请运行: pip install langchain-anthropic")
            return ChatAnthropic(
                model=cfg.CLAUDE_MODEL,
                api_key=cfg.ANTHROPIC_API_KEY,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            kwargs = {
                "model": cfg.CLAUDE_MODEL,
                "api_key": cfg.OPENAI_API_KEY,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if cfg.OPENAI_API_BASE:
                kwargs["base_url"] = cfg.OPENAI_API_BASE
            return ChatOpenAI(**kwargs)

    elif cfg.LLM_PROVIDER == "openai":
        kwargs = {
            "model": cfg.OPENAI_MODEL,
            "api_key": cfg.OPENAI_API_KEY,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if cfg.OPENAI_API_BASE:
            kwargs["base_url"] = cfg.OPENAI_API_BASE
        return ChatOpenAI(**kwargs)

    else:
        raise ValueError(f"不支持的模型提供商: {cfg.LLM_PROVIDER}，请设置 LLM_PROVIDER 为 zhipu/claude/openai")


def get_model_name() -> str:
    cfg = _get_config()
    if cfg.LLM_PROVIDER == "claude":
        return cfg.CLAUDE_MODEL
    names = {"zhipu": cfg.ZHIPU_MODEL, "openai": cfg.OPENAI_MODEL}
    return names.get(cfg.LLM_PROVIDER, "unknown")
