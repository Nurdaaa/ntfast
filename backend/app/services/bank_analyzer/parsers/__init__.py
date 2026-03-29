"""
Банковские парсеры для разных источников
"""
from .kaspi import KaspiParser
from .generic import GenericParser

__all__ = ["KaspiParser", "GenericParser"]
