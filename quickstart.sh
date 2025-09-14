#!/bin/bash

# Banking Personalization System - Quick Start Script

echo "🏦 Banking Personalization System - Quick Start"
echo "=============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your Azure OpenAI credentials before running analysis"
fi

echo "🚀 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "📊 Checking service status..."
docker-compose ps

# Test system
echo "🔬 Running system tests..."
docker-compose exec -T app python test_system.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 System is ready!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Access Adminer at: http://localhost:8080"
    echo "   - Server: postgres"
    echo "   - Username: banking_user"
    echo "   - Password: banking_pass"
    echo "   - Database: banking_personalization"
    echo ""
    echo "2. Run the analysis:"
    echo "   docker-compose exec app python src/main.py"
    echo ""
    echo "3. View results in the output/ directory"
    echo ""
    echo "4. For individual commands:"
    echo "   docker-compose exec app python src/main.py migrate"
    echo "   docker-compose exec app python src/main.py analyze 1"
    echo "   docker-compose exec app python src/main.py report"
    echo ""
    echo "5. Stop services when done:"
    echo "   docker-compose down"
else
    echo "❌ System tests failed. Check the logs above."
    docker-compose logs app
    exit 1
fi