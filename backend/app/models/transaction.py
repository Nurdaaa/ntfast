from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Transaction(Base):
    """
    Transaction model for financial transactions
    Расширенная модель: парсинг, ML, антифрод
    """

    __tablename__ = "transactions"

    # Основные поля
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True, index=True)

    # Информация о транзакции
    amount = Column(Numeric(15, 2), nullable=False, index=True)
    currency = Column(String(3), default="KZT")
    transaction_type = Column(String(20), nullable=False, index=True)
    transaction_date = Column(DateTime, nullable=False, index=True)

    # Мультивалютность
    original_amount = Column(Numeric(15, 2), nullable=True)
    original_currency = Column(String(3), nullable=True)
    exchange_rate = Column(Float, nullable=True)

    # Контрагент
    counterparty_name = Column(String(500), nullable=True)
    counterparty_account = Column(String(100), nullable=True)
    counterparty_bank = Column(String(200), nullable=True)
    counterparty_iin_bin = Column(String(12), nullable=True, index=True)
    counterparty_type = Column(String(20), nullable=True)  # person, merchant, bank, atm, government

    # Описание и категория
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    subcategory = Column(String(50), nullable=True)
    payment_purpose = Column(Text, nullable=True)

    # Мерчант
    merchant_name = Column(String(300), nullable=True)
    merchant_type = Column(String(20), nullable=True)  # ИП, ТОО, АО
    merchant_risk_level = Column(String(10), nullable=True)  # low, medium, high

    # Флаги транзакции
    is_blocked = Column(Boolean, default=False)
    is_deposit_operation = Column(Boolean, default=False)
    is_pension_benefit = Column(Boolean, default=False)
    is_bank_transfer = Column(Boolean, default=False)
    is_atm = Column(Boolean, default=False)
    is_salary = Column(Boolean, default=False)
    is_cash_operation = Column(Boolean, default=False)

    # ML анализ и риски
    is_suspicious = Column(Boolean, default=False, index=True)
    is_anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Float, nullable=True)
    risk_score = Column(Integer, default=0)
    risk_factors = Column(JSON, nullable=True)

    # ML метаданные
    ml_features = Column(JSON, nullable=True)
    ml_processed = Column(Boolean, default=False)
    ml_processed_at = Column(DateTime, nullable=True)

    # Источник
    source_file = Column(String(255), nullable=True)
    source_page = Column(Integer, nullable=True)
    source_row = Column(Integer, nullable=True)
    raw_data = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, type='{self.transaction_type}', date='{self.transaction_date}')>"
