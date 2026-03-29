"""
Data Anonymizer - Replaces personal data with tags on-the-fly
"""
import re
from typing import Dict, List, Set
from dataclasses import dataclass, field

from .models import Transaction, Counterparty


@dataclass
class AnonymizationMap:
    """Tracks anonymization mappings"""
    customer_name: str = ""
    customer_tag: str = "[CUSTOMER_NAME]"
    counterparties: Dict[str, str] = field(default_factory=dict)
    phones: Dict[str, str] = field(default_factory=dict)
    iins: Dict[str, str] = field(default_factory=dict)
    cards: Dict[str, str] = field(default_factory=dict)
    accounts: Dict[str, str] = field(default_factory=dict)
    _counterparty_counter: int = 0
    _phone_counter: int = 0
    _iin_counter: int = 0
    _card_counter: int = 0
    _account_counter: int = 0


class DataAnonymizer:
    """Anonymizes personal data in financial transactions"""

    # Regex patterns for personal data
    IIN_PATTERN = re.compile(r'\b\d{12}\b')  # Kazakhstan IIN
    PHONE_PATTERN = re.compile(r'\+?7[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}')
    CARD_PATTERN = re.compile(r'\b\d{4}[\s*]{0,3}\d{4}[\s*]{0,3}\d{4}[\s*]{0,3}\d{4}\b')
    ACCOUNT_PATTERN = re.compile(r'\bKZ\d{2}[A-Z0-9]{16}\b')

    def __init__(self, customer_name: str = None):
        self.anon_map = AnonymizationMap()
        self.name_variations: Set[str] = set()

        if customer_name:
            self.anon_map.customer_name = customer_name
            self._add_name_variations(customer_name)

    def _add_name_variations(self, full_name: str):
        """Generate name variations for matching"""
        parts = full_name.split()
        self.name_variations = {full_name, full_name.upper(), full_name.lower()}

        if len(parts) >= 2:
            self.name_variations.add(f"{parts[0]} {parts[1][0]}.")
            self.name_variations.add(f"{parts[1]} {parts[0][0]}.")
            self.name_variations.add(parts[0])
            self.name_variations.add(f"{parts[0]} {parts[1]}")

        if len(parts) >= 3:
            self.name_variations.add(f"{parts[0]} {parts[1]} {parts[2]}")
            self.name_variations.add(f"{parts[0]} {parts[1][0]}. {parts[2][0]}.")

    def anonymize_text(self, text: str) -> str:
        """Anonymize all personal data in text"""
        if not text:
            return text

        result = text

        # Replace customer name variations (only full matches, not partial words)
        if self.anon_map.customer_name:
            for variation in sorted(self.name_variations, key=len, reverse=True):
                # Skip single-character or very short variations
                if len(variation) < 3:
                    continue
                # Use word boundaries to avoid replacing parts of words
                pattern = re.compile(r'\b' + re.escape(variation) + r'\b', re.IGNORECASE)
                result = pattern.sub("[CUSTOMER_NAME]", result)

        # Replace IINs
        result = self._anonymize_pattern(result, self.IIN_PATTERN, self.anon_map.iins, "IIN")

        # Replace phones
        result = self._anonymize_pattern(result, self.PHONE_PATTERN, self.anon_map.phones, "PHONE")

        # Replace cards
        result = self._anonymize_pattern(result, self.CARD_PATTERN, self.anon_map.cards, "CARD")

        # Replace accounts
        result = self._anonymize_pattern(result, self.ACCOUNT_PATTERN, self.anon_map.accounts, "ACCOUNT")

        return result

    def _anonymize_pattern(self, text: str, pattern: re.Pattern, mapping: Dict[str, str], tag_prefix: str) -> str:
        """Replace pattern matches with tags"""
        counter = len(mapping)

        def replace(match):
            nonlocal counter
            original = match.group(0)
            normalized = re.sub(r'\s+', '', original).upper()

            if normalized not in mapping:
                counter += 1
                mapping[normalized] = f"[{tag_prefix}_{counter}]"

            return mapping[normalized]

        return pattern.sub(replace, text)

    def anonymize_counterparty(self, name: str) -> str:
        """Anonymize counterparty name"""
        if not name:
            return ""

        normalized = name.strip().upper()

        # Check if it's the customer
        if self.anon_map.customer_name:
            if normalized == self.anon_map.customer_name.upper() or any(
                v.upper() == normalized for v in self.name_variations
            ):
                return "[CUSTOMER_NAME]"

        # Assign counterparty ID
        if normalized not in self.anon_map.counterparties:
            self.anon_map._counterparty_counter += 1
            self.anon_map.counterparties[normalized] = f"[COUNTERPARTY_{self.anon_map._counterparty_counter}]"

        return self.anon_map.counterparties[normalized]

    def anonymize_transaction(self, transaction: Transaction) -> Transaction:
        """Anonymize a single transaction"""
        transaction.anonymized_description = self.anonymize_text(transaction.description)

        if transaction.counterparty:
            transaction.anonymized_counterparty = self.anonymize_counterparty(transaction.counterparty)

        return transaction

    def anonymize_transactions(self, transactions: List[Transaction]) -> List[Transaction]:
        """Anonymize all transactions"""
        return [self.anonymize_transaction(t) for t in transactions]

    def get_counterparty_mapping(self) -> Dict[str, str]:
        """Get reverse mapping (tag -> original)"""
        return {v: k for k, v in self.anon_map.counterparties.items()}

    def create_anonymized_counterparties(self) -> List[Counterparty]:
        """Create anonymized counterparty list"""
        return [
            Counterparty(original_name=orig, anonymized_id=tag)
            for orig, tag in self.anon_map.counterparties.items()
        ]

    def get_anonymization_report(self) -> Dict:
        """Generate anonymization report"""
        return {
            "customer_name": {
                "original": self.anon_map.customer_name,
                "tag": "[CUSTOMER_NAME]"
            },
            "counterparties_count": len(self.anon_map.counterparties),
            "phones_count": len(self.anon_map.phones),
            "iins_count": len(self.anon_map.iins),
            "cards_count": len(self.anon_map.cards),
            "accounts_count": len(self.anon_map.accounts),
            "counterparty_tags": list(self.anon_map.counterparties.values())
        }
