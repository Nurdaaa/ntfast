"""
Kaspi Bank PDF Statement Parser v3.0
Ultra-precise parsing using table extraction
Handles all edge cases: multi-currency, split names, complex formatting
"""
import re
import pdfplumber
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class Transaction:
    """Single transaction record"""
    date: datetime
    amount: float  # In KZT, negative for expenses
    type: str  # Покупка, Перевод, Пополнение, Разное, Снятие
    details: str
    currency: str = "KZT"
    original_amount: Optional[float] = None
    original_currency: Optional[str] = None
    raw_text: str = ""


@dataclass
class AccountInfo:
    """Account metadata"""
    owner: str = ""
    card_number: str = ""
    account_number: str = ""
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    balance_start: float = 0.0
    balance_end: float = 0.0


@dataclass
class ExpectedSummary:
    """Expected totals from summary table"""
    total_deposits: float = 0.0  # Пополнения (positive)
    total_transfers: float = 0.0  # Переводы (negative, stored as positive)
    total_purchases: float = 0.0  # Покупки (negative, stored as positive)
    total_withdrawals: float = 0.0  # Снятия
    total_misc: float = 0.0  # Разное (negative, stored as positive)


class KaspiParser:
    """
    Advanced parser for Kaspi Bank PDF statements
    Uses table extraction for maximum accuracy
    """

    # Currency pattern: (- 20,00 USD) or (+ 100.50 CNY)
    CURRENCY_PATTERN = re.compile(
        r'\(([+-])\s*([0-9\s]+(?:[.,]\d{2})?)\s*([A-Z]{3})\)',
        re.UNICODE
    )

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.transactions: List[Transaction] = []
        self.account = AccountInfo()
        self.expected = ExpectedSummary()

    def parse(self) -> Tuple[List[Transaction], AccountInfo, Dict[str, Any]]:
        """
        Parse PDF and return transactions with metadata
        Uses table extraction for accuracy
        """
        logger.info(f"Parsing PDF: {self.pdf_path}")

        with pdfplumber.open(self.pdf_path) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"PDF has {total_pages} pages")

            # Parse first page for account info and summary
            self._parse_first_page_tables(pdf.pages[0])

            # Parse all pages for transactions
            for page_num, page in enumerate(pdf.pages):
                self._parse_transactions_from_page(page, page_num)

        # Remove duplicates (some pages may have overlapping data)
        self._deduplicate_transactions()

        # Validate against expected totals
        validation = self._validate_totals()

        logger.info(f"Successfully parsed {len(self.transactions)} transactions")
        return self.transactions, self.account, validation

    def _parse_first_page_tables(self, page) -> None:
        """
        Extract account info and summary from first page tables
        Table structure:
        - Table 0: Owner info (name, card, account)
        - Table 1: Summary (balances, totals)
        - Table 2: Limits (can ignore)
        - Table 3+: Transactions
        """
        tables = page.extract_tables()
        text = page.extract_text() or ""

        # Parse period from text
        period_match = re.search(
            r'за период с (\d{2}\.\d{2}\.\d{2}) по (\d{2}\.\d{2}\.\d{2})',
            text, re.IGNORECASE
        )
        if period_match:
            self.account.period_start = self._parse_date(period_match.group(1))
            self.account.period_end = self._parse_date(period_match.group(2))

        # Process tables
        for table_idx, table in enumerate(tables):
            if not table:
                continue

            # Table 0: Owner info
            if table_idx == 0:
                self._parse_owner_table(table)

            # Table 1: Summary with balances
            elif table_idx == 1:
                self._parse_summary_table(table)

    def _parse_owner_table(self, table: List[List]) -> None:
        """
        Parse owner information table
        Format:
        ['Алиев', None, None, 'Номер карты:', '*0000']
        ['Алибек Нұрланұлы', None, None, 'Номер счета:', 'KZ00722C000000000000']
        """
        name_parts = []

        for row in table:
            if not row:
                continue

            # First column often contains name parts
            first_cell = str(row[0] or "").strip()
            if first_cell and self._is_name_part(first_cell):
                name_parts.append(first_cell)

            # Look for card number
            for i, cell in enumerate(row):
                cell_str = str(cell or "").strip()
                if 'Номер карты' in cell_str or cell_str == 'Номер карты:':
                    # Next cell should have card number
                    if i + 1 < len(row) and row[i + 1]:
                        card = str(row[i + 1]).strip()
                        if card.startswith('*') or card.isdigit():
                            self.account.card_number = card if card.startswith('*') else '*' + card

                # Look for account number
                if 'Номер счета' in cell_str or cell_str == 'Номер счета:':
                    if i + 1 < len(row) and row[i + 1]:
                        acc = str(row[i + 1]).strip()
                        if acc.startswith('KZ'):
                            self.account.account_number = acc

        # Combine name parts in correct order (Surname First_name Middle_name)
        if name_parts:
            # Kazakh names: typically Surname First_name or Surname First_name Middle_name
            # In the table: first row has last name(s), second row has first name + patronymic
            # Example: ['Алиев'] then ['Алибек Нұрланұлы']
            # Result should be: "Алиев Алибек Нұрланұлы"
            self.account.owner = ' '.join(name_parts)

    def _is_name_part(self, text: str) -> bool:
        """Check if text looks like a name part (Cyrillic/Kazakh letters only)"""
        # Must be mostly Cyrillic/Kazakh letters
        clean = text.replace(' ', '')
        if not clean:
            return False

        # Check for name-like pattern
        name_pattern = re.compile(r'^[А-ЯЁа-яёӘәҒғҚқҢңӨөҰұҮүІіҺһəƏ\s]+$')
        if not name_pattern.match(text):
            return False

        # Exclude common non-name words
        exclude_words = ['доступно', 'номер', 'карты', 'счета', 'валюта', 'тенге', 'краткое']
        if any(word in text.lower() for word in exclude_words):
            return False

        return len(clean) >= 3

    def _parse_summary_table(self, table: List[List]) -> None:
        """
        Parse summary table with balances and totals
        Format:
        ['Краткое содержание операций по карте:', None]
        ['Доступно на 08.02.25', '+ 17 975,78 ₸']
        ['Пополнения', '+ 3 331 652,73 ₸']
        ['Переводы', '- 1 545 076,60 ₸']
        ['Покупки', '- 1 773 761,64 ₸']
        ['Снятия', '+ 0,00 ₸']
        ['Разное', '- 4 190,00 ₸']
        ['Доступно на 08.02.26', '+ 26 600,27 ₸']
        """
        start_balance_found = False

        for row in table:
            if not row or len(row) < 2:
                continue

            label = str(row[0] or "").strip().lower()
            value = str(row[1] or "").strip()

            # Parse amount from value
            amount = self._parse_signed_amount(value)

            # Balance at start of period
            if 'доступно' in label and not start_balance_found:
                self.account.balance_start = amount
                start_balance_found = True
                continue

            # Balance at end of period (second occurrence)
            if 'доступно' in label and start_balance_found:
                self.account.balance_end = amount
                continue

            # Category totals
            if 'пополнен' in label:
                self.expected.total_deposits = abs(amount)
            elif 'перевод' in label:
                self.expected.total_transfers = abs(amount)
            elif 'покупк' in label:
                self.expected.total_purchases = abs(amount)
            elif 'снят' in label:
                self.expected.total_withdrawals = abs(amount)
            elif 'разно' in label:
                self.expected.total_misc = abs(amount)

    def _parse_transactions_from_page(self, page, page_num: int) -> None:
        """
        Extract transactions from page tables
        Transaction table format:
        ['Дата', 'Сумма', 'Операция', 'Детали']
        ['06.02.26', '- 1 400,00 ₸', 'Покупка', 'YANDEX.DELIVERY']
        ['05.02.26', '- 9 999,00 ₸\n(- 20,00 USD)', 'Покупка', 'CLAUDE.AI SUBSCRIPTION']
        """
        tables = page.extract_tables()

        for table in tables:
            if not table:
                continue

            # Check if this is a transaction table
            if not self._is_transaction_table(table):
                continue

            # Determine if table has header row
            has_header = self._has_header_row(table)

            # Process rows (skip header if present)
            start_idx = 1 if has_header else 0
            for row in table[start_idx:]:
                tx = self._parse_transaction_row(row)
                if tx:
                    self.transactions.append(tx)

    def _is_transaction_table(self, table: List[List]) -> bool:
        """
        Check if table contains transactions
        Can have headers OR start directly with transaction data
        """
        if not table or len(table) < 1:
            return False

        # Check first row
        first_row = table[0]
        if not first_row or len(first_row) < 4:
            return False

        # Convert to lowercase strings
        first_row_str = ' '.join(str(cell or '').lower() for cell in first_row)

        # Option 1: Has proper headers
        if 'дата' in first_row_str and ('операция' in first_row_str or 'сумма' in first_row_str):
            return True

        # Option 2: First row is already a transaction (no headers)
        # Check if first cell looks like a date
        first_cell = str(first_row[0] or "").strip()
        if re.match(r'\d{2}\.\d{2}\.\d{2}', first_cell):
            # Check if third cell is a valid transaction type
            tx_type = str(first_row[2] or "").strip()
            if tx_type in ['Покупка', 'Перевод', 'Пополнение', 'Разное', 'Снятие']:
                return True

        return False

    def _has_header_row(self, table: List[List]) -> bool:
        """Check if table has a header row"""
        if not table:
            return False
        first_row = table[0]
        if not first_row:
            return False
        first_row_str = ' '.join(str(cell or '').lower() for cell in first_row)
        return 'дата' in first_row_str

    def _parse_transaction_row(self, row: List) -> Optional[Transaction]:
        """
        Parse a single transaction row
        Format: ['06.02.26', '- 1 400,00 ₸', 'Покупка', 'YANDEX.DELIVERY']
        With currency: ['05.02.26', '- 9 999,00 ₸\n(- 20,00 USD)', 'Покупка', 'CLAUDE.AI SUBSCRIPTION']
        """
        if not row or len(row) < 4:
            return None

        try:
            # Extract fields
            date_str = str(row[0] or "").strip()
            amount_str = str(row[1] or "").strip()
            tx_type = str(row[2] or "").strip()
            details = str(row[3] or "").strip()

            # Validate date format
            if not re.match(r'\d{2}\.\d{2}\.\d{2}', date_str):
                return None

            # Validate transaction type
            valid_types = ['Покупка', 'Перевод', 'Пополнение', 'Разное', 'Снятие']
            if tx_type not in valid_types:
                return None

            # Parse date
            date = self._parse_date(date_str)

            # Parse amount (may include currency)
            amount, orig_amount, orig_currency = self._parse_amount_with_currency(amount_str)

            return Transaction(
                date=date,
                amount=amount,
                type=tx_type,
                details=details,
                currency="KZT",
                original_amount=orig_amount,
                original_currency=orig_currency,
                raw_text=f"{date_str} {amount_str} {tx_type} {details}"
            )

        except Exception as e:
            logger.debug(f"Failed to parse row {row}: {e}")
            return None

    def _parse_amount_with_currency(self, amount_str: str) -> Tuple[float, Optional[float], Optional[str]]:
        """
        Parse amount string that may contain foreign currency
        Examples:
        - '- 1 400,00 ₸' -> (-1400.0, None, None)
        - '- 9 999,00 ₸\n(- 20,00 USD)' -> (-9999.0, -20.0, 'USD')
        - '+ 3 100,00 ₸' -> (3100.0, None, None)
        """
        original_amount = None
        original_currency = None

        # Check for foreign currency
        currency_match = self.CURRENCY_PATTERN.search(amount_str)
        if currency_match:
            sign = currency_match.group(1)
            curr_amount_str = currency_match.group(2)
            original_currency = currency_match.group(3)
            original_amount = self._parse_numeric(curr_amount_str)
            if sign == '-':
                original_amount = -original_amount

        # Parse main KZT amount
        # Remove currency info if present
        kzt_str = amount_str.split('\n')[0] if '\n' in amount_str else amount_str

        # Determine sign
        is_negative = '-' in kzt_str
        is_positive = '+' in kzt_str

        # Parse numeric value
        amount = self._parse_numeric(kzt_str)

        # Apply sign
        if is_negative:
            amount = -abs(amount)
        elif is_positive:
            amount = abs(amount)

        return amount, original_amount, original_currency

    def _parse_signed_amount(self, amount_str: str) -> float:
        """Parse amount with sign (+ or -)"""
        is_negative = '-' in amount_str
        amount = self._parse_numeric(amount_str)
        return -amount if is_negative else amount

    def _parse_numeric(self, value_str: str) -> float:
        """Extract numeric value from string"""
        if not value_str:
            return 0.0

        # Remove everything except digits, comma, and dot
        # Replace non-breaking space and regular space
        cleaned = re.sub(r'[^\d,.]', '', value_str.replace('\xa0', '').replace(' ', ''))

        # Handle comma as decimal separator
        if ',' in cleaned and '.' not in cleaned:
            cleaned = cleaned.replace(',', '.')

        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string DD.MM.YY or DD.MM.YYYY"""
        date_str = date_str.strip()
        try:
            return datetime.strptime(date_str, '%d.%m.%y')
        except ValueError:
            try:
                return datetime.strptime(date_str, '%d.%m.%Y')
            except ValueError:
                logger.warning(f"Could not parse date: {date_str}")
                return datetime.now()

    def _deduplicate_transactions(self) -> None:
        """
        Remove duplicate transactions that may appear due to PDF extraction issues.
        Keep ALL transactions as they appear - PDF table extraction should be reliable
        and each page should have unique transactions.

        Note: Legitimate repeated transactions (same amount, same merchant, same day)
        are valid and should NOT be removed.
        """
        # For now, keep all transactions - no deduplication
        # The PDF structure should ensure unique transactions per page
        # If there are issues, we can add smarter logic later
        pass

    def _validate_totals(self) -> Dict[str, Any]:
        """Validate parsed totals against expected summary"""
        # Calculate actual totals from transactions
        actual_deposits = sum(t.amount for t in self.transactions if t.type == 'Пополнение' and t.amount > 0)
        actual_transfers_out = sum(abs(t.amount) for t in self.transactions if t.type == 'Перевод' and t.amount < 0)
        actual_purchases = sum(abs(t.amount) for t in self.transactions if t.type == 'Покупка' and t.amount < 0)
        actual_withdrawals = sum(abs(t.amount) for t in self.transactions if t.type == 'Снятие' and t.amount < 0)
        actual_misc = sum(abs(t.amount) for t in self.transactions if t.type == 'Разное' and t.amount < 0)

        # Transfers that are income (Пополнение from transfers)
        actual_transfers_in = sum(t.amount for t in self.transactions if t.type == 'Перевод' and t.amount > 0)

        validation = {
            "total_transactions": len(self.transactions),
            "expected": {
                "deposits": self.expected.total_deposits,
                "transfers": self.expected.total_transfers,
                "purchases": self.expected.total_purchases,
                "withdrawals": self.expected.total_withdrawals,
                "misc": self.expected.total_misc,
            },
            "actual": {
                "deposits": actual_deposits,
                "transfers": actual_transfers_out,
                "purchases": actual_purchases,
                "withdrawals": actual_withdrawals,
                "misc": actual_misc,
            },
            "differences": {},
            "is_valid": True,
            "errors": [],
            "account": {
                "owner": self.account.owner,
                "card": self.account.card_number,
                "account_number": self.account.account_number,
                "balance_start": self.account.balance_start,
                "balance_end": self.account.balance_end,
                "period_start": self.account.period_start.isoformat() if self.account.period_start else None,
                "period_end": self.account.period_end.isoformat() if self.account.period_end else None,
            }
        }

        # Calculate differences
        tolerance = 0.02  # 2% tolerance for rounding errors

        for key in ['deposits', 'transfers', 'purchases', 'withdrawals', 'misc']:
            expected = validation['expected'][key]
            actual = validation['actual'][key]
            diff = abs(actual - expected)
            validation['differences'][key] = diff

            # Check if difference is significant
            if expected > 0 and diff / expected > tolerance:
                validation['is_valid'] = False
                validation['errors'].append(
                    f"{key}: expected {expected:,.2f}, got {actual:,.2f} (diff: {diff:,.2f}, {diff/expected*100:.1f}%)"
                )

        # Verify balance calculation
        total_income = actual_deposits + actual_transfers_in
        total_expense = actual_transfers_out + actual_purchases + actual_withdrawals + actual_misc
        calculated_end = self.account.balance_start + total_income - total_expense

        balance_diff = abs(calculated_end - self.account.balance_end)
        if balance_diff > 1:  # Allow 1 tenge rounding error
            validation['errors'].append(
                f"Balance mismatch: start {self.account.balance_start:,.2f} + income {total_income:,.2f} - expense {total_expense:,.2f} = {calculated_end:,.2f}, expected {self.account.balance_end:,.2f}"
            )

        return validation
