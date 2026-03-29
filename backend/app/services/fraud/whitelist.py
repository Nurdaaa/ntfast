"""
PatternWhitelist — подавление легальных паттернов в fraud-анализе.

Транзакции из whitelist не влияют на скоринг большинства модулей.
Это главный механизм предотвращения ложных срабатываний на законопослушных людях.
"""
import math
from collections import defaultdict
from typing import List, Set, Optional

from .models import AccountProfile, AccountType


# ── Ключевые слова легальных категорий ───────────────────────────

UTILITY_KEYWORDS = {
    # Коммунальные услуги Казахстана
    "АЛМАТЫЭНЕРГОСБЫТ", "ГОРГАЗ", "КАЗТЕЛЕКОМ", "KCELL", "ALTEL",
    "BEELINE", "TELE2", "КОММУНАЛ", "ЖКХ", "КСК", "SNABKAZ",
    "ASTANAGAS", "ENERGO", "SVЕТ", "ВОД", "КАНАЛ", "ТЕПЛОСЕТЬ",
    "ЖЫЛУ", "СУ", "ЭЛЕКТР",
}

MORTGAGE_KEYWORDS = {
    "ИПОТЕКА", "ЖИЛСТРОЙСБЕРБАНК", "ЖССБ", "MORTGAGE",
    "HALYK MORTGAGE", "HOME CREDIT MORTGAGE", "ТҰРҒЫН ҮЙ",
    "ЖИЛИЩНЫЙ КРЕДИТ", "БАСПАНА",
}

INSURANCE_KEYWORDS = {
    "СТРАХОВА", "INSURANCE", "NOMAD LIFE", "JUSAN LIFE",
    "ХАЛЫК СТРАХОВАНИЕ", "КАЗКОММЕРЦ LIFE", "СИГМА",
    "INTERTEACH", "САҚТАНДЫРУ",
}

TRANSPORT_KEYWORDS = {
    "AVTOBYS", "АВТОБУС", "METRO", "МЕТРО", "ТРАНСПОРТ",
    "UBER", "YANDEX TAXI", "INDRIVE", "BOLT",
}

SALARY_KEYWORDS = {"ЗАРПЛАТА", "SALARY", "ОКЛАД", "ЗП", "ЖАЛАҚЫ"}

# Ключевые слова мерчантов / юрлиц (НЕ физические лица)
MERCHANT_KEYWORDS = {
    "ТОО", "АО ", "ИП ", "ООО", "ЗАО", "ОАО",
    "BANK", "БАНК", "KASPI", "ХАЛЫК",
    "МАГНУМ", "MAGNUM", "SMALL", "GLOVO", "WOLT",
    "ТЕХНОДОМ", "SULPAK", "MECHTA", "МЕЧТА",
    "METRO", "SPAR",
    "WILDBERRIES", "OZON", "LAMODA", "ALIEXPRESS", "AMAZON",
    "GOOGLE", "APPLE", "SPOTIFY", "NETFLIX", "YOUTUBE",
    "UBER", "YANDEX", "INDRIVE", "BOLT",
    "PHARMACIE", "АПТЕКА", "PHARMA",
    "FREEDOM", "JUSAN",
}

# Паттерны, однозначно указывающие на юрлицо
MERCHANT_PREFIXES = ("ТОО ", "АО ", "ИП ", "ООО ", "ЗАО ", "ОАО ")


