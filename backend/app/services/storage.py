"""
AnalysisStorageService — сохранение результатов парсинга и антифрода в БД
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.transaction import Transaction as TransactionModel

logger = logging.getLogger(__name__)


class AnalysisStorageService:
    """Сервис сохранения результатов анализа в БД"""

    def __init__(self, db: Session):
        self.db = db

    def save_analysis(self, result: Dict[str, Any], analyst_id: int,
                      file_name: Optional[str] = None,
                      file_size: Optional[int] = None) -> Analysis:
        """
        Сохранить полный результат анализа BankAnalyzer в БД

        Args:
            result: Результат от BankAnalyzer.analyze()
            analyst_id: ID аналитика
            file_name: Имя загруженного файла
            file_size: Размер файла
        """
        meta = result.get("meta", {})
        account = result.get("account", {})
        summary = result.get("summary", {})
        fraud = result.get("fraud_report")
        detected_bank = meta.get("detected_bank", {})

        # Создаём запись анализа
        analysis = Analysis(
            analyst_id=analyst_id,
            status="completed",
            file_name=file_name or meta.get("pdf_file"),
            file_type="pdf",
            file_size=file_size,

            # Банк
            bank_type=detected_bank.get("type"),
            bank_name=detected_bank.get("name"),
            bank_confidence=detected_bank.get("confidence"),

            # Счёт
            account_owner=account.get("owner"),
            account_number=account.get("account_number"),
            account_currency=account.get("currency", "KZT"),
            balance_start=account.get("balance_start"),
            balance_end=account.get("balance_end"),
            parsed_account_info=account,

            # Период
            period_start=self._parse_date(account.get("period", {}).get("from")),
            period_end=self._parse_date(account.get("period", {}).get("to")),

            # Статистика
            total_transactions=summary.get("total_transactions", 0),
            total_income=summary.get("total_income", 0),
            total_expense=summary.get("total_expense", 0),
            net_flow=summary.get("net_flow", 0),

            # Аналитика
            analytics_result=result.get("analytics"),

            completed_at=datetime.utcnow(),
        )

        # Антифрод
        if fraud:
            analysis.fraud_composite_score = fraud.get("composite_score")
            analysis.fraud_risk_level = fraud.get("risk_level")
            analysis.fraud_report = fraud
            analysis.fraud_red_flags = fraud.get("red_flags")
            analysis.fraud_recommendations = fraud.get("recommendations")
            analysis.risk_score = int(fraud.get("composite_score", 0))

            # Отдельные модули
            analysis.velocity_result = fraud.get("velocity")
            analysis.graph_result = fraud.get("graph")
            analysis.behavioral_result = fraud.get("behavioral")
            analysis.structuring_result = fraud.get("structuring")
            analysis.cross_reference_result = fraud.get("cross_reference")
            analysis.merchant_risk_result = fraud.get("merchant_risk")

        self.db.add(analysis)
        self.db.flush()  # Получить ID

        # Сохраняем транзакции
        transactions = result.get("transactions", [])
        self._save_transactions(transactions, analysis.id, file_name)

        self.db.commit()
        logger.info(f"Сохранён анализ #{analysis.id}: {len(transactions)} транзакций, fraud={fraud.get('risk_level') if fraud else 'N/A'}")

        return analysis

    def _save_transactions(self, transactions: List[Dict], analysis_id: int,
                           file_name: Optional[str] = None) -> None:
        """Bulk insert транзакций"""
        batch = []
        for tx in transactions:
            tx_model = TransactionModel(
                analysis_id=analysis_id,
                amount=tx.get("amount", 0),
                currency=tx.get("currency", "KZT"),
                transaction_type=tx.get("type", "other"),
                transaction_date=self._parse_date(tx.get("date")),
                original_amount=tx.get("original_amount"),
                original_currency=tx.get("original_currency"),
                exchange_rate=tx.get("exchange_rate"),
                counterparty_name=tx.get("counterparty"),
                counterparty_type=tx.get("counterparty_type"),
                description=tx.get("description"),
                category=tx.get("category"),
                subcategory=tx.get("subcategory"),
                merchant_name=tx.get("merchant_name"),
                merchant_type=tx.get("merchant_type"),
                is_blocked=tx.get("is_blocked", False),
                is_deposit_operation=tx.get("is_deposit_operation", False),
                is_pension_benefit=tx.get("is_pension_benefit", False),
                is_bank_transfer=tx.get("is_bank_transfer", False),
                is_atm=tx.get("is_atm", False),
                is_salary=tx.get("is_salary", False),
                is_cash_operation=tx.get("is_cash_operation", False),
                source_file=file_name,
                source_page=tx.get("source_page"),
                source_row=tx.get("source_row"),
                raw_data=tx.get("raw_data"),
            )
            batch.append(tx_model)

        if batch:
            self.db.bulk_save_objects(batch)
            logger.info(f"Сохранено {len(batch)} транзакций для анализа #{analysis_id}")

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Парсинг ISO даты"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            return None

    def get_analysis_with_fraud(self, analysis_id: int) -> Optional[Dict]:
        """Получить анализ с антифрод-отчётом"""
        analysis = self.db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            return None

        return {
            "id": analysis.id,
            "status": analysis.status,
            "bank_type": analysis.bank_type,
            "bank_name": analysis.bank_name,
            "account_owner": analysis.account_owner,
            "total_transactions": analysis.total_transactions,
            "total_income": float(analysis.total_income or 0),
            "total_expense": float(analysis.total_expense or 0),
            "fraud_composite_score": analysis.fraud_composite_score,
            "fraud_risk_level": analysis.fraud_risk_level,
            "fraud_report": analysis.fraud_report,
            "fraud_red_flags": analysis.fraud_red_flags,
            "fraud_recommendations": analysis.fraud_recommendations,
            "analytics_result": analysis.analytics_result,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        }
