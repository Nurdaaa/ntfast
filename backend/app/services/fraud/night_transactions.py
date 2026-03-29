"""
Детектор ночных транзакций — подозрительные операции в нерабочее время (23:00-06:00)

Суть: для обычного человека (зарплатник, пенсионер) переводы в 3 часа ночи —
это красный флаг. Мошенники часто действуют ночью, когда жертва спит.
Для бизнеса/трейдеров — менее подозрительно.

ВАЖНО: Если парсер не извлёк время (DD.MM.YY → 00:00:00), ночной анализ
пропускается, т.к. все транзакции ложно попадут в "ночные".
"""
import logging
from typing import List, Dict, Optional
from collections import defaultdict
from ..bank_analyzer.base_parser import Transaction
from .models import AccountProfile, AccountType

logger = logging.getLogger(__name__)

# Ночные часы (подозрительные)
NIGHT_START = 23  # 23:00
NIGHT_END = 6     # 06:00

# Порог суммы для крупных ночных переводов (50k — нормальное снятие в банкомате)
NIGHT_AMOUNT_THRESHOLD_KZT = 200_000  # 200k KZT

# Автоплатежи — ночные операции по расписанию, не подозрительные
AUTOPAYMENT_KEYWORDS = ("КОММУНАЛ", "ЖКХ", "АВТОПЛАТЕЖ", "AUTO", "АБОНЕНТ", "ПОДПИСКА")


class NightTransactionResult:
    """Результат анализа ночных транзакций"""
    def __init__(self):
        self.night_transactions: List[Dict] = []   # Список ночных транзакций
        self.night_count: int = 0                   # Количество ночных транзакций
        self.night_total_amount: float = 0.0        # Общая сумма ночных переводов
        self.night_ratio: float = 0.0               # Доля ночных от общего числа
        self.large_night_transfers: List[Dict] = [] # Крупные ночные переводы
        self.night_clusters: List[Dict] = []        # Кластеры ночных транзакций (серии)
        self.risk_score: float = 0.0
        self.no_time_data: bool = False             # Флаг: нет данных о времени

    def to_dict(self) -> Dict:
        return {
            "night_count": self.night_count,
            "night_total_amount": round(self.night_total_amount, 2),
            "night_ratio": round(self.night_ratio, 3),
            "large_night_transfers": self.large_night_transfers[:10],
            "night_clusters": self.night_clusters[:5],
            "risk_score": self.risk_score,
            "no_time_data": self.no_time_data,
        }


