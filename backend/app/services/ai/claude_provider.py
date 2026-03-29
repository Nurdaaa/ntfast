"""
Claude API провайдер (Anthropic)
Использует tool_use для structured output
"""
import logging
from typing import Dict, Any
from .base_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class ClaudeProvider(BaseAIProvider):
    """Anthropic Claude API провайдер"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=api_key)
        except ImportError:
            logger.warning("anthropic package not installed. Run: pip install anthropic")
            self.client = None
        self.model = model
        self._api_key = api_key

    async def generate(self, prompt: str, system_prompt: str = "",
                       max_tokens: int = 4096) -> str:
        if not self.client:
            raise RuntimeError("anthropic package not installed")

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = await self.client.messages.create(**kwargs)
        return response.content[0].text

    async def generate_structured(self, prompt: str, schema: Dict[str, Any],
                                   system_prompt: str = "") -> Dict[str, Any]:
        """Используем tool_use для получения структурированного JSON"""
        if not self.client:
            raise RuntimeError("anthropic package not installed")

        tool = {
            "name": "analysis_output",
            "description": "Output structured financial analysis data",
            "input_schema": schema
        }

        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
            "tools": [tool],
            "tool_choice": {"type": "tool", "name": "analysis_output"},
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = await self.client.messages.create(**kwargs)

        for block in response.content:
            if block.type == "tool_use":
                return block.input

        return {}

    async def check_connection(self) -> bool:
        if not self.client or not self._api_key:
            return False
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}]
            )
            return bool(response.content)
        except Exception as e:
            logger.debug(f"Claude connection check failed: {e}")
            return False

    @property
    def provider_name(self) -> str:
        return "Claude API"
