"""
Абстрактный базовый класс для AI провайдеров
Все провайдеры (Claude, Ollama, etc.) наследуются от этого класса
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum


class AIProvider(Enum):
    CLAUDE = "claude"
    OLLAMA = "ollama"


class BaseAIProvider(ABC):
    """Абстрактный AI провайдер"""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "",
                       max_tokens: int = 4096) -> str:
        """Генерация текстового ответа"""
        pass

    @abstractmethod
    async def generate_structured(self, prompt: str, schema: Dict[str, Any],
                                   system_prompt: str = "") -> Dict[str, Any]:
        """Генерация структурированного JSON ответа"""
        pass

    @abstractmethod
    async def check_connection(self) -> bool:
        """Проверка доступности провайдера"""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Имя провайдера"""
        pass
