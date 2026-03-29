"""
PDF Parser for Kaspi Bank Statements
Uses pdfplumber for accurate table extraction
"""
import re
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
import pdfplumber

from .models import Transaction, TransactionType, TransactionCategory

logger = logging.getLogger(__name__)


class KaspiStatementParser:
    """Parser for Kaspi Bank PDF statements"""

    DATE_PATTERN = re.compile(r'(\d{2}\.\d{2}\.\d{2})')

    CATEGORY_KEYWORDS = {
        TransactionCategory.GAMING_GAMBLING: [
            "SENET", "1XBET", "MOSTBET", "STEAM", "CODASHOP",
            "GOLD GAME", "TOP GAME", "PLAYSTATION", "XBOX",
            "EPIC GAMES", "RIOT", "CASINO", "POKER", "СТАВКИ",
            "MELBET", "FONBET", "PARIMATCH", "OLIMPBET"
        ],
        TransactionCategory.P2P_TRANSFER: [
            "KASPI ПЕРЕВОД", "ПЕРЕВОД", "P2P"
        ],
        TransactionCategory.SALARY_PENSION: [
            "ЗАРПЛАТА", "SALARY", "ПЕНСИЯ", "PENSION",
            "СТИПЕНДИЯ", "ПОСОБИЕ", "ВЫПЛАТА", "АО ЕНПФ",
            "ГЦВП", "СОЦИАЛЬНАЯ"
        ],
        TransactionCategory.UTILITIES: [
            "КОММУНАЛЬН", "АЛМАТЫЭНЕРГО", "ГАЗ", "СВЯЗЬ",
            "BEELINE", "KCELL", "TELE2", "ACTIV"
        ],
        TransactionCategory.TRANSPORT: [
            "YANDEX.GO", "ЯНДЕКС.ТАКСИ", "UBER", "BOLT",
            "INDRIVER", "АЗС", "БЕНЗИН"
        ],
        TransactionCategory.FOOD: [
            "GLOVO", "WOLT", "YANDEX.EDA", "CHOCOFOOD",
            "MAGNUM", "SMALL", "ARBUZ"
        ],
        TransactionCategory.SUBSCRIPTION: [
            "APPLE.COM", "SPOTIFY", "NETFLIX", "YOUTUBE",
            "YANDEX PLUS", "CLAUDE", "OPENAI", "ПОДПИСКА"
        ],
        TransactionCategory.SHOPPING: [
            "KASPI МАГАЗИН", "WILDBERRIES", "OZON", "ALIEXPRESS",
            "PINDUODUO", "AMAZON"
        ],
        TransactionCategory.CASH_WITHDRAWAL: [
            "СНЯТИЕ", "ATM", "БАНКОМАТ"
        ],
        TransactionCategory.CASH_DEPOSIT: [
            "ВНЕСЕНИЕ", "ПОПОЛНЕНИЕ НАЛИЧНЫМИ"
        ]
    }

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.pdf_hash = self._calculate_hash()
        self.transactions: List[Transaction] = []
        self.metadata: Dict[str, Any] = {}

    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash of PDF"""
        sha256_hash = hashlib.sha256()
        with open(self.pdf_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def parse(self) -> Tuple[List[Transaction], Dict[str, Any]]:
        """Parse PDF and extract transactions"""
        logger.info(f"Parsing PDF: {self.pdf_path}")
        logger.info(f"PDF Hash: {self.pdf_hash}")

        with pdfplumber.open(self.pdf_path) as pdf:
            self._extract_metadata(pdf)
            self._extract_transactions(pdf)

        logger.info(f"Extracted {len(self.transactions)} transactions")
        return self.transactions, self.metadata

    def _extract_metadata(self, pdf: Any):
        """Extract statement metadata from Kaspi Bank PDF"""
        first_page = pdf.pages[0]
        text = first_page.extract_text() or ""
        lines = text.split('\n')

        # Extract customer name (Kaspi format: name is split across lines 3 and 5)
        # Format: ВЫПИСКА / по Kaspi Gold... / Surname / Номер карты / Name Patronymic
        name_parts = []
        # Kazakh/Russian name pattern (includes Cyrillic + Kazakh special + Latin schwa)
        # ə (U+0259) is Latin schwa sometimes used in Kazakh PDFs
        name_pattern = re.compile(r'^[А-ЯЁа-яёӘәҒғҚқҢңӨөҰұҮүІіҺһəƏ\s]+$')

        for i, line in enumerate(lines):
            line = line.strip()
            # Skip empty lines
            if not line:
                continue
            # Skip headers and metadata lines (must be exact matches or clear metadata)
            skip_keywords = ['выписка', 'kaspi', 'номер карты', 'номер счета',
                           'доступно', 'валюта', 'краткое', 'лимит', 'период',
                           'пополнен', 'перевод', 'покупк', 'снятия', 'остаток',
                           'разное', 'дата', 'сумма', 'операция', 'детали',
                           'зарплат', 'итого', 'www.', 'bank', 'бик']
            line_lower = line.lower()
            if any(kw in line_lower for kw in skip_keywords):
                continue
            # Skip lines with numbers (dates, amounts, account numbers)
            if re.search(r'\d{2,}', line):
                continue
            # Skip lines with currency or symbols
            if '₸' in line or '+' in line or '-' in line or '*' in line:
                continue
            # Check if line looks like a Kazakh/Russian name
            if name_pattern.match(line) and len(line) >= 3:
                name_parts.append(line)
                if len(name_parts) >= 2:
                    break

        if name_parts:
            self.metadata['customer_name'] = ' '.join(name_parts)

        # Extract period
        period_match = re.search(
            r'(?:период\s+с\s+)?(\d{2}\.\d{2}\.\d{2,4})\s*(?:по|-|–)\s*(\d{2}\.\d{2}\.\d{2,4})',
            text, re.IGNORECASE
        )
        if period_match:
            self.metadata['period_start'] = self._parse_date(period_match.group(1))
            self.metadata['period_end'] = self._parse_date(period_match.group(2))

        # Extract account number
        account_match = re.search(r'(KZ\d{2}[A-Z0-9]{16})', text)
        if account_match:
            self.metadata['account_number'] = account_match.group(1)

        # Extract card number
        card_match = re.search(r'Номер карты:\s*\*?(\d{4})', text)
        if card_match:
            self.metadata['card_last4'] = card_match.group(1)

        self.metadata['total_pages'] = len(pdf.pages)
        self.metadata['pdf_hash'] = self.pdf_hash

    def _extract_transactions(self, pdf: Any):
        """Extract transactions from all pages - prefer text extraction for Kaspi format"""
        for page_num, page in enumerate(pdf.pages):
            # For Kaspi Bank, text extraction works better than table extraction
            self._extract_from_text(page)

    def _process_table(self, table: List[List[str]]):
        """Process extracted table"""
        if not table or len(table) < 2:
            return

        # Find header
        header_row = 0
        for i, row in enumerate(table):
            row_text = ' '.join(str(cell or '') for cell in row).lower()
            if 'дата' in row_text or 'сумма' in row_text:
                header_row = i
                break

        headers = [str(cell or '').lower().strip() for cell in table[header_row]]
        col_map = self._map_columns(headers)

        for row in table[header_row + 1:]:
            try:
                transaction = self._parse_row(row, col_map)
                if transaction:
                    self.transactions.append(transaction)
            except Exception as e:
                logger.warning(f"Failed to parse row: {e}")

    def _map_columns(self, headers: List[str]) -> Dict[str, int]:
        """Map column headers to indices"""
        col_map = {}
        for i, header in enumerate(headers):
            if 'дата' in header:
                col_map['date'] = i
            elif 'сумма' in header:
                col_map['amount'] = i
            elif any(x in header for x in ['операция', 'описание', 'назначение']):
                col_map['description'] = i
            elif 'остаток' in header or 'баланс' in header:
                col_map['balance'] = i
            elif 'приход' in header:
                col_map['income'] = i
            elif 'расход' in header:
                col_map['expense'] = i
        return col_map

    def _parse_row(self, row: List[str], col_map: Dict[str, int]) -> Optional[Transaction]:
        """Parse table row to Transaction"""
        if not row or all(not cell for cell in row):
            return None

        # Extract date
        date = None
        if 'date' in col_map:
            date = self._parse_date(str(row[col_map['date']] or ''))

        if not date:
            for cell in row:
                date = self._parse_date(str(cell or ''))
                if date:
                    break

        if not date:
            return None

        # Extract amount
        amount = 0.0
        transaction_type = TransactionType.EXPENSE

        if 'income' in col_map and 'expense' in col_map:
            income_str = str(row[col_map['income']] or '').strip()
            expense_str = str(row[col_map['expense']] or '').strip()

            if income_str and income_str not in ['-', '']:
                amount = self._parse_amount(income_str)
                transaction_type = TransactionType.INCOME
            elif expense_str and expense_str not in ['-', '']:
                amount = abs(self._parse_amount(expense_str))
                transaction_type = TransactionType.EXPENSE
        elif 'amount' in col_map:
            amount = self._parse_amount(str(row[col_map['amount']] or ''))
            transaction_type = TransactionType.INCOME if amount > 0 else TransactionType.EXPENSE
            amount = abs(amount)

        if amount == 0:
            return None

        # Extract description
        description = ""
        if 'description' in col_map:
            description = str(row[col_map['description']] or '').strip()
        else:
            for cell in row:
                cell_str = str(cell or '').strip()
                if len(cell_str) > len(description) and not self._is_amount(cell_str):
                    description = cell_str

        # Extract balance
        balance = None
        if 'balance' in col_map:
            balance_str = str(row[col_map['balance']] or '')
            if balance_str:
                balance = self._parse_amount(balance_str)

        # Classify
        category = self._classify_transaction(description)

        if category == TransactionCategory.P2P_TRANSFER:
            transaction_type = TransactionType.P2P_IN if transaction_type == TransactionType.INCOME else TransactionType.P2P_OUT

        counterparty = self._extract_counterparty(description)

        return Transaction(
            date=date,
            amount=amount,
            description=description,
            transaction_type=transaction_type,
            category=category,
            counterparty=counterparty,
            balance_after=balance,
            raw_text=' | '.join(str(c or '') for c in row)
        )

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string"""
        if not date_str:
            return None

        date_str = date_str.strip()
        formats = ['%d.%m.%y', '%d.%m.%Y', '%d/%m/%y', '%d/%m/%Y']

        for fmt in formats:
            try:
                return datetime.strptime(date_str[:10], fmt)
            except ValueError:
                continue

        match = self.DATE_PATTERN.search(date_str)
        if match:
            try:
                return datetime.strptime(match.group(1), '%d.%m.%y')
            except ValueError:
                pass

        return None

    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float"""
        if not amount_str:
            return 0.0

        amount_str = amount_str.replace('₸', '').replace('тг', '').replace('KZT', '')
        amount_str = amount_str.replace(' ', '').replace('\xa0', '')
        amount_str = amount_str.replace(',', '.')
        cleaned = re.sub(r'[^\d.\-+]', '', amount_str)

        try:
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0

    def _is_amount(self, text: str) -> bool:
        """Check if text is an amount"""
        cleaned = re.sub(r'[\s₸тгKZT,.]', '', text)
        return cleaned.replace('-', '').replace('+', '').isdigit()

    def _classify_transaction(self, description: str) -> TransactionCategory:
        """Classify transaction by description"""
        desc_upper = description.upper()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in desc_upper:
                    return category

        return TransactionCategory.UNKNOWN

    def _extract_counterparty(self, description: str) -> Optional[str]:
        """Extract counterparty from description"""
        # Pattern for Kazakh/Russian names: "Surname N." or "Name Surname"
        name_pattern = r'([А-ЯЁA-Z][а-яёa-z]+\s+[А-ЯЁA-Z]\.?)'
        match = re.search(name_pattern, description)
        if match:
            return match.group(1).strip()
        return None

    def _extract_from_text(self, page: Any):
        """Extract transactions from Kaspi Bank statement text format"""
        text = page.extract_text() or ""
        lines = text.split('\n')

        # Kaspi format: "DD.MM.YY +/- AMOUNT ₸ Operation Details"
        # Pattern: date, sign+amount, currency, operation type, details
        transaction_pattern = re.compile(
            r'^(\d{2}\.\d{2}\.\d{2})\s+'  # Date
            r'([+-])\s*([\d\s]+(?:,\d{2})?)\s*₸\s+'  # Sign, Amount, Currency
            r'(\S+)\s*'  # Operation type (Покупка, Пополнение, Перевод, etc.)
            r'(.*)$'  # Details
        )

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip header lines
            if any(x in line.lower() for x in ['дата', 'сумма', 'операция', 'детали',
                                                  'kaspi bank', 'www.kaspi']):
                continue

            # Try to match Kaspi transaction format
            match = transaction_pattern.match(line)
            if match:
                date_str, sign, amount_str, operation, details = match.groups()
                date = self._parse_date(date_str)
                if not date:
                    continue

                amount = self._parse_amount(amount_str)
                if amount == 0:
                    continue

                # Determine transaction type based on sign and operation
                is_income = sign == '+'
                description = f"{operation} {details}".strip()

                # Classify by operation type
                if 'Перевод' in operation:
                    trans_type = TransactionType.P2P_IN if is_income else TransactionType.P2P_OUT
                    category = TransactionCategory.P2P_TRANSFER
                elif 'Пополнение' in operation:
                    trans_type = TransactionType.INCOME
                    category = self._classify_transaction(details)
                    # Check for pension/salary
                    if 'пенси' in details.lower() or 'пособи' in details.lower():
                        category = TransactionCategory.SALARY_PENSION
                elif 'Покупка' in operation:
                    trans_type = TransactionType.EXPENSE
                    category = self._classify_transaction(details)
                elif 'Снятие' in operation:
                    trans_type = TransactionType.EXPENSE
                    category = TransactionCategory.CASH_WITHDRAWAL
                else:
                    trans_type = TransactionType.INCOME if is_income else TransactionType.EXPENSE
                    category = self._classify_transaction(description)

                # Extract counterparty (usually for P2P and some deposits)
                counterparty = None
                if trans_type in [TransactionType.P2P_IN, TransactionType.P2P_OUT]:
                    counterparty = details.strip()
                elif 'Пополнение' in operation and details:
                    # Check if details is a person name
                    if not any(x in details.upper() for x in ['ПЕНСИЯ', 'ПОСОБИЕ', 'ЗАРПЛАТА', 'KASPI']):
                        counterparty = details.strip()

                self.transactions.append(Transaction(
                    date=date,
                    amount=amount,
                    description=description,
                    transaction_type=trans_type,
                    category=category,
                    counterparty=counterparty,
                    raw_text=line
                ))
