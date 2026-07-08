"""
LLM service — supports OpenRouter, Google Gemini, and OpenAI.
OpenRouter is a unified API gateway compatible with the OpenAI SDK.
Initialized once and reused across the app via lru_cache.
"""
import logging
from functools import lru_cache
from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)


@lru_cache()
def get_llm() -> BaseChatModel:
    """
    Returns a cached LangChain chat model based on config.
    Supports: openrouter, gemini, openai
    """
    from config import get_settings
    settings = get_settings()

    provider = settings.llm_provider.lower()
    model = settings.effective_llm_model

    # ── ZAI (Zhipu AI Open Platform) ───────────────────────────────────
    if provider == "zai":
        if not settings.zai_api_key:
            raise ValueError("ZAI_API_KEY is not set in .env")
        logger.info(f"Using ZAI model: {model}")
        return ChatZAI(
            model_name=model,
            zai_api_key=settings.zai_api_key,
            temperature=0.3,
            max_tokens=8192
        )
    
    raise ValueError(f"Unsupported LLM provider: {provider}")

from typing import Any, List, Optional
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
import asyncio

class ChatZAI(BaseChatModel):
    model_name: str
    zai_api_key: str
    temperature: float = 0.3
    max_tokens: int = 8192

    @property
    def _llm_type(self) -> str:
        return "zai"

    def _convert_messages(self, messages: List[BaseMessage]) -> List[dict]:
        zai_msgs = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                zai_msgs.append({"role": "user", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                zai_msgs.append({"role": "system", "content": msg.content})
            elif isinstance(msg, AIMessage):
                zai_msgs.append({"role": "assistant", "content": msg.content})
            else:
                zai_msgs.append({"role": "user", "content": msg.content})
        return zai_msgs

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        from zhipuai import ZhipuAI
        client = ZhipuAI(api_key=self.zai_api_key)
        zai_messages = self._convert_messages(messages)
        
        response = client.chat.completions.create(
            model=self.model_name,
            messages=zai_messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        content = response.choices[0].message.content
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        return await asyncio.to_thread(self._generate, messages, stop, run_manager, **kwargs)


def extract_text(response) -> str:
    """Safely extract text from AIMessage, handling multi-modal list content."""
    content = response.content
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                texts.append(item["text"])
            elif isinstance(item, str):
                texts.append(item)
        return "".join(texts).strip()
    return str(content).strip()
