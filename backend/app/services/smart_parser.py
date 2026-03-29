"""
Smart Parser with ML Integration
Интеллектуальный парсер с ML для извлечения данных из банковских выписок
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import re
import csv
import io

logger = logging.getLogger(__name__)


class SmartBankStatementParser:
    """
    Умный парсер банковских выписок с ML

    Умеет:
    - Определять тип субъекта (физ/юр лицо) по ИИН/БИН
    - Извлекать номера счетов, карт
    - Определять банк из выписки
    - Работать с разными валютами
    - Извлекать ФИО и названия компаний
    """

    # Паттерны для ИИН/БИН
    IIN_PATTERN = re.compile(r'\b\d{12}\b')  # ИИН - 12 цифр
    BIN_PATTERN = re.compile(r'\b\d{12}\b')  # БИН - 12 цифр (совпадает с ИИН, различие в первой цифре)

    # Паттерны для счетов
    ACCOUNT_PATTERN = re.compile(r'KZ\d{18}|[A-Z]{2}\d{16,34}')  # IBAN
    CARD_PATTERN = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')  # Карта

    # Банки Казахстана
    KAZAKHSTAN_BANKS = [
        'Halyk Bank', 'Kaspi Bank', 'ForteBank', 'Eurasian Bank',
        'Bank CenterCredit', 'Jusan Bank', 'Home Credit Bank',
        'Alfa-Bank', 'Sberbank', 'ATFBank', 'Bereke Bank',
        'Халык Банк', 'Каспи Банк', 'Форте Банк', 'Евразийский Банк'
    ]

    # Валюты
    CURRENCIES = {
        '₸': 'KZT', '₽': 'RUB', '$': 'USD', '€': 'EUR',
        'тг': 'KZT', 'тенге': 'KZT', 'руб': 'RUB', 'доллар': 'USD', 'евро': 'EUR'
    }

    @staticmethod
    def detect_subject_type(identifier: str) -> str:
        """
        Определение типа субъекта по ИИН/БИН

        ИИН (физ. лицо): первая цифра 0-6
        БИН (юр. лицо): первая цифра 7-9
        """
        if not identifier or len(identifier) != 12:
            return 'unknown'

        first_digit = int(identifier[0])
        if first_digit <= 6:
            return 'individual'  # Физическое лицо
        else:
            return 'legal'  # Юридическое лицо

    @staticmethod
    def extract_iin_bin(text: str) -> Optional[str]:
        """Извлечение ИИН/БИН из текста"""
        matches = SmartBankStatementParser.IIN_PATTERN.findall(text)
        return matches[0] if matches else None

    @staticmethod
    def extract_account(text: str) -> Optional[str]:
        """Извлечение номера счета"""
        matches = SmartBankStatementParser.ACCOUNT_PATTERN.findall(text)
        return matches[0] if matches else None

    @staticmethod
    def detect_bank(text: str) -> Optional[str]:
        """Определение банка из текста"""
        text_lower = text.lower()
        for bank in SmartBankStatementParser.KAZAKHSTAN_BANKS:
            if bank.lower() in text_lower:
                return bank
        return None

    @staticmethod
    def detect_currency(text: str) -> str:
        """Определение валюты"""
        for symbol, currency in SmartBankStatementParser.CURRENCIES.items():
            if symbol.lower() in text.lower():
                return currency
        return 'KZT'  # По умолчанию тенге

    @staticmethod
    def parse_csv(file_path: str) -> Dict[str, Any]:
        """
        Парсинг CSV файла с интеллектуальным извлечением данных

        Returns:
            Dict с информацией о выписке и транзакциях
        """
        logger.info(f"Smart parsing CSV file: {file_path}")

        result = {
            'bank': None,
            'account_holder': None,
            'account_holder_type': 'unknown',
            'account_holder_iin_bin': None,
            'account_number': None,
            'currency': 'KZT',
            'transactions': [],
            'subjects': set(),  # Уникальные контрагенты
        }

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
                # Читаем первые строки для определения банка
                first_lines = ''.join([csvfile.readline() for _ in range(5)])
                csvfile.seek(0)

                # Определяем банк
                result['bank'] = SmartBankStatementParser.detect_bank(first_lines)
                result['currency'] = SmartBankStatementParser.detect_currency(first_lines)

                # Парсим CSV
                sample = csvfile.read(1024)
                csvfile.seek(0)

                sniffer = csv.Sniffer()
                try:
                    dialect = sniffer.sniff(sample)
                except csv.Error:
                    dialect = csv.excel

                reader = csv.DictReader(csvfile, dialect=dialect)

                for row in reader:
                    try:
                        # Дата - пробуем разные форматы
                        date_str = (row.get('Date') or row.get('Дата') or
                                  row.get('date') or row.get('Transaction Date'))
                        transaction_date = None
                        if date_str:
                            for date_format in ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%Y/%m/%d', '%d-%m-%Y']:
                                try:
                                    transaction_date = datetime.strptime(str(date_str).strip(), date_format)
                                    break
                                except ValueError:
                                    continue
                        if not transaction_date:
                            transaction_date = datetime.now()

                        # Сумма
                        amount_str = (row.get('Amount') or row.get('Сумма') or
                                    row.get('amount') or row.get('сумма') or '0')
                        amount = 0.0
                        try:
                            # Убираем все нецифровые символы кроме точки и минуса
                            cleaned = re.sub(r'[^\d.-]', '', str(amount_str))
                            amount = float(cleaned) if cleaned else 0.0
                        except (ValueError, TypeError):
                            amount = 0.0

                        # Тип транзакции
                        trans_type = (row.get('Type') or row.get('Тип') or
                                    row.get('type') or row.get('тип') or 'outgoing')
                        trans_type = trans_type.lower().strip()
                        if trans_type not in ['incoming', 'outgoing', 'transfer']:
                            trans_type = 'incoming' if amount > 0 else 'outgoing'

                        # Контрагент
                        counterparty = (row.get('Counterparty') or row.get('Контрагент') or
                                      row.get('counterparty') or row.get('контрагент') or
                                      row.get('Получатель') or row.get('Отправитель') or
                                      row.get('Name') or row.get('Имя') or 'Unknown')
                        counterparty = str(counterparty).strip()

                        # ИИН/БИН контрагента
                        iin_bin_col = (row.get('IIN_BIN') or row.get('ИИН_БИН') or
                                     row.get('ИИН') or row.get('БИН') or
                                     row.get('IIN') or row.get('BIN'))

                        # Если ИИН/БИН не в отдельной колонке, ищем в имени
                        counterparty_iin_bin = None
                        if iin_bin_col:
                            counterparty_iin_bin = str(iin_bin_col).strip()
                        else:
                            # Пытаемся извлечь из названия
                            extracted = SmartBankStatementParser.extract_iin_bin(counterparty)
                            if extracted:
                                counterparty_iin_bin = extracted

                        # Определяем тип контрагента
                        counterparty_type = 'unknown'
                        if counterparty_iin_bin and len(counterparty_iin_bin) == 12:
                            counterparty_type = SmartBankStatementParser.detect_subject_type(counterparty_iin_bin)

                        # Счет контрагента
                        account = (row.get('Account') or row.get('Счет') or
                                 row.get('account') or row.get('счет') or
                                 row.get('Счет получателя'))
                        if account:
                            account = str(account).strip()
                        else:
                            # Пытаемся извлечь из текста
                            for col_value in row.values():
                                if col_value:
                                    extracted = SmartBankStatementParser.extract_account(str(col_value))
                                    if extracted:
                                        account = extracted
                                        break

                        # Банк контрагента
                        bank = (row.get('Bank') or row.get('Банк') or
                               row.get('bank') or row.get('банк'))
                        if bank:
                            bank = str(bank).strip()
                        else:
                            # Пытаемся определить из текста
                            for col_value in row.values():
                                if col_value:
                                    detected = SmartBankStatementParser.detect_bank(str(col_value))
                                    if detected:
                                        bank = detected
                                        break

                        # Назначение платежа
                        purpose = (row.get('Purpose') or row.get('Назначение') or
                                 row.get('purpose') or row.get('назначение') or
                                 row.get('Description') or row.get('Описание') or '')
                        purpose = str(purpose).strip()

                        # Валюта (если указана в строке)
                        currency = result['currency']
                        currency_col = row.get('Currency') or row.get('Валюта')
                        if currency_col:
                            currency = str(currency_col).strip().upper()

                        transaction = {
                            'transaction_date': transaction_date,
                            'amount': abs(amount),
                            'currency': currency,
                            'transaction_type': trans_type,
                            'counterparty_name': counterparty,
                            'counterparty_type': counterparty_type,
                            'counterparty_account': account,
                            'counterparty_bank': bank,
                            'counterparty_iin_bin': counterparty_iin_bin,
                            'description': purpose,
                            'payment_purpose': purpose
                        }

                        result['transactions'].append(transaction)

                        # Добавляем контрагента в список субъектов
                        if counterparty_iin_bin:
                            result['subjects'].add((
                                counterparty,
                                counterparty_iin_bin,
                                counterparty_type
                            ))

                    except Exception as e:
                        logger.warning(f"Failed to parse row: {e}")
                        continue

            # Преобразуем subjects в список
            result['subjects'] = [
                {'name': name, 'identifier': iin_bin, 'type': s_type}
                for name, iin_bin, s_type in result['subjects']
            ]

            logger.info(f"Parsed {len(result['transactions'])} transactions, "
                       f"found {len(result['subjects'])} subjects")
            logger.info(f"Bank: {result['bank']}, Currency: {result['currency']}")

        except Exception as e:
            logger.error(f"Failed to parse CSV file: {e}")

        return result
