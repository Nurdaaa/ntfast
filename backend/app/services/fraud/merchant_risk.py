"""
Merchant Risk Scoring — оценка рисков мерчантов по категориям
"""
import logging
from typing import List, Dict, Optional
from collections import defaultdict
from ..bank_analyzer.base_parser import Transaction
from .models import MerchantRiskResult, AccountProfile, AccountType

logger = logging.getLogger(__name__)


# Категории рисков мерчантов
HIGH_RISK_KEYWORDS = {
    "gambling": ["1XBET", "MOSTBET", "MELBET", "FONBET", "PARIMATCH",
                 "OLIMPBET", "BETBOOM", "PINNACLE", "CASINO", "POKER",
                 "SLOTS", "ЛОТЕРЕЯ", "КАЗИНО", "СТАВКИ"],
    "crypto": ["BINANCE", "BYBIT", "OKEX", "HUOBI", "KUCOIN", "MEXC",
               "GATE.IO", "COINBASE", "KRAKEN", "BITGET"],
    "pawnshop": ["ЛОМБАРД", "PAWNSHOP", "ЗАЛОГ"],
    "money_transfer": ["WESTERN UNION", "CONTACT", "ЗОЛОТАЯ КОРОНА",
                       "MONEY GRAM", "UNISTREAM"],
}

MEDIUM_RISK_KEYWORDS = {
    "gaming": ["SENET", "CODASHOP", "STEAM", "EPIC GAMES", "XBOX",
               "PLAYSTATION", "NINTENDO", "RIOT", "BLIZZARD", "TOP GAME",
               "GOLD GAME"],
    "adult": ["ONLYFANS", "18+"],
    "fast_loans": ["ЗАЙМ", "МИКРОКРЕДИТ", "БЫСТРЫЕ ДЕНЬГИ"],
}

LOW_RISK_KEYWORDS = {
    "transport": ["YANDEX.GO", "BOLT", "UBER", "INDRIVER"],
    "food": ["MAGNUM", "SMALL", "FAMILY", "DUKEN", "РАХАТ", "РАХМЕТ"],
    "subscriptions": ["APPLE.COM", "SPOTIFY", "NETFLIX", "YOUTUBE",
                      "CLAUDE.AI", "YANDEX PLUS"],
    "telecom": ["ALTEL", "BEELINE", "KCELL", "TELE2"],
}


class MerchantRiskScorer:
    """Оценка рисков мерчантов с учётом типа аккаунта"""

    def analyze(
        self,
        transactions: List[Transaction],
        profile: Optional[AccountProfile] = None
    ) -> MerchantRiskResult:
        result = MerchantRiskResult()
        expenses = [t for t in transactions if t.amount < 0]
        if not expenses:
            return result

        if profile is None:
            profile = AccountProfile()

        total_expense = sum(abs(t.amount) for t in expenses)

        # Проверить каждую транзакцию-расход
        high_risk = defaultdict(lambda: {"amount": 0, "count": 0, "category": ""})
        medium_risk = defaultdict(lambda: {"amount": 0, "count": 0, "category": ""})

        for tx in expenses:
            desc = (tx.description or "").upper()

            # High risk
            for cat, keywords in HIGH_RISK_KEYWORDS.items():
                if any(kw in desc for kw in keywords):
                    matched = next(kw for kw in keywords if kw in desc)
                    high_risk[matched]["amount"] += abs(tx.amount)
                    high_risk[matched]["count"] += 1
                    high_risk[matched]["category"] = cat
                    break
            else:
                # Medium risk
                for cat, keywords in MEDIUM_RISK_KEYWORDS.items():
                    if any(kw in desc for kw in keywords):
                        matched = next(kw for kw in keywords if kw in desc)
                        medium_risk[matched]["amount"] += abs(tx.amount)
                        medium_risk[matched]["count"] += 1
                        medium_risk[matched]["category"] = cat
                        break

        result.high_risk_merchants = [
            {"name": name, "amount": d["amount"], "count": d["count"],
             "category": d["category"]}
            for name, d in sorted(high_risk.items(), key=lambda x: x[1]["amount"], reverse=True)
        ]

        result.medium_risk_merchants = [
            {"name": name, "amount": d["amount"], "count": d["count"],
             "category": d["category"]}
            for name, d in sorted(medium_risk.items(), key=lambda x: x[1]["amount"], reverse=True)
        ]

        result.total_high_risk_amount = sum(d["amount"] for d in high_risk.values())
        result.total_high_risk_pct = round(
            result.total_high_risk_amount / total_expense * 100, 2
        ) if total_expense > 0 else 0

        # Crypto and gambling amounts
        crypto_amount = sum(
            d["amount"] for d in high_risk.values() if d["category"] == "crypto"
        )
        gambling_amount = sum(
            d["amount"] for d in high_risk.values() if d["category"] == "gambling"
        )

        # Risk score — контекстный подход
        score = 0

        # ── Крипто: контекст трейдера ──────────────────────────
        if crypto_amount > 0:
            if profile.account_type == AccountType.TRADER:
                # Трейдер: штраф только если объём > 5x месячного дохода
                monthly_income = profile.avg_monthly_income or 1
                if crypto_amount > monthly_income * 5:
                    score += 30
                # иначе — 0 штрафа
            else:
                # Не-трейдер: штраф пропорционально % от расходов
                crypto_pct = crypto_amount / total_expense * 100 if total_expense > 0 else 0
                if crypto_pct > 30:
                    score += 40
                elif crypto_pct > 15:
                    score += 20
                elif crypto_pct > 5:
                    score += 10

        # ── Гемблинг: % от годового дохода ────────────────────
        if gambling_amount > 0:
            annual_income = profile.avg_monthly_income * 12 if profile.avg_monthly_income > 0 else 0
            if annual_income > 0:
                gambling_pct = gambling_amount / annual_income * 100
                if gambling_pct > 20:
                    score += 50
                elif gambling_pct > 10:
                    score += 30
                elif gambling_pct > 3:
                    score += 10
                # < 3% — не штрафуем
            else:
                # Нет данных о доходе — используем % от расходов
                gambling_pct_expense = gambling_amount / total_expense * 100 if total_expense > 0 else 0
                if gambling_pct_expense > 20:
                    score += 50
                elif gambling_pct_expense > 10:
                    score += 30
                elif gambling_pct_expense > 5:
                    score += 15

        # ── Прочие high-risk (ломбарды, переводы) ─────────────
        other_high_risk = result.total_high_risk_amount - crypto_amount - gambling_amount
        if total_expense > 0 and other_high_risk > 0:
            other_pct = other_high_risk / total_expense * 100
            if other_pct > 20:
                score += 30
            elif other_pct > 10:
                score += 15
            elif other_pct > 5:
                score += 8

        result.risk_score = min(100, score)
        return result
