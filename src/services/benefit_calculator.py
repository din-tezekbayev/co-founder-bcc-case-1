"""Benefit calculation engine for different banking products."""

import logging
from typing import List, Dict, Any, Tuple
from decimal import Decimal
from src.models.client import ClientAnalytics, ProductBenefit
from src.utils.database import db_manager
from sqlalchemy import text
import json

logger = logging.getLogger(__name__)

class BenefitCalculator:
    """Calculate potential benefits for each banking product per client."""

    def __init__(self):
        self.session = db_manager.get_session()
        self.products = self._load_products()

    def _load_products(self) -> Dict[str, Dict]:
        """Load product definitions from database."""
        products = {}
        result = self.session.execute(text("SELECT * FROM products WHERE is_active = true"))

        for row in result:
            products[row.name] = {
                'id': row.id,
                'name': row.name,
                'product_type': row.product_type,
                'base_rate': float(row.base_rate) if row.base_rate else 0.0,
                'cashback_rate': float(row.cashback_rate) if row.cashback_rate else 0.0,
                'monthly_limit': float(row.monthly_limit) if row.monthly_limit else None
            }

        return products

    def calculate_all_benefits(self, analytics: ClientAnalytics) -> List[ProductBenefit]:
        """Calculate benefits for all products for a given client."""
        benefits = []

        # Travel Card Benefits
        travel_benefit = self._calculate_travel_card_benefit(analytics)
        if travel_benefit:
            benefits.append(travel_benefit)

        # Premium Card Benefits
        premium_benefit = self._calculate_premium_card_benefit(analytics)
        if premium_benefit:
            benefits.append(premium_benefit)

        # Credit Card Benefits
        credit_benefit = self._calculate_credit_card_benefit(analytics)
        if credit_benefit:
            benefits.append(credit_benefit)

        # FX Exchange Benefits
        fx_benefit = self._calculate_fx_benefit(analytics)
        if fx_benefit:
            benefits.append(fx_benefit)

        # Cash Loan Benefits
        loan_benefit = self._calculate_loan_benefit(analytics)
        if loan_benefit:
            benefits.append(loan_benefit)

        # Deposit Benefits
        deposit_benefits = self._calculate_deposit_benefits(analytics)
        benefits.extend(deposit_benefits)

        # Investment Benefits
        investment_benefit = self._calculate_investment_benefit(analytics)
        if investment_benefit:
            benefits.append(investment_benefit)

        # Gold Bars Benefits
        gold_benefit = self._calculate_gold_benefit(analytics)
        if gold_benefit:
            benefits.append(gold_benefit)

        return benefits

    def _calculate_travel_card_benefit(self, analytics: ClientAnalytics) -> ProductBenefit:
        """Calculate travel card benefits: 4% cashback on travel/taxi/transport."""
        product = self.products.get('Карта для путешествий')
        if not product:
            return None

        travel_categories = ['Путешествия', 'Отели', 'Такси']
        travel_spending = sum(
            analytics.spending_by_category.get(cat, Decimal('0')) for cat in travel_categories
        )

        if travel_spending == 0:
            return None

        # 4% cashback on travel spending
        annual_benefit = travel_spending * Decimal('0.04') * 4  # Annualized from 3 months

        # Additional benefits from foreign currency savings
        foreign_spending = analytics.foreign_currency_spending
        fx_savings = foreign_spending * Decimal('0.02')  # Assume 2% savings on FX fees

        total_benefit = annual_benefit + fx_savings

        details = {
            'travel_spending_3m': float(travel_spending),
            'annual_travel_spending': float(travel_spending * 4),
            'annual_cashback': float(annual_benefit),
            'fx_savings': float(fx_savings),
            'total_annual_benefit': float(total_benefit)
        }

        confidence = 0.9 if travel_spending > 50000 else 0.7

        return ProductBenefit(
            client_code=analytics.client.client_code,
            product_id=product['id'],
            product_name=product['name'],
            potential_benefit=total_benefit,
            benefit_type='cashback_and_savings',
            calculation_details=details,
            confidence_score=confidence
        )

    def _calculate_premium_card_benefit(self, analytics: ClientAnalytics) -> ProductBenefit:
        """Calculate premium card benefits: tiered cashback + fee savings."""
        product = self.products.get('Премиальная карта')
        if not product:
            return None

        balance = analytics.client.avg_monthly_balance_kzt
        total_spending = analytics.total_spending

        # Determine effective deposit amount (not just balance)
        deposit_operations = analytics.transfer_patterns['out'].get('deposit_topup_out', Decimal('0'))

        # Estimate potential deposit (balance minus living expenses buffer)
        monthly_spending = total_spending / 3 if total_spending > 0 else Decimal('50000')  # Default 50K/month
        buffer = monthly_spending * 2  # 2-month expenses buffer
        potential_deposit = max(balance - buffer, Decimal('0'))

        # Use the maximum of actual deposits or potential deposit
        effective_deposit = max(deposit_operations, potential_deposit)

        # Determine cashback tier based on DEPOSIT amount, not balance
        if effective_deposit >= 6000000:
            base_rate = Decimal('0.04')
            tier = 'депозит 6М+'
        elif effective_deposit >= 1000000:
            base_rate = Decimal('0.03')
            tier = 'депозит 1-6М'
        else:
            base_rate = Decimal('0.02')
            tier = 'базовый'

        # Base cashback calculation
        annual_spending = total_spending * 4  # Annualized
        base_cashback_raw = annual_spending * base_rate

        # Premium categories: 4% on jewelry, cosmetics, restaurants
        premium_categories = ['Кафе и рестораны', 'Косметика и Парфюмерия', 'Ювелирные украшения']
        premium_spending = sum(
            analytics.spending_by_category.get(cat, Decimal('0')) for cat in premium_categories
        )
        premium_cashback_raw = premium_spending * 4 * Decimal('0.04')  # Annualized

        # Apply monthly cashback limit (100K KZT/month = 1.2M KZT/year)
        monthly_limit = Decimal('100000')
        annual_limit = monthly_limit * 12

        # Calculate total cashback before limit
        total_cashback_raw = base_cashback_raw + premium_cashback_raw

        # Apply limit and distribute proportionally if exceeded
        if total_cashback_raw > annual_limit:
            # Proportional distribution when limit is exceeded
            if total_cashback_raw > 0:
                base_share = base_cashback_raw / total_cashback_raw
                premium_share = premium_cashback_raw / total_cashback_raw

                base_cashback = annual_limit * base_share
                premium_cashback = annual_limit * premium_share
            else:
                base_cashback = Decimal('0')
                premium_cashback = Decimal('0')

            total_cashback = annual_limit
            limit_applied = True
        else:
            base_cashback = base_cashback_raw
            premium_cashback = premium_cashback_raw
            total_cashback = total_cashback_raw
            limit_applied = False

        # Fee savings: ATM withdrawals and transfers (not subject to cashback limit)
        atm_volume = analytics.transfer_patterns['out'].get('atm_withdrawal', Decimal('0'))
        atm_savings = min(atm_volume * 4, Decimal('360000'))  # Max 3M KZT/month free withdrawal

        transfer_volume = sum(
            analytics.transfer_patterns['out'].get(t_type, Decimal('0'))
            for t_type in ['p2p_out', 'card_out']
        )
        transfer_savings = transfer_volume * 4 * Decimal('0.01')  # Assume 1% fee saved

        total_benefit = total_cashback + atm_savings + transfer_savings

        details = {
            'account_balance': float(balance),
            'effective_deposit': float(effective_deposit),
            'deposit_operations': float(deposit_operations),
            'potential_deposit': float(potential_deposit),
            'tier': tier,
            'base_rate': float(base_rate),
            'annual_spending': float(annual_spending),
            'premium_spending': float(premium_spending * 4),
            'base_cashback_raw': float(base_cashback_raw),
            'premium_cashback_raw': float(premium_cashback_raw),
            'total_cashback_before_limit': float(total_cashback_raw),
            'annual_cashback_limit': float(annual_limit),
            'limit_applied': limit_applied,
            'final_base_cashback': float(base_cashback),
            'final_premium_cashback': float(premium_cashback),
            'final_total_cashback': float(total_cashback),
            'atm_savings': float(atm_savings),
            'transfer_savings': float(transfer_savings),
            'total_annual_benefit': float(total_benefit)
        }

        confidence = 0.9 if effective_deposit > 1000000 else 0.6

        return ProductBenefit(
            client_code=analytics.client.client_code,
            product_id=product['id'],
            product_name=product['name'],
            potential_benefit=total_benefit,
            benefit_type='cashback_and_savings',
            calculation_details=details,
            confidence_score=confidence
        )

    def _calculate_credit_card_benefit(self, analytics: ClientAnalytics) -> ProductBenefit:
        """Calculate credit card benefits: 10% on top-3 categories + online services."""
        product = self.products.get('Кредитная карта')
        if not product:
            return None

        # Top 3 spending categories
        top_categories = analytics.top_spending_categories[:3]
        if len(top_categories) < 3:
            return None

        top_3_spending = sum(amount for _, amount in top_categories)
        top_3_cashback = top_3_spending * 4 * Decimal('0.10')  # 10% annualized

        # Online services: 10% cashback
        online_categories = ['Смотрим дома', 'Играем дома', 'Кино']
        online_spending = sum(
            analytics.spending_by_category.get(cat, Decimal('0')) for cat in online_categories
        )
        online_cashback = online_spending * 4 * Decimal('0.10')  # Annualized

        # Interest-free period value (2 months)
        monthly_spending = analytics.total_spending / 3
        credit_value = monthly_spending * 2 * Decimal('0.02')  # Assume 2% monthly interest saved

        total_benefit = top_3_cashback + online_cashback + credit_value

        details = {
            'top_3_categories': [cat for cat, _ in top_categories],
            'top_3_spending_3m': float(top_3_spending),
            'top_3_annual_cashback': float(top_3_cashback),
            'online_spending_3m': float(online_spending),
            'online_annual_cashback': float(online_cashback),
            'credit_period_value': float(credit_value),
            'total_annual_benefit': float(total_benefit)
        }

        confidence = 0.8 if top_3_spending > 200000 else 0.6

        return ProductBenefit(
            client_code=analytics.client.client_code,
            product_id=product['id'],
            product_name=product['name'],
            potential_benefit=total_benefit,
            benefit_type='cashback_and_credit',
            calculation_details=details,
            confidence_score=confidence
        )

    def _calculate_fx_benefit(self, analytics: ClientAnalytics) -> ProductBenefit:
        """Calculate FX exchange benefits: spread savings + target rate optimization."""
        product = self.products.get('Обмен валют')
        if not product:
            return None

        # FX volume from transfers
        fx_volume = sum(
            analytics.transfer_patterns['out'].get(fx_type, Decimal('0'))
            for fx_type in ['fx_buy', 'fx_sell']
        )

        # Calculate with minimum FX volume if no actual FX activity
        if fx_volume == 0:
            # Estimate potential FX need from foreign spending
            foreign_spending = analytics.foreign_currency_spending
            if foreign_spending > 0:
                fx_volume = foreign_spending  # Assume need to buy foreign currency
            else:
                fx_volume = Decimal('50000')  # Minimum viable FX volume for calculation

        # Spread savings: assume 1% better rate than market
        spread_savings = fx_volume * 4 * Decimal('0.01')  # Annualized

        # Target rate optimization: assume 0.5% additional benefit
        optimization_value = fx_volume * 4 * Decimal('0.005')

        total_benefit = spread_savings + optimization_value

        details = {
            'fx_volume_3m': float(fx_volume),
            'annual_fx_volume': float(fx_volume * 4),
            'spread_savings': float(spread_savings),
            'optimization_value': float(optimization_value),
            'total_annual_benefit': float(total_benefit)
        }

        confidence = 0.8 if analytics.fx_activity_score > 0.1 else 0.6

        return ProductBenefit(
            client_code=analytics.client.client_code,
            product_id=product['id'],
            product_name=product['name'],
            potential_benefit=total_benefit,
            benefit_type='fx_savings',
            calculation_details=details,
            confidence_score=confidence
        )

    def _calculate_loan_benefit(self, analytics: ClientAnalytics) -> ProductBenefit:
        """Calculate cash loan benefits: interest savings vs alternatives."""
        product = self.products.get('Кредит наличными')
        if not product:
            return None

        # Check if client has cash flow needs
        total_inflows = sum(analytics.transfer_patterns['in'].values())
        total_outflows = sum(analytics.transfer_patterns['out'].values()) + analytics.total_spending

        if total_outflows <= total_inflows:
            return None  # No apparent need for additional cash

        cash_gap = total_outflows - total_inflows
        monthly_gap = cash_gap / 3

        # Estimate loan amount needed
        loan_amount = min(monthly_gap * 6, Decimal('2000000'))  # Max 2M KZT

        if loan_amount < 100000:  # Minimum threshold
            return None

        # Compare with alternative financing costs (assume 25% market rate vs 12-21% bank rate)
        market_rate = Decimal('0.25')
        bank_rate = Decimal('0.12') if loan_amount <= 1000000 else Decimal('0.21')

        annual_savings = loan_amount * (market_rate - bank_rate)

        details = {
            'cash_gap_3m': float(cash_gap),
            'monthly_gap': float(monthly_gap),
            'estimated_loan_amount': float(loan_amount),
            'bank_rate': float(bank_rate),
            'market_rate': float(market_rate),
            'annual_interest_savings': float(annual_savings)
        }

        confidence = 0.7 if cash_gap > 300000 else 0.5

        return ProductBenefit(
            client_code=analytics.client.client_code,
            product_id=product['id'],
            product_name=product['name'],
            potential_benefit=annual_savings,
            benefit_type='interest_savings',
            calculation_details=details,
            confidence_score=confidence
        )

    def _calculate_deposit_benefits(self, analytics: ClientAnalytics) -> List[ProductBenefit]:
        """Calculate benefits for all deposit products."""
        benefits = []

        monthly_spending = analytics.total_spending / 3
        balance = analytics.client.avg_monthly_balance_kzt

        # Available funds for deposits (keep 2-3 months buffer)
        available_funds = balance - (monthly_spending * 2)

        # Calculate with minimum viable deposit amount if client doesn't have enough funds
        if available_funds < 100000:
            available_funds = Decimal('100000')  # Use minimum deposit for calculation

        # Savings Deposit: 16.5%
        savings_product = self.products.get('Депозит Сберегательный (защита KDIF)')
        if savings_product:
            savings_benefit = available_funds * Decimal('0.165')  # Annual interest
            benefits.append(ProductBenefit(
                client_code=analytics.client.client_code,
                product_id=savings_product['id'],
                product_name=savings_product['name'],
                potential_benefit=savings_benefit,
                benefit_type='interest_income',
                calculation_details={
                    'deposit_amount': float(available_funds),
                    'interest_rate': 0.165,
                    'annual_interest': float(savings_benefit)
                },
                confidence_score=0.8
            ))

        # Accumulative Deposit: 15.5%
        accumulative_product = self.products.get('Депозит Накопительный')
        if accumulative_product:
            accumulative_benefit = available_funds * Decimal('0.155')
            benefits.append(ProductBenefit(
                client_code=analytics.client.client_code,
                product_id=accumulative_product['id'],
                product_name=accumulative_product['name'],
                potential_benefit=accumulative_benefit,
                benefit_type='interest_income',
                calculation_details={
                    'deposit_amount': float(available_funds),
                    'interest_rate': 0.155,
                    'annual_interest': float(accumulative_benefit)
                },
                confidence_score=0.7
            ))

        # Multi-currency Deposit: 14.5% (if client has FX activity)
        multicurrency_product = self.products.get('Депозит Мультивалютный (KZT/USD/RUB/EUR)')
        if multicurrency_product and analytics.fx_activity_score > 0.05:
            multicurrency_benefit = available_funds * Decimal('0.145')
            benefits.append(ProductBenefit(
                client_code=analytics.client.client_code,
                product_id=multicurrency_product['id'],
                product_name=multicurrency_product['name'],
                potential_benefit=multicurrency_benefit,
                benefit_type='interest_income',
                calculation_details={
                    'deposit_amount': float(available_funds),
                    'interest_rate': 0.145,
                    'annual_interest': float(multicurrency_benefit),
                    'fx_activity_score': analytics.fx_activity_score
                },
                confidence_score=0.8 if analytics.fx_activity_score > 0.1 else 0.6
            ))

        return benefits

    def _calculate_investment_benefit(self, analytics: ClientAnalytics) -> ProductBenefit:
        """Calculate investment benefits: commission savings + growth potential."""
        product = self.products.get('Инвестиции')
        if not product:
            return None

        monthly_spending = analytics.total_spending / 3
        balance = analytics.client.avg_monthly_balance_kzt

        # Available funds for investment (keep 3 months buffer)
        available_funds = balance - (monthly_spending * 3)

        # Calculate with minimum viable investment amount if client doesn't have enough funds
        if available_funds < 10000:
            available_funds = Decimal('10000')  # Use minimum investment for calculation

        # Commission savings: 0% first year
        estimated_trades_per_year = 12  # Assume monthly rebalancing
        market_commission = Decimal('0.005')  # 0.5% per trade
        commission_savings = available_funds * market_commission * estimated_trades_per_year

        # Conservative growth assumption (not guaranteed)
        potential_growth = available_funds * Decimal('0.08')  # 8% annual growth assumption

        total_benefit = commission_savings  # Only guaranteed benefit

        details = {
            'investment_amount': float(available_funds),
            'annual_commission_savings': float(commission_savings),
            'potential_growth': float(potential_growth),
            'total_guaranteed_benefit': float(total_benefit)
        }

        confidence = 0.6  # Lower confidence due to investment risks

        return ProductBenefit(
            client_code=analytics.client.client_code,
            product_id=product['id'],
            product_name=product['name'],
            potential_benefit=total_benefit,
            benefit_type='commission_savings',
            calculation_details=details,
            confidence_score=confidence
        )

    def _calculate_gold_benefit(self, analytics: ClientAnalytics) -> ProductBenefit:
        """Calculate gold bars benefits: diversification value."""
        product = self.products.get('Золотые слитки')
        if not product:
            return None

        balance = analytics.client.avg_monthly_balance_kzt

        # Calculate with minimum viable allocation even for smaller balances
        if balance < 2000000:
            balance = Decimal('2000000')  # Use minimum threshold for calculation

        # Conservative allocation: 5-10% of liquid assets
        allocation = min(balance * Decimal('0.10'), Decimal('5000000'))

        # Historical gold performance vs inflation
        inflation_protection = allocation * Decimal('0.05')  # 5% annual inflation hedge

        details = {
            'liquid_assets': float(balance),
            'recommended_allocation': float(allocation),
            'inflation_protection_value': float(inflation_protection)
        }

        confidence = 0.5  # Lower confidence due to commodity volatility

        return ProductBenefit(
            client_code=analytics.client.client_code,
            product_id=product['id'],
            product_name=product['name'],
            potential_benefit=inflation_protection,
            benefit_type='inflation_hedge',
            calculation_details=details,
            confidence_score=confidence
        )

    def save_benefits(self, benefits: List[ProductBenefit]):
        """Save calculated benefits to database."""
        try:
            # Clear existing benefits for the client
            if benefits:
                client_code = benefits[0].client_code
                self.session.execute(text("DELETE FROM product_benefits WHERE client_code = :client_code"),
                    {'client_code': client_code}
                )

            # Insert new benefits
            for benefit in benefits:
                self.session.execute(text("""
                    INSERT INTO product_benefits
                    (client_code, product_id, potential_benefit, benefit_type, calculation_details, confidence_score)
                    VALUES (:client_code, :product_id, :potential_benefit, :benefit_type, :calculation_details, :confidence_score)
                    """),
                    {
                        'client_code': benefit.client_code,
                        'product_id': benefit.product_id,
                        'potential_benefit': float(benefit.potential_benefit),
                        'benefit_type': benefit.benefit_type,
                        'calculation_details': json.dumps(benefit.calculation_details),
                        'confidence_score': benefit.confidence_score
                    }
                )

            self.session.commit()

        except Exception as e:
            logger.error(f"Error saving benefits: {e}")
            self.session.rollback()
            raise

    def close(self):
        """Close database session."""
        self.session.close()