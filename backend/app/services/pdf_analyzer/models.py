"""
Data models for PDF Financial Analyzer
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum


class TransactionType(Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    P2P_IN = "p2p_in"
    P2P_OUT = "p2p_out"


class TransactionCategory(Enum):
    GAMING_GAMBLING = "gaming_gambling"
    P2P_TRANSFER = "p2p_transfer"
    SALARY_PENSION = "salary_pension"
    UTILITIES = "utilities"
    SHOPPING = "shopping"
    TRANSPORT = "transport"
    FOOD = "food"
    SUBSCRIPTION = "subscription"
    CASH_WITHDRAWAL = "cash_withdrawal"
    CASH_DEPOSIT = "cash_deposit"
    UNKNOWN = "unknown"


@dataclass
class Transaction:
    """Single transaction record"""
    date: datetime
    amount: float
    description: str
    transaction_type: TransactionType
    category: TransactionCategory = TransactionCategory.UNKNOWN
    counterparty: Optional[str] = None
    balance_after: Optional[float] = None
    raw_text: str = ""
    anonymized_description: str = ""
    anonymized_counterparty: str = ""
    risk_flags: List[str] = field(default_factory=list)
    risk_score: float = 0.0


@dataclass
class Counterparty:
    """Counterparty analysis"""
    original_name: str
    anonymized_id: str
    total_transactions: int = 0
    total_income: float = 0.0
    total_expense: float = 0.0
    first_transaction: Optional[datetime] = None
    last_transaction: Optional[datetime] = None
    frequency_per_month: float = 0.0
    relationship_type: str = "unknown"


@dataclass
class GamingGamblingAnalysis:
    """Gaming and Gambling analysis"""
    total_transactions: int = 0
    total_amount: float = 0.0
    platforms_detected: List[str] = field(default_factory=list)
    high_risk_transactions: List[Dict] = field(default_factory=list)
    frequency_per_month: float = 0.0
    percentage_of_expenses: float = 0.0
    risk_score: float = 0.0
    risk_level: str = "low"


@dataclass
class MoneyLaunderingAnalysis:
    """AML analysis"""
    suspicious_patterns: List[Dict[str, Any]] = field(default_factory=list)
    round_amount_transactions: int = 0
    split_transaction_groups: int = 0
    transit_operations: int = 0
    cash_intensity: float = 0.0
    risk_score: float = 0.0
    risk_level: str = "low"


@dataclass
class P2PAnalysis:
    """P2P transfer analysis"""
    total_p2p_income: float = 0.0
    total_p2p_expense: float = 0.0
    unique_counterparties: int = 0
    top_counterparties: List[Dict] = field(default_factory=list)
    dependency_on_single_source: float = 0.0
    suspicious_patterns: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    risk_level: str = "low"


@dataclass
class SocialProfile:
    """Customer social profile"""
    estimated_status: str = "unknown"  # pensioner, student, employed, unemployed, entrepreneur
    confidence: float = 0.0
    has_regular_income: bool = False
    income_sources: List[str] = field(default_factory=list)
    avg_monthly_income: float = 0.0
    avg_monthly_expense: float = 0.0
    main_expense_categories: List[str] = field(default_factory=list)
    subscriptions: List[str] = field(default_factory=list)
    transport_preference: str = "unknown"
    financial_stability: str = "unknown"


@dataclass
class RiskAssessment:
    """Overall risk assessment"""
    total_score: float = 0.0
    risk_level: str = "low"
    gaming_gambling: GamingGamblingAnalysis = field(default_factory=GamingGamblingAnalysis)
    money_laundering: MoneyLaunderingAnalysis = field(default_factory=MoneyLaunderingAnalysis)
    p2p_analysis: P2PAnalysis = field(default_factory=P2PAnalysis)
    social_profile: SocialProfile = field(default_factory=SocialProfile)
    recommendations: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)


@dataclass
class AnalysisReport:
    """Complete analysis report"""
    analysis_id: str = ""
    analysis_date: datetime = field(default_factory=datetime.now)
    pdf_filename: str = ""
    pdf_hash: str = ""
    customer_id: str = "[CUSTOMER_NAME]"
    account_period_start: Optional[datetime] = None
    account_period_end: Optional[datetime] = None
    total_transactions: int = 0
    transactions: List[Transaction] = field(default_factory=list)
    risk_assessment: RiskAssessment = field(default_factory=RiskAssessment)
    counterparties: List[Counterparty] = field(default_factory=list)
    total_income: float = 0.0
    total_expense: float = 0.0
    net_flow: float = 0.0
    avg_balance: float = 0.0
    ai_summary: str = ""
    ai_recommendations: List[str] = field(default_factory=list)
