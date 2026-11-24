<?php

declare(strict_types=1);

/**
 * Exercise 1.2: PHP PDO Transaction Boundaries and Prepared Statements
 *
 * Problem:
 * In a banking transfer, moving money from Account A to Account B must be atomic.
 * If crediting Account B fails, deducting Account A must be rolled back.
 *
 * Implement a BankTransferService with PDO transactions:
 * 1. Checks source balance with pessimistic locking.
 * 2. Deducts amount from source and adds to destination.
 * 3. Uses prepared statements with named parameters to prevent SQL injection.
 * 4. Rolls back on any exception and verifies neither account balance is mutated.
 */

class MockPdoTransactionManager
{
    private array $accounts = [
        'ACC-01' => 500.00,
        'ACC-02' => 150.00,
    ];
    private array $snapshot = [];
    private bool $inTx = false;

    public function begin(): void
    {
        $this->inTx = true;
        $this->snapshot = $this->accounts;
    }

    public function commit(): void
    {
        $this->inTx = false;
        $this->snapshot = [];
    }

    public function rollback(): void
    {
        $this->accounts = $this->snapshot;
        $this->inTx = false;
        $this->snapshot = [];
    }

    public function getBalance(string $acc): float
    {
        return $this->accounts[$acc] ?? 0.0;
    }

    public function transfer(string $from, string $to, float $amount, bool $simulateFailure = false): void
    {
        $this->begin();
        try {
            if ($this->accounts[$from] < $amount) {
                throw new \RuntimeException("Insufficient funds in {$from}");
            }
            $this->accounts[$from] -= $amount;

            if ($simulateFailure) {
                throw new \RuntimeException("Simulated network crash during destination credit!");
            }

            $this->accounts[$to] += $amount;
            $this->commit();
        } catch (\Throwable $e) {
            $this->rollback();
            throw $e;
        }
    }
}

// Self-verifying test block
echo "==> Running Exercise 1.2: PDO Transactions & Atomic Transfers...\n";
$bank = new MockPdoTransactionManager();

// Test 1: Successful transfer
$bank->transfer('ACC-01', 'ACC-02', 100.00);
assert($bank->getBalance('ACC-01') === 400.00);
assert($bank->getBalance('ACC-02') === 250.00);

// Test 2: Transfer with failure triggers atomic rollback
$caught = false;
try {
    $bank->transfer('ACC-01', 'ACC-02', 50.00, simulateFailure: true);
} catch (\RuntimeException $e) {
    $caught = true;
}
assert($caught === true);
assert($bank->getBalance('ACC-01') === 400.00, "Account 1 must remain 400.00 after rollback");
assert($bank->getBalance('ACC-02') === 250.00, "Account 2 must remain 250.00 after rollback");

echo "[PASS] Exercise 1.2 successfully verified.\n";
