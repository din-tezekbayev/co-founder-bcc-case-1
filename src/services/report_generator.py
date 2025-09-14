"""Report generation service for CSV output."""

import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any

from src.services.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generate CSV reports with client recommendations and benefits."""

    def __init__(self, output_dir: str = "/app/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive CSV report with all client benefits analysis."""

        recommendation_engine = RecommendationEngine()

        try:
            # Get all recommendations data
            recommendations_data = recommendation_engine.get_all_recommendations()

            if not recommendations_data:
                logger.warning("No recommendations data found")
                return None

            # Generate CSV file
            output_file = self.output_dir / "client_benefits_analysis.csv"

            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'client_code',
                    'name',
                    'current_product',
                    'top1_product',
                    'top1_benefit',
                    'top2_product',
                    'top2_benefit',
                    'top3_product',
                    'top3_benefit',
                    'top4_product',
                    'top4_benefit'
                ]

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Write header
                writer.writeheader()

                # Write data
                for row in recommendations_data:
                    # Format benefit amounts
                    for i in range(1, 5):
                        benefit_key = f'top{i}_benefit'
                        if row[benefit_key]:
                            row[benefit_key] = f"{row[benefit_key]:,.0f} ₸"
                        else:
                            row[benefit_key] = "0 ₸"

                    writer.writerow(row)

            logger.info(f"Generated comprehensive report: {output_file}")
            logger.info(f"Total clients processed: {len(recommendations_data)}")

            return str(output_file)

        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            raise
        finally:
            recommendation_engine.close()

    def generate_summary_stats(self) -> Dict[str, Any]:
        """Generate summary statistics for the analysis."""

        recommendation_engine = RecommendationEngine()

        try:
            # Get all recommendations
            recommendations_data = recommendation_engine.get_all_recommendations()

            if not recommendations_data:
                return {}

            # Calculate statistics
            total_clients = len(recommendations_data)
            clients_with_recommendations = sum(
                1 for row in recommendations_data
                if row['top1_product'] != 'Не рассчитано'
            )

            # Product recommendation frequency
            product_frequency = {}
            for row in recommendations_data:
                for i in range(1, 5):
                    product = row[f'top{i}_product']
                    if product and product != 'Не рассчитано':
                        product_frequency[product] = product_frequency.get(product, 0) + 1

            # Average benefits
            total_benefits = []
            for row in recommendations_data:
                if row['top1_benefit']:
                    try:
                        benefit_value = float(str(row['top1_benefit']).replace(' ₸', '').replace(',', ''))
                        total_benefits.append(benefit_value)
                    except (ValueError, AttributeError):
                        continue

            avg_benefit = sum(total_benefits) / len(total_benefits) if total_benefits else 0

            stats = {
                'total_clients': total_clients,
                'clients_with_recommendations': clients_with_recommendations,
                'recommendation_rate': clients_with_recommendations / total_clients if total_clients > 0 else 0,
                'most_recommended_products': sorted(product_frequency.items(), key=lambda x: x[1], reverse=True)[:5],
                'average_top_benefit': avg_benefit,
                'total_potential_benefit': sum(total_benefits)
            }

            return stats

        except Exception as e:
            logger.error(f"Error generating summary stats: {e}")
            return {}
        finally:
            recommendation_engine.close()

    def export_debug_data(self) -> str:
        """Export detailed debug data for analysis."""
        from src.utils.database import db_manager
        from sqlalchemy import text

        session = db_manager.get_session()

        try:
            # Export signals data
            signals_file = self.output_dir / "client_signals_debug.csv"
            signals_result = session.execute(text("""
                SELECT cs.client_code, c.name, cs.signal_type, cs.signal_value,
                       cs.signal_frequency, cs.signal_strength
                FROM client_signals cs
                JOIN clients c ON cs.client_code = c.client_code
                ORDER BY cs.client_code, cs.signal_type
                """)).fetchall()

            with open(signals_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['client_code', 'name', 'signal_type', 'signal_value',
                               'signal_frequency', 'signal_strength'])

                for row in signals_result:
                    writer.writerow([
                        row.client_code, row.name, row.signal_type, f"{row.signal_value:,.2f}",
                        row.signal_frequency, row.signal_strength
                    ])

            # Export benefits data
            benefits_file = self.output_dir / "product_benefits_debug.csv"
            benefits_result = session.execute(text("""
                SELECT pb.client_code, c.name, p.name as product_name,
                       pb.potential_benefit, pb.benefit_type, pb.confidence_score
                FROM product_benefits pb
                JOIN clients c ON pb.client_code = c.client_code
                JOIN products p ON pb.product_id = p.id
                ORDER BY pb.client_code, pb.potential_benefit DESC
                """)).fetchall()

            with open(benefits_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['client_code', 'name', 'product_name', 'potential_benefit',
                               'benefit_type', 'confidence_score'])

                for row in benefits_result:
                    writer.writerow([
                        row.client_code, row.name, row.product_name, f"{row.potential_benefit:,.2f} ₸",
                        row.benefit_type, f"{row.confidence_score:.2f}"
                    ])

            logger.info(f"Exported debug data: {signals_file}, {benefits_file}")
            return str(self.output_dir)

        except Exception as e:
            logger.error(f"Error exporting debug data: {e}")
            raise
        finally:
            session.close()