class PatternWhitelist:
    """
    Определяет транзакции, которые НЕ должны штрафоваться в fraud-анализе.

    Использование:
        whitelist = PatternWhitelist()
        safe_ids = whitelist.build_whitelisted_tx_ids(transactions, profile)
        analysis_txs = [t for i, t in enumerate(transactions) if i not in safe_ids]
    """

    def build_whitelisted_tx_ids(
        self,
        transactions: list,
        profile: AccountProfile
    ) -> Set[int]:
        """
        Возвращает множество индексов транзакций, которые безопасны (whitelist).
        """
        whitelisted: Set[int] = set()

        for i, tx in enumerate(transactions):
            amount = self._get_amount(tx)
            cp = self._get_counterparty(tx).upper()
            desc = self._get_description(tx).upper()
            combined = cp + " " + desc

            if amount > 0:
                # Зарплата
                if self.is_regular_salary(tx, profile, combined):
                    whitelisted.add(i)
            elif amount < 0:
                # Коммунальные платежи
                if self.is_utility_payment(combined):
                    whitelisted.add(i)
                # Транспорт
                elif self.is_transport_payment(combined):
                    whitelisted.add(i)

        # Семейные переводы (требуют анализа всей истории)
        family_ids = self._find_family_transfers(transactions)
        whitelisted.update(family_ids)

        return whitelisted

    def is_regular_salary(
        self,
        tx,
        profile: AccountProfile,
        combined_text: str = ""
    ) -> bool:
        """Зарплатный перевод от работодателя."""
        if getattr(tx, 'is_salary', False):
            return True
        if any(kw in combined_text for kw in SALARY_KEYWORDS):
            return True
        # Регулярный источник при высоком income_regularity_score
        if profile.has_salary_flag and profile.income_regularity_score > 0.5:
            return True
        return False

    def is_utility_payment(self, combined_text: str) -> bool:
        """Оплата коммунальных услуг, ипотеки, страховки."""
        return any(
            kw in combined_text
            for kw in UTILITY_KEYWORDS | MORTGAGE_KEYWORDS | INSURANCE_KEYWORDS
        )

    def is_transport_payment(self, combined_text: str) -> bool:
        """Оплата транспорта (автобус, такси, метро)."""
        return any(kw in combined_text for kw in TRANSPORT_KEYWORDS)

    def is_investment_activity(
        self,
        tx,
        profile: AccountProfile,
        combined_text: str = ""
    ) -> bool:
        """
        Инвестиционная активность (крипто/акции).
        Для TRADER — всегда легально.
        Для остальных — легально если < 10% от месячного дохода.
        """
        if profile.account_type == AccountType.TRADER:
            return True
        if profile.avg_monthly_income > 0:
            pct = abs(self._get_amount(tx)) / profile.avg_monthly_income
            return pct < 0.10
        return False

    def is_family_transfer(
        self,
        tx,
        all_transactions: list,
        profile: AccountProfile
    ) -> bool:
        """
        Регулярный перевод одному и тому же получателю >= 3 месяца.
        CV суммы < 0.2 (стабильная сумма = признак семейной поддержки).
        Только для ФИЗИЧЕСКИХ ЛИЦ, не для мерчантов.
        """
        cp = self._get_counterparty(tx)
        if not cp or self._get_amount(tx) >= 0:
            return False
        # Мерчанты не являются «семейными переводами»
        if self._looks_like_merchant(cp):
            return False

        months_seen: Set[tuple] = set()
        amounts: List[float] = []

        for t in all_transactions:
            if self._get_amount(t) < 0 and self._get_counterparty(t) == cp:
                dt = self._get_date(t)
                if dt:
                    months_seen.add((dt.year, dt.month))
                    amounts.append(abs(self._get_amount(t)))

        if len(months_seen) < 3:
            return False

        if len(amounts) >= 3:
            mean = sum(amounts) / len(amounts)
            if mean > 0:
                variance = sum((a - mean) ** 2 for a in amounts) / len(amounts)
                cv = math.sqrt(variance) / mean
                return cv < 0.20

        return False

    def is_payroll_distribution(
        self,
        transactions: list,
        profile: AccountProfile
    ) -> bool:
        """
        Работодатель, распределяющий зарплаты.
        Признак: один день, >= 3 разных физлиц получают переводы.
        Применяется только для BUSINESS_OWNER.
        """
        if profile.account_type != AccountType.BUSINESS_OWNER:
            return False

        daily_recipients: dict = defaultdict(set)
        for t in transactions:
            if self._get_amount(t) < 0:
                dt = self._get_date(t)
                cp = self._get_counterparty(t)
                if dt and cp:
                    daily_recipients[dt.date()].add(cp)

        return any(len(recipients) >= 3 for recipients in daily_recipients.values())

    def is_business_cashflow(self, income_tx, expense_tx) -> bool:
        """
        Бизнес cash flow: получили платёж → оплатили поставщику за 48ч.
        Легально для FREELANCER и BUSINESS_OWNER если получатель — мерчант/банк.
        """
        try:
            income_date = self._get_date(income_tx)
            expense_date = self._get_date(expense_tx)
            if income_date is None or expense_date is None:
                return False

            hours_gap = (expense_date - income_date).total_seconds() / 3600
            if hours_gap < 0 or hours_gap > 48:
                return False

            # Проверяем тип получателя расходной транзакции
            cp = self._get_counterparty(expense_tx).upper()
            # Если это мерчант (ТОО, АО, ИП) — легально
            for kw in ("ТОО", "АО ", "ИП ", "ООО", "BANK", "БАНК", "KASPI"):
                if kw in cp:
                    return True

            return False
        except Exception:
            return False

    # ── Внутренние методы ───────────────────────────────────────

    def _looks_like_merchant(self, counterparty: str) -> bool:
        """
        Определяет, является ли контрагент мерчантом/юрлицом.

        Мерчанты НЕ должны попадать в «семейные переводы».
        Семейные переводы — это регулярные переводы физическим лицам
        (родители, дети, супруги).
        """
        cp_upper = counterparty.upper().strip()

        # 1. Проверка по известным ключевым словам мерчантов
        for kw in MERCHANT_KEYWORDS:
            if kw in cp_upper:
                return True

        # 2. Проверка по префиксам юрлиц
        for prefix in MERCHANT_PREFIXES:
            if cp_upper.startswith(prefix):
                return True

        # 3. Проверка на утилиты, страховки, транспорт
        if any(kw in cp_upper for kw in UTILITY_KEYWORDS | INSURANCE_KEYWORDS | TRANSPORT_KEYWORDS | MORTGAGE_KEYWORDS):
            return True

        return False

    def _find_family_transfers(self, transactions: list) -> Set[int]:
        """
        Найти все индексы семейных переводов в списке транзакций.

        Семейные переводы — регулярные переводы ФИЗИЧЕСКИМ ЛИЦАМ
        (>= 3 месяца, CV суммы < 0.20).
        Мерчанты / юрлица исключаются — они не являются семьёй.
        """
        whitelisted: Set[int] = set()
        # Группируем расходы по контрагенту
        cp_indices: dict = defaultdict(list)
        cp_amounts: dict = defaultdict(list)
        cp_months: dict = defaultdict(set)

        for i, t in enumerate(transactions):
            amount = self._get_amount(t)
            if amount >= 0:
                continue
            cp = self._get_counterparty(t)
            if not cp:
                continue

            # ── КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: пропускаем мерчантов ──
            if self._looks_like_merchant(cp):
                continue

            dt = self._get_date(t)
            cp_indices[cp].append(i)
            cp_amounts[cp].append(abs(amount))
            if dt:
                cp_months[cp].add((dt.year, dt.month))

        for cp, indices in cp_indices.items():
            months = cp_months.get(cp, set())
            amounts = cp_amounts.get(cp, [])
            if len(months) < 3 or len(amounts) < 3:
                continue

            mean = sum(amounts) / len(amounts)
            if mean <= 0:
                continue

            variance = sum((a - mean) ** 2 for a in amounts) / len(amounts)
            cv = math.sqrt(variance) / mean
            if cv < 0.20:
                whitelisted.update(indices)

        return whitelisted

    def _get_amount(self, t) -> float:
        return float(getattr(t, 'amount', 0) or 0)

    def _get_counterparty(self, t) -> str:
        for attr in ('counterparty_name', 'counterparty', 'merchant_name'):
            val = getattr(t, attr, None)
            if val:
                return str(val).strip()
        return ""

    def _get_description(self, t) -> str:
        return str(getattr(t, 'description', '') or '').strip()

    def _get_date(self, t):
        for attr in ('transaction_date', 'date', 'created_at'):
            val = getattr(t, attr, None)
            if val is not None:
                return val
        return None
