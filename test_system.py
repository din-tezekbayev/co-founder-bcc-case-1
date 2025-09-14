#!/usr/bin/env python3
"""System test script for the banking personalization system."""

import sys
import os

# Add src to path
sys.path.append('/app/src')
sys.path.append('/app')

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from src.utils.database import db_manager
        from src.services.data_migration import DataMigrationService
        from src.services.signal_detection import SignalDetectionEngine
        from src.services.benefit_calculator import BenefitCalculator
        from src.services.recommendation_engine import RecommendationEngine
        from src.services.report_generator import ReportGenerator
        from src.models.client import ClientAnalytics
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_database_connection():
    """Test database connectivity."""
    print("\nTesting database connection...")

    try:
        from src.utils.database import db_manager
        if db_manager.test_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

def test_dataset_files():
    """Test that dataset files exist."""
    print("\nTesting dataset files...")

    dataset_path = "/app/dataset"
    required_files = ["clients.csv"]

    if not os.path.exists(dataset_path):
        print(f"❌ Dataset directory not found: {dataset_path}")
        return False

    files = os.listdir(dataset_path)
    print(f"Found {len(files)} files in dataset")

    # Check for clients.csv
    if "clients.csv" not in files:
        print("❌ clients.csv not found")
        return False

    # Check for transaction and transfer files
    transaction_files = [f for f in files if "_transactions_3m.csv" in f]
    transfer_files = [f for f in files if "_transfers_3m.csv" in f]

    print(f"Found {len(transaction_files)} transaction files")
    print(f"Found {len(transfer_files)} transfer files")

    if len(transaction_files) == 0 or len(transfer_files) == 0:
        print("❌ Missing transaction or transfer files")
        return False

    print("✅ Dataset files validation passed")
    return True

def test_basic_functionality():
    """Test basic system functionality."""
    print("\nTesting basic functionality...")

    try:
        from src.services.data_migration import DataMigrationService
        from src.utils.database import db_manager

        # Test creating services
        migration_service = DataMigrationService()
        print("✅ DataMigrationService created")

        # Test database query
        session = db_manager.get_session()
        from sqlalchemy import text
        result = session.execute(text("SELECT 1 as test")).fetchone()
        session.close()

        if result and result.test == 1:
            print("✅ Database query test passed")
        else:
            print("❌ Database query test failed")
            return False

        return True

    except Exception as e:
        print(f"❌ Basic functionality test error: {e}")
        return False

def main():
    """Run all tests."""
    print("=== Banking Personalization System Tests ===")

    tests = [
        test_imports,
        test_database_connection,
        test_dataset_files,
        test_basic_functionality
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n=== Test Results: {passed}/{total} passed ===")

    if passed == total:
        print("🎉 All tests passed! System is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())