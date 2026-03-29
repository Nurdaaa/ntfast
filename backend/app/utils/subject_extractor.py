"""
Subject Extractor Utility
Утилита для автоматического извлечения субъектов из транзакций

v2: Исправлен маппинг полей Subject модели
    - unique_identifier (обязательное) = normalized_name + type
    - iin_bin (опциональное) вместо inn
    - Убраны несуществующие поля: description, is_verified, tags, metadata
"""
import re
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from ..models.subject import Subject
from ..models.transaction import Transaction

logger = logging.getLogger(__name__)


class SubjectExtractor:
    """
    Класс для извлечения субъектов из транзакций.

    Функционал:
    - Извлечение информации о контрагентах
    - Определение типа субъекта (физлицо/юрлицо)
    - Извлечение ИИН/БИН
    - Автоматическое создание Subject в БД
    """

    # Паттерны для определения типа субъекта (КЗ + РФ + международные)
    LEGAL_ENTITY_PATTERNS = [
        r'\b(ТОО|АО|ОАО|ЗАО|ПАО|НАО|ИП)\b',     # КЗ/РФ
        r'\b(ООО|ОДО|МУП|ГУП|КФХ)\b',              # РФ
        r'\b(LLC|LTD|Inc|Corp|Co|GmbH|AG|SA|BV)\b', # Международные
    ]

    # Паттерн для ИИН/БИН (12 цифр для КЗ)
    IIN_BIN_PATTERN = r'\b(\d{12})\b'

    # Ключевые слова для определения категорий
    CATEGORY_KEYWORDS = {
        'bank': ['банк', 'bank', 'кредит', 'credit'],
        'retail': ['магазин', 'shop', 'store', 'маркет', 'market'],
        'online': ['онлайн', 'online', 'интернет', 'web'],
        'transport': ['транспорт', 'transport', 'такси', 'taxi', 'uber', 'yandex'],
        'utilities': ['коммунальн', 'utility', 'услуг', 'service'],
        'food': ['рестора', 'кафе', 'cafe', 'restaurant', 'food'],
        'government': ['налог', 'tax', 'госуслуг', 'government', 'пенси', 'пособи'],
        'crypto': ['binance', 'bybit', 'crypto', 'крипт', 'bitcoin', 'btc'],
    }

    def __init__(self, db: Session):
        self.db = db
        self._subject_cache: Dict[str, Subject] = {}

    def extract_subjects_from_transactions(
        self,
        transactions: List[Transaction],
        auto_create: bool = True
    ) -> Dict[str, Subject]:
        """
        Извлечение субъектов из списка DB-транзакций.

        Args:
            transactions: Список DB-транзакций (app.models.transaction.Transaction)
            auto_create: Автоматически создавать субъектов в БД

        Returns:
            Dict[counterparty_name, Subject]
        """
        logger.info(f"Extracting subjects from {len(transactions)} transactions")

        extracted_subjects = {}

        for transaction in transactions:
            counterparty = transaction.counterparty_name

            if not counterparty or not counterparty.strip():
                continue

            counterparty = counterparty.strip()

            # Проверяем кэш
            if counterparty in self._subject_cache:
                extracted_subjects[counterparty] = self._subject_cache[counterparty]
                if transaction.subject_id is None:
                    transaction.subject_id = self._subject_cache[counterparty].id
                continue

            # Генерируем unique_identifier для поиска
            subject_type = self._determine_subject_type(counterparty)
            unique_id = self._generate_unique_identifier(counterparty, subject_type)

            # Проверяем БД по unique_identifier
            existing_subject = self.db.query(Subject).filter(
                Subject.unique_identifier == unique_id
            ).first()

            if existing_subject:
                self._subject_cache[counterparty] = existing_subject
                extracted_subjects[counterparty] = existing_subject
                if transaction.subject_id is None:
                    transaction.subject_id = existing_subject.id
                continue

            # Также проверяем по имени (для обратной совместимости)
            existing_by_name = self.db.query(Subject).filter(
                Subject.name == counterparty
            ).first()

            if existing_by_name:
                self._subject_cache[counterparty] = existing_by_name
                extracted_subjects[counterparty] = existing_by_name
                if transaction.subject_id is None:
                    transaction.subject_id = existing_by_name.id
                continue

            # Создаем новый субъект
            if auto_create:
                new_subject = self._create_subject_from_counterparty(
                    counterparty, subject_type, unique_id, transaction
                )

                if new_subject:
                    self._subject_cache[counterparty] = new_subject
                    extracted_subjects[counterparty] = new_subject
                    transaction.subject_id = new_subject.id

        if auto_create:
            try:
                self.db.commit()
            except Exception as e:
                logger.error(f"Error committing subjects: {e}")
                self.db.rollback()

        logger.info(f"Extracted {len(extracted_subjects)} subjects")
        return extracted_subjects

    def _generate_unique_identifier(self, name: str, subject_type: str) -> str:
        """
        Генерация unique_identifier для субъекта.

        Формат: normalized_name_type
        Пример: "ержан_о_individual", "too_kaspi_gold_legal_entity"
        """
        normalized = self._normalize_name(name).lower()
        # Заменяем пробелы на подчёркивания, убираем спецсимволы
        normalized = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\s]', '', normalized)
        normalized = re.sub(r'\s+', '_', normalized.strip())

        # Ограничиваем длину
        if len(normalized) > 150:
            normalized = normalized[:150]

        return f"{normalized}_{subject_type}"

    def _create_subject_from_counterparty(
        self,
        counterparty_name: str,
        subject_type: str,
        unique_identifier: str,
        transaction: Transaction
    ) -> Optional[Subject]:
        """
        Создание субъекта в БД из данных контрагента.

        Поля Subject модели:
        - unique_identifier (обязательное, unique)
        - name (обязательное)
        - iin_bin (опциональное)
        - type (обязательное): individual, legal_entity, account_owner
        - risk_level (default 0)
        - status (default "active")
        """
        try:
            # Извлекаем ИИН/БИН если есть
            iin_bin = self._extract_iin_bin(counterparty_name)
            if not iin_bin and transaction.counterparty_iin_bin:
                iin_bin = transaction.counterparty_iin_bin

            # Нормализуем имя
            normalized_name = self._normalize_name(counterparty_name)

            new_subject = Subject(
                unique_identifier=unique_identifier,
                name=normalized_name,
                iin_bin=iin_bin,
                type=subject_type,
                risk_level=0,
                status="active",
            )

            self.db.add(new_subject)
            self.db.flush()  # Получаем ID без commit

            logger.info(
                f"Created subject: {new_subject.name} "
                f"(ID: {new_subject.id}, type: {subject_type}, "
                f"uid: {unique_identifier})"
            )

            return new_subject

        except Exception as e:
            logger.error(f"Error creating subject '{counterparty_name}': {e}")
            self.db.rollback()
            return None

    def _determine_subject_type(self, name: str) -> str:
        """
        Определение типа субъекта (физлицо/юрлицо).

        Returns:
            'legal_entity' или 'individual'
        """
        # Проверяем паттерны юрлиц
        for pattern in self.LEGAL_ENTITY_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return 'legal_entity'

        # Казахские имена: "Ержан О.", "Маржан П." — физлица
        if re.match(r'^[А-ЯЁA-Z][а-яёa-z]+\s+[А-ЯЁA-Z]\.?$', name.strip()):
            return 'individual'

        # ФИО: "Иванов Иван Иванович"
        if name.count(' ') >= 1 and len(name.split()) <= 4:
            if not re.search(r'\d', name):
                return 'individual'

        # По умолчанию — юрлицо (мерчанты, магазины и т.д.)
        return 'legal_entity'

    def _extract_iin_bin(self, text: str) -> Optional[str]:
        """
        Извлечение ИИН/БИН из текста.
        ИИН — 12 цифр (физлица КЗ), БИН — 12 цифр (юрлица КЗ)
        """
        matches = re.findall(self.IIN_BIN_PATTERN, text)
        for match in matches:
            if len(match) == 12:
                return match
        return None

    def _determine_category(self, name: str) -> Optional[str]:
        """Определение категории субъекта по ключевым словам."""
        name_lower = name.lower()
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in name_lower:
                    return category
        return None

    def _normalize_name(self, name: str) -> str:
        """Нормализация имени контрагента."""
        # Убираем лишние пробелы
        normalized = ' '.join(name.split())

        # Убираем ИИН/БИН из имени
        normalized = re.sub(self.IIN_BIN_PATTERN, '', normalized)

        # Убираем повторяющиеся слова
        words = normalized.split()
        seen = set()
        unique_words = []
        for word in words:
            word_lower = word.lower()
            if word_lower not in seen:
                seen.add(word_lower)
                unique_words.append(word)

        normalized = ' '.join(unique_words).strip()
        return normalized if normalized else name.strip()

    def get_or_create_subject(
        self,
        counterparty_name: str,
        transaction: Optional[Transaction] = None
    ) -> Optional[Subject]:
        """Получить существующий или создать новый субъект."""
        if not counterparty_name or not counterparty_name.strip():
            return None

        counterparty_name = counterparty_name.strip()

        # Проверяем кэш
        if counterparty_name in self._subject_cache:
            return self._subject_cache[counterparty_name]

        # Определяем тип и unique_identifier
        subject_type = self._determine_subject_type(counterparty_name)
        unique_id = self._generate_unique_identifier(counterparty_name, subject_type)

        # Проверяем БД по unique_identifier
        existing = self.db.query(Subject).filter(
            Subject.unique_identifier == unique_id
        ).first()

        if existing:
            self._subject_cache[counterparty_name] = existing
            return existing

        # Проверяем по имени (обратная совместимость)
        existing_by_name = self.db.query(Subject).filter(
            Subject.name == counterparty_name
        ).first()

        if existing_by_name:
            self._subject_cache[counterparty_name] = existing_by_name
            return existing_by_name

        # Создаем новый субъект — нужен dummy transaction если не передан
        if transaction is None:
            transaction = Transaction(
                amount=0, transaction_type="other",
                transaction_date=datetime.utcnow()
            )

        new_subject = self._create_subject_from_counterparty(
            counterparty_name, subject_type, unique_id, transaction
        )

        if new_subject:
            try:
                self.db.commit()
            except Exception as e:
                logger.error(f"Error committing new subject: {e}")
                self.db.rollback()
                return None
            self._subject_cache[counterparty_name] = new_subject

        return new_subject

    def create_account_owner_subject(
        self,
        owner_name: str,
        account_number: str,
        iin_bin: Optional[str] = None
    ) -> Optional[Subject]:
        """
        Создание субъекта-владельца счёта.

        Args:
            owner_name: ФИО владельца
            account_number: Номер счёта / IBAN
            iin_bin: ИИН/БИН (опционально)

        Returns:
            Subject или None
        """
        # unique_identifier = IBAN или номер счёта
        unique_id = account_number if account_number else \
            self._generate_unique_identifier(owner_name, "account_owner")

        # Проверяем существует ли
        existing = self.db.query(Subject).filter(
            Subject.unique_identifier == unique_id
        ).first()

        if existing:
            return existing

        try:
            subject = Subject(
                unique_identifier=unique_id,
                name=self._normalize_name(owner_name),
                iin_bin=iin_bin,
                type="account_owner",
                risk_level=0,
                status="active",
            )
            self.db.add(subject)
            self.db.flush()

            logger.info(
                f"Created account owner subject: {subject.name} "
                f"(ID: {subject.id}, uid: {unique_id})"
            )
            return subject

        except Exception as e:
            logger.error(f"Error creating account owner subject: {e}")
            self.db.rollback()
            return None

    def link_transaction_to_subject(self, transaction: Transaction, subject: Subject):
        """Связывание транзакции с субъектом."""
        transaction.subject_id = subject.id
        self.db.add(transaction)

    def merge_duplicate_subjects(self) -> int:
        """
        Объединение дубликатов субъектов по нормализованному имени.

        Returns:
            Количество объединенных субъектов
        """
        logger.info("Searching for duplicate subjects...")

        all_subjects = self.db.query(Subject).all()

        # Группируем по нормализованному имени
        name_groups: Dict[str, List[Subject]] = {}
        for subject in all_subjects:
            normalized = self._normalize_name(subject.name).lower()
            if normalized not in name_groups:
                name_groups[normalized] = []
            name_groups[normalized].append(subject)

        merged_count = 0

        for normalized_name, subjects in name_groups.items():
            if len(subjects) > 1:
                main_subject = subjects[0]
                duplicates = subjects[1:]

                logger.info(f"Found {len(duplicates)} duplicates for '{main_subject.name}'")

                for duplicate in duplicates:
                    # Переносим транзакции на основной субъект
                    self.db.query(Transaction).filter(
                        Transaction.subject_id == duplicate.id
                    ).update({'subject_id': main_subject.id})

                    # Если у дубликата есть ИИН а у основного нет — копируем
                    if duplicate.iin_bin and not main_subject.iin_bin:
                        main_subject.iin_bin = duplicate.iin_bin

                    self.db.delete(duplicate)
                    merged_count += 1

        try:
            self.db.commit()
        except Exception as e:
            logger.error(f"Error merging subjects: {e}")
            self.db.rollback()

        logger.info(f"Merged {merged_count} duplicate subjects")
        return merged_count
