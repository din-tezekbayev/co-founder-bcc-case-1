"""Data migration service to load CSV data into PostgreSQL."""

import os
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm

from src.utils.database import db_manager
from sqlalchemy import text

logger = logging.getLogger(__name__)

class DataMigrationService:
    """Service to migrate CSV data to PostgreSQL database."""

    def __init__(self, dataset_path: str = "/app/dataset"):
        self.dataset_path = Path(dataset_path)
        self.session = db_manager.get_session()

    def migrate_all_data(self):
        """Migrate all CSV data to database."""
        logger.info("Starting data migration...")

        try:
            # Clear existing data first
            self.clear_existing_data()

            # Migrate clients data
            self.migrate_clients()

            # Migrate transactions and transfers for all clients
            self.migrate_transactions_and_transfers()

            logger.info("Data migration completed successfully")

        except Exception as e:
            logger.error(f"Data migration failed: {e}")
            self.session.rollback()
            raise
        finally:
            self.session.close()

    def clear_existing_data(self):
        """Clear existing data from tables (except products)."""
        logger.info("Clearing existing data...")

        tables_to_clear = [
            'client_recommendations',
            'product_benefits',
            'client_signals',
            'transfers',
            'transactions',
            'clients'
        ]

        for table in tables_to_clear:
            self.session.execute(text(f"DELETE FROM {table}"))

        self.session.commit()
        logger.info("Existing data cleared")

    def migrate_clients(self):
        """Migrate client profiles from clients.csv."""
        logger.info("Migrating clients data...")

        clients_file = self.dataset_path / "clients.csv"
        if not clients_file.exists():
            raise FileNotFoundError(f"Clients file not found: {clients_file}")

        # Read clients CSV
        df = pd.read_csv(clients_file)

        # Clean column names and data
        df.columns = df.columns.str.strip()

        logger.info(f"Loading {len(df)} clients...")

        # Insert clients in batches
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Inserting clients"):
            try:
                self.session.execute(text("""
                    INSERT INTO clients (client_code, name, status, age, city, avg_monthly_balance_kzt)
                    VALUES (:client_code, :name, :status, :age, :city, :avg_monthly_balance_kzt)
                    """),
                    {
                        'client_code': int(row['client_code']),
                        'name': str(row['name']).strip(),
                        'status': str(row['status']).strip(),
                        'age': int(row['age']),
                        'city': str(row['city']).strip(),
                        'avg_monthly_balance_kzt': float(row['avg_monthly_balance_KZT'])
                    }
                )
            except Exception as e:
                logger.error(f"Error inserting client {row.get('client_code', 'unknown')}: {e}")
                continue

        self.session.commit()
        logger.info("Clients migration completed")

    def migrate_transactions_and_transfers(self):
        """Migrate transactions and transfers for all clients."""
        logger.info("Migrating transactions and transfers...")

        # Get all client files
        transaction_files = list(self.dataset_path.glob("client_*_transactions_3m.csv"))
        transfer_files = list(self.dataset_path.glob("client_*_transfers_3m.csv"))

        logger.info(f"Found {len(transaction_files)} transaction files and {len(transfer_files)} transfer files")

        # Migrate transactions
        for file_path in tqdm(transaction_files, desc="Migrating transaction files"):
            self.migrate_transactions_file(file_path)

        # Migrate transfers
        for file_path in tqdm(transfer_files, desc="Migrating transfer files"):
            self.migrate_transfers_file(file_path)

    def migrate_transactions_file(self, file_path: Path):
        """Migrate transactions from a single CSV file."""
        try:
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip()

            # Convert date column
            df['date'] = pd.to_datetime(df['date'])

            for _, row in df.iterrows():
                try:
                    self.session.execute(text("""
                        INSERT INTO transactions
                        (client_code, name, product, status, city, transaction_date, category, amount, currency)
                        VALUES (:client_code, :name, :product, :status, :city, :transaction_date, :category, :amount, :currency)
                        """),
                        {
                            'client_code': int(row['client_code']),
                            'name': str(row['name']).strip(),
                            'product': str(row.get('product', '')).strip(),
                            'status': str(row.get('status', '')).strip(),
                            'city': str(row.get('city', '')).strip(),
                            'transaction_date': row['date'],
                            'category': str(row['category']).strip(),
                            'amount': float(row['amount']),
                            'currency': str(row.get('currency', 'KZT')).strip()
                        }
                    )
                except Exception as e:
                    logger.warning(f"Error inserting transaction from {file_path.name}: {e}")
                    continue

            self.session.commit()
            logger.debug(f"Completed transactions migration for {file_path.name}")

        except Exception as e:
            logger.error(f"Error migrating transactions file {file_path}: {e}")
            self.session.rollback()

    def migrate_transfers_file(self, file_path: Path):
        """Migrate transfers from a single CSV file."""
        try:
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip()

            # Convert date column
            df['date'] = pd.to_datetime(df['date'])

            for _, row in df.iterrows():
                try:
                    self.session.execute(text("""
                        INSERT INTO transfers
                        (client_code, name, product, status, city, transfer_date, type, direction, amount, currency)
                        VALUES (:client_code, :name, :product, :status, :city, :transfer_date, :type, :direction, :amount, :currency)
                        """),
                        {
                            'client_code': int(row['client_code']),
                            'name': str(row['name']).strip(),
                            'product': str(row.get('product', '')).strip(),
                            'status': str(row.get('status', '')).strip(),
                            'city': str(row.get('city', '')).strip(),
                            'transfer_date': row['date'],
                            'type': str(row['type']).strip(),
                            'direction': str(row['direction']).strip(),
                            'amount': float(row['amount']),
                            'currency': str(row.get('currency', 'KZT')).strip()
                        }
                    )
                except Exception as e:
                    logger.warning(f"Error inserting transfer from {file_path.name}: {e}")
                    continue

            self.session.commit()
            logger.debug(f"Completed transfers migration for {file_path.name}")

        except Exception as e:
            logger.error(f"Error migrating transfers file {file_path}: {e}")
            self.session.rollback()

    def get_migration_stats(self) -> Dict[str, Any]:
        """Get migration statistics."""
        stats = {}

        try:
            # Count records in each table
            tables = ['clients', 'transactions', 'transfers']

            for table in tables:
                result = self.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                stats[table] = result.scalar()

            return stats

        except Exception as e:
            logger.error(f"Error getting migration stats: {e}")
            return {}