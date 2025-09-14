# Banking Personalization System

A comprehensive system for analyzing client banking behavior and generating personalized product recommendations with benefit calculations.

## System Overview

This system processes 60 clients' 3-month banking data to:
1. **Detect behavioral signals** for 10 different banking products
2. **Calculate potential benefits** using precise formulas per product
3. **Rank top 4 products** per client based on potential benefit
4. **Generate comprehensive reports** with detailed analysis

## Architecture

- **PostgreSQL Database**: Structured data storage with optimized queries
- **Python Application**: Signal detection, benefit calculation, and recommendation engines
- **Adminer**: Database management interface
- **Docker Compose**: Complete containerized environment

## Quick Start

### 1. Set up environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Azure OpenAI credentials
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_API_KEY=your-api-key-here
```

### 2. Start the system

```bash
# Build and start all services
docker-compose up -d

# Check services status
docker-compose ps
```

### 3. Access Adminer (Database Management)

Open http://localhost:8080 in your browser:
- **System**: PostgreSQL
- **Server**: postgres
- **Username**: banking_user
- **Password**: banking_pass
- **Database**: banking_personalization

### 4. Run the analysis

```bash
# Run complete analysis pipeline
docker-compose exec app python src/main.py

# Or run individual commands:
docker-compose exec app python src/main.py migrate     # Just migrate data
docker-compose exec app python src/main.py analyze 1   # Analyze single client
docker-compose exec app python src/main.py report      # Generate reports only
```

### 5. View results

Reports are generated in the `output/` directory:
- `client_benefits_analysis.csv` - Main comprehensive report
- `client_signals_debug.csv` - Detected behavioral signals
- `product_benefits_debug.csv` - Calculated benefits per product

## Database Schema

### Core Tables

- **`clients`** - Client profiles (60 records)
- **`transactions`** - Spending behavior data (~3 months per client)
- **`transfers`** - Money movement patterns (in/out, various types)
- **`products`** - 10 banking product definitions
- **`client_signals`** - Detected behavioral patterns
- **`product_benefits`** - Calculated benefit potential
- **`client_recommendations`** - Final ranked recommendations

## Product Analysis

### 1. Travel Card
- **Signals**: Travel/hotel/taxi spending, foreign currency transactions
- **Benefits**: 4% cashback on travel categories, FX fee savings
- **Formula**: `4% * (travel_spending) + fx_savings`

### 2. Premium Card
- **Signals**: High balance (>1M KZT), frequent ATM/transfers, premium category spending
- **Benefits**: Tiered cashback (2-4%), fee savings, premium category bonuses
- **Formula**: `tier_rate * spending + 4% * premium_categories + fee_savings`

### 3. Credit Card
- **Signals**: Clear top-3 spending categories, online services usage
- **Benefits**: 10% on top categories, interest-free period value
- **Formula**: `10% * top_3_spending + 10% * online_services + credit_value`

### 4. FX Exchange
- **Signals**: FX trading activity, regular foreign spending
- **Benefits**: Better exchange rates, target rate optimization
- **Formula**: `fx_volume * (spread_savings + optimization_value)`

### 5. Cash Loan
- **Signals**: Cash flow gaps, low balance ratios
- **Benefits**: Lower interest rates vs market alternatives
- **Formula**: `loan_amount * (market_rate - bank_rate)`

### 6-8. Deposits (3 types)
- **Savings**: 16.5% rate, locked deposits
- **Accumulative**: 15.5% rate, contributions allowed
- **Multi-currency**: 14.5% rate, FX flexibility
- **Formula**: `deposit_amount * annual_rate`

### 9. Investments
- **Signals**: Available funds, existing investment activity
- **Benefits**: Commission-free first year
- **Formula**: `investment_amount * commission_savings`

### 10. Gold Bars
- **Signals**: High liquidity, luxury spending patterns
- **Benefits**: Inflation protection, portfolio diversification
- **Formula**: `allocation * inflation_hedge_rate`

## Signal Detection

The system detects behavioral patterns including:

- **Spending patterns**: Category analysis, frequency, amounts
- **Balance behavior**: Stability, growth trends, liquidity
- **Transfer patterns**: Types, directions, volumes
- **FX activity**: Currency conversion frequency and volumes
- **Credit usage**: Existing loan patterns, payment behavior

## Benefit Calculation

Precise formulas calculate potential annual benefits:

1. **Cashback calculations** with tier adjustments and limits
2. **Fee savings** on ATM withdrawals, transfers, FX operations
3. **Interest optimization** for loans and deposits
4. **Commission savings** on investment operations
5. **Risk-adjusted returns** for portfolio products

## Output Format

### Main Report: `client_benefits_analysis.csv`

```csv
client_code,name,current_product,top1_product,top1_benefit,top2_product,top2_benefit,top3_product,top3_benefit,top4_product,top4_benefit
1,Айгерим,Карта для путешествий,Премиальная карта,"124,500 ₸",Кредитная карта,"89,200 ₸",...
```

### Debug Files

- **Signals**: All detected behavioral patterns per client
- **Benefits**: Detailed benefit calculations with formulas

## Database Queries

Access the database through Adminer or direct SQL:

```sql
-- Client overview with top recommendation
SELECT c.name, c.status, c.avg_monthly_balance_kzt,
       p.name as top_product, cr.potential_benefit
FROM clients c
LEFT JOIN client_recommendations cr ON c.client_code = cr.client_code AND cr.rank = 1
LEFT JOIN products p ON cr.product_id = p.id
ORDER BY cr.potential_benefit DESC;

-- Signals analysis for specific client
SELECT signal_type, signal_value, signal_strength
FROM client_signals
WHERE client_code = 1
ORDER BY signal_value DESC;

-- Product recommendation frequency
SELECT p.name, COUNT(*) as recommendations
FROM client_recommendations cr
JOIN products p ON cr.product_id = p.id
WHERE cr.rank = 1
GROUP BY p.name
ORDER BY recommendations DESC;
```

## Development

### Project Structure

```
/
├── src/
│   ├── main.py                    # Main application
│   ├── models/client.py           # Data models
│   ├── services/
│   │   ├── data_migration.py      # CSV → PostgreSQL
│   │   ├── signal_detection.py    # Behavioral analysis
│   │   ├── benefit_calculator.py  # Product benefits
│   │   ├── recommendation_engine.py # Ranking system
│   │   └── report_generator.py    # CSV reports
│   └── utils/database.py          # DB connections
├── dataset/                       # CSV data files
├── output/                        # Generated reports
├── sql/init/                      # Database schema
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

### Testing

```bash
# Test single client analysis
docker-compose exec app python src/main.py analyze 1

# Check database connection
docker-compose exec app python -c "from src.utils.database import db_manager; print(db_manager.test_connection())"

# View logs
docker-compose logs app
```

### Troubleshooting

1. **Database connection issues**: Check if PostgreSQL container is running
2. **Migration errors**: Verify CSV files exist in dataset/ directory
3. **Missing recommendations**: Check if signals and benefits were calculated
4. **Performance**: Monitor container resources and optimize queries

## Results Interpretation

The system provides:

1. **Signal Strength**: `low`, `medium`, `high` confidence levels
2. **Benefit Amounts**: Annual potential benefit in KZT
3. **Confidence Scores**: 0.0-1.0 recommendation confidence
4. **Ranking**: Top 4 products ordered by potential benefit

Use these metrics to:
- Prioritize client outreach based on benefit amounts
- Focus on high-confidence recommendations
- Understand behavioral patterns driving recommendations
- Monitor system performance and accuracy