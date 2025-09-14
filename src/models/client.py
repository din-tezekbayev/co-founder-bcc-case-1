"""Client data models and entities."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

@dataclass
class Client:
    """Client profile data."""
    client_code: int
    name: str
    status: str  # Студент / Зарплатный клиент / Премиальный клиент / Стандартный клиент
    age: int
    city: str
    avg_monthly_balance_kzt: Decimal

@dataclass
class Transaction:
    """Transaction record."""
    client_code: int
    name: str
    product: Optional[str]
    status: Optional[str]
    city: Optional[str]
    transaction_date: datetime
    category: str
    amount: Decimal
    currency: str = 'KZT'

@dataclass
class Transfer:
    """Transfer record."""
    client_code: int
    name: str
    product: Optional[str]
    status: Optional[str]
    city: Optional[str]
    transfer_date: datetime
    type: str
    direction: str  # 'in' or 'out'
    amount: Decimal
    currency: str = 'KZT'

@dataclass
class ClientSignal:
    """Detected behavioral signal for a client."""
    client_code: int
    signal_type: str
    signal_value: Decimal
    signal_frequency: int = 0
    signal_strength: str = 'medium'  # low, medium, high

@dataclass
class ProductBenefit:
    """Calculated benefit for a client-product combination."""
    client_code: int
    product_id: int
    product_name: str
    potential_benefit: Decimal
    benefit_type: str
    calculation_details: Dict[str, Any]
    confidence_score: float = 0.5

@dataclass
class ClientRecommendation:
    """Final recommendation for a client."""
    client_code: int
    client_name: str
    current_product: Optional[str]
    rank: int
    product_name: str
    potential_benefit: Decimal
    recommendation_reason: str
    confidence_score: float

class ClientAnalytics:
    """Client analytics and behavioral analysis."""

    def __init__(self, client: Client, transactions: List[Transaction], transfers: List[Transfer]):
        self.client = client
        self.transactions = transactions
        self.transfers = transfers
        self._spending_by_category = None
        self._transfer_patterns = None

    @property
    def total_spending(self) -> Decimal:
        """Total spending amount in KZT."""
        return sum(t.amount for t in self.transactions if t.currency == 'KZT')

    @property
    def spending_by_category(self) -> Dict[str, Decimal]:
        """Spending breakdown by category."""
        if self._spending_by_category is None:
            self._spending_by_category = {}
            for transaction in self.transactions:
                if transaction.currency == 'KZT':
                    category = transaction.category
                    self._spending_by_category[category] = (
                        self._spending_by_category.get(category, Decimal('0')) + transaction.amount
                    )
        return self._spending_by_category

    @property
    def top_spending_categories(self) -> List[tuple]:
        """Top spending categories with amounts."""
        spending = self.spending_by_category
        return sorted(spending.items(), key=lambda x: x[1], reverse=True)

    @property
    def transfer_patterns(self) -> Dict[str, Dict[str, Decimal]]:
        """Transfer patterns by type and direction."""
        if self._transfer_patterns is None:
            self._transfer_patterns = {'in': {}, 'out': {}}
            for transfer in self.transfers:
                if transfer.currency == 'KZT':
                    direction = transfer.direction
                    transfer_type = transfer.type
                    self._transfer_patterns[direction][transfer_type] = (
                        self._transfer_patterns[direction].get(transfer_type, Decimal('0')) + transfer.amount
                    )
        return self._transfer_patterns

    @property
    def foreign_currency_spending(self) -> Decimal:
        """Total spending in foreign currencies (converted to KZT equivalent)."""
        # Simple conversion - in real scenario would use exchange rates
        foreign_spending = Decimal('0')
        for transaction in self.transactions:
            if transaction.currency != 'KZT':
                # Rough conversion rates for estimation
                if transaction.currency == 'USD':
                    foreign_spending += transaction.amount * Decimal('450')
                elif transaction.currency == 'EUR':
                    foreign_spending += transaction.amount * Decimal('500')
                elif transaction.currency == 'RUB':
                    foreign_spending += transaction.amount * Decimal('5')
        return foreign_spending

    @property
    def fx_activity_score(self) -> float:
        """Score indicating FX activity level (0.0 to 1.0)."""
        fx_transfers = ['fx_buy', 'fx_sell']
        fx_volume = sum(
            transfer.amount for transfer in self.transfers
            if transfer.type in fx_transfers and transfer.currency == 'KZT'
        )
        # Normalize by total financial activity
        total_activity = self.total_spending + sum(
            transfer.amount for transfer in self.transfers if transfer.currency == 'KZT'
        )
        if total_activity > 0:
            return min(float(fx_volume / total_activity), 1.0)
        return 0.0

    def has_loan_activity(self) -> bool:
        """Check if client has loan-related transfer activity."""
        loan_types = ['loan_payment_out', 'cc_repayment_out', 'installment_payment_out']
        return any(transfer.type in loan_types for transfer in self.transfers)

    def get_travel_spending(self) -> Decimal:
        """Get spending on travel-related categories."""
        travel_categories = ['Путешествия', 'Отели', 'Такси']
        return sum(
            amount for category, amount in self.spending_by_category.items()
            if category in travel_categories
        )