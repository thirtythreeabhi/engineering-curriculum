<?php

declare(strict_types=1);

namespace App\Database;

final class MockPreparedStatement implements PreparedStatementInterface
{
    /**
     * @param array<int, array<string, mixed>> $results
     */
    public function __construct(
        public readonly string $sql,
        private MockTransactionalConnection $connection,
        private array $results = [],
        private int $affectedRows = 0
    ) {}

    public function execute(?array $params = null): bool
    {
        return $this->connection->executeStatement($this, $params ?? []);
    }

    public function fetch(): array|false
    {
        if (empty($this->results)) {
            return false;
        }
        return array_shift($this->results);
    }

    public function fetchAll(): array
    {
        $res = $this->results;
        $this->results = [];
        return $res;
    }

    public function rowCount(): int
    {
        return $this->affectedRows;
    }

    public function setResults(array $results, int $affectedRows = 0): void
    {
        $this->results = $results;
        $this->affectedRows = $affectedRows;
    }
}

final class MockTransactionalConnection implements ConnectionInterface
{
    private bool $inTransaction = false;
    public ?IsolationLevel $currentIsolationLevel = null;
    public int $beginTransactionCalls = 0;
    public int $commitCalls = 0;
    public int $rollBackCalls = 0;
    public array $executedQueries = [];

    /** @var array<string, array<int|string, array<string, mixed>>> */
    public array $tables = [
        'products' => [],
        'orders' => [],
        'order_items' => [],
    ];

    private array $snapshot = [];
    private int $lastInsertId = 1000;

    public function beginTransaction(?IsolationLevel $level = null): bool
    {
        if ($this->inTransaction) {
            throw new \RuntimeException("Transaction already active");
        }
        $this->inTransaction = true;
        $this->currentIsolationLevel = $level;
        $this->beginTransactionCalls++;
        $this->snapshot = unserialize(serialize($this->tables));
        return true;
    }

    public function commit(): bool
    {
        if (!$this->inTransaction) {
            throw new \RuntimeException("Cannot commit: No active transaction");
        }
        $this->inTransaction = false;
        $this->commitCalls++;
        $this->snapshot = [];
        return true;
    }

    public function rollBack(): bool
    {
        if (!$this->inTransaction) {
            throw new \RuntimeException("Cannot rollback: No active transaction");
        }
        $this->inTransaction = false;
        $this->rollBackCalls++;
        // restore state from snapshot
        $this->tables = $this->snapshot;
        $this->snapshot = [];
        return true;
    }

    public function inTransaction(): bool
    {
        return $this->inTransaction;
    }

    public function prepare(string $sql): PreparedStatementInterface
    {
        return new MockPreparedStatement($sql, $this);
    }

    public function exec(string $sql): int
    {
        $this->executedQueries[] = ['sql' => $sql, 'params' => []];
        return 1;
    }

    public function lastInsertId(?string $name = null): string|int
    {
        return $this->lastInsertId;
    }

    public function executeStatement(MockPreparedStatement $stmt, array $params): bool
    {
        $sql = $stmt->sql;
        $this->executedQueries[] = ['sql' => $sql, 'params' => $params];

        // Match SELECT FOR UPDATE or regular product select
        if (stripos($sql, 'SELECT') === 0 && stripos($sql, 'products') !== false) {
            $productId = $params['id'] ?? $params[0] ?? null;
            if ($productId !== null && isset($this->tables['products'][$productId])) {
                $stmt->setResults([$this->tables['products'][$productId]], 1);
            } else {
                $stmt->setResults([], 0);
            }
            return true;
        }

        // Match UPDATE products SET stock_quantity
        if (stripos($sql, 'UPDATE') === 0 && stripos($sql, 'products') !== false) {
            $stock = $params['stock'] ?? $params[0] ?? 0;
            $productId = $params['id'] ?? $params[1] ?? null;
            if ($productId !== null && isset($this->tables['products'][$productId])) {
                $this->tables['products'][$productId]['stock_quantity'] = (int)$stock;
                $stmt->setResults([], 1);
            }
            return true;
        }

        // Match INSERT INTO orders
        if (stripos($sql, 'INSERT INTO orders') !== false) {
            $this->lastInsertId++;
            $orderId = $this->lastInsertId;
            $this->tables['orders'][$orderId] = [
                'id' => $orderId,
                'customer_id' => $params['customer_id'] ?? 1,
                'status' => $params['status'] ?? 'pending',
                'total_amount' => $params['total_amount'] ?? 0.0,
                'created_at' => date('Y-m-d H:i:s'),
            ];
            $stmt->setResults([], 1);
            return true;
        }

        // Match INSERT INTO order_items
        if (stripos($sql, 'INSERT INTO order_items') !== false) {
            $itemId = count($this->tables['order_items']) + 1;
            $this->tables['order_items'][$itemId] = $params;
            $stmt->setResults([], 1);
            return true;
        }

        return true;
    }
}
