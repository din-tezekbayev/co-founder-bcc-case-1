"""Signal detection engine for identifying client behavioral patterns."""

import logging
from typing import List, Dict, Any
from decimal import Decimal
from collections import defaultdict

from src.models.client import ClientAnalytics, ClientSignal
from src.utils.database import db_manager
from sqlalchemy import text

logger = logging.getLogger(__name__)

class SignalDetectionEngine:
    """Engine to detect behavioral signals for product recommendations."""

    def __init__(self):
        self.session = db_manager.get_session()

    def detect_all_signals(self, client_analytics: ClientAnalytics) -> List[ClientSignal]:
        """Detect all relevant signals for a client."""
        signals = []

        # Travel Card Signals
        signals.extend(self._detect_travel_signals(client_analytics))

        # Premium Card Signals
        signals.extend(self._detect_premium_signals(client_analytics))

        # Credit Card Signals
        signals.extend(self._detect_credit_signals(client_analytics))

        # FX Exchange Signals
        signals.extend(self._detect_fx_signals(client_analytics))

        # Cash Loan Signals
        signals.extend(self._detect_loan_signals(client_analytics))

        # Deposit Signals
        signals.extend(self._detect_deposit_signals(client_analytics))

        # Investment Signals
        signals.extend(self._detect_investment_signals(client_analytics))

        # Gold Bars Signals
        signals.extend(self._detect_gold_signals(client_analytics))

        return signals

    def _detect_travel_signals(self, analytics: ClientAnalytics) -> List[ClientSignal]:
        """Detect travel-related behavioral signals."""
        signals = []

        # Travel spending signal
        travel_categories = ['Путешествия', 'Отели', 'Такси']
        travel_spending = sum(
            analytics.spending_by_category.get(cat, Decimal('0')) for cat in travel_categories
        )

        if travel_spending > 0:
            # Determine signal strength
            monthly_travel = travel_spending / 3  # 3 months of data
            strength = 'low'
            if monthly_travel > 50000:  # 50k KZT per month
                strength = 'high'
            elif monthly_travel > 20000:  # 20k KZT per month
                strength = 'medium'

            signals.append(ClientSignal(
                client_code=analytics.client.client_code,
                signal_type='travel_spending',
                signal_value=travel_spending,
                signal_frequency=len([t for t in analytics.transactions if t.category in travel_categories]),
                signal_strength=strength
            ))

        # Foreign currency spending signal
        foreign_spending = analytics.foreign_currency_spending
        if foreign_spending > 0:
            signals.append(ClientSignal(
                client_code=analytics.client.client_code,
                signal_type='foreign_currency_spending',
                signal_value=foreign_spending,
                signal_frequency=len([t for t in analytics.transactions if t.currency != 'KZT']),
                signal_strength='high' if foreign_spending > 100000 else 'medium'
            ))

        return signals

    def _detect_premium_signals(self, analytics: ClientAnalytics) -> List[ClientSignal]:
        """Detect premium card behavioral signals."""
        signals = []

        # High balance signal
        balance = analytics.client.avg_monthly_balance_kzt
        if balance > 1000000:  # 1M KZT threshold for premium features
            strength = 'high' if balance > 6000000 else 'medium'
            signals.append(ClientSignal(
                client_code=analytics.client.client_code,
                signal_type='high_balance',
                signal_value=balance,
                signal_frequency=1,
                signal_strength=strength
            ))

        # Premium categories spending
        premium_categories = ['Кафе и рестораны', 'Косметика и Парфюмерия', 'Ювелирные украшения']
        premium_spending = sum(
            analytics.spending_by_category.get(cat, Decimal('0')) for cat in premium_categories
        )

        if premium_spending > 0:
            signals.append(ClientSignal(
                client_code=analytics.client.client_code,
                signal_type='premium_categories_spending',
                signal_value=premium_spending,
                signal_frequency=len([t for t in analytics.transactions if t.category in premium_categories]),
                signal_strength='high' if premium_spending > 200000 else 'medium'
            ))

        # ATM and transfer activity
        atm_transfers = analytics.transfer_patterns['out'].get('atm_withdrawal', Decimal('0'))
        if atm_transfers > 0:
            signals.append(ClientSignal(
                client_code=analytics.client.client_code,
                signal_type='frequent_atm_usage',
                signal_value=atm_transfers,
                signal_frequency=len([t for t in analytics.transfers if t.type == 'atm_withdrawal']),
                signal_strength='high' if atm_transfers > 500000 else 'medium'
            ))

        return signals

    def _detect_credit_signals(self, analytics: ClientAnalytics) -> List[ClientSignal]:
        """Detect credit card behavioral signals."""
        signals = []

        # Top spending categories (for 10% cashback optimization)
        top_categories = analytics.top_spending_categories[:3]
        if len(top_categories) >= 3:
            top_3_total = sum(amount for _, amount in top_categories)
            signals.append(ClientSignal(
                client_code=analytics.client.client_code,
                signal_type='top_3_categories_spending',
                signal_value=top_3_total,
                signal_frequency=len(top_categories),
                signal_strength='high' if top_3_total > 300000 else 'medium'
            ))

        # Online services spending
        online_categories = ['Смотрим дома', 'Играем дома', 'Кино']
        online_spending = sum(
            analytics.spending_by_category.get(cat, Decimal('0')) for cat in online_categories
        )

        if online_spending > 0:
            signals.append(ClientSignal(
                client_code=analytics.client.client_code,
                signal_type='online_services_spending',
                signal_value=online_spending,
                signal_frequency=len([t for t in analytics.transactions if t.category in online_categories]),
                signal_strength='high' if online_spending > 100000 else 'medium'
            ))

        # Existing credit activity
        if analytics.has_loan_activity():
            loan_payments = (
                analytics.transfer_patterns['out'].get('cc_repayment_out', Decimal('0')) +
                analytics.transfer_patterns['out'].get('installment_payment_out', Decimal('0'))
            )
            signals.append(ClientSignal(
                client_code=analytics.client.client_code,
                signal_type='existing_credit_usage',
                signal_value=loan_payments,
                signal_frequency=len([t for t in analytics.transfers if 'repayment' in t.type or 'installment' in t.type]),
                signal_strength='high'
            ))

        return signals

    def _detect_fx_signals(self, analytics: ClientAnalytics) -> List[ClientSignal]:
        """Detect FX exchange behavioral signals."""
        signals = []

        # FX trading activity
        fx_activity = analytics.fx_activity_score
        if fx_activity > 0:
            fx_volume = sum(
                analytics.transfer_patterns['out'].get(fx_type, Decimal('0'))
                for fx_type in ['fx_buy', 'fx_sell']
            )

            signals.append(ClientSignal(
                client_code=analytics.client.client_code,
                signal_type='fx_trading_activity',
                signal_value=fx_volume,
                signal_frequency=len([t for t in analytics.transfers if t.type in ['fx_buy', 'fx_sell']]),
                signal_strength='high' if fx_activity > 0.1 else 'medium'
            ))

        # Regular foreign spending
        foreign_spending = analytics.foreign_currency_spending
        if foreign_spending > 0:
            signals.append(ClientSignal(
                client_code=analytics.client.client_code,
                signal_type='regular_foreign_spending',
                signal_value=foreign_spending,
                signal_frequency=len([t for t in analytics.transactions if t.currency != 'KZT']),
                signal_strength='high' if foreign_spending > 200000 else 'medium'
            ))

        return signals

    def _detect_loan_signals(self, analytics: ClientAnalytics) -> List[ClientSignal]:
        """Detect cash loan need signals."""
        signals = []

        # Cash flow analysis
        total_inflows = sum(analytics.transfer_patterns['in'].values())
        total_outflows = sum(analytics.transfer_patterns['out'].values()) + analytics.total_spending

        if total_outflows > total_inflows:
            cash_gap = total_outflows - total_inflows
            signals.append(ClientSignal(
                client_code=analytics.client.client_code,
                signal_type='cash_flow_gap',
                signal_value=cash_gap,
                signal_frequency=1,
                signal_strength='high' if cash_gap > 500000 else 'medium'
            ))

        # Low balance relative to spending
        monthly_spending = analytics.total_spending / 3  # 3 months of data
        balance_ratio = float(analytics.client.avg_monthly_balance_kzt / monthly_spending) if monthly_spending > 0 else 10

        if balance_ratio < 2:  # Less than 2 months of spending in balance
            signals.append(ClientSignal(
                client_code=analytics.client.client_code,
                signal_type='low_balance_ratio',
                signal_value=Decimal(str(balance_ratio)),
                signal_frequency=1,
                signal_strength='high' if balance_ratio < 1 else 'medium'
            ))

        return signals

    def _detect_deposit_signals(self, analytics: ClientAnalytics) -> List[ClientSignal]:
        """Detect deposit product signals."""
        signals = []

        # Available funds for deposits
        monthly_spending = analytics.total_spending / 3
        available_funds = analytics.client.avg_monthly_balance_kzt - (monthly_spending * 2)  # Keep 2 months buffer

        if available_funds > 100000:  # Minimum deposit threshold
            # Determine deposit type based on behavior
            spending_volatility = self._calculate_spending_volatility(analytics)

            if spending_volatility < 0.3:  # Low volatility = stable income
                signals.append(ClientSignal(
                    client_code=analytics.client.client_code,
                    signal_type='savings_deposit_candidate',
                    signal_value=available_funds,
                    signal_frequency=1,
                    signal_strength='high' if available_funds > 1000000 else 'medium'
                ))
            else:
                signals.append(ClientSignal(
                    client_code=analytics.client.client_code,
                    signal_type='accumulative_deposit_candidate',
                    signal_value=available_funds,
                    signal_frequency=1,
                    signal_strength='medium'
                ))

        # Multi-currency deposit signals
        if analytics.fx_activity_score > 0.05 and available_funds > 500000:
            signals.append(ClientSignal(
                client_code=analytics.client.client_code,
                signal_type='multicurrency_deposit_candidate',
                signal_value=available_funds,
                signal_frequency=1,
                signal_strength='high' if analytics.fx_activity_score > 0.1 else 'medium'
            ))

        return signals

    def _detect_investment_signals(self, analytics: ClientAnalytics) -> List[ClientSignal]:
        """Detect investment product signals."""
        signals = []

        # Free funds available for investment
        monthly_spending = analytics.total_spending / 3
        available_funds = analytics.client.avg_monthly_balance_kzt - (monthly_spending * 3)  # Keep 3 months buffer

        if available_funds > 10000:  # Low threshold for investments
            # Check for existing investment activity
            investment_activity = (
                analytics.transfer_patterns['out'].get('invest_out', Decimal('0')) +
                analytics.transfer_patterns['in'].get('invest_in', Decimal('0'))
            )

            strength = 'high' if investment_activity > 0 else 'medium'
            signals.append(ClientSignal(
                client_code=analytics.client.client_code,
                signal_type='investment_candidate',
                signal_value=available_funds,
                signal_frequency=1 if investment_activity > 0 else 0,
                signal_strength=strength
            ))

        return signals

    def _detect_gold_signals(self, analytics: ClientAnalytics) -> List[ClientSignal]:
        """Detect gold bars investment signals."""
        signals = []

        # High liquidity with diversification interest
        if analytics.client.avg_monthly_balance_kzt > 2000000:  # High liquidity threshold
            # Check for luxury/jewelry spending
            luxury_spending = analytics.spending_by_category.get('Ювелирные украшения', Decimal('0'))

            if luxury_spending > 0 or analytics.client.avg_monthly_balance_kzt > 5000000:
                signals.append(ClientSignal(
                    client_code=analytics.client.client_code,
                    signal_type='gold_investment_candidate',
                    signal_value=analytics.client.avg_monthly_balance_kzt,
                    signal_frequency=1,
                    signal_strength='high' if luxury_spending > 0 else 'medium'
                ))

        return signals

    def _calculate_spending_volatility(self, analytics: ClientAnalytics) -> float:
        """Calculate spending volatility over the period."""
        # Group transactions by month and calculate variance
        monthly_spending = defaultdict(Decimal)

        for transaction in analytics.transactions:
            month_key = transaction.transaction_date.strftime('%Y-%m')
            monthly_spending[month_key] += transaction.amount

        if len(monthly_spending) < 2:
            return 0.0

        amounts = list(monthly_spending.values())
        mean_spending = sum(amounts) / len(amounts)

        if mean_spending == 0:
            return 0.0

        variance = sum((amount - mean_spending) ** 2 for amount in amounts) / len(amounts)
        std_dev = float(variance ** Decimal('0.5'))

        return std_dev / float(mean_spending)  # Coefficient of variation

    def save_signals(self, signals: List[ClientSignal]):
        """Save detected signals to database."""
        try:
            # Clear existing signals for the client
            if signals:
                client_code = signals[0].client_code
                self.session.execute(text("DELETE FROM client_signals WHERE client_code = :client_code"),
                    {'client_code': client_code}
                )

            # Insert new signals
            for signal in signals:
                self.session.execute(text("""
                    INSERT INTO client_signals (client_code, signal_type, signal_value, signal_frequency, signal_strength)
                    VALUES (:client_code, :signal_type, :signal_value, :signal_frequency, :signal_strength)
                    """),
                    {
                        'client_code': signal.client_code,
                        'signal_type': signal.signal_type,
                        'signal_value': float(signal.signal_value),
                        'signal_frequency': signal.signal_frequency,
                        'signal_strength': signal.signal_strength
                    }
                )

            self.session.commit()

        except Exception as e:
            logger.error(f"Error saving signals: {e}")
            self.session.rollback()
            raise

    def close(self):
        """Close database session."""
        self.session.close()