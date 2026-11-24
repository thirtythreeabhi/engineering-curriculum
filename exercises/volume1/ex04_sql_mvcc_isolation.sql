-- Exercise 1.4: SQL Transactions, Solvency Constraints, and Isolation Models
--
-- Runs directly in SQLite 3 (via sqlite3 / Python sqlite3) using BEGIN IMMEDIATE
-- and integer cents (never floating-point money), with a companion PostgreSQL
-- MVCC REPEATABLE READ + SELECT ... FOR UPDATE reference section below.
--
-- Why SQLite BEGIN IMMEDIATE vs PostgreSQL MVCC:
-- * SQLite serializes writers at the database file level: BEGIN IMMEDIATE acquires
--   a RESERVED write lock upfront, preventing lost-update anomalies between two
--   concurrent readers that later try to write.
-- * PostgreSQL uses Multi-Version Concurrency Control (MVCC): readers never block
--   writers, so concurrent transactions under READ COMMITTED can read stale balances
--   unless rows are locked with SELECT ... FOR UPDATE or run under REPEATABLE READ /
--   SERIALIZABLE (which aborts conflicting concurrent writers with SQLSTATE 40001).

-- 1. Create banking accounts table using integer cents and solvency CHECK constraint
CREATE TABLE IF NOT EXISTS bank_accounts (
    account_id TEXT PRIMARY KEY,
    owner_name TEXT NOT NULL,
    balance_cents INTEGER NOT NULL CHECK (balance_cents >= 0)
);

-- 2. Populate initial records ($1,000.00 = 100000 cents, $500.00 = 50000 cents)
INSERT INTO bank_accounts (account_id, owner_name, balance_cents) VALUES
('ACC-001', 'Alice Engineer', 100000),
('ACC-002', 'Bob Developer', 50000)
ON CONFLICT (account_id) DO NOTHING;

-- 3. Atomic transfer of $200.00 (20000 cents) from ACC-001 to ACC-002
BEGIN IMMEDIATE;

UPDATE bank_accounts
SET balance_cents = balance_cents - 20000
WHERE account_id = 'ACC-001' AND balance_cents >= 20000;

UPDATE bank_accounts
SET balance_cents = balance_cents + 20000
WHERE account_id = 'ACC-002';

COMMIT;

-- 4. Companion PostgreSQL MVCC + Pessimistic Row Locking Reference (PostgreSQL only):
-- BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;
-- SELECT balance_cents FROM bank_accounts WHERE account_id = 'ACC-001' FOR UPDATE;
-- UPDATE bank_accounts SET balance_cents = balance_cents - 20000 WHERE account_id = 'ACC-001';
-- UPDATE bank_accounts SET balance_cents = balance_cents + 20000 WHERE account_id = 'ACC-002';
-- COMMIT;

-- 5. Verification Query (asserted by exercises/run-all-exercises.sh)
SELECT
    account_id,
    owner_name,
    balance_cents,
    CASE
        WHEN balance_cents >= 0 THEN 'VALID_SOLVENT'
        ELSE 'VIOLATION_NEGATIVE'
    END AS solvency_check
FROM bank_accounts
ORDER BY account_id;
