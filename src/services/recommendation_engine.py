"""Recommendation engine to rank products and generate final recommendations."""

import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal

from src.models.client import ClientRecommendation
from src.utils.database import db_manager
from sqlalchemy import text

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """Engine to rank products and generate final recommendations for clients."""

    def __init__(self):
        self.session = db_manager.get_session()

    def generate_recommendations(self, client_code: int) -> List[ClientRecommendation]:
        """Generate top 4 product recommendations for a client."""

        # Get client info
        client_result = self.session.execute(text("SELECT name FROM clients WHERE client_code = :client_code"),
            {'client_code': client_code}
        ).fetchone()

        if not client_result:
            logger.error(f"Client {client_code} not found")
            return []

        client_name = client_result.name

        # Get current product (if any) from transactions
        current_product = self._get_current_product(client_code)

        # Get all product benefits for this client, ordered by potential benefit
        # Filter out current product if client already uses one
        if current_product:
            benefits_result = self.session.execute(text("""
                SELECT pb.product_id, p.name as product_name, pb.potential_benefit,
                       pb.benefit_type, pb.calculation_details, pb.confidence_score
                FROM product_benefits pb
                JOIN products p ON pb.product_id = p.id
                WHERE pb.client_code = :client_code AND p.name != :current_product
                ORDER BY pb.potential_benefit DESC
                """),
                {'client_code': client_code, 'current_product': current_product}
            ).fetchall()
        else:
            benefits_result = self.session.execute(text("""
                SELECT pb.product_id, p.name as product_name, pb.potential_benefit,
                       pb.benefit_type, pb.calculation_details, pb.confidence_score
                FROM product_benefits pb
                JOIN products p ON pb.product_id = p.id
                WHERE pb.client_code = :client_code
                ORDER BY pb.potential_benefit DESC
                """),
                {'client_code': client_code}
            ).fetchall()

        if not benefits_result:
            logger.warning(f"No benefits calculated for client {client_code}")
            return []

        # If after filtering we have less than 4 products, get additional products (but still exclude current product)
        if len(benefits_result) < 4:
            logger.info(f"Client {client_code} has only {len(benefits_result)} recommendable products after excluding current product '{current_product}'. Looking for additional products to complete top-4.")

            # Get all benefits including current product to find additional options
            all_benefits_result = self.session.execute(text("""
                SELECT pb.product_id, p.name as product_name, pb.potential_benefit,
                       pb.benefit_type, pb.calculation_details, pb.confidence_score
                FROM product_benefits pb
                JOIN products p ON pb.product_id = p.id
                WHERE pb.client_code = :client_code
                ORDER BY pb.potential_benefit DESC
                """),
                {'client_code': client_code}
            ).fetchall()

            # Add products that are not current product and not already in results
            used_products = {row.product_name for row in benefits_result}
            if current_product:
                used_products.add(current_product)  # Exclude current product completely

            for benefit_row in all_benefits_result:
                if benefit_row.product_name not in used_products:
                    benefits_result.append(benefit_row)
                    used_products.add(benefit_row.product_name)
                if len(benefits_result) >= 4:
                    break

        recommendations = []

        # Generate recommendations (up to 4 or as many as available)
        for rank, benefit_row in enumerate(benefits_result[:4], 1):
            # Generate recommendation reason
            reason = self._generate_recommendation_reason(
                benefit_row.product_name,
                benefit_row.benefit_type,
                float(benefit_row.potential_benefit),
                benefit_row.calculation_details
            )

            recommendation = ClientRecommendation(
                client_code=client_code,
                client_name=client_name,
                current_product=current_product,
                rank=rank,
                product_name=benefit_row.product_name,
                potential_benefit=Decimal(str(benefit_row.potential_benefit)),
                recommendation_reason=reason,
                confidence_score=benefit_row.confidence_score
            )

            recommendations.append(recommendation)

        return recommendations

    def _get_current_product(self, client_code: int) -> Optional[str]:
        """Get the current product the client is using (if any)."""
        result = self.session.execute(text("""
            SELECT product FROM transactions
            WHERE client_code = :client_code AND product IS NOT NULL
            ORDER BY transaction_date DESC
            LIMIT 1
            """),
            {'client_code': client_code}
        ).fetchone()

        return result.product if result and result.product else None

    def _generate_recommendation_reason(self, product_name: str, benefit_type: str,
                                      benefit_amount: float, details: Dict) -> str:
        """Generate a human-readable recommendation reason."""

        if product_name == 'Карта для путешествий':
            travel_spending = details.get('travel_spending_3m', 0)
            return f"Экономия {benefit_amount:,.0f} ₸/год на кешбэке с поездок (траты {travel_spending:,.0f} ₸ за 3 мес.)"

        elif product_name == 'Премиальная карта':
            tier = details.get('tier', 'базовый')
            total_cashback = details.get('final_total_cashback', 0)
            return f"Кешбэк {total_cashback:,.0f} ₸/год + экономия на комиссиях (тариф {tier})"

        elif product_name == 'Кредитная карта':
            top_3_categories = details.get('top_3_categories', [])
            categories_str = ', '.join(top_3_categories[:2]) if top_3_categories else 'топ-категории'
            return f"До 10% кешбэк на {categories_str}, экономия {benefit_amount:,.0f} ₸/год"

        elif product_name == 'Обмен валют':
            fx_volume = details.get('annual_fx_volume', 0)
            return f"Экономия {benefit_amount:,.0f} ₸/год на валютных операциях (оборот {fx_volume:,.0f} ₸)"

        elif product_name == 'Кредит наличными':
            loan_amount = details.get('estimated_loan_amount', 0)
            return f"Экономия {benefit_amount:,.0f} ₸/год на процентах (лимит до {loan_amount:,.0f} ₸)"

        elif 'Депозит' in product_name:
            rate = details.get('interest_rate', 0) * 100
            deposit_amount = details.get('deposit_amount', 0)
            return f"Доходность {rate:.1f}% годовых, доход {benefit_amount:,.0f} ₸ с суммы {deposit_amount:,.0f} ₸"

        elif product_name == 'Инвестиции':
            commission_savings = details.get('annual_commission_savings', 0)
            return f"Без комиссий в первый год, экономия {commission_savings:,.0f} ₸ на операциях"

        elif product_name == 'Золотые слитки':
            allocation = details.get('recommended_allocation', 0)
            return f"Защита от инфляции, рекомендуется {allocation:,.0f} ₸ для диверсификации"

        else:
            return f"Потенциальная выгода {benefit_amount:,.0f} ₸ в год"

    def save_recommendations(self, recommendations: List[ClientRecommendation]):
        """Save recommendations to database."""
        try:
            if not recommendations:
                return

            client_code = recommendations[0].client_code

            # Clear existing recommendations for the client
            self.session.execute(text("DELETE FROM client_recommendations WHERE client_code = :client_code"),
                {'client_code': client_code}
            )

            # Insert new recommendations
            for rec in recommendations:
                self.session.execute(text("""
                    INSERT INTO client_recommendations
                    (client_code, product_id, rank, potential_benefit, recommendation_reason)
                    VALUES (:client_code, :product_id, :rank, :potential_benefit, :recommendation_reason)
                    """),
                    {
                        'client_code': rec.client_code,
                        'product_id': self._get_product_id(rec.product_name),
                        'rank': rec.rank,
                        'potential_benefit': float(rec.potential_benefit),
                        'recommendation_reason': rec.recommendation_reason
                    }
                )

            self.session.commit()
            logger.debug(f"Saved {len(recommendations)} recommendations for client {client_code}")

        except Exception as e:
            logger.error(f"Error saving recommendations: {e}")
            self.session.rollback()
            raise

    def _get_product_id(self, product_name: str) -> int:
        """Get product ID by name."""
        result = self.session.execute(text("SELECT id FROM products WHERE name = :name"),
            {'name': product_name}
        ).fetchone()

        if not result:
            raise ValueError(f"Product not found: {product_name}")

        return result.id

    def get_all_recommendations(self) -> List[Dict[str, Any]]:
        """Get all client recommendations for export."""
        result = self.session.execute(text("""
            SELECT c.client_code, c.name,
                   MAX(CASE WHEN cr.rank = 1 THEN p.name END) as top1_product,
                   MAX(CASE WHEN cr.rank = 1 THEN cr.potential_benefit END) as top1_benefit,
                   MAX(CASE WHEN cr.rank = 2 THEN p.name END) as top2_product,
                   MAX(CASE WHEN cr.rank = 2 THEN cr.potential_benefit END) as top2_benefit,
                   MAX(CASE WHEN cr.rank = 3 THEN p.name END) as top3_product,
                   MAX(CASE WHEN cr.rank = 3 THEN cr.potential_benefit END) as top3_benefit,
                   MAX(CASE WHEN cr.rank = 4 THEN p.name END) as top4_product,
                   MAX(CASE WHEN cr.rank = 4 THEN cr.potential_benefit END) as top4_benefit,
                   (SELECT product FROM transactions t WHERE t.client_code = c.client_code
                    AND product IS NOT NULL ORDER BY transaction_date DESC LIMIT 1) as current_product
            FROM clients c
            LEFT JOIN client_recommendations cr ON c.client_code = cr.client_code
            LEFT JOIN products p ON cr.product_id = p.id
            GROUP BY c.client_code, c.name
            ORDER BY c.client_code
            """)).fetchall()

        recommendations = []
        for row in result:
            recommendations.append({
                'client_code': row.client_code,
                'name': row.name,
                'current_product': row.current_product or 'Нет данных',
                'top1_product': row.top1_product or 'Не рассчитано',
                'top1_benefit': row.top1_benefit or 0,
                'top2_product': row.top2_product or 'Не рассчитано',
                'top2_benefit': row.top2_benefit or 0,
                'top3_product': row.top3_product or 'Не рассчитано',
                'top3_benefit': row.top3_benefit or 0,
                'top4_product': row.top4_product or 'Не рассчитано',
                'top4_benefit': row.top4_benefit or 0
            })

        return recommendations

    def close(self):
        """Close database session."""
        self.session.close()