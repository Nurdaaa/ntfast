"""
Excel parser for bank statement files
"""
import logging
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
from .csv_parser import CSVParser

logger = logging.getLogger(__name__)


class ExcelParser(CSVParser):
    """
    Parser for Excel bank statement files
    Наследует от CSVParser так как логика парсинга очень похожа
    """

    def parse(self) -> List[Dict[str, Any]]:
        """
        Parse Excel file and extract transactions

        Returns:
            List of transaction dictionaries
        """
        try:
            # Read Excel file
            df = pd.read_excel(self.file_path, engine='openpyxl')
        except Exception as e:
            # Fallback to old Excel format
            try:
                df = pd.read_excel(self.file_path, engine='xlrd')
            except Exception as e2:
                raise ValueError(f"Failed to read Excel file: {str(e)}, Fallback error: {str(e2)}")

        # Skip empty rows at the beginning (common in bank statements)
        df = df.dropna(how='all')

        # Detect header row (look for common keywords)
        header_keywords = ["дата", "date", "сумма", "amount", "контрагент", "counterparty"]
        header_row = 0

        for idx, row in df.iterrows():
            row_str = " ".join([str(val).lower() for val in row if pd.notna(val)])
            if any(keyword in row_str for keyword in header_keywords):
                header_row = idx
                break

        # Re-read with correct header
        if header_row > 0:
            df = pd.read_excel(self.file_path, header=header_row, engine='openpyxl' if self.file_path.suffix == '.xlsx' else 'xlrd')

        # Normalize column names
        df.columns = [str(col).strip().lower() for col in df.columns]

        # Remove completely empty rows
        df = df.dropna(how='all')

        transactions = []
        for index, row in df.iterrows():
            try:
                transaction = self._parse_row(row, index)
                if transaction and self.validate_transaction(transaction):
                    cleaned = self.clean_transaction(transaction)
                    transactions.append(cleaned)
            except Exception as e:
                # Log error but continue parsing
                logger.debug(f"Error parsing Excel row {index}: {e}")
                continue

        return transactions
