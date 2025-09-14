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

## Database Dump file
```text
db-dump.sql
```

## CSV Output Result
```text
output/co-founder-bcc-case-1-result.csv
```

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

# Generate personalized push notifications (requires Azure OpenAI setup)
docker-compose exec app python src/main.py generate_notifications          # All recommendations
docker-compose exec app python src/main.py generate_notification 639       # Specific recommendation ID
```

### 5. View results

Reports are generated in the `output/` directory:
- `client_benefits_analysis.csv` - Main comprehensive report
- `client_signals_debug.csv` - Detected behavioral signals
- `product_benefits_debug.csv` - Calculated benefits per product

## Push Notifications (Azure OpenAI Integration)

The system generates personalized push notifications using Azure OpenAI GPT-4o model with creative, friendly tone.

### Setup Requirements

Ensure your `.env` file contains Azure OpenAI credentials:
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

### Generation Commands

```bash
# Generate notifications for all client recommendations
docker-compose exec app python src/main.py generate_notifications

# Generate notification for specific recommendation ID
docker-compose exec app python src/main.py generate_notification 639
```

### Notification Style (TOV)

- **Friendly and casual** tone using informal "вы"
- **Creative approach** with local references (city, season, lifestyle)
- **Personal observations** based on client spending patterns
- **Specific benefits** with exact amounts in KZT
- **Gentle call-to-action** without aggressive sales pressure
- **Length**: 180-220 characters with max 1 emoji

### Example Generated Notifications

```
Инкар, кажется, кафе и такси Караганды знают вас в лицо 😉
Кредитная карта вернёт до 853 609 ₸ кешбэком за любимые категории.
Настроим карту — и пусть кешбэк работает!

Айгерим, держать 1 500 000 ₸ на счёте — это почти как копить на алматинский отпуск 😏
Премиальная карта даст кешбэк до 420 000 ₸ в год и бесплатные снятия.
Хотите оформить?
```

### Data Processing

The system:
1. **Extracts client data** using SQL query with recommendation details
2. **Converts to JSON format** for Azure OpenAI processing
3. **Uses prompt template** from `prompt.md` with TOV guidelines
4. **Saves results** to `client_recommendations.push_notification` field
5. **Processes by recommendation ID** (not by client code)

## Database Schema

### Core Tables

- **`clients`** - Client profiles (60 records)
- **`transactions`** - Spending behavior data (~3 months per client)
- **`transfers`** - Money movement patterns (in/out, various types)
- **`products`** - 10 banking product definitions
- **`client_signals`** - Detected behavioral patterns
- **`product_benefits`** - Calculated benefit potential
- **`client_recommendations`** - Final ranked recommendations with AI-generated notifications

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

-- View generated push notifications
SELECT cr.id, c.name, p.name as product_name,
       cr.potential_benefit, cr.push_notification
FROM client_recommendations cr
JOIN clients c ON cr.client_code = c.client_code
JOIN products p ON cr.product_id = p.id
WHERE cr.push_notification IS NOT NULL
ORDER BY cr.id;

-- Find recommendations without notifications
SELECT cr.id, c.name, p.name as product_name
FROM client_recommendations cr
JOIN clients c ON cr.client_code = c.client_code
JOIN products p ON cr.product_id = p.id
WHERE cr.push_notification IS NULL
LIMIT 10;
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
│   │   ├── report_generator.py    # CSV reports
│   │   └── notification_generator.py # Azure OpenAI notifications
│   └── utils/database.py          # DB connections
├── dataset/                       # CSV data files
├── output/                        # Generated reports
├── sql/init/                      # Database schema
├── prompt.md                      # Azure OpenAI prompt template
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

### Testing

```bash
# Test single client analysis
docker-compose exec app python src/main.py analyze 1

# Test push notification generation for specific recommendation
docker-compose exec app python src/main.py generate_notification 639

