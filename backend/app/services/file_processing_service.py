"""
File Processing Service
Сервис для обработки загруженных банковских выписок
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from app.models.analysis import Analysis
from app.models.transaction import Transaction
from app.models.subject import Subject
from app.services.parsers import ParserFactory
from app.services.smart_parser import SmartBankStatementParser
from app.utils.subject_extractor import SubjectExtractor
from app.utils.helpers import (
    generate_subject_identifier,
    is_organization,
    normalize_name
)
import logging

logger = logging.getLogger(__name__)


class FileProcessingService:
    """
    Service for processing uploaded bank statement files
    Парсинг файлов и сохранение транзакций в БД
    """

    def __init__(self, db: Session):
        self.db = db

    def process_file(self, analysis_id: int, file_path: str) -> Dict[str, Any]:
        """
        Process uploaded file: parse and save transactions

        Args:
            analysis_id: ID of the analysis
            file_path: Path to the uploaded file

        Returns:
            Dictionary with processing results

        Raises:
            ValueError: If file cannot be parsed
        """
        # Get analysis from DB
        analysis = self.db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise ValueError(f"Analysis with ID {analysis_id} not found")

        # Update status to parsing
        analysis.status = "parsing"
        self.db.commit()

        try:
            # Determine file type
            file_extension = file_path.split('.')[-1].lower()

            # Use SmartParser for CSV files (ML-powered parsing)
            if file_extension == 'csv':
                logger.info(f"Using SmartBankStatementParser for CSV file: {file_path}")
                smart_result = SmartBankStatementParser.parse_csv(file_path)

                # Create subjects from smart parser results
                subject_id_map = self._create_subjects_from_smart_parser(smart_result)

                # Save transactions with subject IDs
                saved_transactions = self._save_smart_transactions(
                    analysis_id=analysis_id,
                    smart_result=smart_result,
                    subject_id_map=subject_id_map,
                    source_file=analysis.file_name
                )

                logger.info(f"Smart parser created {len(subject_id_map)} subjects and {len(saved_transactions)} transactions")
            else:
                # Use regular parsers for other formats
                logger.info(f"Using ParserFactory for {file_extension} file: {file_path}")
                transactions_data = ParserFactory.parse_file(file_path)

                if not transactions_data:
                    analysis.status = "failed"
                    self.db.commit()
                    raise ValueError("No transactions found in file")

                # Save transactions to database
                saved_transactions = self._save_transactions(
                    analysis_id=analysis_id,
                    transactions_data=transactions_data,
                    source_file=analysis.file_name
                )

                # Auto-generate subjects from transactions
                logger.info(f"Extracting subjects from {len(saved_transactions)} transactions")
                subject_extractor = SubjectExtractor(self.db)
                extracted_subjects = subject_extractor.extract_subjects_from_transactions(
                    transactions=saved_transactions,
                    auto_create=True
                )
                logger.info(f"Extracted {len(extracted_subjects)} subjects")

            # Update analysis statistics
            self._update_analysis_stats(analysis, saved_transactions)

            # Update status to completed
            analysis.status = "completed"
            analysis.completed_at = datetime.utcnow()
            self.db.commit()

            return {
                "success": True,
                "analysis_id": analysis_id,
                "total_transactions": len(saved_transactions),
                "total_amount": sum(t.amount for t in saved_transactions),
                "message": f"Successfully parsed {len(saved_transactions)} transactions"
            }

        except Exception as e:
            # Update status to failed
            analysis.status = "failed"
            self.db.commit()
            raise ValueError(f"Failed to process file: {str(e)}")

    def _save_transactions(
        self,
        analysis_id: int,
        transactions_data: List[Dict[str, Any]],
        source_file: str
    ) -> List[Transaction]:
        """
        Save parsed transactions to database

        Args:
            analysis_id: Analysis ID
            transactions_data: List of transaction dictionaries
            source_file: Source file name

        Returns:
            List of saved Transaction objects
        """
        saved_transactions = []

        for idx, trans_data in enumerate(transactions_data):
            # Create Transaction object
            transaction = Transaction(
                analysis_id=analysis_id,
                subject_id=None,  # Will be set later by auto-generation
                amount=trans_data["amount"],
                currency=trans_data.get("currency", "KZT"),
                transaction_type=trans_data["transaction_type"],
                transaction_date=trans_data["transaction_date"],
                counterparty_name=trans_data.get("counterparty_name"),
                counterparty_account=trans_data.get("counterparty_account"),
                counterparty_bank=trans_data.get("counterparty_bank"),
                counterparty_iin_bin=trans_data.get("counterparty_iin_bin"),
                description=trans_data.get("description"),
                payment_purpose=trans_data.get("payment_purpose"),
                source_file=source_file,
                source_row=idx + 1,
                raw_data=trans_data,  # Save original data for re-analysis
            )

            self.db.add(transaction)
            saved_transactions.append(transaction)

        # Commit all transactions
        self.db.commit()

        # Refresh to get IDs
        for transaction in saved_transactions:
            self.db.refresh(transaction)

        return saved_transactions

    def _create_subjects_from_smart_parser(self, smart_result: Dict[str, Any]) -> Dict[str, int]:
        """
        Create Subject records from smart parser results
        Использует новую систему идентификации БЕЗ ИИН/БИН

        Args:
            smart_result: Result dictionary from SmartBankStatementParser

        Returns:
            Dictionary mapping unique_identifier to Subject ID
        """
        subject_id_map = {}
        subjects_data = smart_result.get('subjects', [])

        logger.info(f"Creating {len(subjects_data)} subjects from smart parser")

        for subject_data in subjects_data:
            iin_bin = subject_data.get('identifier')  # May be None
            name = subject_data.get('name')
            subject_type = subject_data.get('type', 'unknown')

            if not name:
                continue

            # Generate unique identifier using new system
            # Для получателей используем name + type
            unique_identifier = generate_subject_identifier(
                name=name,
                account=None,
                is_account_owner=False
            )

            # Check if subject already exists by unique_identifier
            existing_subject = self.db.query(Subject).filter(
                Subject.unique_identifier == unique_identifier
            ).first()

            if existing_subject:
                subject_id_map[unique_identifier] = existing_subject.id
                logger.info(f"Subject already exists: {name} ({unique_identifier})")
                continue

            # Create new subject
            try:
                # Determine type using is_organization helper
                is_org = is_organization(name)
                db_type = 'legal_entity' if is_org else 'individual'

                new_subject = Subject(
                    unique_identifier=unique_identifier,
                    name=name,
                    type=db_type,
                    iin_bin=iin_bin,  # May be None
                    risk_level=0,
                    status="active"
                )

                self.db.add(new_subject)
                self.db.flush()  # Get ID without committing

                subject_id_map[unique_identifier] = new_subject.id
                logger.info(f"Created subject: {name} ({unique_identifier}) as {db_type}")

            except Exception as e:
                logger.error(f"Failed to create subject {name}: {e}")
                continue

        # Commit all subjects
        self.db.commit()

        return subject_id_map

    def _save_smart_transactions(
        self,
        analysis_id: int,
        smart_result: Dict[str, Any],
        subject_id_map: Dict[str, int],
        source_file: str
    ) -> List[Transaction]:
        """
        Save transactions from smart parser with subject links
        Использует новую систему идентификации БЕЗ ИИН/БИН

        Args:
            analysis_id: Analysis ID
            smart_result: Result from SmartBankStatementParser
            subject_id_map: Mapping of unique_identifier to Subject IDs
            source_file: Source file name

        Returns:
            List of saved Transaction objects
        """
        saved_transactions = []
        transactions_data = smart_result.get('transactions', [])

        logger.info(f"Saving {len(transactions_data)} smart transactions")

        for idx, trans_data in enumerate(transactions_data):
            # Generate unique identifier for counterparty
            counterparty_name = trans_data.get('counterparty_name')
            counterparty_account = trans_data.get('counterparty_account')

            subject_id = None
            if counterparty_name:
                # Generate identifier using new system
                unique_identifier = generate_subject_identifier(
                    name=counterparty_name,
                    account=None,
                    is_account_owner=False
                )

                subject_id = subject_id_map.get(unique_identifier)

            # Create Transaction object
            transaction = Transaction(
                analysis_id=analysis_id,
                subject_id=subject_id,
                amount=trans_data["amount"],
                currency=trans_data.get("currency", "KZT"),
                transaction_type=trans_data["transaction_type"],
                transaction_date=trans_data["transaction_date"],
                counterparty_name=counterparty_name,
                counterparty_account=counterparty_account,
                counterparty_bank=trans_data.get("counterparty_bank"),
                counterparty_iin_bin=trans_data.get("counterparty_iin_bin"),
                description=trans_data.get("description"),
                payment_purpose=trans_data.get("payment_purpose"),
                source_file=source_file,
                source_row=idx + 1,
                raw_data=trans_data,
            )

            self.db.add(transaction)
            saved_transactions.append(transaction)

        # Commit all transactions
        self.db.commit()

        # Refresh to get IDs
        for transaction in saved_transactions:
            self.db.refresh(transaction)

        logger.info(f"Successfully saved {len(saved_transactions)} smart transactions")

        return saved_transactions

    def _update_analysis_stats(self, analysis: Analysis, transactions: List[Transaction]):
        """
        Update analysis statistics based on transactions

        Args:
            analysis: Analysis object
            transactions: List of Transaction objects
        """
        analysis.total_transactions = len(transactions)

        # Calculate total amount (sum of all transactions)
        analysis.total_amount = int(sum(t.amount for t in transactions))

        # Count suspicious and anomalies (will be updated by ML later)
        analysis.suspicious_count = sum(1 for t in transactions if t.is_suspicious)
        analysis.anomaly_count = sum(1 for t in transactions if t.is_anomaly)

        # Count high risk (will be updated by ML later)
        analysis.high_risk_count = sum(1 for t in transactions if t.risk_score >= 70)

        self.db.commit()

    def get_transactions_by_analysis(self, analysis_id: int) -> List[Transaction]:
        """
        Get all transactions for an analysis

        Args:
            analysis_id: Analysis ID

        Returns:
            List of Transaction objects
        """
        return self.db.query(Transaction).filter(
            Transaction.analysis_id == analysis_id
        ).all()

    def get_transaction_stats(self, analysis_id: int) -> Dict[str, Any]:
        """
        Get transaction statistics for an analysis

        Args:
            analysis_id: Analysis ID

        Returns:
            Dictionary with statistics
        """
        transactions = self.get_transactions_by_analysis(analysis_id)

        incoming_count = sum(1 for t in transactions if t.transaction_type == "incoming")
        outgoing_count = sum(1 for t in transactions if t.transaction_type == "outgoing")
        transfer_count = sum(1 for t in transactions if t.transaction_type == "transfer")

        incoming_amount = sum(t.amount for t in transactions if t.transaction_type == "incoming")
        outgoing_amount = sum(t.amount for t in transactions if t.transaction_type == "outgoing")

        return {
            "total_transactions": len(transactions),
            "incoming_count": incoming_count,
            "outgoing_count": outgoing_count,
            "transfer_count": transfer_count,
            "incoming_amount": float(incoming_amount),
            "outgoing_amount": float(outgoing_amount),
            "net_amount": float(incoming_amount - outgoing_amount),
            "avg_transaction_amount": float(sum(t.amount for t in transactions) / len(transactions)) if transactions else 0,
            "suspicious_count": sum(1 for t in transactions if t.is_suspicious),
            "anomaly_count": sum(1 for t in transactions if t.is_anomaly),
        }
