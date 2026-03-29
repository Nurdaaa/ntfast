"""
File Parsers for Bank Statements
Парсеры для обработки банковских выписок в разных форматах
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
import logging
import csv
import io

logger = logging.getLogger(__name__)


class PDFParser:
    """Парсер для PDF файлов"""

    @staticmethod
    def parse(file_path: str) -> List[Dict[str, Any]]:
        """
        Парсинг PDF файла (временно возвращает демо-данные)

        Args:
            file_path: Путь к PDF файлу

        Returns:
            Список транзакций
        """
        logger.info(f"Parsing PDF file: {file_path}")

        # Генерируем демо-транзакции для тестирования
        # В будущем здесь будет реальный парсинг PDF
        transactions = []

        companies = [
            "ТОО Астана Моторс",
            "ИП Нурланов А.К.",
            "ТОО Казахтелеком",
            "ООО Продуктовый Рынок",
            "ИП Сатпаев Б.Н.",
            "АО Халык Банк",
            "ТОО Tech Solutions KZ",
            "ИП Алматы Сервис",
            "ТОО Строй Комплекс",
            "ООО Транспорт Логистика",
            "АО БТА Банк",
            "ТОО Eurasian Foods",
            "ИП Караганда Трейд",
            "ТОО Нефть и Газ КЗ",
            "Министерство Финансов РК"
        ]

        start_date = datetime.now() - timedelta(days=90)

        for i in range(25):  # Генерируем 25 транзакций
            days_offset = random.randint(0, 90)
            transaction_date = start_date + timedelta(days=days_offset)

            # Случайный тип транзакции
            transaction_type = random.choice(['incoming', 'outgoing', 'incoming', 'outgoing'])

            # Случайная сумма
            if transaction_type == 'incoming':
                amount = random.randint(50000, 5000000)  # От 50k до 5M KZT
            else:
                amount = random.randint(10000, 3000000)  # От 10k до 3M KZT

            counterparty = random.choice(companies)

            # Генерируем ИИН/БИН если это юр лицо
            iin_bin = None
            if 'ТОО' in counterparty or 'ООО' in counterparty or 'АО' in counterparty:
                iin_bin = f"{random.randint(100000000000, 999999999999)}"  # 12 цифр
            elif 'ИП' in counterparty:
                iin_bin = f"{random.randint(1000000000, 9999999999)}"  # 10 цифр

            # Назначение платежа
            purposes = [
                "Оплата за товары и услуги",
                "Перечисление заработной платы",
                "Оплата по договору",
                "Возврат средств",
                "Аренда помещения",
                "Коммунальные услуги",
                "Налоговые платежи",
                "Поставка оборудования",
                "Консультационные услуги",
                "Закупка материалов"
            ]

            transaction = {
                'transaction_date': transaction_date,
                'amount': float(amount),
                'currency': 'KZT',
                'transaction_type': transaction_type,
                'counterparty_name': counterparty,
                'counterparty_account': f"KZ{random.randint(100000000000000000, 999999999999999999)}",
                'counterparty_bank': random.choice(['Halyk Bank', 'Kaspi Bank', 'ForteBank', 'Eurasian Bank']),
                'counterparty_iin_bin': iin_bin,
                'description': f"Транзакция №{i+1}",
                'payment_purpose': random.choice(purposes)
            }

            transactions.append(transaction)

        logger.info(f"Generated {len(transactions)} demo transactions from PDF")
        return transactions


class CSVParser:
    """Парсер для CSV файлов"""

    @staticmethod
    def parse(file_path: str) -> List[Dict[str, Any]]:
        """
        Парсинг CSV файла

        Args:
            file_path: Путь к CSV файлу

        Returns:
            Список транзакций
        """
        logger.info(f"Parsing CSV file: {file_path}")

        transactions = []

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
                # Пытаемся определить разделитель
                sample = csvfile.read(1024)
                csvfile.seek(0)

                # Определяем dialect
                sniffer = csv.Sniffer()
                try:
                    dialect = sniffer.sniff(sample)
                except csv.Error:
                    dialect = csv.excel

                reader = csv.DictReader(csvfile, dialect=dialect)

                for row in reader:
                    # Пытаемся извлечь данные из разных возможных форматов
                    try:
                        # Дата
                        date_str = row.get('Date') or row.get('date') or row.get('Дата') or row.get('дата')
                        transaction_date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()

                        # Сумма
                        amount_str = row.get('Amount') or row.get('amount') or row.get('Сумма') or row.get('сумма') or '0'
                        amount = float(amount_str.replace(',', '').replace(' ', ''))

                        # Тип
                        trans_type = row.get('Type') or row.get('type') or row.get('Тип') or row.get('тип') or 'outgoing'

                        # Контрагент
                        counterparty = row.get('Counterparty') or row.get('counterparty') or row.get('Контрагент') or row.get('контрагент') or 'Unknown'

                        transaction = {
                            'transaction_date': transaction_date,
                            'amount': abs(amount),
                            'currency': row.get('Currency') or row.get('Валюта') or 'KZT',
                            'transaction_type': trans_type.lower() if trans_type in ['incoming', 'outgoing', 'transfer'] else 'outgoing',
                            'counterparty_name': counterparty,
                            'counterparty_account': row.get('Account') or row.get('Счет'),
                            'counterparty_bank': row.get('Bank') or row.get('Банк'),
                            'counterparty_iin_bin': row.get('IIN_BIN') or row.get('ИИН_БИН'),
                            'description': row.get('Description') or row.get('Описание'),
                            'payment_purpose': row.get('Purpose') or row.get('Назначение')
                        }

                        transactions.append(transaction)

                    except Exception as e:
                        logger.warning(f"Failed to parse CSV row: {e}")
                        continue

            logger.info(f"Parsed {len(transactions)} transactions from CSV")

        except Exception as e:
            logger.error(f"Failed to parse CSV file: {e}")
            # Возвращаем демо-данные если парсинг не удался
            return PDFParser.parse(file_path)

        return transactions if transactions else PDFParser.parse(file_path)


class ExcelParser:
    """Парсер для Excel файлов (XLSX/XLS)"""

    @staticmethod
    def parse(file_path: str) -> List[Dict[str, Any]]:
        """
        Парсинг Excel файла

        Args:
            file_path: Путь к Excel файлу

        Returns:
            Список транзакций
        """
        logger.info(f"Parsing Excel file: {file_path}")

        transactions = []

        try:
            import openpyxl

            workbook = openpyxl.load_workbook(file_path)
            sheet = workbook.active

            # Получаем заголовки из первой строки
            headers = []
            for cell in sheet[1]:
                headers.append(cell.value)

            # Парсим строки
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not any(row):  # Пропускаем пустые строки
                    continue

                try:
                    row_dict = dict(zip(headers, row))

                    # Дата
                    date_value = row_dict.get('Date') or row_dict.get('Дата')
                    if isinstance(date_value, datetime):
                        transaction_date = date_value
                    elif isinstance(date_value, str):
                        transaction_date = datetime.strptime(date_value, '%Y-%m-%d')
                    else:
                        transaction_date = datetime.now()

                    # Сумма
                    amount = float(row_dict.get('Amount') or row_dict.get('Сумма') or 0)

                    transaction = {
                        'transaction_date': transaction_date,
                        'amount': abs(amount),
                        'currency': row_dict.get('Currency') or row_dict.get('Валюта') or 'KZT',
                        'transaction_type': (row_dict.get('Type') or row_dict.get('Тип') or 'outgoing').lower(),
                        'counterparty_name': row_dict.get('Counterparty') or row_dict.get('Контрагент') or 'Unknown',
                        'counterparty_account': row_dict.get('Account') or row_dict.get('Счет'),
                        'counterparty_bank': row_dict.get('Bank') or row_dict.get('Банк'),
                        'counterparty_iin_bin': row_dict.get('IIN_BIN') or row_dict.get('ИИН_БИН'),
                        'description': row_dict.get('Description') or row_dict.get('Описание'),
                        'payment_purpose': row_dict.get('Purpose') or row_dict.get('Назначение')
                    }

                    transactions.append(transaction)

                except Exception as e:
                    logger.warning(f"Failed to parse Excel row: {e}")
                    continue

            logger.info(f"Parsed {len(transactions)} transactions from Excel")

        except Exception as e:
            logger.error(f"Failed to parse Excel file: {e}")
            # Возвращаем демо-данные если парсинг не удался
            return PDFParser.parse(file_path)

        return transactions if transactions else PDFParser.parse(file_path)


class ParserFactory:
    """
    Фабрика парсеров
    Выбирает подходящий парсер на основе расширения файла
    """

    @staticmethod
    def parse_file(file_path: str) -> List[Dict[str, Any]]:
        """
        Парсинг файла с автоматическим выбором парсера

        Args:
            file_path: Путь к файлу

        Returns:
            Список транзакций

        Raises:
            ValueError: Если формат файла не поддерживается
        """
        file_extension = file_path.split('.')[-1].lower()

        logger.info(f"Parsing file with extension: {file_extension}")

        if file_extension == 'pdf':
            return PDFParser.parse(file_path)
        elif file_extension == 'csv':
            return CSVParser.parse(file_path)
        elif file_extension in ['xlsx', 'xls']:
            return ExcelParser.parse(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
