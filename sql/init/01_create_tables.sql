-- Banking Personalization Database Schema

-- Clients table - core client information
CREATE TABLE clients (
    client_code INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL, -- Студент / Зарплатный клиент / Премиальный клиент / Стандартный клиент
    age INTEGER NOT NULL,
    city VARCHAR(100) NOT NULL,
    avg_monthly_balance_kzt DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table - spending behavior data
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    client_code INTEGER NOT NULL REFERENCES clients(client_code),
    name VARCHAR(100) NOT NULL,
    product VARCHAR(100),
    status VARCHAR(50),
    city VARCHAR(100),
    transaction_date TIMESTAMP NOT NULL,
    category VARCHAR(100) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'KZT',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transfers table - money movement patterns
CREATE TABLE transfers (
    id SERIAL PRIMARY KEY,
    client_code INTEGER NOT NULL REFERENCES clients(client_code),
    name VARCHAR(100) NOT NULL,
    product VARCHAR(100),
    status VARCHAR(50),
    city VARCHAR(100),
    transfer_date TIMESTAMP NOT NULL,
    type VARCHAR(50) NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('in', 'out')),
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'KZT',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table - banking product definitions
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    product_type VARCHAR(50) NOT NULL,
    description TEXT,
    base_rate DECIMAL(5,4),
    cashback_rate DECIMAL(5,4),
    monthly_limit DECIMAL(15,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Client signals table - detected behavioral patterns
CREATE TABLE client_signals (
    id SERIAL PRIMARY KEY,
    client_code INTEGER NOT NULL REFERENCES clients(client_code),
    signal_type VARCHAR(100) NOT NULL,
    signal_value DECIMAL(15,2),
    signal_frequency INTEGER DEFAULT 0,
    signal_strength VARCHAR(20) DEFAULT 'medium', -- low, medium, high
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(client_code, signal_type)
);

-- Product benefits table - calculated benefit potential
CREATE TABLE product_benefits (
    id SERIAL PRIMARY KEY,
    client_code INTEGER NOT NULL REFERENCES clients(client_code),
    product_id INTEGER NOT NULL REFERENCES products(id),
    potential_benefit DECIMAL(15,2) NOT NULL,
    benefit_type VARCHAR(50) NOT NULL, -- cashback, savings, interest, etc.
    calculation_details JSONB,
    confidence_score DECIMAL(3,2) DEFAULT 0.5, -- 0.0 to 1.0
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(client_code, product_id)
);

-- Client recommendations table - final ranked recommendations
CREATE TABLE client_recommendations (
    id SERIAL PRIMARY KEY,
    client_code INTEGER NOT NULL REFERENCES clients(client_code),
    product_id INTEGER NOT NULL REFERENCES products(id),
    rank INTEGER NOT NULL CHECK (rank >= 1),
    potential_benefit DECIMAL(15,2) NOT NULL,
    recommendation_reason TEXT,
    push_notification TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(client_code, rank)
);

-- Create indexes for better performance
CREATE INDEX idx_transactions_client_code ON transactions(client_code);
CREATE INDEX idx_transactions_category ON transactions(category);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);

CREATE INDEX idx_transfers_client_code ON transfers(client_code);
CREATE INDEX idx_transfers_type ON transfers(type);
CREATE INDEX idx_transfers_direction ON transfers(direction);
CREATE INDEX idx_transfers_date ON transfers(transfer_date);

CREATE INDEX idx_client_signals_client_code ON client_signals(client_code);
CREATE INDEX idx_client_signals_type ON client_signals(signal_type);

CREATE INDEX idx_product_benefits_client_code ON product_benefits(client_code);
CREATE INDEX idx_product_benefits_benefit ON product_benefits(potential_benefit DESC);

CREATE INDEX idx_client_recommendations_client_code ON client_recommendations(client_code);
CREATE INDEX idx_client_recommendations_rank ON client_recommendations(rank);