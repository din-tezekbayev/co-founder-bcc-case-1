"""Database utilities and connection management."""

import os
import logging
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

Base = declarative_base()

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection and session management."""

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()

    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def execute_query(self, query: str, params: Optional[dict] = None):
        """Execute a raw SQL query."""
        with self.engine.connect() as conn:
            return conn.execute(text(query), params or {})

    def close(self):
        """Close database connection."""
        self.engine.dispose()

# Global database manager instance
db_manager = DatabaseManager()