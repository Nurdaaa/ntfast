"""
AI Manager — мультипровайдерная архитектура с fallback-цепочкой
Claude (primary) → Ollama (fallback)
"""
import logging
from typing import List, Tuple, Dict, Any, Optional
from .base_provider import BaseAIProvider
from .claude_provider import ClaudeProvider
from .ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)


class AIManager:
    """Управляет AI провайдерами с автоматическим fallback"""

    def __init__(self, claude_api_key: str = "", claude_model: str = "claude-sonnet-4-20250514",
                 ollama_host: str = "http://localhost:11434", ollama_model: str = "llama3:8b"):
        self.providers: List[BaseAIProvider] = []

        # Primary: Claude API
        if claude_api_key:
            self.providers.append(ClaudeProvider(
                api_key=claude_api_key,
                model=claude_model
            ))
            logger.info("Claude API provider configured as primary")

        # Fallback: Ollama (local)
        self.providers.append(OllamaProvider(
            host=ollama_host,
            model=ollama_model
        ))
        logger.info("Ollama provider configured as fallback")

    async def generate(self, prompt: str, system_prompt: str = "",
                       max_tokens: int = 4096) -> Tuple[str, str]:
        """
        Генерация ответа с fallback
        Returns: (response_text, provider_name)
        """
        for provider in self.providers:
            try:
                if await provider.check_connection():
                    response = await provider.generate(prompt, system_prompt, max_tokens)
                    logger.info(f"AI response from {provider.provider_name}")
                    return response, provider.provider_name
            except Exception as e:
                logger.warning(f"{provider.provider_name} failed: {e}")
                continue

        return "AI analysis unavailable — no providers connected", "none"

    async def generate_structured(self, prompt: str, schema: Dict[str, Any],
                                   system_prompt: str = "") -> Tuple[Dict[str, Any], str]:
        """
        Структурированная генерация с fallback
        Returns: (structured_data, provider_name)
        """
        for provider in self.providers:
            try:
                if await provider.check_connection():
                    result = await provider.generate_structured(prompt, schema, system_prompt)
                    if result:
                        logger.info(f"Structured AI response from {provider.provider_name}")
                        return result, provider.provider_name
            except Exception as e:
                logger.warning(f"{provider.provider_name} structured generation failed: {e}")
                continue

        return {}, "none"

    async def get_status(self) -> Dict[str, Any]:
        """Статус всех провайдеров"""
        status = {"providers": [], "active_provider": None}
        for provider in self.providers:
            try:
                connected = await provider.check_connection()
            except Exception:
                connected = False

            info = {
                "name": provider.provider_name,
                "connected": connected,
            }
            status["providers"].append(info)
            if connected and status["active_provider"] is None:
                status["active_provider"] = provider.provider_name

        return status
