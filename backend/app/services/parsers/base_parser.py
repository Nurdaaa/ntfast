"""
Base parser for bank statement files
Базовый класс для всех парсеров
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path


class BaseParser(ABC):
    """
    Abstract base class for file parsers
    Все парсеры должны наследоваться от этого класса
    """

    def __init__(self, file_path: str):
        """
        Initialize parser with file path

        Args:
            file_path: Path to the file to parse
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

    @abstractmethod
    def parse(self) -> List[Dict[str, Any]]:
        """
        Parse the file and return list of transactions

        Returns:
            List of transaction dictionaries with keys:
            - amount: float
            - currency: str (optional, default "KZT")
            - transaction_type: str (incoming/outgoing/transfer)
            - transaction_date: datetime
            - counterparty_name: str (optional)
            - counterparty_account: str (optional)
            - counterparty_bank: str (optional)
            - counterparty_iin_bin: str (optional)
            - description: str (optional)
            - payment_purpose: str (optional)
        """
        pass

    def validate_transaction(self, transaction: Dict[str, Any]) -> bool:
        """
        Validate a transaction dictionary

        Args:
            transaction: Transaction dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["amount", "transaction_type", "transaction_date"]

        # Check required fields
        for field in required_fields:
            if field not in transaction:
                return False

        # Validate amount
        try:
            amount = float(transaction["amount"])
            if amount == 0:
                return False
        except (ValueError, TypeError):
            return False

        # Validate transaction type
        if transaction["transaction_type"] not in ["incoming", "outgoing", "transfer"]:
            return False

        # Validate date
        if not isinstance(transaction["transaction_date"], datetime):
            return False

        return True

    def clean_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and normalize transaction data

        Args:
            transaction: Raw transaction dictionary

        Returns:
            Cleaned transaction dictionary
        """
        cleaned = {}

        # Required fields
        cleaned["amount"] = abs(float(transaction["amount"]))
        cleaned["currency"] = transaction.get("currency", "KZT").upper()
        cleaned["transaction_type"] = transaction["transaction_type"].lower()
        cleaned["transaction_date"] = transaction["transaction_date"]

        # Optional fields
        optional_fields = [
            "counterparty_name",
            "counterparty_account",
            "counterparty_bank",
            "counterparty_iin_bin",
            "description",
            "payment_purpose",
        ]

        for field in optional_fields:
            if field in transaction and transaction[field]:
                # Clean strings: strip whitespace, remove extra spaces
                value = str(transaction[field]).strip()
                value = " ".join(value.split())  # Remove extra spaces
                cleaned[field] = value if value else None
            else:
                cleaned[field] = None

        return cleaned
