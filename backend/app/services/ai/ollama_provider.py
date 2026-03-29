"""
Ollama провайдер (локальный LLM)
Совместим с существующим OllamaAnalyzer
"""
import json
import logging
from typing import Dict, Any
import httpx
from .base_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseAIProvider):
    """Локальный Ollama провайдер"""

    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3:8b"):
        self.host = host.rstrip("/")
        self.model = model

    async def generate(self, prompt: str, system_prompt: str = "",
                       max_tokens: int = 4096) -> str:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {"num_predict": max_tokens}
                }
            )
            response.raise_for_status()
            return response.json().get("response", "")

    async def generate_structured(self, prompt: str, schema: Dict[str, Any],
                                   system_prompt: str = "") -> Dict[str, Any]:
        """Ollama не поддерживает tool_use, используем JSON-промпт"""
        json_prompt = (
            f"{prompt}\n\n"
            f"IMPORTANT: Respond ONLY with a valid JSON object matching this schema:\n"
            f"{json.dumps(schema, indent=2)}\n"
            f"No text before or after the JSON."
        )

        response_text = await self.generate(json_prompt, system_prompt)

        # Извлечь JSON из ответа
        try:
            # Попробовать напрямую
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Найти JSON блок в ответе
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(response_text[start:end])
                except json.JSONDecodeError:
                    pass
        return {}

    async def check_connection(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.host}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    @property
    def provider_name(self) -> str:
        return "Ollama (local)"
