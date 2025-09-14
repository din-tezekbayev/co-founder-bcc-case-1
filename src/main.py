"""Main application for banking personalization system."""

import os
import sys
import logging
import time
from pathlib import Path
from typing import List
from tqdm import tqdm

# Add src to Python path
sys.path.append('/app/src')
sys.path.append('/app')

from src.utils.database import db_manager
from src.services.data_migration import DataMigrationService
from src.services.signal_detection import SignalDetectionEngine
from src.services.benefit_calculator import BenefitCalculator
from src.services.recommendation_engine import RecommendationEngine
from src.services.report_generator import ReportGenerator
from src.models.client import Client, Transaction, Transfer, ClientAnalytics
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/logs/application.log', mode='a', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class BankingPersonalizationApp:
    """Main application class for banking personalization system."""

    def __init__(self):
        self.db_manager = db_manager
        self.migration_service = DataMigrationService()
        self.signal_engine = SignalDetectionEngine()
        self.benefit_calculator = BenefitCalculator()
        self.recommendation_engine = RecommendationEngine()
        self.report_generator = ReportGenerator()

    def run_full_pipeline(self):
        """Run the complete personalization pipeline."""
        logger.info("Starting Banking Personalization System")
        start_time = time.time()

        try:
            # Step 1: Test database connection
            if not self.db_manager.test_connection():
                raise Exception("Database connection failed")

            # Step 2: Migrate data
            logger.info("Step 1: Migrating CSV data to database...")
            self.migration_service.migrate_all_data()
            migration_stats = self.migration_service.get_migration_stats()
            logger.info(f"Migration completed: {migration_stats}")

            # Step 3: Process all clients
            logger.info("Step 2: Processing all clients for personalization...")
            self.process_all_clients()

            # Step 4: Generate reports
            logger.info("Step 3: Generating comprehensive reports...")
            report_file = self.report_generator.generate_comprehensive_report()
            debug_dir = self.report_generator.export_debug_data()

            # Step 5: Generate summary statistics
            stats = self.report_generator.generate_summary_stats()
            logger.info("Analysis Summary:")
            logger.info(f"  Total clients: {stats.get('total_clients', 0)}")
            logger.info(f"  Clients with recommendations: {stats.get('clients_with_recommendations', 0)}")
            logger.info(f"  Recommendation rate: {stats.get('recommendation_rate', 0):.1%}")
            logger.info(f"  Average top benefit: {stats.get('average_top_benefit', 0):,.0f} ₸")

            if stats.get('most_recommended_products'):
                logger.info("  Top recommended products:")
                for product, count in stats['most_recommended_products']:
                    logger.info(f"    {product}: {count} clients")

            total_time = time.time() - start_time
            logger.info(f"Pipeline completed successfully in {total_time:.2f} seconds")
            logger.info(f"Reports generated:")
            logger.info(f"  Main report: {report_file}")
            logger.info(f"  Debug data: {debug_dir}")

            return {
                'success': True,
                'report_file': report_file,
                'debug_dir': debug_dir,
                'stats': stats,
                'execution_time': total_time
            }

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }

    def process_all_clients(self):
        """Process all clients for signal detection, benefit calculation, and recommendations."""

        # Get all clients
        session = self.db_manager.get_session()
        try:
            clients_result = session.execute(text("SELECT * FROM clients ORDER BY client_code")).fetchall()
            logger.info(f"Processing {len(clients_result)} clients...")

            for client_row in tqdm(clients_result, desc="Processing clients"):
                try:
                    self.process_single_client(client_row.client_code)
                except Exception as e:
                    logger.error(f"Error processing client {client_row.client_code}: {e}")
                    continue

        finally:
            session.close()

    def process_single_client(self, client_code: int):
        """Process a single client through the complete analysis pipeline."""

        session = self.db_manager.get_session()
        try:
            # Load client data
            client_analytics = self._load_client_analytics(client_code, session)
            if not client_analytics:
                logger.warning(f"No data found for client {client_code}")
                return

            # Step 1: Detect behavioral signals
            signals = self.signal_engine.detect_all_signals(client_analytics)
            self.signal_engine.save_signals(signals)

            # Step 2: Calculate product benefits
            benefits = self.benefit_calculator.calculate_all_benefits(client_analytics)
            self.benefit_calculator.save_benefits(benefits)

            # Step 3: Generate recommendations (top 4 products)
            recommendations = self.recommendation_engine.generate_recommendations(client_code)
            self.recommendation_engine.save_recommendations(recommendations)

            logger.debug(f"Client {client_code} processed: {len(signals)} signals, "
                        f"{len(benefits)} benefits, {len(recommendations)} recommendations")

        except Exception as e:
            logger.error(f"Error in client {client_code} processing pipeline: {e}")
            raise
        finally:
            session.close()

    def _load_client_analytics(self, client_code: int, session) -> ClientAnalytics:
        """Load client data and create ClientAnalytics object."""

        # Load client profile
        client_result = session.execute(text("SELECT * FROM clients WHERE client_code = :client_code"),
            {'client_code': client_code}
        ).fetchone()

        if not client_result:
            return None

        client = Client(
            client_code=client_result.client_code,
            name=client_result.name,
            status=client_result.status,
            age=client_result.age,
            city=client_result.city,
            avg_monthly_balance_kzt=client_result.avg_monthly_balance_kzt
        )

        # Load transactions
        transactions_result = session.execute(text("SELECT * FROM transactions WHERE client_code = :client_code ORDER BY transaction_date"),
            {'client_code': client_code}
        ).fetchall()

        transactions = []
        for tx_row in transactions_result:
            transaction = Transaction(
                client_code=tx_row.client_code,
                name=tx_row.name,
                product=tx_row.product,
                status=tx_row.status,
                city=tx_row.city,
                transaction_date=tx_row.transaction_date,
                category=tx_row.category,
                amount=tx_row.amount,
                currency=tx_row.currency
            )
            transactions.append(transaction)

        # Load transfers
        transfers_result = session.execute(text("SELECT * FROM transfers WHERE client_code = :client_code ORDER BY transfer_date"),
            {'client_code': client_code}
        ).fetchall()

        transfers = []
        for tf_row in transfers_result:
            transfer = Transfer(
                client_code=tf_row.client_code,
                name=tf_row.name,
                product=tf_row.product,
                status=tf_row.status,
                city=tf_row.city,
                transfer_date=tf_row.transfer_date,
                type=tf_row.type,
                direction=tf_row.direction,
                amount=tf_row.amount,
                currency=tf_row.currency
            )
            transfers.append(transfer)

        return ClientAnalytics(client, transactions, transfers)

    def run_single_client_analysis(self, client_code: int):
        """Run analysis for a single client (for testing/debugging)."""
        logger.info(f"Running analysis for client {client_code}")

        try:
            self.process_single_client(client_code)

            # Get and display results
            session = self.db_manager.get_session()
            try:
                # Get client info
                client_result = session.execute(text("SELECT name FROM clients WHERE client_code = :client_code"),
                    {'client_code': client_code}
                ).fetchone()

                logger.info(f"Analysis completed for {client_result.name} (ID: {client_code})")

                # Get signals
                signals_result = session.execute(text("SELECT signal_type, signal_value, signal_strength FROM client_signals WHERE client_code = :client_code"),
                    {'client_code': client_code}
                ).fetchall()

                logger.info(f"Detected {len(signals_result)} behavioral signals:")
                for signal in signals_result:
                    logger.info(f"  {signal.signal_type}: {signal.signal_value:,.0f} ({signal.signal_strength})")

                # Get top recommendations
                recommendations_result = session.execute(text("""
                    SELECT p.name, cr.potential_benefit, cr.recommendation_reason
                    FROM client_recommendations cr
                    JOIN products p ON cr.product_id = p.id
                    WHERE cr.client_code = :client_code
                    ORDER BY cr.rank
                    """),
                    {'client_code': client_code}
                ).fetchall()

                logger.info(f"Top {len(recommendations_result)} product recommendations:")
                for i, rec in enumerate(recommendations_result, 1):
                    logger.info(f"  {i}. {rec.name}: {rec.potential_benefit:,.0f} ₸")
                    logger.info(f"     {rec.recommendation_reason}")

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Single client analysis failed: {e}")
            raise

    def generate_all_push_notifications(self):
        """Generate push notifications for all clients using Azure OpenAI."""
        from src.services.notification_generator import NotificationGenerator

        logger.info("Generating push notifications for all clients...")

        notification_generator = NotificationGenerator()

        try:
            # Get all recommendation records
            session = self.db_manager.get_session()
            recommendations_result = session.execute(text("SELECT id FROM client_recommendations ORDER BY id")).fetchall()

            total_recommendations = len(recommendations_result)
            generated_count = 0

            for recommendation_row in recommendations_result:
                try:
                    recommendation_id = recommendation_row.id
                    success = notification_generator.generate_and_save_notification_by_id(recommendation_id)
                    if success:
                        generated_count += 1
                        logger.info(f"Generated notification for recommendation {recommendation_id}")
                    else:
                        logger.warning(f"Failed to generate notification for recommendation {recommendation_id}")

                except Exception as e:
                    logger.error(f"Error generating notification for recommendation {recommendation_row.id}: {e}")
                    continue

            session.close()
            logger.info(f"Notification generation completed: {generated_count}/{total_recommendations} successful")

        except Exception as e:
            logger.error(f"Error in notification generation pipeline: {e}")
            raise
        finally:
            notification_generator.close()

    def generate_single_push_notification(self, recommendation_id: int):
        """Generate push notification for a single recommendation using Azure OpenAI."""
        from src.services.notification_generator import NotificationGenerator

        logger.info(f"Generating push notification for recommendation {recommendation_id}...")

        notification_generator = NotificationGenerator()

        try:
            success = notification_generator.generate_and_save_notification_by_id(recommendation_id)
            if success:
                logger.info(f"Successfully generated notification for recommendation {recommendation_id}")

                # Display the generated notification
                session = self.db_manager.get_session()
                try:
                    result = session.execute(text("""
                        SELECT c.name, p.name as product_name, cr.push_notification
                        FROM client_recommendations cr
                        JOIN clients c ON cr.client_code = c.client_code
                        JOIN products p ON cr.product_id = p.id
                        WHERE cr.id = :recommendation_id
                    """), {'recommendation_id': recommendation_id}).fetchone()

                    if result:
                        logger.info(f"Generated notification:")
                        logger.info(f"Client: {result.name}")
                        logger.info(f"Product: {result.product_name}")
                        logger.info(f"Notification: {result.push_notification}")

                finally:
                    session.close()
            else:
                logger.error(f"Failed to generate notification for recommendation {recommendation_id}")

        except Exception as e:
            logger.error(f"Error generating notification for recommendation {recommendation_id}: {e}")
            raise
        finally:
            notification_generator.close()

