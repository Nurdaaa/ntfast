"""
Main Financial Analyzer - Orchestrates all components
"""
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import asdict

from .parser import KaspiStatementParser
from .anonymizer import DataAnonymizer
from .fraud_detector import FraudDetector
from .ollama_client import OllamaAnalyzer, OllamaAnalyzerSync
from .models import AnalysisReport, Transaction, TransactionType

logger = logging.getLogger(__name__)


class FinancialAnalyzer:
    """Main orchestrator for PDF financial analysis"""

    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        ollama_model: str = "llama3:8b",
        use_ai: bool = True
    ):
        self.fraud_detector = FraudDetector()
        self.ollama = OllamaAnalyzerSync(host=ollama_host, model=ollama_model) if use_ai else None
        self.use_ai = use_ai and self.ollama is not None

    def analyze_pdf(self, pdf_path: str, anonymize: bool = True) -> Dict[str, Any]:
        """
        Analyze PDF bank statement

        Args:
            pdf_path: Path to PDF file
            anonymize: Whether to anonymize personal data

        Returns:
            Complete analysis report as dictionary
        """
        logger.info(f"Starting analysis of: {pdf_path}")

        # 1. Parse PDF
        parser = KaspiStatementParser(pdf_path)
        transactions, metadata = parser.parse()

        if not transactions:
            return {
                "success": False,
                "error": "No transactions found in PDF",
                "pdf_hash": parser.pdf_hash
            }

        # 2. Anonymize data
        customer_name = metadata.get("customer_name", "")
        anonymizer = DataAnonymizer(customer_name) if anonymize else None

        if anonymizer:
            transactions = anonymizer.anonymize_transactions(transactions)

        # 3. Run fraud detection
        risk_assessment = self.fraud_detector.analyze(transactions)

        # 4. Build report
        report = self._build_report(
            transactions=transactions,
            metadata=metadata,
            risk_assessment=risk_assessment,
            pdf_path=pdf_path,
            pdf_hash=parser.pdf_hash
        )

        # 5. AI analysis (if enabled)
        if self.use_ai and self.ollama.check_connection():
            try:
                prompt = self._build_ai_prompt(report)
                ai_response = self.ollama.generate(prompt)
                report.ai_summary = ai_response
            except Exception as e:
                logger.error(f"AI analysis failed: {e}")
                report.ai_summary = "AI analysis unavailable"

        # 6. Convert to dict
        result = self._report_to_dict(report)

        # Add anonymization info
        if anonymizer:
            result["anonymization"] = anonymizer.get_anonymization_report()

        logger.info(f"Analysis complete. Risk level: {risk_assessment.risk_level}")
        return result

    def _build_report(
        self,
        transactions: list,
        metadata: dict,
        risk_assessment,
        pdf_path: str,
        pdf_hash: str
    ) -> AnalysisReport:
        """Build complete analysis report"""
        report = AnalysisReport(
            analysis_id=str(uuid.uuid4()),
            analysis_date=datetime.now(),
            pdf_filename=Path(pdf_path).name,
            pdf_hash=pdf_hash,
            customer_id="[CUSTOMER_NAME]",
            account_period_start=metadata.get("period_start"),
            account_period_end=metadata.get("period_end"),
            total_transactions=len(transactions),
            transactions=transactions,
            risk_assessment=risk_assessment
        )

        # Calculate totals
        report.total_income = sum(
            t.amount for t in transactions
            if t.transaction_type in [TransactionType.INCOME, TransactionType.P2P_IN, TransactionType.TRANSFER_IN]
        )
        report.total_expense = sum(
            t.amount for t in transactions
            if t.transaction_type in [TransactionType.EXPENSE, TransactionType.P2P_OUT, TransactionType.TRANSFER_OUT]
        )
        report.net_flow = report.total_income - report.total_expense

        # Average balance
        balances = [t.balance_after for t in transactions if t.balance_after is not None]
        report.avg_balance = sum(balances) / len(balances) if balances else 0

        return report

    def _build_ai_prompt(self, report: AnalysisReport) -> str:
        """Build prompt for AI summary"""
        risk = report.risk_assessment

        prompt = f"""Проанализируй финансовую выписку и дай краткое заключение на русском языке.

ДАННЫЕ:
- Всего транзакций: {report.total_transactions}
- Доход: {report.total_income:,.0f} ₸
- Расход: {report.total_expense:,.0f} ₸
- Баланс: {report.net_flow:,.0f} ₸

ОЦЕНКА РИСКОВ:
- Общий балл: {risk.total_score:.0f}/100 ({risk.risk_level})
- Игры/Ставки: {risk.gaming_gambling.risk_score:.0f}/100
- Отмывание: {risk.money_laundering.risk_score:.0f}/100
- P2P риски: {risk.p2p_analysis.risk_score:.0f}/100

ПРОФИЛЬ:
- Статус: {risk.social_profile.estimated_status}
- Стабильность: {risk.social_profile.financial_stability}

КРАСНЫЕ ФЛАГИ:
{chr(10).join('- ' + f for f in risk.red_flags) if risk.red_flags else '- Не обнаружены'}

Дай:
1. Краткое заключение (2-3 предложения)
2. Главные риски
3. Рекомендации

Будь кратким и конкретным."""

        return prompt

    def _report_to_dict(self, report: AnalysisReport) -> Dict[str, Any]:
        """Convert report to JSON-serializable dict"""

        def serialize(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            if hasattr(obj, 'value'):  # Enum
                return obj.value
            if hasattr(obj, '__dataclass_fields__'):
                return {k: serialize(v) for k, v in asdict(obj).items()}
            if isinstance(obj, list):
                return [serialize(i) for i in obj]
            if isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            return obj

        result = {
            "success": True,
            "analysis_id": report.analysis_id,
            "analysis_date": report.analysis_date.isoformat(),
            "pdf_filename": report.pdf_filename,
            "pdf_hash": report.pdf_hash,
            "period": {
                "start": report.account_period_start.isoformat() if report.account_period_start else None,
                "end": report.account_period_end.isoformat() if report.account_period_end else None
            },
            "summary": {
                "total_transactions": report.total_transactions,
                "total_income": report.total_income,
                "total_expense": report.total_expense,
                "net_flow": report.net_flow,
                "avg_balance": report.avg_balance
            },
            "risk_assessment": {
                "total_score": report.risk_assessment.total_score,
                "risk_level": report.risk_assessment.risk_level,
                "gaming_gambling": {
                    "score": report.risk_assessment.gaming_gambling.risk_score,
                    "level": report.risk_assessment.gaming_gambling.risk_level,
                    "total_amount": report.risk_assessment.gaming_gambling.total_amount,
                    "transactions": report.risk_assessment.gaming_gambling.total_transactions,
                    "platforms": report.risk_assessment.gaming_gambling.platforms_detected,
                    "percentage_of_expenses": report.risk_assessment.gaming_gambling.percentage_of_expenses
                },
                "money_laundering": {
                    "score": report.risk_assessment.money_laundering.risk_score,
                    "level": report.risk_assessment.money_laundering.risk_level,
                    "round_amounts": report.risk_assessment.money_laundering.round_amount_transactions,
                    "split_groups": report.risk_assessment.money_laundering.split_transaction_groups,
                    "transit_ops": report.risk_assessment.money_laundering.transit_operations,
                    "cash_intensity": report.risk_assessment.money_laundering.cash_intensity
                },
                "p2p_analysis": {
                    "score": report.risk_assessment.p2p_analysis.risk_score,
                    "level": report.risk_assessment.p2p_analysis.risk_level,
                    "total_income": report.risk_assessment.p2p_analysis.total_p2p_income,
                    "total_expense": report.risk_assessment.p2p_analysis.total_p2p_expense,
                    "unique_counterparties": report.risk_assessment.p2p_analysis.unique_counterparties,
                    "dependency": report.risk_assessment.p2p_analysis.dependency_on_single_source,
                    "top_counterparties": report.risk_assessment.p2p_analysis.top_counterparties
                },
                "red_flags": report.risk_assessment.red_flags,
                "recommendations": report.risk_assessment.recommendations
            },
            "social_profile": {
                "status": report.risk_assessment.social_profile.estimated_status,
                "confidence": report.risk_assessment.social_profile.confidence,
                "income_sources": report.risk_assessment.social_profile.income_sources,
                "avg_monthly_income": report.risk_assessment.social_profile.avg_monthly_income,
                "avg_monthly_expense": report.risk_assessment.social_profile.avg_monthly_expense,
                "financial_stability": report.risk_assessment.social_profile.financial_stability,
                "subscriptions": report.risk_assessment.social_profile.subscriptions
            },
            "ai_summary": report.ai_summary
        }

        # Add transaction details (limited for JSON size)
        result["transactions"] = [
            {
                "date": t.date.isoformat(),
                "amount": t.amount,
                "type": t.transaction_type.value,
                "category": t.category.value,
                "description": t.anonymized_description or t.description,
                "counterparty": t.anonymized_counterparty or t.counterparty,
                "risk_flags": t.risk_flags
            }
            for t in report.transactions[:100]  # Limit to first 100
        ]

        if len(report.transactions) > 100:
            result["transactions_truncated"] = True
            result["total_transactions_in_pdf"] = len(report.transactions)

        return result


def analyze_pdf_file(pdf_path: str, use_ai: bool = True) -> Dict[str, Any]:
    """Convenience function for PDF analysis"""
    analyzer = FinancialAnalyzer(use_ai=use_ai)
    return analyzer.analyze_pdf(pdf_path)
