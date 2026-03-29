"""
Универсальный анализатор банковских выписок

Поддерживаемые банки и платформы:
- Kaspi Bank (Казахстан)
- Halyk Bank (Казахстан) - в разработке
- Сбербанк (Казахстан/Россия) - в разработке
- Jusan Bank (Казахстан) - в разработке
- ForteBank (Казахстан) - в разработке
- Binance (Криптовалюта) - в разработке
- Freedom Finance (Брокер) - в разработке

Использование:
    from app.services.bank_analyzer import BankAnalyzer

    analyzer = BankAnalyzer("/path/to/statement.pdf")
    result = analyzer.analyze()
"""

from .analyzer import BankAnalyzer
from .detector import BankDetector, BankType, BankDetectionResult
from .base_parser import BaseParser, Transaction, TransactionType, AccountInfo

__all__ = [
    "BankAnalyzer",
    "BankDetector",
    "BankType",
    "BankDetectionResult",
    "BaseParser",
    "Transaction",
    "TransactionType",
    "AccountInfo",
]

__version__ = "3.0.0"
