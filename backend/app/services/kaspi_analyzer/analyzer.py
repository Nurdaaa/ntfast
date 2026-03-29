"""
Kaspi Analyzer - Main orchestrator
Combines parsing, categorization, and analytics
"""
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from .parser import KaspiParser
from .categorizer import TransactionCategorizer
from .analytics import FinancialAnalytics

logger = logging.getLogger(__name__)


class KaspiAnalyzer:
    """Main analyzer class that orchestrates all components"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.parser = KaspiParser(pdf_path)
        self.categorizer = TransactionCategorizer()
        self.transactions = []
        self.account = None
        self.validation = None
        self.analytics_engine = None

    def analyze(self) -> Dict[str, Any]:
        """Run full analysis pipeline"""
        logger.info("Starting Kaspi Bank statement analysis...")

        # Step 1: Parse PDF
        logger.info("Step 1: Parsing PDF...")
        self.transactions, self.account, self.validation = self.parser.parse()
        logger.info(f"Parsed {len(self.transactions)} transactions")

        # Step 2: Analyze contacts for categorization
        logger.info("Step 2: Analyzing contacts...")
        self.categorizer.analyze_contacts(self.transactions)

        # Step 3: Categorize transactions
        logger.info("Step 3: Categorizing transactions...")
        categorized = self._categorize_all()

        # Step 4: Calculate analytics
        logger.info("Step 4: Calculating analytics...")
        self.analytics_engine = FinancialAnalytics(self.transactions, self.account)
        self.analytics_engine.set_categorized_transactions(categorized)
        analytics = self.analytics_engine.calculate_all()

        # Step 5: Build final report
        logger.info("Step 5: Building report...")
        report = self._build_report(categorized, analytics)

        logger.info("Analysis complete!")
        return report

    def _categorize_all(self) -> List[Dict[str, Any]]:
        """Categorize all transactions"""
        categorized = []
        for tx in self.transactions:
            category, subcategory = self.categorizer.categorize(tx)
            categorized.append({
                "date": tx.date.isoformat(),
                "amount": tx.amount,
                "type": tx.type,
                "details": tx.details,
                "category": category,
                "subcategory": subcategory,
                "currency": tx.currency,
                "original_amount": tx.original_amount,
                "original_currency": tx.original_currency
            })
        return categorized

    def _build_report(self, categorized: List[Dict], analytics: Dict) -> Dict[str, Any]:
        """Build complete analysis report"""
        return {
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "pdf_file": str(Path(self.pdf_path).name),
                "parser_version": "2.0"
            },
            "account": {
                "owner": self.account.owner,
                "card": self.account.card_number,
                "account_number": self.account.account_number,
                "currency": "KZT",
                "period": {
                    "from": self.account.period_start.isoformat() if self.account.period_start else None,
                    "to": self.account.period_end.isoformat() if self.account.period_end else None
                },
                "balance_start": self.account.balance_start,
                "balance_end": self.account.balance_end
            },
            "validation": self.validation,
            "summary": {
                "total_transactions": len(self.transactions),
                "total_income": analytics["general_stats"]["total_income"],
                "total_expense": analytics["general_stats"]["total_expense"],
                "net_flow": analytics["general_stats"]["net_flow"],
                "avg_daily_expense": analytics["general_stats"]["avg_daily_expense"],
                "median_transaction": analytics["general_stats"]["median_transaction"]
            },
            "transactions": categorized,
            "analytics": {
                "monthly_breakdown": analytics["monthly_breakdown"],
                "category_breakdown": analytics["category_breakdown"],
                "top_merchants": analytics["top_merchants"],
                "top_contacts": analytics["top_contacts"],
                "recurring_payments": analytics["recurring_payments"],
                "anomalies": analytics["anomalies"],
                "foreign_currency": analytics["foreign_currency"],
                "financial_health": analytics["financial_health"],
                "weekday_analysis": analytics["weekday_analysis"],
                "daily_patterns": analytics["daily_patterns"]
            },
            "contacts": self.categorizer.get_contact_stats()
        }

    def export_json(self, output_path: str = None) -> str:
        """Export analysis to JSON file"""
        report = self.analyze()

        if output_path is None:
            output_path = str(Path(self.pdf_path).with_suffix('.json'))

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"Report exported to: {output_path}")
        return output_path


def analyze_kaspi_statement(pdf_path: str) -> Dict[str, Any]:
    """Convenience function to analyze Kaspi statement"""
    analyzer = KaspiAnalyzer(pdf_path)
    return analyzer.analyze()