class NightTransactionDetector:
    """Детектор подозрительных ночных транзакций"""

    def _has_time_info(self, transactions: List[Transaction]) -> bool:
        """
        Проверяет, содержат ли транзакции реальную информацию о времени.
        Если все или почти все транзакции имеют время 00:00:00 — значит
        парсер не извлёк время (формат DD.MM.YY без времени), и ночной
        анализ бессмысленен.
        """
        if not transactions:
            return False

        midnight_count = sum(
            1 for tx in transactions
            if tx.date.hour == 0 and tx.date.minute == 0 and tx.date.second == 0
        )
        # Если >50% транзакций в 00:00:00 — скорее всего нет данных о времени
        # (многие банковские экспорты дают 60-70% записей без времени)
        midnight_ratio = midnight_count / len(transactions)
        return midnight_ratio < 0.5

    def analyze(
        self,
        transactions: List[Transaction],
        profile: Optional[AccountProfile] = None
    ) -> NightTransactionResult:
        result = NightTransactionResult()

        if not transactions or len(transactions) < 5:
            return result

        if profile is None:
            profile = AccountProfile()

        # ── ВАЖНО: Проверить есть ли данные о времени ──
        # Kaspi и другие парсеры часто дают даты без времени (DD.MM.YY → 00:00:00)
        # В этом случае ночной анализ невозможен — все бы попали в "ночные"
        if not self._has_time_info(transactions):
            result.no_time_data = True
            logger.info(
                "NightTransactions: SKIPPED — no time info in dates "
                f"(most of {len(transactions)} transactions at 00:00). "
                "Parser likely uses DD.MM.YY format without time."
            )
            return result

        sorted_txs = sorted(transactions, key=lambda t: t.date)

        # ── 1. Найти все ночные транзакции ──
        # Пропускаем входящие (получение денег ночью — не подозрительно)
        # Пропускаем автоплатежи (коммуналка, подписки — работают по расписанию)
        night_txs = []
        for tx in sorted_txs:
            hour = tx.date.hour
            if hour >= NIGHT_START or hour < NIGHT_END:
                # Входящие транзакции ночью не подозрительны
                if tx.amount > 0:
                    continue
                # Автоплатежи (коммуналка, подписки) — пропускаем
                desc_upper = (tx.description or "").upper()
                cp_upper = (tx.counterparty or "").upper()
                combined = desc_upper + " " + cp_upper
                if any(kw in combined for kw in AUTOPAYMENT_KEYWORDS):
                    continue
                night_txs.append(tx)
                result.night_transactions.append({
                    "date": tx.date.isoformat(),
                    "hour": hour,
                    "amount": tx.amount,
                    "counterparty": tx.counterparty or "",
                    "description": tx.description[:100],
                    "type": tx.type.value,
                })

        result.night_count = len(night_txs)
        result.night_total_amount = sum(abs(tx.amount) for tx in night_txs)
        result.night_ratio = len(night_txs) / len(transactions) if transactions else 0

        # ── 2. Крупные ночные переводы (исходящие) ──
        for tx in night_txs:
            if tx.amount < 0 and abs(tx.amount) >= NIGHT_AMOUNT_THRESHOLD_KZT:
                result.large_night_transfers.append({
                    "date": tx.date.isoformat(),
                    "hour": tx.date.hour,
                    "amount": abs(tx.amount),
                    "counterparty": tx.counterparty or "неизвестен",
                    "description": tx.description[:100],
                })

        # Сортируем по сумме (самые крупные сверху)
        result.large_night_transfers.sort(key=lambda x: x["amount"], reverse=True)

        # ── 3. Кластеры (серии ночных транзакций подряд) ──
        result.night_clusters = self._find_night_clusters(night_txs)

        # ── 4. Скоринг ──
        score = 0.0

        # Доля ночных транзакций (многие люди активны поздно — порог повышен)
        if result.night_ratio > 0.5:
            score += 20  # >50% ночных — умеренный риск
        elif result.night_ratio > 0.3:
            score += 10

        # Крупные ночные переводы (смягчённый скоринг)
        large_count = len(result.large_night_transfers)
        if large_count >= 5:
            score += 25
        elif large_count >= 3:
            score += 15
        elif large_count >= 1:
            score += 5

        # Кластеры (серии ночных)
        if result.night_clusters:
            max_cluster_size = max(c["count"] for c in result.night_clusters)
            if max_cluster_size >= 5:
                score += 25  # 5+ транзакций подряд ночью = подозрительно
            elif max_cluster_size >= 3:
                score += 15

        # Ночные исходящие переводы >1M KZT
        million_night = [t for t in result.large_night_transfers if t["amount"] >= 1_000_000]
        if million_night:
            score += min(30, 15 * len(million_night))

        result.risk_score = min(100, round(score, 1))

        logger.info(
            f"NightTransactions: {result.night_count} night txs "
            f"({result.night_ratio:.1%}), "
            f"large={len(result.large_night_transfers)}, "
            f"score={result.risk_score}"
        )

        return result

    def _find_night_clusters(self, night_txs: List[Transaction]) -> List[Dict]:
        """Найти серии ночных транзакций, совершённых подряд за одну ночь"""
        if len(night_txs) < 2:
            return []

        clusters = []
        current_cluster = [night_txs[0]]

        for i in range(1, len(night_txs)):
            prev = night_txs[i - 1]
            curr = night_txs[i]

            # Если между транзакциями < 2 часа — одна серия
            delta = (curr.date - prev.date).total_seconds()
            if delta <= 7200:  # 2 часа
                current_cluster.append(curr)
            else:
                if len(current_cluster) >= 2:
                    clusters.append(self._cluster_to_dict(current_cluster))
                current_cluster = [curr]

        # Последний кластер
        if len(current_cluster) >= 2:
            clusters.append(self._cluster_to_dict(current_cluster))

        return clusters

    def _cluster_to_dict(self, txs: List[Transaction]) -> Dict:
        return {
            "start": txs[0].date.isoformat(),
            "end": txs[-1].date.isoformat(),
            "count": len(txs),
            "total_amount": round(sum(abs(t.amount) for t in txs), 2),
            "counterparties": list(set(t.counterparty for t in txs if t.counterparty)),
        }