def main():
    """Main entry point."""
    logger.info("Banking Personalization System starting...")

    # Create logs directory
    os.makedirs('/app/logs', exist_ok=True)

    app = BankingPersonalizationApp()

    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "migrate":
            # Just run migration
            app.migration_service.migrate_all_data()
            stats = app.migration_service.get_migration_stats()
            logger.info(f"Migration completed: {stats}")

        elif command == "analyze" and len(sys.argv) > 2:
            # Analyze single client
            client_code = int(sys.argv[2])
            app.run_single_client_analysis(client_code)

        elif command == "report":
            # Just generate reports
            report_file = app.report_generator.generate_comprehensive_report()
            debug_dir = app.report_generator.export_debug_data()
            logger.info(f"Reports generated: {report_file}, {debug_dir}")

        elif command == "generate_notifications":
            # Generate push notifications for all clients
            app.generate_all_push_notifications()

        elif command == "generate_notification" and len(sys.argv) > 2:
            # Generate push notification for single recommendation
            recommendation_id = int(sys.argv[2])
            app.generate_single_push_notification(recommendation_id)

        else:
            logger.info("Usage: python main.py [migrate|analyze <client_code>|report|generate_notifications|generate_notification <recommendation_id>]")

    else:
        # Run full pipeline
        result = app.run_full_pipeline()
        if result['success']:
            logger.info("Application completed successfully")
        else:
            logger.error("Application failed")
            sys.exit(1)

if __name__ == "__main__":
    main()