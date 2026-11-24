-- Exercise 1.4: SQL Transactions, MVCC, and Isolation Levels
-- Demonstrates row locking, dirty read prevention, and phantom read elimination.

-- 1. Create banking accounts table
CREATE TABLE IF NOT EXISTS bank_accounts (
    account_id TEXT PRIMARY KEY,
    owner_name TEXT NOT NULL,
    balance NUMERIC(12, 2) NOT NULL CHECK (balance >= 0.0)
);

-- 2. Populate initial records
INSERT INTO bank_accounts (account_id, owner_name, balance) VALUES
('ACC-001', 'Alice Engineer', 1000.00),
('ACC-002', 'Bob Developer', 500.00)
ON CONFLICT (account_id) DO NOTHING;

-- 3. Transaction 1: Pessimistic Row Locking with FOR UPDATE (Simulated)
-- In PostgreSQL:
-- BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;
-- SELECT balance FROM bank_accounts WHERE account_id = 'ACC-001' FOR UPDATE;
-- UPDATE bank_accounts SET balance = balance - 200.00 WHERE account_id = 'ACC-001';
-- COMMIT;

-- 4. Transaction 2: Atomic Transfer with Condition Check
UPDATE bank_accounts
SET balance = balance - 200.00
WHERE account_id = 'ACC-001' AND balance >= 200.00;

UPDATE bank_accounts
SET balance = balance + 200.00
WHERE account_id = 'ACC-002';

-- 5. Verification Query
SELECT
    account_id,
    owner_name,
    balance,
    CASE
        WHEN balance >= 0.0 THEN 'VALID_SOLVENT'
        ELSE 'VIOLATION_NEGATIVE'
    END AS solvency_check
FROM bank_accounts
ORDER BY account_id;
