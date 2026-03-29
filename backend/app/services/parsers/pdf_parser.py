"""
PDF parser for bank statement files
"""
import logging
import pdfplumber
import re
from typing import List, Dict, Any
from datetime import datetime
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class PDFParser(BaseParser):
    """
    Parser for PDF bank statement files
    Извлекает текст и таблицы из PDF файлов
    """

    def parse(self) -> List[Dict[str, Any]]:
        """
        Parse PDF file and extract transactions

        Returns:
            List of transaction dictionaries
        """
        transactions = []

        try:
            with pdfplumber.open(self.file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Try extracting tables first (most common format)
                    tables = page.extract_tables()

                    if tables:
                        for table in tables:
                            page_transactions = self._parse_table(table, page_num)
                            transactions.extend(page_transactions)
                    else:
                        # Fallback to text extraction
                        text = page.extract_text()
                        if text:
                            page_transactions = self._parse_text(text, page_num)
                            transactions.extend(page_transactions)

        except Exception as e:
            raise ValueError(f"Failed to parse PDF file: {str(e)}")

        # Clean and validate
        cleaned_transactions = []
        for transaction in transactions:
            if self.validate_transaction(transaction):
                cleaned = self.clean_transaction(transaction)
                cleaned_transactions.append(cleaned)

        return cleaned_transactions

    def _parse_table(self, table: List[List[str]], page_num: int) -> List[Dict[str, Any]]:
        """
        Parse table extracted from PDF

        Args:
            table: List of rows (each row is list of cells)
            page_num: Page number

        Returns:
            List of transactions
        """
        if not table or len(table) < 2:
            return []

        # First row is usually header
        header = [cell.lower().strip() if cell else "" for cell in table[0]]

        # Find column indices
        date_col = self._find_column_index(header, ["дата", "date"])
        amount_col = self._find_column_index(header, ["сумма", "amount", "sum"])
        type_col = self._find_column_index(header, ["тип", "type", "операция", "вид"])
        counterparty_col = self._find_column_index(header, ["контрагент", "counterparty", "получатель", "плательщик"])
        desc_col = self._find_column_index(header, ["описание", "description", "назначение", "purpose"])

        if date_col is None or amount_col is None:
            # Try to parse as free-form text
            return []

        transactions = []
        for row in table[1:]:  # Skip header
            try:
                if not row or len(row) <= max(date_col, amount_col):
                    continue

                transaction = {}

                # Date
                date_str = row[date_col]
                if not date_str:
                    continue
                transaction["transaction_date"] = self._parse_date(date_str.strip())

                # Amount
                amount_str = row[amount_col]
                if not amount_str:
                    continue
                amount = self._parse_amount(amount_str.strip())
                transaction["amount"] = amount

                # Transaction type
                if type_col is not None and len(row) > type_col and row[type_col]:
                    type_str = row[type_col].lower().strip()
                    transaction["transaction_type"] = self._determine_type(type_str, amount)
                else:
                    transaction["transaction_type"] = "incoming" if amount > 0 else "outgoing"

                # Counterparty
                if counterparty_col is not None and len(row) > counterparty_col and row[counterparty_col]:
                    transaction["counterparty_name"] = row[counterparty_col].strip()

                # Description
                if desc_col is not None and len(row) > desc_col and row[desc_col]:
                    transaction["description"] = row[desc_col].strip()
                    transaction["payment_purpose"] = transaction["description"]

                transaction["currency"] = "KZT"  # Default

                transactions.append(transaction)

            except Exception as e:
                logger.debug(f"Error parsing table row on page {page_num}: {e}")
                continue

        return transactions

    def _parse_text(self, text: str, page_num: int) -> List[Dict[str, Any]]:
        """
        Parse free-form text from PDF pages.

        Supports multiple formats:
        - Single-line: "01.01.2024  Оплата за услуги  -50 000,00"
        - Multi-line blocks where date starts a new transaction
        - Kaspi/Halyk-style text extracts

        Args:
            text: Extracted text from a PDF page
            page_num: Page number (0-indexed)

        Returns:
            List of transaction dicts
        """
        transactions = []
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        # Regex patterns
        date_re = re.compile(r'(\d{2}[./]\d{2}[./]\d{2,4})')
        # Amount: optional sign, digits with spaces/dots as thousands sep, comma or dot for decimals
        amount_re = re.compile(
            r'([+-]?\s*[\d\s.]+[.,]\d{2})\b'
        )
        # Counterparty hints (common KZ patterns)
        counterparty_re = re.compile(
            r'(?:от|получатель|плательщик|контрагент|counterparty)[:\s]+(.+)',
            re.IGNORECASE,
        )
        # Currency detection
        currency_re = re.compile(r'\b(KZT|USD|EUR|RUB|USDT|GBP)\b', re.IGNORECASE)

        # Group lines into transaction blocks: each block starts with a line containing a date
        blocks: List[List[str]] = []
        current_block: List[str] = []

        for line in lines:
            if date_re.search(line) and current_block:
                blocks.append(current_block)
                current_block = [line]
            else:
                current_block.append(line)
        if current_block:
            blocks.append(current_block)

        for block in blocks:
            full_text = ' '.join(block)

            # Must have a date
            date_match = date_re.search(full_text)
            if not date_match:
                continue

            # Must have an amount
            # Find ALL amounts in the block (credit, debit, balance)
            amounts = amount_re.findall(full_text)
            if not amounts:
                continue

            try:
                tx_date = self._parse_date(date_match.group(1))
            except ValueError:
                continue

            # Use the first amount as the transaction amount
            try:
                amount = self._parse_amount(amounts[0])
            except (ValueError, IndexError):
                continue

            # Skip zero amounts
            if amount == 0:
                continue

            # Determine transaction type
            tx_type = "incoming" if amount > 0 else "outgoing"
            # Check for type keywords in block text
            lower_text = full_text.lower()
            if any(w in lower_text for w in ["приход", "поступление", "зачисление", "income", "credit"]):
                tx_type = "incoming"
            elif any(w in lower_text for w in ["расход", "списание", "оплата", "перевод", "debit", "payment"]):
                tx_type = "outgoing"
            elif any(w in lower_text for w in ["перевод", "transfer"]):
                tx_type = "transfer"

            # Extract counterparty
            counterparty = None
            cp_match = counterparty_re.search(full_text)
            if cp_match:
                counterparty = cp_match.group(1).strip()

            # Currency
            currency = "KZT"
            cur_match = currency_re.search(full_text)
            if cur_match:
                currency = cur_match.group(1).upper()

            # Description: use block text minus the date/amount portions
            description = full_text
            # Remove matched date from description
            description = description.replace(date_match.group(0), '', 1).strip()
            # Clean up excessive whitespace
            description = re.sub(r'\s{2,}', ' ', description).strip()
            if len(description) > 500:
                description = description[:500]

            transactions.append({
                "transaction_date": tx_date,
                "amount": abs(amount),
                "transaction_type": tx_type,
                "counterparty_name": counterparty,
                "description": description,
                "payment_purpose": description,
                "currency": currency,
                "source_page": page_num,
            })

        return transactions

    def _find_column_index(self, header: List[str], possible_names: List[str]) -> int:
        """Find column index by name"""
        for idx, col_name in enumerate(header):
            for name in possible_names:
                if name in col_name:
                    return idx
        return None

    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float"""
        # Remove spaces
        amount_str = amount_str.replace(" ", "").replace("\xa0", "")
        # Replace comma with dot
        amount_str = amount_str.replace(",", ".")
        # Remove currency symbols
        amount_str = re.sub(r'[^\d.-]', '', amount_str)
        return float(amount_str)

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string"""
        # Remove extra whitespace
        date_str = date_str.strip()

        # Common formats
        formats = [
            "%d.%m.%Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%Y.%m.%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        raise ValueError(f"Unable to parse date: {date_str}")

    def _determine_type(self, type_str: str, amount: float) -> str:
        """Determine transaction type from string"""
        if any(word in type_str for word in ["приход", "поступление", "incoming", "зачисление"]):
            return "incoming"
        elif any(word in type_str for word in ["расход", "списание", "outgoing", "payment"]):
            return "outgoing"
        elif any(word in type_str for word in ["перевод", "transfer"]):
            return "transfer"
        else:
            return "incoming" if amount > 0 else "outgoing"
