"""
CSV parser for bank statement files
"""
import logging
import csv
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class CSVParser(BaseParser):
    """
    Parser for CSV bank statement files
    Поддерживает различные форматы CSV выписок
    """

    def parse(self) -> List[Dict[str, Any]]:
        """
        Parse CSV file and extract transactions

        Returns:
            List of transaction dictionaries
        """
        try:
            # Try pandas first (handles various encodings and formats)
            df = pd.read_csv(self.file_path, encoding="utf-8")
        except UnicodeDecodeError:
            # Fallback to cp1251 (common for Russian banks)
            df = pd.read_csv(self.file_path, encoding="cp1251")
        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {str(e)}")

        # Detect column names (normalize case and whitespace)
        df.columns = [col.strip().lower() for col in df.columns]

        transactions = []
        for index, row in df.iterrows():
            try:
                transaction = self._parse_row(row, index)
                if transaction and self.validate_transaction(transaction):
                    cleaned = self.clean_transaction(transaction)
                    transactions.append(cleaned)
            except Exception as e:
                # Log error but continue parsing
                logger.debug(f"Error parsing CSV row {index}: {e}")
                continue

        return transactions

    def _parse_row(self, row: pd.Series, row_index: int) -> Dict[str, Any]:
        """
        Parse a single CSV row into transaction dict

        Args:
            row: Pandas series representing a CSV row
            row_index: Index of the row

        Returns:
            Transaction dictionary or None if invalid
        """
        transaction = {}

        # Amount (try common column names)
        amount_col = self._find_column(row, ["сумма", "amount", "sum", "summa", "сума"])
        if amount_col is None:
            return None

        try:
            amount = float(str(row[amount_col]).replace(",", ".").replace(" ", ""))
            transaction["amount"] = amount
        except (ValueError, TypeError):
            return None

        # Transaction type (determine from amount sign or type column)
        type_col = self._find_column(row, ["тип", "type", "вид", "операция", "operation"])
        if type_col:
            type_value = str(row[type_col]).lower()
            if any(word in type_value for word in ["приход", "поступление", "income", "incoming", "зачисление"]):
                transaction["transaction_type"] = "incoming"
            elif any(word in type_value for word in ["расход", "списание", "outgoing", "expense", "payment"]):
                transaction["transaction_type"] = "outgoing"
            elif any(word in type_value for word in ["перевод", "transfer"]):
                transaction["transaction_type"] = "transfer"
            else:
                transaction["transaction_type"] = "incoming" if amount > 0 else "outgoing"
        else:
            # Determine from amount sign
            transaction["transaction_type"] = "incoming" if amount > 0 else "outgoing"

        # Date
        date_col = self._find_column(row, ["дата", "date", "дата операции", "transaction_date", "operation_date"])
        if date_col is None:
            return None

        try:
            date_str = str(row[date_col])
            transaction["transaction_date"] = self._parse_date(date_str)
        except Exception:
            return None

        # Currency
        currency_col = self._find_column(row, ["валюта", "currency", "curr"])
        if currency_col:
            transaction["currency"] = str(row[currency_col]).upper()
        else:
            transaction["currency"] = "KZT"

        # Counterparty information
        counterparty_col = self._find_column(row, [
            "контрагент", "counterparty", "плательщик", "получатель", "payer", "payee", "контрагент/назначение"
        ])
        if counterparty_col:
            transaction["counterparty_name"] = str(row[counterparty_col])

        # Account number
        account_col = self._find_column(row, ["счет", "account", "счет контрагента", "counterparty_account"])
        if account_col:
            transaction["counterparty_account"] = str(row[account_col])

        # Bank
        bank_col = self._find_column(row, ["банк", "bank", "банк контрагента", "counterparty_bank"])
        if bank_col:
            transaction["counterparty_bank"] = str(row[bank_col])

        # IIN/BIN
        iin_col = self._find_column(row, ["иин", "бин", "iin", "bin", "iin/bin", "ИИН/БИН"])
        if iin_col:
            transaction["counterparty_iin_bin"] = str(row[iin_col])

        # Description
        desc_col = self._find_column(row, [
            "описание", "description", "назначение", "purpose", "назначение платежа", "payment_purpose", "примечание", "note"
        ])
        if desc_col:
            transaction["description"] = str(row[desc_col])

        # Payment purpose (may be same as description)
        purpose_col = self._find_column(row, ["назначение платежа", "payment_purpose", "purpose"])
        if purpose_col:
            transaction["payment_purpose"] = str(row[purpose_col])
        elif desc_col:
            transaction["payment_purpose"] = transaction["description"]

        return transaction

    def _find_column(self, row: pd.Series, possible_names: List[str]) -> str:
        """
        Find column name from list of possible names

        Args:
            row: Pandas series
            possible_names: List of possible column names

        Returns:
            Column name if found, None otherwise
        """
        for name in possible_names:
            if name in row.index:
                return name
        return None

    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string into datetime object

        Args:
            date_str: Date string in various formats

        Returns:
            Datetime object
        """
        # Common date formats
        formats = [
            "%Y-%m-%d",
            "%d.%m.%Y",
            "%d/%m/%Y",
            "%Y.%m.%d",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d.%m.%Y %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # If all fails, try pandas
        try:
            return pd.to_datetime(date_str)
        except Exception:
            raise ValueError(f"Unable to parse date: {date_str}")
