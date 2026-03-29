"""
Парсер выписок Kaspi Bank
Поддерживает: Gold карты, депозиты
"""
import re
import pdfplumber
from datetime import datetime
from typing import List, Optional, Tuple
import logging

from ..base_parser import BaseParser, Transaction, TransactionType, CounterpartyType, AccountInfo, ExpectedTotals

logger = logging.getLogger(__name__)


class KaspiParser(BaseParser):
    """
    Парсер PDF выписок Kaspi Bank
    Использует table extraction для максимальной точности
    """

    # Маппинг типов транзакций Kaspi -> универсальные
    TYPE_MAPPING = {
        'Покупка': TransactionType.EXPENSE,
        'Перевод': TransactionType.TRANSFER_OUT,  # По умолчанию исходящий
        'Пополнение': TransactionType.INCOME,
        'Снятие': TransactionType.WITHDRAWAL,
        'Разное': TransactionType.OTHER,
    }

    # Паттерн для валюты: (- 20,00 USD) или (+ 100.50 CNY)
    CURRENCY_PATTERN = re.compile(
        r'\(([+-])\s*([0-9\s]+(?:[.,]\d{2})?)\s*([A-Z]{3})\)',
        re.UNICODE
    )

    def __init__(self, pdf_path: str):
        super().__init__(pdf_path)
        self.account.bank_name = "Kaspi Bank"
        self.account.currency = "KZT"

    def parse(self) -> bool:
        """Основной метод парсинга"""
        try:
            logger.info(f"Парсинг Kaspi PDF: {self.pdf_path}")

            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"PDF содержит {total_pages} страниц")

                # Первая страница - информация о счете и итоги
                self._parse_first_page_tables(pdf.pages[0])

                # Все страницы - транзакции
                for page_num, page in enumerate(pdf.pages):
                    self._parse_transactions_from_page(page, page_num)

            logger.info(f"Успешно спарсено {len(self.transactions)} транзакций")
            return True

        except Exception as e:
            logger.error(f"Ошибка парсинга Kaspi PDF: {e}", exc_info=True)
            self.errors.append(f"Ошибка парсинга: {str(e)}")
            return False

    def _parse_account_info(self) -> None:
        """Реализовано в _parse_first_page_tables"""
        pass

    def _parse_transactions(self) -> None:
        """Реализовано в parse()"""
        pass

    def _parse_first_page_tables(self, page) -> None:
        """
        Извлечь информацию о счете и итоги с первой страницы
        Структура таблиц:
        - Таблица 0: Информация о владельце (имя, карта, счет)
        - Таблица 1: Итоги (балансы, суммы)
        - Таблица 2: Лимиты (игнорируем)
        - Таблица 3+: Транзакции
        """
        tables = page.extract_tables()
        text = page.extract_text() or ""

        # Извлечь период из текста
        period_match = re.search(
            r'за период с (\d{2}\.\d{2}\.\d{2}) по (\d{2}\.\d{2}\.\d{2})',
            text, re.IGNORECASE
        )
        if period_match:
            self.account.period_start = self._parse_date(period_match.group(1))
            self.account.period_end = self._parse_date(period_match.group(2))

        # Обработка таблиц
        for table_idx, table in enumerate(tables):
            if not table:
                continue

            if table_idx == 0:
                self._parse_owner_table(table)
            elif table_idx == 1:
                self._parse_summary_table(table)
            elif table_idx == 2:
                self._parse_limits_table(table)

    def _parse_owner_table(self, table: List[List]) -> None:
        """
        Парсинг таблицы с информацией о владельце
        Формат:
        ['Алиев', None, None, 'Номер карты:', '*0000']
        ['Алибек Нұрланұлы', None, None, 'Номер счета:', 'KZ00722C000000000000']
        """
        name_parts = []

        for row in table:
            if not row:
                continue

            first_cell = str(row[0] or "").strip()
            if first_cell and self._is_name_part(first_cell):
                name_parts.append(first_cell)

            for i, cell in enumerate(row):
                cell_str = str(cell or "").strip()

                if 'Номер карты' in cell_str or cell_str == 'Номер карты:':
                    if i + 1 < len(row) and row[i + 1]:
                        card = str(row[i + 1]).strip()
                        if card.startswith('*') or card.isdigit():
                            self.account.card_number = card if card.startswith('*') else '*' + card

                if 'Номер счета' in cell_str or cell_str == 'Номер счета:':
                    if i + 1 < len(row) and row[i + 1]:
                        acc = str(row[i + 1]).strip()
                        if acc.startswith('KZ'):
                            self.account.account_number = acc

        if name_parts:
            self.account.owner = ' '.join(name_parts)

    def _is_name_part(self, text: str) -> bool:
        """Проверить, является ли текст частью имени"""
        clean = text.replace(' ', '')
        if not clean:
            return False

        name_pattern = re.compile(r'^[А-ЯЁа-яёӘәҒғҚқҢңӨөҰұҮүІіҺһəƏ\s]+$')
        if not name_pattern.match(text):
            return False

        exclude_words = ['доступно', 'номер', 'карты', 'счета', 'валюта', 'тенге', 'краткое']
        if any(word in text.lower() for word in exclude_words):
            return False

        return len(clean) >= 3

    def _parse_summary_table(self, table: List[List]) -> None:
        """
        Парсинг таблицы с итогами
        Формат:
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
            amount = self._parse_signed_amount(value)

            if 'доступно' in label and not start_balance_found:
                self.account.balance_start = amount
                start_balance_found = True
                continue

            if 'доступно' in label and start_balance_found:
                self.account.balance_end = amount
                continue

            if 'пополнен' in label:
                self.expected_totals.deposits = abs(amount)
            elif 'перевод' in label:
                self.expected_totals.transfers = abs(amount)
            elif 'покупк' in label:
                self.expected_totals.purchases = abs(amount)
            elif 'снят' in label:
                self.expected_totals.withdrawals = abs(amount)
            elif 'разно' in label:
                self.expected_totals.other = abs(amount)

    def _parse_limits_table(self, table: List[List]) -> None:
        """
        Парсинг Таблицы 2: Лимиты на снятие наличности
        Формат:
        ['Лимит на снятие наличности без комиссии:', None]
        ['Остаток зарплатных денег', '0,00 ₸']
        ['Другие пополнения', '300 000,00 ₸']
        ['Итого', '300 000,00 ₸']
        """
        for row in table:
            if not row or len(row) < 2:
                continue

            label = str(row[0] or "").strip().lower()
            value_str = str(row[1] or "").strip()

            if not value_str:
                continue

            amount = self._parse_numeric(value_str)

            if 'зарплатн' in label:
                self.account.salary_money_limit = amount
            elif 'друг' in label and 'пополнен' in label:
                self.account.other_deposits_limit = amount
            elif 'итого' in label:
                self.account.total_cash_limit = amount

    def _parse_transactions_from_page(self, page, page_num: int) -> None:
        """Извлечь транзакции со страницы с поддержкой continuation rows"""
        tables = page.extract_tables()

        for table in tables:
            if not table:
                continue

            if not self._is_transaction_table(table):
                continue

            has_header = self._has_header_row(table)
            start_idx = 1 if has_header else 0

            last_tx = None
            row_idx = 0
            for row in table[start_idx:]:
                # Проверка на continuation row (не начинается с даты)
                first_cell = str(row[0] or "").strip() if row and row[0] else ""

                if not re.match(r'\d{2}\.\d{2}\.\d{2}', first_cell) and last_tx:
                    # Это продолжение предыдущей транзакции
                    continuation_text = " ".join(str(c or "").strip() for c in row if c).strip()
                    if 'заблокирована' in continuation_text.lower():
                        last_tx.is_blocked = True
                        last_tx.raw_data["blocked_note"] = continuation_text
                    continue

                tx = self._parse_transaction_row(row, page_num, row_idx)
                if tx:
                    self.transactions.append(tx)
                    last_tx = tx
                row_idx += 1

    def _is_transaction_table(self, table: List[List]) -> bool:
        """Проверить, содержит ли таблица транзакции"""
        if not table or len(table) < 1:
            return False

        first_row = table[0]
        if not first_row or len(first_row) < 4:
            return False

        first_row_str = ' '.join(str(cell or '').lower() for cell in first_row)

        if 'дата' in first_row_str and ('операция' in first_row_str or 'сумма' in first_row_str):
            return True

        first_cell = str(first_row[0] or "").strip()
        if re.match(r'\d{2}\.\d{2}\.\d{2}', first_cell):
            tx_type = str(first_row[2] or "").strip()
            if tx_type in ['Покупка', 'Перевод', 'Пополнение', 'Разное', 'Снятие']:
                return True

        return False

    def _has_header_row(self, table: List[List]) -> bool:
        """Проверить наличие заголовка"""
        if not table:
            return False
        first_row = table[0]
        if not first_row:
            return False
        first_row_str = ' '.join(str(cell or '').lower() for cell in first_row)
        return 'дата' in first_row_str

    # Префиксы юридических лиц для извлечения merchant_type
    ENTITY_PREFIXES = ["ИП ", "ТОО ", "АО ", "ОО ", "TOO ", "ТОО\"", "ТОО "]

    # Ключевые слова для определения типа контрагента
    DEPOSIT_KEYWORDS = ["на kaspi депозит", "с kaspi депозита", "kaspi депозит"]
    PENSION_KEYWORDS = ["пенсия", "пособие", "пенсия/пособие"]
    SALARY_KEYWORDS = ["зарплата", "зарп.", "salary"]
    ATM_KEYWORDS = ["банкомат", "atm"]
    BANK_TRANSFER_KEYWORDS = ["карты другого банка", "другого банка"]

    def _parse_transaction_row(self, row: List, page_num: int = 0, row_idx: int = 0) -> Optional[Transaction]:
        """
        Парсинг строки транзакции с извлечением ВСЕХ данных
        Формат: ['06.02.26', '- 1 400,00 ₸', 'Покупка', 'YANDEX.DELIVERY']
        """
        if not row or len(row) < 4:
            return None

        try:
            date_str = str(row[0] or "").strip()
            amount_str = str(row[1] or "").strip()
            tx_type_str = str(row[2] or "").strip()
            details = str(row[3] or "").strip()

            if not re.match(r'\d{2}\.\d{2}\.\d{2}', date_str):
                return None

            valid_types = ['Покупка', 'Перевод', 'Пополнение', 'Разное', 'Снятие']
            if tx_type_str not in valid_types:
                return None

            date = self._parse_date(date_str)
            amount, orig_amount, orig_currency = self._parse_amount_with_currency(amount_str)

            # Определить тип транзакции
            tx_type = self.TYPE_MAPPING.get(tx_type_str, TransactionType.OTHER)
            if tx_type_str == 'Перевод':
                tx_type = TransactionType.TRANSFER_IN if amount > 0 else TransactionType.TRANSFER_OUT

            # Вычислить обменный курс
            exchange_rate = None
            if orig_amount and orig_amount != 0:
                exchange_rate = round(abs(amount / orig_amount), 4)

            # Извлечь тип мерчанта (ИП, ТОО, АО)
            merchant_type = None
            merchant_name = details
            for prefix in self.ENTITY_PREFIXES:
                if details.upper().startswith(prefix.upper()):
                    merchant_type = prefix.strip().strip('"')
                    merchant_name = details[len(prefix):].strip().strip('"')
                    break

            # Определить тип контрагента и флаги
            details_lower = details.lower()
            counterparty_type = CounterpartyType.UNKNOWN
            is_deposit_op = False
            is_pension = False
            is_salary = False
            is_atm = False
            is_bank_transfer = False
            is_cash = False
            counterparty = None

            # Депозитные операции
            if any(kw in details_lower for kw in self.DEPOSIT_KEYWORDS):
                counterparty_type = CounterpartyType.DEPOSIT
                is_deposit_op = True
            # Пенсия/пособие
            elif any(kw in details_lower for kw in self.PENSION_KEYWORDS):
                counterparty_type = CounterpartyType.GOVERNMENT
                is_pension = True
            # Зарплата
            elif any(kw in details_lower for kw in self.SALARY_KEYWORDS):
                counterparty_type = CounterpartyType.GOVERNMENT
                is_salary = True
            # Банкомат
            elif any(kw in details_lower for kw in self.ATM_KEYWORDS):
                counterparty_type = CounterpartyType.ATM
                is_atm = True
                is_cash = True
            # Перевод с другого банка
            elif any(kw in details_lower for kw in self.BANK_TRANSFER_KEYWORDS):
                counterparty_type = CounterpartyType.BANK
                is_bank_transfer = True
            # Перевод физлицу (имя формата "Имя Б." или "Имя Фамилия")
            elif tx_type_str in ['Перевод', 'Пополнение'] and self._is_person_name(details):
                counterparty_type = CounterpartyType.PERSON
                counterparty = details
            # Покупка = мерчант
            elif tx_type_str == 'Покупка':
                counterparty_type = CounterpartyType.MERCHANT
                counterparty = details
            # Снятие = наличные
            elif tx_type_str == 'Снятие':
                is_cash = True
                counterparty_type = CounterpartyType.ATM

            # Для переводов без имени — мерчант
            if counterparty_type == CounterpartyType.UNKNOWN and tx_type_str == 'Пополнение':
                counterparty_type = CounterpartyType.MERCHANT

            return Transaction(
                date=date,
                amount=amount,
                type=tx_type,
                description=details,
                currency="KZT",
                original_amount=orig_amount,
                original_currency=orig_currency,
                exchange_rate=exchange_rate,
                counterparty=counterparty or details,
                counterparty_type=counterparty_type,
                merchant_name=merchant_name,
                merchant_type=merchant_type,
                is_deposit_operation=is_deposit_op,
                is_pension_benefit=is_pension,
                is_salary=is_salary,
                is_bank_transfer=is_bank_transfer,
                is_atm=is_atm,
                is_cash_operation=is_cash,
                source_page=page_num,
                source_row=row_idx,
                raw_data={"row": row, "type_original": tx_type_str}
            )

        except Exception as e:
            logger.debug(f"Ошибка парсинга строки {row}: {e}")
            return None

    def _is_person_name(self, text: str) -> bool:
        """
        Проверить, является ли текст именем человека
        Примеры: "Ержан О.", "Маржан П.", "Ақсана А.", "Гулсайра К."
        """
        text = text.strip()
        if not text or len(text) < 3:
            return False

        # Паттерн: Имя + инициал с точкой (Ержан О.)
        if re.match(r'^[А-ЯЁӘҒҚҢӨҰҮІҺа-яёәғқңөұүіһəƏ][а-яёәғқңөұүіһəƏА-ЯЁ]+\s+[А-ЯЁӘҒҚҢӨҰҮІҺа-яёәғқңөұүіһəƏ]\.$', text):
            return True

        # Паттерн: Имя Фамилия (оба слова с заглавной, кириллица)
        if re.match(r'^[А-ЯЁӘҒҚҢӨҰҮІҺəƏ][а-яёәғқңөұүіһəƏ]+\s+[А-ЯЁӘҒҚҢӨҰҮІҺəƏ][а-яёәғқңөұүіһəƏ]+$', text):
            return True

        return False

    def _parse_amount_with_currency(self, amount_str: str) -> Tuple[float, Optional[float], Optional[str]]:
        """
        Парсинг суммы с возможной иностранной валютой
        Примеры:
        - '- 1 400,00 ₸' -> (-1400.0, None, None)
        - '- 9 999,00 ₸\n(- 20,00 USD)' -> (-9999.0, -20.0, 'USD')
        """
        original_amount = None
        original_currency = None

        currency_match = self.CURRENCY_PATTERN.search(amount_str)
        if currency_match:
            sign = currency_match.group(1)
            curr_amount_str = currency_match.group(2)
            original_currency = currency_match.group(3)
            original_amount = self._parse_numeric(curr_amount_str)
            if sign == '-':
                original_amount = -original_amount

        kzt_str = amount_str.split('\n')[0] if '\n' in amount_str else amount_str

        is_negative = '-' in kzt_str
        is_positive = '+' in kzt_str

        amount = self._parse_numeric(kzt_str)

        if is_negative:
            amount = -abs(amount)
        elif is_positive:
            amount = abs(amount)

        return amount, original_amount, original_currency

    def _parse_signed_amount(self, amount_str: str) -> float:
        """Парсинг суммы со знаком"""
        is_negative = '-' in amount_str
        amount = self._parse_numeric(amount_str)
        return -amount if is_negative else amount

    def _parse_numeric(self, value_str: str) -> float:
        """Извлечь числовое значение из строки"""
        if not value_str:
            return 0.0

        cleaned = re.sub(r'[^\d,.]', '', value_str.replace('\xa0', '').replace(' ', ''))

        if ',' in cleaned and '.' not in cleaned:
            cleaned = cleaned.replace(',', '.')

        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _parse_date(self, date_str: str) -> datetime:
        """Парсинг даты DD.MM.YY или DD.MM.YYYY"""
        date_str = date_str.strip()
        try:
            return datetime.strptime(date_str, '%d.%m.%y')
        except ValueError:
            try:
                return datetime.strptime(date_str, '%d.%m.%Y')
            except ValueError:
                logger.warning(f"Не удалось распарсить дату: {date_str}")
                return datetime.now()
