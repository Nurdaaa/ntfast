"""
Anti-Fraud Detection Engine
Detects: Gaming/Gambling, Money Laundering, P2P Anomalies, Social Profiling
"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import logging

from .models import (
    Transaction, TransactionType, TransactionCategory,
    RiskAssessment, GamingGamblingAnalysis, MoneyLaunderingAnalysis,
    P2PAnalysis, SocialProfile, Counterparty
)

logger = logging.getLogger(__name__)


class FraudDetector:
    """Comprehensive fraud detection engine"""

    # Gaming/Gambling platforms
    GAMING_PLATFORMS = {
        # Betting
        "1XBET": "betting", "MOSTBET": "betting", "MELBET": "betting",
        "FONBET": "betting", "PARIMATCH": "betting", "OLIMPBET": "betting",
        "BETBOOM": "betting", "PINNACLE": "betting",
        # Gaming
        "SENET": "gaming", "STEAM": "gaming", "CODASHOP": "gaming",
        "GOLD GAME": "gaming", "TOP GAME": "gaming",
        "PLAYSTATION": "gaming", "XBOX": "gaming", "NINTENDO": "gaming",
        "EPIC GAMES": "gaming", "RIOT": "gaming", "BLIZZARD": "gaming",
        # Gambling
        "CASINO": "gambling", "POKER": "gambling", "SLOTS": "gambling",
        "КАЗИНО": "gambling", "ПОКЕР": "gambling", "ЛОТЕРЕЯ": "gambling"
    }

    # Income sources for social profiling
    INCOME_SOURCES = {
        "ПЕНСИЯ": "pension", "PENSION": "pension", "ЕНПФ": "pension",
        "ПОСОБИЕ": "social_benefit", "ГЦВП": "social_benefit",
        "СТИПЕНДИЯ": "scholarship", "SCHOLARSHIP": "scholarship",
        "ЗАРПЛАТА": "salary", "SALARY": "salary",
        "ИП": "entrepreneur", "ТОО": "business", "ДИВИДЕНД": "investment"
    }

    def __init__(self):
        self.thresholds = {
            "gaming_high_risk_amount": 50000,  # KZT
            "gaming_frequency_alert": 5,  # per week
            "round_amount_threshold": 100000,
            "split_window_hours": 24,
            "split_min_count": 3,
            "transit_window_hours": 48,
            "p2p_dependency_threshold": 0.3,  # 30%
            "pension_range": (50000, 200000),
            "scholarship_range": (20000, 80000)
        }

    def analyze(self, transactions: List[Transaction]) -> RiskAssessment:
        """Run full fraud analysis"""
        logger.info(f"Analyzing {len(transactions)} transactions")

        assessment = RiskAssessment()

        # 1. Gaming/Gambling Analysis
        assessment.gaming_gambling = self._analyze_gaming_gambling(transactions)

        # 2. Money Laundering Analysis
        assessment.money_laundering = self._analyze_money_laundering(transactions)

        # 3. P2P Analysis
        assessment.p2p_analysis = self._analyze_p2p(transactions)

        # 4. Social Profiling
        assessment.social_profile = self._build_social_profile(transactions)

        # Calculate total risk score
        assessment.total_score = self._calculate_total_score(assessment)
        assessment.risk_level = self._get_risk_level(assessment.total_score)

        # Generate recommendations and red flags
        assessment.recommendations, assessment.red_flags = self._generate_findings(assessment)

        return assessment

    def _analyze_gaming_gambling(self, transactions: List[Transaction]) -> GamingGamblingAnalysis:
        """Analyze gaming and gambling activity"""
        analysis = GamingGamblingAnalysis()

        gaming_transactions = []
        platforms = set()
        total_expense = sum(t.amount for t in transactions if t.transaction_type in [
            TransactionType.EXPENSE, TransactionType.P2P_OUT, TransactionType.TRANSFER_OUT
        ])

        for t in transactions:
            desc_upper = t.description.upper()

            for platform, ptype in self.GAMING_PLATFORMS.items():
                if platform in desc_upper:
                    gaming_transactions.append(t)
                    platforms.add(f"{platform} ({ptype})")
                    t.risk_flags.append(f"gaming_{ptype}")

                    if t.amount >= self.thresholds["gaming_high_risk_amount"]:
                        analysis.high_risk_transactions.append({
                            "date": t.date.isoformat(),
                            "amount": t.amount,
                            "platform": platform,
                            "type": ptype
                        })
                    break

        analysis.total_transactions = len(gaming_transactions)
        analysis.total_amount = sum(t.amount for t in gaming_transactions)
        analysis.platforms_detected = list(platforms)

        if transactions:
            # Calculate frequency
            if len(transactions) > 1:
                date_range = (transactions[-1].date - transactions[0].date).days or 1
                weeks = date_range / 7 or 1
                analysis.frequency_per_month = len(gaming_transactions) / (date_range / 30) if date_range > 0 else 0

        if total_expense > 0:
            analysis.percentage_of_expenses = (analysis.total_amount / total_expense) * 100

        # Risk scoring
        risk_score = 0.0

        # Betting is highest risk
        betting_count = sum(1 for p in platforms if "betting" in p)
        gambling_count = sum(1 for p in platforms if "gambling" in p)

        if betting_count > 0:
            risk_score += 40
        if gambling_count > 0:
            risk_score += 30
        if analysis.percentage_of_expenses > 20:
            risk_score += 20
        if len(analysis.high_risk_transactions) > 3:
            risk_score += 10

        analysis.risk_score = min(risk_score, 100)
        analysis.risk_level = self._get_risk_level(risk_score)

        return analysis

    def _analyze_money_laundering(self, transactions: List[Transaction]) -> MoneyLaunderingAnalysis:
        """Analyze for money laundering indicators"""
        analysis = MoneyLaunderingAnalysis()

        # 1. Round amount analysis
        round_amounts = [t for t in transactions if t.amount >= self.thresholds["round_amount_threshold"]
                         and t.amount % 10000 == 0]
        analysis.round_amount_transactions = len(round_amounts)

        # 2. Split transaction detection
        split_groups = self._detect_split_transactions(transactions)
        analysis.split_transaction_groups = len(split_groups)

        for group in split_groups:
            analysis.suspicious_patterns.append({
                "type": "split_transaction",
                "count": len(group),
                "total_amount": sum(t.amount for t in group),
                "time_window_hours": (group[-1].date - group[0].date).total_seconds() / 3600
            })

        # 3. Transit operations (money in and out quickly)
        transit_ops = self._detect_transit_operations(transactions)
        analysis.transit_operations = len(transit_ops)

        for op in transit_ops:
            analysis.suspicious_patterns.append({
                "type": "transit_operation",
                "in_amount": op["in_amount"],
                "out_amount": op["out_amount"],
                "time_diff_hours": op["time_diff"]
            })

        # 4. Cash intensity
        cash_transactions = [t for t in transactions if t.category in [
            TransactionCategory.CASH_WITHDRAWAL, TransactionCategory.CASH_DEPOSIT
        ]]
        total_turnover = sum(t.amount for t in transactions)
        if total_turnover > 0:
            analysis.cash_intensity = sum(t.amount for t in cash_transactions) / total_turnover * 100

        # Risk scoring
        risk_score = 0.0
        if analysis.split_transaction_groups > 2:
            risk_score += 30
        if analysis.transit_operations > 3:
            risk_score += 30
        if analysis.cash_intensity > 50:
            risk_score += 20
        if analysis.round_amount_transactions > 5:
            risk_score += 20

        analysis.risk_score = min(risk_score, 100)
        analysis.risk_level = self._get_risk_level(risk_score)

        return analysis

    def _detect_split_transactions(self, transactions: List[Transaction]) -> List[List[Transaction]]:
        """Detect potential split transactions"""
        split_groups = []
        window_hours = self.thresholds["split_window_hours"]
        min_count = self.thresholds["split_min_count"]

        # Group by counterparty
        by_counterparty = defaultdict(list)
        for t in transactions:
            if t.counterparty:
                by_counterparty[t.counterparty].append(t)

        for counterparty, trans in by_counterparty.items():
            if len(trans) < min_count:
                continue

            # Sort by date
            sorted_trans = sorted(trans, key=lambda x: x.date)

            # Find clusters within time window
            current_group = [sorted_trans[0]]
            for t in sorted_trans[1:]:
                time_diff = (t.date - current_group[-1].date).total_seconds() / 3600
                if time_diff <= window_hours:
                    current_group.append(t)
                else:
                    if len(current_group) >= min_count:
                        split_groups.append(current_group)
                    current_group = [t]

            if len(current_group) >= min_count:
                split_groups.append(current_group)

        return split_groups

    def _detect_transit_operations(self, transactions: List[Transaction]) -> List[Dict]:
        """Detect transit operations (quick in/out)"""
        transit_ops = []
        window_hours = self.thresholds["transit_window_hours"]

        income = [t for t in transactions if t.transaction_type in [
            TransactionType.INCOME, TransactionType.P2P_IN, TransactionType.TRANSFER_IN
        ]]
        expense = [t for t in transactions if t.transaction_type in [
            TransactionType.EXPENSE, TransactionType.P2P_OUT, TransactionType.TRANSFER_OUT
        ]]

        for inc in income:
            for exp in expense:
                time_diff = abs((exp.date - inc.date).total_seconds() / 3600)
                if time_diff <= window_hours:
                    # Check if amounts are similar (within 10%)
                    if abs(inc.amount - exp.amount) / max(inc.amount, exp.amount) < 0.1:
                        if inc.amount >= 50000:  # Minimum threshold
                            transit_ops.append({
                                "in_amount": inc.amount,
                                "out_amount": exp.amount,
                                "time_diff": time_diff,
                                "in_date": inc.date.isoformat(),
                                "out_date": exp.date.isoformat()
                            })

        return transit_ops

    def _analyze_p2p(self, transactions: List[Transaction]) -> P2PAnalysis:
        """Analyze P2P transfer patterns"""
        analysis = P2PAnalysis()

        p2p_transactions = [t for t in transactions if t.transaction_type in [
            TransactionType.P2P_IN, TransactionType.P2P_OUT
        ] or t.category == TransactionCategory.P2P_TRANSFER]

        # Calculate totals
        analysis.total_p2p_income = sum(t.amount for t in p2p_transactions
                                         if t.transaction_type in [TransactionType.P2P_IN, TransactionType.INCOME])
        analysis.total_p2p_expense = sum(t.amount for t in p2p_transactions
                                          if t.transaction_type in [TransactionType.P2P_OUT, TransactionType.EXPENSE])

        # Analyze counterparties
        counterparty_stats = defaultdict(lambda: {"income": 0, "expense": 0, "count": 0, "dates": []})

        for t in p2p_transactions:
            if t.counterparty:
                cp = t.counterparty.upper()
                counterparty_stats[cp]["count"] += 1
                counterparty_stats[cp]["dates"].append(t.date)

                if t.transaction_type in [TransactionType.P2P_IN, TransactionType.INCOME]:
                    counterparty_stats[cp]["income"] += t.amount
                else:
                    counterparty_stats[cp]["expense"] += t.amount

        analysis.unique_counterparties = len(counterparty_stats)

        # Top counterparties
        sorted_cp = sorted(counterparty_stats.items(),
                          key=lambda x: x[1]["income"] + x[1]["expense"], reverse=True)

        for name, stats in sorted_cp[:5]:
            analysis.top_counterparties.append({
                "name": name,
                "total_income": stats["income"],
                "total_expense": stats["expense"],
                "transaction_count": stats["count"]
            })

        # Dependency analysis
        total_income = sum(t.amount for t in transactions
                          if t.transaction_type in [TransactionType.INCOME, TransactionType.P2P_IN])

        if total_income > 0 and counterparty_stats:
            max_income_from_single = max(s["income"] for s in counterparty_stats.values())
            analysis.dependency_on_single_source = max_income_from_single / total_income

            if analysis.dependency_on_single_source > self.thresholds["p2p_dependency_threshold"]:
                analysis.suspicious_patterns.append(
                    f"High dependency on single P2P source: {analysis.dependency_on_single_source*100:.1f}%"
                )

        # Risk scoring
        risk_score = 0.0
        if analysis.dependency_on_single_source > 0.5:
            risk_score += 30
        if analysis.unique_counterparties > 20:
            risk_score += 20  # Too many P2P contacts
        if analysis.total_p2p_expense > analysis.total_p2p_income * 1.5:
            risk_score += 20  # Spending more than receiving via P2P

        analysis.risk_score = min(risk_score, 100)
        analysis.risk_level = self._get_risk_level(risk_score)

        return analysis

    def _build_social_profile(self, transactions: List[Transaction]) -> SocialProfile:
        """Build social profile from transaction patterns"""
        profile = SocialProfile()

        # Income source detection
        income_types = defaultdict(float)
        for t in transactions:
            if t.transaction_type in [TransactionType.INCOME, TransactionType.P2P_IN]:
                desc_upper = t.description.upper()
                for keyword, source_type in self.INCOME_SOURCES.items():
                    if keyword in desc_upper:
                        income_types[source_type] += t.amount
                        break

        profile.income_sources = list(income_types.keys())

        # Determine status
        if "pension" in income_types:
            profile.estimated_status = "pensioner"
            profile.confidence = 0.9
        elif "scholarship" in income_types:
            profile.estimated_status = "student"
            profile.confidence = 0.85
        elif "salary" in income_types:
            profile.estimated_status = "employed"
            profile.confidence = 0.9
        elif "entrepreneur" in income_types or "business" in income_types:
            profile.estimated_status = "entrepreneur"
            profile.confidence = 0.8
        elif income_types:
            profile.estimated_status = "mixed_income"
            profile.confidence = 0.6

        # Check for regular income
        income_transactions = [t for t in transactions
                               if t.transaction_type in [TransactionType.INCOME, TransactionType.P2P_IN]]

        if len(income_transactions) >= 3:
            profile.has_regular_income = True

        # Calculate averages
        total_income = sum(t.amount for t in transactions
                          if t.transaction_type in [TransactionType.INCOME, TransactionType.P2P_IN])
        total_expense = sum(t.amount for t in transactions
                           if t.transaction_type in [TransactionType.EXPENSE, TransactionType.P2P_OUT])

        if transactions:
            date_range = (transactions[-1].date - transactions[0].date).days or 1
            months = date_range / 30 or 1
            profile.avg_monthly_income = total_income / months
            profile.avg_monthly_expense = total_expense / months

        # Expense categories
        category_totals = defaultdict(float)
        for t in transactions:
            if t.transaction_type in [TransactionType.EXPENSE, TransactionType.P2P_OUT]:
                category_totals[t.category.value] += t.amount

        profile.main_expense_categories = [cat for cat, _ in
                                            sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:5]]

        # Subscriptions detection
        subs = set()
        for t in transactions:
            desc_upper = t.description.upper()
            for sub in ["APPLE", "SPOTIFY", "NETFLIX", "YOUTUBE", "YANDEX PLUS", "CLAUDE"]:
                if sub in desc_upper:
                    subs.add(sub)
        profile.subscriptions = list(subs)

        # Transport preference
        transport = [t for t in transactions if t.category == TransactionCategory.TRANSPORT]
        if transport:
            profile.transport_preference = "taxi" if any("YANDEX" in t.description.upper() for t in transport) else "other"

        # Financial stability
        if profile.avg_monthly_income > profile.avg_monthly_expense * 1.2:
            profile.financial_stability = "stable"
        elif profile.avg_monthly_income > profile.avg_monthly_expense:
            profile.financial_stability = "balanced"
        else:
            profile.financial_stability = "unstable"

        return profile

    def _calculate_total_score(self, assessment: RiskAssessment) -> float:
        """Calculate weighted total risk score"""
        weights = {
            "gaming_gambling": 0.35,
            "money_laundering": 0.30,
            "p2p": 0.20,
            "social": 0.15
        }

        total = (
            assessment.gaming_gambling.risk_score * weights["gaming_gambling"] +
            assessment.money_laundering.risk_score * weights["money_laundering"] +
            assessment.p2p_analysis.risk_score * weights["p2p"]
        )

        # Social profile can reduce risk if stable
        if assessment.social_profile.financial_stability == "stable":
            total *= 0.9

        return min(total, 100)

    def _get_risk_level(self, score: float) -> str:
        """Convert score to risk level"""
        if score >= 70:
            return "critical"
        elif score >= 50:
            return "high"
        elif score >= 25:
            return "medium"
        return "low"

    def _generate_findings(self, assessment: RiskAssessment) -> Tuple[List[str], List[str]]:
        """Generate recommendations and red flags"""
        recommendations = []
        red_flags = []

        # Gaming/Gambling
        if assessment.gaming_gambling.risk_level in ["high", "critical"]:
            red_flags.append(f"🎰 Active gambling/betting: {len(assessment.gaming_gambling.platforms_detected)} platforms detected")
            recommendations.append("Investigate gambling addiction patterns")

        if assessment.gaming_gambling.percentage_of_expenses > 15:
            red_flags.append(f"⚠️ {assessment.gaming_gambling.percentage_of_expenses:.1f}% of expenses on gaming/gambling")

        # Money Laundering
        if assessment.money_laundering.risk_level in ["high", "critical"]:
            red_flags.append("💰 Potential money laundering indicators detected")

        if assessment.money_laundering.split_transaction_groups > 0:
            red_flags.append(f"🔄 {assessment.money_laundering.split_transaction_groups} split transaction patterns detected")
            recommendations.append("Review split transaction groups for structuring")

        if assessment.money_laundering.transit_operations > 0:
            red_flags.append(f"➡️ {assessment.money_laundering.transit_operations} transit operations detected")

        # P2P
        if assessment.p2p_analysis.dependency_on_single_source > 0.5:
            red_flags.append(f"👥 High P2P dependency: {assessment.p2p_analysis.dependency_on_single_source*100:.1f}% from single source")
            recommendations.append("Verify relationship with primary P2P counterparty")

        # Social Profile
        if assessment.social_profile.financial_stability == "unstable":
            red_flags.append("📉 Financially unstable: expenses exceed income")
            recommendations.append("Assess financial risk for credit decisions")

        if not recommendations:
            recommendations.append("✅ No significant risk indicators found")

        return recommendations, red_flags