# Check available recommendation IDs
docker-compose exec app python -c "
from src.utils.database import db_manager
from sqlalchemy import text
session = db_manager.get_session()
result = session.execute(text('SELECT id FROM client_recommendations LIMIT 5')).fetchall()
print('Available IDs:', [row.id for row in result])
session.close()
"

# Check database connection
docker-compose exec app python -c "from src.utils.database import db_manager; print(db_manager.test_connection())"

# View logs
docker-compose logs app
```

### Troubleshooting

1. **Database connection issues**: Check if PostgreSQL container is running
2. **Migration errors**: Verify CSV files exist in dataset/ directory
3. **Missing recommendations**: Check if signals and benefits were calculated
4. **Azure OpenAI errors**: Verify credentials in .env and check API quotas
5. **Notification generation fails**: Ensure recommendation IDs exist in database
6. **Performance**: Monitor container resources and optimize queries

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

---

## Q&A

### 1. Данные и подготовка

#### Источники данных

**Профили клиентов (clients.csv):**
- 60 уникальных клиентов из различных городов Казахстана
- Демографические данные: имя, возраст (25-55 лет), город проживания
- Финансовый профиль: текущий статус, средний месячный баланс (от 50,000 до 5,000,000 ₸)
- Текущие банковские продукты для исключения дублирования рекомендаций

**Транзакции (client_X_transactions_3m.csv):**
- Детальная история трат каждого клиента за 3 месяца
- ~250-300 операций на клиента (всего ~15,000+ транзакций)
- Категоризация: продукты питания, кафе/рестораны, такси, онлайн-сервисы, медицина, развлечения, путешествия
- Суммы операций: от 500 ₸ (мелкие покупки) до 500,000 ₸ (крупные траты)
- Общий объем проанализированных трат: >1 млрд ₸

**Переводы (client_X_transfers_3m.csv):**
- История денежных переводов и снятий за 3 месяца
- ~50-80 операций на клиента (всего ~3,000+ переводов)
- Типы: входящие переводы, исходящие платежи, снятия в ATM, межбанковские переводы
- Направления: пополнения счета, выводы средств, P2P переводы
- Анализ cash flow для понимания финансового поведения

#### Объём данных

**Масштаб клиентской базы:**
- **60 клиентов** — репрезентативная выборка из разных городов: Алматы (40%), Нур-Султан (25%), Караганда (20%), Шымкент и другие (15%)
- **Возрастные группы**: 25-35 лет (45%), 35-45 лет (35%), 45-55 лет (20%)
- **Финансовые сегменты**: масс-маркет (<500K ₸), премиум (500K-2M ₸), VIP (>2M ₸)

**Операционные данные:**
- **~15,000+ транзакций** с детализацией по категориям и суммам
- **~3,000+ переводов** для анализа денежных потоков
- **3 месяца активности** — достаточный период для выявления устойчивых поведенческих паттернов
- **Общий оборот**: >1 млрд ₸ проанализированных операций

#### Шаги предобработки

**1. Очистка и валидация данных:**
- Проверка форматов дат транзакций и переводов
- Валидация сумм операций (исключение отрицательных и нереалистичных значений)
- Стандартизация категорий трат (унификация похожих категорий)
- Обработка null значений и дубликатов записей

**2. Агрегация и группировка:**
- Группировка транзакций по категориям для каждого клиента
- Подсчёт частоты операций по типам (ежедневные, еженедельные, месячные)
- Расчёт общих объёмов трат и переводов за период
- Определение сезонных паттернов и трендов активности

**3. Расчёт поведенческих метрик:**
- **Топ-3 категории трат** (для персонализации кредитной карты)
- **Коэффициент стабильности баланса** (для премиум продуктов и депозитов)
- **FX активность и потери на курсе** (для валютных продуктов)
- **Cash flow паттерны** (соотношение доходов к расходам для кредитных продуктов)
- **Частота ATM операций** (для определения потребности в премиум обслуживании)

### 2. Подход и логика решения

#### Как находим «сигналы выгоды» по каждому продукту

**Travel Card (Карта для путешествий):**
- **Сигналы поведения:**
  - Траты на категории "Путешествия", "Отели", "Такси" >50,000 ₸/месяц
  - FX транзакции с потерями на курсе >5,000 ₸/месяц
  - Частые поездки (разные города в транзакциях)
- **Логика выгоды:** 4% кешбэк на travel категории + экономия на валютных операциях
- **Формула расчёта:** `4% × (travel_spending) + fx_savings_annual`

**Premium Card (Премиальная карта):**
- **Сигналы поведения:**
  - Средний баланс >1,000,000 ₸ стабильно 3 месяца
  - Частые ATM операции (>10 операций/месяц)
  - Траты на премиум категории (рестораны, развлечения) >100,000 ₸/месяц
- **Логика выгоды:** Многоуровневый кешбэк (2-4%) + отсутствие комиссий + премиум сервисы
- **Формула расчёта:** `tier_rate × spending + 4% × premium_categories + fee_savings`

**Credit Card (Кредитная карта):**
- **Сигналы поведения:**
  - Четко выраженные топ-3 категории трат (>70% всех операций)
  - Регулярные траты на онлайн-сервисы и подписки >20,000 ₸/месяц
  - Стабильная трата в одних и тех же категориях 3 месяца подряд
- **Логика выгоды:** 10% кешбэк на топ категории + беспроцентный период
- **Формула расчёта:** `10% × top_3_spending + 10% × online_services + credit_period_value`

**FX Exchange (Валютные операции):**
- **Сигналы поведения:**
  - Регулярные FX операции (>5 в месяц)
  - Объем валютных операций >$1,000/месяц
  - Потери на спреде >10,000 ₸/месяц
- **Логика выгоды:** Лучший обменный курс + автоматическая оптимизация
- **Формула расчёта:** `fx_volume × (spread_savings + optimization_value)`

**Cash Loan (Кредит наличными):**
- **Сигналы поведения:**
  - Отрицательные балансы или близкие к нулю (коэффициент баланс/траты <0.5)
  - Нерегулярные поступления доходов
  - Кассовые разрывы между доходами и тратами
- **Логика выгоды:** Выгодная ставка vs рыночных альтернатив
- **Формула расчёта:** `loan_amount × (market_rate - bank_rate) × loan_period`

**Депозиты (3 типа - Накопительный, Сберегательный, Мультивалютный):**
- **Сигналы поведения:**
  - Стабильно высокие остатки (>500,000 ₸) без активного использования
  - Низкая трата относительно баланса (<30% баланса в месяц)
  - Отсутствие инвестиционных продуктов
- **Логика выгоды:** Доходность 14.5-16.5% vs инфляции и банковских рисков
- **Формула расчёта:** `available_funds × annual_rate × deposit_period`

**Investments (Инвестиции):**
- **Сигналы поведения:**
  - Высокая ликвидность (>1,000,000 ₸ свободных средств)
  - Отсутствие активных инвестиционных продуктов
  - Интерес к финансовым услугам (траты на финтех, консультации)
- **Логика выгоды:** Освобождение от комиссий первый год
- **Формула расчёта:** `investment_amount × commission_savings_rate`

**Gold Bars (Золотые слитки):**
- **Сигналы поведения:**
  - Очень высокая ликвидность (>2,000,000 ₸)
  - Траты на люксовые товары и услуги
  - Консервативное управление средствами
- **Логика выгоды:** Защита от инфляции + диверсификация портфеля
- **Формула расчёта:** `allocation_amount × inflation_hedge_rate`

#### Как выбираем лучший продукт

**Метрика ранжирования:**
- **Основная метрика:** Потенциальная годовая выгода в ₸ (кешбэк + экономия - затраты на обслуживание)
- **Дополнительные факторы:** Confidence score (0.0-1.0), совместимость с текущими продуктами
- **Минимальный порог:** Выгода должна быть >50,000 ₸/год для включения в рекомендации

**Правила фильтрации:**
- Исключаем продукты, которыми клиент уже пользуется
- Применяем бизнес-ограничения (например, максимум 1 кредитный продукт)
- Учитываем региональные ограничения (доступность продуктов по городам)

**Модель принятия решений:**
1. Ранжирование всех подходящих продуктов по убыванию потенциальной выгоды
2. Применение бизнес-правил и фильтров
3. Отбор топ-4 продуктов для финальных рекомендаций
4. Расчёт confidence score на основе силы поведенческих сигналов

#### Алгоритм обработки (детально)

**Пошаговый процесс для каждого клиента:**

```
ЭТАП 1: Загрузка данных клиента
├── Профиль клиента (возраст, город, баланс)
├── Транзакции за 3 месяца (категории, суммы, даты)
└── Переводы за 3 месяца (типы, направления, объемы)

