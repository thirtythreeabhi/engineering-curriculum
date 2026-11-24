-- Platform Schema Initialization

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS platform_orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total_amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed initial catalog
INSERT INTO products (sku, name, category, price, stock_quantity) VALUES
('LAPTOP-X1', 'ThinkPad Carbon X1', 'Electronics', 1499.00, 25),
('HEADSET-PRO', 'Sony WH-1000XM5', 'Audio', 399.00, 50),
('KEYBOARD-MECH', 'Keychron Q1 Pro', 'Accessories', 199.00, 80),
('MONITOR-4K', 'Dell UltraSharp 32', 'Displays', 799.00, 15)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO users (username, email) VALUES
('developer_dave', 'dave@example.com'),
('architect_alice', 'alice@example.com')
ON CONFLICT (username) DO NOTHING;
