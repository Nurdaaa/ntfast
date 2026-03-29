"""
Поведенческий анализ — установление baseline и обнаружение отклонений
"""
import logging
from typing import List, Dict, Optional
from collections import defaultdict
from ..bank_analyzer.base_parser import Transaction
from .models import BehavioralResult, AccountProfile, AccountType

logger = logging.getLogger(__name__)

# Пороги коэффициента вариации расходов по типу аккаунта
# Выше порога → "volatile"
VOLATILE_CV_THRESHOLDS = {
    AccountType.BUSINESS_OWNER:  1.2,   # норма для бизнеса — сезонность, проекты
    AccountType.TRADER:          1.0,   # трейдеры могут иметь нерегулярные расходы
    AccountType.FREELANCER:      0.9,   # фрилансеры — нерегулярные проекты
    AccountType.SALARY_EMPLOYEE: 0.6,   # наёмный работник — стабильные расходы
    AccountType.PENSIONER:       0.3,   # пенсионер — очень стабильные расходы
    AccountType.STUDENT:         0.7,   # студент
    AccountType.UNKNOWN:         0.7,   # по умолчанию
}


class BehavioralProfiler:
    """Поведенческое профилирование по транзакциям"""

    def analyze(
        self,
        transactions: List[Transaction],
        profile: Optional[AccountProfile] = None
    ) -> BehavioralResult:
        result = BehavioralResult()
        if len(transactions) < 10:
            return result

        if profile is None:
            profile = AccountProfile()

        sorted_txs = sorted(transactions, key=lambda t: t.date)

        # Baseline по дням недели
        result.weekday_pattern = self._weekday_baseline(sorted_txs)

        # Тренд расходов (с учётом типа аккаунта)
        result.spending_trend = self._spending_trend(sorted_txs, profile)

        # Аномалии по категориям
        result.category_anomalies = self._category_anomalies(sorted_txs)

        # Risk score
        score = 0
        if result.spending_trend == "volatile":
            score += 20
        elif result.spending_trend == "increasing":
            score += 10
        score += min(30, len(result.category_anomalies) * 10)

        result.risk_score = min(100, score)
        return result

    def _weekday_baseline(self, txs: List[Transaction]) -> Dict[str, float]:
        """Средние расходы по дням недели"""
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        weekday_amounts = defaultdict(list)

        for tx in txs:
            if tx.amount < 0:
                wd = tx.date.weekday()
                weekday_amounts[days[wd]].append(abs(tx.amount))

        return {
            day: round(sum(amounts) / len(amounts), 2) if amounts else 0
            for day in days
            for amounts in [weekday_amounts[day]]
        }

    def _spending_trend(
        self,
        txs: List[Transaction],
        profile: AccountProfile
    ) -> str:
        """Определить тренд расходов по месяцам с учётом типа аккаунта"""
        monthly = defaultdict(float)
        for tx in txs:
            if tx.amount < 0:
                key = (tx.date.year, tx.date.month)
                monthly[key] += abs(tx.amount)

        if len(monthly) < 3:
            return "insufficient_data"

        values = [monthly[k] for k in sorted(monthly.keys())]
        if len(values) < 3:
            return "stable"

        # Считаем среднее первой и второй половин
        mid = len(values) // 2
        first_half = sum(values[:mid]) / mid
        second_half = sum(values[mid:]) / (len(values) - mid)

        # Коэффициент вариации
        mean = sum(values) / len(values)
        if mean == 0:
            return "stable"
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        cv = (variance ** 0.5) / mean

        # Контекстный порог волатильности
        volatile_threshold = VOLATILE_CV_THRESHOLDS.get(profile.account_type, 0.7)

        if cv > volatile_threshold:
            return "volatile"
        elif second_half > first_half * 1.3:
            return "increasing"
        elif second_half < first_half * 0.7:
            return "decreasing"
        return "stable"

    def _category_anomalies(self, txs: List[Transaction]) -> List[Dict]:
        """Обнаружение аномальных категорий расходов"""
        category_amounts = defaultdict(list)

        for tx in txs:
            if tx.amount < 0 and tx.category:
                category_amounts[tx.category].append(abs(tx.amount))

        anomalies = []
        for cat, amounts in category_amounts.items():
            if len(amounts) < 3:
                continue

            mean = sum(amounts) / len(amounts)
            variance = sum((a - mean) ** 2 for a in amounts) / len(amounts)
            std = variance ** 0.5

            if std == 0:
                continue

            for amount in amounts:
                z = (amount - mean) / std
                if z > 3:
                    anomalies.append({
                        "category": cat,
                        "amount": amount,
                        "z_score": round(z, 2),
                        "category_mean": round(mean, 2),
                    })

        return sorted(anomalies, key=lambda a: a["z_score"], reverse=True)[:10]