ЭТАП 2: Детекция поведенческих сигналов
├── Travel Card: анализ travel категорий + FX активность
├── Premium Card: анализ баланса + ATM частота + премиум траты
├── Credit Card: топ-3 категории + онлайн сервисы
├── FX Exchange: валютные операции + потери на спреде
├── Cash Loan: анализ cash flow + коэффициенты ликвидности
├── Deposits: свободные средства + низкая активность
├── Investments: высокая ликвидность + финансовые интересы
└── Gold Bars: очень высокие остатки + люкс траты

ЭТАП 3: Расчёт потенциальной выгоды
├── Применение формул расчёта для каждого продукта
├── Учёт индивидуальных паттернов клиента
├── Прогнозирование годовой выгоды в ₸
└── Расчёт confidence score (сила сигналов)

ЭТАП 4: Ранжирование и отбор
├── Сортировка по убыванию потенциальной выгоды
├── Исключение текущих продуктов клиента
├── Применение бизнес-правил и ограничений
└── Отбор топ-4 продуктов для рекомендации

ЭТАП 5: Сохранение результатов
├── Детализация расчётов (calculation_details JSON)
├── Причина рекомендации (recommendation_reason)
├── Ранг продукта (1-4) и confidence score
└── Подготовка данных для генерации уведомлений
```

**Пример логики для конкретного клиента:**
- **Инкар, 32 года, Караганда, баланс 1,200,000 ₸**
- **Сигналы:** 180,000 ₸/месяц на кафе + такси, 15 ATM операций/месяц
- **Результат:** Кредитная карта (853,609 ₸ выгоды) > Премиальная карта (420,000 ₸ выгоды)

### 3. Генерация пуш-уведомлений

#### Структура сообщения: контекст → польза → CTA

**1. Контекст (40-60 символов) - Персональное наблюдение:**
- **Основано на реальных данных клиента:** анализ трат, паттернов, поведения
- **Эмоциональная подача:** легкие метафоры, образы, локальные отсылки
- **Примеры контекста:**
  - *"кафе и такси Караганды знают вас в лицо"* — для клиента с высокими тратами на питание/транспорт в Караганде
  - *"держать 1,500,000 ₸ на счёте"* — для клиента с стабильно высоким балансом
  - *"лето в Алматы явно прошло вкусно"* — сезонная отсылка для клиента с высокими тратами на рестораны
  - *"иногда хочется чуть больше свободы, чем даёт зарплата"* — для клиента с признаками нехватки ликвидности

**2. Польза (60-80 символов) - Конкретная выгода с цифрами:**
- **Точные расчёты:** используются реальные суммы potential_benefit из базы данных
- **Формат цифр:** разряды через пробелы, валюта отделена пробелом (853 609 ₸)
- **Конкретика продукта:** кешбэк, экономия, удобство — четко и коротко
- **Примеры пользы:**
  - *"вернёт до 853 609 ₸ кешбэком за любимые категории"* — кредитная карта
  - *"даст кешбэк до 420 000 ₸ в год и бесплатные снятия"* — премиальная карта
  - *"с выгодной ставкой экономит 180 000 ₸ в год"* — кредит наличными
  - *"16,5% доходности принесёт 247 500 ₸ дохода"* — депозит

**3. CTA (40-60 символов) - Дружеский призыв к действию:**
- **Живые акценты:** без официоза, на равных с клиентом
- **Вариативность:** разные формулировки для избежания шаблонности
- **Примеры CTA:**
  - *"Погнали оформим?"* — энергичный, молодежный
  - *"Настроим карту — и пусть кешбэк работает!"* — процессуальный, конкретный
  - *"Хотите оформить?"* — классический, вежливый
  - *"Попробуем оформить?"* — мягкий, без давления

#### Применение Tone of Voice (на равных, без воды, 180–220 символов)

**TOV принципы в деталях:**

**На равных:**
- Обращение "вы" с маленькой буквы (не "Вы")
- Отсутствие официоза и банковской терминологии
- Дружеский тон как с хорошим знакомым
- Допустимый ненавязчивый юмор и ирония

**Без воды:**
- Каждое слово работает и несет смысловую нагрузку
- Конкретные цифры выгоды без размытых формулировок
- Отсутствие агрессивных триггеров дефицита ("только сегодня", "последний шанс")
- Максимум 1 восклицательный знак на сообщение

**180-220 символов точно:**
- Оптимальная длина для мобильных пуш-уведомлений
- Полное отображение без сокращений в большинстве устройств
- Достаточно места для контекста + пользы + CTA
- Контроль через автоматический подсчет символов в генерации

**Дополнительные элементы:**
- **1 эмодзи максимум:** только по смыслу и к месту (😉 😏 💸 😋)
- **Локальные отсылки:** город клиента, сезон, местные особенности
- **Возрастная адаптация:** для 30-40 лет — чуть моложе и веселее, без перебора со сленгом

#### Автоматизация (шаблоны + подстановка параметров)

**Технологический процесс:**

**1. Шаблоны и базовая структура:**
- **prompt.md** — основной шаблон с TOV требованиями и примерами
- **Переменная {client_data}** — JSON с данными клиента и рекомендацией
- **Инструкции для AI** — четкие правила генерации одного уведомления

**2. Подстановка параметров из БД:**
- **Данные клиента:** `client_name`, `city`, `age`, `avg_monthly_balance_kzt`
- **Данные продукта:** `product_name`, `potential_benefit`, `calculation_details`
- **Поведенческие данные:** топ категории трат, суммы, частота операций
- **Контекстные данные:** текущий сезон, региональные особенности

**3. Azure OpenAI обработка:**
- **Модель:** GPT-4o для креативности и понимания контекста
- **API версия:** 2025-01-01-preview для стабильности
- **Формат входа:** JSON структурированные данные клиента
- **Формат выхода:** готовое пуш-уведомление 180-220 символов

**4. Автосохранение и валидация:**
- **Сохранение в БД:** поле `client_recommendations.push_notification`
- **Валидация длины:** автоматическая проверка 180-220 символов
- **Проверка TOV:** соответствие дружескому тону и отсутствие КАПС
- **Логирование:** отслеживание успешности генерации и ошибок

**Пример полного цикла:**
```json
[
  {
    "Вход": {
      "client_name": "Инкар",
      "city": "Караганда",
      "product_name": "Кредитная карта",
      "potential_benefit": 853609,
      "top_categories": ["Кафе/рестораны", "Такси", "Продукты"]
    }
  }
]
```
Azure OpenAI обработка с prompt.md ↓

Выход: 
```text
"Инкар, кажется, кафе и такси Караганды знают вас в лицо 😉
Кредитная карта вернёт до 853 609 ₸ кешбэком за любимые категории.
Настроим карту — и пусть кешбэк работает!" (218 символов)
```

**Масштабирование:**
- **Обработка всех рекомендаций:** команда `generate_notifications` для массовой генерации
- **Индивидуальная обработка:** команда `generate_notification <id>` для тестирования
- **Мониторинг качества:** анализ сгенерированных уведомлений на соответствие TOV
- **A/B тестирование:** возможность генерации нескольких вариантов для оптимизации конверсии
